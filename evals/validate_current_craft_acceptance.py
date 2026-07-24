#!/usr/bin/env python3
"""Bind current-run craft acceptance to fresh Playwright evidence and frozen case provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "wow-frontend-design" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import evidence_ledger  # noqa: E402
import validate_quality_result  # noqa: E402


MAX_JSON_BYTES = 2_000_000
MAX_CAPTURE_BYTES = 8_000_000
MAX_TOTAL_CAPTURE_BYTES = 64_000_000
HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
PACKAGE_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?$")
CORE_CRAFT = validate_quality_result.VERIFIED_CORE_CRAFT_DIMENSIONS
PROFILE_STANDARD = [
    {"name": "desktop-default", "viewport": {"width": 1440, "height": 1000}, "reducedMotion": "no-preference", "dpr": 1},
    {"name": "mobile-default", "viewport": {"width": 390, "height": 844}, "reducedMotion": "reduce", "dpr": 1},
]
CASE_KEYS = {"schema_version", "case_id", "run_id", "partition", "brief", "capture_plan", "craft"}
RECEIPT_KEYS = {"schema_version", "status", "case", "source", "runtime", "capture_standard", "captures"}
CAPTURE_KEYS = {
    "label", "page", "profile", "path", "bytes", "sha256", "width", "height", "captured_at", "context"
}


class CurrentCraftError(ValueError):
    """Raised when current-run craft evidence is stale, incomplete, or outside policy."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_JSON_BYTES:
        raise CurrentCraftError(f"{label} must be a bounded regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CurrentCraftError(f"{label} is not valid JSON: {error}") from error
    if not isinstance(value, dict):
        raise CurrentCraftError(f"{label} must be an object")
    return value


def _repository_playwright_version() -> str:
    package = _load_json(ROOT / "package.json", "repository package manifest")
    dependencies = package.get("devDependencies")
    version = dependencies.get("playwright") if isinstance(dependencies, dict) else None
    if not isinstance(version, str) or PACKAGE_VERSION_PATTERN.fullmatch(version) is None:
        raise CurrentCraftError("repository Playwright dependency must use one exact version")
    return version


def _unaliased_file(path: Path, label: str) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        raise CurrentCraftError(f"{label} must be an unaliased regular file")
    try:
        info = expanded.lstat()
        canonical = expanded.resolve(strict=True)
    except OSError as error:
        raise CurrentCraftError(f"{label} must be an unaliased regular file") from error
    if (
        not stat.S_ISREG(info.st_mode)
        or expanded.is_symlink()
        or canonical != expanded
        or info.st_nlink != 1
    ):
        raise CurrentCraftError(f"{label} must be an unaliased regular file")
    return canonical


def _exact(value: object, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise CurrentCraftError(f"{label} must contain exactly {sorted(keys)}")
    return value


def _browser_contract_record(value: object, label: str) -> dict[str, Any]:
    record = _exact(
        value,
        {"schema_version", "bytes", "sha256", "case_count", "step_count"},
        label,
    )
    if (
        type(record["schema_version"]) is not int
        or record["schema_version"] not in {1, 2}
        or type(record["bytes"]) is not int
        or not 1 <= record["bytes"] <= MAX_JSON_BYTES
        or not isinstance(record["sha256"], str)
        or HASH_PATTERN.fullmatch(record["sha256"]) is None
        or type(record["case_count"]) is not int
        or not 1 <= record["case_count"] <= 4
        or type(record["step_count"]) is not int
        or not 1 <= record["step_count"] <= 96
    ):
        raise CurrentCraftError(f"{label} is invalid")
    return record


def _relative(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise CurrentCraftError(f"{label} must be a normalized relative path")
    candidate = Path(value)
    if candidate.is_absolute() or candidate.as_posix() != value or any(part in {"", ".", ".."} for part in candidate.parts):
        raise CurrentCraftError(f"{label} must be a normalized relative path")
    return value


def _png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise CurrentCraftError(f"capture is not a PNG: {path.name}")
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


def _outside_workspace(path: Path, workspace: Path, label: str) -> None:
    try:
        path.resolve(strict=True).relative_to(workspace)
    except ValueError:
        return
    raise CurrentCraftError(f"{label} must remain outside the model-writable workspace")


def _outside_authoring_repository(path: Path, label: str) -> None:
    repository = ROOT.resolve(strict=True)
    try:
        path.resolve(strict=True).relative_to(repository)
    except ValueError:
        return
    raise CurrentCraftError(f"{label} must remain outside the authoring repository")


def validate_current_capture_evidence(
    workspace_root: Path,
    case_path: Path,
    receipt_path: Path,
    manifest_path: Path,
    *,
    allow_draft_subset: bool = False,
) -> dict[str, Any]:
    try:
        return _validate_current_capture_evidence(
            workspace_root,
            case_path,
            receipt_path,
            manifest_path,
            allow_draft_subset=allow_draft_subset,
        )
    except CurrentCraftError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, AttributeError, KeyError) as error:
        raise CurrentCraftError(
            "current capture evidence is malformed or changed during validation"
        ) from error


def _validate_current_capture_evidence(
    workspace_root: Path,
    case_path: Path,
    receipt_path: Path,
    manifest_path: Path,
    *,
    allow_draft_subset: bool,
) -> dict[str, Any]:
    workspace = workspace_root.expanduser().resolve(strict=True)
    case_file = _unaliased_file(case_path, "case")
    receipt_file = _unaliased_file(receipt_path, "capture receipt")
    manifest_file = _unaliased_file(manifest_path, "run manifest")
    for path, label in ((case_file, "case"), (receipt_file, "capture receipt")):
        _outside_workspace(path, workspace, label)
        _outside_authoring_repository(path, label)
    try:
        manifest_file.relative_to(workspace)
    except ValueError as error:
        raise CurrentCraftError("run manifest must remain inside the current workspace") from error

    case_value = _load_json(case_file, "case")
    case_schema = case_value.get("schema_version")
    case_keys = CASE_KEYS | ({"browser_contract"} if case_schema in {2, 3} else set())
    case = _exact(case_value, case_keys, "case")
    receipt_value = _load_json(receipt_file, "capture receipt")
    receipt_schema = receipt_value.get("schema_version")
    receipt_keys = RECEIPT_KEYS.copy()
    if receipt_schema == 2:
        receipt_keys |= {"state_evidence"}
    elif receipt_schema == 3:
        receipt_keys |= {"motion_evidence"}
    receipt = _exact(receipt_value, receipt_keys, "capture receipt")
    manifest = _load_json(manifest_file, "run manifest")

    if (
        type(case["schema_version"]) is not int
        or case["schema_version"] not in {1, 2, 3}
        or not isinstance(case["case_id"], str)
        or not case["case_id"].strip()
    ):
        raise CurrentCraftError("case identity is invalid")
    if not isinstance(case["run_id"], str) or RUN_ID_PATTERN.fullmatch(case["run_id"]) is None:
        raise CurrentCraftError("case run_id is invalid")
    if not isinstance(case["partition"], str) or case["partition"] not in {"validation", "test"}:
        raise CurrentCraftError("current acceptance requires a validation or test case")
    case_brief = _exact(case["brief"], {"bytes", "sha256"}, "case.brief")
    if (
        not isinstance(case_brief["bytes"], int)
        or isinstance(case_brief["bytes"], bool)
        or case_brief["bytes"] < 1
        or not isinstance(case_brief["sha256"], str)
        or HASH_PATTERN.fullmatch(case_brief["sha256"]) is None
    ):
        raise CurrentCraftError("case brief provenance is invalid")
    craft_case = _exact(case["craft"], {"rubric_version", "required_dimensions", "feedback_policy"}, "case.craft")
    if (
        not isinstance(craft_case["rubric_version"], str)
        or not craft_case["rubric_version"].strip()
        or not isinstance(craft_case["required_dimensions"], list)
        or set(craft_case["required_dimensions"]) != CORE_CRAFT
        or craft_case["feedback_policy"] != "aggregate-failure-families-only"
    ):
        raise CurrentCraftError("case craft floor is not the current standard")
    capture_plan_keys = {"locale", "state", "pages", "wait_condition", "profiles"}
    if case_schema == 2:
        capture_plan_keys.add("consequential_state")
    elif case_schema == 3:
        capture_plan_keys.add("motion_sequence")
    capture_plan = _exact(
        case["capture_plan"],
        capture_plan_keys,
        "case.capture_plan",
    )
    selected_pages = capture_plan["pages"]
    explicit_pages: list[str] | None = None
    if selected_pages != "all_html_outputs":
        selection = _exact(
            selected_pages,
            {"policy", "paths"},
            "case.capture_plan.pages",
        )
        if (
            not allow_draft_subset
            or selection["policy"] != "draft_direction_subset"
            or not isinstance(selection["paths"], list)
            or not 2 <= len(selection["paths"]) <= 3
        ):
            raise CurrentCraftError(
                "case capture pages must be all_html_outputs outside draft calibration"
            )
        explicit_pages = [
            _relative(page, f"case.capture_plan.pages.paths[{index}]")
            for index, page in enumerate(selection["paths"])
        ]
        if (
            len(set(explicit_pages)) != len(explicit_pages)
            or any(not page.lower().endswith(".html") for page in explicit_pages)
            or any(
                len(Path(page).parts) != 2
                or Path(page).parts[0] != "directions"
                or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*\.html", Path(page).name) is None
                for page in explicit_pages
            )
        ):
            raise CurrentCraftError("draft capture pages must be unique directions HTML outputs")
    if (
        not isinstance(capture_plan["locale"], str)
        or capture_plan["locale"] not in {"zh-Hant", "en"}
        or capture_plan["state"] != "default"
        or capture_plan["wait_condition"] != "load+fonts+two-raf+300ms+two-raf"
        or capture_plan["profiles"] != PROFILE_STANDARD
    ):
        raise CurrentCraftError("case capture plan is not the current standard")
    consequential_state: dict[str, Any] | None = None
    motion_sequence: dict[str, Any] | None = None
    case_contract: dict[str, Any] | None = None
    if case_schema == 2:
        if explicit_pages is not None:
            raise CurrentCraftError(
                "consequential state evidence is unavailable for draft calibration"
            )
        consequential_state = _exact(
            capture_plan["consequential_state"],
            {"contract_case_id"},
            "case.capture_plan.consequential_state",
        )
        contract_case_id = consequential_state["contract_case_id"]
        if (
            not isinstance(contract_case_id, str)
            or re.fullmatch(r"[a-z][a-z0-9-]{0,47}", contract_case_id) is None
        ):
            raise CurrentCraftError("case consequential state is invalid")
        case_contract = _browser_contract_record(
            case["browser_contract"],
            "case.browser_contract",
        )
    elif case_schema == 3:
        if explicit_pages is not None:
            raise CurrentCraftError(
                "motion sequence evidence is unavailable for draft calibration"
            )
        motion_sequence = _exact(
            capture_plan["motion_sequence"],
            {
                "page",
                "motion_contract_case_id",
                "reduced_motion_contract_case_id",
                "offsets_ms",
            },
            "case.capture_plan.motion_sequence",
        )
        motion_page = _relative(
            motion_sequence["page"],
            "case.capture_plan.motion_sequence.page",
        )
        offsets = motion_sequence["offsets_ms"]
        if (
            not motion_page.lower().endswith(".html")
            or not isinstance(motion_sequence["motion_contract_case_id"], str)
            or re.fullmatch(
                r"[a-z][a-z0-9-]{0,47}",
                motion_sequence["motion_contract_case_id"],
            )
            is None
            or not isinstance(
                motion_sequence["reduced_motion_contract_case_id"],
                str,
            )
            or re.fullmatch(
                r"[a-z][a-z0-9-]{0,47}",
                motion_sequence["reduced_motion_contract_case_id"],
            )
            is None
            or motion_sequence["motion_contract_case_id"]
            == motion_sequence["reduced_motion_contract_case_id"]
            or not isinstance(offsets, list)
            or len(offsets) != 3
            or any(type(offset) is not int or not 50 <= offset <= 5000 for offset in offsets)
            or offsets != sorted(set(offsets))
        ):
            raise CurrentCraftError("case motion sequence is invalid")
        case_contract = _browser_contract_record(
            case["browser_contract"],
            "case.browser_contract",
        )

    if (
        type(receipt["schema_version"]) is not int
        or receipt["schema_version"] != case_schema
        or receipt["status"] != "captured"
    ):
        raise CurrentCraftError("capture receipt is not a completed current receipt")
    runtime = _exact(receipt["runtime"], {"package", "version", "browser", "browser_version", "headless"}, "capture receipt.runtime")
    if (
        runtime["package"] != "playwright"
        or not isinstance(runtime["version"], str)
        or runtime["version"] != _repository_playwright_version()
        or runtime["browser"] != "chromium"
        or not isinstance(runtime["browser_version"], str)
        or not runtime["browser_version"].strip()
        or runtime["headless"] is not True
    ):
        raise CurrentCraftError("capture runtime is not the current Playwright Chromium standard")
    capture_standard_keys = {"profiles", "screenshot_mode", "animations", "caret", "network"}
    if case_schema == 3:
        capture_standard_keys.add("motion_evidence_animations")
    capture_standard = _exact(
        receipt["capture_standard"],
        capture_standard_keys,
        "capture receipt.capture_standard",
    )
    expected_capture_standard = {
        "profiles": PROFILE_STANDARD,
        "screenshot_mode": "viewport",
        "animations": "disabled",
        "caret": "hide",
        "network": "local-output-only",
    }
    if case_schema == 3:
        expected_capture_standard["motion_evidence_animations"] = "allow"
    if capture_standard != expected_capture_standard:
        raise CurrentCraftError("capture receipt standard drifted")
    receipt_case = _exact(receipt["case"], {"case_id", "run_id", "partition", "case_sha256"}, "capture receipt.case")
    if receipt_case != {
        "case_id": case["case_id"],
        "run_id": case["run_id"],
        "partition": case["partition"],
        "case_sha256": _sha256(case_file),
    }:
        raise CurrentCraftError("capture receipt does not match the frozen case")

    if manifest.get("schema_version") != 2 or manifest.get("status") != "completed":
        raise CurrentCraftError("run manifest is not a completed current build")
    if explicit_pages is not None:
        manifest_case = _exact(manifest.get("case"), {"mode", "lane_contract"}, "manifest.case")
        mutation = _exact(
            manifest.get("mutation"),
            {"allowed_changes", "observed_changes", "preserved_directories"},
            "manifest.mutation",
        )
        verification = _exact(
            manifest.get("html_verification"),
            {"policy", "pages"},
            "manifest.html_verification",
        )
        expected_changes = {"DESIGN.md", *explicit_pages}
        if (
            manifest_case != {"mode": "retrofit", "lane_contract": "RETROFIT"}
            or not isinstance(manifest.get("seed_snapshot"), dict)
            or verification["policy"] != "draft_direction_subset"
            or verification["pages"] != explicit_pages
            or not isinstance(mutation["allowed_changes"], list)
            or set(mutation["allowed_changes"]) != expected_changes
            or len(mutation["allowed_changes"]) != len(expected_changes)
            or not isinstance(mutation["observed_changes"], list)
            or not set(explicit_pages) <= set(mutation["observed_changes"])
            or not set(mutation["observed_changes"]) <= expected_changes
            or type(mutation["preserved_directories"]) is not int
            or mutation["preserved_directories"] < 0
        ):
            raise CurrentCraftError(
                "draft capture subset is not bound to a seeded RETROFIT manifest"
            )
    source_keys = {"run_manifest_sha256", "brief", "skill_tree_sha256", "outputs"}
    if case_schema in {2, 3}:
        source_keys.add("browser_contract")
    source = _exact(receipt["source"], source_keys, "capture receipt.source")
    if source["run_manifest_sha256"] != _sha256(manifest_file):
        raise CurrentCraftError("run manifest changed after capture")
    if source["brief"] != case_brief or source["brief"] != manifest.get("brief"):
        raise CurrentCraftError("brief provenance disagrees across case, capture, and current build")
    if source["skill_tree_sha256"] != manifest.get("skill_snapshot", {}).get("tree_sha256"):
        raise CurrentCraftError("Skill snapshot provenance disagrees with the current build")
    if source["outputs"] != manifest.get("outputs") or not isinstance(source["outputs"], list):
        raise CurrentCraftError("output provenance disagrees with the current build")
    state_evidence: dict[str, Any] | None = None
    motion_evidence: dict[str, Any] | None = None
    if case_schema in {2, 3}:
        manifest_contract = _browser_contract_record(
            manifest.get("browser_contract"),
            "manifest.browser_contract",
        )
        receipt_contract = _browser_contract_record(
            source["browser_contract"],
            "capture receipt.source.browser_contract",
        )
        if case_contract != manifest_contract or case_contract != receipt_contract:
            raise CurrentCraftError(
                "browser contract provenance disagrees across case, capture, and current build"
            )
    if case_schema == 2:
        state_evidence = _exact(
            receipt["state_evidence"],
            {"contract_case_id", "page", "profile", "steps_executed", "status"},
            "capture receipt.state_evidence",
        )
        state_page = _relative(
            state_evidence["page"],
            "capture receipt.state_evidence.page",
        )
        if (
            state_evidence["contract_case_id"]
            != consequential_state["contract_case_id"]
            or not state_page.lower().endswith(".html")
            or state_evidence["profile"]
            not in {"desktop-default", "mobile-default"}
            or type(state_evidence["steps_executed"]) is not int
            or not 1 <= state_evidence["steps_executed"] <= case_contract["step_count"]
            or state_evidence["status"] != "passed"
        ):
            raise CurrentCraftError("consequential state evidence is invalid")
    elif case_schema == 3:
        motion_evidence = _exact(
            receipt["motion_evidence"],
            {
                "motion_contract",
                "reduced_motion_contract",
                "capture_labels",
                "claim_scope",
            },
            "capture receipt.motion_evidence",
        )
        motion_contract_evidence = _exact(
            motion_evidence["motion_contract"],
            {"contract_case_id", "steps_executed", "status"},
            "capture receipt.motion_evidence.motion_contract",
        )
        reduced_contract_evidence = _exact(
            motion_evidence["reduced_motion_contract"],
            {"contract_case_id", "steps_executed", "status"},
            "capture receipt.motion_evidence.reduced_motion_contract",
        )
        motion_labels = _exact(
            motion_evidence["capture_labels"],
            {"motion_sequence", "reduced_motion_static"},
            "capture receipt.motion_evidence.capture_labels",
        )
        claim_scope = _exact(
            motion_evidence["claim_scope"],
            {"observed", "not_certified"},
            "capture receipt.motion_evidence.claim_scope",
        )
        sequence_labels = motion_labels["motion_sequence"]
        reduced_label = motion_labels["reduced_motion_static"]
        if (
            motion_contract_evidence["contract_case_id"]
            != motion_sequence["motion_contract_case_id"]
            or reduced_contract_evidence["contract_case_id"]
            != motion_sequence["reduced_motion_contract_case_id"]
            or any(
                evidence["status"] != "passed"
                or type(evidence["steps_executed"]) is not int
                or not 1 <= evidence["steps_executed"] <= case_contract["step_count"]
                for evidence in (motion_contract_evidence, reduced_contract_evidence)
            )
            or not isinstance(sequence_labels, list)
            or len(sequence_labels) != 3
            or any(not isinstance(label, str) or not label for label in sequence_labels)
            or len(set(sequence_labels)) != 3
            or not isinstance(reduced_label, str)
            or not reduced_label
            or reduced_label in sequence_labels
            or claim_scope["observed"]
            != [
                "fresh-fixed-request-offset-viewport-frames",
                "fresh-reduced-motion-static-frame",
            ]
            or claim_scope["not_certified"]
            != [
                "timing",
                "easing",
                "spatial-continuity",
                "runtime-performance",
                "award-quality",
            ]
        ):
            raise CurrentCraftError("motion evidence is invalid")

    output_root = manifest_file.parent
    html_pages: set[str] = set()
    output_paths: set[str] = set()
    for index, record in enumerate(source["outputs"]):
        record = _exact(record, {"path", "bytes", "mode", "sha256"}, f"outputs[{index}]")
        relative = _relative(record["path"], f"outputs[{index}].path")
        if relative in output_paths:
            raise CurrentCraftError("current output paths must be unique")
        if (
            type(record["bytes"]) is not int
            or record["bytes"] < 1
            or not isinstance(record["mode"], str)
            or re.fullmatch(r"0[0-7]{3}", record["mode"]) is None
            or not isinstance(record["sha256"], str)
            or HASH_PATTERN.fullmatch(record["sha256"]) is None
        ):
            raise CurrentCraftError(f"current output provenance record is invalid: {relative}")
        output = _unaliased_file(output_root / relative, "current output")
        try:
            output.relative_to(output_root.resolve(strict=True))
        except ValueError as error:
            raise CurrentCraftError("current output escapes its workspace") from error
        if (
            output.stat().st_size != record["bytes"]
            or f"{stat.S_IMODE(output.stat().st_mode):04o}" != record["mode"]
            or _sha256(output) != record["sha256"]
        ):
            raise CurrentCraftError(f"current output changed after capture: {relative}")
        output_paths.add(relative)
        if relative.lower().endswith(".html"):
            html_pages.add(relative)

    capture_pages = html_pages if explicit_pages is None else set(explicit_pages)
    if not capture_pages <= html_pages:
        raise CurrentCraftError("case capture pages must exist in the current manifest")
    captures = receipt["captures"]
    if motion_sequence is not None and capture_pages != {motion_sequence["page"]}:
        raise CurrentCraftError("motion evidence requires exactly one selected HTML output")
    expected_capture_count = (
        len(capture_pages) * 2
        + (1 if state_evidence else 0)
        + (4 if motion_evidence else 0)
    )
    if (
        not isinstance(captures, list)
        or not captures
        or len(captures) != expected_capture_count
    ):
        raise CurrentCraftError("capture receipt must cover every selected HTML output at desktop and mobile")
    capture_labels: set[str] = set()
    capture_paths: set[str] = set()
    default_capture_matrix: set[tuple[str, str]] = set()
    state_capture_matrix: list[tuple[str, str, str]] = []
    motion_capture_matrix: list[tuple[str, str, str]] = []
    capture_artifacts: dict[str, Path] = {}
    total_bytes = 0
    evidence_root = receipt_file.parent.resolve(strict=True)
    for index, raw_capture in enumerate(captures):
        capture = _exact(raw_capture, CAPTURE_KEYS, f"captures[{index}]")
        label = capture["label"]
        if not isinstance(label, str) or not label or label in capture_labels:
            raise CurrentCraftError("capture labels must be unique non-empty strings")
        if (
            not isinstance(capture["page"], str)
            or not isinstance(capture["profile"], str)
            or type(capture["bytes"]) is not int
            or capture["bytes"] < 1
            or type(capture["width"]) is not int
            or capture["width"] < 1
            or type(capture["height"]) is not int
            or capture["height"] < 1
            or not isinstance(capture["sha256"], str)
            or HASH_PATTERN.fullmatch(capture["sha256"]) is None
        ):
            raise CurrentCraftError("capture provenance fields are invalid")
        relative = _relative(capture["path"], f"captures[{index}].path")
        if relative in capture_paths:
            raise CurrentCraftError("capture paths must be unique")
        candidate = evidence_root / relative
        artifact = _unaliased_file(candidate, "capture artifact")
        try:
            artifact.relative_to(evidence_root)
        except ValueError as error:
            raise CurrentCraftError("capture artifact is outside the evaluator evidence root") from error
        if artifact != candidate or not artifact.is_file():
            raise CurrentCraftError(f"capture artifact must be an unaliased regular file: {relative}")
        info = artifact.stat()
        if info.st_nlink != 1:
            raise CurrentCraftError(f"capture artifact must have one filesystem identity: {relative}")
        size = info.st_size
        if size != capture["bytes"] or size > MAX_CAPTURE_BYTES or _sha256(artifact) != capture["sha256"]:
            raise CurrentCraftError(f"capture artifact provenance is invalid: {relative}")
        width, height = _png_dimensions(artifact)
        if (width, height) != (capture["width"], capture["height"]):
            raise CurrentCraftError(f"capture dimensions are invalid: {relative}")
        context = _exact(
            capture["context"],
            {"route", "state", "locale", "viewport", "dpr", "reduced_motion", "wait_condition"},
            f"captures[{index}].context",
        )
        if type(context["dpr"]) is not int or context["dpr"] < 1:
            raise CurrentCraftError("capture context numeric fields are invalid")
        profile = capture["profile"]
        profile_rule = next((item for item in PROFILE_STANDARD if item["name"] == profile), None)
        if profile == "desktop-motion":
            profile_rule = {
                "name": profile,
                "viewport": {"width": 1440, "height": 1000},
                "reducedMotion": "no-preference",
                "dpr": 1,
            }
        elif profile in {"mobile-motion", "mobile-reduced-static"}:
            profile_rule = {
                "name": profile,
                "viewport": {"width": 390, "height": 844},
                "reducedMotion": (
                    "no-preference"
                    if profile == "mobile-motion"
                    else "reduce"
                ),
                "dpr": 1,
            }
        expected_viewport = (
            f"{profile_rule['viewport']['width']}x{profile_rule['viewport']['height']}"
            if profile_rule else None
        )
        try:
            captured_at = datetime.fromisoformat(capture["captured_at"].replace("Z", "+00:00"))
        except (AttributeError, ValueError) as error:
            raise CurrentCraftError("capture timestamp is invalid") from error
        if context["route"] != f"/{capture['page']}":
            raise CurrentCraftError("capture route does not match its declared page")
        is_state_capture = context["state"] != capture_plan["state"]
        expected_state = (
            f"contract:{state_evidence['contract_case_id']}"
            if state_evidence
            else None
        )
        motion_states = (
            {
                f"contract:{motion_sequence['motion_contract_case_id']}:motion-{offset}ms":
                f"post-trigger+{offset}ms"
                for offset in motion_sequence["offsets_ms"]
            }
            if motion_sequence
            else {}
        )
        reduced_state = (
            f"contract:{motion_sequence['reduced_motion_contract_case_id']}:reduced-static"
            if motion_sequence
            else None
        )
        is_motion_capture = context["state"] in motion_states
        is_reduced_capture = context["state"] == reduced_state
        if (
            capture["page"] not in capture_pages
            or expected_viewport is None
            or context["viewport"] != expected_viewport
            or context["dpr"] != 1
            or context["locale"] != capture_plan["locale"]
            or (
                is_state_capture
                and not is_motion_capture
                and not is_reduced_capture
                and (
                    expected_state is None
                    or context["state"] != expected_state
                    or capture["page"] != state_evidence["page"]
                    or profile != state_evidence["profile"]
                )
            )
            or (
                not is_state_capture
                and context["state"] != capture_plan["state"]
            )
            or (
                not is_motion_capture
                and not is_reduced_capture
                and context["wait_condition"] != capture_plan["wait_condition"]
            )
            or (
                is_motion_capture
                and (
                    profile not in {"desktop-motion", "mobile-motion"}
                    or context["wait_condition"] != motion_states[context["state"]]
                    or capture["page"] != motion_sequence["page"]
                )
            )
            or (
                is_reduced_capture
                and (
                    profile != "mobile-reduced-static"
                    or context["wait_condition"] != "contract-replay-complete"
                    or capture["page"] != motion_sequence["page"]
                )
            )
            or context["reduced_motion"] != profile_rule["reducedMotion"]
            or captured_at.tzinfo is None
            or f"{width}x{height}" != expected_viewport
        ):
            raise CurrentCraftError("capture matrix or dimensions drifted from the current standard")
        capture_labels.add(label)
        capture_paths.add(relative)
        capture_artifacts[label] = artifact
        if is_motion_capture or is_reduced_capture:
            motion_capture_matrix.append(
                (capture["page"], profile, context["state"])
            )
        elif is_state_capture:
            state_capture_matrix.append(
                (capture["page"], profile, context["state"])
            )
        else:
            default_capture_matrix.add((capture["page"], profile))
        total_bytes += size
    expected_matrix = {
        (page, profile)
        for page in capture_pages
        for profile in ("desktop-default", "mobile-default")
    }
    expected_state_matrix = (
        [
            (
                state_evidence["page"],
                state_evidence["profile"],
                f"contract:{state_evidence['contract_case_id']}",
            )
        ]
        if state_evidence
        else []
    )
    expected_motion_profiles = {"desktop-motion", "mobile-motion"}
    observed_motion_profiles = {
        profile
        for _, profile, state in motion_capture_matrix
        if state in motion_states
    }
    expected_motion_matrix = (
        [
            (
                motion_sequence["page"],
                next(iter(observed_motion_profiles)) if len(observed_motion_profiles) == 1 else "",
                f"contract:{motion_sequence['motion_contract_case_id']}:motion-{offset}ms",
            )
            for offset in motion_sequence["offsets_ms"]
        ]
        + [
            (
                motion_sequence["page"],
                "mobile-reduced-static",
                f"contract:{motion_sequence['reduced_motion_contract_case_id']}:reduced-static",
            )
        ]
        if motion_sequence
        else []
    )
    if (
        default_capture_matrix != expected_matrix
        or state_capture_matrix != expected_state_matrix
        or observed_motion_profiles - expected_motion_profiles
        or motion_capture_matrix != expected_motion_matrix
        or (
            motion_evidence
            and set(motion_evidence["capture_labels"]["motion_sequence"])
            | {motion_evidence["capture_labels"]["reduced_motion_static"]}
            != {
                capture["label"]
                for capture in captures
                if capture["context"]["state"] != capture_plan["state"]
            }
        )
        or total_bytes > MAX_TOTAL_CAPTURE_BYTES
    ):
        raise CurrentCraftError("capture matrix is incomplete or exceeds its evidence budget")

    capture_projection = [
        {
            "label": capture["label"],
            "path": capture["path"],
            "sha256": capture["sha256"],
        }
        for capture in captures
    ]
    capture_set_sha256 = hashlib.sha256(
        json.dumps(capture_projection, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "case": case,
        "craft_case": craft_case,
        "receipt": receipt,
        "manifest": manifest,
        "capture_labels": capture_labels,
        "capture_paths": capture_paths,
        "capture_artifacts": capture_artifacts,
        "capture_count": len(captures),
        "capture_set_sha256": capture_set_sha256,
        "capture_standard": capture_standard,
    }


def validate_current_acceptance(
    result_path: Path,
    ledger_path: Path,
    policy_path: Path,
    workspace_root: Path,
    case_path: Path,
    receipt_path: Path,
    manifest_path: Path,
) -> int:
    workspace = workspace_root.expanduser().resolve(strict=True)
    ledger_file = _unaliased_file(ledger_path, "ledger")
    policy_file = _unaliased_file(policy_path, "policy")
    for path, label in ((ledger_file, "ledger"), (policy_file, "policy")):
        _outside_workspace(path, workspace, label)
        _outside_authoring_repository(path, label)
    validated = validate_current_capture_evidence(
        workspace,
        case_path,
        receipt_path,
        manifest_path,
    )
    case = validated["case"]
    craft_case = validated["craft_case"]
    receipt = validated["receipt"]
    captures = receipt["captures"]
    capture_labels = validated["capture_labels"]
    capture_artifacts = validated["capture_artifacts"]
    policy = _load_json(policy_file, "policy")
    result = _load_json(_unaliased_file(result_path, "quality result"), "quality result")
    ledger_root = ledger_file.parent.resolve(strict=True)
    capture_paths: set[str] = set()
    capture_ledger_paths: dict[str, str] = {}
    for label, artifact in capture_artifacts.items():
        try:
            relative = artifact.relative_to(ledger_root).as_posix()
        except ValueError as error:
            raise CurrentCraftError(f"capture artifact is outside the ledger root: {label}") from error
        capture_paths.add(relative)
        capture_ledger_paths[label] = relative

    if policy.get("case_id") != case["case_id"] or policy.get("run_id") != case["run_id"]:
        raise CurrentCraftError("evaluator policy does not match the frozen case")
    craft_review = policy.get("craft_review")
    if not isinstance(craft_review, dict) or craft_review.get("rubric_version") != craft_case["rubric_version"]:
        raise CurrentCraftError("evaluator craft review does not match the case rubric")
    dimensions = craft_review.get("dimensions")
    if not isinstance(dimensions, list) or {item.get("id") for item in dimensions if isinstance(item, dict)} != CORE_CRAFT:
        raise CurrentCraftError("evaluator craft review must contain the complete core craft floor")
    for dimension in dimensions:
        if set(dimension.get("evidence", [])) != capture_labels:
            raise CurrentCraftError(f"core craft review must inspect every fresh capture: {dimension.get('id')}")

    evidence = policy.get("evidence")
    if not isinstance(evidence, dict):
        raise CurrentCraftError("evaluator policy evidence is invalid")
    expected_artifacts: dict[str, dict[str, Any]] = {}
    for capture in captures:
        rule = evidence.get(capture["label"])
        if not isinstance(rule, dict) or rule.get("kind") != "artifact" or rule.get("artifact_kind") != "screenshot":
            raise CurrentCraftError(f"fresh capture is not evaluator-approved: {capture['label']}")
        policy_artifact = (ledger_root / _relative(rule.get("path"), f"policy evidence {capture['label']}")).resolve(strict=True)
        receipt_artifact = capture_artifacts[capture["label"]]
        if policy_artifact != receipt_artifact:
            raise CurrentCraftError(f"policy screenshot path does not match capture receipt: {capture['label']}")
        context = rule.get("context")
        if not isinstance(context, dict) or any(
            context.get(field) != capture["context"][field] for field in ("route", "viewport", "locale", "state")
        ) or context.get("note") != "dpr=1":
            raise CurrentCraftError(f"policy screenshot context does not match capture receipt: {capture['label']}")
        expected_artifacts[capture["label"]] = {
            "kind": "artifact",
            "artifact_kind": "screenshot",
            "path": capture_ledger_paths[capture["label"]],
            "exists": True,
            "bytes": capture["bytes"],
            "sha256": capture["sha256"],
            "media_type": "image/png",
            "width": capture["width"],
            "height": capture["height"],
            "context": {
                "route": capture["context"]["route"],
                "viewport": capture["context"]["viewport"],
                "locale": capture["context"]["locale"],
                "state": capture["context"]["state"],
                "note": "dpr=1",
            },
        }

    rendered = result.get("handoff", {}).get("rendered_evidence", {})
    if rendered.get("status") != "OBSERVED" or set(rendered.get("paths", [])) != capture_paths:
        raise CurrentCraftError("quality result must hand off the complete fresh capture set")

    try:
        count = validate_quality_result.validate_with_ledger(
            result_path.expanduser(),
            ledger_file,
            workspace,
            ("novel-discovery",),
            policy_file,
            expected_artifacts=expected_artifacts,
        )
    except (validate_quality_result.QualityResultError, evidence_ledger.LedgerError) as error:
        raise CurrentCraftError(str(error)) from error
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--capture-receipt", required=True, type=Path)
    parser.add_argument("--run-manifest", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        count = validate_current_acceptance(
            args.result,
            args.ledger,
            args.policy,
            args.workspace_root,
            args.case,
            args.capture_receipt,
            args.run_manifest,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, CurrentCraftError) as error:
        print(f"current craft acceptance invalid: {error}", file=sys.stderr)
        return 1
    print(f"current craft acceptance valid: {count} hard gates bound to fresh evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
