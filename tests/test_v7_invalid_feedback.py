#!/usr/bin/env python3
"""Playwright-backed tests for invalid-feedback linkage replay."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "evals" / "v7_invalid_feedback.cjs"
FIXTURE = ROOT / "evals" / "fixtures" / "v7-invalid-feedback.html"


class V7InvalidFeedbackTests(unittest.TestCase):
    def test_contract_requires_unique_controls_errors_and_ordered_step_roles(self) -> None:
        source = f"""
const {{ validateInvalidFeedbackTargets }} = require({json.dumps(str(MODULE))});
const steps = JSON.parse(process.argv[1]);
const cases = JSON.parse(process.argv[2]);
process.stdout.write(JSON.stringify(cases.map((item) => {{
  try {{ validateInvalidFeedbackTargets(item, steps); return 'accepted'; }}
  catch {{ return 'rejected'; }}
}})));
"""
        steps = [
            {"id": "fill-control", "action": "fill", "selector": "#control", "value": "secret"},
            {"id": "invalidate", "action": "click", "selector": "#invalidate"},
        ]
        target = {"id": "field-feedback", "controlStepId": "fill-control", "invalidationStepId": "invalidate", "errorSelector": "[data-error]"}
        cases = [
            [target],
            [{**target, "copy": "forbidden"}],
            [{**target, "controlStepId": "missing"}],
            [{**target, "controlStepId": "invalidate", "invalidationStepId": "fill-control"}],
            [target, {**target, "id": "second-feedback"}],
            [target, {**target, "id": "second-feedback", "controlStepId": "fill-control", "errorSelector": "#other"}],
        ]
        completed = subprocess.run(
            ["node", "-e", source, json.dumps(steps), json.dumps(cases)],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        self.assertEqual(["accepted", "rejected", "rejected", "rejected", "rejected", "rejected"], json.loads(completed.stdout))

    def test_fresh_replays_classify_relations_and_fail_closed_contract_gaps(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ auditInvalidFeedbackTargets }} = require({json.dumps(str(MODULE))});
const base = new URL({json.dumps(FIXTURE.as_uri())});
const cases = JSON.parse(process.argv[1]);
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const results = {{}};
  for (const item of cases) {{
    const url = new URL(`${{base.href}}?mode=${{item.mode}}`);
    results[item.mode] = await auditInvalidFeedbackTargets(browser, url, {{ viewport: {{ width: 800, height: 600 }} }}, item.spec);
  }}
  await browser.close();
  process.stdout.write(JSON.stringify(results));
}})().catch(() => {{ console.error('fixed-test-failure'); process.exit(1); }});
"""

        def case(mode: str) -> dict:
            action = "select" if mode == "select" else "fill"
            steps = [
                {"id": "control-step", "action": action, "selector": "#control", "value": "two" if mode == "select" else "PRIVATE-VALUE"},
                {"id": "invalidate-step", "action": "click", "selector": "#invalidate"},
            ]
            return {
                "mode": mode,
                "spec": {
                    "steps": steps,
                    "invalidFeedbackTargets": [{
                        "id": f"{mode}-feedback", "controlStepId": "control-step",
                        "invalidationStepId": "invalidate-step", "errorSelector": "[data-error]",
                    }],
                },
            }

        modes = [
            "describedby", "errormessage", "both", "missing", "textarea", "select",
            "invalid-false", "hidden-error", "aria-hidden-error", "aria-hidden-control", "inert-error",
            "multi-errormessage", "empty-error", "idless-error", "duplicate-id",
            "unsupported", "shadow", "external",
        ]
        completed = subprocess.run(
            ["node", "-e", source, json.dumps([case(mode) for mode in modes])],
            cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        results = json.loads(completed.stdout)
        record = lambda mode: results[mode]["invalidFeedbackTargets"][0]
        for mode, relation in {"describedby": "describedby", "errormessage": "errormessage", "both": "both"}.items():
            self.assertEqual(("clear", relation), (record(mode)["status"], record(mode)["relation"]))
        self.assertEqual(("confirmed", "missing"), (record("missing")["status"], record("missing")["relation"]))
        self.assertEqual("confirmed", record("textarea")["status"])
        self.assertEqual("confirmed", record("select")["status"])
        for mode in (
            "invalid-false", "hidden-error", "aria-hidden-error", "aria-hidden-control", "inert-error",
            "multi-errormessage", "empty-error", "idless-error", "duplicate-id", "unsupported", "shadow",
        ):
            with self.subTest(mode=mode):
                self.assertEqual(("unavailable", "feedback_contract_unavailable"), (record(mode)["status"], record(mode)["reason"]))
        self.assertEqual(("unavailable", "external_request_blocked"), (record("external")["status"], record("external")["reason"]))
        expected_coverage = {"status", "reason", "declaredTargets", "completedTargets", "freshReplays", "claimBoundary"}
        self.assertTrue(all(set(result["invalidFeedbackCoverage"]) == expected_coverage for result in results.values()))
        self.assertTrue(all(result["invalidFeedbackCoverage"]["freshReplays"] == 2 for result in results.values()))
        self.assertTrue(all(result["invalidFeedbackCoverage"]["claimBoundary"] == "two fresh evaluator-controlled invalid-feedback linkage replays" for result in results.values()))
        for result in results.values():
            item = result["invalidFeedbackTargets"][0]
            expected = {"id", "status", "replays", "reason"} if item["status"] == "unavailable" else {"id", "status", "replays", "relation"}
            self.assertEqual(expected, set(item))
        serialized = json.dumps(results)
        for secret in ("[data-error]", "field-error", "Secret validation copy", "PRIVATE-VALUE"):
            self.assertNotIn(secret, serialized)
            self.assertNotIn(secret, completed.stderr)
        self.assertNotIn("screenshot", MODULE.read_text(encoding="utf-8"))

    def test_mixed_relation_and_native_signature_drift_are_unavailable(self) -> None:
        source = f"""
const {{ aggregateInvalidFeedbackResults }} = require({json.dumps(str(MODULE))});
const target = {{ id: 'field-feedback' }};
const aggregate = (items) => aggregateInvalidFeedbackResults([target], new Map([['field-feedback', items]])).invalidFeedbackTargets[0];
process.stdout.write(JSON.stringify({{
  mixed: aggregate([{{status:'linked',relation:'describedby',signature:'input-text:error'}},{{status:'missing',relation:'missing',signature:'input-text:error'}}]),
  relation: aggregate([{{status:'linked',relation:'describedby',signature:'input-text:error'}},{{status:'linked',relation:'errormessage',signature:'input-text:error'}}]),
  native: aggregate([{{status:'linked',relation:'describedby',signature:'input-text:error'}},{{status:'linked',relation:'describedby',signature:'textarea:error'}}]),
}}));
"""
        completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True, check=True)
        result = json.loads(completed.stdout)
        self.assertTrue(all(item["status"] == "unavailable" and item["reason"] == "replay_unstable" for item in result.values()))


if __name__ == "__main__":
    unittest.main()
