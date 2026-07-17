#!/usr/bin/env python3
"""Project one pinned source-layout probe into a bounded advisory sidecar."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "evals" / "v7-source-layout-probe-contract.json"
SHA256 = __import__("re").compile(r"[0-9a-f]{64}")
REPORT_KEYS = {
    "schema_version", "status", "claim_boundary", "scanned_files",
    "scan_truncated", "finding_count", "findings",
}
FINDING_KEYS = {"code", "severity", "path", "line", "evidence", "confirmation"}
MAX_REPORT_FIELD_CHARS = 8_192
REGISTRY_BOUNDARY = (
    "Source-risk advisory only; it is neither rendered evidence nor a visual, "
    "interaction, accessibility, or conformance pass."
)


class V7SupportingProbeError(ValueError):
    """Raised when a sidecar cannot be validated without inventing evidence."""


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _load(path: Path, label: str, maximum: int = 2 * 1024 * 1024) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > maximum:
        raise V7SupportingProbeError(f"{label} is missing, unsafe or oversized")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise V7SupportingProbeError(f"cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise V7SupportingProbeError(f"{label} root must be an object")
    return value


def _safe_bound_file(root: Path, record: Any, label: str) -> Path:
    if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
        raise V7SupportingProbeError(f"{label} binding is malformed")
    raw = record.get("path")
    if not isinstance(raw, str) or not raw or raw.startswith("/") or ".." in Path(raw).parts:
        raise V7SupportingProbeError(f"{label} path is unsafe")
    current = root
    for part in Path(raw).parts:
        current = current / part
        if current.is_symlink():
            raise V7SupportingProbeError(f"{label} traverses a symlink")
    resolved = current.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise V7SupportingProbeError(f"{label} escapes the repository") from error
    if not resolved.is_file() or _digest(resolved) != record.get("sha256"):
        raise V7SupportingProbeError(f"{label} binding is stale")
    return resolved


def load_contract(repository_root: Path, contract_path: Path = CONTRACT_PATH) -> tuple[dict[str, Any], str]:
    root = repository_root.resolve(strict=True)
    contract = _load(contract_path, "source-layout probe contract", 64 * 1024)
    if set(contract) != {
        "schema_version", "probe_id", "script", "dependency", "report_schema_version",
        "report_claim_boundary", "registry_claim_boundary", "codes", "limits",
    } or contract.get("schema_version") != 1 or contract.get("probe_id") != "source-layout-v1":
        raise V7SupportingProbeError("source-layout probe contract schema changed")
    if contract.get("report_schema_version") != 1 or contract.get("registry_claim_boundary") != REGISTRY_BOUNDARY:
        raise V7SupportingProbeError("source-layout probe contract boundary changed")
    codes = contract.get("codes")
    expected_codes = {
        "fixed_text_clipping": ("high", True),
        "forced_body_break": ("medium", False),
        "global_emergency_breaking": ("high", True),
        "heading_latin_ch_measure": ("medium", False),
        "prose_wrap_disabled": ("high", True),
    }
    if not isinstance(codes, dict) or {
        key: (value.get("severity"), value.get("project"))
        for key, value in codes.items() if isinstance(value, dict) and set(value) == {"severity", "project"}
    } != expected_codes:
        raise V7SupportingProbeError("source-layout probe code allowlist changed")
    if contract.get("limits") != {
        "max_advisories": 3, "max_files": 2,
        "max_subject_bytes": 1_048_576, "timeout_seconds": 5,
    }:
        raise V7SupportingProbeError("source-layout probe limits changed")
    _safe_bound_file(root, contract["script"], "source-layout script")
    _safe_bound_file(root, contract["dependency"], "source-layout dependency")
    return contract, _digest(contract_path)


def _subject(target_root: Path, maximum: int) -> tuple[Path, dict[str, Any]]:
    root = target_root.resolve(strict=True)
    index = root / "index.html"
    if (
        not root.is_dir()
        or target_root.is_symlink()
        or not index.is_file()
        or index.is_symlink()
        or index.stat().st_size < 1
        or index.stat().st_size > maximum
    ):
        raise V7SupportingProbeError("source-layout subject is missing, unsafe or oversized")
    return index, {"path": "index.html", "bytes": index.stat().st_size, "sha256": _digest(index)}


def _unavailable(
    contract: dict[str, Any],
    contract_sha256: str,
    subject: dict[str, Any],
    reason_code: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "probe": {
            "id": contract["probe_id"],
            "contract_sha256": contract_sha256,
            "script": contract["script"],
            "dependency": contract["dependency"],
            "report_schema_version": contract["report_schema_version"],
        },
        "subject": subject,
        "coverage": {
            "status": "unavailable",
            "reason_code": reason_code,
            "scanned_files": 0,
            "scan_truncated": False,
        },
        "claim_boundary": contract["registry_claim_boundary"],
        "advisories": [],
    }


def project_report(
    report: dict[str, Any],
    contract: dict[str, Any],
    contract_sha256: str,
    subject: dict[str, Any],
) -> dict[str, Any]:
    if (
        set(report) != REPORT_KEYS
        or isinstance(report.get("schema_version"), bool)
        or not isinstance(report.get("schema_version"), int)
        or report.get("schema_version") != contract["report_schema_version"]
    ):
        return _unavailable(contract, contract_sha256, subject, "report_schema_invalid")
    findings = report.get("findings")
    status = report.get("status")
    if (
        report.get("claim_boundary") != contract["report_claim_boundary"]
        or not isinstance(report.get("scan_truncated"), bool)
        or report["scan_truncated"] is not False
        or isinstance(report.get("scanned_files"), bool)
        or not isinstance(report.get("scanned_files"), int)
        or report["scanned_files"] != 1
        or not isinstance(findings, list)
        or isinstance(report.get("finding_count"), bool)
        or not isinstance(report.get("finding_count"), int)
        or report["finding_count"] != len(findings)
        or status not in {"risks_found", "no_source_risks_observed"}
        or (status == "risks_found") != bool(findings)
    ):
        return _unavailable(contract, contract_sha256, subject, "report_coverage_invalid")
    selected: dict[tuple[str, str], dict[str, Any]] = {}
    for finding in findings:
        if not isinstance(finding, dict) or set(finding) != FINDING_KEYS:
            return _unavailable(contract, contract_sha256, subject, "finding_schema_invalid")
        code = finding.get("code")
        specification = contract["codes"].get(code)
        evidence = finding.get("evidence")
        confirmation = finding.get("confirmation")
        if (
            not isinstance(specification, dict)
            or finding.get("severity") != specification["severity"]
            or finding.get("path") != "index.html"
            or isinstance(finding.get("line"), bool)
            or not isinstance(finding.get("line"), int)
            or not 1 <= finding["line"] <= 1_000_000
            or not isinstance(evidence, str)
            or not 0 < len(evidence) <= MAX_REPORT_FIELD_CHARS
            or not isinstance(confirmation, str)
            or not 0 < len(confirmation) <= MAX_REPORT_FIELD_CHARS
        ):
            return _unavailable(contract, contract_sha256, subject, "finding_contract_invalid")
        if not specification["project"]:
            continue
        key = (code, "index.html")
        current = selected.get(key)
        if current is None or finding["line"] < current["line"]:
            selected[key] = {"code": code, "severity": "high", "path": "index.html", "line": finding["line"]}
    if len(selected) > contract["limits"]["max_advisories"]:
        return _unavailable(contract, contract_sha256, subject, "advisory_limit_exceeded")
    advisories = []
    for item in sorted(selected.values(), key=lambda value: (value["code"], value["path"], value["line"])):
        item = dict(item)
        item["dedupe_key"] = _canonical_sha256({
            "probe": contract["probe_id"], "code": item["code"], "path": item["path"],
        })
        advisories.append(item)
    return {
        "schema_version": 1,
        "probe": {
            "id": contract["probe_id"],
            "contract_sha256": contract_sha256,
            "script": contract["script"],
            "dependency": contract["dependency"],
            "report_schema_version": contract["report_schema_version"],
        },
        "subject": subject,
        "coverage": {
            "status": "complete",
            "reason_code": None,
            "scanned_files": 1,
            "scan_truncated": False,
        },
        "claim_boundary": contract["registry_claim_boundary"],
        "advisories": advisories,
    }


def run_source_layout_probe(
    target_root: Path,
    repository_root: Path = ROOT,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    try:
        contract, contract_sha256 = load_contract(repository_root)
        index, subject = _subject(target_root, contract["limits"]["max_subject_bytes"])
    except (OSError, V7SupportingProbeError):
        raise
    with tempfile.TemporaryDirectory(prefix="wow-v7-source-probe-") as directory:
        isolated = Path(directory)
        shutil.copy2(index, isolated / "index.html")
        command = [
            sys.executable,
            str((repository_root / contract["script"]["path"]).resolve(strict=True)),
            str(isolated),
            "--authorized-root", str(isolated),
            "--max-files", str(contract["limits"]["max_files"]),
            "--fail-on", "none",
        ]
        try:
            completed = runner(
                command,
                cwd=repository_root,
                capture_output=True,
                text=True,
                timeout=contract["limits"]["timeout_seconds"],
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return _unavailable(contract, contract_sha256, subject, "probe_execution_unavailable")
    if completed.returncode != 0 or len(completed.stdout.encode("utf-8")) > 2 * 1024 * 1024:
        return _unavailable(contract, contract_sha256, subject, "probe_execution_failed")
    try:
        current_contract, current_contract_sha256 = load_contract(repository_root)
        _current_index, current_subject = _subject(
            target_root, contract["limits"]["max_subject_bytes"]
        )
    except (OSError, V7SupportingProbeError):
        return _unavailable(contract, contract_sha256, subject, "probe_provenance_drift")
    if current_contract != contract or current_contract_sha256 != contract_sha256:
        return _unavailable(contract, contract_sha256, subject, "probe_provenance_drift")
    if current_subject != subject:
        return _unavailable(contract, contract_sha256, subject, "probe_subject_drift")
    try:
        report = json.loads(completed.stdout)
    except (TypeError, UnicodeError, json.JSONDecodeError):
        return _unavailable(contract, contract_sha256, subject, "probe_output_invalid")
    if not isinstance(report, dict):
        return _unavailable(contract, contract_sha256, subject, "probe_output_invalid")
    registry = project_report(report, contract, contract_sha256, subject)
    try:
        validate_registry(registry, target_root, repository_root)
    except V7SupportingProbeError:
        return _unavailable(contract, contract_sha256, subject, "probe_validation_failed")
    return registry


def validate_registry_file(
    path: Path,
    expected_sha256: str,
    target_root: Path,
    repository_root: Path,
) -> dict[str, Any]:
    if not isinstance(expected_sha256, str) or SHA256.fullmatch(expected_sha256) is None:
        raise V7SupportingProbeError("supporting registry hash is malformed")
    registry = _load(path, "supporting registry")
    if _digest(path) != expected_sha256:
        raise V7SupportingProbeError("supporting registry hash changed")
    validate_registry(registry, target_root, repository_root)
    return registry


def advisory_feedback(registry: dict[str, Any]) -> str:
    advisories = registry.get("advisories") if isinstance(registry, dict) else None
    if not isinstance(advisories, list) or not advisories:
        return ""
    labels = ", ".join(f"{item['code']}@index.html:{item['line']}" for item in advisories)
    return (
        f"SOURCE-RISK ADVISORY (not rendered evidence): {labels}. "
        "Only address it when it shares the verified browser finding's root cause; "
        "Playwright remains authoritative."
    )


def validate_registry(
    registry: dict[str, Any],
    target_root: Path,
    repository_root: Path,
) -> str:
    contract, contract_sha256 = load_contract(repository_root)
    _index, subject = _subject(target_root, contract["limits"]["max_subject_bytes"])
    if not isinstance(registry, dict) or set(registry) != {
        "schema_version", "probe", "subject", "coverage", "claim_boundary", "advisories",
    }:
        raise V7SupportingProbeError("supporting registry schema changed")
    probe = registry.get("probe")
    if not isinstance(probe, dict) or probe != {
        "id": contract["probe_id"],
        "contract_sha256": contract_sha256,
        "script": contract["script"],
        "dependency": contract["dependency"],
        "report_schema_version": contract["report_schema_version"],
    }:
        raise V7SupportingProbeError("supporting registry provenance changed")
    if registry.get("schema_version") != 1 or registry.get("subject") != subject:
        raise V7SupportingProbeError("supporting registry subject changed")
    if registry.get("claim_boundary") != REGISTRY_BOUNDARY:
        raise V7SupportingProbeError("supporting registry claim boundary changed")
    coverage = registry.get("coverage")
    advisories = registry.get("advisories")
    if not isinstance(coverage, dict) or not isinstance(advisories, list):
        raise V7SupportingProbeError("supporting registry coverage changed")
    if coverage.get("status") == "unavailable":
        if advisories or not isinstance(coverage.get("reason_code"), str):
            raise V7SupportingProbeError("unavailable registry invented advisories")
        return ""
    if coverage != {
        "status": "complete", "reason_code": None, "scanned_files": 1, "scan_truncated": False,
    }:
        raise V7SupportingProbeError("supporting registry coverage is invalid")
    if len(advisories) > contract["limits"]["max_advisories"]:
        raise V7SupportingProbeError("supporting registry exceeds its advisory limit")
    seen = set()
    for item in advisories:
        if not isinstance(item, dict) or set(item) != {"code", "severity", "path", "line", "dedupe_key"}:
            raise V7SupportingProbeError("supporting advisory schema changed")
        expected = _canonical_sha256({
            "probe": contract["probe_id"], "code": item.get("code"), "path": item.get("path"),
        })
        if (
            item.get("code") not in contract["codes"]
            or contract["codes"][item["code"]] != {"severity": "high", "project": True}
            or item.get("severity") != "high"
            or item.get("path") != "index.html"
            or isinstance(item.get("line"), bool)
            or not isinstance(item.get("line"), int)
            or not 1 <= item["line"] <= 1_000_000
            or item.get("dedupe_key") != expected
            or expected in seen
        ):
            raise V7SupportingProbeError("supporting advisory is invalid or duplicated")
        seen.add(expected)
    if advisories != sorted(advisories, key=lambda value: (value["code"], value["path"], value["line"])):
        raise V7SupportingProbeError("supporting advisories are not canonical")
    return advisory_feedback(registry)
