#!/usr/bin/env python3
"""Unit tests for the fixed product-flow matrix orchestrator."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "evals" / "run_product_flow_matrix.py"
SPEC = importlib.util.spec_from_file_location("run_product_flow_matrix", MODULE_PATH)
assert SPEC and SPEC.loader
matrix = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(matrix)


class ProductFlowMatrixTests(unittest.TestCase):
    def test_fixed_selection_contains_six_models_and_three_themes(self) -> None:
        cases = matrix.selected_cases("all", "all")
        self.assertEqual(18, len(cases))
        self.assertEqual(6, len(matrix.selected_cases("all", "mountain-rescue-flow-v3")))
        self.assertEqual(
            {"haiku", "sonnet", "opus", "gpt-5.4-mini", "gpt-5.4", "gpt-5.5"},
            {model for _, model, _ in cases},
        )
        self.assertEqual({"mountain-rescue-flow-v3", "city-poetry-festival-v3", "bookstore-one-line-v3"}, {case for _, _, case in cases})

    def test_existing_output_requires_manifest_digest_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            outputs = []
            for name, content in (("DESIGN.md", "# Design\n"), ("index.html", "<main></main>")):
                path = target / name
                path.write_text(content, encoding="utf-8")
                outputs.append({"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            manifest_path = target / "run-manifest.json"
            manifest_path.write_text(json.dumps({"outputs": outputs}), encoding="utf-8")
            self.assertEqual(outputs, matrix.verified_existing(target, "mountain-rescue-flow-v3")["outputs"])
            (target / "index.html").write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                matrix.verified_existing(target, "mountain-rescue-flow-v3")

    def test_bookstore_is_the_multi_page_consistency_case(self) -> None:
        self.assertEqual(
            ("DESIGN.md", "index.html", "catalog.html", "book.html"),
            matrix.outputs_for("bookstore-one-line-v3"),
        )

    def test_failure_classification_is_bounded(self) -> None:
        self.assertEqual("infrastructure_failure", matrix.classify_failure(2, "login unavailable"))
        self.assertEqual("model_resolution_failure", matrix.classify_failure(1, "requested model is unsupported"))
        self.assertEqual("output_policy_rejected", matrix.classify_failure(1, "isolated output policy rejected"))
        self.assertEqual("generation_failed", matrix.classify_failure(1, "generic failure"))

    def test_timeout_terminates_the_entire_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pid_file = Path(directory) / "child.pid"
            command = ["bash", "-c", f"sleep 60 & echo $! > '{pid_file}'; wait"]
            with self.assertRaises(subprocess.TimeoutExpired):
                matrix.run_isolated(command, 0.2)
            child_pid = int(pid_file.read_text(encoding="utf-8"))
            for _ in range(20):
                try:
                    os.kill(child_pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.05)
            else:
                self.fail(f"child process {child_pid} survived process-group timeout")


if __name__ == "__main__":
    unittest.main()
