#!/usr/bin/env python3
"""Validate evaluator-owned Skill activation/reference-routing fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


EXPECTED = {"trigger", "do_not_trigger"}
CASE_KEYS = {"id", "locale", "prompt", "expected", "required_references"}


class TriggerCaseError(ValueError):
    """Raised when trigger fixtures are malformed or unsafe."""


def load_json(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise TriggerCaseError(f"refusing symlink fixture: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TriggerCaseError(f"cannot read valid JSON fixture: {error}") from error
    if not isinstance(value, dict):
        raise TriggerCaseError("fixture root must be an object")
    return value


def validate(path: Path, references_dir: Path) -> int:
    data = load_json(path)
    if data.get("schema_version") != 1:
        raise TriggerCaseError("schema_version must equal 1")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise TriggerCaseError("cases must be a non-empty array")

    ids: set[str] = set()
    outcomes: set[str] = set()
    locales: set[str] = set()
    for index, case in enumerate(cases):
        label = f"cases[{index}]"
        if not isinstance(case, dict) or set(case) != CASE_KEYS:
            raise TriggerCaseError(f"{label} must contain exactly {sorted(CASE_KEYS)}")

        case_id = case["id"]
        if not isinstance(case_id, str) or not case_id or case_id in ids:
            raise TriggerCaseError(f"{label}.id must be a unique non-empty string")
        ids.add(case_id)

        locale = case["locale"]
        prompt = case["prompt"]
        expected = case["expected"]
        references = case["required_references"]
        if not isinstance(locale, str) or not locale:
            raise TriggerCaseError(f"{label}.locale must be a non-empty string")
        if not isinstance(prompt, str) or len(prompt.strip()) < 12:
            raise TriggerCaseError(f"{label}.prompt is too short")
        if expected not in EXPECTED:
            raise TriggerCaseError(f"{label}.expected must be one of {sorted(EXPECTED)}")
        if not isinstance(references, list) or any(not isinstance(item, str) for item in references):
            raise TriggerCaseError(f"{label}.required_references must be an array of strings")
        if len(references) != len(set(references)):
            raise TriggerCaseError(f"{label}.required_references contains duplicates")
        if expected == "do_not_trigger" and references:
            raise TriggerCaseError(f"{label} must not route references when activation is rejected")
        if expected == "trigger" and not references:
            raise TriggerCaseError(f"{label} must route at least one reference")
        for reference in references:
            if Path(reference).name != reference or not reference.endswith(".md"):
                raise TriggerCaseError(f"{label} has unsafe reference name: {reference}")
            if not (references_dir / reference).is_file():
                raise TriggerCaseError(f"{label} routes missing reference: {reference}")
        outcomes.add(expected)
        locales.add(locale)

    if outcomes != EXPECTED:
        raise TriggerCaseError("fixture must include positive and negative activation cases")
    if not {"zh-Hant", "en"}.issubset(locales):
        raise TriggerCaseError("fixture must include zh-Hant and en cases")
    return len(cases)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--references", type=Path, required=True)
    args = parser.parse_args()
    try:
        count = validate(args.fixture.expanduser(), args.references.expanduser().resolve())
    except TriggerCaseError as error:
        print(f"trigger fixture invalid: {error}", file=sys.stderr)
        return 1
    print(f"trigger fixture valid: {count} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
