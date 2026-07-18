#!/usr/bin/env python3
"""Playwright-backed tests for mutually exclusive form outcomes."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "evals" / "v7_form_outcome.cjs"
FIXTURE = ROOT / "evals" / "fixtures" / "v7-form-outcome.html"


def target(identifier: str = "primary-outcome", *, validation_mode: str = "custom-aria") -> dict:
    return {
        "id": identifier,
        "validControlStepId": "valid-control",
        "successStepId": "show-success",
        "invalidControlStepId": "invalid-control",
        "invalidationStepId": "show-error",
        "successSelector": "#success",
        "errorSelector": "#error" if validation_mode == "custom-aria" else None,
        "outcomeSemantics": "mutually-exclusive",
        "normalization": "none",
        "settling": "reduced-motion-static",
        "validationMode": validation_mode,
    }


def steps(*, press: bool = False) -> list[dict]:
    action = "press" if press else "click"
    action_value = {"value": "Enter"} if press else {}
    return [
        {"id": "valid-control", "action": "fill", "selector": "#control", "value": "eval-outcome-valid-alpha"},
        {"id": "show-success", "action": action, "selector": "#submit", **action_value},
        {"id": "invalid-control", "action": "fill", "selector": "#control", "value": "eval-outcome-invalid-alpha"},
        {"id": "show-error", "action": action, "selector": "#submit", **action_value},
    ]


class V7FormOutcomeTests(unittest.TestCase):
    def test_contract_is_exact_consecutive_and_synthetic(self) -> None:
        source = f"""
const {{ validateFormOutcomeTargets }} = require({json.dumps(str(MODULE))});
const cases = JSON.parse(process.argv[1]);
process.stdout.write(JSON.stringify(cases.map((item) => {{
  try {{ validateFormOutcomeTargets(item.targets, item.steps); return 'accepted'; }}
  catch {{ return 'rejected'; }}
}})));
"""
        base_target = target()
        native_target = target(validation_mode="native-constraint")
        base_steps = steps()
        select_steps = [
            {"id": "valid-control", "action": "select", "selector": "#control", "value": "eval-outcome-valid-option"},
            base_steps[1],
            {"id": "invalid-control", "action": "select", "selector": "#control", "value": "eval-outcome-invalid-option"},
            base_steps[3],
        ]
        cases = [
            {"targets": [base_target], "steps": base_steps},
            {"targets": [{**base_target, "copy": "forbidden"}], "steps": base_steps},
            {"targets": [{key: value for key, value in base_target.items() if key != "settling"}], "steps": base_steps},
            {"targets": [{key: value for key, value in base_target.items() if key != "validationMode"}], "steps": base_steps},
            {"targets": [{**base_target, "outcomeSemantics": "independent"}], "steps": base_steps},
            {"targets": [{**base_target, "validationMode": "unknown"}], "steps": base_steps},
            {"targets": [{**base_target, "errorSelector": None}], "steps": base_steps},
            {"targets": [{**native_target, "errorSelector": "#error"}], "steps": base_steps},
            {"targets": [base_target], "steps": [{**base_steps[0], "value": "user-value"}, *base_steps[1:]]},
            {"targets": [base_target], "steps": [
                {**base_steps[0], "value": f"eval-outcome-valid-{'a' * 41}"}, *base_steps[1:],
            ]},
            {"targets": [base_target], "steps": [*base_steps[:2], {"id": "gap", "action": "click", "selector": "#gap"}, *base_steps[2:]]},
            {"targets": [base_target], "steps": [*base_steps[:2], {**base_steps[2], "selector": "#other"}, base_steps[3]]},
            {"targets": [base_target], "steps": [base_steps[0], {**base_steps[1], "action": "press", "value": "Escape"}, *base_steps[2:]]},
            {"targets": [base_target], "steps": select_steps},
            {"targets": [native_target], "steps": base_steps},
            {"targets": [base_target, {**base_target, "id": "second-outcome"}], "steps": base_steps},
        ]
        completed = subprocess.run(
            ["node", "-e", source, json.dumps(cases)], cwd=ROOT, text=True, capture_output=True, check=True,
        )
        self.assertEqual(
            [
                "accepted", "rejected", "rejected", "rejected", "rejected", "rejected", "rejected", "rejected",
                "rejected", "rejected", "rejected", "rejected", "rejected", "accepted", "accepted", "rejected",
            ],
            json.loads(completed.stdout),
        )

    def test_fresh_replays_classify_stale_success_and_fail_closed(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ auditFormOutcomeTargets, replayFormOutcomeTarget }} = require({json.dumps(str(MODULE))});
const base = new URL({json.dumps(FIXTURE.as_uri())});
const cases = JSON.parse(process.argv[1]);
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const results = {{}};
  for (const item of cases) {{
    const url = new URL(`${{base.href}}?mode=${{item.mode}}`);
    results[item.key] = await auditFormOutcomeTargets(browser, url,
      {{ viewport: {{ width: 800, height: 600 }} }}, item.spec);
  }}
  const driftSpec = cases[0].spec;
  let replay = 0;
  results.drift = await auditFormOutcomeTargets(browser, new URL(`${{base.href}}?mode=drift`),
    {{ viewport: {{ width: 800, height: 600 }} }}, driftSpec,
    async (activeBrowser, url, options, declaredTarget, declaredSteps) => {{
      const replayUrl = new URL(url.href);
      replayUrl.searchParams.set('variant', replay++ === 0 ? 'clean' : 'stale');
      return replayFormOutcomeTarget(activeBrowser, replayUrl, options, declaredTarget, declaredSteps);
    }});
  await browser.close();
  process.stdout.write(JSON.stringify(results));
}})().catch(() => {{ console.error('fixed-test-failure'); process.exit(1); }});
"""

        def case(key: str, mode: str, *, press: bool = False, validation_mode: str = "custom-aria") -> dict:
            return {
                "key": key,
                "mode": mode,
                "spec": {
                    "steps": steps(press=press),
                    "formOutcomeTargets": [target(f"{key}-outcome", validation_mode=validation_mode)],
                },
            }

        cases = [
            case("correct", "correct"),
            case("press", "correct", press=True),
            case("stale", "stale"),
            case("initial", "initial"),
            case("success", "success"),
            case("noop", "noop"),
            case("unsupported", "unsupported"),
            case("shadow", "shadow"),
            case("external", "external"),
            case("motion", "motion"),
            case("paint", "paint"),
            case("clear-value", "clear-value"),
            case("native-correct", "native-correct", validation_mode="native-constraint"),
            case("native-stale", "native-stale", validation_mode="native-constraint"),
            case("native-novalidate", "native-novalidate", validation_mode="native-constraint"),
            case("native-clear-value", "native-clear-value", validation_mode="native-constraint"),
            case("visual-opacity-clean", "visual-opacity-clean"),
            case("repurposed-success", "repurposed-success"),
            case("empty-success", "empty-success"),
            case("empty-error", "empty-error"),
            case("hidden-child-text", "hidden-child-text"),
            case("child-complex-paint", "child-complex-paint"),
        ]
        completed = subprocess.run(
            ["node", "-e", source, json.dumps(cases)], cwd=ROOT, text=True, capture_output=True, timeout=60,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        results = json.loads(completed.stdout)
        record = lambda key: results[key]["records"][0]
        for key in (
            "correct", "press", "native-correct", "visual-opacity-clean", "repurposed-success",
        ):
            self.assertEqual(("clear", False), (record(key)["status"], record(key)["staleSuccess"]))
        for key in (
            "stale", "native-stale",
        ):
            self.assertEqual(("confirmed", True), (record(key)["status"], record(key)["staleSuccess"]))
        expected_reasons = {
            "initial": "initial_state_unavailable",
            "success": "success_checkpoint_unavailable",
            "noop": "invalid_checkpoint_unavailable",
            "unsupported": "initial_state_unavailable",
            "shadow": "initial_state_unavailable",
            "external": "external_request_blocked",
            "motion": "state_settling_unavailable",
            "paint": "form_outcome_contract_unavailable",
            "clear-value": "invalid_checkpoint_unavailable",
            "native-novalidate": "initial_state_unavailable",
            "native-clear-value": "invalid_checkpoint_unavailable",
            "empty-success": "success_checkpoint_unavailable",
            "empty-error": "invalid_checkpoint_unavailable",
            "hidden-child-text": "success_checkpoint_unavailable",
            "child-complex-paint": "form_outcome_contract_unavailable",
            "drift": "replay_unstable",
        }
        for key, reason in expected_reasons.items():
            self.assertEqual(("unavailable", reason), (record(key)["status"], record(key)["reason"]))
        coverage_keys = {"status", "reason", "declaredTargets", "completedTargets", "freshReplays", "claimBoundary"}
        self.assertTrue(all(set(result["coverage"]) == coverage_keys for result in results.values()))
        self.assertTrue(all(result["coverage"]["freshReplays"] == 2 for result in results.values()))
        self.assertTrue(all(
            result["coverage"]["claimBoundary"]
            == "two fresh evaluator-controlled mutually-exclusive visual form outcome replays"
            for result in results.values()
        ))
        for result in results.values():
            item = result["records"][0]
            expected = {"id", "status", "replays", "reason"} if item["status"] == "unavailable" else {
                "id", "status", "replays", "staleSuccess",
            }
            self.assertEqual(expected, set(item))
        serialized = json.dumps(results)
        for secret in (
            "#control", "#success", "#error", "eval-outcome-valid-alpha", "eval-outcome-invalid-alpha",
            "Secret field copy", "Secret success copy", "Secret error copy",
        ):
            self.assertNotIn(secret, serialized)
            self.assertNotIn(secret, completed.stderr)
        self.assertNotIn("screenshot", MODULE.read_text(encoding="utf-8"))

    def test_aggregate_rejects_status_signature_and_boolean_drift(self) -> None:
        source = f"""
const {{ aggregateFormOutcomeResults }} = require({json.dumps(str(MODULE))});
const target = {{ id: 'primary-outcome' }};
const aggregate = (items) => aggregateFormOutcomeResults([target], new Map([['primary-outcome', items]])).records[0];
process.stdout.write(JSON.stringify([
  aggregate([{{status:'clean',staleSuccess:false,signature:'same'}},{{status:'stale',staleSuccess:true,signature:'same'}}]),
  aggregate([{{status:'clean',staleSuccess:false,signature:'first'}},{{status:'clean',staleSuccess:false,signature:'second'}}]),
  aggregate([{{status:'clean',staleSuccess:false,signature:'same'}},{{status:'clean',staleSuccess:true,signature:'same'}}]),
  aggregate([{{status:'unavailable',reason:'runtime_unavailable'}},{{status:'clean',staleSuccess:false,signature:'same'}}]),
]));
"""
        completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True, check=True)
        result = json.loads(completed.stdout)
        self.assertTrue(all(item["status"] == "unavailable" and item["reason"] == "replay_unstable" for item in result))


if __name__ == "__main__":
    unittest.main()
