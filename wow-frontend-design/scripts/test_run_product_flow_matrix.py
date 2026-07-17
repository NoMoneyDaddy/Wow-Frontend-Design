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


def write_manifest(target: Path, provider: str, model: str, case_id: str) -> dict[str, object]:
    output_records = []
    for name in matrix.outputs_for(case_id):
        path = target / name
        output_records.append(
            {"path": name, "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        )
    runner_name = "run_claude_case.sh" if provider == "claude" else "run_codex_case.sh"
    runner = ROOT / "evals" / runner_name
    validator = ROOT / "evals" / "validate_visual_web_output.py"
    manifest = {
        "schema_version": 1,
        "status": "completed",
        "case": {"id": case_id, "target": str(target.resolve())},
        "model": {"requested_alias" if provider == "claude" else "requested_identifier": model},
        "runner": {"path": f"evals/{runner_name}", "sha256": hashlib.sha256(runner.read_bytes()).hexdigest()},
        "output_validator": {
            "path": "evals/validate_visual_web_output.py",
            "sha256": hashlib.sha256(validator.read_bytes()).hexdigest(),
        },
        "outputs": output_records,
    }
    if provider == "codex":
        manifest["provider"] = "openai-first-party-chatgpt-oauth"
    (target / "run-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


class ProductFlowMatrixTests(unittest.TestCase):
    def test_fixed_selection_contains_one_model_and_eight_themes(self) -> None:
        cases = matrix.selected_cases("all", "all")
        self.assertEqual(8, len(cases))
        self.assertEqual(1, len(matrix.selected_cases("all", "wind-maintenance-dispatch-v6")))
        self.assertEqual(
            {"gpt-5.4-mini"},
            {model for _, model, _ in cases},
        )
        self.assertEqual(
            {
                "wind-maintenance-dispatch-v6",
                "type-foundry-specimen-v6",
                "repair-cafe-intake-v6",
                "night-market-allergen-v6",
                "royalty-statement-v6",
                "packaging-configurator-v6",
                "oral-history-archive-v6",
                "grant-review-board-v6",
            },
            {case for _, _, case in cases},
        )
        mini_cases = matrix.selected_cases("all", "all", "gpt-5.4-mini")
        self.assertEqual(8, len(mini_cases))
        self.assertEqual({"codex"}, {provider for provider, _, _ in mini_cases})
        self.assertEqual({"gpt-5.4-mini"}, {model for _, model, _ in mini_cases})

    def test_existing_output_requires_manifest_digest_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for name, content in (("DESIGN.md", "# Design\n"), ("index.html", "<main></main>")):
                path = target / name
                path.write_text(content, encoding="utf-8")
            manifest = write_manifest(target, "codex", "gpt-5.4-mini", "wind-maintenance-dispatch-v6")
            self.assertEqual(
                manifest["outputs"],
                matrix.verified_existing(target, "codex", "gpt-5.4-mini", "wind-maintenance-dispatch-v6")["outputs"],
            )
            forged_receipt = matrix._manifest_receipt(target, manifest)
            forged_receipt["manifest_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "receipt mismatch"):
                matrix.verified_existing(
                    target,
                    "codex",
                    "gpt-5.4-mini",
                    "wind-maintenance-dispatch-v6",
                    expected_receipt=forged_receipt,
                )
            (target / "index.html").write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                matrix.verified_existing(target, "codex", "gpt-5.4-mini", "wind-maintenance-dispatch-v6")

    def test_publication_can_verify_frozen_receipt_without_rebinding_historical_tools(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for name in matrix.outputs_for("wind-maintenance-dispatch-v6"):
                (target / name).write_text(name, encoding="utf-8")
            manifest = write_manifest(target, "codex", "gpt-5.4-mini", "wind-maintenance-dispatch-v6")
            manifest["runner"]["sha256"] = "0" * 64  # type: ignore[index]
            (target / "run-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            receipt = matrix._manifest_receipt(target, manifest)
            with self.assertRaisesRegex(ValueError, "runner provenance"):
                matrix.verified_existing(target, "codex", "gpt-5.4-mini", "wind-maintenance-dispatch-v6")
            verified = matrix.verified_existing(
                target,
                "codex",
                "gpt-5.4-mini",
                "wind-maintenance-dispatch-v6",
                expected_receipt=receipt,
                verify_current_tools=False,
            )
            self.assertEqual(manifest["outputs"], verified["outputs"])

    def test_minimal_self_signed_manifest_is_rejected_as_untrusted_preexisting_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            outputs = []
            for name in matrix.outputs_for("wind-maintenance-dispatch-v6"):
                path = target / name
                path.write_text(name, encoding="utf-8")
                outputs.append({"path": name, "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            (target / "run-manifest.json").write_text(
                json.dumps({"schema_version": 1, "status": "completed", "outputs": outputs}),
                encoding="utf-8",
            )
            attempt = matrix.run_case_attempt(
                "codex", "gpt-5.4-mini", "wind-maintenance-dispatch-v6", target, 30, 30, None
            )
            self.assertEqual("infrastructure_failure", attempt["status"])
            self.assertIn("provenance", str(attempt["error_summary"]))

    def test_existing_output_rejects_symlink_target_and_duplicate_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "real"
            target.mkdir()
            for name in matrix.outputs_for("wind-maintenance-dispatch-v6"):
                (target / name).write_text(name, encoding="utf-8")
            manifest = write_manifest(target, "codex", "gpt-5.4-mini", "wind-maintenance-dispatch-v6")
            linked = root / "linked"
            linked.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "unsafe pre-existing target"):
                matrix.verified_existing(linked, "codex", "gpt-5.4-mini", "wind-maintenance-dispatch-v6")
            manifest["outputs"].append(dict(manifest["outputs"][0]))  # type: ignore[union-attr]
            (target / "run-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid manifest outputs"):
                matrix.verified_existing(target, "codex", "gpt-5.4-mini", "wind-maintenance-dispatch-v6")

    def test_v6_multi_page_contracts_are_fixed(self) -> None:
        self.assertEqual(
            ("DESIGN.md", "index.html", "materials.html", "summary.html"),
            matrix.outputs_for("packaging-configurator-v6"),
        )
        self.assertEqual(
            ("DESIGN.md", "index.html", "archive.html", "story.html"),
            matrix.outputs_for("oral-history-archive-v6"),
        )

    def test_failure_classification_is_bounded(self) -> None:
        self.assertEqual("infrastructure_failure", matrix.classify_failure(2, "login unavailable"))
        self.assertEqual("model_resolution_failure", matrix.classify_failure(1, "requested model is unsupported"))
        self.assertEqual("output_policy_rejected", matrix.classify_failure(1, "isolated output policy rejected"))
        self.assertEqual("generation_failed", matrix.classify_failure(1, "generic failure"))

    def test_incomplete_generation_statuses_are_retryable(self) -> None:
        self.assertTrue(matrix.should_retry("timeout", "inactivity"))
        self.assertFalse(matrix.should_retry("timeout", "hard-runtime"))
        self.assertFalse(matrix.should_retry("timeout", "output-limit"))
        self.assertTrue(matrix.should_retry("generation_failed"))
        self.assertFalse(matrix.should_retry("output_policy_rejected"))
        self.assertFalse(matrix.should_retry("model_resolution_failure"))
        self.assertFalse(matrix.should_retry("infrastructure_failure"))

    def test_retry_stops_after_success_and_preserves_attempts(self) -> None:
        outcomes = iter(
            (
                {"status": "timeout", "timeout_kind": "inactivity", "started_at": "one", "finished_at": "one", "duration_seconds": 1.0},
                {"status": "generation_failed", "started_at": "two", "finished_at": "two", "duration_seconds": 2.0},
                {"status": "completed", "started_at": "three", "finished_at": "three", "duration_seconds": 3.0},
            )
        )
        sleeps: list[float] = []

        def fake_attempt(*_args: object) -> dict[str, object]:
            return next(outcomes)

        attempts = matrix.run_case_with_retries(
            "claude",
            "haiku",
            "repair-cafe-intake-v6",
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

    def test_policy_failure_does_not_retry_blindly(self) -> None:
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
            "haiku",
            "repair-cafe-intake-v6",
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

    def test_hard_timeout_does_not_retry(self) -> None:
        calls = 0

        def fake_attempt(*_args: object) -> dict[str, object]:
            nonlocal calls
            calls += 1
            return {
                "status": "timeout",
                "timeout_kind": "hard-runtime",
                "started_at": "one",
                "finished_at": "one",
                "duration_seconds": 1.0,
            }

        attempts = matrix.run_case_with_retries(
            "codex",
            "gpt-5.4-mini",
            "repair-cafe-intake-v6",
            Path("unused"),
            initial_attempts=[],
            max_attempts=3,
            timeout_seconds=900,
            hard_timeout_seconds=3600,
            retry_delay_seconds=0,
            attempt_runner=fake_attempt,
        )
        self.assertEqual(1, calls)
        self.assertEqual("hard-runtime", attempts[-1]["timeout_kind"])

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

    def test_hard_timeout_still_applies_after_child_closes_both_pipes(self) -> None:
        started = time.monotonic()
        with self.assertRaises(matrix.ProgressTimeoutExpired) as captured:
            matrix.run_isolated(
                ["bash", "-c", "exec 1>&- 2>&-; sleep 5"],
                1.0,
                hard_timeout_seconds=0.25,
            )
        self.assertEqual("hard-runtime", captured.exception.kind)
        self.assertLess(time.monotonic() - started, 1.5)

    def test_combined_output_is_bounded_before_join_and_decode(self) -> None:
        with self.assertRaises(matrix.OutputLimitExceeded) as captured:
            matrix.run_isolated(
                ["bash", "-c", "python3 -c 'import sys; sys.stdout.write(\"x\" * 4096)'"],
                2,
                hard_timeout_seconds=3,
                max_output_bytes=1024,
            )
        self.assertEqual(1024, len(captured.exception.output))

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
            "wind-maintenance-dispatch-v6",
            Path("unused"),
            initial_attempts=[],
            max_attempts=2,
            timeout_seconds=900,
            hard_timeout_seconds=3600,
            retry_delay_seconds=0,
            attempt_runner=fake_attempt,
        )
        self.assertEqual([None, "orphan color token"], received)

    def test_case_feedback_selects_only_the_matching_visual_diagnostic(self) -> None:
        environment = {
            "PRODUCT_FLOW_RETRY_FEEDBACK": "stale global value",
            "PRODUCT_FLOW_RETRY_FEEDBACK_BY_CASE": json.dumps(
                {
                    "wind-maintenance-dispatch-v6": "wind finding",
                    "repair-cafe-intake-v6": "repair finding",
                }
            ),
        }
        matrix.apply_case_feedback(environment, "repair-cafe-intake-v6", None)
        self.assertEqual("repair finding", environment["PRODUCT_FLOW_RETRY_FEEDBACK"])
        self.assertNotIn("PRODUCT_FLOW_RETRY_FEEDBACK_BY_CASE", environment)

    def test_case_feedback_prefers_provider_model_target_key(self) -> None:
        environment = {
            "PRODUCT_FLOW_RETRY_FEEDBACK_BY_CASE": json.dumps(
                {
                    "repair-cafe-intake-v6:claude-haiku": "claude finding",
                    "repair-cafe-intake-v6:codex-gpt-5.4-mini": "codex finding",
                }
            )
        }
        matrix.apply_case_feedback(
            environment,
            "repair-cafe-intake-v6",
            None,
            provider="codex",
            model="gpt-5.4-mini",
        )
        self.assertEqual("codex finding", environment["PRODUCT_FLOW_RETRY_FEEDBACK"])

    def test_case_feedback_rejects_unbounded_selected_value(self) -> None:
        environment = {
            "PRODUCT_FLOW_RETRY_FEEDBACK_BY_CASE": json.dumps(
                {"repair-cafe-intake-v6": "x" * 501}
            )
        }
        with self.assertRaisesRegex(ValueError, "bounded line"):
            matrix.apply_case_feedback(environment, "repair-cafe-intake-v6", None)


if __name__ == "__main__":
    unittest.main()
