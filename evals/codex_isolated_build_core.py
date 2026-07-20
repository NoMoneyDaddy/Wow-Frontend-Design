#!/usr/bin/env python3
"""Generation-neutral fail-closed core for isolated Codex execution."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import resource
import shutil
import signal
import stat
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, NamedTuple


ROOT = Path(__file__).resolve().parents[1]
TRACE_VALIDATOR = ROOT / "evals" / "validate_codex_log_policy.py"
DEFAULT_MODEL = "gpt-5.4-mini"
STAGE_LIMIT = 8 * 1024 * 1024
LOG_LIMIT = 16 * 1024 * 1024
SKILL_LIMIT = 16 * 1024 * 1024
SKILL_FILE_LIMIT = 1_048_576
MAX_STAGE_ENTRIES = 16
MAX_SKILL_ENTRIES = 512
MODEL_LIMIT = 128
SKILL_REFERENCE_FILE_LIMIT = 64 * 1024
SKILL_REFERENCE_TOTAL_LIMIT = 128 * 1024
MAX_SKILL_REFERENCES = 3
SKILL_REFERENCE_PATH = re.compile(r"references/[a-z0-9][a-z0-9-]{0,127}\.md")


def _module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load required module: {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


trace_policy = _module("current_skill_trace_policy", TRACE_VALIDATOR)


class ExecutionSpec(NamedTuple):
    stage: Path
    stdout_log: Path
    stderr_log: Path
    skill_source: Path
    skill_name: str
    prompt: str
    model: str = DEFAULT_MODEL
    hard_seconds: int = 1800
    inactivity_seconds: int | None = None
    reasoning_effort: str | None = None
    skill_references: tuple[tuple[str, int, str], ...] = ()


class RunnerError(ValueError):
    """Raised when an isolated generation cannot be executed safely."""


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _validate_model(model: str) -> str:
    if (
        not isinstance(model, str)
        or not 1 <= len(model) <= MODEL_LIMIT
        or any(not (character.isalnum() or character in ".:_-/") for character in model)
        or model.startswith(("-", "/"))
        or ".." in model
    ):
        raise RunnerError("model must be a bounded identifier")
    return model


def _validate_reasoning_effort(value: str | None) -> str | None:
    if value is not None and value not in {"low", "medium", "high", "xhigh"}:
        raise RunnerError("reasoning effort must be one of low, medium, high, or xhigh")
    return value


def _tree_records(source: Path) -> list[dict[str, Any]]:
    if not source.is_dir() or source.is_symlink():
        raise RunnerError("wow-frontend-design skill source is missing or unsafe")
    records: list[dict[str, Any]] = []
    total = 0
    count = 0
    for path in sorted(source.rglob("*")):
        count += 1
        if count > MAX_SKILL_ENTRIES:
            raise RunnerError("skill snapshot entry quota exceeded")
        try:
            info = path.lstat()
        except OSError as error:
            raise RunnerError("skill snapshot changed while being inspected") from error
        relative = path.relative_to(source).as_posix()
        mode = f"{stat.S_IMODE(info.st_mode):04o}"
        if stat.S_ISDIR(info.st_mode):
            records.append({"path": relative, "kind": "directory", "mode": mode})
            continue
        if not stat.S_ISREG(info.st_mode) or path.is_symlink():
            raise RunnerError("skill snapshot contains a non-regular entry")
        if info.st_size > SKILL_FILE_LIMIT:
            raise RunnerError("skill snapshot contains an oversized file")
        total += info.st_size
        if total > SKILL_LIMIT:
            raise RunnerError("skill snapshot byte quota exceeded")
        records.append(
            {
                "path": relative,
                "kind": "file",
                "mode": mode,
                "bytes": info.st_size,
                "sha256": _digest(path),
            }
        )
    if not records or not any(record["path"] == "SKILL.md" and record["kind"] == "file" for record in records):
        raise RunnerError("skill snapshot has no SKILL.md")
    return records


def _tree_summary(records: list[dict[str, Any]], name: str) -> dict[str, Any]:
    encoded = json.dumps(records, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return {
        "name": name,
        "entry_count": len(records),
        "file_count": sum(record["kind"] == "file" for record in records),
        "bytes": sum(record.get("bytes", 0) for record in records),
        "tree_sha256": _digest_bytes(encoded),
        "inventory": records,
    }


def _validated_skill_reference_records(
    records: tuple[tuple[str, int, str], ...],
) -> tuple[tuple[str, int, str], ...]:
    if not isinstance(records, tuple) or len(records) > MAX_SKILL_REFERENCES:
        raise RunnerError("skill reference selection may contain at most three files")
    normalized: list[tuple[str, int, str]] = []
    seen: set[str] = set()
    total = 0
    for record in records:
        if (
            not isinstance(record, tuple)
            or len(record) != 3
            or not isinstance(record[0], str)
            or SKILL_REFERENCE_PATH.fullmatch(record[0]) is None
            or type(record[1]) is not int
            or not 1 <= record[1] <= SKILL_REFERENCE_FILE_LIMIT
            or not isinstance(record[2], str)
            or re.fullmatch(r"[0-9a-f]{64}", record[2]) is None
        ):
            raise RunnerError("skill reference record is invalid")
        folded = record[0].casefold()
        if folded in seen:
            raise RunnerError("skill reference selection contains a duplicate")
        seen.add(folded)
        total += record[1]
        if total > SKILL_REFERENCE_TOTAL_LIMIT:
            raise RunnerError("skill reference context byte quota exceeded")
        normalized.append(record)
    return tuple(normalized)


def _skill_reference_summary(
    records: tuple[tuple[str, int, str], ...],
) -> dict[str, Any]:
    return {
        "files": [
            {"path": path, "bytes": size, "sha256": digest}
            for path, size, digest in records
        ],
        "total_bytes": sum(size for _, size, _ in records),
    }


def _assert_skill_reference_records(
    tree: dict[str, Any], records: tuple[tuple[str, int, str], ...]
) -> None:
    files = {
        item["path"]: item
        for item in tree.get("inventory", ())
        if item.get("kind") == "file"
    }
    for path, size, digest in records:
        observed = files.get(path)
        if observed is None or observed.get("bytes") != size or observed.get("sha256") != digest:
            raise RunnerError("selected skill reference provenance drifted")


def _read_skill_reference(root: Path, path: str) -> tuple[os.stat_result, bytes, str]:
    """Read one fixed-depth reference through no-follow directory descriptors."""

    if SKILL_REFERENCE_PATH.fullmatch(path) is None:
        raise RunnerError("skill reference path is invalid")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:
        raise RunnerError("safe skill reference reads are unavailable on this platform")
    root_fd = references_fd = file_fd = None
    try:
        root_fd = os.open(root, os.O_RDONLY | directory | nofollow)
        references_fd = os.open("references", os.O_RDONLY | directory | nofollow, dir_fd=root_fd)
        file_fd = os.open(path.removeprefix("references/"), os.O_RDONLY | nofollow, dir_fd=references_fd)
        info = os.fstat(file_fd)
        if not stat.S_ISREG(info.st_mode) or not 1 <= info.st_size <= SKILL_REFERENCE_FILE_LIMIT:
            raise RunnerError("selected skill reference is not a bounded regular file")
        chunks: list[bytes] = []
        remaining = SKILL_REFERENCE_FILE_LIMIT + 1
        while remaining:
            chunk = os.read(file_fd, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if len(data) != info.st_size or len(data) > SKILL_REFERENCE_FILE_LIMIT:
            raise RunnerError("selected skill reference changed while being read")
        try:
            text = data.decode("utf-8")
        except UnicodeError as error:
            raise RunnerError("selected skill reference is not strict UTF-8") from error
        if "\x00" in text:
            raise RunnerError("selected skill reference contains NUL")
        return info, data, text
    except OSError as error:
        raise RunnerError("selected skill reference is unsafe or unreadable") from error
    finally:
        for descriptor in (file_fd, references_fd, root_fd):
            if descriptor is not None:
                os.close(descriptor)


def _assert_skill_reference_files(
    root: Path, records: tuple[tuple[str, int, str], ...]
) -> None:
    for path, size, digest in records:
        info, data, _ = _read_skill_reference(root, path)
        if (
            len(data) != size
            or _digest_bytes(data) != digest
        ):
            raise RunnerError("selected skill reference provenance drifted")


def prepare_skill_reference_context(
    source: Path, paths: tuple[str, ...]
) -> tuple[tuple[tuple[str, int, str], ...], tuple[dict[str, Any], ...]]:
    """Read a bounded, source-owned reference set and freeze its provenance."""

    if not isinstance(paths, tuple) or not 1 <= len(paths) <= MAX_SKILL_REFERENCES:
        raise RunnerError("skill reference selection must contain one to three files")
    before = _tree_records(source)
    files = {
        item["path"]: item
        for item in before
        if item.get("kind") == "file"
    }
    selected: list[tuple[str, int, str]] = []
    payload: list[dict[str, Any]] = []
    seen: set[str] = set()
    total = 0
    for path in paths:
        if not isinstance(path, str) or SKILL_REFERENCE_PATH.fullmatch(path) is None:
            raise RunnerError("skill reference must match references/<safe-name>.md")
        folded = path.casefold()
        if folded in seen:
            raise RunnerError("skill reference selection contains a duplicate")
        seen.add(folded)
        expected = files.get(path)
        if expected is None:
            raise RunnerError(f"unknown skill reference: {path}")
        info, data, text = _read_skill_reference(source, path)
        digest = _digest_bytes(data)
        if (
            info.st_size != expected.get("bytes")
            or len(data) != expected.get("bytes")
            or digest != expected.get("sha256")
        ):
            raise RunnerError(f"skill reference changed while being read: {path}")
        total += len(data)
        if total > SKILL_REFERENCE_TOTAL_LIMIT:
            raise RunnerError("skill reference context byte quota exceeded")
        selected.append((path, len(data), digest))
        payload.append({
            "path": path,
            "bytes": len(data),
            "sha256": digest,
            "content": text,
        })
    frozen = _validated_skill_reference_records(tuple(selected))
    if _tree_records(source) != before:
        raise RunnerError("skill snapshot drifted while references were being read")
    return frozen, tuple(payload)


def _snapshot_skill(source: Path, destination: Path, name: str) -> dict[str, Any]:
    before = _tree_records(source)
    destination.mkdir(mode=0o700, parents=True)
    for record in before:
        source_entry = source / record["path"]
        target_entry = destination / record["path"]
        if record["kind"] == "directory":
            target_entry.mkdir(mode=int(record["mode"], 8), parents=True, exist_ok=False)
            target_entry.chmod(int(record["mode"], 8))
        else:
            target_entry.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            shutil.copy2(source_entry, target_entry, follow_symlinks=False)
    copied = _tree_records(destination)
    after = _tree_records(source)
    if before != copied or before != after:
        raise RunnerError("skill snapshot drifted while being copied")
    return _tree_summary(copied, name)


def _validate_login(result: subprocess.CompletedProcess[str]) -> None:
    channels = [value.strip() for value in (result.stdout, result.stderr) if value and value.strip()]
    status = "\n".join(channels)
    if result.returncode != 0 or status != "Logged in using ChatGPT":
        raise RunnerError("Codex login status is not first-party ChatGPT")


def _codex_record(codex: Path, environment: dict[str, str]) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [str(codex), "--version"], env=environment, text=True, capture_output=True, check=False, timeout=15
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RunnerError("Codex CLI version preflight failed") from error
    version = result.stdout.strip()
    if result.returncode != 0 or re.fullmatch(r"codex-cli [A-Za-z0-9.+_-]{1,100}", version) is None:
        raise RunnerError("Codex CLI version preflight failed")
    info = codex.stat()
    return {
        "version": version,
        "bytes": info.st_size,
        "mode": f"{stat.S_IMODE(info.st_mode):04o}",
        "sha256": _digest(codex),
    }


def _isolated_environment(
    skill_source: Path, skill_name: str
) -> tuple[Path, dict[str, str], Path, dict[str, Any]]:
    isolation = Path(tempfile.mkdtemp(prefix="wow-current-codex-"))
    try:
        home = isolation / "home"
        codex_home = isolation / "codex"
        temp = isolation / "tmp"
        home.mkdir(mode=0o700)
        codex_home.mkdir(mode=0o700)
        temp.mkdir(mode=0o700)
        original_codex = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
        auth = original_codex / "auth.json"
        if not auth.is_file() or auth.is_symlink():
            raise RunnerError("Codex auth.json is missing or unsafe")
        shutil.copy2(auth, codex_home / "auth.json", follow_symlinks=False)
        (codex_home / "auth.json").chmod(0o600)
        skill_record = _snapshot_skill(skill_source, codex_home / "skills" / skill_name, skill_name)
        codex = shutil.which("codex")
        if not codex:
            raise RunnerError("codex CLI is unavailable")
        codex_path = Path(codex).resolve(strict=True)
        if not codex_path.is_file() or not os.access(codex_path, os.X_OK):
            raise RunnerError("codex CLI is unsafe")
        safe_path = f"{codex_path.parent}:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        environment = {
            "HOME": str(home),
            "CODEX_HOME": str(codex_home),
            "PATH": safe_path,
            "TMPDIR": str(temp),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
        }
        try:
            login_result = subprocess.run(
                [str(codex_path), "login", "status"],
                env=environment,
                text=True,
                capture_output=True,
                check=False,
                timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RunnerError("Codex CLI preflight failed") from error
        codex_record = _codex_record(codex_path, environment)
        _validate_login(login_result)
        return isolation, environment, codex_path, {"skill": skill_record, "codex": codex_record}
    except BaseException:
        shutil.rmtree(isolation, ignore_errors=True)
        raise


def _stage_fingerprint(stage: Path) -> tuple[tuple[str, str, int, int], ...]:
    records = []
    count = 0
    for path in sorted(stage.rglob("*")):
        count += 1
        if count > MAX_STAGE_ENTRIES:
            raise RunnerError("stage entry quota exceeded")
        info = path.lstat()
        kind = "directory" if stat.S_ISDIR(info.st_mode) else "file" if stat.S_ISREG(info.st_mode) else "other"
        size = info.st_size if kind == "file" else 0
        records.append((path.relative_to(stage).as_posix(), kind, size, info.st_mtime_ns))
    return tuple(records)


def _stage_bytes(stage: Path) -> int:
    return sum(size for _, _, size, _ in _stage_fingerprint(stage))


def _meaningful_event_count(lines: list[str]) -> int:
    count = 0
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and event.get("type") in {
            "thread.started",
            "turn.started",
            "item.started",
            "item.completed",
            "turn.completed",
            "turn.failed",
        }:
            count += 1
    return count


def _terminate(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=2)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    process.wait(timeout=5)


def _child_limits() -> None:
    os.setsid()
    resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024 * 1024, 2 * 1024 * 1024))


def _open_private_log(path: Path) -> Any:
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        return os.fdopen(descriptor, "w+b")
    except BaseException:
        os.close(descriptor)
        raise


def _read_fd_exact(descriptor: int, size: int) -> bytes:
    chunks: list[bytes] = []
    offset = 0
    while offset < size:
        chunk = os.pread(descriptor, size - offset, offset)
        if not chunk:
            raise RunnerError("generation log snapshot changed during read")
        chunks.append(chunk)
        offset += len(chunk)
    if os.fstat(descriptor).st_size != size:
        raise RunnerError("generation log snapshot changed during read")
    return b"".join(chunks)


def _run_codex(
    command: list[str],
    prompt: str,
    environment: dict[str, str],
    stage: Path,
    stdout_log: Path,
    stderr_log: Path,
    hard_seconds: int,
    inactivity_seconds: int | None = None,
    initial_fingerprint: tuple[tuple[str, str, int, int], ...] = (),
) -> tuple[int, str, int, bytes, bytes]:
    with _open_private_log(stdout_log) as stdout, _open_private_log(stderr_log) as stderr:
        process: subprocess.Popen[bytes] | None = None
        try:
            process = subprocess.Popen(
                command,
                cwd=stage,
                env=environment,
                stdin=subprocess.PIPE,
                stdout=stdout,
                stderr=stderr,
                start_new_session=False,
                preexec_fn=_child_limits,
            )
            assert process.stdin is not None
            process.stdin.write(prompt.encode("utf-8"))
            process.stdin.close()
            started = time.monotonic()
            last_progress = started
            last_fingerprint = initial_fingerprint
            log_offset = 0
            buffered = ""
            progress_events = 0
            reason = "completed"
            while process.poll() is None:
                now = time.monotonic()
                fingerprint = _stage_fingerprint(stage)
                if fingerprint != last_fingerprint:
                    last_fingerprint = fingerprint
                    last_progress = now
                    progress_events += 1
                stdout_size = os.fstat(stdout.fileno()).st_size
                if stdout_size > log_offset:
                    chunk = os.pread(stdout.fileno(), stdout_size - log_offset, log_offset)
                    log_offset += len(chunk)
                    decoded = buffered + chunk.decode("utf-8", errors="replace")
                    lines = decoded.splitlines(keepends=True)
                    buffered = "" if not lines or lines[-1].endswith(("\n", "\r")) else lines.pop()
                    meaningful = _meaningful_event_count([line.rstrip("\r\n") for line in lines])
                    if meaningful:
                        progress_events += meaningful
                        last_progress = now
                if _stage_bytes(stage) > STAGE_LIMIT:
                    reason = "resource_quota"
                    _terminate(process)
                    break
                if os.fstat(stdout.fileno()).st_size + os.fstat(stderr.fileno()).st_size > LOG_LIMIT:
                    reason = "resource_quota"
                    _terminate(process)
                    break
                if now - started >= hard_seconds:
                    reason = "hard_timeout"
                    _terminate(process)
                    break
                if inactivity_seconds is not None and now - last_progress >= inactivity_seconds:
                    reason = "inactivity_timeout"
                    _terminate(process)
                    break
                time.sleep(0.1)
            exit_code = process.wait(timeout=5)
        except (OSError, BrokenPipeError, subprocess.TimeoutExpired) as error:
            raise RunnerError("Codex process execution failed") from error
        finally:
            if process is not None:
                _terminate(process)
        stdout_info = os.fstat(stdout.fileno())
        stderr_info = os.fstat(stderr.fileno())
        try:
            stdout_path_info = stdout_log.lstat()
            stderr_path_info = stderr_log.lstat()
        except OSError as error:
            raise RunnerError("generation log provenance drifted during execution") from error
        if (
            stdout_log.is_symlink()
            or stderr_log.is_symlink()
            or (stdout_info.st_dev, stdout_info.st_ino)
            != (stdout_path_info.st_dev, stdout_path_info.st_ino)
            or (stderr_info.st_dev, stderr_info.st_ino)
            != (stderr_path_info.st_dev, stderr_path_info.st_ino)
        ):
            raise RunnerError("generation log provenance drifted during execution")
        stdout_data = _read_fd_exact(stdout.fileno(), stdout_info.st_size)
        stderr_data = _read_fd_exact(stderr.fileno(), stderr_info.st_size)
    return exit_code, reason, progress_events, stdout_data, stderr_data


def _validate_trace_bytes(
    raw: bytes, stage: Path, *, require_terminal: bool = True
) -> dict[str, Any]:
    try:
        lines = raw.decode("utf-8").splitlines()
        events = [json.loads(line) for line in lines if line.strip()]
        if any(not isinstance(event, dict) for event in events):
            raise RunnerError("Codex trace has no valid events")
        command_events = trace_policy.validate_events(events, stage, allow_commands=False)
    except (UnicodeError, json.JSONDecodeError, trace_policy.PolicyError) as error:
        raise RunnerError(f"Codex trace violated the controlled policy: {error}") from error
    event_types = [event.get("type") for event in events]
    if require_terminal and (not events or "turn.failed" in event_types or "turn.completed" not in event_types):
        raise RunnerError("Codex trace has no successful terminal event")
    completed_items = {"file_change": 0, "agent_message": 0}
    for event in events:
        if event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") not in completed_items:
            continue
        item_type = item["type"]
        completed_items[item_type] += 1
    usage_keys = (
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    )
    terminal_usage: dict[str, Any] = {"status": "unreported"}
    for event in reversed(events):
        if event.get("type") != "turn.completed":
            continue
        usage = event.get("usage")
        if not isinstance(usage, dict):
            break
        observed_usage = {
            key: usage[key]
            for key in usage_keys
            if type(usage.get(key)) is int and usage[key] >= 0
        }
        if observed_usage:
            terminal_usage = {"status": "reported", **observed_usage}
        break
    return {
        "policy": "passed",
        "event_count": len(events),
        "command_event_count": command_events,
        "successful_terminal_event": "turn.completed" in event_types and "turn.failed" not in event_types,
        "completed_item_counts": completed_items,
        "terminal_usage": terminal_usage,
    }


def _validate_trace(path: Path, stage: Path, *, require_terminal: bool = True) -> dict[str, Any]:
    try:
        if not path.is_file() or path.is_symlink():
            raise OSError("trace is missing or unsafe")
        raw = path.read_bytes()
    except OSError as error:
        raise RunnerError(f"Codex trace violated the controlled policy: {error}") from error
    return _validate_trace_bytes(raw, stage, require_terminal=require_terminal)


def _file_tool_records() -> dict[str, Any]:
    records: dict[str, Any] = {}
    for name, path in (
        ("core", Path(__file__).resolve()),
        ("trace_validator", TRACE_VALIDATOR),
    ):
        info = path.stat()
        records[name] = {
            "bytes": info.st_size,
            "mode": f"{stat.S_IMODE(info.st_mode):04o}",
            "sha256": _digest(path),
        }
    return records


def _assert_file_tool_records(expected: dict[str, Any]) -> None:
    if _file_tool_records() != expected:
        raise RunnerError("runner tool provenance drifted during execution")


def _execution_paths(spec: ExecutionSpec) -> tuple[tuple[str, str, int, int], ...]:
    if not spec.stage.is_absolute():
        raise RunnerError("stage must be an absolute real directory")
    try:
        info = spec.stage.lstat()
        canonical = spec.stage.resolve(strict=True)
    except OSError as error:
        raise RunnerError("stage must be an absolute real directory") from error
    if not stat.S_ISDIR(info.st_mode) or spec.stage.is_symlink() or canonical != spec.stage:
        raise RunnerError("stage must be an absolute real directory")
    initial_fingerprint = _stage_fingerprint(spec.stage)
    if sum(record[2] for record in initial_fingerprint) > STAGE_LIMIT:
        raise RunnerError("initial stage byte quota exceeded")
    if spec.stdout_log == spec.stderr_log:
        raise RunnerError("stdout and stderr logs must be distinct")
    for path, label in ((spec.stdout_log, "stdout log"), (spec.stderr_log, "stderr log")):
        if not path.is_absolute() or path.exists() or path.is_symlink():
            raise RunnerError(f"{label} must be an absolute nonexistent path")
        parent = path.parent.resolve(strict=True)
        if parent != path.parent or not parent.is_dir():
            raise RunnerError(f"{label} parent must be a real directory")
        if path == spec.stage or spec.stage in path.parents:
            raise RunnerError(f"{label} must be outside the writable stage")
    return initial_fingerprint


def execute_isolated(spec: ExecutionSpec) -> dict[str, Any]:
    """Execute canonical Codex in isolation, leaving caller-owned stage and logs in place."""

    if not isinstance(spec, ExecutionSpec):
        raise RunnerError("execute_isolated requires an ExecutionSpec")
    initial_fingerprint = _execution_paths(spec)
    model = _validate_model(spec.model)
    reasoning_effort = _validate_reasoning_effort(spec.reasoning_effort)
    skill_references = _validated_skill_reference_records(spec.skill_references)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", spec.skill_name):
        raise RunnerError("skill name must be a bounded identifier")
    if type(spec.hard_seconds) is not int or not 1 <= spec.hard_seconds <= 14_400:
        raise RunnerError("hard timeout must be within 1..14400 seconds")
    if spec.inactivity_seconds is not None and (
        type(spec.inactivity_seconds) is not int
        or not 1 <= spec.inactivity_seconds <= spec.hard_seconds
    ):
        raise RunnerError("inactivity timeout must be within 1..hard timeout seconds")
    prompt_bytes = spec.prompt.encode("utf-8")
    if not prompt_bytes or len(prompt_bytes) > 1024 * 1024 or "\x00" in spec.prompt:
        raise RunnerError("prompt must be bounded UTF-8 text without NUL")

    tool_before = _file_tool_records()
    isolation: Path | None = None
    try:
        isolation, environment, codex, provenance = _isolated_environment(spec.skill_source, spec.skill_name)
        installed_skill = Path(environment["CODEX_HOME"]) / "skills" / spec.skill_name
        installed_before = _tree_summary(_tree_records(installed_skill), spec.skill_name)
        _assert_skill_reference_records(provenance["skill"], skill_references)
        _assert_skill_reference_records(installed_before, skill_references)
        _assert_skill_reference_files(spec.skill_source, skill_references)
        _assert_skill_reference_files(installed_skill, skill_references)
        shell_path = json.dumps(environment["PATH"])
        shell_home = json.dumps(str(spec.stage))
        command = [
            str(codex),
            "exec",
            "--model",
            model,
            "--cd",
            str(spec.stage),
            "--skip-git-repo-check",
            "--ephemeral",
            "--disable",
            "apps",
            "--disable",
            "multi_agent",
            "--disable",
            "browser_use",
            "--disable",
            "computer_use",
            "--disable",
            "image_generation",
            "--disable",
            "plugins",
            "--disable",
            "skill_mcp_dependency_install",
            "--disable",
            "tool_call_mcp_elicitation",
            "--disable",
            "tool_suggest",
            "--ignore-user-config",
            "--ignore-rules",
            "--strict-config",
            "-c",
            'approval_policy="never"',
            "-c",
            'default_permissions="workspace"',
            "-c",
            'permissions.workspace.filesystem={":minimal"="read",":workspace_roots"={"."="write"}}',
            "-c",
            "permissions.workspace.network={enabled=false}",
            "-c",
            'shell_environment_policy.inherit="none"',
            "-c",
            f"shell_environment_policy.set={{PATH={shell_path},HOME={shell_home}}}",
            "-c",
            'model_reasoning_summary="none"',
        ]
        if reasoning_effort is not None:
            command.extend(("-c", f'model_reasoning_effort="{reasoning_effort}"'))
        command.extend([
            "--color",
            "never",
            "--json",
            "-",
        ])
        exit_code, reason, progress_events, stdout_data, stderr_data = _run_codex(
            command,
            spec.prompt,
            environment,
            spec.stage,
            spec.stdout_log,
            spec.stderr_log,
            spec.hard_seconds,
            spec.inactivity_seconds,
            initial_fingerprint,
        )
        if len(stdout_data) + len(stderr_data) > LOG_LIMIT:
            raise RunnerError("generation log quota exceeded")
        observed = _validate_trace_bytes(
            stdout_data,
            spec.stage,
            require_terminal=reason == "completed" and exit_code == 0,
        )
        if _codex_record(codex, environment) != provenance["codex"]:
            raise RunnerError("Codex CLI provenance drifted during execution")
        source_after = _tree_summary(_tree_records(spec.skill_source), spec.skill_name)
        installed_after = _tree_summary(_tree_records(installed_skill), spec.skill_name)
        if source_after != provenance["skill"] or installed_after != provenance["skill"]:
            raise RunnerError("skill snapshot provenance drifted during execution")
        _assert_skill_reference_records(source_after, skill_references)
        _assert_skill_reference_records(installed_after, skill_references)
        _assert_skill_reference_files(spec.skill_source, skill_references)
        _assert_skill_reference_files(installed_skill, skill_references)
        _assert_file_tool_records(tool_before)
        model_record = {
            "requested_identifier": model,
            "resolution_status": "not_observed",
            "resolved_backend_snapshot": None,
        }
        if reasoning_effort is not None:
            model_record["requested_reasoning_effort"] = reasoning_effort
        return {
            "model": model_record,
            "prompt": {"bytes": len(prompt_bytes), "sha256": _digest_bytes(prompt_bytes)},
            "skill_snapshot": provenance["skill"],
            "skill_references": _skill_reference_summary(skill_references),
            "configured_isolation": {
                "ephemeral_codex_home": True,
                "first_party_chatgpt_login_required": True,
                "workspace_write": True,
                "sandbox_network": False,
                "apps_plugins_mcp": False,
                "browser_computer_image": False,
                "subagents": False,
                "shell_tool_available": True,
                "shell_commands_allowed_by_contract": False,
                "shell_command_prevention": False,
                "shell_command_acceptance": "inert_noop_only_other_commands_post_trace_rejection",
                "filesystem_profile": "minimal-read-workspace-write",
                "process_environment_inheritance": "none",
            },
            "trace_observed": observed,
            "execution": {
                "exit_code": exit_code,
                "reason": reason,
                "hard_timeout_seconds": spec.hard_seconds,
                "inactivity_timeout_seconds": spec.inactivity_seconds,
                "progress_events": progress_events,
                "initial_stage": {
                    "entry_count": len(initial_fingerprint),
                    "bytes": sum(record[2] for record in initial_fingerprint),
                    "fingerprint_sha256": _digest_bytes(
                        json.dumps(initial_fingerprint, separators=(",", ":")).encode("utf-8")
                    ),
                },
                "trace": {
                    "bytes": len(stdout_data),
                    "sha256": _digest_bytes(stdout_data),
                },
                "stderr": {
                    "bytes": len(stderr_data),
                    "sha256": _digest_bytes(stderr_data),
                },
            },
            "tools": {"codex": provenance["codex"], **tool_before},
        }
    finally:
        if isolation is not None:
            shutil.rmtree(isolation, ignore_errors=True)
