#!/usr/bin/env python3
"""Validate an exact v7 screenshot inventory, attempt history and decoded PNG evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EVALS = ROOT / "evals"
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence_ledger import LedgerError, screenshot_metadata  # noqa: E402

PREFLIGHT_SPEC = importlib.util.spec_from_file_location("v7_preflight", EVALS / "v7_preflight.py")
assert PREFLIGHT_SPEC and PREFLIGHT_SPEC.loader
preflight = importlib.util.module_from_spec(PREFLIGHT_SPEC)
PREFLIGHT_SPEC.loader.exec_module(preflight)


SHA256 = re.compile(r"[0-9a-f]{64}")
RECORD_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
VARIANTS = ("accepted", "candidate")
GATES = ("fast", "full")
FAST_PROFILES = ("desktop", "mobile")
BASE_PROFILES = ("desktop", "standard-desktop", "short-desktop", "tablet", "mobile", "compact-mobile")
PARITY_PROFILES = ("desktop", "short-desktop", "mobile")
PARITY_ENGINES = ("chromium", "firefox", "webkit")
PROFILE_CONTRACTS = {
    "desktop": {"width": 1440, "height": 1000, "deviceScaleFactor": 1, "hasTouch": False, "isMobile": False},
    "standard-desktop": {"width": 1280, "height": 720, "deviceScaleFactor": 1, "hasTouch": False, "isMobile": False},
    "short-desktop": {"width": 1024, "height": 600, "deviceScaleFactor": 1, "hasTouch": False, "isMobile": False},
    "tablet": {"width": 768, "height": 1024, "deviceScaleFactor": 2, "hasTouch": True, "isMobile": False},
    "mobile": {"width": 390, "height": 844, "deviceScaleFactor": 3, "hasTouch": True, "isMobile": True},
    "compact-mobile": {"width": 360, "height": 800, "deviceScaleFactor": 3, "hasTouch": True, "isMobile": True},
}
LEDGER_KEYS = {
    "schema_version",
    "cohort_manifest",
    "split",
    "gate",
    "status",
    "variants",
    "expected_count",
    "hidden_matrix_sha256",
    "input_inventory_sha256",
    "attempts",
}
FOCUS_CLAIM_BOUNDARY = (
    "Programmatic focus of evaluator-declared task controls against simple opaque author-created fixed/sticky "
    "DOM rectangles in the named browser/profile/state; no keyboard, virtual-keyboard, assistive-technology, "
    "or WCAG conformance claim."
)


class V7EvidenceError(ValueError):
    """Raised when v7 evidence is incomplete, stale or inconsistent."""


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 4 * 1024 * 1024:
        raise V7EvidenceError(f"{label} is missing, unsafe or oversized")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise V7EvidenceError(f"cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise V7EvidenceError(f"{label} root must be an object")
    return value


def _safe_child(root: Path, name: Any, suffix: str, label: str) -> Path:
    if not isinstance(name, str) or Path(name).name != name or not name.endswith(suffix) or "\x00" in name:
        raise V7EvidenceError(f"{label} path is invalid")
    path = root / name
    if not path.is_file() or path.is_symlink() or path.resolve().parent != root:
        raise V7EvidenceError(f"{label} is missing or unsafe")
    return path


def _key(variant: str, case_id: str, state: str, profile: str, engine: str) -> tuple[str, str, str, str, str]:
    return variant, case_id, state, profile, engine


def artifact_stem(key: tuple[str, str, str, str, str]) -> str:
    return "--".join(key)


def expected_inventory(
    manifest: dict[str, Any],
    split: str,
    gate: str = "full",
) -> list[tuple[str, str, str, str, str]]:
    if gate not in GATES:
        raise V7EvidenceError(f"unknown visual gate: {gate}")
    splits = manifest.get("splits")
    if not isinstance(splits, dict) or split not in splits or not isinstance(splits[split], list):
        raise V7EvidenceError(f"unknown split: {split}")
    inventory: set[tuple[str, str, str, str, str]] = set()
    for case in splits[split]:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise V7EvidenceError("manifest split contains an invalid case")
        states = case.get("required_states")
        if set(states) != {"base", "interaction"}:
            raise V7EvidenceError(f"case {case['id']} must freeze base and interaction states")
        for variant in VARIANTS:
            if gate == "fast":
                for state in ("base", "interaction"):
                    for profile in FAST_PROFILES:
                        inventory.add(_key(variant, case["id"], state, profile, "chromium"))
            else:
                for profile in BASE_PROFILES:
                    inventory.add(_key(variant, case["id"], "base", profile, "chromium"))
                for profile in PARITY_PROFILES:
                    for engine in PARITY_ENGINES:
                        inventory.add(_key(variant, case["id"], "interaction", profile, engine))
    return sorted(inventory)


def _validate_timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.endswith("Z") or len(value) != 20:
        raise V7EvidenceError(f"{label} must be canonical UTC")
    return value


def _validate_focus_evidence(
    runtime: dict[str, Any],
    label: str,
    result_schema: int,
) -> tuple[bool, bool, set[str]]:
    """Validate optional spec-v2 focus evidence and return blocking finding/unavailable flags."""

    has_coverage = "focusCoverage" in runtime
    has_controls = "focusedControls" in runtime
    if has_coverage != has_controls:
        raise V7EvidenceError(f"focus evidence is incomplete for {label}")
    if not has_coverage:
        return False, False, set()
    coverage = runtime["focusCoverage"]
    controls = runtime["focusedControls"]
    coverage_keys = {
        "status", "reason", "declaredTargets", "completedTargets", "freshReplays", "claimBoundary",
    }
    if not isinstance(coverage, dict) or set(coverage) != coverage_keys or not isinstance(controls, list):
        raise V7EvidenceError(f"focus evidence schema changed for {label}")
    if coverage.get("status") not in {"complete", "unavailable"}:
        raise V7EvidenceError(f"focus coverage status is invalid for {label}")
    if coverage.get("claimBoundary") != FOCUS_CLAIM_BOUNDARY:
        raise V7EvidenceError(f"focus claim boundary changed for {label}")
    for field in ("declaredTargets", "completedTargets", "freshReplays"):
        value = coverage.get(field)
        if type(value) is not int or value < 0:
            raise V7EvidenceError(f"focus coverage counts are invalid for {label}")
    declared = coverage["declaredTargets"]
    completed = coverage["completedTargets"]
    replays = coverage["freshReplays"]
    if declared > 8 or completed > declared or replays > declared * 2 or len(controls) != declared:
        raise V7EvidenceError(f"focus coverage bounds changed for {label}")
    ids: set[str] = set()
    completed_records = 0
    confirmed = 0
    unavailable = 0
    confirmed_click_candidate_steps: set[str] = set()
    step_ids: set[str] = set()
    for record in controls:
        if not isinstance(record, dict):
            raise V7EvidenceError(f"focused control record is malformed for {label}")
        status = record.get("status")
        expected_keys = (
            {"id", "role", "status", "fullyObscured", "replays", "reason"}
            if status == "unavailable"
            else {"id", "role", "status", "fullyObscured", "replays", "occluderCount", "targetArea", "coveredArea"}
        )
        if result_schema == 3:
            expected_keys = expected_keys | {"stepId"}
        if set(record) != expected_keys:
            raise V7EvidenceError(f"focused control record schema changed for {label}")
        control_id = record.get("id")
        if not isinstance(control_id, str) or RECORD_ID.fullmatch(control_id) is None or control_id in ids:
            raise V7EvidenceError(f"focused control id is invalid or duplicated for {label}")
        ids.add(control_id)
        if result_schema == 3:
            step_id = record.get("stepId")
            if not isinstance(step_id, str) or RECORD_ID.fullmatch(step_id) is None or step_id in step_ids:
                raise V7EvidenceError(f"focused control step id is invalid or duplicated for {label}")
            step_ids.add(step_id)
        if record.get("role") not in {"form-control", "primary-action"}:
            raise V7EvidenceError(f"focused control role is invalid for {label}")
        if status not in {"clear", "confirmed", "unavailable"} or type(record.get("fullyObscured")) is not bool:
            raise V7EvidenceError(f"focused control status is invalid for {label}")
        if record.get("replays") != 2:
            raise V7EvidenceError(f"focused control replay count is invalid for {label}")
        if status == "unavailable":
            reason = record.get("reason")
            if (
                record["fullyObscured"] is not False
                or not isinstance(reason, str)
                or RECORD_ID.fullmatch(reason.replace("_", "-")) is None
            ):
                raise V7EvidenceError(f"focused control unavailable record is invalid for {label}")
            unavailable += 1
            continue
        if record["replays"] != 2 or record["fullyObscured"] is not (status == "confirmed"):
            raise V7EvidenceError(f"focused control confirmation is inconsistent for {label}")
        count = record.get("occluderCount")
        target_area = record.get("targetArea")
        covered_area = record.get("coveredArea")
        if (
            type(count) is not int
            or not 0 <= count <= 12
            or isinstance(target_area, bool)
            or not isinstance(target_area, (int, float))
            or not math.isfinite(target_area)
            or target_area <= 0
            or isinstance(covered_area, bool)
            or not isinstance(covered_area, (int, float))
            or not math.isfinite(covered_area)
            or not 0 <= covered_area <= target_area + 1
        ):
            raise V7EvidenceError(f"focused control geometry is invalid for {label}")
        if status == "confirmed" and (count < 1 or abs(covered_area - target_area) > 1):
            raise V7EvidenceError(f"focused control obscuration is not fully covered for {label}")
        if status == "clear" and covered_area >= target_area:
            raise V7EvidenceError(f"clear focused control is fully covered for {label}")
        completed_records += 1
        confirmed += int(status == "confirmed")
        if status == "confirmed" and result_schema == 3 and record["role"] == "primary-action":
            confirmed_click_candidate_steps.add(record["stepId"])
    if completed != completed_records:
        raise V7EvidenceError(f"focus completed target count changed for {label}")
    status = coverage["status"]
    reason = coverage["reason"]
    if declared == 0:
        raise V7EvidenceError(f"focus coverage must declare at least one target for {label}")
    if replays != declared * 2:
        raise V7EvidenceError(f"focus replay inventory is incomplete for {label}")
    if unavailable:
        if status != "unavailable" or reason != "one_or_more_targets_unavailable":
            raise V7EvidenceError(f"unavailable focus coverage is inconsistent for {label}")
    elif status != "complete" or reason is not None or completed != declared or replays != declared * 2:
        raise V7EvidenceError(f"complete focus coverage is inconsistent for {label}")
    return confirmed > 0, unavailable > 0, confirmed_click_candidate_steps


def _validate_result(
    key: tuple[str, str, str, str, str],
    result_path: Path,
    screenshot_path: Path,
    expected_result_hash: Any,
    expected_screenshot_hash: Any,
    expected_spec_hash: str | None = None,
    expected_playwright: str | None = None,
) -> str:
    if not isinstance(expected_result_hash, str) or SHA256.fullmatch(expected_result_hash) is None:
        raise V7EvidenceError("result SHA-256 is invalid")
    if not isinstance(expected_screenshot_hash, str) or SHA256.fullmatch(expected_screenshot_hash) is None:
        raise V7EvidenceError("screenshot SHA-256 is invalid")
    if _digest(result_path) != expected_result_hash or _digest(screenshot_path) != expected_screenshot_hash:
        raise V7EvidenceError(f"artifact hash is stale for {artifact_stem(key)}")
    try:
        media_type, width, height = screenshot_metadata(screenshot_path.read_bytes())
    except (OSError, LedgerError) as error:
        raise V7EvidenceError(f"screenshot is not a complete decodable PNG: {artifact_stem(key)}: {error}") from error
    evidence = _load(result_path, f"result {artifact_stem(key)}")
    input_record = evidence.get("input")
    if not isinstance(input_record, dict) or set(input_record) != {"scheme", "route", "specSha256"}:
        raise V7EvidenceError(f"result input schema changed for {artifact_stem(key)}")
    if not isinstance(input_record.get("specSha256"), str) or SHA256.fullmatch(input_record["specSha256"]) is None:
        raise V7EvidenceError(f"result spec digest is invalid for {artifact_stem(key)}")
    if expected_spec_hash is not None and input_record["specSha256"] != expected_spec_hash:
        raise V7EvidenceError(f"result spec digest drifted for {artifact_stem(key)}")
    identity = evidence.get("identity")
    expected_identity = {
        "variant": key[0],
        "caseId": key[1],
        "state": key[2],
        "profile": key[3],
        "engine": key[4],
    }
    if set(evidence) != {"schemaVersion", "identity", "input", "browser", "runtime", "typography", "verdict", "screenshot"}:
        raise V7EvidenceError(f"result root schema changed for {artifact_stem(key)}")
    result_schema = evidence.get("schemaVersion")
    if type(result_schema) is not int or result_schema not in {1, 2, 3} or identity != expected_identity:
        raise V7EvidenceError(f"result identity changed for {artifact_stem(key)}")
    if result_schema == 3 and key[2] != "interaction":
        raise V7EvidenceError(f"result schema 3 is reserved for blocked interaction evidence: {artifact_stem(key)}")
    if evidence.get("verdict") not in {"clean", "findings"}:
        raise V7EvidenceError(f"result verdict is invalid for {artifact_stem(key)}")
    screenshot = evidence.get("screenshot")
    if not isinstance(screenshot, dict) or set(screenshot) != {"path", "fullPage", "width", "height", "bytes", "sha256"} or screenshot.get("path") != screenshot_path.name:
        raise V7EvidenceError(f"result screenshot path changed for {artifact_stem(key)}")
    if (
        media_type != "image/png"
        or screenshot.get("sha256") != expected_screenshot_hash
        or screenshot.get("bytes") != screenshot_path.stat().st_size
        or screenshot.get("width") != width
        or screenshot.get("height") != height
    ):
        raise V7EvidenceError(f"result screenshot metadata is stale for {artifact_stem(key)}")
    browser = evidence.get("browser")
    profile = browser.get("profile") if isinstance(browser, dict) else None
    if not isinstance(browser, dict) or set(browser) != {"playwright", "engineVersion", "profile"}:
        raise V7EvidenceError(f"browser schema changed for {artifact_stem(key)}")
    if expected_playwright is not None and browser.get("playwright") != expected_playwright:
        raise V7EvidenceError(f"Playwright version drifted for {artifact_stem(key)}")
    if not isinstance(browser.get("engineVersion"), str) or not browser["engineVersion"]:
        raise V7EvidenceError(f"browser engine version is missing for {artifact_stem(key)}")
    if not isinstance(profile, dict) or set(profile) != {
        "width", "height", "deviceScaleFactor", "hasTouch", "isMobile", "fullMobileEmulation", "userAgent",
    }:
        raise V7EvidenceError(f"browser profile is missing for {artifact_stem(key)}")
    expected_profile = PROFILE_CONTRACTS[key[3]]
    if any(profile.get(field) != value for field, value in expected_profile.items()):
        raise V7EvidenceError(f"browser profile contract changed for {artifact_stem(key)}")
    if not isinstance(profile.get("userAgent"), str) or not profile["userAgent"]:
        raise V7EvidenceError(f"browser user agent is missing for {artifact_stem(key)}")
    if key[3] in {"mobile", "compact-mobile"}:
        if profile.get("hasTouch") is not True or profile.get("deviceScaleFactor") != 3:
            raise V7EvidenceError(f"mobile emulation signals are incomplete for {artifact_stem(key)}")
        expected_full = key[4] != "firefox"
        if profile.get("fullMobileEmulation") is not expected_full:
            raise V7EvidenceError(f"mobile engine support claim is wrong for {artifact_stem(key)}")
    runtime = evidence.get("runtime")
    typography = evidence.get("typography")
    base_runtime_keys = {
        "fontsReady", "interactions", "assertions", "consoleErrors", "pageErrors",
        "externalRequests", "pageBounds", "devicePixelArea", "horizontalOverflow", "eventOverflow",
        "eventCounts", "issues",
    }
    expected_runtime_keys = (
        base_runtime_keys
        if result_schema == 1
        else base_runtime_keys | {"focusCoverage", "focusedControls"}
    )
    if not isinstance(runtime, dict) or set(runtime) != expected_runtime_keys:
        raise V7EvidenceError(f"runtime schema changed for {artifact_stem(key)}")
    if not isinstance(typography, dict) or set(typography) != {
        "schemaVersion", "issues", "observations", "targets", "environment",
    } or typography.get("schemaVersion") != 1 or not isinstance(typography.get("issues"), list):
        raise V7EvidenceError(f"typography result is missing for {artifact_stem(key)}")
    array_fields = ("interactions", "assertions", "consoleErrors", "pageErrors", "externalRequests", "issues")
    if any(not isinstance(runtime.get(field), list) for field in array_fields):
        raise V7EvidenceError(f"runtime arrays are malformed for {artifact_stem(key)}")
    focus_blocking, focus_unavailable, confirmed_click_candidate_steps = _validate_focus_evidence(
        runtime, artifact_stem(key), result_schema,
    )
    if key[2] == "interaction" and (not runtime["interactions"] or not runtime["assertions"]):
        raise V7EvidenceError(f"interaction evidence must record at least one step and one assertion for {artifact_stem(key)}")
    if key[2] == "interaction":
        interaction_ids: list[str] = []
        blocked_index: int | None = None
        for index, item in enumerate(runtime["interactions"]):
            base_valid = (
                isinstance(item, dict)
                and isinstance(item.get("id"), str)
                and RECORD_ID.fullmatch(item["id"]) is not None
                and item.get("action") in {"click", "fill", "select", "press"}
                and type(item.get("completed")) is bool
            )
            if not base_valid:
                raise V7EvidenceError(f"interaction step evidence is malformed for {artifact_stem(key)}")
            if result_schema != 3:
                if set(item) != {"id", "action", "completed"} or item["completed"] is not True:
                    raise V7EvidenceError(f"interaction step evidence is malformed for {artifact_stem(key)}")
            elif item["completed"] is True:
                if set(item) != {"id", "action", "completed"} or blocked_index is not None:
                    raise V7EvidenceError(f"completed interaction appears after a blocked step for {artifact_stem(key)}")
                if item["action"] == "click" and item["id"] in confirmed_click_candidate_steps:
                    raise V7EvidenceError(f"confirmed obscured click was marked completed for {artifact_stem(key)}")
            else:
                if set(item) != {"id", "action", "completed", "reason"}:
                    raise V7EvidenceError(f"incomplete interaction evidence is malformed for {artifact_stem(key)}")
                reason = item.get("reason")
                if blocked_index is None:
                    if reason != "focused_control_obscured" or item["action"] != "click":
                        raise V7EvidenceError(f"blocked interaction reason is invalid for {artifact_stem(key)}")
                    blocked_index = index
                elif reason != "prior_step_not_completed":
                    raise V7EvidenceError(f"dependent interaction reason is invalid for {artifact_stem(key)}")
            interaction_ids.append(item["id"])
        assertion_ids: list[str] = []
        for item in runtime["assertions"]:
            common_valid = (
                isinstance(item, dict)
                and isinstance(item.get("id"), str)
                and RECORD_ID.fullmatch(item["id"]) is not None
                and item.get("type") in {"visible", "hidden", "text"}
            )
            if not common_valid:
                raise V7EvidenceError(f"interaction assertion evidence is malformed for {artifact_stem(key)}")
            if result_schema == 3:
                if (
                    set(item) != {"id", "type", "evaluated", "reason"}
                    or item.get("evaluated") is not False
                    or item.get("reason") != "interaction_state_unavailable"
                ):
                    raise V7EvidenceError(f"unevaluated assertion evidence is malformed for {artifact_stem(key)}")
            elif (
                set(item) != {"id", "type", "count", "passed"}
                or isinstance(item.get("count"), bool)
                or not isinstance(item.get("count"), int)
                or item["count"] < 0
                or type(item.get("passed")) is not bool
            ):
                raise V7EvidenceError(f"interaction assertion evidence is malformed for {artifact_stem(key)}")
            assertion_ids.append(item["id"])
        if len(interaction_ids) != len(set(interaction_ids)) or len(assertion_ids) != len(set(assertion_ids)):
            raise V7EvidenceError(f"interaction evidence ids must be unique for {artifact_stem(key)}")
        if result_schema == 3:
            if (
                blocked_index is None
                or runtime["interactions"][blocked_index]["id"] not in confirmed_click_candidate_steps
                or not focus_blocking
                or focus_unavailable
            ):
                raise V7EvidenceError(f"blocked interaction is not bound to complete focus evidence for {artifact_stem(key)}")
    if type(runtime.get("fontsReady")) is not bool or type(runtime.get("horizontalOverflow")) is not bool or type(runtime.get("eventOverflow")) is not bool:
        raise V7EvidenceError(f"runtime flags are malformed for {artifact_stem(key)}")
    page_bounds = runtime.get("pageBounds")
    if not isinstance(page_bounds, dict) or set(page_bounds) != {"width", "height"} or any(type(page_bounds[field]) is not int or page_bounds[field] < 1 for field in page_bounds):
        raise V7EvidenceError(f"page bounds are malformed for {artifact_stem(key)}")
    if runtime["horizontalOverflow"] != (page_bounds["width"] > expected_profile["width"] + 2):
        raise V7EvidenceError(f"overflow derivation changed for {artifact_stem(key)}")
    expected_area = page_bounds["width"] * page_bounds["height"] * expected_profile["deviceScaleFactor"] ** 2
    if runtime.get("devicePixelArea") != expected_area:
        raise V7EvidenceError(f"device pixel area changed for {artifact_stem(key)}")
    counts = runtime.get("eventCounts")
    if not isinstance(counts, dict) or set(counts) != {"consoleErrors", "pageErrors", "externalRequests"}:
        raise V7EvidenceError(f"runtime event counts are malformed for {artifact_stem(key)}")
    if any(type(value) is not int or value < 0 for value in counts.values()):
        raise V7EvidenceError(f"runtime event counts are invalid for {artifact_stem(key)}")
    if runtime["eventOverflow"] != any(value > 50 for value in counts.values()):
        raise V7EvidenceError(f"runtime event overflow changed for {artifact_stem(key)}")
    expected_runtime_issues = [
        *(["page_horizontal_overflow"] if runtime["horizontalOverflow"] else []),
        *(["page_capture_area_exceeded"] if screenshot.get("fullPage") is not True else []),
        *(["runtime_event_limit_exceeded"] if runtime["eventOverflow"] else []),
        *(["focused_control_obscured"] if focus_blocking else []),
        *(["focus_obscuration_verification_unavailable"] if focus_unavailable else []),
    ]
    if runtime.get("issues") != expected_runtime_issues:
        raise V7EvidenceError(f"runtime issue derivation changed for {artifact_stem(key)}")
    assertions_pass = result_schema != 3 and all(
        isinstance(item, dict) and item.get("passed") is True for item in runtime["assertions"]
    )
    recomputed_clean = (
        runtime.get("fontsReady") is True
        and screenshot.get("fullPage") is True
        and runtime.get("horizontalOverflow") is False
        and runtime.get("eventOverflow") is False
        and not focus_blocking
        and not focus_unavailable
        and assertions_pass
        and runtime["consoleErrors"] == []
        and runtime["pageErrors"] == []
        and runtime["externalRequests"] == []
        and typography["issues"] == []
    )
    capture_width = page_bounds["width"] if screenshot.get("fullPage") is True else expected_profile["width"]
    capture_height = page_bounds["height"] if screenshot.get("fullPage") is True else expected_profile["height"]
    if screenshot.get("width") != capture_width * expected_profile["deviceScaleFactor"] or screenshot.get("height") != capture_height * expected_profile["deviceScaleFactor"]:
        raise V7EvidenceError(f"screenshot dimensions disagree with capture geometry for {artifact_stem(key)}")
    expected_verdict = "clean" if recomputed_clean else "findings"
    if evidence.get("verdict") != expected_verdict:
        raise V7EvidenceError(f"result verdict does not match frozen evidence predicate for {artifact_stem(key)}")
    return str(evidence["verdict"])


def validate(
    manifest_path: Path,
    ledger_path: Path,
    result_dir: Path,
    screenshot_dir: Path,
    repository_root: Path,
    gate: str = "full",
) -> tuple[int, int]:
    root = repository_root.resolve(strict=True)
    preflight.validate_manifest(manifest_path, root)
    manifest = _load(manifest_path, "cohort manifest")
    ledger = _load(ledger_path, "visual ledger")
    if set(ledger) != LEDGER_KEYS or ledger.get("schema_version") != 1 or ledger.get("status") != "completed":
        raise V7EvidenceError("visual ledger root is incomplete or invalid")
    manifest_record = ledger.get("cohort_manifest")
    if manifest_record != {"path": manifest_path.relative_to(root).as_posix(), "sha256": _digest(manifest_path)}:
        raise V7EvidenceError("visual ledger is not bound to the current cohort manifest")
    split = ledger.get("split")
    if not isinstance(split, str):
        raise V7EvidenceError("visual ledger split is invalid")
    if ledger.get("gate") != gate:
        raise V7EvidenceError("visual ledger gate does not match requested gate")
    expected = expected_inventory(manifest, split, gate)
    if ledger.get("variants") != list(VARIANTS) or ledger.get("expected_count") != len(expected):
        raise V7EvidenceError("visual ledger inventory contract changed")
    if not isinstance(ledger.get("hidden_matrix_sha256"), str) or SHA256.fullmatch(ledger["hidden_matrix_sha256"]) is None:
        raise V7EvidenceError("hidden matrix digest is missing")
    if not isinstance(ledger.get("input_inventory_sha256"), str) or SHA256.fullmatch(ledger["input_inventory_sha256"]) is None:
        raise V7EvidenceError("input inventory digest is missing")
    attempts = ledger.get("attempts")
    if not isinstance(attempts, list) or len(attempts) != len(expected):
        raise V7EvidenceError("visual ledger attempt inventory is incomplete")
    if not result_dir.is_dir() or result_dir.is_symlink() or not screenshot_dir.is_dir() or screenshot_dir.is_symlink():
        raise V7EvidenceError("artifact directories are missing or unsafe")
    result_root = result_dir.resolve(strict=True)
    screenshot_root = screenshot_dir.resolve(strict=True)
    seen: set[tuple[str, str, str, str, str]] = set()
    finding_count = 0
    expected_result_names: set[str] = set()
    expected_screenshot_names: set[str] = set()
    for record in attempts:
        if not isinstance(record, dict) or set(record) != {"key", "attempts"}:
            raise V7EvidenceError("attempt record is malformed")
        identity = record["key"]
        if not isinstance(identity, dict) or set(identity) != {"variant", "case_id", "state", "profile", "engine"}:
            raise V7EvidenceError("attempt identity is malformed")
        key = _key(identity["variant"], identity["case_id"], identity["state"], identity["profile"], identity["engine"])
        if key not in expected or key in seen:
            raise V7EvidenceError(f"unexpected or duplicate attempt identity: {artifact_stem(key)}")
        seen.add(key)
        history = record["attempts"]
        if not isinstance(history, list) or not 1 <= len(history) <= 3:
            raise V7EvidenceError(f"attempt history must preserve 1..3 tries: {artifact_stem(key)}")
        completed = []
        for index, attempt in enumerate(history, start=1):
            if not isinstance(attempt, dict) or attempt.get("number") != index:
                raise V7EvidenceError(f"attempt numbering is invalid: {artifact_stem(key)}")
            _validate_timestamp(attempt.get("started_at"), "started_at")
            _validate_timestamp(attempt.get("finished_at"), "finished_at")
            status = attempt.get("status")
            if status == "infrastructure_failure":
                if set(attempt) != {"number", "started_at", "finished_at", "status", "exit_code", "failure_class"}:
                    raise V7EvidenceError(f"failure attempt contract is invalid: {artifact_stem(key)}")
            elif status == "completed":
                if set(attempt) != {
                    "number", "started_at", "finished_at", "status", "exit_code",
                    "result", "result_sha256", "screenshot", "screenshot_sha256",
                    "route_sha256", "spec_sha256",
                }:
                    raise V7EvidenceError(f"completed attempt contract is invalid: {artifact_stem(key)}")
                completed.append(attempt)
            else:
                raise V7EvidenceError(f"attempt status is invalid: {artifact_stem(key)}")
        if len(completed) != 1 or completed[0] is not history[-1]:
            raise V7EvidenceError(f"attempt history must end in exactly one completion: {artifact_stem(key)}")
        final = completed[0]
        if final["exit_code"] not in {0, 2}:
            raise V7EvidenceError(f"completed audit exit code is invalid: {artifact_stem(key)}")
        expected_result_name = f"{artifact_stem(key)}.json"
        expected_screenshot_name = f"{artifact_stem(key)}.png"
        if final["result"] != expected_result_name or final["screenshot"] != expected_screenshot_name:
            raise V7EvidenceError(f"artifact names changed for {artifact_stem(key)}")
        expected_result_names.add(expected_result_name)
        expected_screenshot_names.add(expected_screenshot_name)
        result_path = _safe_child(result_root, final["result"], ".json", "result")
        screenshot_path = _safe_child(screenshot_root, final["screenshot"], ".png", "screenshot")
        for digest_key in ("route_sha256", "spec_sha256"):
            if not isinstance(final[digest_key], str) or SHA256.fullmatch(final[digest_key]) is None:
                raise V7EvidenceError(f"input digest is invalid for {artifact_stem(key)}")
        verdict = _validate_result(
            key,
            result_path,
            screenshot_path,
            final["result_sha256"],
            final["screenshot_sha256"],
            final["spec_sha256"],
            manifest["toolchain"]["packages"]["playwright"]["version"],
        )
        if (verdict == "clean") != (final["exit_code"] == 0):
            raise V7EvidenceError(f"exit code and verdict disagree for {artifact_stem(key)}")
        finding_count += int(verdict == "findings")
    if seen != set(expected):
        raise V7EvidenceError("visual ledger is missing expected identities")
    actual_results = {path.name for path in result_root.iterdir() if path.is_file() and not path.is_symlink()}
    actual_screenshots = {path.name for path in screenshot_root.iterdir() if path.is_file() and not path.is_symlink()}
    if actual_results != expected_result_names or actual_screenshots != expected_screenshot_names:
        raise V7EvidenceError("artifact directories contain missing, stale or extra files")
    return len(expected), finding_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--result-dir", required=True, type=Path)
    parser.add_argument("--screenshot-dir", required=True, type=Path)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    parser.add_argument("--gate", choices=GATES, default="full")
    args = parser.parse_args()
    try:
        count, findings = validate(
            args.manifest.resolve(strict=True),
            args.ledger.resolve(strict=True),
            args.result_dir.resolve(strict=True),
            args.screenshot_dir.resolve(strict=True),
            args.repository_root.resolve(strict=True),
            args.gate,
        )
    except (OSError, V7EvidenceError, preflight.PreflightError) as error:
        print(f"v7 evidence invalid: {error}", file=sys.stderr)
        return 1
    print(f"v7 evidence valid: {count} screenshots, {findings} finding runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
