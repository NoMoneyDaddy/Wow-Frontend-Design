#!/usr/bin/env python3
"""Contract tests for the externalized v7 visual matrix."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "evals" / "run_v7_visual_matrix.py"
SPEC = importlib.util.spec_from_file_location("run_v7_visual_matrix", MODULE)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class V7VisualMatrixTests(unittest.TestCase):
    def test_hidden_matrix_must_stay_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "matrix.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(runner.V7VisualRunnerError, "outside the repository"):
                runner._outside_repository(path, ROOT, "hidden matrix")

    def test_complete_external_matrix_resolves_routes_and_specs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            outside = Path(directory)
            cohort = {
                "cohort_id": "v7-a1-test",
                "splits": {"development": [
                    {"id": "case-one", "required_states": ["base", "interaction"]},
                    {"id": "case-two", "required_states": ["base", "interaction"]},
                ]},
            }
            targets = []
            for variant in runner.evidence.VARIANTS:
                for case_id in ("case-one", "case-two"):
                    target = outside / f"{variant}-{case_id}"
                    target.mkdir()
                    (target / "index.html").write_text("<!doctype html><title>test</title>", encoding="utf-8")
                    states = {}
                    for state in ("base", "interaction"):
                        spec = outside / f"{variant}-{case_id}-{state}.json"
                        spec.write_text("{}", encoding="utf-8")
                        states[state] = {"route": "index.html", "spec": str(spec)}
                    targets.append({"variant": variant, "case_id": case_id, "root": str(target), "states": states})
            matrix = outside / "matrix.json"
            matrix.write_text(json.dumps({
                "schema_version": 1,
                "cohort_id": "v7-a1-test",
                "split": "development",
                "targets": targets,
            }), encoding="utf-8")
            loaded = runner.load_hidden_matrix(matrix, cohort, "development", ROOT)
            self.assertEqual(4, len(loaded))
            self.assertTrue(Path(loaded[("candidate", "case-two")]["states"]["base"]["route"]).is_file())


if __name__ == "__main__":
    unittest.main()
