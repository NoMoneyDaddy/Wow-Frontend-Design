#!/usr/bin/env python3
"""Assemble a complete v6 ledger from repaired and unchanged verified targets."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CASE_PAGES = {
    "wind-maintenance-dispatch-v6": ("index.html",),
    "type-foundry-specimen-v6": ("index.html",),
    "repair-cafe-intake-v6": ("index.html",),
    "night-market-allergen-v6": ("index.html",),
    "royalty-statement-v6": ("index.html",),
    "packaging-configurator-v6": ("index.html", "materials.html", "summary.html"),
    "oral-history-archive-v6": ("index.html", "archive.html", "story.html"),
    "grant-review-board-v6": ("index.html",),
}


class AssemblyError(ValueError):
    """Raised when repair evidence is incomplete or inconsistent."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-ledger", required=True, type=Path)
    parser.add_argument("--repaired-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--promote-clean", action="append", default=[])
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def load_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise AssemblyError(f"{label} is missing or unsafe: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AssemblyError(f"cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise AssemblyError(f"{label} must be a JSON object")
    return value


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def required_outputs(case_id: str) -> tuple[str, ...]:
    try:
        return ("DESIGN.md", *CASE_PAGES[case_id])
    except KeyError as error:
        raise AssemblyError(f"unknown v6 case: {case_id}") from error


def validate_outputs(target: Path, case_id: str, manifest: dict[str, Any]) -> None:
    records = manifest.get("outputs")
    if not isinstance(records, list):
        raise AssemblyError(f"manifest has no outputs list: {target}")
    by_path = {
        record.get("path"): record
        for record in records
        if isinstance(record, dict) and isinstance(record.get("path"), str)
    }
    expected = set(required_outputs(case_id))
    if set(by_path) != expected:
        raise AssemblyError(f"manifest output inventory disagrees for {case_id}")
    for name in expected:
        artifact = target / name
        record = by_path[name]
        if not artifact.is_file() or artifact.is_symlink():
            raise AssemblyError(f"output is missing or unsafe: {artifact}")
        if record.get("sha256") != digest(artifact) or record.get("bytes") != artifact.stat().st_size:
            raise AssemblyError(f"output integrity disagrees: {artifact}")


def promote_clean_target(source: Path, target: Path, case_id: str) -> None:
    if target.is_symlink() or not target.is_dir():
        raise AssemblyError(f"promotion target is missing or unsafe: {target}")
    if any(target.iterdir()):
        raise AssemblyError(f"promotion target is not empty: {target}")
    source_manifest_path = source / "run-manifest.json"
    source_manifest = load_object(source_manifest_path, "source manifest")
    validate_outputs(source, case_id, source_manifest)
    for name in required_outputs(case_id):
        shutil.copy2(source / name, target / name)
    promoted = copy.deepcopy(source_manifest)
    promoted["run_id"] = f"{source_manifest.get('run_id', 'unknown')}-promoted-clean"
    promoted["status"] = "completed"
    promoted["finished_at"] = utc_now()
    promoted["case"] = {"id": case_id, "target": display_path(target)}
    promoted["mode"] = "promoted_clean"
    promoted["promotion"] = {
        "reason": "independent_visual_audit_found_no_observed_issues",
        "source_manifest": {
            "path": display_path(source_manifest_path),
            "sha256": digest(source_manifest_path),
        },
        "changed_outputs": [],
    }
    write_json(target / "run-manifest.json", promoted)


def write_json(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise AssemblyError(f"refusing to overwrite existing artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> int:
    args = parse_args()
    ledger_path = args.source_ledger.expanduser().resolve()
    repaired_root = args.repaired_root.expanduser().resolve()
    output = args.output.expanduser().resolve()
    ledger = load_object(ledger_path, "source ledger")
    results = ledger.get("results")
    if ledger.get("status") != "completed" or not isinstance(results, list):
        raise AssemblyError("source generation ledger is incomplete")
    if repaired_root.is_symlink() or not repaired_root.is_dir():
        raise AssemblyError("repaired root is missing or unsafe")
    promote = set(args.promote_clean)
    if not promote.issubset(CASE_PAGES):
        raise AssemblyError(f"unknown clean cases: {sorted(promote - set(CASE_PAGES))}")

    assembled = copy.deepcopy(ledger)
    contract = assembled.get("contract")
    if not isinstance(contract, dict):
        raise AssemblyError("source ledger has no contract")
    source_root_value = contract.get("artifact_root")
    if not isinstance(source_root_value, str):
        raise AssemblyError("source ledger has no artifact root")
    source_root = Path(source_root_value).resolve()
    if source_root.is_symlink() or not source_root.is_dir():
        raise AssemblyError("source artifact root is missing or unsafe")
    contract["artifact_root"] = str(repaired_root)
    contract["repair_assembly"] = {
        "source_ledger": {"path": display_path(ledger_path), "sha256": digest(ledger_path)},
        "promoted_clean_cases": sorted(promote),
    }

    assembled_results = assembled.get("results")
    if not isinstance(assembled_results, list):
        raise AssemblyError("assembled ledger has no results list")
    repaired_count = 0
    promoted_count = 0
    for result in assembled_results:
        if not isinstance(result, dict):
            raise AssemblyError("source ledger result must be an object")
        case_id = result.get("case_id")
        provider = result.get("provider")
        model = result.get("model")
        if not isinstance(case_id, str) or case_id not in CASE_PAGES:
            raise AssemblyError(f"invalid source case: {case_id}")
        target_name = f"{provider}-{model}-{case_id}"
        source_target = source_root / target_name
        target = repaired_root / target_name
        if case_id in promote:
            promote_clean_target(source_target, target, case_id)
            promoted_count += 1
        manifest_path = target / "run-manifest.json"
        manifest = load_object(manifest_path, "assembled manifest")
        case = manifest.get("case")
        if not isinstance(case, dict) or case.get("id") != case_id or Path(str(case.get("target", ""))).name != target_name:
            raise AssemblyError(f"manifest identity disagrees for {case_id}")
        if manifest.get("model", {}).get("requested_identifier") != model:
            raise AssemblyError(f"manifest model disagrees for {case_id}")
        validate_outputs(target, case_id, manifest)
        mode = manifest.get("mode")
        if mode == "repair":
            repaired_count += 1
        elif mode != "promoted_clean":
            raise AssemblyError(f"assembled target lacks repair provenance: {case_id}")
        result.update(
            target=display_path(target),
            status="completed",
            manifest=display_path(manifest_path),
            evidence_mode=mode,
        )

    if repaired_count + promoted_count != len(assembled_results):
        raise AssemblyError("assembled result count disagrees")
    assembled["started_at"] = ledger.get("started_at")
    assembled["finished_at"] = utc_now()
    assembled["summary"] = {
        "requested": len(assembled_results),
        "completed": len(assembled_results),
        "failed": 0,
        "repaired_cases": repaired_count,
        "promoted_clean_cases": promoted_count,
    }
    assembled["repair_provenance"] = {
        "source_ledger": {"path": display_path(ledger_path), "sha256": digest(ledger_path)},
        "repaired_cases": repaired_count,
        "promoted_clean_cases": promoted_count,
    }
    write_json(output, assembled)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssemblyError as error:
        raise SystemExit(f"repair ledger assembly failed: {error}") from error
