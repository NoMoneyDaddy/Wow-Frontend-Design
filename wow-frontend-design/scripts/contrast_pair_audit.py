#!/usr/bin/env python3
"""Audit evaluator-declared opaque sRGB color pairs against WCAG 2.x ratios."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


HEX_COLOR = re.compile(r"^#(?P<value>[0-9a-fA-F]{6})$")
PAIR_KINDS = {"normal-text", "large-text", "non-text", "custom"}


class ContrastManifestError(ValueError):
    """Raised when the evaluator-owned pair manifest is malformed."""


def _channel(value: int) -> float:
    encoded = value / 255
    return encoded / 12.92 if encoded <= 0.04045 else ((encoded + 0.055) / 1.055) ** 2.4


def luminance(color: str) -> float:
    match = HEX_COLOR.fullmatch(color)
    if not match:
        raise ContrastManifestError(f"expected opaque #RRGGBB sRGB color, got {color!r}")
    raw = match.group("value")
    red, green, blue = (_channel(int(raw[index : index + 2], 16)) for index in (0, 2, 4))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> float:
    lighter, darker = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def _nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContrastManifestError(f"{field} must be a non-empty string")
    return value.strip()


def audit(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContrastManifestError(f"cannot read manifest: {error}") from error

    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ContrastManifestError("schema_version must equal 1")
    pairs = payload.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        raise ContrastManifestError("pairs must be a non-empty array")

    findings: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for index, pair in enumerate(pairs):
        prefix = f"pairs[{index}]"
        if not isinstance(pair, dict):
            raise ContrastManifestError(f"{prefix} must be an object")
        identifier = _nonempty(pair.get("id"), f"{prefix}.id")
        if identifier in identifiers:
            raise ContrastManifestError(f"duplicate pair id: {identifier}")
        identifiers.add(identifier)
        appearance = _nonempty(pair.get("appearance"), f"{prefix}.appearance")
        kind = _nonempty(pair.get("kind"), f"{prefix}.kind")
        if kind not in PAIR_KINDS:
            raise ContrastManifestError(f"{prefix}.kind must be one of {sorted(PAIR_KINDS)}")
        foreground = _nonempty(pair.get("foreground"), f"{prefix}.foreground")
        background = _nonempty(pair.get("background"), f"{prefix}.background")
        required = pair.get("required_ratio")
        if isinstance(required, bool) or not isinstance(required, (int, float)):
            raise ContrastManifestError(f"{prefix}.required_ratio must be a finite number")
        required = float(required)
        if not math.isfinite(required) or not 1 <= required <= 21:
            raise ContrastManifestError(f"{prefix}.required_ratio must be between 1 and 21")

        ratio = contrast_ratio(foreground, background)
        result = {
            "id": identifier,
            "appearance": appearance,
            "kind": kind,
            "foreground": foreground.lower(),
            "background": background.lower(),
            "required_ratio": required,
            "actual_ratio": round(ratio, 3),
            "passed": ratio + 1e-9 >= required,
        }
        findings.append(result)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit declared opaque sRGB token pairs; this is not rendered contrast or WCAG conformance."
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    try:
        results = audit(args.manifest)
    except ContrastManifestError as error:
        print(f"contrast manifest invalid: {error}", file=sys.stderr)
        return 2

    failed = [result for result in results if not result["passed"]]
    if args.as_json:
        print(json.dumps({"scope": "opaque-srgb-token-pairs", "results": results}, ensure_ascii=False))
    else:
        for result in results:
            status = "PASS" if result["passed"] else "FAIL"
            print(
                f"{status} {result['id']} [{result['appearance']}] "
                f"{result['actual_ratio']:.3f}:1 required {result['required_ratio']:.3f}:1"
            )
        print(f"audited={len(results)} failed={len(failed)} scope=opaque-srgb-token-pairs")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
