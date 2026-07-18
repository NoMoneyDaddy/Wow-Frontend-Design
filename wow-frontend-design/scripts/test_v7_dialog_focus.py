#!/usr/bin/env python3
"""Playwright-backed tests for bounded dialog focus lifecycle replay."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "evals" / "v7_dialog_focus.cjs"
FIXTURE = ROOT / "evals" / "fixtures" / "v7-dialog-focus.html"


STEPS = [
    {"id": "open-dialog", "action": "click", "selector": "#open-dialog"},
    {"id": "prepare-dialog", "action": "fill", "selector": "#middle-field", "value": "prepared"},
    {"id": "close-dialog", "action": "click", "selector": "#close-dialog"},
]
LIFECYCLE = {
    "id": "primary-dialog",
    "dialogSelector": "#dialog",
    "openStepId": "open-dialog",
    "openFocusSelector": "#first-focus",
    "closeStepId": "close-dialog",
    "returnFocusSelector": "#open-dialog",
}


class V7DialogFocusTests(unittest.TestCase):
    def test_contract_is_exact_and_open_close_steps_are_ordered_actions(self) -> None:
        source = f"""
const {{ validateDialogFocusLifecycles }} = require({json.dumps(str(MODULE))});
const steps = JSON.parse(process.argv[1]);
const cases = JSON.parse(process.argv[2]);
process.stdout.write(JSON.stringify(cases.map((item) => {{
  try {{ validateDialogFocusLifecycles(item, steps); return 'accepted'; }}
  catch {{ return 'rejected'; }}
}})));
"""
        cases = [
            [LIFECYCLE],
            [{**LIFECYCLE, "name": "forbidden"}],
            [{**LIFECYCLE, "openStepId": "missing"}],
            [{**LIFECYCLE, "openStepId": "close-dialog", "closeStepId": "open-dialog"}],
            [LIFECYCLE, {**LIFECYCLE}],
        ]
        completed = subprocess.run(
            ["node", "-e", source, json.dumps(STEPS), json.dumps(cases)],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        self.assertEqual(["accepted", "rejected", "rejected", "rejected", "rejected"], json.loads(completed.stdout))

    def test_fresh_replays_cover_focus_mismatches_structural_failures_and_close_modes(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ auditDialogFocusLifecycles }} = require({json.dumps(str(MODULE))});
const base = new URL({json.dumps(FIXTURE.as_uri())});
const steps = JSON.parse(process.argv[1]);
const lifecycleSource = JSON.parse(process.argv[2]);
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const results = {{}};
  for (const mode of ['clear','open-mismatch','return-mismatch','invalid-role','invalid-modal','invalid-descendant','hidden-target','title-declaration','title-focus','shadow-return','detached','not-closed','external']) {{
    const lifecycle = JSON.parse(JSON.stringify(lifecycleSource));
    if (mode === 'invalid-descendant') lifecycle.openFocusSelector = '#outside-focus';
    if (mode === 'title-declaration' || mode === 'title-focus') lifecycle.openFocusSelector = '#dialog-title';
    if (mode === 'shadow-return') lifecycle.returnFocusSelector = '#shadow-return';
    const url = new URL(`${{base.href}}?mode=${{mode}}`);
    results[mode] = await auditDialogFocusLifecycles(browser, url, {{ viewport: {{ width: 800, height: 600 }} }}, {{ steps, dialogFocusLifecycles: [lifecycle] }});
  }}
  await browser.close();
  process.stdout.write(JSON.stringify(results));
}})().catch(() => {{ console.error('fixed-test-failure'); process.exit(1); }});
"""
        completed = subprocess.run(
            ["node", "-e", source, json.dumps(STEPS), json.dumps(LIFECYCLE)],
            cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        results = json.loads(completed.stdout)
        record = lambda mode: results[mode]["dialogFocusLifecycles"][0]
        self.assertEqual(("clear", True, True), (
            record("clear")["status"], record("clear")["openFocus"], record("clear")["returnFocus"],
        ))
        self.assertEqual(("confirmed", False, True), (
            record("open-mismatch")["status"], record("open-mismatch")["openFocus"], record("open-mismatch")["returnFocus"],
        ))
        self.assertEqual(("confirmed", True, False), (
            record("return-mismatch")["status"], record("return-mismatch")["openFocus"], record("return-mismatch")["returnFocus"],
        ))
        expected_reasons = {
            "invalid-role": "dialog_contract_unavailable",
            "invalid-modal": "dialog_contract_unavailable",
            "invalid-descendant": "dialog_contract_unavailable",
            "hidden-target": "dialog_contract_unavailable",
            "not-closed": "dialog_contract_unavailable",
            "title-declaration": "dialog_contract_unavailable",
            "shadow-return": "dialog_contract_unavailable",
            "external": "external_request_blocked",
        }
        for mode, reason in expected_reasons.items():
            with self.subTest(mode=mode):
                self.assertEqual(("unavailable", reason), (record(mode)["status"], record(mode)["reason"]))
        self.assertEqual("clear", record("detached")["status"])
        self.assertEqual("clear", record("title-focus")["status"])
        self.assertTrue(all(result["dialogFocusCoverage"]["freshReplays"] == 2 for result in results.values()))
        for result in results.values():
            for item in result["dialogFocusLifecycles"]:
                expected = {"id", "status", "replays", "reason"} if item["status"] == "unavailable" else {
                    "id", "status", "replays", "openFocus", "returnFocus",
                }
                self.assertEqual(expected, set(item))
        serialized = json.dumps(results)
        for secret in (
            "#dialog", "#first-focus", "#dialog-title", "#shadow-return",
            "Open secret dialog", "Secret dialog title", "Secret shadow return", "prepared",
        ):
            self.assertNotIn(secret, serialized)
            self.assertNotIn(secret, completed.stderr)
        self.assertNotIn("screenshot", MODULE.read_text(encoding="utf-8"))

    def test_mixed_and_mismatch_signature_drift_are_unavailable(self) -> None:
        source = f"""
const {{ aggregateDialogFocusResults }} = require({json.dumps(str(MODULE))});
const lifecycle = {{ id: 'primary-dialog' }};
const aggregate = (items) => aggregateDialogFocusResults([lifecycle], new Map([['primary-dialog', items]])).dialogFocusLifecycles[0];
process.stdout.write(JSON.stringify({{
  mixed: aggregate([{{status:'match',openFocus:true,returnFocus:true,signature:'open-match:return-match'}},{{status:'mismatch',openFocus:false,returnFocus:true,signature:'open-mismatch:return-match'}}]),
  drift: aggregate([{{status:'mismatch',openFocus:false,returnFocus:true,signature:'open-mismatch:return-match'}},{{status:'mismatch',openFocus:true,returnFocus:false,signature:'open-match:return-mismatch'}}]),
}}));
"""
        completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True, check=True)
        result = json.loads(completed.stdout)
        self.assertEqual(("unavailable", "replay_unstable"), (result["mixed"]["status"], result["mixed"]["reason"]))
        self.assertEqual(("unavailable", "replay_unstable"), (result["drift"]["status"], result["drift"]["reason"]))


if __name__ == "__main__":
    unittest.main()
