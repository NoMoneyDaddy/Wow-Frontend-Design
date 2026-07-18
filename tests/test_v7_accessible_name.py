#!/usr/bin/env python3
"""Playwright-backed tests for native-control accessible-name replay."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "evals" / "v7_accessible_name.cjs"
FIXTURE = ROOT / "evals" / "fixtures" / "v7-accessible-name.html"


class V7AccessibleNameTests(unittest.TestCase):
    def test_target_contract_requires_unique_form_control_references(self) -> None:
        source = f"""
const {{ validateAccessibleNameTargets }} = require({json.dumps(str(MODULE))});
const focus = [{{ id: 'field-focus', stepId: 'fill-field', role: 'form-control' }}];
const cases = JSON.parse(process.argv[1]);
const results = cases.map((value) => {{
  try {{ validateAccessibleNameTargets(value, focus); return 'accepted'; }}
  catch {{ return 'rejected'; }}
}});
process.stdout.write(JSON.stringify(results));
"""
        valid = {"id": "field-name", "focusTargetId": "field-focus", "expectedRole": "textbox", "expectedName": "Secret label"}
        cases = [
            [valid],
            [{**valid, "selector": "#forbidden"}],
            [{**valid, "focusTargetId": "missing"}],
            [{**valid, "expectedRole": "dialog"}],
            [valid, {**valid, "id": "second-name"}],
        ]
        completed = subprocess.run(
            ["node", "-e", source, json.dumps(cases)], cwd=ROOT, text=True, capture_output=True, check=True,
        )
        self.assertEqual(["accepted", "rejected", "rejected", "rejected", "rejected"], json.loads(completed.stdout))

    def test_two_fresh_contexts_classify_native_controls_without_name_leakage(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ auditAccessibleNames }} = require({json.dumps(str(MODULE))});
const fixture = new URL({json.dumps(FIXTURE.as_uri())});
const cases = JSON.parse(process.argv[1]);
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const results = {{}};
  for (const item of cases) {{
    const url = item.external ? new URL(`${{fixture.href}}?external=1`) : fixture;
    results[item.key] = (await auditAccessibleNames(browser, url, {{ viewport: {{ width: 800, height: 600 }} }}, item.spec)).accessibleNameControls[0];
  }}
  await browser.close();
  process.stdout.write(JSON.stringify(results));
}})().catch(() => {{ console.error('fixed-test-failure'); process.exit(1); }});
"""

        def case(key: str, selector: str, expected_role: str, expected_name: str, *, prefix: bool = False) -> dict:
            steps = []
            if prefix:
                steps.append({"id": "reveal-field", "action": "click", "selector": "#reveal"})
            steps.append({"id": "target-step", "action": "fill", "selector": selector, "value": "fixture"})
            return {
                "key": key,
                "spec": {
                    "steps": steps,
                    "focusTargets": [{"id": "field-focus", "stepId": "target-step", "role": "form-control"}],
                    "accessibleNameTargets": [{
                        "id": f"{key}-name", "focusTargetId": "field-focus",
                        "expectedRole": expected_role, "expectedName": expected_name,
                    }],
                },
            }

        cases = [
            case("named", "#named-input", "textbox", "Account secret label", prefix=True),
            case("unnamed", "#unnamed-input", "textbox", "Expected secret name"),
            case("overridden", "#overridden-input", "textbox", "Visible account label"),
            case("role-drift", "#role-drift-input", "textbox", "Role drift label"),
            case("duplicate", "#duplicate-one", "textbox", "Duplicate secret label"),
            case("password", "#password-input", "textbox", "Password secret label"),
            case("hidden", "#hidden-input", "textbox", "Hidden secret label"),
            case("textarea", "#notes", "textbox", "Notes secret label"),
            case("select", "#choice", "combobox", "Choice secret label"),
            case("color", "#color-input", "textbox", "Color secret label"),
        ]
        external = case("external", "#unnamed-input", "textbox", "Expected secret name")
        external["external"] = True
        cases.append(external)
        completed = subprocess.run(
            ["node", "-e", source, json.dumps(cases)], cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        results = json.loads(completed.stdout)
        self.assertEqual("clear", results["named"]["status"])
        self.assertEqual("confirmed", results["unnamed"]["status"])
        self.assertEqual("confirmed", results["overridden"]["status"])
        self.assertEqual("accessibility_tree_unavailable", results["role-drift"]["reason"])
        self.assertEqual("accessibility_tree_unavailable", results["duplicate"]["reason"])
        self.assertEqual("accessibility_tree_unavailable", results["password"]["reason"])
        self.assertEqual("control_not_rendered", results["hidden"]["reason"])
        self.assertEqual("clear", results["textarea"]["status"])
        self.assertEqual("clear", results["select"]["status"])
        self.assertEqual("accessibility_tree_unavailable", results["color"]["reason"])
        self.assertEqual("external_request_blocked", results["external"]["reason"])
        self.assertTrue(all(item["replays"] == 2 for item in results.values()))
        self.assertTrue(all(
            set(item) == ({"id", "role", "status", "replays", "reason"} if item["status"] == "unavailable"
                          else {"id", "role", "status", "replays"})
            for item in results.values()
        ))
        serialized = json.dumps(results)
        for secret in (
            "Account secret label", "Expected secret name", "Visible account label", "Wrong account label",
            "Role drift label", "#named-input", "Duplicate secret label",
        ):
            self.assertNotIn(secret, serialized)
            self.assertNotIn(secret, completed.stderr)
        self.assertNotIn("screenshot", MODULE.read_text(encoding="utf-8"))

    def test_mixed_and_native_signature_drift_fail_closed(self) -> None:
        source = f"""
const {{ aggregateAccessibleNameResults }} = require({json.dumps(str(MODULE))});
const target = {{ id: 'field-name', expectedRole: 'textbox' }};
const aggregate = (items) => aggregateAccessibleNameResults([target], new Map([['field-name', items]]))[0];
process.stdout.write(JSON.stringify({{
  mixed: aggregate([{{status:'match',signature:'input:text:textbox'}},{{status:'miss',signature:'input:text:textbox'}}]),
  drift: aggregate([{{status:'match',signature:'input:text:textbox'}},{{status:'match',signature:'textarea:textbox'}}]),
}}));
"""
        completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True, check=True)
        result = json.loads(completed.stdout)
        self.assertEqual(("unavailable", "replay_unstable"), (result["mixed"]["status"], result["mixed"]["reason"]))
        self.assertEqual(("unavailable", "replay_unstable"), (result["drift"]["status"], result["drift"]["reason"]))


if __name__ == "__main__":
    unittest.main()
