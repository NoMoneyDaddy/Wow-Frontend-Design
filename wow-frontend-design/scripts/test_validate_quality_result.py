#!/usr/bin/env python3
"""Tests for validate_quality_result.py."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_quality_result


class QualityResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parent
        cls.example_path = cls.root / "quality_result.example.json"
        cls.example = json.loads(cls.example_path.read_text(encoding="utf-8"))

    def test_repository_example_is_valid(self) -> None:
        self.assertEqual(validate_quality_result.validate(self.example_path), 2)

    def test_required_failure_makes_eligible_false_and_total_null(self) -> None:
        result = copy.deepcopy(self.example)
        result["hard_gates"][0]["status"] = "FAIL"
        result["hard_gates"][0]["evidence"] = ["failure.json"]
        result["eligible"] = False
        result["coverage"]["required_passed"] = 1
        result["release"] = "PARTIALLY_VERIFIED"
        self.assertEqual(validate_quality_result.validate_data(result), 2)

    def test_ineligible_result_cannot_claim_verified(self) -> None:
        result = copy.deepcopy(self.example)
        result["hard_gates"][0]["status"] = "UNVERIFIED"
        result["hard_gates"][0]["evidence"] = []
        result["eligible"] = False
        result["coverage"]["required_passed"] = 1
        result["coverage"]["evidence_items"] = 2
        with self.assertRaisesRegex(validate_quality_result.QualityResultError, "release cannot"):
            validate_quality_result.validate_data(result)

    def test_weighted_total_is_rejected(self) -> None:
        result = copy.deepcopy(self.example)
        result["weighted_total"] = 94
        with self.assertRaisesRegex(validate_quality_result.QualityResultError, "weighted_total"):
            validate_quality_result.validate_data(result)

    def test_builder_cannot_self_certify_craft(self) -> None:
        result = copy.deepcopy(self.example)
        result["craft"]["independent"] = False
        result["craft"]["evaluator_id"] = ""
        with self.assertRaisesRegex(validate_quality_result.QualityResultError, "independent evaluator"):
            validate_quality_result.validate_data(result)

    def test_unverified_rendering_requires_reason(self) -> None:
        result = copy.deepcopy(self.example)
        result["handoff"]["rendered_evidence"] = {
            "status": "UNVERIFIED",
            "paths": [],
            "reason": "",
        }
        with self.assertRaisesRegex(validate_quality_result.QualityResultError, "requires a reason"):
            validate_quality_result.validate_data(result)

    def test_symlink_and_oversized_input_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real.json"
            real.write_text("{}", encoding="utf-8")
            linked = root / "linked.json"
            linked.symlink_to(real)
            with self.assertRaises(validate_quality_result.QualityResultError):
                validate_quality_result.validate(linked)
            oversized = root / "oversized.json"
            oversized.write_bytes(b" " * (validate_quality_result.MAX_INPUT_BYTES + 1))
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "size limit"):
                validate_quality_result.validate(oversized)


if __name__ == "__main__":
    unittest.main()
