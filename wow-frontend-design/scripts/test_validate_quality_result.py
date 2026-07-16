#!/usr/bin/env python3
"""Tests for validate_quality_result.py."""

from __future__ import annotations

import copy
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_quality_result
import evidence_ledger


class QualityResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parent
        cls.example_path = cls.root / "quality_result.example.json"
        cls.example = json.loads(cls.example_path.read_text(encoding="utf-8"))

    def test_repository_example_is_valid(self) -> None:
        self.assertEqual(validate_quality_result.validate(self.example_path), 2)

    def _strict_fixture(self, root: Path) -> tuple[Path, Path, Path]:
        workspace = root / "workspace"
        workspace.mkdir()
        ledger = root / "ledger.json"
        self.assertEqual(
            evidence_ledger.main(
                ["init", "--ledger", str(ledger), "--case-id", "quality-case", "--run-id", "quality-run-001"]
            ),
            0,
        )
        result = copy.deepcopy(self.example)
        labels = ["primary-task", "rendered-mobile-layout", "novel-discovery"]
        result["hard_gates"].append(
            {
                "id": "novel-discovery",
                "required": True,
                "applicable": True,
                "status": "PASS",
                "evidence": [labels[2]],
                "reason": "",
            }
        )
        self.assertEqual(len(result["hard_gates"]), len(labels))
        for gate, label in zip(result["hard_gates"], labels):
            gate["evidence"] = [label]
        result["coverage"] = {
            "required_applicable": 3,
            "required_passed": 3,
            "evidence_items": 3,
        }
        for dimension in result["craft"]["dimensions"]:
            dimension["status"] = "UNVERIFIED"
            dimension["evidence"] = []
        result["handoff"]["rendered_evidence"] = {
            "status": "UNVERIFIED",
            "paths": [],
            "reason": "Strict unit fixture records command evidence only.",
        }
        result_path = workspace / "result.json"
        result_path.write_text(json.dumps(result), encoding="utf-8")
        for label in labels:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(
                    evidence_ledger.main(
                        [
                            "run",
                            "--ledger",
                            str(ledger),
                            "--label",
                            label,
                            "--cwd",
                            str(workspace),
                            "--",
                            sys.executable,
                            "-c",
                            "raise SystemExit(0)",
                        ]
                    ),
                    0,
                )
        return result_path, ledger, workspace

    def test_strict_validation_binds_passes_and_discovery_to_evaluator_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result, ledger, workspace = self._strict_fixture(Path(directory))
            self.assertEqual(
                validate_quality_result.validate_with_ledger(
                    result, ledger, workspace, ("novel-discovery",)
                ),
                3,
            )

    def test_strict_validation_uses_latest_repair_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result, ledger, workspace = self._strict_fixture(Path(directory))
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(
                    evidence_ledger.main(
                        [
                            "run",
                            "--ledger",
                            str(ledger),
                            "--label",
                            "primary-task",
                            "--cwd",
                            str(workspace),
                            "--",
                            sys.executable,
                            "-c",
                            "raise SystemExit(7)",
                        ]
                    ),
                    7,
                )
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "did not pass"):
                validate_quality_result.validate_with_ledger(
                    result, ledger, workspace, ("novel-discovery",)
                )

    def test_strict_validation_rejects_unbound_or_workspace_owned_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result, ledger, workspace = self._strict_fixture(root)
            data = json.loads(result.read_text(encoding="utf-8"))
            data["hard_gates"][0]["evidence"] = ["not-recorded"]
            result.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "one latest ledger event"):
                validate_quality_result.validate_with_ledger(
                    result, ledger, workspace, ("novel-discovery",)
                )
            forged = workspace / "ledger.json"
            forged.write_bytes(ledger.read_bytes())
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "outside"):
                validate_quality_result.validate_with_ledger(
                    result, forged, workspace, ("novel-discovery",)
                )

    def test_cli_requires_explicit_structure_only_or_bound_evidence(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(validate_quality_result.main([str(self.example_path)]), 1)
            self.assertEqual(
                validate_quality_result.main([str(self.example_path), "--structure-only"]),
                0,
            )

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
