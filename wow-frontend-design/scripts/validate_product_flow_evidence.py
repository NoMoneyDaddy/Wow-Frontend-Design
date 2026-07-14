#!/usr/bin/env python3
"""Validate the integrity and boundaries of the three-theme v3 visual cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from evidence_ledger import LedgerError, png_metadata


SHA256 = re.compile(r"^[0-9a-f]{64}$")
MODELS = {
    ("claude", "haiku"): "claude-haiku",
    ("claude", "sonnet"): "claude-sonnet",
    ("claude", "opus"): "claude-opus",
    ("codex", "gpt-5.4-mini"): "codex-gpt-5.4-mini",
    ("codex", "gpt-5.4"): "codex-gpt-5.4",
    ("codex", "gpt-5.5"): "codex-gpt-5.5",
}
CASE_PAGES = {
    "mountain-rescue-flow-v3": ("index.html",),
    "city-poetry-festival-v3": ("index.html",),
    "bookstore-one-line-v3": ("index.html", "catalog.html", "book.html"),
}
VIEWPORTS = {"desktop": (1440, 1000), "mobile": (390, 844)}


class ProductFlowEvidenceError(ValueError):
    """Raised when v3 product-flow evidence is stale or inconsistent."""


def _load(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink():
        raise ProductFlowEvidenceError(f"{label} must not be a symlink")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProductFlowEvidenceError(f"cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise ProductFlowEvidenceError(f"{label} must be a JSON object")
    return value


def _artifact(root: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ProductFlowEvidenceError(f"{label} path is invalid")
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts or "\x00" in relative:
        raise ProductFlowEvidenceError(f"{label} path is unsafe")
    path = (root / candidate).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ProductFlowEvidenceError(f"{label} path escapes repository root") from error
    if not path.is_file() or path.is_symlink():
        raise ProductFlowEvidenceError(f"{label} path is missing or unsafe")
    return path


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expected_runs() -> set[tuple[str, str, str]]:
    return {(provider, model, case_id) for provider, model in MODELS for case_id in CASE_PAGES}


def _validate_generation(root: Path, path: Path) -> tuple[dict[str, Any], dict[tuple[str, str, str], dict[str, Any]]]:
    ledger = _load(path, "generation ledger")
    if ledger.get("schema_version") != 1 or ledger.get("selection") != {
        "provider": "all",
        "theme": "all",
        "count": 18,
    }:
        raise ProductFlowEvidenceError("generation ledger is not the fixed v3 cohort")
    if ledger.get("status") != "partial" or ledger.get("summary") != {
        "requested": 18,
        "completed": 17,
        "failed": 1,
        "statuses": {"completed": 17, "generation_failed": 1},
    }:
        raise ProductFlowEvidenceError("generation ledger must retain the 17 completed plus one connection failure outcome")
    results = ledger.get("results")
    if not isinstance(results, list) or len(results) != 18:
        raise ProductFlowEvidenceError("generation ledger must contain 18 results")
    indexed: dict[tuple[str, str, str], dict[str, Any]] = {}
    for result in results:
        if not isinstance(result, dict):
            raise ProductFlowEvidenceError("generation result is malformed")
        key = (result.get("provider"), result.get("model"), result.get("case_id"))
        if key in indexed or key not in _expected_runs():
            raise ProductFlowEvidenceError("generation model/case set is invalid")
        indexed[key] = result
        expected_failure = key == ("claude", "sonnet", "city-poetry-festival-v3")
        expected_status = "generation_failed" if expected_failure else "completed"
        if result.get("status") != expected_status:
            raise ProductFlowEvidenceError("the formal Sonnet poetry failure cannot be removed or reassigned")
        if expected_failure:
            if result.get("error_summary") != "API Error: Connection closed mid-response. The response above may be incomplete.":
                raise ProductFlowEvidenceError("the formal Sonnet infrastructure error changed")
        else:
            manifest_path = _artifact(root, result.get("manifest"), f"manifest {key}")
            manifest = _load(manifest_path, f"manifest {key}")
            if manifest.get("status") != "completed" or manifest.get("case", {}).get("id") != key[2]:
                raise ProductFlowEvidenceError(f"manifest {key} disagrees with generation ledger")
    return ledger, indexed


def _validate_retry(root: Path, path: Path, formal: dict[tuple[str, str, str], dict[str, Any]]) -> dict[str, Any]:
    ledger = _load(path, "infrastructure retry ledger")
    original = ledger.get("original_attempt")
    retry = ledger.get("retry")
    if not isinstance(original, dict) or not isinstance(retry, dict):
        raise ProductFlowEvidenceError("retry ledger is malformed")
    key = ("claude", "sonnet", "city-poetry-festival-v3")
    source = formal[key]
    if any(original.get(field) != source.get(field) for field in ("provider", "model", "case_id", "status", "duration_seconds", "exit_code", "error_summary")):
        raise ProductFlowEvidenceError("retry ledger no longer preserves the formal failed attempt")
    if (
        (retry.get("provider"), retry.get("model"), retry.get("case_id")) != key
        or retry.get("status") != "completed"
        or retry.get("visual_evaluation_eligible") is not True
        or retry.get("same_generation_context") is not True
    ):
        raise ProductFlowEvidenceError("retry must remain a labelled, same-context, one-time infrastructure retry")
    manifest_path = _artifact(root, retry.get("manifest"), "retry manifest")
    manifest = _load(manifest_path, "retry manifest")
    if manifest.get("run_id") != retry.get("run_id") or manifest.get("status") != "completed":
        raise ProductFlowEvidenceError("retry manifest disagrees with retry ledger")
    return ledger


def _validate_design(root: Path, path: Path, generation_path: Path, retry_path: Path) -> None:
    report = _load(path, "DESIGN.md lint report")
    if report.get("schema_version") != 1 or report.get("linter") != {
        "package": "@google/design.md",
        "version": "0.2.0",
    }:
        raise ProductFlowEvidenceError("DESIGN.md report must use the pinned official 0.2.0 linter")
    generation_ref = report.get("generation_ledger")
    retry_ref = report.get("supplemental_retry_ledger")
    if not isinstance(generation_ref, dict) or generation_ref.get("sha256") != _digest(generation_path):
        raise ProductFlowEvidenceError("DESIGN.md report generation-ledger hash is stale")
    if not isinstance(retry_ref, dict) or retry_ref.get("sha256") != _digest(retry_path):
        raise ProductFlowEvidenceError("DESIGN.md report retry-ledger hash is stale")
    results = report.get("results")
    if not isinstance(results, list) or len(results) != 18:
        raise ProductFlowEvidenceError("DESIGN.md report must contain all 18 model/theme results")
    seen: set[tuple[str, str, str]] = set()
    clean = findings = failures = 0
    for result in results:
        if not isinstance(result, dict):
            raise ProductFlowEvidenceError("DESIGN.md result is malformed")
        key = (result.get("provider"), result.get("model"), result.get("case_id"))
        if key in seen or key not in _expected_runs():
            raise ProductFlowEvidenceError("DESIGN.md model/case set is invalid")
        seen.add(key)
        expected_source = "infrastructure_retry" if key == ("claude", "sonnet", "city-poetry-festival-v3") else "formal_matrix"
        if result.get("evidence_source") != expected_source:
            raise ProductFlowEvidenceError("DESIGN.md evidence source hides the formal/retry boundary")
        design = _artifact(root, result.get("path"), f"DESIGN.md {key}")
        if result.get("sha256") != _digest(design):
            raise ProductFlowEvidenceError(f"DESIGN.md hash is stale for {key}")
        summary = result.get("summary")
        if not isinstance(summary, dict) or any(not isinstance(summary.get(name), int) or summary[name] < 0 for name in ("errors", "warnings", "infos")):
            raise ProductFlowEvidenceError(f"DESIGN.md summary is malformed for {key}")
        expected_status = "clean" if summary["errors"] == 0 and summary["warnings"] == 0 else "findings"
        if result.get("status") != expected_status:
            raise ProductFlowEvidenceError(f"DESIGN.md status overstates lint outcome for {key}")
        if expected_status == "clean":
            clean += 1
        else:
            findings += 1
    if seen != _expected_runs() or report.get("summary") != {
        "checked": 18,
        "clean": clean,
        "with_findings": findings,
        "infrastructure_failures": failures,
    }:
        raise ProductFlowEvidenceError("DESIGN.md aggregate summary changed")


def _expected_visuals() -> set[tuple[str, str, str, str]]:
    return {
        (case_id, alias, page, viewport)
        for alias in MODELS.values()
        for case_id, pages in CASE_PAGES.items()
        for page in pages
        for viewport in VIEWPORTS
    }


def _validate_visual(root: Path, path: Path) -> None:
    report = _load(path, "visual report")
    if report.get("schema_version") != 1 or report.get("viewports") != [
        {"name": "desktop", "width": 1440, "height": 1000},
        {"name": "mobile", "width": 390, "height": 844},
    ]:
        raise ProductFlowEvidenceError("visual report viewport contract changed")
    targets = report.get("targets")
    expected_targets = {(case_id, alias) for alias in MODELS.values() for case_id in CASE_PAGES}
    actual_targets = {
        (target.get("caseId"), target.get("alias"))
        for target in targets
        if isinstance(target, dict)
    } if isinstance(targets, list) else set()
    if len(targets or []) != 18 or actual_targets != expected_targets:
        raise ProductFlowEvidenceError("visual report must retain all 18 targets")
    results = report.get("results")
    if not isinstance(results, list) or len(results) != 60:
        raise ProductFlowEvidenceError("visual report must retain exactly 60 page/viewport results")
    seen: set[tuple[str, str, str, str]] = set()
    for result in results:
        if not isinstance(result, dict):
            raise ProductFlowEvidenceError("visual result is malformed")
        key = (result.get("caseId"), result.get("alias"), result.get("page"), result.get("viewport"))
        if key in seen or key not in _expected_visuals():
            raise ProductFlowEvidenceError("visual screenshot inventory changed")
        seen.add(key)
        width, height = VIEWPORTS[key[3]]
        expected_path = f"assets/product-flow-v3/{key[0]}-{key[1]}-{Path(key[2]).stem}-{key[3]}.png"
        if result.get("screenshot") != expected_path or result.get("size") != f"{width}x{height}":
            raise ProductFlowEvidenceError(f"visual screenshot metadata changed for {key}")
        screenshot = _artifact(root, expected_path, f"screenshot {key}")
        digest = result.get("screenshotSha256")
        if not isinstance(digest, str) or SHA256.fullmatch(digest) is None or digest != _digest(screenshot):
            raise ProductFlowEvidenceError(f"screenshot hash is stale for {key}")
        try:
            media_type, decoded_width, decoded_height = png_metadata(screenshot.read_bytes())
        except LedgerError as error:
            raise ProductFlowEvidenceError(f"screenshot failed full PNG decode for {key}: {error}") from error
        if (media_type, decoded_width, decoded_height) != ("image/png", width, height):
            raise ProductFlowEvidenceError(f"screenshot dimensions changed for {key}")
        if any(result.get(field) != [] for field in ("consoleErrors", "externalRequests", "badResponses")):
            raise ProductFlowEvidenceError(f"screenshot page has runtime/network failures for {key}")
    if seen != _expected_visuals():
        raise ProductFlowEvidenceError("visual screenshot set is incomplete")
    comparisons = report.get("crossPageComparisons")
    if not isinstance(comparisons, list) or len(comparisons) != 12:
        raise ProductFlowEvidenceError("bookstore must retain desktop/mobile cross-page comparisons for all six models")
    summary = report.get("summary")
    if not isinstance(summary, dict) or summary.get("checkedPages") != 60 or summary.get("verdict") != "observed_issues":
        raise ProductFlowEvidenceError("visual report must preserve observed issues rather than overstate a pass")
    issues = summary.get("issuesByTarget")
    if not isinstance(issues, dict) or set(issues) != {f"{case_id}:{alias}" for case_id, alias in expected_targets}:
        raise ProductFlowEvidenceError("visual issue summary target set changed")


def _validate_manual(path: Path) -> None:
    report = _load(path, "manual review")
    method = report.get("method")
    if report.get("schema_version") != 1 or not isinstance(method, dict) or method.get("screenshots_reviewed") != 60:
        raise ProductFlowEvidenceError("manual review must retain the 60-screenshot boundary")
    results = report.get("results")
    if not isinstance(results, list) or len(results) != 18:
        raise ProductFlowEvidenceError("manual review must contain 18 model/theme observations")
    expected = {(case_id, alias) for alias in MODELS.values() for case_id in CASE_PAGES}
    actual: set[tuple[str, str]] = set()
    allowed = {"pass", "mixed", "fail", "not_applicable"}
    for result in results:
        if not isinstance(result, dict):
            raise ProductFlowEvidenceError("manual review result is malformed")
        key = (result.get("case_id"), result.get("model"))
        if key in actual or key not in expected:
            raise ProductFlowEvidenceError("manual review model/theme set changed")
        actual.add(key)
        for field in ("hierarchy", "responsive_composition", "text_integrity", "authored_distinction", "multi_page_visual_coherence"):
            if result.get(field) not in allowed:
                raise ProductFlowEvidenceError(f"manual review field {field} is invalid for {key}")
        if not isinstance(result.get("observation"), str) or not result["observation"].strip():
            raise ProductFlowEvidenceError(f"manual review observation is missing for {key}")
    if actual != expected:
        raise ProductFlowEvidenceError("manual review set is incomplete")


def validate(
    visual_path: Path,
    repository_root: Path,
    *,
    generation_path: Path | None = None,
    retry_path: Path | None = None,
    design_path: Path | None = None,
    manual_path: Path | None = None,
) -> int:
    root = repository_root.resolve()
    generation_path = generation_path or root / "evals" / "product-flow-v3-generation-results.json"
    retry_path = retry_path or root / "evals" / "product-flow-v3-infrastructure-retry.json"
    design_path = design_path or root / "evals" / "product-flow-v3-design-md-results.json"
    manual_path = manual_path or root / "evals" / "product-flow-v3-manual-review.json"
    _, formal = _validate_generation(root, generation_path)
    _validate_retry(root, retry_path, formal)
    _validate_design(root, design_path, generation_path, retry_path)
    _validate_visual(root, visual_path)
    _validate_manual(manual_path)
    return 18


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("visual_report", type=Path)
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--generation", type=Path)
    parser.add_argument("--retry", type=Path)
    parser.add_argument("--design", type=Path)
    parser.add_argument("--manual", type=Path)
    args = parser.parse_args()
    try:
        count = validate(
            args.visual_report.expanduser(),
            args.repository_root.expanduser(),
            generation_path=args.generation.expanduser() if args.generation else None,
            retry_path=args.retry.expanduser() if args.retry else None,
            design_path=args.design.expanduser() if args.design else None,
            manual_path=args.manual.expanduser() if args.manual else None,
        )
    except ProductFlowEvidenceError as error:
        print(f"product-flow evidence invalid: {error}", file=sys.stderr)
        return 1
    print(f"product-flow v3 evidence valid: {count} model/theme targets and 60 screenshots retained")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
