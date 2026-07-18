#!/usr/bin/env python3
"""Validate the published Codex v4 product-flow evidence and screenshots."""

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
MODELS = ("gpt-5.4-mini", "gpt-5.4", "gpt-5.5")
CASES = {
    "harbor-cold-chain-v4": ("index.html",),
    "island-sound-archive-v4": ("index.html",),
    "plant-swap-one-line-v4": ("index.html", "browse.html", "listing.html"),
}
VIEWPORTS = {
    "desktop": (1440, 1000, 1),
    "mobile": (390, 844, 3),
}
FROZEN_SKILL_SHA256 = "430116b2fd1bcf4162b3e450ee1ea27cc687f65a989bccc5789aa7d0291c8a3f"
EXPECTED_ISSUES = {
    "harbor-cold-chain-v4:codex-gpt-5.4-mini": [
        "closed_mobile_navigation_exposed",
        "page_horizontal_overflow",
    ],
    "harbor-cold-chain-v4:codex-gpt-5.4": ["short_action_label_wrapped_or_clipped"],
    "harbor-cold-chain-v4:codex-gpt-5.5": [],
    "island-sound-archive-v4:codex-gpt-5.4-mini": ["visible_text_clipped"],
    "island-sound-archive-v4:codex-gpt-5.4": [
        "closed_mobile_navigation_exposed",
        "critical_text_collision",
        "fixed_or_sticky_content_obstruction",
        "vertical_type_contract_failed",
    ],
    "island-sound-archive-v4:codex-gpt-5.5": ["vertical_type_contract_failed"],
    "plant-swap-one-line-v4:codex-gpt-5.4-mini": [
        "document_lang_not_zh_hant",
        "fixed_or_sticky_content_obstruction",
        "short_action_label_wrapped_or_clipped",
    ],
    "plant-swap-one-line-v4:codex-gpt-5.4": [],
    "plant-swap-one-line-v4:codex-gpt-5.5": ["document_lang_not_zh_hant"],
}


class ProductFlowEvidenceError(ValueError):
    """Raised when checked-in v4 evidence is stale, incomplete, or overstated."""


def _load(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ProductFlowEvidenceError(f"{label} is missing or unsafe")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProductFlowEvidenceError(f"cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise ProductFlowEvidenceError(f"{label} must be a JSON object")
    return value


def _artifact(root: Path, relative: Any, label: str, *, directory: bool = False) -> Path:
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        raise ProductFlowEvidenceError(f"{label} path is invalid")
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ProductFlowEvidenceError(f"{label} path is unsafe")
    path = (root / candidate).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ProductFlowEvidenceError(f"{label} escapes repository root") from error
    valid = path.is_dir() if directory else path.is_file()
    if not valid or path.is_symlink():
        raise ProductFlowEvidenceError(f"{label} is missing or unsafe")
    return path


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expected_runs() -> set[tuple[str, str, str]]:
    return {("codex", model, case_id) for model in MODELS for case_id in CASES}


def _validate_generation(root: Path, path: Path) -> None:
    ledger = _load(path, "generation ledger")
    if ledger.get("schema_version") != 1 or ledger.get("selection") != {
        "provider": "codex",
        "theme": "all",
        "count": 9,
    }:
        raise ProductFlowEvidenceError("generation ledger is not the fixed Codex v4 cohort")
    if ledger.get("status") != "completed" or ledger.get("summary") != {
        "requested": 9,
        "completed": 9,
        "failed": 0,
        "attempts": 13,
        "retried_cases": 3,
        "statuses": {"completed": 9},
    }:
        raise ProductFlowEvidenceError("generation summary must preserve the completed 9-target, 13-attempt run")
    contract = ledger.get("contract")
    if not isinstance(contract, dict) or contract.get("artifact_root") != "evals/product-flow-v4-targets":
        raise ProductFlowEvidenceError("generation artifact root changed")
    skill = contract.get("skill")
    if not isinstance(skill, dict) or skill.get("sha256") != FROZEN_SKILL_SHA256:
        raise ProductFlowEvidenceError("generation must retain the frozen pre-optimization Skill hash")
    for case_id, record in contract.get("briefs", {}).items():
        if case_id not in CASES or not isinstance(record, dict):
            raise ProductFlowEvidenceError("generation brief inventory changed")
        brief = _artifact(root, record.get("path"), f"brief {case_id}")
        if record.get("sha256") != _digest(brief):
            raise ProductFlowEvidenceError(f"generation brief hash is stale for {case_id}")
    results = ledger.get("results")
    if not isinstance(results, list) or len(results) != 9:
        raise ProductFlowEvidenceError("generation ledger must contain 9 results")
    seen: set[tuple[str, str, str]] = set()
    attempt_total = 0
    retried = 0
    for result in results:
        if not isinstance(result, dict):
            raise ProductFlowEvidenceError("generation result is malformed")
        key = (result.get("provider"), result.get("model"), result.get("case_id"))
        if key in seen or key not in _expected_runs():
            raise ProductFlowEvidenceError("generation model/case set changed")
        seen.add(key)  # type: ignore[arg-type]
        provider, model, case_id = key
        expected_target = f"evals/product-flow-v4-targets/codex-{model}-{case_id}"
        expected_manifest = f"{expected_target}/run-manifest.json"
        attempts = result.get("attempts")
        if result.get("status") != "completed" or not isinstance(attempts, list) or result.get("attempt_count") != len(attempts):
            raise ProductFlowEvidenceError(f"generation result is incomplete for {key}")
        if not attempts or attempts[-1].get("status") != "completed":
            raise ProductFlowEvidenceError(f"generation attempts do not end in completion for {key}")
        attempt_total += len(attempts)
        retried += int(len(attempts) > 1)
        if result.get("target") != expected_target or result.get("manifest") != expected_manifest:
            raise ProductFlowEvidenceError(f"generation path changed for {key}")
        target = _artifact(root, expected_target, f"target {key}", directory=True)
        manifest = _load(_artifact(root, expected_manifest, f"manifest {key}"), f"manifest {key}")
        if (
            manifest.get("schema_version") != 1
            or manifest.get("status") != "completed"
            or manifest.get("case") != {"id": case_id, "target": expected_target}
            or manifest.get("model", {}).get("requested_identifier") != model
        ):
            raise ProductFlowEvidenceError(f"manifest disagrees with generation result for {key}")
        outputs = manifest.get("outputs")
        expected_files = {"DESIGN.md", *CASES[str(case_id)]}
        if not isinstance(outputs, list) or {item.get("path") for item in outputs if isinstance(item, dict)} != expected_files:
            raise ProductFlowEvidenceError(f"manifest output inventory changed for {key}")
        for output in outputs:
            if not isinstance(output, dict):
                raise ProductFlowEvidenceError(f"manifest output is malformed for {key}")
            artifact = target / str(output.get("path"))
            if not artifact.is_file() or artifact.is_symlink():
                raise ProductFlowEvidenceError(f"manifest output is missing for {key}")
            if output.get("bytes") != artifact.stat().st_size or output.get("sha256") != _digest(artifact):
                raise ProductFlowEvidenceError(f"manifest output hash is stale for {key}")
    if seen != _expected_runs() or (attempt_total, retried) != (13, 3):
        raise ProductFlowEvidenceError("generation result or retry inventory changed")


def _validate_design(root: Path, path: Path, generation_path: Path) -> None:
    report = _load(path, "DESIGN.md lint report")
    generation_ref = report.get("generation_ledger")
    if (
        report.get("schema_version") != 1
        or report.get("linter") != {"package": "@google/design.md", "version": "0.2.0"}
        or not isinstance(generation_ref, dict)
        or generation_ref.get("path") != "evals/product-flow-v4-generation-results.json"
        or generation_ref.get("sha256") != _digest(generation_path)
    ):
        raise ProductFlowEvidenceError("DESIGN.md report provenance is stale")
    if report.get("summary") != {"checked": 9, "clean": 9, "with_findings": 0, "infrastructure_failures": 0}:
        raise ProductFlowEvidenceError("DESIGN.md summary must retain 9/9 clean")
    results = report.get("results")
    if not isinstance(results, list) or len(results) != 9:
        raise ProductFlowEvidenceError("DESIGN.md report must contain 9 results")
    seen: set[tuple[str, str, str]] = set()
    for result in results:
        if not isinstance(result, dict):
            raise ProductFlowEvidenceError("DESIGN.md result is malformed")
        key = (result.get("provider"), result.get("model"), result.get("case_id"))
        if key in seen or key not in _expected_runs() or result.get("status") != "clean":
            raise ProductFlowEvidenceError("DESIGN.md model/case set or clean status changed")
        seen.add(key)  # type: ignore[arg-type]
        design = _artifact(root, result.get("path"), f"DESIGN.md {key}")
        if result.get("sha256") != _digest(design):
            raise ProductFlowEvidenceError(f"DESIGN.md hash is stale for {key}")
        summary = result.get("summary")
        if not isinstance(summary, dict) or summary.get("errors") != 0 or summary.get("warnings") != 0:
            raise ProductFlowEvidenceError(f"DESIGN.md result is not clean for {key}")
    if seen != _expected_runs():
        raise ProductFlowEvidenceError("DESIGN.md result inventory is incomplete")


def _visual_issues(report: dict[str, Any]) -> dict[str, list[str]]:
    by_target: dict[str, set[str]] = {key: set() for key in EXPECTED_ISSUES}
    for collection_name in ("results", "crossPageComparisons"):
        collection = report.get(collection_name)
        if not isinstance(collection, list):
            raise ProductFlowEvidenceError(f"visual {collection_name} is malformed")
        for item in collection:
            if not isinstance(item, dict) or not isinstance(item.get("visualIssues"), list):
                raise ProductFlowEvidenceError(f"visual {collection_name} entry is malformed")
            key = f"{item.get('caseId')}:{item.get('alias')}"
            if key not in by_target or any(not isinstance(issue, str) for issue in item["visualIssues"]):
                raise ProductFlowEvidenceError("visual issue target or code changed")
            by_target[key].update(item["visualIssues"])
    return {key: sorted(value) for key, value in sorted(by_target.items())}


def _validate_visual(root: Path, path: Path) -> None:
    report = _load(path, "visual report")
    auditor = report.get("auditor")
    auditor_path = _artifact(root, "evals/playwright_visual_v4_audit.cjs", "visual auditor")
    if (
        report.get("schema_version") != 1
        or not isinstance(auditor, dict)
        or auditor.get("path") != "evals/playwright_visual_v4_audit.cjs"
        or auditor.get("sha256") != _digest(auditor_path)
    ):
        raise ProductFlowEvidenceError("visual auditor provenance is stale")
    expected_targets = {(case_id, f"codex-{model}") for model in MODELS for case_id in CASES}
    targets = report.get("targets")
    actual_targets = {
        (item.get("caseId"), item.get("alias"))
        for item in targets
        if isinstance(item, dict)
    } if isinstance(targets, list) else set()
    if not isinstance(targets, list) or len(targets) != 9 or actual_targets != expected_targets:
        raise ProductFlowEvidenceError("visual target inventory changed")
    expected = {
        (case_id, f"codex-{model}", page, viewport)
        for model in MODELS
        for case_id, pages in CASES.items()
        for page in pages
        for viewport in VIEWPORTS
    }
    results = report.get("results")
    if not isinstance(results, list) or len(results) != 30:
        raise ProductFlowEvidenceError("visual report must retain exactly 30 screenshots")
    seen: set[tuple[str, str, str, str]] = set()
    screenshots: set[Path] = set()
    for result in results:
        if not isinstance(result, dict):
            raise ProductFlowEvidenceError("visual result is malformed")
        key = (result.get("caseId"), result.get("alias"), result.get("page"), result.get("viewport"))
        if key in seen or key not in expected:
            raise ProductFlowEvidenceError("visual screenshot inventory changed")
        seen.add(key)  # type: ignore[arg-type]
        width, height, scale = VIEWPORTS[str(key[3])]
        expected_path = f"assets/product-flow-v4/{key[0]}-{key[1]}-{Path(str(key[2])).stem}-{key[3]}.png"
        if result.get("screenshot") != expected_path or result.get("size") != f"{width}x{height}":
            raise ProductFlowEvidenceError(f"visual screenshot metadata changed for {key}")
        screenshot = _artifact(root, expected_path, f"screenshot {key}")
        screenshots.add(screenshot)
        digest = result.get("screenshotSha256")
        if not isinstance(digest, str) or SHA256.fullmatch(digest) is None or digest != _digest(screenshot):
            raise ProductFlowEvidenceError(f"screenshot hash is stale for {key}")
        try:
            metadata = png_metadata(screenshot.read_bytes())
        except LedgerError as error:
            raise ProductFlowEvidenceError(f"screenshot decode failed for {key}: {error}") from error
        if metadata != ("image/png", width * scale, height * scale):
            raise ProductFlowEvidenceError(f"screenshot dimensions changed for {key}")
        if any(result.get(field) != [] for field in ("consoleErrors", "externalRequests", "badResponses")):
            raise ProductFlowEvidenceError(f"runtime/network evidence changed for {key}")
    actual_pngs = {
        item.resolve()
        for item in (root / "assets" / "product-flow-v4").glob("*.png")
        if item.is_file() and not item.is_symlink()
    }
    if seen != expected or screenshots != actual_pngs:
        raise ProductFlowEvidenceError("visual screenshot file set is incomplete or has extras")
    actual_issues = _visual_issues(report)
    expected_issues = {key: sorted(value) for key, value in sorted(EXPECTED_ISSUES.items())}
    if actual_issues != expected_issues:
        raise ProductFlowEvidenceError("visual blockers changed")
    summary = report.get("summary")
    reported_issues = summary.get("issuesByTarget") if isinstance(summary, dict) else None
    normalized_reported = {
        key: sorted(value)
        for key, value in sorted(reported_issues.items())
        if isinstance(key, str) and isinstance(value, list) and all(isinstance(issue, str) for issue in value)
    } if isinstance(reported_issues, dict) else None
    if (
        not isinstance(summary, dict)
        or summary.get("checkedPages") != 30
        or summary.get("targetsWithObservedIssues") != 7
        or summary.get("verdict") != "observed_issues"
        or normalized_reported != actual_issues
    ):
        raise ProductFlowEvidenceError("visual summary overstates or disagrees with observed issues")


def validate(
    visual_path: Path,
    root: Path,
    *,
    generation_path: Path | None = None,
    design_path: Path | None = None,
) -> int:
    root = root.resolve()
    generation = generation_path or root / "evals" / "product-flow-v4-generation-results.json"
    design = design_path or root / "evals" / "product-flow-v4-design-md-results.json"
    _validate_generation(root, generation)
    _validate_design(root, design, generation)
    _validate_visual(root, visual_path)
    return 9


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("visual_report", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        count = validate(args.visual_report, args.repository_root)
    except ProductFlowEvidenceError as error:
        parser.error(str(error))
    print(f"validated {count} Codex v4 targets, 9 DESIGN.md reports, and 30 screenshots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
