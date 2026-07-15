#!/usr/bin/env python3
"""Unit tests for the pinned DESIGN.md clean gate."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "evals" / "validate_design_md_clean.py"
SPEC = importlib.util.spec_from_file_location("validate_design_md_clean", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class DesignMdCleanGateTests(unittest.TestCase):
    def test_accepts_integer_summary(self) -> None:
        self.assertEqual((0, 0, 1), validator.clean_summary({"summary": {"errors": 0, "warnings": 0, "infos": 1}}))

    def test_rejects_bool_or_missing_summary_values(self) -> None:
        for payload in (
            {"summary": {"errors": False, "warnings": 0, "infos": 0}},
            {"summary": {"errors": 0, "warnings": 0}},
            {},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                validator.clean_summary(payload)


if __name__ == "__main__":
    unittest.main()
