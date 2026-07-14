#!/usr/bin/env python3
"""Tests for validate_product_cases.py."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_product_cases


class ProductCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = Path(__file__).resolve().parents[2] / "evals" / "product_cases.json"
        cls.data = json.loads(cls.fixture.read_text(encoding="utf-8"))

    def validate_copy(self, data: dict[str, object]) -> int:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "product_cases.json"
            fixture.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return validate_product_cases.validate(fixture)

    def test_repository_fixture_is_valid_definition_only_coverage(self) -> None:
        self.assertEqual(validate_product_cases.validate(self.fixture), 8)
        self.assertIs(self.data["model_results_included"], False)
        self.assertEqual({case["locale"] for case in self.data["cases"]}, {"zh-Hant", "en"})

    def test_result_claim_is_rejected(self) -> None:
        data = deepcopy(self.data)
        data["model_results_included"] = True
        with self.assertRaises(validate_product_cases.ProductCaseError):
            self.validate_copy(data)

    def test_fixed_case_id_change_is_rejected(self) -> None:
        data = deepcopy(self.data)
        data["cases"][0]["case_id"] = "renamed-audit-case"
        with self.assertRaises(validate_product_cases.ProductCaseError):
            self.validate_copy(data)

    def test_missing_locale_distribution_is_rejected(self) -> None:
        data = deepcopy(self.data)
        for case in data["cases"]:
            case["locale"] = "en"
        with self.assertRaises(validate_product_cases.ProductCaseError):
            self.validate_copy(data)


if __name__ == "__main__":
    unittest.main()
