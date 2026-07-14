#!/usr/bin/env python3
"""Tests for validate_trigger_cases.py."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_trigger_cases


class TriggerCaseTests(unittest.TestCase):
    def test_repository_fixture_is_valid(self) -> None:
        root = Path(__file__).resolve().parents[2]
        count = validate_trigger_cases.validate(
            root / "evals" / "trigger_cases.json",
            root / "wow-frontend-design" / "references",
        )
        self.assertEqual(count, 28)

    def test_negative_case_cannot_route_skill_references(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            references = root / "references"
            references.mkdir()
            (references / "quality-gates.md").write_text("# gate", encoding="utf-8")
            fixture = root / "cases.json"
            fixture.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "cases": [
                            {
                                "id": "wrong-route",
                                "locale": "en",
                                "prompt": "Write a backend-only database migration.",
                                "expected": "do_not_trigger",
                                "required_references": ["quality-gates.md"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(validate_trigger_cases.TriggerCaseError):
                validate_trigger_cases.validate(fixture, references)


if __name__ == "__main__":
    unittest.main()
