#!/usr/bin/env python3
"""Validate evaluator-packaged visual samples without judging their design."""

from __future__ import annotations

import sys
from pathlib import Path


EXPECTED_BY_CASE = {
    "showcase": ("index.html",),
    "product-dashboard": ("index.html",),
    "product-dashboard-remake": ("index.html",),
    "harbor-cold-chain-v4": ("DESIGN.md", "index.html"),
    "island-sound-archive-v4": ("DESIGN.md", "index.html"),
    "plant-swap-one-line-v4": ("DESIGN.md", "index.html", "browse.html", "listing.html"),
}


def validate(case_id: str, root: Path) -> list[str]:
    expected = EXPECTED_BY_CASE.get(case_id)
    if expected is None:
        return [f"unsupported case: {case_id}"]
    if root.is_symlink() or not root.is_dir():
        return ["output root must be a real directory"]

    issues: list[str] = []
    entries = tuple(sorted(path.name for path in root.iterdir()))
    if entries != tuple(sorted(expected)):
        issues.append(f"output set must be exactly: {', '.join(expected)}")

    for name in expected:
        path = root / name
        if path.is_symlink() or not path.is_file():
            issues.append(f"{name}: missing, non-file, or symlink")
            continue
        size = path.stat().st_size
        if not 1 <= size <= 1_048_576:
            issues.append(f"{name}: size outside 1..1048576 bytes")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            issues.append(f"{name}: invalid strict UTF-8: {error}")
            continue
        if "\x00" in text:
            issues.append(f"{name}: NUL byte is forbidden")
    return issues


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: validate_visual_web_output.py CASE_ID OUTPUT_DIRECTORY", file=sys.stderr)
        return 2
    issues = validate(sys.argv[1], Path(sys.argv[2]))
    for issue in issues:
        print(issue, file=sys.stderr)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
