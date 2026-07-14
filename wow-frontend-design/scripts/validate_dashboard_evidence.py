#!/usr/bin/env python3
"""Validate hashes and fail semantics for the checked-in dashboard evaluation."""

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


class DashboardEvidenceError(ValueError):
    """Raised when dashboard evidence is stale or can mask acceptance failures."""


def _load(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise DashboardEvidenceError(f"cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise DashboardEvidenceError(f"{label} must be a JSON object")
    return value


def _verify(root: Path, item: Any, label: str) -> Path:
    if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
        raise DashboardEvidenceError(f"{label} must contain exactly path and sha256")
    relative, digest = item["path"], item["sha256"]
    if not isinstance(relative, str) or not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
        raise DashboardEvidenceError(f"{label} path/hash is invalid")
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts or "\x00" in relative:
        raise DashboardEvidenceError(f"{label} path is unsafe")
    path = (root / candidate).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise DashboardEvidenceError(f"{label} path escapes repository root") from error
    if not path.is_file() or path.is_symlink():
        raise DashboardEvidenceError(f"{label} path is missing or a symlink")
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise DashboardEvidenceError(f"{label} hash is stale")
    return path


def _assert_replay(report: dict[str, Any], *, mode: str, fallback_allowed: bool) -> None:
    if report.get("schema_version") != 2 or report.get("mode") != mode:
        raise DashboardEvidenceError(f"{mode} replay has wrong schema or mode")
    results = [viewport for target in report.get("results", []) for viewport in target.get("viewports", [])]
    expected_verdict = "failed" if mode == "acceptance" else "diagnostic_only"
    summary = report.get("summary")
    if not isinstance(summary, dict) or summary != {
        "checkedViewports": 4,
        "failedViewports": 4,
        "verdict": expected_verdict,
    }:
        raise DashboardEvidenceError(f"{mode} replay summary is not the fixed 4/4 failure")
    if len(results) != 4 or any(result.get("acceptancePassed") is not False for result in results):
        raise DashboardEvidenceError(f"{mode} replay must retain four failed viewport results")
    fallbacks = [
        action.get("continuationUsedDomClick")
        for result in results
        for action in (result.get("clearAction", {}), result.get("detail", {}).get("openAction", {}))
    ]
    if mode == "acceptance" and any(fallbacks):
        raise DashboardEvidenceError("acceptance replay used forbidden DOM-click continuation")
    if mode == "diagnostic" and fallback_allowed and not any(fallbacks):
        raise DashboardEvidenceError("diagnostic replay no longer demonstrates its bounded fallback")


def validate(summary_path: Path, repository_root: Path) -> int:
    if summary_path.is_symlink():
        raise DashboardEvidenceError("summary must not be a symlink")
    root = repository_root.resolve()
    summary = _load(summary_path, "dashboard summary")
    if summary.get("schema_version") != 1 or len(summary.get("runs", [])) != 2:
        raise DashboardEvidenceError("dashboard summary must retain the paired-run schema")
    _verify(root, summary.get("brief"), "brief")

    aliases = set()
    for run_index, run in enumerate(summary["runs"]):
        aliases.add(run.get("requested_alias"))
        if run.get("verdict") != "failed_strict_acceptance":
            raise DashboardEvidenceError(f"runs[{run_index}] must retain failed strict acceptance")
        _verify(root, run.get("manifest"), f"runs[{run_index}].manifest")
        screenshots = run.get("screenshots")
        if not isinstance(screenshots, list) or len(screenshots) != 2:
            raise DashboardEvidenceError(f"runs[{run_index}] must retain desktop/mobile screenshots")
        for shot_index, screenshot in enumerate(screenshots):
            item = {"path": screenshot.get("path"), "sha256": screenshot.get("sha256")}
            image = _verify(root, item, f"runs[{run_index}].screenshots[{shot_index}]")
            try:
                png_metadata(image.read_bytes())
            except LedgerError as error:
                raise DashboardEvidenceError(f"dashboard screenshot failed full PNG decode: {error}") from error
    if aliases != {"haiku", "opus"}:
        raise DashboardEvidenceError("paired aliases must remain haiku and opus")

    replays = summary.get("evaluator_replays")
    if not isinstance(replays, dict):
        raise DashboardEvidenceError("evaluator_replays is required")
    _verify(root, replays.get("script"), "evaluator_replays.script")
    _verify(root, replays.get("dependency_lock"), "evaluator_replays.dependency_lock")
    for name, mode, exit_code, fallback_allowed in (
        ("acceptance", "acceptance", 1, False),
        ("diagnostic", "diagnostic", 0, True),
    ):
        record = replays.get(name)
        if not isinstance(record, dict) or record.get("exit_code") != exit_code:
            raise DashboardEvidenceError(f"{name} replay exit code boundary is invalid")
        report_path = _verify(root, {"path": record.get("path"), "sha256": record.get("sha256")}, f"{name} replay")
        _assert_replay(_load(report_path, f"{name} replay"), mode=mode, fallback_allowed=fallback_allowed)
    remediation = summary.get("remediation_run")
    if not isinstance(remediation, dict) or remediation.get("status") != "rejected_before_publish":
        raise DashboardEvidenceError("remediation must remain rejected before publish")
    _verify(root, remediation.get("record"), "remediation record")
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path)
    parser.add_argument("--repository-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        count = validate(args.summary.expanduser(), args.repository_root.expanduser())
    except DashboardEvidenceError as error:
        print(f"dashboard evidence invalid: {error}", file=sys.stderr)
        return 1
    print(f"dashboard evidence valid: {count} failed model runs retained")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
