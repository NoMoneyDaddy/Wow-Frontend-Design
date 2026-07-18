#!/usr/bin/env python3
"""Contract tests for the externalized v7 visual matrix."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "evals" / "run_v7_visual_matrix.py"
SPEC = importlib.util.spec_from_file_location("run_v7_visual_matrix", MODULE)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class V7VisualMatrixTests(unittest.TestCase):
    def test_capture_inventory_runs_only_exact_selected_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.mkdir()
            route = target / "index.html"
            spec = root / "spec.json"
            route.write_text("<!doctype html><title>test</title>", encoding="utf-8")
            spec.write_text("{}", encoding="utf-8")
            targets = {("candidate", "case-one"): {
                "root": str(target),
                "states": {"base": {
                    "route": str(route),
                    "route_sha256": runner._digest(route),
                    "spec": str(spec),
                    "spec_sha256": runner._digest(spec),
                }},
            }}
            key = ("candidate", "case-one", "base", "desktop", "chromium")
            results = root / "results"
            screenshots = root / "screenshots"
            results.mkdir()
            screenshots.mkdir()
            commands = []

            def fake_auditor(command: list[str], _root: Path, _timeout: int) -> tuple[int, str]:
                commands.append(command)
                Path(command[command.index("--output") + 1]).write_text("{}", encoding="utf-8")
                Path(command[command.index("--screenshot") + 1]).write_bytes(b"png")
                return 0, "auditor_nonzero"

            with mock.patch.object(runner.evidence, "_validate_result", return_value="clean"):
                attempts = runner.capture_inventory(
                    targets,
                    [key],
                    results,
                    screenshots,
                    30,
                    1,
                    ROOT,
                    allowed_keys={key},
                    auditor_runner=fake_auditor,
                )
            self.assertEqual(1, len(commands))
            self.assertEqual("desktop", commands[0][commands[0].index("--profile") + 1])
            self.assertEqual("completed", attempts[0]["attempts"][-1]["status"])
            with self.assertRaisesRegex(runner.V7VisualRunnerError, "duplicated"):
                runner.capture_inventory(
                    targets,
                    [key, key],
                    results,
                    screenshots,
                    30,
                    1,
                    ROOT,
                    allowed_keys={key},
                    auditor_runner=fake_auditor,
                )

    def test_gate_inventory_defaults_to_full_and_fast_is_sixteen(self) -> None:
        cohort = {
            "splits": {"development": [
                {"id": "case-one", "required_states": ["base", "interaction"]},
                {"id": "case-two", "required_states": ["base", "interaction"]},
            ]},
        }
        self.assertEqual(60, len(runner.evidence.expected_inventory(cohort, "development")))
        self.assertEqual(16, len(runner.evidence.expected_inventory(cohort, "development", "fast")))

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

    def test_generation_cohort_requires_matching_briefs_and_stable_packages(self) -> None:
        records = {}
        for variant in runner.evidence.VARIANTS:
            for case_id in ("case-one", "case-two"):
                records[(variant, case_id)] = {
                    "materialized_tree_sha256": variant * 8,
                    "editable_sha256": variant * 8,
                    "brief_sha256": case_id * 8,
                }
        self.assertIsNone(runner.validate_generation_cohort(records, {"case-one", "case-two"}))
        records[("candidate", "case-two")]["brief_sha256"] = "different"
        with self.assertRaisesRegex(runner.V7VisualRunnerError, "briefs differ"):
            runner.validate_generation_cohort(records, {"case-one", "case-two"})


if __name__ == "__main__":
    unittest.main()
