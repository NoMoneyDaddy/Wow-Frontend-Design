#!/usr/bin/env python3
"""Publish one complete v6 latest-Skill repair pass with integrity-bound evidence."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVALS_ROOT = Path(__file__).resolve().parent
if str(EVALS_ROOT) not in sys.path:
    sys.path.insert(0, str(EVALS_ROOT))
import run_product_flow_evaluation as evaluation  # noqa: E402
import run_product_flow_matrix as matrix  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
MODEL = "gpt-5.4-mini"
ALIAS = f"codex-{MODEL}"
CASES = {
    "wind-maintenance-dispatch-v6": ("DESIGN.md", "index.html"),
    "type-foundry-specimen-v6": ("DESIGN.md", "index.html"),
    "repair-cafe-intake-v6": ("DESIGN.md", "index.html"),
    "night-market-allergen-v6": ("DESIGN.md", "index.html"),
    "royalty-statement-v6": ("DESIGN.md", "index.html"),
    "packaging-configurator-v6": ("DESIGN.md", "index.html", "materials.html", "summary.html"),
    "oral-history-archive-v6": ("DESIGN.md", "index.html", "archive.html", "story.html"),
    "grant-review-board-v6": ("DESIGN.md", "index.html"),
}
TARGET_ROOT = Path("evals/product-flow-v6-repaired-v2-targets")
SOURCE_ROOT = Path("evals/product-flow-v6-repaired-targets")
VISUAL_PATH = Path("evals/product-flow-v6-visual-results.json")
GENERATION_PATH = Path("evals/product-flow-v6-repaired-v2-generation-results.json")
SCREENSHOT_ROOT = Path("assets/product-flow-v6")
SKILL_PATH = Path("wow-frontend-design/SKILL.md")
NOTE_PATH = Path("evals/product-flow-v6-latest-skill-repair.md")
AUDITOR_PATH = Path("evals/playwright_visual_v6_audit.cjs")


class PublishError(ValueError):
    """Raised when a repair pass is incomplete, unsafe, or inconsistent."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visual-report", required=True, type=Path)
    parser.add_argument("--screenshot-dir", required=True, type=Path)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError as error:
        raise PublishError(f"path escapes repository: {path}") from error


def load_object(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise PublishError(f"{label} is missing or unsafe: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PublishError(f"cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise PublishError(f"{label} must be a JSON object")
    return value


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _repository_file(value: str | Path, label: str) -> Path:
    path = Path(value)
    root = ROOT.resolve()
    raw_root = Path(os.path.abspath(ROOT))
    if path.is_absolute():
        raw_candidate = Path(os.path.abspath(path))
        try:
            relative_input = raw_candidate.relative_to(raw_root)
        except ValueError:
            try:
                relative_input = raw_candidate.relative_to(root)
            except ValueError as error:
                raise PublishError(f"{label} escapes repository: {value}") from error
    else:
        relative_input = path
    candidate = Path(os.path.abspath(root / relative_input))
    try:
        relative_parts = candidate.relative_to(root).parts
    except ValueError as error:
        raise PublishError(f"{label} escapes repository: {value}") from error
    current = root
    for part in relative_parts:
        current /= part
        if current.is_symlink():
            raise PublishError(f"{label} is symlinked: {current}")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise PublishError(f"{label} escapes repository: {value}") from error
    if not resolved.is_file():
        raise PublishError(f"{label} is missing or unsafe: {candidate}")
    return resolved


def _generation_targets(ledger: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    results = ledger.get("results")
    if ledger.get("status") != "completed" or not isinstance(results, list) or len(results) != len(CASES):
        raise PublishError("generation ledger is not a complete pass")
    by_case: dict[str, dict[str, Any]] = {}
    targets: list[dict[str, Any]] = []
    for result in results:
        if (
            not isinstance(result, dict)
            or result.get("provider") != "codex"
            or result.get("model") != MODEL
            or result.get("case_id") not in CASES
        ):
            raise PublishError("generation result identity is invalid")
        case_id = str(result["case_id"])
        if case_id in by_case or not isinstance(result.get("receipt"), dict):
            raise PublishError("generation result is duplicated or has no evaluator receipt")
        target = (ROOT / TARGET_ROOT / f"{ALIAS}-{case_id}").resolve()
        try:
            manifest = matrix.verified_existing(
                target,
                "codex",
                MODEL,
                case_id,
                expected_receipt=result["receipt"],
                verify_current_tools=False,
            )
        except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError) as error:
            raise PublishError(f"generation target provenance failed for {case_id}: {error}") from error
        if manifest is None:
            raise PublishError(f"generation target is incomplete for {case_id}")
        by_case[case_id] = result
        targets.append({"case_id": case_id, "alias": ALIAS, "directory": target})
    if set(by_case) != set(CASES):
        raise PublishError("generation result inventory is incomplete")
    return targets, by_case


def _prepare_visual(
    report_path: Path,
    screenshot_dir: Path,
    generation_path: Path,
    targets: list[dict[str, Any]],
) -> tuple[dict[Path, bytes], dict[str, Any]]:
    try:
        evaluation.validate_visual_completion(report_path, screenshot_dir, targets, generation_path)
        blockers = evaluation.blocking_visual_findings(report_path)
    except (OSError, evaluation.EvaluationError) as error:
        raise PublishError(f"visual evidence validation failed: {error}") from error
    if blockers:
        raise PublishError(f"visual report has blocking findings: {evaluation.repair_summary(blockers)}")
    report = copy.deepcopy(load_object(report_path, "visual report"))
    results = report.get("results")
    assert isinstance(results, list)
    destination_root = ROOT / SCREENSHOT_ROOT
    if destination_root.is_symlink() or not destination_root.is_dir():
        raise PublishError("published screenshot root is missing or unsafe")
    expected_names = {Path(str(result["screenshot"])).name for result in results if isinstance(result, dict)}
    destination_names = {path.name for path in destination_root.glob("*.png") if path.is_file() and not path.is_symlink()}
    if len(expected_names) != len(results) or destination_names != expected_names:
        raise PublishError("published screenshot inventory disagrees with validated visual report")
    plan: dict[Path, bytes] = {}
    for result in results:
        assert isinstance(result, dict)
        source = Path(str(result["screenshot"]))
        source = (source if source.is_absolute() else ROOT / source).resolve()
        name = source.name
        content = source.read_bytes()
        destination = destination_root / name
        plan[destination] = content
        result["screenshot"] = f"{SCREENSHOT_ROOT.as_posix()}/{name}"
        result["screenshotSha256"] = hashlib.sha256(content).hexdigest()
    auditor = report.get("auditor")
    if not isinstance(auditor, dict) or auditor.get("sha256") != digest(ROOT / AUDITOR_PATH):
        raise PublishError("visual report auditor provenance disagrees")
    auditor["path"] = AUDITOR_PATH.as_posix()
    target_inputs = report.get("target_inputs")
    if not isinstance(target_inputs, list) or len(target_inputs) != len(CASES):
        raise PublishError("visual report target-input inventory disagrees")
    for record in target_inputs:
        if not isinstance(record, dict) or record.get("caseId") not in CASES:
            raise PublishError("visual report target-input record is malformed")
        record["target"] = f"{TARGET_ROOT.as_posix()}/{ALIAS}-{record['caseId']}"
    return plan, report


def _prepare_manifests(report: dict[str, Any]) -> tuple[dict[Path, bytes], dict[str, dict[str, object]]]:
    skill = _repository_file(SKILL_PATH, "Skill")
    note = _repository_file(NOTE_PATH, "research note")
    skill_record = {"path": SKILL_PATH.as_posix(), "sha256": digest(skill)}
    # The visual report hashes the final generation ledger, which hashes these
    # manifests. Keeping only this reverse path avoids a circular digest graph.
    visual_record = {"path": VISUAL_PATH.as_posix(), "bound_by": "generation_ledger"}
    note_record = {"path": NOTE_PATH.as_posix(), "sha256": digest(note)}
    report_generated_at = report.get("generated_at")
    finished_at = report_generated_at if isinstance(report_generated_at, str) and report_generated_at else utc_now()
    plan: dict[Path, bytes] = {}
    receipts: dict[str, dict[str, object]] = {}
    for case_id, outputs in CASES.items():
        target = ROOT / TARGET_ROOT / f"{ALIAS}-{case_id}"
        source = ROOT / SOURCE_ROOT / f"{ALIAS}-{case_id}"
        if target.is_symlink() or not target.is_dir() or source.is_symlink() or not source.is_dir():
            raise PublishError(f"target or source directory is missing or unsafe for {case_id}")
        manifest_path = target / "run-manifest.json"
        source_manifest_path = source / "run-manifest.json"
        manifest = load_object(manifest_path, f"manifest {case_id}")
        source_manifest = load_object(source_manifest_path, f"source manifest {case_id}")
        source_declared = {
            item.get("path"): item.get("sha256")
            for item in source_manifest.get("outputs", [])
            if isinstance(item, dict)
        }
        if set(source_declared) != set(outputs):
            raise PublishError(f"source manifest output set disagrees for {case_id}")
        changed: list[str] = []
        before_outputs: dict[str, str] = {}
        output_records: list[dict[str, Any]] = []
        for name in outputs:
            artifact = target / name
            before = source / name
            if artifact.is_symlink() or not artifact.is_file() or before.is_symlink() or not before.is_file():
                raise PublishError(f"repair output is missing or unsafe: {artifact}")
            before_outputs[name] = digest(before)
            if before_outputs[name] != source_declared[name]:
                raise PublishError(f"source manifest digest mismatch: {before}")
            artifact_digest = digest(artifact)
            if artifact_digest != before_outputs[name]:
                changed.append(name)
            output_records.append({"path": name, "bytes": artifact.stat().st_size, "sha256": artifact_digest})
        if not changed:
            raise PublishError(f"latest Skill repair changed no outputs for {case_id}")
        run_id = str(manifest.get("run_id", case_id))
        suffix = "-latest-skill-repair"
        if not run_id.endswith(suffix):
            run_id += suffix
        manifest.update(
            run_id=run_id,
            status="completed",
            finished_at=finished_at,
            mode="repair",
            promotion=None,
            outputs=output_records,
            skill_repair={
                "reason": "latest_skill_self_repair_after_typography_layout_locale_and_visual_audit",
                "source_manifest": {"path": relative(source_manifest_path), "sha256": digest(source_manifest_path)},
                "before_outputs": before_outputs,
                "changed_outputs": changed,
                "skill": copy.deepcopy(skill_record),
                "visual_report": copy.deepcopy(visual_record),
                "research_note": copy.deepcopy(note_record),
            },
        )
        cli = manifest.get("cli")
        if isinstance(cli, dict) and isinstance(cli.get("path"), str):
            cli["path"] = Path(cli["path"]).name
        serialized = _json_bytes(manifest)
        plan[manifest_path] = serialized
        receipts[case_id] = {
            "manifest_sha256": hashlib.sha256(serialized).hexdigest(),
            "outputs": {record["path"]: record["sha256"] for record in output_records},
        }
    return plan, receipts


def _prepare_generation(ledger: dict[str, Any], receipts: dict[str, dict[str, object]]) -> bytes:
    ledger = copy.deepcopy(ledger)
    contract = ledger.get("contract")
    results = ledger.get("results")
    if not isinstance(contract, dict) or not isinstance(results, list):
        raise PublishError("generation ledger inventory is malformed")
    contract["artifact_root"] = TARGET_ROOT.as_posix()
    for field in ("skill",):
        record = contract.get(field)
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise PublishError(f"generation contract {field} is malformed")
        record["sha256"] = digest(_repository_file(record["path"], f"generation contract {field}"))
    for field in ("trusted_context", "evaluator_inputs"):
        records = contract.get(field)
        if not isinstance(records, list) or any(not isinstance(record, dict) for record in records):
            raise PublishError(f"generation contract {field} is malformed")
        for record in records:
            path_value = record.get("path")
            if not isinstance(path_value, str):
                raise PublishError(f"generation contract {field} path is malformed")
            record["sha256"] = digest(_repository_file(path_value, f"generation contract {field}"))
    briefs = contract.get("briefs")
    if not isinstance(briefs, dict) or set(briefs) != set(CASES):
        raise PublishError("generation contract briefs are malformed")
    for case_id, record in briefs.items():
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise PublishError(f"generation contract brief is malformed for {case_id}")
        record["sha256"] = digest(_repository_file(record["path"], f"generation brief {case_id}"))
    contract["context_routing"] = "runner_selects_smallest_fixed_set_by_caller_model_and_case"
    source_ledger = _repository_file("evals/product-flow-v6-repaired-generation-results.json", "source ledger")
    repair_records = {
        "skill": {"path": SKILL_PATH.as_posix(), "sha256": digest(_repository_file(SKILL_PATH, "Skill"))},
        "visual_report": {"path": VISUAL_PATH.as_posix(), "bound_by": "generation_ledger"},
        "research_note": {"path": NOTE_PATH.as_posix(), "sha256": digest(_repository_file(NOTE_PATH, "research note"))},
    }
    source_record = {"path": relative(source_ledger), "sha256": digest(source_ledger)}
    contract["repair_assembly"] = {
        "source_ledger": copy.deepcopy(source_record),
        "latest_skill_repair": copy.deepcopy(repair_records),
        "repaired_cases": sorted(CASES),
        "promoted_clean_cases": [],
    }
    seen: set[str] = set()
    for result in results:
        if not isinstance(result, dict) or result.get("case_id") not in CASES:
            raise PublishError("generation result has an unknown case")
        case_id = str(result["case_id"])
        if case_id in seen:
            raise PublishError("generation result has a duplicate case")
        seen.add(case_id)
        result.update(
            status="completed",
            evidence_mode="repair",
            target=f"{TARGET_ROOT.as_posix()}/{ALIAS}-{case_id}",
            manifest=f"{TARGET_ROOT.as_posix()}/{ALIAS}-{case_id}/run-manifest.json",
            receipt=copy.deepcopy(receipts[case_id]),
        )
    if seen != set(CASES):
        raise PublishError("generation result inventory is incomplete")
    ledger["status"] = "completed"
    ledger["finished_at"] = utc_now()
    ledger["summary"] = {
        "requested": len(CASES),
        "completed": len(CASES),
        "failed": 0,
        "repaired_cases": len(CASES),
        "promoted_clean_cases": 0,
    }
    ledger["repair_provenance"] = {
        "source_ledger": source_record,
        **repair_records,
        "repaired_cases": len(CASES),
        "promoted_clean_cases": 0,
    }
    return _json_bytes(ledger)


def _finalize_visual(report: dict[str, Any], generation_bytes: bytes) -> bytes:
    report = copy.deepcopy(report)
    report["generation_ledger"] = {
        "path": GENERATION_PATH.as_posix(),
        "sha256": hashlib.sha256(generation_bytes).hexdigest(),
    }
    return _json_bytes(report)


def _validate_publication_plan(plan: dict[Path, bytes]) -> None:
    generation_path = ROOT / GENERATION_PATH
    visual_path = ROOT / VISUAL_PATH
    try:
        ledger = json.loads(plan[generation_path])
        report = json.loads(plan[visual_path])
    except (KeyError, UnicodeError, json.JSONDecodeError) as error:
        raise PublishError(f"staged publication JSON is incomplete: {error}") from error
    expected_generation = {
        "path": GENERATION_PATH.as_posix(),
        "sha256": hashlib.sha256(plan[generation_path]).hexdigest(),
    }
    if report.get("generation_ledger") != expected_generation:
        raise PublishError("staged visual report does not bind the final generation ledger")
    results = ledger.get("results")
    if not isinstance(results, list) or len(results) != len(CASES):
        raise PublishError("staged generation result inventory is incomplete")
    seen: set[str] = set()
    for result in results:
        if not isinstance(result, dict) or result.get("case_id") not in CASES:
            raise PublishError("staged generation result identity is invalid")
        case_id = str(result["case_id"])
        if case_id in seen:
            raise PublishError("staged generation result is duplicated")
        seen.add(case_id)
        manifest_path = ROOT / TARGET_ROOT / f"{ALIAS}-{case_id}" / "run-manifest.json"
        manifest_bytes = plan.get(manifest_path)
        receipt = result.get("receipt")
        if (
            manifest_bytes is None
            or not isinstance(receipt, dict)
            or receipt.get("manifest_sha256") != hashlib.sha256(manifest_bytes).hexdigest()
        ):
            raise PublishError(f"staged generation receipt disagrees for {case_id}")
    screenshots = report.get("results")
    if not isinstance(screenshots, list):
        raise PublishError("staged visual result inventory is malformed")
    for result in screenshots:
        if not isinstance(result, dict) or not isinstance(result.get("screenshot"), str):
            raise PublishError("staged visual result is malformed")
        screenshot_path = ROOT / str(result["screenshot"])
        content = plan.get(screenshot_path)
        if content is None or result.get("screenshotSha256") != hashlib.sha256(content).hexdigest():
            raise PublishError(f"staged screenshot digest disagrees: {screenshot_path}")


def build_publication_plan(report_path: Path, screenshot_dir: Path) -> dict[Path, bytes]:
    generation_path = ROOT / GENERATION_PATH
    ledger = load_object(generation_path, "generation ledger")
    targets, _ = _generation_targets(ledger)
    visual_plan, report = _prepare_visual(report_path, screenshot_dir, generation_path, targets)
    manifest_plan, receipts = _prepare_manifests(report)
    generation_bytes = _prepare_generation(ledger, receipts)
    plan = {
        **visual_plan,
        **manifest_plan,
        generation_path: generation_bytes,
        ROOT / VISUAL_PATH: _finalize_visual(report, generation_bytes),
    }
    _validate_publication_plan(plan)
    return plan


def commit_publication(plan: dict[Path, bytes]) -> None:
    if not plan:
        raise PublishError("publication plan is empty")
    root = ROOT.resolve()
    ordered = sorted(plan.items(), key=lambda item: str(item[0]))
    for destination, _ in ordered:
        if destination.is_symlink() or not destination.is_file():
            raise PublishError(f"publication destination is missing or unsafe: {destination}")
        try:
            destination.resolve().relative_to(root)
        except ValueError as error:
            raise PublishError(f"publication destination escapes repository: {destination}") from error
    with tempfile.TemporaryDirectory(prefix=".product-flow-publication-", dir=ROOT) as directory:
        transaction_root = Path(directory)
        staged_root = transaction_root / "staged"
        backup_root = transaction_root / "backup"
        staged_root.mkdir()
        backup_root.mkdir()
        staged: list[tuple[Path, Path, Path]] = []
        for index, (destination, content) in enumerate(ordered):
            staged_path = staged_root / str(index)
            with staged_path.open("xb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(staged_path, 0o644)
            staged.append((destination, staged_path, backup_root / str(index)))
        moved: list[tuple[Path, Path]] = []
        try:
            for destination, staged_path, backup_path in staged:
                os.replace(destination, backup_path)
                moved.append((destination, backup_path))
                os.replace(staged_path, destination)
        except BaseException as error:
            rollback_errors: list[str] = []
            for destination, backup_path in reversed(moved):
                try:
                    if destination.exists() or destination.is_symlink():
                        destination.unlink()
                    os.replace(backup_path, destination)
                except OSError as rollback_error:
                    rollback_errors.append(f"{destination}: {rollback_error}")
            if rollback_errors:
                raise PublishError(f"publication failed and rollback was incomplete: {'; '.join(rollback_errors)}") from error
            raise PublishError(f"publication transaction failed and was rolled back: {error}") from error


def main() -> int:
    args = parse_args()
    plan = build_publication_plan(
        args.visual_report.expanduser(),
        args.screenshot_dir.expanduser(),
    )
    commit_publication(plan)
    print("published 8 latest-Skill repairs and 64 integrity-bound screenshots")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PublishError as error:
        raise SystemExit(f"v6 repair publication failed: {error}") from error
