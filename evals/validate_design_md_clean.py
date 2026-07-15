#!/usr/bin/env python3
"""Require DESIGN.md to pass the pinned official linter without findings."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PACKAGE = "@google/design.md"
VERSION = "0.2.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("design", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    args = parser.parse_args()
    if not 5 <= args.timeout_seconds <= 300:
        parser.error("--timeout-seconds must be within 5..300")
    return args


def clean_summary(payload: Any) -> tuple[int, int, int]:
    if not isinstance(payload, dict) or not isinstance(payload.get("summary"), dict):
        raise ValueError("official linter returned no summary")
    summary = payload["summary"]
    values = tuple(summary.get(name) for name in ("errors", "warnings", "infos"))
    if any(type(value) is not int or value < 0 for value in values):
        raise ValueError("official linter returned a malformed summary")
    return values  # type: ignore[return-value]


def main() -> int:
    args = parse_args()
    raw_design = args.design.expanduser()
    if raw_design.is_symlink():
        print(f"DESIGN.md clean gate infrastructure failure: unsafe file: {raw_design}", file=sys.stderr)
        return 2
    design = raw_design.resolve()
    if not design.is_file():
        print(f"DESIGN.md clean gate infrastructure failure: missing file: {design}", file=sys.stderr)
        return 2
    try:
        completed = subprocess.run(
            ["npx", "--yes", f"{PACKAGE}@{VERSION}", "lint", str(design)],
            cwd=design.parent,
            text=True,
            capture_output=True,
            timeout=args.timeout_seconds,
            check=False,
        )
        payload = json.loads(completed.stdout)
        errors, warnings, infos = clean_summary(payload)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError) as error:
        print(f"DESIGN.md clean gate infrastructure failure: {error}", file=sys.stderr)
        return 2
    if completed.returncode not in (0, 1):
        diagnostic = " ".join((completed.stderr or "official linter failed").split())[:500]
        print(f"DESIGN.md clean gate infrastructure failure: {diagnostic}", file=sys.stderr)
        return 2
    if errors or warnings:
        print(
            f"DESIGN.md clean gate rejected findings: errors={errors}, warnings={warnings}, infos={infos}",
            file=sys.stderr,
        )
        findings = payload.get("findings")
        if isinstance(findings, list):
            for finding in findings[:10]:
                if isinstance(finding, dict) and isinstance(finding.get("message"), str):
                    print("- " + " ".join(finding["message"].split())[:300], file=sys.stderr)
        return 1
    print(f"DESIGN.md clean gate passed: errors=0, warnings=0, infos={infos}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
