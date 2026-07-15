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
        self.assertEqual(6, len(matrix.selected_cases("all", "harbor-cold-chain-v4")))
        self.assertEqual(
            {"haiku", "sonnet", "opus", "gpt-5.4-mini", "gpt-5.4", "gpt-5.5"},
            {model for _, model, _ in cases},
        )
        self.assertEqual({"harbor-cold-chain-v4", "island-sound-archive-v4", "plant-swap-one-line-v4"}, {case for _, _, case in cases})

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
            self.assertEqual(outputs, matrix.verified_existing(target, "harbor-cold-chain-v4")["outputs"])
            (target / "index.html").write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                matrix.verified_existing(target, "harbor-cold-chain-v4")

    def test_plant_swap_is_the_multi_page_consistency_case(self) -> None:
        self.assertEqual(
            ("DESIGN.md", "index.html", "browse.html", "listing.html"),
            matrix.outputs_for("plant-swap-one-line-v4"),
        )

    def test_failure_classification_is_bounded(self) -> None:
        self.assertEqual("infrastructure_failure", matrix.classify_failure(2, "login unavailable"))
        self.assertEqual("model_resolution_failure", matrix.classify_failure(1, "requested model is unsupported"))
        self.assertEqual("output_policy_rejected", matrix.classify_failure(1, "isolated output policy rejected"))
        self.assertEqual("generation_failed", matrix.classify_failure(1, "generic failure"))

    def test_timeout_and_generation_failure_are_retryable(self) -> None:
        self.assertTrue(matrix.should_retry("timeout"))
        self.assertTrue(matrix.should_retry("generation_failed"))
        self.assertFalse(matrix.should_retry("output_policy_rejected"))
        self.assertFalse(matrix.should_retry("model_resolution_failure"))
        self.assertFalse(matrix.should_retry("infrastructure_failure"))

    def test_retry_stops_after_success_and_preserves_attempts(self) -> None:
        outcomes = iter(
            (
                {"status": "timeout", "started_at": "one", "finished_at": "one", "duration_seconds": 1.0},
                {"status": "generation_failed", "started_at": "two", "finished_at": "two", "duration_seconds": 2.0},
                {"status": "completed", "started_at": "three", "finished_at": "three", "duration_seconds": 3.0},
            )
        )
        sleeps: list[float] = []

        def fake_attempt(*_args: object) -> dict[str, object]:
            return next(outcomes)

        attempts = matrix.run_case_with_retries(
            "claude",
            "sonnet",
            "island-sound-archive-v4",
            Path("unused"),
            initial_attempts=[],
            max_attempts=3,
            timeout_seconds=900,
            hard_timeout_seconds=3600,
            retry_delay_seconds=0.25,
            attempt_runner=fake_attempt,
            sleeper=sleeps.append,
        )
        self.assertEqual(["timeout", "generation_failed", "completed"], [item["status"] for item in attempts])
        self.assertEqual([1, 2, 3], [item["attempt"] for item in attempts])
        self.assertEqual([0.25, 0.25], sleeps)

        record: dict[str, object] = {}
        matrix.apply_attempts(record, attempts)
        self.assertEqual("completed", record["status"])
        self.assertEqual(3, record["attempt_count"])
        self.assertEqual("one", record["started_at"])

    def test_nonretryable_failure_stops_immediately(self) -> None:
        calls = 0

        def fake_attempt(*_args: object) -> dict[str, object]:
            nonlocal calls
            calls += 1
            return {
                "status": "output_policy_rejected",
                "started_at": "one",
                "finished_at": "one",
                "duration_seconds": 1.0,
            }

        attempts = matrix.run_case_with_retries(
            "claude",
            "sonnet",
            "island-sound-archive-v4",
            Path("unused"),
            initial_attempts=[],
            max_attempts=3,
            timeout_seconds=900,
            hard_timeout_seconds=3600,
            retry_delay_seconds=0,
            attempt_runner=fake_attempt,
        )
        self.assertEqual(1, calls)
        self.assertEqual("output_policy_rejected", attempts[-1]["status"])

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

    def test_advancing_output_extends_the_inactivity_deadline(self) -> None:
        completed = matrix.run_isolated(
            ["bash", "-c", "for value in 1 2 3 4; do echo $value; sleep 0.08; done"],
            0.15,
            hard_timeout_seconds=1.0,
        )
        self.assertEqual(0, completed.returncode)
        self.assertEqual(["1", "2", "3", "4"], completed.stdout.splitlines())

    def test_hard_timeout_still_bounds_continuous_output(self) -> None:
        with self.assertRaises(matrix.ProgressTimeoutExpired) as captured:
            matrix.run_isolated(
                ["bash", "-c", "while true; do echo tick; sleep 0.04; done"],
                0.15,
                hard_timeout_seconds=0.25,
            )
        self.assertEqual("hard-runtime", captured.exception.kind)

    def test_retry_receives_previous_bounded_diagnostic(self) -> None:
        received: list[str | None] = []

        def fake_attempt(*args: object) -> dict[str, object]:
            received.append(args[-1] if isinstance(args[-1], str) else None)
            if len(received) == 1:
                return {
                    "status": "generation_failed",
                    "error_summary": "orphan color token",
                    "started_at": "one",
                    "finished_at": "one",
                    "duration_seconds": 1.0,
                }
            return {
                "status": "completed",
                "started_at": "two",
                "finished_at": "two",
                "duration_seconds": 1.0,
            }

        matrix.run_case_with_retries(
            "codex",
            "gpt-5.4",
            "harbor-cold-chain-v4",
            Path("unused"),
            initial_attempts=[],
            max_attempts=2,
            timeout_seconds=900,
            hard_timeout_seconds=3600,
            retry_delay_seconds=0,
            attempt_runner=fake_attempt,
        )
        self.assertEqual([None, "orphan color token"], received)


if __name__ == "__main__":
    unittest.main()
