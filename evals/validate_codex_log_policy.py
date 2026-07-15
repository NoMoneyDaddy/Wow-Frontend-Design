#!/usr/bin/env python3
"""Reject Codex evaluation traces that use disallowed host or network tooling."""

from __future__ import annotations

import argparse
import json
import re
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
    "pnpm",
    "rsync",
    "scp",
    "ssh",
    "wget",
    "yarn",
)
FORBIDDEN_ITEM_TYPES = {"mcp_tool_call", "web_search"}
OUTSIDE_TEMP_PREFIXES = ("/private/tmp", "/private/var/folders", "/tmp", "/var/folders")


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


def _forbidden_executable(command: str) -> str | None:
    names = "|".join(re.escape(name) for name in FORBIDDEN_EXECUTABLES)
    scrubbed = re.sub(rf"\b(?:command\s+-v|which)\s+(?:{names})\b", "", command)
    match = re.search(rf"(?<![A-Za-z0-9_.-])({names})(?![A-Za-z0-9_.-])", scrubbed)
    return match.group(1) if match else None


def validate(path: Path, stage: Path) -> int:
    stage = stage.resolve()
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
        command = item.get("command")
        if not isinstance(command, str) or not command:
            raise PolicyError("command_execution has no command")
        checked_commands += 1
        executable = _forbidden_executable(command)
        if executable is not None:
            raise PolicyError(f"forbidden executable in trace: {executable}")
        for prefix in OUTSIDE_TEMP_PREFIXES:
            if prefix in command and str(stage) not in command:
                raise PolicyError(f"command referenced evaluator-external temporary storage: {prefix}")
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
