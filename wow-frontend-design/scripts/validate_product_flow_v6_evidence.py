#!/usr/bin/env python3
"""Validate the published Codex v6 repair cohort and 64 screenshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from evidence_ledger import LedgerError, png_metadata


MODEL = "gpt-5.4-mini"
ALIAS = f"codex-{MODEL}"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
CASES = {
    "wind-maintenance-dispatch-v6": ("index.html",),
    "type-foundry-specimen-v6": ("index.html",),
    "repair-cafe-intake-v6": ("index.html",),
    "night-market-allergen-v6": ("index.html",),
    "royalty-statement-v6": ("index.html",),
    "packaging-configurator-v6": ("index.html", "materials.html", "summary.html"),
    "oral-history-archive-v6": ("index.html", "archive.html", "story.html"),
    "grant-review-board-v6": ("index.html",),
}
VIEWPORTS = {
    "desktop": (1440, 1000, 1, False, False),
    "tablet": (834, 1112, 2, True, True),
    "mobile": (390, 844, 3, True, True),
    "compact-mobile": (360, 800, 3, True, True),
}
ARTIFACT_ROOT = "evals/product-flow-v6-repaired-v2-targets"
GENERATION_PATH = "evals/product-flow-v6-repaired-v2-generation-results.json"
DESIGN_PATH = "evals/product-flow-v6-repaired-v2-design-md-results.json"
AUDITOR_PATH = "evals/playwright_visual_v6_audit.cjs"
SCREENSHOT_ROOT = "assets/product-flow-v6"


class ProductFlowV6EvidenceError(ValueError):
    """Raised when checked-in v6 evidence is stale or incomplete."""


def _load(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ProductFlowV6EvidenceError(f"{label} is missing or unsafe")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProductFlowV6EvidenceError(f"cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise ProductFlowV6EvidenceError(f"{label} must be a JSON object")
    return value


def _artifact(root: Path, relative: Any, label: str, *, directory: bool = False) -> Path:
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        raise ProductFlowV6EvidenceError(f"{label} path is invalid")
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ProductFlowV6EvidenceError(f"{label} path is unsafe")
    path = (root / candidate).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ProductFlowV6EvidenceError(f"{label} escapes repository root") from error
    valid = path.is_dir() if directory else path.is_file()
    if not valid or path.is_symlink():
        raise ProductFlowV6EvidenceError(f"{label} is missing or unsafe")
    return path


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_source_manifest(root: Path, record: Any, label: str) -> None:
    if not isinstance(record, dict):
        raise ProductFlowV6EvidenceError(f"{label} provenance is missing")
    source = _artifact(root, record.get("path"), label)
    if record.get("sha256") != _digest(source):
        raise ProductFlowV6EvidenceError(f"{label} hash is stale")


def _validate_generation(root: Path, path: Path) -> None:
    ledger = _load(path, "generation ledger")
    if ledger.get("schema_version") != 1 or ledger.get("status") != "completed":
        raise ProductFlowV6EvidenceError("generation ledger is incomplete")
    if ledger.get("selection") != {"provider": "codex", "model": MODEL, "theme": "all", "count": 8}:
        raise ProductFlowV6EvidenceError("generation ledger is not the exact Codex v6 mini cohort")
    if ledger.get("summary") != {
        "requested": 8,
        "completed": 8,
        "failed": 0,
        "repaired_cases": 1,
        "promoted_clean_cases": 7,
    }:
        raise ProductFlowV6EvidenceError("generation repair summary changed")
    contract = ledger.get("contract")
    if not isinstance(contract, dict):
        raise ProductFlowV6EvidenceError("generation contract is missing")
    if Path(str(contract.get("artifact_root"))).resolve() != (root / ARTIFACT_ROOT).resolve():
        raise ProductFlowV6EvidenceError("generation artifact root changed")
    briefs = contract.get("briefs")
    outputs_by_case = contract.get("outputs_by_case")
    if not isinstance(briefs, dict) or set(briefs) != set(CASES) or not isinstance(outputs_by_case, dict):
        raise ProductFlowV6EvidenceError("generation case contract changed")
    for case_id, record in briefs.items():
        if not isinstance(record, dict):
            raise ProductFlowV6EvidenceError(f"brief record is malformed for {case_id}")
        brief = _artifact(root, record.get("path"), f"brief {case_id}")
        if record.get("sha256") != _digest(brief):
            raise ProductFlowV6EvidenceError(f"brief hash is stale for {case_id}")
        if outputs_by_case.get(case_id) != ["DESIGN.md", *CASES[case_id]]:
            raise ProductFlowV6EvidenceError(f"output contract changed for {case_id}")

    results = ledger.get("results")
    if not isinstance(results, list) or len(results) != len(CASES):
        raise ProductFlowV6EvidenceError("generation result inventory changed")
    seen: set[str] = set()
    repair_cases = 0
    for result in results:
        if not isinstance(result, dict):
            raise ProductFlowV6EvidenceError("generation result is malformed")
        case_id = result.get("case_id")
        if case_id not in CASES or case_id in seen:
            raise ProductFlowV6EvidenceError("generation case identity changed")
        seen.add(str(case_id))
        mode = result.get("evidence_mode")
        expected_mode = "repair" if case_id == "oral-history-archive-v6" else "promoted_clean"
        if (
            result.get("provider") != "codex"
            or result.get("model") != MODEL
            or result.get("status") != "completed"
            or mode != expected_mode
        ):
            raise ProductFlowV6EvidenceError(f"generation result changed for {case_id}")
        repair_cases += int(mode == "repair")
        target_value = f"{ARTIFACT_ROOT}/{ALIAS}-{case_id}"
        manifest_value = f"{target_value}/run-manifest.json"
        if result.get("target") != target_value or result.get("manifest") != manifest_value:
            raise ProductFlowV6EvidenceError(f"generation path changed for {case_id}")
        target = _artifact(root, target_value, f"target {case_id}", directory=True)
        manifest_path = _artifact(root, manifest_value, f"manifest {case_id}")
        manifest = _load(manifest_path, f"manifest {case_id}")
        if (
            manifest.get("schema_version") != 1
            or manifest.get("status") != "completed"
            or manifest.get("case") != {"id": case_id, "target": target_value}
            or manifest.get("model", {}).get("requested_identifier") != MODEL
        ):
            raise ProductFlowV6EvidenceError(f"manifest contract changed for {case_id}")
        manifest_outputs = manifest.get("outputs")
        expected_outputs = {"DESIGN.md", *CASES[str(case_id)]}
        if not isinstance(manifest_outputs, list) or {
            item.get("path") for item in manifest_outputs if isinstance(item, dict)
        } != expected_outputs:
            raise ProductFlowV6EvidenceError(f"manifest output inventory changed for {case_id}")
        for output in manifest_outputs:
            if not isinstance(output, dict):
                raise ProductFlowV6EvidenceError(f"manifest output is malformed for {case_id}")
            artifact = target / str(output.get("path"))
            if not artifact.is_file() or artifact.is_symlink():
                raise ProductFlowV6EvidenceError(f"manifest output is missing for {case_id}")
            if output.get("bytes") != artifact.stat().st_size or output.get("sha256") != _digest(artifact):
                raise ProductFlowV6EvidenceError(f"manifest output hash is stale for {case_id}")
        provenance = manifest.get("repair") if mode == "repair" else manifest.get("promotion")
        if not isinstance(provenance, dict):
            raise ProductFlowV6EvidenceError(f"repair provenance is missing for {case_id}")
        _validate_source_manifest(root, provenance.get("source_manifest"), f"source manifest {case_id}")
    if seen != set(CASES) or repair_cases != 1:
        raise ProductFlowV6EvidenceError("generation repair inventory changed")


def _validate_design(root: Path, path: Path, generation_path: Path) -> None:
    report = _load(path, "DESIGN.md lint report")
    generation_ref = report.get("generation_ledger")
    if (
        report.get("schema_version") != 1
        or report.get("linter") != {"package": "@google/design.md", "version": "0.3.0"}
        or not isinstance(generation_ref, dict)
        or generation_ref.get("path") != GENERATION_PATH
        or generation_ref.get("sha256") != _digest(generation_path)
        or report.get("summary") != {"checked": 8, "clean": 8, "with_findings": 0, "infrastructure_failures": 0}
    ):
        raise ProductFlowV6EvidenceError("DESIGN.md report provenance or clean summary changed")
    results = report.get("results")
    if not isinstance(results, list) or len(results) != len(CASES):
        raise ProductFlowV6EvidenceError("DESIGN.md result inventory changed")
    seen: set[str] = set()
    for result in results:
        if not isinstance(result, dict):
            raise ProductFlowV6EvidenceError("DESIGN.md result is malformed")
        case_id = result.get("case_id")
        if (
            case_id not in CASES
            or case_id in seen
            or result.get("provider") != "codex"
            or result.get("model") != MODEL
            or result.get("status") != "clean"
            or result.get("summary", {}).get("errors") != 0
            or result.get("summary", {}).get("warnings") != 0
        ):
            raise ProductFlowV6EvidenceError("DESIGN.md clean result changed")
        seen.add(str(case_id))
        design = _artifact(root, result.get("path"), f"DESIGN.md {case_id}")
        if result.get("sha256") != _digest(design):
            raise ProductFlowV6EvidenceError(f"DESIGN.md hash is stale for {case_id}")
    if seen != set(CASES):
        raise ProductFlowV6EvidenceError("DESIGN.md case inventory is incomplete")


def _expected_visual_results() -> set[tuple[str, str, str, str]]:
    expected = {
        (case_id, page, "base", viewport)
        for case_id, pages in CASES.items()
        for page in pages
        for viewport in VIEWPORTS
    }
    expected.update((case_id, pages[0], "interaction", viewport) for case_id, pages in CASES.items() for viewport in ("desktop", "mobile"))
    return expected


def _validate_visual(root: Path, path: Path) -> None:
    report = _load(path, "visual report")
    auditor = _artifact(root, AUDITOR_PATH, "visual auditor")
    auditor_ref = report.get("auditor")
    if (
        report.get("schema_version") != 1
        or not isinstance(auditor_ref, dict)
        or auditor_ref.get("path") != AUDITOR_PATH
        or auditor_ref.get("sha256") != _digest(auditor)
    ):
        raise ProductFlowV6EvidenceError("visual auditor provenance is stale")
    profiles = report.get("viewports")
    if not isinstance(profiles, list) or len(profiles) != len(VIEWPORTS):
        raise ProductFlowV6EvidenceError("visual viewport inventory changed")
    for profile in profiles:
        if not isinstance(profile, dict) or profile.get("name") not in VIEWPORTS:
            raise ProductFlowV6EvidenceError("visual viewport profile is malformed")
        width, height, scale, is_mobile, has_touch = VIEWPORTS[profile["name"]]
        if any((profile.get("width") != width, profile.get("height") != height, profile.get("deviceScaleFactor") != scale, profile.get("isMobile") != is_mobile, profile.get("hasTouch") != has_touch)):
            raise ProductFlowV6EvidenceError(f"visual viewport contract changed for {profile['name']}")
        if is_mobile and "Android" not in str(profile.get("userAgent")):
            raise ProductFlowV6EvidenceError(f"mobile emulation signal is missing for {profile['name']}")

    expected_targets = {(case_id, ALIAS) for case_id in CASES}
    targets = report.get("targets")
    actual_targets = {(item.get("caseId"), item.get("alias")) for item in targets if isinstance(item, dict)} if isinstance(targets, list) else set()
    if not isinstance(targets, list) or len(targets) != 8 or actual_targets != expected_targets:
        raise ProductFlowV6EvidenceError("visual target inventory changed")
    expected = _expected_visual_results()
    results = report.get("results")
    if not isinstance(results, list) or len(results) != len(expected):
        raise ProductFlowV6EvidenceError("visual report must retain exactly 64 screenshots")
    seen: set[tuple[str, str, str, str]] = set()
    screenshot_paths: set[Path] = set()
    for result in results:
        if not isinstance(result, dict):
            raise ProductFlowV6EvidenceError("visual result is malformed")
        key = (result.get("caseId"), result.get("page"), result.get("state"), result.get("viewport"))
        if key in seen or key not in expected or result.get("alias") != ALIAS:
            raise ProductFlowV6EvidenceError(f"visual screenshot identity changed: {key}")
        seen.add(key)  # type: ignore[arg-type]
        width, height, scale, _, _ = VIEWPORTS[str(key[3])]
        stem = Path(str(key[1])).stem
        expected_path = f"{SCREENSHOT_ROOT}/{key[0]}-{ALIAS}-{stem}-{key[2]}-{key[3]}.png"
        if result.get("screenshot") != expected_path or result.get("size") != f"{width}x{height}":
            raise ProductFlowV6EvidenceError(f"visual screenshot metadata changed for {key}")
        screenshot = _artifact(root, expected_path, f"screenshot {key}")
        screenshot_paths.add(screenshot)
        if result.get("screenshotSha256") != _digest(screenshot):
            raise ProductFlowV6EvidenceError(f"screenshot hash is stale for {key}")
        try:
            metadata = png_metadata(screenshot.read_bytes())
        except LedgerError as error:
            raise ProductFlowV6EvidenceError(f"screenshot decode failed for {key}: {error}") from error
        if metadata != ("image/png", width * scale, height * scale):
            raise ProductFlowV6EvidenceError(f"screenshot dimensions changed for {key}")
        body_flow = result.get("bodyFlow")
        if not isinstance(body_flow, dict) or body_flow.get("forcedLineBreaks") != [] or body_flow.get("nonWrappingProse") != []:
            raise ProductFlowV6EvidenceError(f"body flow repair finding remains for {key}")
        if result.get("visualIssues") != [] or any(result.get(field) != [] for field in ("consoleErrors", "externalRequests", "badResponses")):
            raise ProductFlowV6EvidenceError(f"runtime or visual finding remains for {key}")
    actual_pngs = {_artifact(root, str(path.relative_to(root)), "published screenshot") for path in (root / SCREENSHOT_ROOT).glob("*.png")}
    if seen != expected or screenshot_paths != actual_pngs:
        raise ProductFlowV6EvidenceError("visual screenshot file set is incomplete or has extras")
    comparisons = report.get("crossPageComparisons")
    if not isinstance(comparisons, list) or any(not isinstance(item, dict) or item.get("visualIssues") != [] for item in comparisons):
        raise ProductFlowV6EvidenceError("cross-page visual findings remain")
    expected_issues = {f"{case_id}:{ALIAS}": [] for case_id in CASES}
    if report.get("summary") != {
        "checkedPages": 64,
        "minimumExpectedScreenshots": 60,
        "targetsWithObservedIssues": 0,
        "issuesByTarget": expected_issues,
        "verdict": "no_observed_issues",
    }:
        raise ProductFlowV6EvidenceError("visual summary changed or overstates acceptance")


def validate(
    visual_path: Path,
    root: Path,
    *,
    generation_path: Path | None = None,
    design_path: Path | None = None,
) -> int:
    root = root.resolve()
    generation = generation_path or root / GENERATION_PATH
    design = design_path or root / DESIGN_PATH
    _validate_generation(root, generation)
    _validate_design(root, design, generation)
    _validate_visual(root, visual_path)
    return len(CASES)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("visual_report", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        count = validate(args.visual_report, args.repository_root)
    except ProductFlowV6EvidenceError as error:
        parser.error(str(error))
    print(f"validated {count} Codex v6 mini targets, 8 clean DESIGN.md files, and 64 screenshots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
