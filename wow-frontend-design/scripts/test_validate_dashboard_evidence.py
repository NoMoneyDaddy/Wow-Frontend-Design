#!/usr/bin/env python3
"""Tests for validate_dashboard_evidence.py."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_dashboard_evidence


class DashboardEvidenceTests(unittest.TestCase):
    def test_repository_dashboard_failures_are_integrity_bound(self) -> None:
        root = Path(__file__).resolve().parents[2]
        count = validate_dashboard_evidence.validate(root / "evals" / "dashboard-browser-results.json", root)
        self.assertEqual(2, count)

    def test_acceptance_exit_code_cannot_be_upgraded(self) -> None:
        root = Path(__file__).resolve().parents[2]
        data = json.loads((root / "evals" / "dashboard-browser-results.json").read_text(encoding="utf-8"))
        data["evaluator_replays"]["acceptance"]["exit_code"] = 0
        with tempfile.TemporaryDirectory() as directory:
            summary = Path(directory) / "summary.json"
            summary.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(validate_dashboard_evidence.DashboardEvidenceError, "exit code"):
                validate_dashboard_evidence.validate(summary, root)


if __name__ == "__main__":
    unittest.main()
