#!/usr/bin/env python3
"""Validate the published Codex v5 mini product-flow evidence and screenshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

SCRIPT_RUNTIME = Path(__file__).resolve().parents[2] / "wow-frontend-design" / "scripts"
sys.path.insert(0, str(SCRIPT_RUNTIME))

from evidence_ledger import LedgerError, png_metadata


SHA256 = re.compile(r"^[0-9a-f]{64}$")
MODEL = "gpt-5.4-mini"
ALIAS = f"codex-{MODEL}"
CASES = {
    "rail-rebooking-v5": ("index.html",),
    "subscription-audit-v5": ("index.html",),
    "community-translation-v5": ("index.html",),
    "ceramics-festival-one-line-v5": ("index.html", "program.html", "visit.html"),
}
VIEWPORTS = {
    "desktop": (1440, 1000, 1),
    "mobile": (390, 844, 3),
}
FROZEN_SKILL_SHA256 = "0e6337f3f4638c255908ca60b779782103aaecdc70d09001e0d4f2b44b919c47"
EXPECTED_ISSUES = {
    f"rail-rebooking-v5:{ALIAS}": ["rail_required_structure_missing"],
    f"subscription-audit-v5:{ALIAS}": ["subscription_filter_count_failed"],
    f"community-translation-v5:{ALIAS}": [
        "content_column_too_narrow",
        "short_action_label_wrapped_or_clipped",
        "translation_mobile_review_layout_squeezed",
    ],
    f"ceramics-festival-one-line-v5:{ALIAS}": ["paragraph_line_height_too_tight"],
}


class ProductFlowV5EvidenceError(ValueError):
    """Raised when checked-in v5 mini evidence is stale or incomplete."""


def _load(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ProductFlowV5EvidenceError(f"{label} is missing or unsafe")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProductFlowV5EvidenceError(f"cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise ProductFlowV5EvidenceError(f"{label} must be a JSON object")
    return value


def _artifact(root: Path, relative: Any, label: str, *, directory: bool = False) -> Path:
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        raise ProductFlowV5EvidenceError(f"{label} path is invalid")
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ProductFlowV5EvidenceError(f"{label} path is unsafe")
    path = (root / candidate).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ProductFlowV5EvidenceError(f"{label} escapes repository root") from error
    valid = path.is_dir() if directory else path.is_file()
    if not valid or path.is_symlink():
        raise ProductFlowV5EvidenceError(f"{label} is missing or unsafe")
    return path


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expected_runs() -> set[tuple[str, str, str]]:
    return {("codex", MODEL, case_id) for case_id in CASES}


def _validate_generation(root: Path, path: Path) -> None:
    ledger = _load(path, "generation ledger")
    expected_selection = {"provider": "codex", "model": MODEL, "theme": "all", "count": 4}
    expected_summary = {
        "requested": 4,
        "completed": 4,
        "failed": 0,
        "attempts": 5,
        "retried_cases": 1,
        "statuses": {"completed": 4},
    }
    if ledger.get("schema_version") != 1 or ledger.get("selection") != expected_selection:
        raise ProductFlowV5EvidenceError("generation ledger is not the fixed Codex v5 mini cohort")
    if ledger.get("status") != "completed" or ledger.get("summary") != expected_summary:
        raise ProductFlowV5EvidenceError("generation summary must preserve the completed 4-target, 5-attempt run")
    contract = ledger.get("contract")
    if not isinstance(contract, dict) or contract.get("artifact_root") != "evals/product-flow-v5-mini-targets":
        raise ProductFlowV5EvidenceError("generation artifact root changed")
    skill = contract.get("skill")
    if not isinstance(skill, dict) or skill.get("sha256") != FROZEN_SKILL_SHA256:
        raise ProductFlowV5EvidenceError("generation must retain the frozen pre-optimization Skill hash")
    briefs = contract.get("briefs")
    if not isinstance(briefs, dict) or set(briefs) != set(CASES):
        raise ProductFlowV5EvidenceError("generation brief inventory changed")
    for case_id, record in briefs.items():
        if not isinstance(record, dict):
            raise ProductFlowV5EvidenceError(f"brief record is malformed for {case_id}")
        brief = _artifact(root, record.get("path"), f"brief {case_id}")
        if record.get("sha256") != _digest(brief):
            raise ProductFlowV5EvidenceError(f"generation brief hash is stale for {case_id}")

    results = ledger.get("results")
    if not isinstance(results, list) or len(results) != 4:
        raise ProductFlowV5EvidenceError("generation ledger must contain 4 results")
    seen: set[tuple[str, str, str]] = set()
    attempts_total = retried = 0
    for result in results:
        if not isinstance(result, dict):
            raise ProductFlowV5EvidenceError("generation result is malformed")
        key = (result.get("provider"), result.get("model"), result.get("case_id"))
        if key in seen or key not in _expected_runs():
            raise ProductFlowV5EvidenceError("generation model/case set changed")
        seen.add(key)  # type: ignore[arg-type]
        case_id = str(key[2])
        target_path = f"evals/product-flow-v5-mini-targets/{ALIAS}-{case_id}"
        manifest_path = f"{target_path}/run-manifest.json"
        attempts = result.get("attempts")
        if (
            result.get("status") != "completed"
            or not isinstance(attempts, list)
            or not attempts
            or result.get("attempt_count") != len(attempts)
            or attempts[-1].get("status") != "completed"
        ):
            raise ProductFlowV5EvidenceError(f"generation attempts are incomplete for {key}")
        attempts_total += len(attempts)
        retried += int(len(attempts) > 1)
        if result.get("target") != target_path or result.get("manifest") != manifest_path:
            raise ProductFlowV5EvidenceError(f"generation path changed for {key}")
        target = _artifact(root, target_path, f"target {key}", directory=True)
        manifest = _load(_artifact(root, manifest_path, f"manifest {key}"), f"manifest {key}")
        if (
            manifest.get("schema_version") != 1
            or manifest.get("status") != "completed"
            or manifest.get("case") != {"id": case_id, "target": target_path}
            or manifest.get("model", {}).get("requested_identifier") != MODEL
        ):
            raise ProductFlowV5EvidenceError(f"manifest disagrees with generation result for {key}")
        outputs = manifest.get("outputs")
        expected_outputs = {"DESIGN.md", *CASES[case_id]}
        if not isinstance(outputs, list) or {item.get("path") for item in outputs if isinstance(item, dict)} != expected_outputs:
            raise ProductFlowV5EvidenceError(f"manifest output inventory changed for {key}")
        for output in outputs:
            if not isinstance(output, dict):
                raise ProductFlowV5EvidenceError(f"manifest output is malformed for {key}")
            artifact = target / str(output.get("path"))
            if not artifact.is_file() or artifact.is_symlink():
                raise ProductFlowV5EvidenceError(f"manifest output is missing for {key}")
            if output.get("bytes") != artifact.stat().st_size or output.get("sha256") != _digest(artifact):
                raise ProductFlowV5EvidenceError(f"manifest output hash is stale for {key}")
    if seen != _expected_runs() or (attempts_total, retried) != (5, 1):
        raise ProductFlowV5EvidenceError("generation result or retry inventory changed")


def _validate_design(root: Path, path: Path, generation_path: Path) -> None:
    report = _load(path, "DESIGN.md lint report")
    generation_ref = report.get("generation_ledger")
    if (
        report.get("schema_version") != 1
        or report.get("linter") != {"package": "@google/design.md", "version": "0.3.0"}
        or not isinstance(generation_ref, dict)
        or generation_ref.get("path") != "evals/product-flow-v5-mini-generation-results.json"
        or generation_ref.get("sha256") != _digest(generation_path)
    ):
        raise ProductFlowV5EvidenceError("DESIGN.md report provenance is stale")
    if report.get("summary") != {"checked": 4, "clean": 4, "with_findings": 0, "infrastructure_failures": 0}:
        raise ProductFlowV5EvidenceError("DESIGN.md summary must retain 4/4 clean")
    results = report.get("results")
    if not isinstance(results, list) or len(results) != 4:
        raise ProductFlowV5EvidenceError("DESIGN.md report must contain 4 results")
    seen: set[tuple[str, str, str]] = set()
    for result in results:
        if not isinstance(result, dict):
            raise ProductFlowV5EvidenceError("DESIGN.md result is malformed")
        key = (result.get("provider"), result.get("model"), result.get("case_id"))
        if key in seen or key not in _expected_runs() or result.get("status") != "clean":
            raise ProductFlowV5EvidenceError("DESIGN.md model/case set or clean status changed")
        seen.add(key)  # type: ignore[arg-type]
        design = _artifact(root, result.get("path"), f"DESIGN.md {key}")
        if result.get("sha256") != _digest(design):
            raise ProductFlowV5EvidenceError(f"DESIGN.md hash is stale for {key}")
        summary = result.get("summary")
        if not isinstance(summary, dict) or summary.get("errors") != 0 or summary.get("warnings") != 0:
            raise ProductFlowV5EvidenceError(f"DESIGN.md result is not clean for {key}")
    if seen != _expected_runs():
        raise ProductFlowV5EvidenceError("DESIGN.md result inventory is incomplete")


def _visual_issues(report: dict[str, Any]) -> dict[str, list[str]]:
    by_target: dict[str, set[str]] = {key: set() for key in EXPECTED_ISSUES}
    for collection_name in ("results", "crossPageComparisons"):
        collection = report.get(collection_name)
        if not isinstance(collection, list):
            raise ProductFlowV5EvidenceError(f"visual {collection_name} is malformed")
        for item in collection:
            if not isinstance(item, dict) or not isinstance(item.get("visualIssues"), list):
                raise ProductFlowV5EvidenceError(f"visual {collection_name} entry is malformed")
            key = f"{item.get('caseId')}:{item.get('alias')}"
            if key not in by_target or any(not isinstance(issue, str) for issue in item["visualIssues"]):
                raise ProductFlowV5EvidenceError("visual issue target or code changed")
            by_target[key].update(item["visualIssues"])
    return {key: sorted(value) for key, value in sorted(by_target.items())}


def _validate_visual(root: Path, path: Path) -> None:
    report = _load(path, "visual report")
    auditor = report.get("auditor")
    auditor_path = _artifact(root, "evals/playwright_visual_v5_audit.cjs", "visual auditor")
    if (
        report.get("schema_version") != 1
        or not isinstance(auditor, dict)
        or auditor.get("path") != "evals/playwright_visual_v5_audit.cjs"
        or auditor.get("sha256") != _digest(auditor_path)
    ):
        raise ProductFlowV5EvidenceError("visual auditor provenance is stale")
    expected_targets = {(case_id, ALIAS) for case_id in CASES}
    targets = report.get("targets")
    actual_targets = {
        (item.get("caseId"), item.get("alias"))
        for item in targets
        if isinstance(item, dict)
    } if isinstance(targets, list) else set()
    if not isinstance(targets, list) or len(targets) != 4 or actual_targets != expected_targets:
        raise ProductFlowV5EvidenceError("visual target inventory changed")
    expected = {
        (case_id, ALIAS, page, viewport)
        for case_id, pages in CASES.items()
        for page in pages
        for viewport in VIEWPORTS
    }
    results = report.get("results")
    if not isinstance(results, list) or len(results) != 12:
        raise ProductFlowV5EvidenceError("visual report must retain exactly 12 screenshots")
    seen: set[tuple[str, str, str, str]] = set()
    screenshots: set[Path] = set()
    for result in results:
        if not isinstance(result, dict):
            raise ProductFlowV5EvidenceError("visual result is malformed")
        key = (result.get("caseId"), result.get("alias"), result.get("page"), result.get("viewport"))
        if key in seen or key not in expected:
            raise ProductFlowV5EvidenceError("visual screenshot inventory changed")
        seen.add(key)  # type: ignore[arg-type]
        width, height, scale = VIEWPORTS[str(key[3])]
        expected_path = f"assets/product-flow-v5-mini/{key[0]}-{key[1]}-{Path(str(key[2])).stem}-{key[3]}.png"
        if result.get("screenshot") != expected_path or result.get("size") != f"{width}x{height}":
            raise ProductFlowV5EvidenceError(f"visual screenshot metadata changed for {key}")
        screenshot = _artifact(root, expected_path, f"screenshot {key}")
        screenshots.add(screenshot)
        digest = result.get("screenshotSha256")
        if not isinstance(digest, str) or SHA256.fullmatch(digest) is None or digest != _digest(screenshot):
            raise ProductFlowV5EvidenceError(f"screenshot hash is stale for {key}")
        try:
            metadata = png_metadata(screenshot.read_bytes())
        except LedgerError as error:
            raise ProductFlowV5EvidenceError(f"screenshot decode failed for {key}: {error}") from error
        if metadata != ("image/png", width * scale, height * scale):
            raise ProductFlowV5EvidenceError(f"screenshot dimensions changed for {key}")
        if any(result.get(field) != [] for field in ("consoleErrors", "externalRequests", "badResponses")):
            raise ProductFlowV5EvidenceError(f"runtime/network evidence changed for {key}")
    actual_pngs = {
        item.resolve()
        for item in (root / "assets" / "product-flow-v5-mini").glob("*.png")
        if item.is_file() and not item.is_symlink()
    }
    if seen != expected or screenshots != actual_pngs:
        raise ProductFlowV5EvidenceError("visual screenshot file set is incomplete or has extras")
    actual_issues = _visual_issues(report)
    expected_issues = {key: sorted(value) for key, value in sorted(EXPECTED_ISSUES.items())}
    if actual_issues != expected_issues:
        raise ProductFlowV5EvidenceError("visual repair findings changed")
    summary = report.get("summary")
    issues_by_target = summary.get("issuesByTarget") if isinstance(summary, dict) else None
    if (
        not isinstance(summary, dict)
        or not isinstance(issues_by_target, dict)
        or summary.get("checkedPages") != 12
        or summary.get("targetsWithObservedIssues") != 4
        or summary.get("verdict") != "observed_issues"
        or any(not isinstance(value, list) for value in issues_by_target.values())
        or {key: sorted(value) for key, value in sorted(issues_by_target.items())} != actual_issues
    ):
        raise ProductFlowV5EvidenceError("visual summary overstates or disagrees with observed issues")


def validate(
    visual_path: Path,
    root: Path,
    *,
    generation_path: Path | None = None,
    design_path: Path | None = None,
) -> int:
    root = root.resolve()
    generation = generation_path or root / "evals" / "product-flow-v5-mini-generation-results.json"
    design = design_path or root / "evals" / "product-flow-v5-mini-design-md-results.json"
    _validate_generation(root, generation)
    _validate_design(root, design, generation)
    _validate_visual(root, visual_path)
    return 4


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("visual_report", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        count = validate(args.visual_report, args.repository_root)
    except ProductFlowV5EvidenceError as error:
        parser.error(str(error))
    print(f"validated {count} Codex v5 mini targets, 4 DESIGN.md reports, and 12 screenshots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
