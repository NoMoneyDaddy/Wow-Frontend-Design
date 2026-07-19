#!/usr/bin/env python3
"""Bind current-run craft acceptance to fresh Playwright evidence and frozen case provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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


def _exact(value: object, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise CurrentCraftError(f"{label} must contain exactly {sorted(keys)}")
    return value


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
    case_file = case_path.expanduser().resolve(strict=True)
    receipt_file = receipt_path.expanduser().resolve(strict=True)
    manifest_file = manifest_path.expanduser().resolve(strict=True)
    ledger_file = ledger_path.expanduser().resolve(strict=True)
    policy_file = policy_path.expanduser().resolve(strict=True)
    for path, label in ((case_file, "case"), (receipt_file, "capture receipt"), (ledger_file, "ledger"), (policy_file, "policy")):
        _outside_workspace(path, workspace, label)
        _outside_authoring_repository(path, label)
    try:
        manifest_file.relative_to(workspace)
    except ValueError as error:
        raise CurrentCraftError("run manifest must remain inside the current workspace") from error

    case = _exact(_load_json(case_file, "case"), CASE_KEYS, "case")
    receipt = _exact(_load_json(receipt_file, "capture receipt"), RECEIPT_KEYS, "capture receipt")
    manifest = _load_json(manifest_file, "run manifest")
    policy = _load_json(policy_file, "policy")
    result = _load_json(result_path.expanduser().resolve(strict=True), "quality result")

    if case["schema_version"] != 1 or not isinstance(case["case_id"], str) or not case["case_id"].strip():
        raise CurrentCraftError("case identity is invalid")
    if not isinstance(case["run_id"], str) or RUN_ID_PATTERN.fullmatch(case["run_id"]) is None:
        raise CurrentCraftError("case run_id is invalid")
    if case["partition"] not in {"validation", "test"}:
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
    capture_plan = _exact(
        case["capture_plan"],
        {"locale", "state", "pages", "wait_condition", "profiles"},
        "case.capture_plan",
    )
    if (
        capture_plan["locale"] not in {"zh-Hant", "en"}
        or capture_plan["state"] != "default"
        or capture_plan["pages"] != "all_html_outputs"
        or capture_plan["wait_condition"] != "load+fonts+two-raf+300ms+two-raf"
        or capture_plan["profiles"] != PROFILE_STANDARD
    ):
        raise CurrentCraftError("case capture plan is not the current standard")

    if receipt["schema_version"] != 1 or receipt["status"] != "captured":
        raise CurrentCraftError("capture receipt is not a completed current receipt")
    runtime = _exact(receipt["runtime"], {"package", "version", "browser", "browser_version", "headless"}, "capture receipt.runtime")
    if (
        runtime["package"] != "playwright"
        or not isinstance(runtime["version"], str)
        or not runtime["version"].strip()
        or runtime["browser"] != "chromium"
        or not isinstance(runtime["browser_version"], str)
        or not runtime["browser_version"].strip()
        or runtime["headless"] is not True
    ):
        raise CurrentCraftError("capture runtime is not the current Playwright Chromium standard")
    capture_standard = _exact(
        receipt["capture_standard"],
        {"profiles", "screenshot_mode", "animations", "caret", "network"},
        "capture receipt.capture_standard",
    )
    if capture_standard != {
        "profiles": PROFILE_STANDARD,
        "screenshot_mode": "viewport",
        "animations": "disabled",
        "caret": "hide",
        "network": "local-output-only",
    }:
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
    source = _exact(receipt["source"], {"run_manifest_sha256", "brief", "skill_tree_sha256", "outputs"}, "capture receipt.source")
    if source["run_manifest_sha256"] != _sha256(manifest_file):
        raise CurrentCraftError("run manifest changed after capture")
    if source["brief"] != case_brief or source["brief"] != manifest.get("brief"):
        raise CurrentCraftError("brief provenance disagrees across case, capture, and current build")
    if source["skill_tree_sha256"] != manifest.get("skill_snapshot", {}).get("tree_sha256"):
        raise CurrentCraftError("Skill snapshot provenance disagrees with the current build")
    if source["outputs"] != manifest.get("outputs") or not isinstance(source["outputs"], list):
        raise CurrentCraftError("output provenance disagrees with the current build")

    output_root = manifest_file.parent
    html_pages: set[str] = set()
    for index, record in enumerate(source["outputs"]):
        record = _exact(record, {"path", "bytes", "mode", "sha256"}, f"outputs[{index}]")
        relative = _relative(record["path"], f"outputs[{index}].path")
        output = (output_root / relative).resolve(strict=True)
        try:
            output.relative_to(output_root.resolve(strict=True))
        except ValueError as error:
            raise CurrentCraftError("current output escapes its workspace") from error
        if output.is_symlink() or not output.is_file() or output.stat().st_size != record["bytes"] or _sha256(output) != record["sha256"]:
            raise CurrentCraftError(f"current output changed after capture: {relative}")
        if relative.lower().endswith(".html"):
            html_pages.add(relative)

    captures = receipt["captures"]
    if not isinstance(captures, list) or not captures or len(captures) != len(html_pages) * 2:
        raise CurrentCraftError("capture receipt must cover every HTML output at desktop and mobile")
    capture_labels: set[str] = set()
    capture_paths: set[str] = set()
    capture_matrix: set[tuple[str, str]] = set()
    total_bytes = 0
    evidence_root = receipt_file.parent.resolve(strict=True)
    ledger_root = ledger_file.parent.resolve(strict=True)
    for index, raw_capture in enumerate(captures):
        capture = _exact(raw_capture, CAPTURE_KEYS, f"captures[{index}]")
        label = capture["label"]
        if not isinstance(label, str) or not label or label in capture_labels:
            raise CurrentCraftError("capture labels must be unique non-empty strings")
        relative = _relative(capture["path"], f"captures[{index}].path")
        artifact = (evidence_root / relative).resolve(strict=True)
        try:
            artifact.relative_to(evidence_root)
            ledger_relative = artifact.relative_to(ledger_root).as_posix()
        except ValueError as error:
            raise CurrentCraftError("capture artifact is outside evaluator evidence roots") from error
        if artifact.is_symlink() or not artifact.is_file():
            raise CurrentCraftError(f"capture artifact is missing: {relative}")
        size = artifact.stat().st_size
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
        profile = capture["profile"]
        profile_rule = next((item for item in PROFILE_STANDARD if item["name"] == profile), None)
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
        if (
            capture["page"] not in html_pages
            or expected_viewport is None
            or context["viewport"] != expected_viewport
            or context["dpr"] != 1
            or context["locale"] != capture_plan["locale"]
            or context["state"] != capture_plan["state"]
            or context["wait_condition"] != capture_plan["wait_condition"]
            or context["reduced_motion"] != profile_rule["reducedMotion"]
            or captured_at.tzinfo is None
            or f"{width}x{height}" != expected_viewport
        ):
            raise CurrentCraftError("capture matrix or dimensions drifted from the current standard")
        capture_labels.add(label)
        capture_paths.add(ledger_relative)
        capture_matrix.add((capture["page"], profile))
        total_bytes += size
    expected_matrix = {(page, profile) for page in html_pages for profile in ("desktop-default", "mobile-default")}
    if capture_matrix != expected_matrix or total_bytes > MAX_TOTAL_CAPTURE_BYTES:
        raise CurrentCraftError("capture matrix is incomplete or exceeds its evidence budget")

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
    for capture in captures:
        rule = evidence.get(capture["label"])
        if not isinstance(rule, dict) or rule.get("kind") != "artifact" or rule.get("artifact_kind") != "screenshot":
            raise CurrentCraftError(f"fresh capture is not evaluator-approved: {capture['label']}")
        policy_artifact = (ledger_root / _relative(rule.get("path"), f"policy evidence {capture['label']}")).resolve(strict=True)
        receipt_artifact = (evidence_root / capture["path"]).resolve(strict=True)
        if policy_artifact != receipt_artifact:
            raise CurrentCraftError(f"policy screenshot path does not match capture receipt: {capture['label']}")
        context = rule.get("context")
        if not isinstance(context, dict) or any(
            context.get(field) != capture["context"][field] for field in ("route", "viewport", "locale", "state")
        ) or context.get("note") != "dpr=1":
            raise CurrentCraftError(f"policy screenshot context does not match capture receipt: {capture['label']}")

    rendered = result.get("handoff", {}).get("rendered_evidence", {})
    if rendered.get("status") != "OBSERVED" or set(rendered.get("paths", [])) != capture_paths:
        raise CurrentCraftError("quality result must hand off the complete fresh capture set")

    try:
        return validate_quality_result.validate_with_ledger(
            result_path.expanduser(),
            ledger_file,
            workspace,
            ("novel-discovery",),
            policy_file,
        )
    except (validate_quality_result.QualityResultError, evidence_ledger.LedgerError) as error:
        raise CurrentCraftError(str(error)) from error


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
