#!/usr/bin/env python3
"""Tests for the v3 product-flow evidence validator."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_product_flow_evidence


class ProductFlowEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.visual = self.root / "evals" / "product-flow-v3-visual-results.json"
        self.generation = self.root / "evals" / "product-flow-v3-generation-results.json"

    @staticmethod
    def _write(data: dict[str, object], directory: str, name: str) -> Path:
        path = Path(directory) / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_repository_v3_evidence_is_integrity_bound(self) -> None:
        self.assertEqual(18, validate_product_flow_evidence.validate(self.visual, self.root))

    def test_formal_sonnet_failure_cannot_be_upgraded(self) -> None:
        data = json.loads(self.generation.read_text(encoding="utf-8"))
        run = next(item for item in data["results"] if item["model"] == "sonnet" and item["case_id"] == "city-poetry-festival-v3")
        run["status"] = "completed"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(data, directory, "generation.json")
            with self.assertRaisesRegex(validate_product_flow_evidence.ProductFlowEvidenceError, "cannot be removed"):
                validate_product_flow_evidence.validate(self.visual, self.root, generation_path=path)

    def test_unknown_model_cannot_enter_the_model_set(self) -> None:
        data = json.loads(self.generation.read_text(encoding="utf-8"))
        run = next(item for item in data["results"] if item["model"] == "gpt-5.5")
        run["model"] = "gpt-unknown"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(data, directory, "generation.json")
            with self.assertRaisesRegex(validate_product_flow_evidence.ProductFlowEvidenceError, "model/case set"):
                validate_product_flow_evidence.validate(self.visual, self.root, generation_path=path)

    def test_stale_screenshot_hash_is_rejected(self) -> None:
        data = json.loads(self.visual.read_text(encoding="utf-8"))
        data["results"][0]["screenshotSha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(data, directory, "visual.json")
            with self.assertRaisesRegex(validate_product_flow_evidence.ProductFlowEvidenceError, "hash is stale"):
                validate_product_flow_evidence.validate(path, self.root)

    def test_missing_screenshot_result_is_rejected(self) -> None:
        data = json.loads(self.visual.read_text(encoding="utf-8"))
        data["results"].pop()
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(data, directory, "visual.json")
            with self.assertRaisesRegex(validate_product_flow_evidence.ProductFlowEvidenceError, "exactly 60"):
                validate_product_flow_evidence.validate(path, self.root)


if __name__ == "__main__":
    unittest.main()
