#!/usr/bin/env python3
"""Capture an exact v7 accepted/candidate screenshot matrix with bounded retries."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / "evals" / "playwright_v7_a1_audit.cjs"
SCRIPTS = ROOT / "wow-frontend-design" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import validate_v7_evidence as evidence  # noqa: E402

PREFLIGHT_SPEC = importlib.util.spec_from_file_location("v7_preflight_runner", ROOT / "evals" / "v7_preflight.py")
assert PREFLIGHT_SPEC and PREFLIGHT_SPEC.loader
preflight = importlib.util.module_from_spec(PREFLIGHT_SPEC)
PREFLIGHT_SPEC.loader.exec_module(preflight)

TARGET_KEYS = {"variant", "case_id", "root", "states"}
STATE_KEYS = {"route", "spec"}


class V7VisualRunnerError(ValueError):
    """Raised when the hidden matrix or capture run is unsafe or incomplete."""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 2 * 1024 * 1024:
        raise V7VisualRunnerError(f"{label} is missing, unsafe or oversized")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise V7VisualRunnerError(f"cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise V7VisualRunnerError(f"{label} root must be an object")
    return value


def _outside_repository(path: Path, root: Path, label: str) -> Path:
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError:
        return resolved
    raise V7VisualRunnerError(f"{label} must remain evaluator-owned outside the repository")


def _safe_route(root: Path, value: Any) -> Path:
    if not isinstance(value, str) or "\x00" in value or "\\" in value:
        raise V7VisualRunnerError("state route is invalid")
    relative = PurePosixPath(value)
    if relative.is_absolute() or not relative.parts or "." in relative.parts or ".." in relative.parts:
        raise V7VisualRunnerError("state route is unsafe")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise V7VisualRunnerError("state route traverses a symlink")
    resolved = current.resolve(strict=True)
    if not resolved.is_file() or resolved.stat().st_size > 2 * 1024 * 1024:
        raise V7VisualRunnerError("state route is missing or oversized")
    return resolved


def validate_target_provenance(
    target_root: Path,
    variant: str,
    case_id: str,
    cohort: dict[str, Any],
    cohort_manifest_path: Path,
    repository_root: Path,
) -> dict[str, str]:
    run_manifest_path = target_root / "run-manifest.json"
    run_manifest = _load(run_manifest_path, f"generation manifest {variant}/{case_id}")
    if (
        run_manifest.get("schema_version") != 1
        or run_manifest.get("status") != "completed"
        or run_manifest.get("case_id") != case_id
        or run_manifest.get("variant") != variant
        or run_manifest.get("model") != {"provider": "codex", "requested": "gpt-5.4-mini", "silent_fallback": False}
    ):
        raise V7VisualRunnerError(f"generation identity is invalid for {variant}/{case_id}")
    expected_cohort = {
        "path": cohort_manifest_path.relative_to(repository_root).as_posix(),
        "sha256": _digest(cohort_manifest_path),
    }
    if run_manifest.get("cohort_manifest") != expected_cohort:
        raise V7VisualRunnerError(f"generation cohort binding changed for {variant}/{case_id}")
    package = run_manifest.get("package")
    expected_changed = [] if variant == "accepted" else [preflight.EXPECTED_EDITABLE_PATH]
    if (
        not isinstance(package, dict)
        or package.get("variant") != variant
        or package.get("baseline_commit") != cohort["baseline"]["commit"]
        or package.get("source_baseline_tree_sha256") != cohort["baseline"]["tree_sha256"]
        or package.get("file_count") != cohort["baseline"]["file_count"]
        or package.get("changed_paths") != expected_changed
        or not isinstance(package.get("materialized_tree_sha256"), str)
        or not isinstance(package.get("editable_sha256"), str)
    ):
        raise V7VisualRunnerError(f"generation package provenance changed for {variant}/{case_id}")
    if cohort["stage"] == "frozen" and variant == "candidate" and package["editable_sha256"] != cohort["candidate"]["reference_sha256"]:
        raise V7VisualRunnerError(f"frozen candidate bytes changed for {case_id}")
    outputs = run_manifest.get("outputs")
    if not isinstance(outputs, list) or {item.get("path") for item in outputs if isinstance(item, dict)} != {"DESIGN.md", "index.html"}:
        raise V7VisualRunnerError(f"generation output inventory changed for {variant}/{case_id}")
    for item in outputs:
        if not isinstance(item, dict) or set(item) != {"path", "bytes", "sha256"}:
            raise V7VisualRunnerError(f"generation output record is malformed for {variant}/{case_id}")
        artifact = target_root / item["path"]
        if not artifact.is_file() or artifact.is_symlink() or artifact.stat().st_size != item["bytes"] or _digest(artifact) != item["sha256"]:
            raise V7VisualRunnerError(f"generation output hash is stale for {variant}/{case_id}")
    brief_sha256 = run_manifest.get("brief_sha256")
    if not isinstance(brief_sha256, str) or preflight.SHA256_PATTERN.fullmatch(brief_sha256) is None:
        raise V7VisualRunnerError(f"generation brief binding is invalid for {variant}/{case_id}")
    return {
        "materialized_tree_sha256": package["materialized_tree_sha256"],
        "editable_sha256": package["editable_sha256"],
        "brief_sha256": brief_sha256,
    }


def validate_generation_cohort(
    records: dict[tuple[str, str], dict[str, str]], public_cases: set[str]
) -> None:
    package_records: dict[str, set[tuple[str, str]]] = {variant: set() for variant in evidence.VARIANTS}
    for (variant, _case_id), record in records.items():
        package_records[variant].add((record["materialized_tree_sha256"], record["editable_sha256"]))
    if any(len(items) != 1 for items in package_records.values()):
        raise V7VisualRunnerError("all cases of each variant must use one identical Skill package")
    for case_id in public_cases:
        brief_hashes = {records[(variant, case_id)]["brief_sha256"] for variant in evidence.VARIANTS}
        if len(brief_hashes) != 1:
            raise V7VisualRunnerError(f"accepted and candidate briefs differ for {case_id}")


def load_hidden_matrix(
    matrix_path: Path,
    cohort: dict[str, Any],
    split: str,
    repository_root: Path,
) -> dict[tuple[str, str], dict[str, Any]]:
    matrix_file = _outside_repository(matrix_path, repository_root, "hidden matrix")
    data = _load(matrix_file, "hidden matrix")
    if set(data) != {"schema_version", "cohort_id", "split", "targets"} or data.get("schema_version") != 1:
        raise V7VisualRunnerError("hidden matrix root contract is invalid")
    if data.get("cohort_id") != cohort.get("cohort_id") or data.get("split") != split:
        raise V7VisualRunnerError("hidden matrix identity does not match cohort")
    public_cases = {item["id"] for item in cohort["splits"][split]}
    targets = data.get("targets")
    if not isinstance(targets, list) or len(targets) != len(public_cases) * len(evidence.VARIANTS):
        raise V7VisualRunnerError("hidden target inventory is incomplete")
    indexed: dict[tuple[str, str], dict[str, Any]] = {}
    for target in targets:
        if not isinstance(target, dict) or set(target) != TARGET_KEYS:
            raise V7VisualRunnerError("hidden target contract is invalid")
        variant = target["variant"]
        case_id = target["case_id"]
        key = (variant, case_id)
        if variant not in evidence.VARIANTS or case_id not in public_cases or key in indexed:
            raise V7VisualRunnerError("hidden target identity is unexpected or duplicated")
        root_value = target["root"]
        if not isinstance(root_value, str) or not Path(root_value).is_absolute():
            raise V7VisualRunnerError("hidden target root must be absolute")
        target_root = Path(root_value).resolve(strict=True)
        if not target_root.is_dir() or target_root.is_symlink():
            raise V7VisualRunnerError("hidden target root is missing or unsafe")
        states = target["states"]
        if not isinstance(states, dict) or set(states) != {"base", "interaction"}:
            raise V7VisualRunnerError("hidden state inventory must contain base and interaction")
        normalized_states: dict[str, dict[str, str]] = {}
        for state, contract in states.items():
            if not isinstance(contract, dict) or set(contract) != STATE_KEYS:
                raise V7VisualRunnerError("hidden state contract is invalid")
            route = _safe_route(target_root, contract["route"])
            if not isinstance(contract["spec"], str) or not Path(contract["spec"]).is_absolute():
                raise V7VisualRunnerError("hidden state spec must be absolute")
            spec = _outside_repository(Path(contract["spec"]), repository_root, "hidden state spec")
            normalized_states[state] = {
                "route": str(route),
                "route_sha256": _digest(route),
                "spec": str(spec),
                "spec_sha256": _digest(spec),
            }
        indexed[key] = {"root": str(target_root), "states": normalized_states}
    if set(indexed) != {(variant, case_id) for variant in evidence.VARIANTS for case_id in public_cases}:
        raise V7VisualRunnerError("hidden target inventory is incomplete")
    return indexed


def _empty_directory(path: Path, label: str) -> Path:
    resolved = path.resolve(strict=True)
    if not resolved.is_dir() or resolved.is_symlink() or any(resolved.iterdir()):
        raise V7VisualRunnerError(f"{label} must be an existing empty real directory")
    return resolved


def _write_once(path: Path, value: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise V7VisualRunnerError(f"refusing to overwrite ledger: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _run_auditor(command: list[str], root: Path, timeout_seconds: int) -> tuple[int, str]:
    process = subprocess.Popen(
        command,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        process.communicate(timeout=timeout_seconds)
        return process.returncode, "auditor_nonzero"
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=2)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)
        return 124, "capture_hard_timeout"
    finally:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)


def _write_completed_ledger(
    path: Path,
    value: dict[str, Any],
    manifest_path: Path,
    result_dir: Path,
    screenshot_dir: Path,
    repository_root: Path,
) -> None:
    if path.exists() or path.is_symlink():
        raise V7VisualRunnerError(f"refusing to overwrite ledger: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".json", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        evidence.validate(manifest_path, temporary_path, result_dir, screenshot_dir, repository_root)
        os.replace(temporary_path, path)
    except BaseException:
        try:
            temporary_path.unlink()
        except OSError:
            pass
        raise


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = args.repository_root.resolve(strict=True)
    manifest_path = args.manifest.resolve(strict=True)
    preflight.validate_manifest(manifest_path, root)
    cohort = _load(manifest_path, "cohort manifest")
    if args.split not in cohort["splits"]:
        raise V7VisualRunnerError("split is not present in cohort")
    hidden_path = _outside_repository(args.hidden_matrix, root, "hidden matrix")
    targets = load_hidden_matrix(hidden_path, cohort, args.split, root)
    roots = [Path(target["root"]).resolve(strict=True) for target in targets.values()]
    if len(roots) != len(set(roots)):
        raise V7VisualRunnerError("accepted and candidate targets must use distinct roots")
    generation_records: dict[tuple[str, str], dict[str, str]] = {}
    for (variant, case_id), target in targets.items():
        generation_records[(variant, case_id)] = validate_target_provenance(
            Path(target["root"]), variant, case_id, cohort, manifest_path, root
        )
    validate_generation_cohort(generation_records, {item["id"] for item in cohort["splits"][args.split]})
    input_records = [
        {
            "variant": variant,
            "case_id": case_id,
            "state": state,
            "route_sha256": contract["route_sha256"],
            "spec_sha256": contract["spec_sha256"],
        }
        for (variant, case_id), target in sorted(targets.items())
        for state, contract in sorted(target["states"].items())
    ]
    input_inventory_sha256 = hashlib.sha256(
        json.dumps(input_records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    capture_timeout = cohort["timeouts"]["capture"]["hard_seconds"]
    result_dir = _empty_directory(args.result_dir, "result directory")
    screenshot_dir = _empty_directory(args.screenshot_dir, "screenshot directory")
    expected = evidence.expected_inventory(cohort, args.split)
    attempts: list[dict[str, Any]] = []
    for key in expected:
        variant, case_id, state, profile, engine = key
        state_input = targets[(variant, case_id)]["states"][state]
        stem = evidence.artifact_stem(key)
        result = result_dir / f"{stem}.json"
        screenshot = screenshot_dir / f"{stem}.png"
        history: list[dict[str, Any]] = []
        for number in range(1, args.max_attempts + 1):
            if _digest(Path(state_input["route"])) != state_input["route_sha256"] or _digest(Path(state_input["spec"])) != state_input["spec_sha256"]:
                raise V7VisualRunnerError(f"route or hidden spec drifted during capture: {stem}")
            for partial in (result, screenshot):
                if partial.exists() and partial.is_file() and not partial.is_symlink():
                    partial.unlink()
            started = _now()
            with tempfile.TemporaryDirectory(prefix="wow-v7-visual-opaque-") as opaque_directory:
                opaque_route = Path(opaque_directory) / "index.html"
                shutil.copy2(state_input["route"], opaque_route)
                command = [
                    "node", str(AUDITOR),
                    "--url", opaque_route.as_uri(),
                    "--variant", variant,
                    "--case-id", case_id,
                    "--state", state,
                    "--profile", profile,
                    "--engine", engine,
                    "--spec", state_input["spec"],
                    "--screenshot", str(screenshot),
                    "--output", str(result),
                ]
                exit_code, failure_class = _run_auditor(command, root, capture_timeout)
            finished = _now()
            if exit_code in {0, 2} and result.is_file() and screenshot.is_file():
                completed_attempt = {
                    "number": number,
                    "started_at": started,
                    "finished_at": finished,
                    "status": "completed",
                    "exit_code": exit_code,
                    "result": result.name,
                    "result_sha256": _digest(result),
                    "screenshot": screenshot.name,
                    "screenshot_sha256": _digest(screenshot),
                    "route_sha256": state_input["route_sha256"],
                    "spec_sha256": state_input["spec_sha256"],
                }
                try:
                    verdict = evidence._validate_result(
                        key,
                        result,
                        screenshot,
                        completed_attempt["result_sha256"],
                        completed_attempt["screenshot_sha256"],
                        state_input["spec_sha256"],
                    )
                    if (verdict == "clean") != (exit_code == 0):
                        raise evidence.V7EvidenceError("auditor exit code and recomputed verdict disagree")
                except evidence.V7EvidenceError:
                    exit_code = 1
                    failure_class = "invalid_evidence"
                else:
                    history.append(completed_attempt)
                    break
            history.append({
                "number": number,
                "started_at": started,
                "finished_at": finished,
                "status": "infrastructure_failure",
                "exit_code": exit_code,
                "failure_class": failure_class,
            })
        identity = dict(zip(("variant", "case_id", "state", "profile", "engine"), key))
        attempts.append({"key": identity, "attempts": history})
        if history[-1]["status"] != "completed":
            ledger = {
                "schema_version": 1,
                "cohort_manifest": {"path": manifest_path.relative_to(root).as_posix(), "sha256": _digest(manifest_path)},
                "split": args.split,
                "status": "failed",
                "variants": list(evidence.VARIANTS),
                "expected_count": len(expected),
                "hidden_matrix_sha256": _digest(hidden_path),
                "input_inventory_sha256": input_inventory_sha256,
                "attempts": attempts,
            }
            _write_once(args.ledger.resolve(strict=False), ledger)
            raise V7VisualRunnerError(f"capture exhausted retries: {stem}")
    ledger = {
        "schema_version": 1,
        "cohort_manifest": {"path": manifest_path.relative_to(root).as_posix(), "sha256": _digest(manifest_path)},
        "split": args.split,
        "status": "completed",
        "variants": list(evidence.VARIANTS),
        "expected_count": len(expected),
        "hidden_matrix_sha256": _digest(hidden_path),
        "input_inventory_sha256": input_inventory_sha256,
        "attempts": attempts,
    }
    _write_completed_ledger(
        args.ledger.resolve(strict=False), ledger, manifest_path, result_dir, screenshot_dir, root
    )
    return ledger


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--hidden-matrix", required=True, type=Path)
    parser.add_argument("--split", choices=("development", "sealed_validation", "sealed_test"), required=True)
    parser.add_argument("--result-dir", required=True, type=Path)
    parser.add_argument("--screenshot-dir", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    parser.add_argument("--max-attempts", type=int, default=3, choices=(1, 2, 3))
    args = parser.parse_args()
    try:
        ledger = run(args)
    except (OSError, subprocess.SubprocessError, V7VisualRunnerError, evidence.V7EvidenceError, preflight.PreflightError) as error:
        print(f"v7 visual matrix failed: {error}", file=sys.stderr)
        return 1
    print(f"v7 visual matrix completed: {ledger['expected_count']} screenshots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
