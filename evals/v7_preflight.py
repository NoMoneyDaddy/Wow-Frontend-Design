#!/usr/bin/env python3
"""Freeze and validate the public v7-A1 cohort contract without network access."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


MAX_JSON_BYTES = 1_048_576
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_PACKAGE_BYTES = 32 * 1024 * 1024
MAX_PACKAGE_FILES = 512
MAX_JSON_DEPTH = 32
CONFIG_KEYS = {
    "schema_version",
    "cohort_id",
    "stage",
    "baseline_commit",
    "candidate",
    "model",
    "timeouts",
    "splits",
    "screenshots",
    "hidden_material_policy",
    "evaluator_paths",
}
CANDIDATE_KEYS = {"id", "hypothesis", "editable_paths", "forbidden_families", "reference_sha256"}
MODEL_KEYS = {"provider", "requested", "silent_fallback"}
CASE_KEYS = {"id", "family", "primary_task", "pressures", "required_states"}
TIMEOUT_KEYS = {"inactivity_seconds", "hard_seconds", "source"}
SCREENSHOT_KEYS = {
    "required_profiles",
    "affected_profiles",
    "engine_parity",
    "required_states",
    "before_after_on_finding",
    "blind_review",
}
HIDDEN_POLICY_KEYS = {"storage", "forbidden_keys"}
MANIFEST_KEYS = {
    "schema_version",
    "cohort_id",
    "stage",
    "frozen_at",
    "config",
    "baseline",
    "candidate",
    "model",
    "timeouts",
    "splits",
    "screenshots",
    "hidden_material_policy",
    "toolchain",
    "evaluators",
}
EXPECTED_EDITABLE_PATH = "wow-frontend-design/references/typographic-layout.md"
EXPECTED_SPLIT_COUNTS = {"development": 2, "sealed_validation": 4, "sealed_test": 2}
EXPECTED_PROFILES = {
    "desktop",
    "standard-desktop",
    "short-desktop",
    "tablet",
    "mobile",
    "compact-mobile",
}
EXPECTED_ENGINES = {"chromium", "firefox", "webkit"}
EXPECTED_PACKAGES = ("playwright", "@google/design.md")
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
FORBIDDEN_HIDDEN_KEYS = {
    "prompt",
    "full_prompt",
    "selector",
    "selectors",
    "weight",
    "weights",
    "expected_dom",
    "expected_html",
    "rubric_answer",
}


class PreflightError(ValueError):
    """Raised when the v7 public contract or frozen evidence is unsafe or inconsistent."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise PreflightError(f"duplicate JSON key is forbidden: {key!r}")
        value[key] = child
    return value


def _check_depth(value: Any, depth: int = 0) -> None:
    if depth > MAX_JSON_DEPTH:
        raise PreflightError(f"JSON nesting exceeds {MAX_JSON_DEPTH}")
    if isinstance(value, dict):
        for child in value.values():
            _check_depth(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _check_depth(child, depth + 1)


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        mode = path.lstat().st_mode
    except OSError as error:
        raise PreflightError(f"cannot stat {label}: {error}") from error
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise PreflightError(f"{label} must be a regular non-symlink file")
    size = path.stat().st_size
    if size > MAX_JSON_BYTES:
        raise PreflightError(f"{label} exceeds {MAX_JSON_BYTES} bytes")
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object_without_duplicates)
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise PreflightError(f"cannot read valid {label}: {error}") from error
    if not isinstance(data, dict):
        raise PreflightError(f"{label} root must be an object")
    _check_depth(data)
    return data


def _safe_repo_file(raw: Any, root: Path, label: str) -> Path:
    if not isinstance(raw, str) or not raw or "\x00" in raw or "\\" in raw:
        raise PreflightError(f"{label} must be a non-empty POSIX path")
    relative = PurePosixPath(raw)
    if relative.is_absolute() or not relative.parts or "." in relative.parts or ".." in relative.parts:
        raise PreflightError(f"{label} is unsafe: {raw!r}")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise PreflightError(f"{label} traverses a symlink: {raw!r}")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as error:
        raise PreflightError(f"{label} is missing or escapes the repository: {raw!r}") from error
    if not resolved.is_file():
        raise PreflightError(f"{label} must resolve to a regular file: {raw!r}")
    if resolved.stat().st_size > MAX_FILE_BYTES:
        raise PreflightError(f"{label} exceeds {MAX_FILE_BYTES} bytes: {raw!r}")
    return resolved


def _string(value: Any, label: str, *, minimum: int = 1, maximum: int = 1_000) -> str:
    if (
        not isinstance(value, str)
        or value != value.strip()
        or len(value) < minimum
        or len(value) > maximum
        or not value.isprintable()
    ):
        raise PreflightError(f"{label} must be a bounded printable string")
    return value


def _string_list(value: Any, label: str, *, minimum: int = 1, maximum: int = 64) -> list[str]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise PreflightError(f"{label} must contain {minimum}..{maximum} strings")
    values = [_string(item, f"{label}[{index}]", maximum=300) for index, item in enumerate(value)]
    if len(values) != len(set(values)):
        raise PreflightError(f"{label} must contain unique values")
    return values


def _reject_hidden_material(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).casefold().replace("-", "_")
            if normalized in FORBIDDEN_HIDDEN_KEYS:
                raise PreflightError(f"hidden evaluation material is forbidden in public config: {path}.{key}")
            _reject_hidden_material(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_hidden_material(child, f"{path}[{index}]")


def _validate_config(data: dict[str, Any], root: Path) -> dict[str, Any]:
    if set(data) != CONFIG_KEYS or data.get("schema_version") != 1:
        raise PreflightError("config root or schema_version is invalid")
    _reject_hidden_material(data)
    cohort_id = _string(data["cohort_id"], "cohort_id", maximum=80)
    if ID_PATTERN.fullmatch(cohort_id) is None or not cohort_id.startswith("v7-a1-"):
        raise PreflightError("cohort_id must be v7-a1-* lowercase kebab-case")
    if data["stage"] not in {"pilot_ready", "frozen"}:
        raise PreflightError("stage must be pilot_ready or frozen")
    if not isinstance(data["baseline_commit"], str) or COMMIT_PATTERN.fullmatch(data["baseline_commit"]) is None:
        raise PreflightError("baseline_commit must be a full lowercase Git SHA-1")

    candidate = data["candidate"]
    if not isinstance(candidate, dict) or set(candidate) != CANDIDATE_KEYS:
        raise PreflightError("candidate contract is invalid")
    if not isinstance(candidate["id"], str) or re.fullmatch(r"v7-a[1-9][0-9]*", candidate["id"]) is None:
        raise PreflightError("candidate.id must match v7-a followed by a positive integer")
    _string(candidate["hypothesis"], "candidate.hypothesis", minimum=80, maximum=1_500)
    editable_paths = _string_list(candidate["editable_paths"], "candidate.editable_paths")
    if editable_paths != [EXPECTED_EDITABLE_PATH]:
        raise PreflightError(f"candidate editable path must be exactly {EXPECTED_EDITABLE_PATH}")
    forbidden = set(_string_list(candidate["forbidden_families"], "candidate.forbidden_families"))
    required_forbidden = {"intrinsic-layout", "native-controls", "color", "motion", "framework-adapter", "registry-security"}
    if forbidden != required_forbidden:
        raise PreflightError(f"candidate.forbidden_families must equal {sorted(required_forbidden)}")
    reference_sha256 = candidate["reference_sha256"]
    if data["stage"] == "pilot_ready":
        if reference_sha256 is not None:
            raise PreflightError("pilot_ready candidate.reference_sha256 must remain null")
    else:
        if not isinstance(reference_sha256, str) or SHA256_PATTERN.fullmatch(reference_sha256) is None:
            raise PreflightError("frozen candidate.reference_sha256 must be a lowercase SHA-256")
        candidate_path = _safe_repo_file(EXPECTED_EDITABLE_PATH, root, "frozen candidate reference")
        if _sha256_bytes(candidate_path.read_bytes()) != reference_sha256:
            raise PreflightError("frozen candidate reference bytes drifted")

    model = data["model"]
    if not isinstance(model, dict) or set(model) != MODEL_KEYS:
        raise PreflightError("model contract is invalid")
    if model != {"provider": "codex", "requested": "gpt-5.4-mini", "silent_fallback": False}:
        raise PreflightError("v7-A1 model must be exact Codex gpt-5.4-mini without silent fallback")

    timeouts = data["timeouts"]
    if not isinstance(timeouts, dict) or set(timeouts) != {"generation", "lint", "capture"}:
        raise PreflightError("timeouts must define generation, lint and capture")
    for stage, contract in timeouts.items():
        if not isinstance(contract, dict) or set(contract) != TIMEOUT_KEYS:
            raise PreflightError(f"timeouts.{stage} is invalid")
        idle = contract["inactivity_seconds"]
        hard = contract["hard_seconds"]
        if not isinstance(idle, int) or not isinstance(hard, int) or not 30 <= idle <= hard <= 14_400:
            raise PreflightError(f"timeouts.{stage} must satisfy 30 <= inactivity <= hard <= 14400")
        if contract["source"] not in {"provisional-before-pilot", "observed-after-pilot", "frozen-after-pilot"}:
            raise PreflightError(f"timeouts.{stage}.source is invalid")
        if data["stage"] == "frozen" and contract["source"] != "frozen-after-pilot":
            raise PreflightError("a frozen cohort cannot retain provisional timeout values")

    splits = data["splits"]
    if not isinstance(splits, dict) or set(splits) != set(EXPECTED_SPLIT_COUNTS):
        raise PreflightError("splits must define development, sealed_validation and sealed_test")
    seen_cases: set[str] = set()
    for split, expected_count in EXPECTED_SPLIT_COUNTS.items():
        cases = splits[split]
        if not isinstance(cases, list) or len(cases) != expected_count:
            raise PreflightError(f"splits.{split} must contain exactly {expected_count} cases")
        for index, case in enumerate(cases):
            label = f"splits.{split}[{index}]"
            if not isinstance(case, dict) or set(case) != CASE_KEYS:
                raise PreflightError(f"{label} must contain exactly {sorted(CASE_KEYS)}")
            case_id = _string(case["id"], f"{label}.id", maximum=80)
            if ID_PATTERN.fullmatch(case_id) is None or case_id in seen_cases:
                raise PreflightError(f"{label}.id must be unique lowercase kebab-case")
            seen_cases.add(case_id)
            _string(case["family"], f"{label}.family", minimum=8, maximum=120)
            _string(case["primary_task"], f"{label}.primary_task", minimum=20, maximum=400)
            _string_list(case["pressures"], f"{label}.pressures", minimum=2, maximum=10)
            _string_list(case["required_states"], f"{label}.required_states", minimum=2, maximum=10)

    screenshots = data["screenshots"]
    if not isinstance(screenshots, dict) or set(screenshots) != SCREENSHOT_KEYS:
        raise PreflightError("screenshots contract is invalid")
    required_profiles = set(_string_list(screenshots["required_profiles"], "screenshots.required_profiles"))
    affected_profiles = set(_string_list(screenshots["affected_profiles"], "screenshots.affected_profiles"))
    engines = set(_string_list(screenshots["engine_parity"], "screenshots.engine_parity"))
    if required_profiles != {"desktop", "mobile"} or affected_profiles != EXPECTED_PROFILES:
        raise PreflightError("screenshot profiles must preserve desktop/mobile and the full A1 affected set")
    if engines != EXPECTED_ENGINES:
        raise PreflightError("engine parity must contain chromium, firefox and webkit")
    if set(_string_list(screenshots["required_states"], "screenshots.required_states")) != {"base", "interaction"}:
        raise PreflightError("screenshots.required_states must contain base and interaction")
    if screenshots["before_after_on_finding"] is not True or screenshots["blind_review"] is not True:
        raise PreflightError("finding screenshots and blind review must be required")

    hidden = data["hidden_material_policy"]
    if not isinstance(hidden, dict) or set(hidden) != HIDDEN_POLICY_KEYS:
        raise PreflightError("hidden_material_policy is invalid")
    if hidden["storage"] != "evaluator-owned-outside-repository":
        raise PreflightError("hidden material must stay outside the repository")
    if set(_string_list(hidden["forbidden_keys"], "hidden_material_policy.forbidden_keys")) != FORBIDDEN_HIDDEN_KEYS:
        raise PreflightError("hidden_material_policy.forbidden_keys must match the validator denylist")

    evaluator_paths = _string_list(data["evaluator_paths"], "evaluator_paths", minimum=3, maximum=32)
    for index, item in enumerate(evaluator_paths):
        _safe_repo_file(item, root, f"evaluator_paths[{index}]")
    return data


def _run_git(root: Path, arguments: list[str], *, text: bool = False) -> bytes | str:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            capture_output=True,
            text=text,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise PreflightError(f"git command failed: {' '.join(arguments)}: {error}") from error
    return completed.stdout


def _package_snapshot(root: Path, commit: str) -> dict[str, Any]:
    resolved = str(_run_git(root, ["rev-parse", "--verify", f"{commit}^{{commit}}"], text=True)).strip()
    if resolved != commit:
        raise PreflightError("baseline_commit does not resolve to itself")
    raw = bytes(_run_git(root, ["ls-tree", "-rz", "--full-tree", commit, "--", "wow-frontend-design"]))
    entries = [entry for entry in raw.split(b"\x00") if entry]
    if not 1 <= len(entries) <= MAX_PACKAGE_FILES:
        raise PreflightError("accepted package file count is outside the bounded inventory")
    records: list[dict[str, Any]] = []
    total = 0
    for entry in entries:
        try:
            metadata, raw_path = entry.split(b"\t", 1)
            mode, kind, object_id = metadata.decode("ascii").split(" ")
            path = raw_path.decode("utf-8")
        except (ValueError, UnicodeError) as error:
            raise PreflightError("cannot parse accepted package Git tree") from error
        if mode not in {"100644", "100755"} or kind != "blob":
            raise PreflightError(f"accepted package contains a non-regular blob: {path}")
        relative = PurePosixPath(path)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or "\\" in path
            or not path.isprintable()
            or not path.startswith("wow-frontend-design/")
        ):
            raise PreflightError(f"accepted package contains an unsafe path: {path}")
        body = bytes(_run_git(root, ["cat-file", "blob", object_id]))
        total += len(body)
        if len(body) > MAX_FILE_BYTES or total > MAX_PACKAGE_BYTES:
            raise PreflightError("accepted package exceeds the bounded byte inventory")
        records.append({"path": path, "mode": mode, "bytes": len(body), "sha256": _sha256_bytes(body)})
    records.sort(key=lambda item: item["path"])
    if EXPECTED_EDITABLE_PATH not in {item["path"] for item in records}:
        raise PreflightError("accepted package does not contain the candidate editable path")
    return {
        "commit": commit,
        "file_count": len(records),
        "total_bytes": total,
        "tree_sha256": _sha256_bytes(_canonical_bytes(records)),
        "files": records,
    }


def _file_record(path: Path, root: Path) -> dict[str, Any]:
    body = path.read_bytes()
    return {"path": path.relative_to(root).as_posix(), "bytes": len(body), "sha256": _sha256_bytes(body)}


def _toolchain(root: Path) -> dict[str, Any]:
    lock = _safe_repo_file("package-lock.json", root, "package-lock.json")
    payload = _load_json(lock, "package-lock.json")
    packages = payload.get("packages")
    if not isinstance(packages, dict):
        raise PreflightError("package-lock.json has no packages object")
    records: dict[str, dict[str, str]] = {}
    for name in EXPECTED_PACKAGES:
        record = packages.get(f"node_modules/{name}")
        if not isinstance(record, dict):
            raise PreflightError(f"package-lock.json has no {name} record")
        selected = {field: record.get(field) for field in ("version", "resolved", "integrity")}
        if any(not isinstance(value, str) or not value or any(character.isspace() for character in value) for value in selected.values()):
            raise PreflightError(f"package-lock.json has no exact integrity-bound {name} record")
        records[name] = selected  # type: ignore[assignment]
    return {"lockfile": _file_record(lock, root), "packages": records}


def _parse_timestamp(value: str) -> str:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise PreflightError("frozen_at must be canonical UTC YYYY-MM-DDTHH:MM:SSZ") from error
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_manifest(config_path: Path, repository_root: Path, frozen_at: str) -> dict[str, Any]:
    root = repository_root.resolve(strict=True)
    config = _load_json(config_path, "v7 public config")
    _validate_config(config, root)
    try:
        config_relative = config_path.resolve(strict=True).relative_to(root).as_posix()
    except (OSError, ValueError) as error:
        raise PreflightError("v7 public config must stay inside the repository") from error
    config_file = _safe_repo_file(config_relative, root, "v7 public config")
    evaluators = [
        _file_record(_safe_repo_file(item, root, f"evaluator_paths[{index}]"), root)
        for index, item in enumerate(config["evaluator_paths"])
    ]
    return {
        "schema_version": 1,
        "cohort_id": config["cohort_id"],
        "stage": config["stage"],
        "frozen_at": _parse_timestamp(frozen_at),
        "config": _file_record(config_file, root),
        "baseline": _package_snapshot(root, config["baseline_commit"]),
        "candidate": config["candidate"],
        "model": config["model"],
        "timeouts": config["timeouts"],
        "splits": config["splits"],
        "screenshots": config["screenshots"],
        "hidden_material_policy": config["hidden_material_policy"],
        "toolchain": _toolchain(root),
        "evaluators": evaluators,
    }


def validate_manifest(manifest_path: Path, repository_root: Path, *, require_stage: str | None = None) -> tuple[int, int]:
    root = repository_root.resolve(strict=True)
    manifest = _load_json(manifest_path, "v7 frozen manifest")
    if set(manifest) != MANIFEST_KEYS or manifest.get("schema_version") != 1:
        raise PreflightError("frozen manifest root or schema_version is invalid")
    _parse_timestamp(_string(manifest["frozen_at"], "frozen_at", maximum=20))
    if require_stage is not None and manifest.get("stage") != require_stage:
        raise PreflightError(f"frozen manifest stage must equal {require_stage}")
    config_record = manifest["config"]
    if not isinstance(config_record, dict) or set(config_record) != {"path", "bytes", "sha256"}:
        raise PreflightError("frozen manifest config record is invalid")
    config_path = _safe_repo_file(config_record["path"], root, "frozen config path")
    if _file_record(config_path, root) != config_record:
        raise PreflightError("v7 public config bytes drifted after freeze")
    config = _load_json(config_path, "v7 public config")
    _validate_config(config, root)
    for key in (
        "cohort_id",
        "stage",
        "candidate",
        "model",
        "timeouts",
        "splits",
        "screenshots",
        "hidden_material_policy",
    ):
        if manifest.get(key) != config.get(key):
            raise PreflightError(f"frozen manifest disagrees with config field: {key}")
    expected_baseline = _package_snapshot(root, config["baseline_commit"])
    if manifest["baseline"] != expected_baseline:
        raise PreflightError("accepted package snapshot drifted or was tampered")
    expected_toolchain = _toolchain(root)
    if manifest["toolchain"] != expected_toolchain:
        raise PreflightError("toolchain lock drifted after freeze")
    expected_evaluators = [
        _file_record(_safe_repo_file(item, root, f"evaluator_paths[{index}]"), root)
        for index, item in enumerate(config["evaluator_paths"])
    ]
    if manifest["evaluators"] != expected_evaluators:
        raise PreflightError("evaluator bytes drifted after freeze")
    return int(expected_baseline["file_count"]), len(expected_evaluators)


def _write_manifest(path: Path, data: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise PreflightError(f"refusing to overwrite frozen manifest: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[1])
    subparsers = parser.add_subparsers(dest="command", required=True)
    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("config", type=Path)
    freeze.add_argument("output", type=Path)
    freeze.add_argument("--frozen-at", default=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    validate = subparsers.add_parser("validate")
    validate.add_argument("manifest", type=Path)
    validate.add_argument("--require-stage", choices=("pilot_ready", "frozen"))
    args = parser.parse_args()
    try:
        root = args.repository_root.expanduser().resolve(strict=True)
        if args.command == "freeze":
            output = args.output.expanduser().resolve(strict=False)
            try:
                output.relative_to(root)
            except ValueError as error:
                raise PreflightError("frozen manifest output must stay inside the repository") from error
            data = build_manifest(args.config.expanduser().resolve(strict=True), root, args.frozen_at)
            _write_manifest(output, data)
            print(
                f"v7 preflight frozen: {data['baseline']['file_count']} package files, "
                f"{len(data['evaluators'])} evaluators, stage={data['stage']}"
            )
        else:
            files, evaluators = validate_manifest(
                args.manifest.expanduser().resolve(strict=True),
                root,
                require_stage=args.require_stage,
            )
            print(f"v7 preflight valid: {files} package files, {evaluators} evaluators")
    except (OSError, PreflightError) as error:
        print(f"v7 preflight invalid: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
