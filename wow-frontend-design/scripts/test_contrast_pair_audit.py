#!/usr/bin/env python3
"""Tests for contrast_pair_audit.py."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import contrast_pair_audit


class ContrastPairAuditTests(unittest.TestCase):
    def write_manifest(self, root: Path, pairs: list[dict[str, object]]) -> Path:
        path = root / "pairs.json"
        path.write_text(json.dumps({"schema_version": 1, "pairs": pairs}), encoding="utf-8")
        return path

    def test_pass_and_fail_are_calculated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_manifest(
                Path(directory),
                [
                    {
                        "id": "black-white",
                        "appearance": "light",
                        "kind": "normal-text",
                        "foreground": "#000000",
                        "background": "#ffffff",
                        "required_ratio": 4.5,
                    },
                    {
                        "id": "gray-white",
                        "appearance": "light",
                        "kind": "normal-text",
                        "foreground": "#aaaaaa",
                        "background": "#ffffff",
                        "required_ratio": 4.5,
                    },
                ],
            )
            results = contrast_pair_audit.audit(path)
            self.assertTrue(results[0]["passed"])
            self.assertFalse(results[1]["passed"])

    def test_rejects_alpha_and_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_manifest(
                Path(directory),
                [
                    {
                        "id": "same",
                        "appearance": "light",
                        "kind": "non-text",
                        "foreground": "#00000080",
                        "background": "#ffffff",
                        "required_ratio": 3,
                    }
                ],
            )
            with self.assertRaises(contrast_pair_audit.ContrastManifestError):
                contrast_pair_audit.audit(path)

            path = self.write_manifest(
                Path(directory),
                [
                    {
                        "id": "same",
                        "appearance": "light",
                        "kind": "non-text",
                        "foreground": "#000000",
                        "background": "#ffffff",
                        "required_ratio": 3,
                    },
                    {
                        "id": "same",
                        "appearance": "dark",
                        "kind": "non-text",
                        "foreground": "#ffffff",
                        "background": "#000000",
                        "required_ratio": 3,
                    },
                ],
            )
            with self.assertRaises(contrast_pair_audit.ContrastManifestError):
                contrast_pair_audit.audit(path)


if __name__ == "__main__":
    unittest.main()
