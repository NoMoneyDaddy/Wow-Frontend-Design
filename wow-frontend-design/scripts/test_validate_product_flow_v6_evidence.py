#!/usr/bin/env python3
"""Tests for the published Codex v6 evidence validator."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_product_flow_v6_evidence


class ProductFlowV6EvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.visual = self.root / "evals/product-flow-v6-visual-results.json"
        self.generation = self.root / "evals/product-flow-v6-repaired-v2-generation-results.json"

    @staticmethod
    def _write(data: dict[str, object], directory: str, name: str) -> Path:
        path = Path(directory) / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_repository_v6_evidence_is_integrity_bound(self) -> None:
        self.assertEqual(8, validate_product_flow_v6_evidence.validate(self.visual, self.root))

    def test_stale_screenshot_hash_is_rejected(self) -> None:
        data = json.loads(self.visual.read_text(encoding="utf-8"))
        data["results"][0]["screenshotSha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(data, directory, "visual.json")
            with self.assertRaisesRegex(validate_product_flow_v6_evidence.ProductFlowV6EvidenceError, "screenshot hash is stale"):
                validate_product_flow_v6_evidence.validate(path, self.root)

    def test_body_flow_finding_cannot_be_hidden(self) -> None:
        data = json.loads(self.visual.read_text(encoding="utf-8"))
        data["results"][0]["bodyFlow"]["forcedLineBreaks"] = [{"breakCount": 1}]
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(data, directory, "visual.json")
            with self.assertRaisesRegex(validate_product_flow_v6_evidence.ProductFlowV6EvidenceError, "body flow repair finding remains"):
                validate_product_flow_v6_evidence.validate(path, self.root)

    def test_exact_model_cohort_cannot_change(self) -> None:
        data = json.loads(self.generation.read_text(encoding="utf-8"))
        data["selection"]["model"] = "gpt-5.4"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(data, directory, "generation.json")
            with self.assertRaisesRegex(validate_product_flow_v6_evidence.ProductFlowV6EvidenceError, "exact Codex v6 mini cohort"):
                validate_product_flow_v6_evidence.validate(self.visual, self.root, generation_path=path)


if __name__ == "__main__":
    unittest.main()
