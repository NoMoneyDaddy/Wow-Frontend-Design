#!/usr/bin/env python3
"""Tests for the published Codex v4 evidence validator."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wow-frontend-design" / "scripts"))

import validate_product_flow_evidence


@unittest.skip("legacy screenshot evidence intentionally cleared; current evidence is validated by the v6 cohort")
class ProductFlowEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.visual = self.root / "evals" / "product-flow-v4-visual-results.json"
        self.generation = self.root / "evals" / "product-flow-v4-generation-results.json"

    @staticmethod
    def _write(data: dict[str, object], directory: str, name: str) -> Path:
        path = Path(directory) / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_repository_v4_evidence_is_integrity_bound(self) -> None:
        self.assertEqual(9, validate_product_flow_evidence.validate(self.visual, self.root))

    def test_stale_screenshot_hash_is_rejected(self) -> None:
        data = json.loads(self.visual.read_text(encoding="utf-8"))
        data["results"][0]["screenshotSha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(data, directory, "visual.json")
            with self.assertRaisesRegex(validate_product_flow_evidence.ProductFlowEvidenceError, "hash is stale"):
                validate_product_flow_evidence.validate(path, self.root)

    def test_generation_retry_history_cannot_be_hidden(self) -> None:
        data = json.loads(self.generation.read_text(encoding="utf-8"))
        retried = next(item for item in data["results"] if item["attempt_count"] > 1)
        retried["attempts"] = retried["attempts"][-1:]
        retried["attempt_count"] = 1
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(data, directory, "generation.json")
            with self.assertRaisesRegex(validate_product_flow_evidence.ProductFlowEvidenceError, "retry inventory"):
                validate_product_flow_evidence.validate(self.visual, self.root, generation_path=path)


if __name__ == "__main__":
    unittest.main()
