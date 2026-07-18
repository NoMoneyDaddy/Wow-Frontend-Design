#!/usr/bin/env python3
"""Playwright-backed tests for declared disclosure state replay."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "evals" / "v7_disclosure_state.cjs"
FIXTURE = ROOT / "evals" / "fixtures" / "v7-disclosure-state.html"


class V7DisclosureStateTests(unittest.TestCase):
    def test_contract_is_exact_and_press_is_bounded(self) -> None:
        source = f"""
const {{ validateDisclosureTargets }} = require({json.dumps(str(MODULE))});
const steps = JSON.parse(process.argv[1]);
const cases = JSON.parse(process.argv[2]);
process.stdout.write(JSON.stringify(cases.map((item) => {{
  try {{ validateDisclosureTargets(item, steps); return 'accepted'; }}
  catch {{ return 'rejected'; }}
}})));
"""
        steps = [
            {"id": "toggle-click", "action": "click", "selector": "#toggle"},
            {"id": "toggle-enter", "action": "press", "selector": "#toggle", "value": "Enter"},
            {"id": "toggle-escape", "action": "press", "selector": "#toggle", "value": "Escape"},
        ]
        target = {
            "id": "primary-disclosure",
            "actionStepId": "toggle-click",
            "panelSelector": "#panel",
            "settling": "reduced-motion-static",
        }
        cases = [
            [target],
            [{**target, "copy": "forbidden"}],
            [{key: value for key, value in target.items() if key != "settling"}],
            [{**target, "settling": "eventual"}],
            [{**target, "actionStepId": "missing"}],
            [{**target, "actionStepId": "toggle-enter"}],
            [{**target, "actionStepId": "toggle-escape"}],
            [target, {**target, "id": "second-disclosure"}],
        ]
        completed = subprocess.run(
            ["node", "-e", source, json.dumps(steps), json.dumps(cases)],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        self.assertEqual(
            ["accepted", "rejected", "rejected", "rejected", "rejected", "accepted", "rejected", "rejected"],
            json.loads(completed.stdout),
        )

    def test_two_fresh_replays_classify_state_and_fail_closed_structure(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ auditDisclosureTargets }} = require({json.dumps(str(MODULE))});
const base = new URL({json.dumps(FIXTURE.as_uri())});
const cases = JSON.parse(process.argv[1]);
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const results = {{}};
  for (const item of cases) {{
    const url = new URL(`${{base.href}}?mode=${{item.mode}}`);
    results[item.key] = await auditDisclosureTargets(browser, url, {{ viewport: {{ width: 800, height: 600 }} }}, item.spec);
  }}
  await browser.close();
  process.stdout.write(JSON.stringify(results));
}})().catch(() => {{ console.error('fixed-test-failure'); process.exit(1); }});
"""

        def case(key: str, mode: str, *, press: bool = False) -> dict:
            step = {"id": "toggle-step", "action": "press" if press else "click", "selector": "#toggle"}
            if press:
                step["value"] = "Enter"
            return {
                "key": key,
                "mode": mode,
                "spec": {
                    "steps": [step],
                    "disclosureTargets": [{
                        "id": f"{key}-disclosure",
                        "actionStepId": "toggle-step",
                        "panelSelector": "#panel",
                        "settling": "reduced-motion-static",
                    }],
                },
            }

        cases = [
            case("correct", "correct"),
            case("shadow-decoy", "shadow-decoy"),
            case("press", "correct", press=True),
            case("display-contents", "display-contents"),
            case("visual-only", "visual-only"),
            case("aria-only", "aria-only"),
            case("opacity0", "opacity0"),
            case("noop", "noop"),
            case("animated", "animated"),
            case("ancestor-waapi", "ancestor-waapi"),
            case("ancestor-css", "ancestor-css"),
            case("filter-opacity0", "filter-opacity0"),
            case("clip-hidden", "clip-hidden"),
            case("role-link", "role-link"),
            case("disabled", "disabled"),
            case("initial-bad", "initial-bad"),
            case("unsupported", "unsupported"),
            case("shadow", "shadow"),
            case("external", "external"),
        ]
        completed = subprocess.run(
            ["node", "-e", source, json.dumps(cases)], cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        results = json.loads(completed.stdout)
        record = lambda key: results[key]["records"][0]
        for key in ("correct", "shadow-decoy", "press", "display-contents"):
            self.assertEqual(("clear", True, True), (
                record(key)["status"], record(key)["expanded"], record(key)["panelVisible"],
            ))
        self.assertEqual(("confirmed", False, True), (
            record("visual-only")["status"], record("visual-only")["expanded"], record("visual-only")["panelVisible"],
        ))
        self.assertEqual(("confirmed", True, False), (
            record("aria-only")["status"], record("aria-only")["expanded"], record("aria-only")["panelVisible"],
        ))
        self.assertEqual(("confirmed", True, False), (
            record("opacity0")["status"], record("opacity0")["expanded"], record("opacity0")["panelVisible"],
        ))
        self.assertEqual(("unavailable", "action_outcome_unavailable"), (
            record("noop")["status"], record("noop")["reason"],
        ))
        for key in ("animated", "ancestor-waapi", "ancestor-css"):
            self.assertEqual(("unavailable", "state_settling_unavailable"), (
                record(key)["status"], record(key)["reason"],
            ))
        for key in ("filter-opacity0", "clip-hidden"):
            self.assertEqual(("unavailable", "disclosure_contract_unavailable"), (
                record(key)["status"], record(key)["reason"],
            ))
        self.assertEqual(("unavailable", "initial_state_unavailable"), (
            record("initial-bad")["status"], record("initial-bad")["reason"],
        ))
        for key in ("unsupported", "shadow", "role-link", "disabled"):
            self.assertEqual(("unavailable", "initial_state_unavailable"), (record(key)["status"], record(key)["reason"]))
        self.assertEqual(("unavailable", "external_request_blocked"), (
            record("external")["status"], record("external")["reason"],
        ))
        expected_coverage = {"status", "reason", "declaredTargets", "completedTargets", "freshReplays", "claimBoundary"}
        self.assertTrue(all(set(result["coverage"]) == expected_coverage for result in results.values()))
        self.assertTrue(all(result["coverage"]["freshReplays"] == 2 for result in results.values()))
        for result in results.values():
            item = result["records"][0]
            expected = {"id", "status", "replays", "reason"} if item["status"] == "unavailable" else {
                "id", "status", "replays", "expanded", "panelVisible",
            }
            self.assertEqual(expected, set(item))
        serialized = json.dumps(results)
        for secret in ("#toggle", "#panel", "Secret disclosure copy", "Secret panel copy"):
            self.assertNotIn(secret, serialized)
            self.assertNotIn(secret, completed.stderr)
        self.assertNotIn("screenshot", MODULE.read_text(encoding="utf-8"))

    def test_status_signature_and_mismatch_drift_are_unavailable(self) -> None:
        source = f"""
const {{ aggregateDisclosureResults }} = require({json.dumps(str(MODULE))});
const target = {{ id: 'primary-disclosure' }};
const aggregate = (items) => aggregateDisclosureResults([target], new Map([['primary-disclosure', items]])).records[0];
process.stdout.write(JSON.stringify({{
  status: aggregate([{{status:'match',expanded:true,panelVisible:true,signature:'same'}},{{status:'mismatch',expanded:false,panelVisible:true,signature:'same'}}]),
  signature: aggregate([{{status:'match',expanded:true,panelVisible:true,signature:'first'}},{{status:'match',expanded:true,panelVisible:true,signature:'second'}}]),
  mismatch: aggregate([{{status:'mismatch',expanded:false,panelVisible:true,signature:'same'}},{{status:'mismatch',expanded:true,panelVisible:false,signature:'same'}}]),
  unavailable: aggregate([{{status:'unavailable',reason:'external_request_blocked'}},{{status:'match',expanded:true,panelVisible:true,signature:'same'}}]),
}}));
"""
        completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True, check=True)
        result = json.loads(completed.stdout)
        self.assertTrue(all(item["status"] == "unavailable" and item["reason"] == "replay_unstable" for item in result.values()))


if __name__ == "__main__":
    unittest.main()
