#!/usr/bin/env python3
"""Emit a privacy-bounded runtime profile without probing network or commands."""

from __future__ import annotations

import argparse
import json
import locale
import platform
import re
import sys
from datetime import datetime, timezone
from typing import Any, Sequence


DECLARATION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+:/-]{0,63}")
ENVIRONMENT_KINDS = {"local", "ci", "remote", "sandbox", "unknown"}
CAPABILITY_STATES = {"available", "unavailable", "not_checked"}
UNKNOWN = "not_reported"


class RuntimeProfileError(ValueError):
    """Raised when caller-owned provenance declarations are malformed."""


def _bounded(value: Any, label: str, maximum: int = 128) -> str:
    if not isinstance(value, str):
        raise RuntimeProfileError(f"{label} must be a string")
    normalized = value.strip()
    if not normalized or len(normalized) > maximum or not normalized.isprintable():
        raise RuntimeProfileError(f"{label} must be printable and contain 1..{maximum} characters")
    return normalized


def _declaration(value: str, label: str) -> str:
    if value == UNKNOWN:
        return value
    if DECLARATION.fullmatch(value) is None:
        raise RuntimeProfileError(f"{label} must be a bounded identifier, version or recorded alias")
    return value


def _captured_at(value: str | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RuntimeProfileError("captured_at must be an ISO-8601 UTC timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise RuntimeProfileError("captured_at must be an ISO-8601 UTC timestamp")
    canonical = parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if canonical != value:
        raise RuntimeProfileError("captured_at must be canonical seconds-precision UTC")
    return canonical


def build_profile(args: argparse.Namespace) -> dict[str, Any]:
    if args.environment_kind not in ENVIRONMENT_KINDS:
        raise RuntimeProfileError("environment_kind is invalid")
    for label in ("network", "browser", "screenshots"):
        if getattr(args, label) not in CAPABILITY_STATES:
            raise RuntimeProfileError(f"{label} capability state is invalid")

    local_now = datetime.now().astimezone()
    timezone_name = local_now.tzname() or UNKNOWN
    raw_offset = local_now.strftime("%z")
    timezone_offset = f"{raw_offset[:3]}:{raw_offset[3:]}" if len(raw_offset) == 5 else UNKNOWN
    return {
        "schema_version": 1,
        "captured_at": _captured_at(args.captured_at),
        "captured_at_source": "caller" if args.captured_at is not None else "system_clock",
        "host": {
            "system": _bounded(platform.system() or UNKNOWN, "host.system"),
            "release": _bounded(platform.release() or UNKNOWN, "host.release"),
            "machine": _bounded(platform.machine() or UNKNOWN, "host.machine"),
            "python_implementation": _bounded(platform.python_implementation(), "host.python_implementation"),
            "python_version": _bounded(platform.python_version(), "host.python_version"),
            "filesystem_encoding": _bounded(sys.getfilesystemencoding(), "host.filesystem_encoding"),
            "locale_encoding": _bounded(locale.getpreferredencoding(False), "host.locale_encoding"),
            "timezone": _bounded(timezone_name, "host.timezone"),
            "timezone_offset": _bounded(timezone_offset, "host.timezone_offset"),
        },
        "caller_declarations": {
            "environment_kind": args.environment_kind,
            "shell_name": _declaration(args.shell_name, "shell_name"),
            "node_version": _declaration(args.node_version, "node_version"),
            "browser_engine": _declaration(args.browser_engine, "browser_engine"),
            "browser_version": _declaration(args.browser_version, "browser_version"),
            "font_profile_id": _declaration(args.font_profile_id, "font_profile_id"),
        },
        "capabilities": {
            "network": args.network,
            "browser": args.browser,
            "screenshots": args.screenshots,
        },
        "evidence_boundary": "Caller declarations are recorded, not probed. No hostname, username, home path, IP address, environment dump, command execution, network request or font enumeration is included.",
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--environment-kind", choices=sorted(ENVIRONMENT_KINDS), default="unknown")
    result.add_argument("--shell-name", default=UNKNOWN)
    result.add_argument("--node-version", default=UNKNOWN)
    result.add_argument("--browser-engine", default=UNKNOWN)
    result.add_argument("--browser-version", default=UNKNOWN)
    result.add_argument("--font-profile-id", default=UNKNOWN)
    result.add_argument("--network", choices=sorted(CAPABILITY_STATES), default="not_checked")
    result.add_argument("--browser", choices=sorted(CAPABILITY_STATES), default="not_checked")
    result.add_argument("--screenshots", choices=sorted(CAPABILITY_STATES), default="not_checked")
    result.add_argument("--captured-at")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        profile = build_profile(args)
    except RuntimeProfileError as error:
        print(f"runtime profile invalid: {error}", file=sys.stderr)
        return 1
    print(json.dumps(profile, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
