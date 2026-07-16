#!/usr/bin/env python3
"""Tests for validate_platform_support.py."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_platform_support


class PlatformSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.matrix_path = self.root / "evals" / "platform-support.json"
        self.matrix = json.loads(self.matrix_path.read_text(encoding="utf-8"))

    def _write_matrix(self, data: dict[str, object], directory: str) -> Path:
        path = Path(directory) / "platform-support.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_repository_snapshot_is_valid(self) -> None:
        self.assertEqual(validate_platform_support.validate(self.matrix_path, self.root), (32, 20))

    def test_scheduled_recheck_field_is_rejected(self) -> None:
        data = copy.deepcopy(self.matrix)
        data["next_review_at"] = "2027-01-01"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(validate_platform_support.PlatformSupportError, "scheduled recheck"):
                validate_platform_support.validate(self._write_matrix(data, directory), self.root)

    def test_unknown_source_binding_is_rejected(self) -> None:
        data = copy.deepcopy(self.matrix)
        data["targets"][0]["source_ids"] = ["invented-source"]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(validate_platform_support.PlatformSupportError, "unknown ids"):
                validate_platform_support.validate(self._write_matrix(data, directory), self.root)

    def test_non_string_status_is_rejected_without_crashing(self) -> None:
        data = copy.deepcopy(self.matrix)
        data["targets"][0]["official_status"] = {"value": "supported"}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(validate_platform_support.PlatformSupportError, "official_status"):
                validate_platform_support.validate(self._write_matrix(data, directory), self.root)

    def test_observed_status_requires_matching_stage_evidence(self) -> None:
        data = copy.deepcopy(self.matrix)
        data["targets"][0]["checks"]["visual"] = "not_run"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(validate_platform_support.PlatformSupportError, "requires passed"):
                validate_platform_support.validate(self._write_matrix(data, directory), self.root)

    def test_artifact_escape_is_rejected(self) -> None:
        data = copy.deepcopy(self.matrix)
        data["targets"][0]["artifacts"] = ["../outside"]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(validate_platform_support.PlatformSupportError, "unsafe"):
                validate_platform_support.validate(self._write_matrix(data, directory), self.root)

    def test_required_target_cannot_be_omitted(self) -> None:
        data = copy.deepcopy(self.matrix)
        data["targets"] = data["targets"][:-1]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(validate_platform_support.PlatformSupportError, "inventory drift"):
                validate_platform_support.validate(self._write_matrix(data, directory), self.root)


if __name__ == "__main__":
    unittest.main()
