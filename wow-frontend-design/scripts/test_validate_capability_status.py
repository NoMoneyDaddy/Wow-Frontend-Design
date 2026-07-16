#!/usr/bin/env python3
"""Tests for validate_capability_status.py."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_capability_status


class CapabilityStatusTests(unittest.TestCase):
    def test_repository_status_is_valid(self) -> None:
        root = Path(__file__).resolve().parents[2]
        count = validate_capability_status.validate(root / "evals" / "capability-status.json", root)
        self.assertEqual(count, 19)

    def test_missing_or_escaping_artifact_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            status = root / "status.json"
            status.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "snapshot_at": "2026-07-14",
                        "semantics": "Evidence paths must exist and claims remain explicitly bounded.",
                        "capabilities": [
                            {
                                "id": "bad-path",
                                "status": "not_tested",
                                "claim": "This intentionally invalid capability has no safe artifact.",
                                "artifacts": ["../outside"],
                                "boundary": "This fixture must be rejected before any claim is accepted.",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(validate_capability_status.CapabilityStatusError):
                validate_capability_status.validate(status, root)

    def test_required_capability_cannot_be_silently_omitted(self) -> None:
        root = Path(__file__).resolve().parents[2]
        data = json.loads((root / "evals" / "capability-status.json").read_text(encoding="utf-8"))
        data["capabilities"] = [item for item in data["capabilities"] if item["id"] != "local-models"]
        with tempfile.TemporaryDirectory() as directory:
            status = Path(directory) / "status.json"
            status.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(validate_capability_status.CapabilityStatusError, "inventory drift"):
                validate_capability_status.validate(status, root)


if __name__ == "__main__":
    unittest.main()
