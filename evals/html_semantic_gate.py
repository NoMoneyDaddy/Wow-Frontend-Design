#!/usr/bin/env python3
"""Run the pinned VNU validator and return a bounded, path-safe receipt."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VNU_RUNNER = ROOT / "evals" / "run_vnu.cjs"
LOCKFILE = ROOT / "package-lock.json"
VNU_PACKAGE_JSON = ROOT / "node_modules" / "vnu-jar" / "package.json"
MAX_FINDINGS_PER_OUTPUT = 16
MAX_MESSAGE_BYTES = 512
_FINDING = re.compile(
    r'^"file:(?P<path>.+?)":(?P<line>[0-9]+)\.(?P<column>[0-9]+)-'
    r'[0-9]+\.[0-9]+: (?P<level>error|warning): (?P<message>.+)$'
)


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_output_name(value: str) -> bool:
    path = PurePosixPath(value)
    return (
        value == path.as_posix()
        and not path.is_absolute()
        and all(part not in {"", ".", ".."} for part in path.parts)
        and value.casefold().endswith((".html", ".htm"))
    )


def _tool() -> dict[str, Any]:
    try:
        lock = json.loads(LOCKFILE.read_text(encoding="utf-8"))
        package = json.loads(VNU_PACKAGE_JSON.read_text(encoding="utf-8"))
        locked = lock.get("packages", {}).get("node_modules/vnu-jar", {})
        version = locked.get("version") if isinstance(locked, dict) else None
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise RuntimeError("semantic HTML validator infrastructure unavailable")
    if (
        not isinstance(version, str)
        or package.get("name") != "vnu-jar"
        or package.get("version") != version
        or not VNU_RUNNER.is_file()
    ):
        raise RuntimeError("semantic HTML validator infrastructure unavailable")
    return {
        "package": "vnu-jar",
        "version": version,
        "runner": "evals/run_vnu.cjs",
        "runner_sha256": _digest(VNU_RUNNER),
        "lockfile_sha256": _digest(LOCKFILE),
        "package_json_sha256": _digest(VNU_PACKAGE_JSON),
    }


def _unavailable(tool: dict[str, Any] | None, reason: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "unavailable",
        "claim_boundary": "semantic-html",
        "tool": tool or {"package": "vnu-jar", "version": None},
        "outputs": [],
        "finding_count": 0,
        "unavailable_reason": reason,
    }


def _normalize_path(raw: str, output_names: tuple[str, ...]) -> str | None:
    candidate = raw.replace("\\", "/")
    for name in output_names:
        if candidate == name or candidate.endswith("/" + name):
            return name
    return None


def _parse_findings(raw: str, output_names: tuple[str, ...]) -> dict[str, list[dict[str, Any]]]:
    findings = {name: [] for name in output_names}
    for line in raw.splitlines():
        match = _FINDING.match(line.strip())
        if match is None:
            continue
        path = _normalize_path(match.group("path"), output_names)
        if path is None:
            continue
        message = " ".join(match.group("message").split())
        if len(message.encode("utf-8")) > MAX_MESSAGE_BYTES:
            encoded = message.encode("utf-8")[:MAX_MESSAGE_BYTES]
            message = encoded.decode("utf-8", errors="ignore")
        if len(findings[path]) >= MAX_FINDINGS_PER_OUTPUT:
            continue
        findings[path].append(
            {
                "path": path,
                "line": int(match.group("line")),
                "column": int(match.group("column")),
                "level": match.group("level"),
                "message": message,
            }
        )
    return findings


def _run_process(command: list[str], stage: Path, timeout: int) -> tuple[int, str]:
    environment = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    for name in ("HOME", "TMPDIR"):
        if name in os.environ:
            environment[name] = os.environ[name]
    try:
        process = subprocess.Popen(
            command,
            cwd=stage,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as error:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate()
            raise RuntimeError("semantic HTML validator timed out") from error
    except OSError as error:
        raise RuntimeError("semantic HTML validator infrastructure unavailable") from error
    return process.returncode, f"{stdout}\n{stderr}"


def run_html_semantic_gate(stage: Path, outputs: tuple[str, ...], timeout: int) -> dict[str, Any]:
    """Validate only declared HTML outputs with the project-pinned VNU runner."""
    if not stage.is_dir() or stage.is_symlink():
        raise ValueError("semantic HTML stage must be a real directory")
    output_names = tuple(dict.fromkeys(outputs))
    if not output_names or any(not _safe_output_name(name) for name in output_names):
        raise ValueError("semantic HTML gate accepts HTML outputs only")
    try:
        tool = _tool()
        node = shutil.which("node")
        if node is None:
            return _unavailable(tool, "node unavailable")
        command = [node, str(VNU_RUNNER), *output_names]
        returncode, raw = _run_process(command, stage, max(1, timeout))
    except RuntimeError as error:
        return _unavailable(None, str(error))
    findings = _parse_findings(raw, output_names)
    total = sum(len(items) for items in findings.values())
    if returncode not in {0, 1}:
        return _unavailable(tool, "vnu runner preflight failed")
    if returncode == 1 and total == 0:
        return _unavailable(tool, "vnu emitted an unparseable finding")
    return {
        "schema_version": 1,
        "status": "rejected" if total else "passed",
        "claim_boundary": "semantic-html",
        "tool": tool,
        "outputs": [
            {
                "path": name,
                "status": "rejected" if findings[name] else "passed",
                "finding_count": len(findings[name]),
                "findings": findings[name],
            }
            for name in output_names
        ],
        "finding_count": total,
    }
