#!/usr/bin/env python3
"""Playwright-backed tests for declared invalid-input preservation."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "evals" / "v7_invalid_input_preservation.cjs"
FIXTURE = ROOT / "evals" / "fixtures" / "v7-invalid-input-preservation.html"


class V7InvalidInputPreservationTests(unittest.TestCase):
    def test_contract_is_exact_and_requires_adjacent_ordered_step_roles(self) -> None:
        source = f"""
const {{ validateInvalidInputPreservationTargets }} = require({json.dumps(str(MODULE))});
const steps = JSON.parse(process.argv[1]);
const cases = JSON.parse(process.argv[2]);
process.stdout.write(JSON.stringify(cases.map((item) => {{
  try {{ validateInvalidInputPreservationTargets(item, steps); return 'accepted'; }}
  catch {{ return 'rejected'; }}
}})));
"""
        steps = [
            {"id": "control-step", "action": "fill", "selector": "#control", "value": "eval-preserve-text"},
            {"id": "invalidate-step", "action": "click", "selector": "#invalidate"},
            {"id": "later-step", "action": "click", "selector": "#later"},
        ]
        target = {"id": "preserve-field", "controlStepId": "control-step", "invalidationStepId": "invalidate-step", "normalization": "none"}
        cases = [
            [target],
            [{**target, "selector": "#forbidden"}],
            [{**target, "controlStepId": "missing"}],
            [{**target, "invalidationStepId": "later-step"}],
            [{**target, "controlStepId": "invalidate-step", "invalidationStepId": "later-step"}],
            [target, {**target, "id": "second-preserve"}],
        ]
        completed = subprocess.run(
            ["node", "-e", source, json.dumps(steps), json.dumps(cases)],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        steps_with_private_value = [dict(step) for step in steps]
        steps_with_private_value[0]["value"] = "PRIVATE-INVALID-VALUE"
        completed_private = subprocess.run(
            ["node", "-e", source, json.dumps(steps_with_private_value), json.dumps([[target]])],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        self.assertEqual(["accepted", "rejected", "rejected", "rejected", "rejected", "rejected"], json.loads(completed.stdout))
        self.assertEqual(["rejected"], json.loads(completed_private.stdout))

    def test_two_fresh_replays_classify_retained_lost_and_contract_unavailable(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ auditInvalidInputPreservationTargets }} = require({json.dumps(str(MODULE))});
const base = new URL({json.dumps(FIXTURE.as_uri())});
const cases = JSON.parse(process.argv[1]);
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const results = {{}};
  for (const item of cases) {{
    const url = new URL(`${{base.href}}?mode=${{item.mode}}`);
    results[item.mode] = await auditInvalidInputPreservationTargets(browser, url, {{ viewport: {{ width: 800, height: 600 }} }}, item.spec);
  }}
  await browser.close();
  process.stdout.write(JSON.stringify(results));
}})().catch(() => {{ console.error('fixed-test-failure'); process.exit(1); }});
"""

        def case(mode: str) -> dict:
            select = mode in {"select", "select-label", "multiple-select"}
            steps = [
                {"id": "control-step", "action": "select" if select else "fill", "selector": "#control", "value": "eval-preserve-label" if mode == "select-label" else "eval-preserve-option" if select else "eval-preserve-text"},
                {"id": "invalidate-step", "action": "click", "selector": "#invalidate"},
            ]
            return {
                "mode": mode,
                "spec": {
                    "steps": steps,
                    "invalidInputPreservationTargets": [{
                        "id": f"{mode}-preservation", "controlStepId": "control-step", "invalidationStepId": "invalidate-step", "normalization": "none",
                    }],
                },
            }

        modes = [
            "retained", "lost", "textarea", "select", "select-label", "initially-invalid", "invalid-false", "hidden", "duplicate",
            "unsupported", "multiple-select", "shadow", "external",
        ]
        completed = subprocess.run(
            ["node", "-e", source, json.dumps([case(mode) for mode in modes])],
            cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        results = json.loads(completed.stdout)
        record = lambda mode: results[mode]["records"][0]
        self.assertEqual(("clear", "input-text", True), (
            record("retained")["status"], record("retained")["nativeKind"], record("retained")["retained"],
        ))
        self.assertEqual(("confirmed", "input-text", False), (
            record("lost")["status"], record("lost")["nativeKind"], record("lost")["retained"],
        ))
        self.assertEqual(("clear", "textarea", True), (
            record("textarea")["status"], record("textarea")["nativeKind"], record("textarea")["retained"],
        ))
        self.assertEqual(("clear", "select-one", True), (
            record("select")["status"], record("select")["nativeKind"], record("select")["retained"],
        ))
        self.assertEqual(("clear", "select-one", True), (
            record("select-label")["status"], record("select-label")["nativeKind"], record("select-label")["retained"],
        ))
        for mode in ("initially-invalid", "invalid-false", "hidden", "duplicate", "unsupported", "multiple-select", "shadow"):
            with self.subTest(mode=mode):
                self.assertEqual(("unavailable", "preservation_contract_unavailable"), (record(mode)["status"], record(mode)["reason"]))
        self.assertEqual(("unavailable", "external_request_blocked"), (record("external")["status"], record("external")["reason"]))
        expected_coverage = {"status", "reason", "declaredTargets", "completedTargets", "freshReplays", "claimBoundary"}
        self.assertTrue(all(set(result["coverage"]) == expected_coverage for result in results.values()))
        self.assertTrue(all(result["coverage"]["freshReplays"] == 2 for result in results.values()))
        self.assertTrue(all(result["coverage"]["claimBoundary"] == "two fresh evaluator-controlled invalid-input preservation replays" for result in results.values()))
        for result in results.values():
            item = result["records"][0]
            expected = {"id", "status", "replays", "reason"} if item["status"] == "unavailable" else {
                "id", "status", "replays", "nativeKind", "retained",
            }
            self.assertEqual(expected, set(item))
        serialized = json.dumps(results)
        for secret in ("#control", "eval-preserve-text", "eval-preserve-option", "selector", "value"):
            self.assertNotIn(secret, serialized)
            self.assertNotIn(secret, completed.stderr)
        self.assertNotIn("screenshot", MODULE.read_text(encoding="utf-8"))

    def test_status_and_native_signature_drift_are_unavailable(self) -> None:
        source = f"""
const {{ aggregateInvalidInputPreservationResults }} = require({json.dumps(str(MODULE))});
const target = {{ id: 'preserve-field' }};
const aggregate = (items) => aggregateInvalidInputPreservationResults([target], new Map([['preserve-field', items]])).records[0];
process.stdout.write(JSON.stringify({{
  status: aggregate([{{status:'retained',nativeKind:'input-text'}},{{status:'lost',nativeKind:'input-text'}}]),
  native: aggregate([{{status:'retained',nativeKind:'input-text'}},{{status:'retained',nativeKind:'textarea'}}]),
}}));
"""
        completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True, check=True)
        result = json.loads(completed.stdout)
        self.assertTrue(all(item["status"] == "unavailable" and item["reason"] == "replay_unstable" for item in result.values()))


if __name__ == "__main__":
    unittest.main()
