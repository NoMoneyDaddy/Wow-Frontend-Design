#!/usr/bin/env python3
"""Reject Codex evaluation traces that use disallowed host or network tooling."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Iterator


FORBIDDEN_EXECUTABLES = (
    "bun",
    "bunx",
    "curl",
    "git",
    "npm",
    "npx",
    "osascript",
    "pnpm",
    "rsync",
    "safaridriver",
    "scp",
    "ssh",
    "swift",
    "swiftc",
    "wget",
    "xcrun",
    "yarn",
)
FORBIDDEN_ITEM_TYPES = {
    "browser_tool_call",
    "collab_tool_call",
    "computer_tool_call",
    "mcp_tool_call",
    "web_search",
}
FORBIDDEN_CREDENTIAL_PATTERNS = (
    ("Codex authentication state", re.compile(r"(?i)(?:\$\{?CODEX_HOME\}?|auth\.json)")),
    ("process environment enumeration", re.compile(r"(?i)(?<![A-Za-z0-9_.-])(?:/usr/bin/)?(?:printenv|env)(?=\s|$|[;&|>])")),
    ("process environment enumeration", re.compile(r"(?i)(?:os\.environ|/proc/(?:self|[0-9]+)/environ)")),
    ("credential store access", re.compile(r"(?i)(?:\.aws/credentials|\.npmrc|\.netrc|\.ssh/|\.config/gh/|security\s+find-(?:generic|internet)-password)")),
)
TEMP_PATH = re.compile(
    r"(?<![A-Za-z0-9_.-])(?P<path>/(?:private/)?(?:tmp|var/folders)(?:/[^\s'\"`|;&<>()\[\]{}]*)?)"
)


class PolicyError(ValueError):
    """Raised when the Codex trace violates the controlled-run contract."""


def _events(path: Path) -> Iterator[dict[str, Any]]:
    if not path.is_file() or path.is_symlink():
        raise PolicyError(f"trace is missing or unsafe: {path}")
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise PolicyError(f"trace line {line_number} is not JSON: {error}") from error
        if not isinstance(event, dict):
            raise PolicyError(f"trace line {line_number} is not an object")
        yield event


def _canonical_command(command: str) -> str:
    if re.search(r"[$*?\[\]{}]", command) or "`" in command:
        raise PolicyError("shell expansion is forbidden in controlled traces")
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as error:
        raise PolicyError(f"command has invalid shell quoting: {error}") from error
    if not tokens:
        raise PolicyError("command_execution has no parsed command")
    return " ".join(tokens).replace("'", "").replace('"', "")


def _forbidden_executable(command: str) -> str | None:
    names = "|".join(re.escape(name) for name in FORBIDDEN_EXECUTABLES)
    capability_probe = re.compile(
        rf"^(?:/bin/(?:ba|z)?sh\s+-l?c\s+)?(?:command\s+-v|which)\s+(?:{names})(?:\s+\|\|\s+true)?$"
    )
    if capability_probe.fullmatch(command):
        return None
    match = re.search(rf"(?<![A-Za-z0-9_.-])({names})(?![A-Za-z0-9_.-])", command)
    return match.group(1) if match else None


def _external_temp_path(command: str, stage: Path) -> str | None:
    """Return the first temporary path outside the evaluator-owned stage."""

    canonical_stage = stage.resolve(strict=False)
    for match in TEMP_PATH.finditer(command):
        raw_path = match.group("path").rstrip(",.:")
        candidate = Path(raw_path).resolve(strict=False)
        if candidate == canonical_stage or canonical_stage in candidate.parents:
            continue
        return raw_path
    return None


def _forbidden_credential_access(command: str) -> str | None:
    for label, pattern in FORBIDDEN_CREDENTIAL_PATTERNS:
        if pattern.search(command):
            return label
    return None


def validate(path: Path, stage: Path, *, allow_commands: bool = True) -> int:
    stage = stage.resolve(strict=False)
    checked_commands = 0
    for event in _events(path):
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type in FORBIDDEN_ITEM_TYPES:
            raise PolicyError(f"forbidden tool event: {item_type}")
        if item_type != "command_execution":
            continue
        if not allow_commands:
            raise PolicyError("command execution is forbidden in this controlled trace")
        command = item.get("command")
        if not isinstance(command, str) or not command:
            raise PolicyError("command_execution has no command")
        checked_commands += 1
        credential_access = _forbidden_credential_access(command)
        if credential_access is not None:
            raise PolicyError(f"forbidden credential access in trace: {credential_access}")
        canonical = _canonical_command(command)
        executable = _forbidden_executable(canonical)
        if executable is not None:
            raise PolicyError(f"forbidden executable in trace: {executable}")
        credential_access = _forbidden_credential_access(canonical)
        if credential_access is not None:
            raise PolicyError(f"forbidden credential access in trace: {credential_access}")
        external_temp = _external_temp_path(canonical, stage)
        if external_temp is not None:
            raise PolicyError(f"command referenced evaluator-external temporary storage: {external_temp}")
    return checked_commands


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--stage", required=True, type=Path)
    args = parser.parse_args()
    try:
        count = validate(args.trace, args.stage)
    except (OSError, UnicodeError, PolicyError) as error:
        print(f"Codex command policy rejected trace: {error}", file=sys.stderr)
        return 1
    print(f"Codex command policy passed: {count} command event(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
