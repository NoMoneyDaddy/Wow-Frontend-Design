#!/usr/bin/env python3
"""Run a bounded v7 packet → repair → narrow → frozen-full verification cycle."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
SHA256 = __import__("re").compile(r"[0-9a-f]{64}")


def _module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


codex = _module("v7_cycle_codex", ROOT / "evals" / "run_v7_codex_case.py")
visual = _module("v7_cycle_visual", ROOT / "evals" / "run_v7_visual_matrix.py")
compiler = _module("v7_cycle_compiler", ROOT / "evals" / "compile_v7_repair_packet.py")
policy = _module("v7_cycle_policy", ROOT / "evals" / "v7_repair_policy.py")
evidence = visual.evidence


class V7RepairCycleError(ValueError):
    """Raised when the repair cycle cannot continue without weakening evidence."""


class V7RepairCycleFuse(V7RepairCycleError):
    """Raised after bounded repair generations or full fallbacks are exhausted."""


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _load(path: Path, label: str, maximum: int = 4 * 1024 * 1024) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > maximum:
        raise V7RepairCycleError(f"{label} is missing, unsafe or oversized")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise V7RepairCycleError(f"cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise V7RepairCycleError(f"{label} root must be an object")
    return value


def _outside(path: Path, repository_root: Path, label: str, *, directory: bool = False) -> Path:
    if path.is_symlink():
        raise V7RepairCycleError(f"{label} is missing or unsafe")
    resolved = path.resolve(strict=True)
    if resolved.is_symlink() or (directory and not resolved.is_dir()) or (not directory and not resolved.is_file()):
        raise V7RepairCycleError(f"{label} is missing or unsafe")
    try:
        resolved.relative_to(repository_root)
    except ValueError:
        return resolved
    raise V7RepairCycleError(f"{label} must remain evaluator-owned outside the repository")


def _empty_outside(path: Path, repository_root: Path, label: str) -> Path:
    resolved = _outside(path, repository_root, label, directory=True)
    if any(resolved.iterdir()):
        raise V7RepairCycleError(f"{label} must be empty")
    return resolved


def _write_once(path: Path, value: dict[str, Any]) -> Path:
    if path.exists() or path.is_symlink():
        raise V7RepairCycleError(f"refusing to overwrite cycle evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as error:
        raise V7RepairCycleError(f"refusing to overwrite cycle evidence: {path}") from error
    return path


def _target_identity(target: dict[str, Any]) -> tuple[str, str]:
    return target["variant"], target["case_id"]


def _source_receipt(root: Path) -> dict[str, Any]:
    expected = {"DESIGN.md", "index.html", "run-manifest.json"}
    if (
        not root.is_dir()
        or root.is_symlink()
        or {item.name for item in root.iterdir()} != expected
        or any(not item.is_file() or item.is_symlink() for item in root.iterdir())
    ):
        raise V7RepairCycleError("target inventory is incomplete or unsafe")
    manifest = root / "run-manifest.json"
    manifest_data = _load(manifest, "target run manifest")
    declared = manifest_data.get("outputs")
    if (
        manifest_data.get("schema_version") != 1
        or manifest_data.get("status") != "completed"
        or not isinstance(declared, list)
        or len(declared) != 2
    ):
        raise V7RepairCycleError("target run manifest is incomplete")
    indexed = {
        item.get("path"): item for item in declared
        if isinstance(item, dict) and set(item) == {"path", "bytes", "sha256"}
    }
    if set(indexed) != {"DESIGN.md", "index.html"}:
        raise V7RepairCycleError("target output declaration is invalid")
    outputs = []
    for name in ("DESIGN.md", "index.html"):
        artifact = root / name
        if not artifact.is_file() or artifact.is_symlink():
            raise V7RepairCycleError(f"target output is missing or unsafe: {name}")
        record = {"path": name, "bytes": artifact.stat().st_size, "sha256": _digest(artifact)}
        if indexed[name] != record:
            raise V7RepairCycleError(f"target output declaration is stale: {name}")
        outputs.append(record)
    return {
        "manifest_sha256": _digest(manifest),
        "outputs": outputs,
    }


def _verify_affected_targets(
    staged: dict[tuple[str, str], Path],
    source_receipts: dict[tuple[str, str], dict[str, Any]],
    captured_receipts: dict[tuple[str, str], dict[str, Any]],
    accepted_selectors: dict[tuple[str, str], dict[str, Any]],
    full_inventory: list[tuple[str, str, str, str, str]],
    support_contract_sha256: str | None,
) -> tuple[dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]]]:
    if set(accepted_selectors) != set(staged):
        raise V7RepairCycleError("affected selector inventory does not match staged targets")
    verified_targets = dict(source_receipts)
    bindings = []
    for key, root in sorted(staged.items()):
        expected = captured_receipts.get(key)
        current = _source_receipt(root)
        if expected is None or current != expected:
            raise V7RepairCycleError(f"affected capture receipt is stale for {key[0]}/{key[1]}")
        record = accepted_selectors[key]
        selector_path = Path(record.get("path", ""))
        selector_sha256 = record.get("sha256")
        if (
            not isinstance(selector_sha256, str)
            or not selector_path.is_file()
            or selector_path.is_symlink()
            or _digest(selector_path) != selector_sha256
        ):
            raise V7RepairCycleError(f"accepted selector is stale for {key[0]}/{key[1]}")
        selector = _load(selector_path, "accepted affected selector")
        try:
            binding = policy.verify_selector_binding(
                selector,
                key,
                current,
                full_inventory,
                support_contract_sha256,
            )
        except policy.V7RepairPolicyError as error:
            raise V7RepairCycleError(f"accepted selector is invalid for {key[0]}/{key[1]}: {error}") from error
        binding["selector_sha256"] = selector_sha256
        bindings.append(binding)
        verified_targets[key] = current
    return verified_targets, bindings


def _require_support_contract(
    path: Path,
    repository_root: Path,
    expected_sha256: str | None,
) -> None:
    if expected_sha256 is None:
        return
    try:
        current_sha256 = policy.validate_support_contract(path, repository_root)
    except policy.V7RepairPolicyError as error:
        raise V7RepairCycleError(f"repair support contract became invalid: {error}") from error
    if current_sha256 != expected_sha256:
        raise V7RepairCycleError("repair support contract drifted during the cycle")


def _brief_map(path: Path, repository_root: Path) -> dict[str, Path]:
    data = _load(_outside(path, repository_root, "brief map"), "brief map", 128 * 1024)
    if set(data) != {"schema_version", "cases"} or data.get("schema_version") != 1:
        raise V7RepairCycleError("brief map contract is invalid")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise V7RepairCycleError("brief map is empty")
    mapped: dict[str, Path] = {}
    for item in cases:
        if not isinstance(item, dict) or set(item) != {"case_id", "path", "sha256"}:
            raise V7RepairCycleError("brief map entry is invalid")
        case_id = item.get("case_id")
        brief = Path(item.get("path", ""))
        if not isinstance(case_id, str) or case_id in mapped or not brief.is_absolute():
            raise V7RepairCycleError("brief map identity is invalid or duplicated")
        resolved = _outside(brief, repository_root, f"brief {case_id}")
        if not isinstance(item.get("sha256"), str) or _digest(resolved) != item["sha256"]:
            raise V7RepairCycleError(f"brief hash is stale for {case_id}")
        mapped[case_id] = resolved
    return mapped


def _make_packet(
    manifest_path: Path,
    ledger_path: Path,
    split: str,
    input_inventory_sha256: str,
    screenshot_count: int,
    finding_run_count: int,
    targets: list[dict[str, Any]],
    repository_root: Path,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "repair_required" if targets else "clean",
        "source": {
            "cohort_manifest": {
                "path": manifest_path.relative_to(repository_root).as_posix(),
                "sha256": _digest(manifest_path),
            },
            "ledger": {"path": ledger_path.name, "sha256": _digest(ledger_path)},
            "compiler": {
                "path": Path(compiler.__file__).resolve().relative_to(repository_root).as_posix(),
                "sha256": _digest(Path(compiler.__file__).resolve()),
            },
            "split": split,
            "gate": "full",
            "input_inventory_sha256": input_inventory_sha256,
            "screenshot_count": screenshot_count,
            "finding_run_count": finding_run_count,
        },
        "targets": targets,
    }


def execute_cycle(
    initial_packet: dict[str, Any],
    *,
    generate: Callable[[dict[str, Any], dict[str, Any], int], dict[str, Any]],
    capture_narrow: Callable[[dict[str, Any], dict[str, Any], int], dict[str, Any]],
    run_full: Callable[[dict[tuple[str, str], Path], int], dict[str, Any]],
    promote: Callable[[dict[tuple[str, str], Path], dict[tuple[str, str], dict[str, Any]]], dict[str, Any]],
    write_receipt: Callable[[dict[str, Any]], None],
    rank_source: Callable[[dict[str, Any]], tuple[Any, ...]] | None = None,
    rank_candidate: Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], tuple[Any, ...]] | None = None,
    retain_best: Callable[[tuple[str, str], dict[str, Any], tuple[Any, ...]], None] | None = None,
    max_generations: int = 3,
    max_full_runs: int = 3,
) -> dict[str, Any]:
    """State-machine seam used by synthetic tests and the evaluator-owned CLI."""
    pending = initial_packet
    staged: dict[tuple[str, str], Path] = {}
    generation_counts: dict[tuple[str, str], int] = {}
    baseline_targets: dict[tuple[str, str], dict[str, Any]] = {}
    best_ranks: dict[tuple[str, str], tuple[Any, ...]] = {}
    full_runs = 0
    verification_runs = 0
    while True:
        if pending.get("status") != "repair_required" or not pending.get("targets"):
            raise V7RepairCycleError("cycle received no actionable repair target")
        restart_pending = False
        for target in pending["targets"]:
            identity = _target_identity(target)
            if identity not in baseline_targets:
                baseline_targets[identity] = copy.deepcopy(target)
                if rank_source is not None:
                    best_ranks[identity] = rank_source(target)
            while True:
                generation_counts[identity] = generation_counts.get(identity, 0) + 1
                if generation_counts[identity] > max_generations:
                    receipt = {
                        "status": "PARTIALLY VERIFIED",
                        "outcome": "generation_fuse",
                        "identity": list(identity),
                        "generation_count": generation_counts[identity] - 1,
                    }
                    write_receipt(receipt)
                    raise V7RepairCycleFuse("target exhausted its bounded repair generations")
                try:
                    generation = generate(target, pending, generation_counts[identity])
                except V7RepairCycleFuse:
                    raise
                except BaseException as error:
                    write_receipt({
                        "status": "generation_failed",
                        "identity": list(identity),
                        "generation_count": generation_counts[identity],
                        "error": str(error)[:500],
                    })
                    raise
                try:
                    narrow = capture_narrow(target, generation, generation_counts[identity])
                except BaseException as error:
                    write_receipt({
                        "status": "narrow_infrastructure_failed",
                        "identity": list(identity),
                        "generation_count": generation_counts[identity],
                        "generation": generation["receipt"],
                        "error": str(error)[:500],
                    })
                    raise
                next_targets = narrow.get("targets")
                if not isinstance(next_targets, list):
                    raise V7RepairCycleError("affected capture omitted repair targets")
                if rank_candidate is not None:
                    candidate_rank = rank_candidate(baseline_targets[identity], narrow, generation)
                    if identity not in best_ranks:
                        raise V7RepairCycleError("best-artifact baseline rank is missing")
                    if not policy.is_strict_improvement(candidate_rank, best_ranks[identity]):
                        write_receipt({
                            "status": "PARTIALLY VERIFIED",
                            "outcome": "non_improving_artifact",
                            "identity": list(identity),
                            "generation_count": generation_counts[identity],
                            "best_rank": policy.rank_receipt(best_ranks[identity]),
                            "rejected_rank": policy.rank_receipt(candidate_rank),
                            "retained_root": str(staged.get(identity, generation.get("source_root", ""))),
                        })
                        raise V7RepairCycleFuse("candidate artifact did not improve the lexicographic ratchet")
                    best_ranks[identity] = candidate_rank
                    if retain_best is not None:
                        retain_best(identity, generation, candidate_rank)
                staged[identity] = Path(generation["root"])
                capture_mode = "affected" if isinstance(narrow.get("selection"), dict) else "narrow"
                receipt = {
                    "status": f"{capture_mode}_clean" if not next_targets else f"{capture_mode}_failed",
                    "identity": list(identity),
                    "generation_count": generation_counts[identity],
                    "generation": generation["receipt"],
                    "narrow": narrow["receipt"],
                }
                if identity in best_ranks:
                    receipt["best_rank"] = policy.rank_receipt(best_ranks[identity])
                write_receipt(receipt)
                if not next_targets:
                    break
                own_targets = [item for item in next_targets if _target_identity(item) == identity]
                foreign_targets = [item for item in next_targets if _target_identity(item) != identity]
                if len(own_targets) > 1:
                    raise V7RepairCycleError("affected capture duplicated the active repair target")
                decision = narrow.get("selection", {}).get("decision")
                if foreign_targets and decision != "cohort-full-matrix":
                    raise V7RepairCycleError("target-scoped capture returned an unexpected repair target")
                pending = narrow["packet"]
                if foreign_targets:
                    restart_pending = True
                    break
                if not own_targets:
                    raise V7RepairCycleError("affected capture omitted its active failing target")
                target = own_targets[0]
            if restart_pending:
                break
        if restart_pending:
            continue
        verification_runs += 1
        if verification_runs > max_full_runs:
            receipt = {
                "status": "PARTIALLY VERIFIED",
                "outcome": "verification_fuse",
                "verification_runs": verification_runs - 1,
            }
            write_receipt(receipt)
            raise V7RepairCycleFuse("repair verification exhausted its bounded runs")
        try:
            full = run_full(staged, verification_runs)
        except BaseException as error:
            write_receipt({
                "status": "full_infrastructure_failed",
                "verification_run": verification_runs,
                "error": str(error)[:500],
            })
            raise
        verification_mode = full.get("receipt", {}).get("mode", "full")
        if verification_mode == "full":
            full_runs += 1
        write_receipt({
            "status": f"{verification_mode}_clean" if full["packet"]["status"] == "clean" else f"{verification_mode}_failed",
            "verification_run": verification_runs,
            "full": full["receipt"],
        })
        if full["packet"]["status"] == "clean":
            try:
                verified_targets = full.get("verified_targets")
                if not isinstance(verified_targets, dict):
                    raise V7RepairCycleError("full matrix omitted verified target receipts")
                promotion = promote(staged, verified_targets)
            except BaseException as error:
                write_receipt({
                    "status": "promotion_rolled_back",
                    "verification_run": verification_runs,
                    "error": str(error)[:500],
                })
                raise
            completed = {
                "schema_version": 1,
                "status": "completed",
                "generation_counts": {"/".join(key): value for key, value in sorted(generation_counts.items())},
                "full_runs": full_runs,
                "verification_runs": verification_runs,
                "best_artifacts": [
                    {
                        "variant": key[0],
                        "case_id": key[1],
                        "root": str(staged[key]),
                        "rank": policy.rank_receipt(best_ranks[key]) if key in best_ranks else None,
                    }
                    for key in sorted(staged)
                ],
                "promotion": promotion,
            }
            write_receipt(completed)
            return completed
        pending = full["packet"]


def _promote_targets(
    staged: dict[tuple[str, str], Path],
    canonical: dict[tuple[str, str], Path],
    archive_root: Path,
    *,
    verify: Callable[[], None] | None = None,
    expected_canonical: dict[tuple[str, str], dict[str, Any]] | None = None,
    expected_staged: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if archive_root.exists() or archive_root.is_symlink():
        raise V7RepairCycleError("promotion archive root already exists")
    archive_root.mkdir()
    token = _canonical_sha256([list(key) for key in sorted(staged)])[:12]
    prepared: dict[tuple[str, str], Path] = {}
    archives: dict[tuple[str, str], Path] = {}
    moved: list[tuple[str, str]] = []
    try:
        if any(path.parent.stat().st_dev != archive_root.stat().st_dev for path in canonical.values()):
            raise V7RepairCycleError("promotion archive and canonical targets must share one filesystem")
        for key, source in sorted(staged.items()):
            target = canonical[key]
            prepared_path = target.parent / f".{target.name}.repair-staged-{token}"
            archive = archive_root / f"{key[0]}--{key[1]}--{token}"
            if prepared_path.exists() or archive.exists() or source.is_symlink() or target.is_symlink():
                raise V7RepairCycleError("promotion destination is stale or unsafe")
            if expected_staged is not None and _source_receipt(source) != expected_staged[key]:
                raise V7RepairCycleError(f"staged target drifted after full verification: {key[0]}/{key[1]}")
            shutil.copytree(source, prepared_path, symlinks=True)
            if _source_receipt(prepared_path) != (
                expected_staged[key] if expected_staged is not None else _source_receipt(source)
            ):
                raise V7RepairCycleError("prepared promotion copy changed")
            prepared[key] = prepared_path
            archives[key] = archive
        for key in sorted(staged):
            target = canonical[key]
            if expected_canonical is not None and _source_receipt(target) != expected_canonical[key]:
                raise V7RepairCycleError(f"canonical target drifted during promotion: {key[0]}/{key[1]}")
            os.rename(target, archives[key])
            try:
                os.rename(prepared[key], target)
            except BaseException:
                os.rename(archives[key], target)
                raise
            moved.append(key)
        if verify is not None:
            verify()
        return {
            "status": "promoted",
            "targets": [
                {"variant": key[0], "case_id": key[1], "archive": archives[key].name}
                for key in sorted(staged)
            ],
        }
    except BaseException:
        for key in reversed(moved):
            target = canonical[key]
            rollback_copy = staged[key]
            if target.exists() and not rollback_copy.exists():
                os.rename(target, rollback_copy)
            elif target.exists():
                shutil.rmtree(target)
            if archives[key].exists():
                os.rename(archives[key], target)
        for path in prepared.values():
            if path.exists():
                shutil.rmtree(path)
        raise


def run(args: Namespace) -> dict[str, Any]:
    repository_root = args.repository_root.resolve(strict=True)
    manifest_path = args.manifest.resolve(strict=True)
    codex.preflight.validate_manifest(manifest_path, repository_root)
    cohort = _load(manifest_path, "cohort manifest")
    if args.split != "development":
        raise V7RepairCycleError("repair cycles are development-only")
    packet_path = _outside(args.packet, repository_root, "repair packet")
    packet = _load(packet_path, "repair packet", 256 * 1024)
    if (
        set(packet) != {"schema_version", "status", "source", "targets"}
        or packet.get("schema_version") != 1
        or packet.get("status") != "repair_required"
        or not isinstance(packet.get("targets"), list)
        or not packet["targets"]
    ):
        raise V7RepairCycleError("initial repair packet is not actionable")
    source_ledger = _outside(args.source_ledger, repository_root, "source ledger")
    source_ledger_data = _load(source_ledger, "source ledger")
    source_results = _outside(args.source_result_dir, repository_root, "source result directory", directory=True)
    source_screenshots = _outside(args.source_screenshot_dir, repository_root, "source screenshot directory", directory=True)
    gate = packet.get("source", {}).get("gate")
    if gate != "full":
        raise V7RepairCycleError("P0 repair cycle requires a frozen full source gate")
    evidence.validate(manifest_path, source_ledger, source_results, source_screenshots, repository_root, "full")
    if packet.get("source", {}).get("ledger") != {"path": source_ledger.name, "sha256": _digest(source_ledger)}:
        raise V7RepairCycleError("repair packet is not bound to the supplied source ledger")
    hidden_path = _outside(args.hidden_matrix, repository_root, "hidden matrix")
    hidden_sha256 = _digest(hidden_path)
    if source_ledger_data.get("hidden_matrix_sha256") != hidden_sha256:
        raise V7RepairCycleError("source ledger is not bound to the supplied hidden matrix")
    _load(hidden_path, "hidden matrix")
    targets = visual.load_hidden_matrix(hidden_path, cohort, args.split, repository_root)
    if _digest(hidden_path) != hidden_sha256:
        raise V7RepairCycleError("hidden matrix drifted during validation")
    canonical = {key: Path(value["root"]).resolve(strict=True) for key, value in targets.items()}
    support_contract_path = ROOT / "evals" / "v7-repair-support-contract.json"
    try:
        support_contract_sha256 = policy.validate_support_contract(
            support_contract_path,
            repository_root,
        )
    except policy.V7RepairPolicyError:
        support_contract_sha256 = None
    target_isolation = {
        key: support_contract_sha256 is not None and all(
            Path(contract["route"]).resolve(strict=True).parent == canonical[key]
            and Path(contract["route"]).name == "index.html"
            for contract in value["states"].values()
        )
        for key, value in targets.items()
    }
    generation_records = {
        key: visual.validate_target_provenance(path, key[0], key[1], cohort, manifest_path, repository_root)
        for key, path in canonical.items()
    }
    visual.validate_generation_cohort(generation_records, {item["id"] for item in cohort["splits"][args.split]})
    briefs = _brief_map(args.brief_map, repository_root)
    if args.candidate_reference is None:
        raise V7RepairCycleError("P0 full fallback requires --candidate-reference for newly discovered candidate findings")
    for case in cohort["splits"][args.split]:
        case_id = case["id"]
        if case_id not in briefs:
            raise V7RepairCycleError(f"brief map is missing a frozen full-matrix case: {case_id}")
        expected_hashes = {generation_records[(variant, case_id)]["brief_sha256"] for variant in evidence.VARIANTS}
        if expected_hashes != {_digest(briefs[case_id])}:
            raise V7RepairCycleError(f"brief does not match source targets: {case_id}")
    if set(briefs) != {case["id"] for case in cohort["splits"][args.split]}:
        raise V7RepairCycleError("brief map must contain exactly the frozen full-matrix cases")
    candidate_reference = args.candidate_reference
    if candidate_reference.is_symlink():
        raise V7RepairCycleError("candidate reference must not be a symlink")
    candidate_reference = candidate_reference.resolve(strict=True)
    try:
        candidate_relative = candidate_reference.relative_to(repository_root).as_posix()
    except ValueError as error:
        raise V7RepairCycleError("candidate reference must remain inside the repository") from error
    if candidate_relative != codex.EDITABLE_PATH:
        raise V7RepairCycleError("candidate reference is not the frozen editable path")
    candidate_hashes = {
        generation_records[("candidate", case["id"])]["editable_sha256"]
        for case in cohort["splits"][args.split]
    }
    if candidate_hashes != {_digest(candidate_reference)}:
        raise V7RepairCycleError("candidate reference does not match source target provenance")
    for target in packet.get("targets", []):
        key = _target_identity(target)
        if key not in canonical or target["case_id"] not in briefs:
            raise V7RepairCycleError("repair packet target is absent from the source cohort or brief map")
        codex._validate_repair_packet(packet, manifest_path, repository_root, *key)
    work_root = _empty_outside(args.work_root, repository_root, "cycle work root")
    log_dir = _outside(args.log_dir, repository_root, "cycle log directory", directory=True)
    output = args.output.resolve(strict=False)
    if output.exists() or output.is_symlink() or output.parent.resolve(strict=True) != work_root:
        raise V7RepairCycleError("cycle output must be a new direct child of the empty work root")
    source_receipts = {key: _source_receipt(path) for key, path in canonical.items()}
    full_inventory = evidence.expected_inventory(cohort, args.split, "full")
    packet_files: dict[str, Path] = {_digest(packet_path): packet_path}
    verified_receipts: dict[tuple[str, str], dict[str, Any]] = {}
    accepted_selectors: dict[tuple[str, str], dict[str, Any]] = {}
    verification_bindings: list[dict[str, Any]] = []
    round_counter = 0

    def write_receipt(value: dict[str, Any]) -> None:
        nonlocal round_counter
        round_counter += 1
        _write_once(work_root / f"receipt-{round_counter:03d}.json", value)

    def generate(target: dict[str, Any], active_packet: dict[str, Any], generation_number: int) -> dict[str, Any]:
        key = _target_identity(target)
        source = staged_roots.get(key, canonical[key])
        round_dir = work_root / f"{key[0]}--{key[1]}--generation-{generation_number}"
        round_dir.mkdir()
        packet_file = round_dir / "repair-packet.json"
        _write_once(packet_file, active_packet)
        packet_files[_digest(packet_file)] = packet_file
        source_manifest = source / "run-manifest.json"
        source_data = _load(source_manifest, "repair source manifest")
        failure_keys = codex._repair_failure_keys(target)
        prior_repair = source_data.get("repair")
        if prior_repair is None:
            prior_counts = {}
        elif isinstance(prior_repair, dict) and isinstance(prior_repair.get("failure_counts"), dict):
            prior_counts = prior_repair["failure_counts"]
        else:
            raise V7RepairCycleError("repair source lineage is malformed")
        if any(
            not isinstance(key_hash, str)
            or SHA256.fullmatch(key_hash) is None
            or isinstance(count, bool)
            or not isinstance(count, int)
            or not 1 <= count <= 3
            for key_hash, count in prior_counts.items()
        ):
            raise V7RepairCycleError("repair source failure counts are malformed")
        next_counts = {key_hash: prior_counts.get(key_hash, 0) + 1 for key_hash in failure_keys}
        if any(value > 3 for value in next_counts.values()):
            write_receipt({
                "status": "PARTIALLY VERIFIED",
                "outcome": "failure_key_fuse",
                "identity": list(key),
                "failure_counts": dict(sorted(next_counts.items())),
                "source": _source_receipt(source),
            })
            raise V7RepairCycleFuse("failure key reached the three-round fuse before generation")
        repair_round = max(next_counts.values())
        context = {
            "schema_version": 1,
            "variant": key[0],
            "case_id": key[1],
            "packet_sha256": _digest(packet_file),
            "source_manifest_sha256": _digest(source_manifest),
            "finding_signature": codex._repair_finding_signature(target),
            "feedback": target["feedback"],
        }
        context_file = _write_once(round_dir / "repair-context.json", context)
        generated = round_dir / "target"
        generated.mkdir()
        manifest = codex.run(Namespace(
            repository_root=repository_root,
            manifest=manifest_path,
            variant=key[0],
            case_id=key[1],
            brief=briefs[key[1]],
            target=generated,
            log_dir=log_dir,
            candidate_reference=candidate_reference if key[0] == "candidate" else None,
            max_attempts=args.max_attempts,
            inactivity_seconds=None,
            hard_seconds=None,
            repair_source=source,
            repair_context=context_file,
            repair_packet=packet_file,
            repair_round=repair_round,
        ))
        return {
            "root": str(generated),
            "source_root": str(source),
            "source_receipt": _source_receipt(source),
            "receipt": {
                "manifest_sha256": _digest(generated / "run-manifest.json"),
                "outputs": manifest["outputs"],
                "packet_sha256": context["packet_sha256"],
                "context_sha256": _digest(context_file),
            },
        }

    def capture_narrow(target: dict[str, Any], generation: dict[str, Any], generation_number: int) -> dict[str, Any]:
        key = _target_identity(target)
        generated = Path(generation["root"])
        _require_support_contract(support_contract_path, repository_root, support_contract_sha256)
        generated_receipt = _source_receipt(generated)
        selector = policy.select_affected_rows(
            target,
            generation["source_receipt"],
            generated_receipt,
            full_inventory,
            target_isolated=target_isolation.get(key, False),
            support_contract_sha256=support_contract_sha256,
        )
        selected = [tuple(item) for item in selector["selected_rows"]]
        overrides = dict(staged_roots)
        overrides[key] = generated
        selected_targets = {identity: {"root": value["root"], "states": {
            state: dict(contract) for state, contract in value["states"].items()
        }} for identity, value in targets.items()}
        selected_identities = {item[:2] for item in selected}
        effective_roots = {
            identity: overrides.get(identity, canonical[identity])
            for identity in selected_identities
        }
        verified_before = {identity: _source_receipt(root) for identity, root in effective_roots.items()}
        for identity, root in effective_roots.items():
            for state, contract in selected_targets[identity]["states"].items():
                route = root / Path(contract["route"]).relative_to(canonical[identity])
                if not route.is_file() or route.is_symlink():
                    raise V7RepairCycleError(
                        f"repaired route is missing for {identity[0]}/{identity[1]}/{state}"
                    )
                contract["route"] = str(route)
                contract["route_sha256"] = _digest(route)
        round_dir = generated.parent
        result_dir = round_dir / "narrow-results"
        screenshot_dir = round_dir / "narrow-screenshots"
        result_dir.mkdir()
        screenshot_dir.mkdir()
        selector_file = _write_once(round_dir / "affected-selection.json", selector)
        attempts = visual.capture_inventory(
            selected_targets,
            selected,
            result_dir,
            screenshot_dir,
            cohort["timeouts"]["capture"]["hard_seconds"],
            args.max_attempts,
            repository_root,
            allowed_keys=set(full_inventory),
        )
        _require_support_contract(support_contract_path, repository_root, support_contract_sha256)
        verified_after = {identity: _source_receipt(root) for identity, root in effective_roots.items()}
        if verified_after != verified_before:
            raise V7RepairCycleError("target changed during affected-matrix capture")
        verified_receipts.update(verified_after)
        ledger = {
            "schema_version": 1,
            "status": "completed",
            "selection": [dict(zip(("variant", "case_id", "state", "profile", "engine"), item)) for item in selected],
            "attempts": attempts,
        }
        ledger_file = _write_once(round_dir / "narrow-ledger.json", ledger)
        next_targets, finding_runs = compiler.targets_from_validated_attempts(attempts, result_dir, screenshot_dir)
        packet_value = _make_packet(
            manifest_path,
            ledger_file,
            args.split,
            _canonical_sha256(ledger["selection"]),
            len(attempts),
            finding_runs,
            next_targets,
            repository_root,
        )
        packet_file = _write_once(round_dir / "narrow-packet.json", packet_value)
        packet_files[_digest(packet_file)] = packet_file
        candidate_target = next(
            (item for item in next_targets if _target_identity(item) == key),
            None,
        )
        changed_bytes = sum(
            item["bytes"]
            for item in selector["repaired_outputs"]
            if item["path"] in selector["diff"]["changed_files"]
        )
        return {
            "targets": next_targets,
            "packet": packet_value,
            "selection": selector,
            "candidate_target": candidate_target,
            "changed_bytes": changed_bytes,
            "artifact_sha256": _canonical_sha256(generated_receipt),
            "receipt": {
                "ledger_sha256": _digest(ledger_file),
                "packet_sha256": _digest(packet_file),
                "selector_sha256": _digest(selector_file),
                "selection_decision": selector["decision"],
                "rows": len(attempts),
                "finding_runs": finding_runs,
            },
        }

    def run_full(staged: dict[tuple[str, str], Path], verification_number: int) -> dict[str, Any]:
        _require_support_contract(support_contract_path, repository_root, support_contract_sha256)
        if _digest(hidden_path) != hidden_sha256:
            raise V7RepairCycleError("hidden matrix drifted before affected verification")
        verified_targets, bindings = _verify_affected_targets(
            staged,
            source_receipts,
            verified_receipts,
            accepted_selectors,
            full_inventory,
            support_contract_sha256,
        )
        verification_bindings[:] = copy.deepcopy(bindings)
        packet_value = {"schema_version": 1, "status": "clean", "targets": []}
        return {
            "packet": packet_value,
            "verified_targets": verified_targets,
            "receipt": {
                "mode": "affected",
                "verification_number": verification_number,
                "targets": len(staged),
                "rows": sum(item["selected_row_count"] for item in bindings),
                "target_bindings": bindings,
            },
        }

    def promote(
        staged: dict[tuple[str, str], Path],
        verified_targets: dict[tuple[str, str], dict[str, Any]],
    ) -> dict[str, Any]:
        _require_support_contract(support_contract_path, repository_root, support_contract_sha256)
        if set(verified_targets) != set(canonical):
            raise V7RepairCycleError("full verification target inventory is incomplete")
        for key, before in source_receipts.items():
            if _source_receipt(canonical[key]) != before:
                raise V7RepairCycleError(f"canonical target drifted before promotion: {key[0]}/{key[1]}")
        for key, expected in verified_targets.items():
            effective = staged[key] if key in staged else canonical[key]
            if _source_receipt(effective) != expected:
                raise V7RepairCycleError(f"target drifted after full verification: {key[0]}/{key[1]}")

        def verify() -> None:
            _require_support_contract(support_contract_path, repository_root, support_contract_sha256)
            for key, before in source_receipts.items():
                expected = verified_targets[key]
                if _source_receipt(canonical[key]) != expected:
                    raise V7RepairCycleError(f"target verification failed after promotion: {key[0]}/{key[1]}")
            _write_once(work_root / "promotion-commit.json", {
                "schema_version": 1,
                "status": "promotion_verified",
                "affected_evidence": verification_bindings,
                "targets": [
                    {"variant": key[0], "case_id": key[1], "receipt": _source_receipt(canonical[key])}
                    for key in sorted(staged)
                ],
            })

        result = _promote_targets(
            staged,
            canonical,
            work_root / "archives",
            verify=verify,
            expected_canonical=source_receipts,
            expected_staged={key: verified_targets[key] for key in staged},
        )
        result["affected_evidence"] = copy.deepcopy(verification_bindings)
        return result

    staged_roots: dict[tuple[str, str], Path] = {}

    def rank_source(target: dict[str, Any]) -> tuple[Any, ...]:
        key = _target_identity(target)
        root = staged_roots.get(key, canonical[key])
        return policy.artifact_rank(
            target,
            target,
            changed_bytes=0,
            artifact_sha256=_canonical_sha256(_source_receipt(root)),
        )

    def rank_candidate(
        baseline_target: dict[str, Any],
        affected: dict[str, Any],
        _generation: dict[str, Any],
    ) -> tuple[Any, ...]:
        return policy.artifact_rank(
            baseline_target,
            affected["candidate_target"],
            changed_bytes=affected["changed_bytes"],
            artifact_sha256=affected["artifact_sha256"],
        )

    def retain_best(
        key: tuple[str, str],
        generation: dict[str, Any],
        _rank: tuple[Any, ...],
    ) -> None:
        staged_roots[key] = Path(generation["root"])
        selector_path = Path(generation["root"]).parent / "affected-selection.json"
        accepted_selectors[key] = {
            "path": str(selector_path),
            "sha256": _digest(selector_path),
        }

    completed = execute_cycle(
        packet,
        generate=generate,
        capture_narrow=capture_narrow,
        run_full=run_full,
        promote=promote,
        write_receipt=write_receipt,
        rank_source=rank_source,
        rank_candidate=rank_candidate,
        retain_best=retain_best,
        max_generations=args.max_generations,
        max_full_runs=args.max_full_runs,
    )
    _write_once(output, completed)
    return completed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--hidden-matrix", required=True, type=Path)
    parser.add_argument("--split", required=True, choices=("development",))
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--source-ledger", required=True, type=Path)
    parser.add_argument("--source-result-dir", required=True, type=Path)
    parser.add_argument("--source-screenshot-dir", required=True, type=Path)
    parser.add_argument("--brief-map", required=True, type=Path)
    parser.add_argument("--candidate-reference", type=Path)
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--log-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    parser.add_argument("--max-attempts", type=int, choices=(1, 2, 3), default=3)
    parser.add_argument("--max-generations", type=int, choices=(1, 2, 3), default=3)
    parser.add_argument("--max-full-runs", type=int, choices=(1, 2, 3), default=3)
    args = parser.parse_args()
    try:
        result = run(args)
    except (
        OSError,
        V7RepairCycleError,
        codex.V7CodexRunnerError,
        visual.V7VisualRunnerError,
        compiler.RepairPacketError,
        policy.V7RepairPolicyError,
        evidence.V7EvidenceError,
    ) as error:
        print(f"v7 repair cycle failed: {error}", file=sys.stderr)
        return 1
    print(
        "v7 repair cycle completed: "
        f"{result['verification_runs']} verification pass(es), {result['full_runs']} full run(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
