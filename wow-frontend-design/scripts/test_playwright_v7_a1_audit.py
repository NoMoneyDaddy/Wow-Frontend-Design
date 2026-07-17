#!/usr/bin/env python3
"""Integration tests for the isolated v7-A1 browser auditor."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDITOR = ROOT / "evals" / "playwright_v7_a1_audit.cjs"
FOCUS_AUDITOR = ROOT / "evals" / "v7_focus_obscuration.cjs"
FIXTURE = ROOT / "evals" / "fixtures" / "v7-a1-typography.html"


class PlaywrightV7A1AuditTests(unittest.TestCase):
    def test_profile_inventory_contains_six_distinct_compositions(self) -> None:
        source = f"""
const {{ PROFILES }} = require({json.dumps(str(AUDITOR))});
process.stdout.write(JSON.stringify(PROFILES));
"""
        completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True, check=True)
        profiles = json.loads(completed.stdout)
        self.assertEqual(
            {"desktop", "standard-desktop", "short-desktop", "tablet", "mobile", "compact-mobile"},
            set(profiles),
        )
        self.assertTrue(profiles["mobile"]["isMobile"])
        self.assertTrue(profiles["mobile"]["hasTouch"])
        self.assertEqual(3, profiles["mobile"]["deviceScaleFactor"])

    def test_fixture_produces_hashed_png_and_findings_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = {
                "schemaVersion": 1,
                "caseId": "fixture-case",
                "state": "base",
                "steps": [],
                "assertions": [{"id": "heading-visible", "type": "visible", "selector": "#heading-orphan"}],
                "targets": [{
                    "id": "orphan",
                    "selector": "#heading-orphan",
                    "ownerSelector": "#owner-orphan",
                    "role": "heading",
                    "mode": "product",
                }],
            }
            spec_path = root / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            screenshot = root / "fixture.png"
            output = root / "result.json"
            command = [
                "node", str(AUDITOR),
                "--url", FIXTURE.as_uri(),
                "--variant", "accepted",
                "--case-id", "fixture-case",
                "--state", "base",
                "--profile", "mobile",
                "--engine", "chromium",
                "--spec", str(spec_path),
                "--screenshot", str(screenshot),
                "--output", str(output),
            ]
            completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(2, completed.returncode, completed.stderr)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("findings", result["verdict"])
            self.assertEqual(1, result["schemaVersion"])
            self.assertEqual("accepted", result["identity"]["variant"])
            self.assertIn("page_horizontal_overflow", result["runtime"]["issues"])
            self.assertTrue(all("url" not in item for item in result["runtime"]["externalRequests"]))
            self.assertEqual("a1_heading_han_orphan", result["typography"]["issues"][0]["code"])
            self.assertNotIn("selector", json.dumps(result["runtime"]))
            self.assertNotIn("#heading-orphan", json.dumps(result["runtime"]))
            self.assertTrue(result["browser"]["profile"]["fullMobileEmulation"])
            self.assertEqual(3, result["browser"]["profile"]["deviceScaleFactor"])
            self.assertEqual(1, result["schemaVersion"])
            self.assertNotIn("focusCoverage", result["runtime"])
            self.assertNotIn("focusedControls", result["runtime"])
            self.assertEqual(64, len(result["screenshot"]["sha256"]))
            self.assertGreater(result["screenshot"]["bytes"], 100)
            self.assertEqual(
                result["runtime"]["pageBounds"]["width"] * 3,
                result["screenshot"]["width"],
            )

    def test_non_loopback_network_target_is_rejected(self) -> None:
        source = f"""
const {{ targetUrl }} = require({json.dumps(str(AUDITOR))});
try {{ targetUrl('https://example.com/'); }}
catch (error) {{ process.stdout.write(error.message); process.exit(0); }}
process.exit(1);
"""
        completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, completed.returncode)
        self.assertIn("loopback", completed.stdout)

    def test_interaction_spec_requires_steps_and_assertions(self) -> None:
        contracts = (
            ("steps", [], [{"id": "dialog-visible", "type": "visible", "selector": "#dialog"}]),
            ("assertions", [{"id": "open-dialog", "action": "click", "selector": "#open"}], []),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for label, steps, assertions in contracts:
                with self.subTest(label=label):
                    spec = {
                        "schemaVersion": 1,
                        "caseId": "fixture-case",
                        "state": "interaction",
                        "steps": steps,
                        "assertions": assertions,
                        "targets": [],
                    }
                    spec_path = root / f"{label}.json"
                    spec_path.write_text(json.dumps(spec), encoding="utf-8")
                    source = f"""
const {{ loadSpec }} = require({json.dumps(str(AUDITOR))});
try {{ loadSpec({json.dumps(str(spec_path))}, 'fixture-case', 'interaction'); }}
catch (error) {{ process.stdout.write(error.message); process.exit(0); }}
process.exit(1);
"""
                    completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True)
                    self.assertEqual(0, completed.returncode)
                    self.assertIn(f"spec {label} must contain 1..20 entries", completed.stdout)

    def test_v2_focus_targets_are_strictly_bound_to_compatible_steps(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = {
                "schemaVersion": 2,
                "caseId": "fixture-case",
                "state": "interaction",
                "steps": [{"id": "submit", "action": "press", "selector": "#submit", "value": "Enter"}],
                "assertions": [{"id": "submit-visible", "type": "visible", "selector": "#submit"}],
                "targets": [{"id": "heading", "selector": "#heading", "ownerSelector": "#owner", "role": "heading", "mode": "product"}],
                "focusTargets": [{"id": "primary-submit", "stepId": "submit", "role": "primary-action"}],
            }
            variants = {
                "valid": (base, True),
                "missing-step": ({**base, "focusTargets": [{"id": "primary-submit", "stepId": "missing", "role": "primary-action"}]}, False),
                "wrong-role": ({**base, "focusTargets": [{"id": "primary-submit", "stepId": "submit", "role": "form-control"}]}, False),
                "extra-key": ({**base, "focusTargets": [{"id": "primary-submit", "stepId": "submit", "role": "primary-action", "selector": "#submit"}]}, False),
                "duplicate": ({**base, "focusTargets": [base["focusTargets"][0], base["focusTargets"][0]]}, False),
                "too-many": ({**base, "focusTargets": [base["focusTargets"][0]] * 9}, False),
                "empty": ({**base, "focusTargets": []}, False),
            }
            for label, (spec, accepted) in variants.items():
                with self.subTest(label=label):
                    spec_path = root / f"{label}.json"
                    spec_path.write_text(json.dumps(spec), encoding="utf-8")
                    source = f"""
const {{ loadSpec }} = require({json.dumps(str(AUDITOR))});
try {{ loadSpec({json.dumps(str(spec_path))}, 'fixture-case', 'interaction'); process.exit(0); }}
catch (error) {{ process.stderr.write(error.message); process.exit(1); }}
"""
                    completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True)
                    self.assertEqual(accepted, completed.returncode == 0, completed.stderr)

    def test_fresh_replay_aggregation_fails_closed_when_unstable(self) -> None:
        source = f"""
const {{ aggregateFocusResults }} = require({json.dumps(str(FOCUS_AUDITOR))});
const targets = [{{ id: 'primary-submit', role: 'primary-action' }}];
const stable = aggregateFocusResults(targets, new Map([['primary-submit', [
  {{ status: 'obscured', occluderCount: 1, targetArea: 1200, coveredArea: 1200 }},
  {{ status: 'obscured', occluderCount: 1, targetArea: 1200, coveredArea: 1200 }},
]]]));
const stableClear = aggregateFocusResults(targets, new Map([['primary-submit', [
  {{ status: 'clear', occluderCount: 1, targetArea: 1200, coveredArea: 600 }},
  {{ status: 'clear', occluderCount: 1, targetArea: 1200, coveredArea: 600 }},
]]]));
const unstable = aggregateFocusResults(targets, new Map([['primary-submit', [
  {{ status: 'obscured', occluderCount: 1, targetArea: 1200, coveredArea: 1200 }},
  {{ status: 'clear', occluderCount: 0, targetArea: 1200, coveredArea: 0 }},
]]]));
const unstableGeometry = aggregateFocusResults(targets, new Map([['primary-submit', [
  {{ status: 'obscured', occluderCount: 1, targetArea: 1200, coveredArea: 1200 }},
  {{ status: 'obscured', occluderCount: 1, targetArea: 1400, coveredArea: 1400 }},
]]]));
process.stdout.write(JSON.stringify({{ stable, stableClear, unstable, unstableGeometry }}));
"""
        completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True, check=True)
        result = json.loads(completed.stdout)
        self.assertEqual("confirmed", result["stable"]["focusedControls"][0]["status"])
        self.assertTrue(result["stable"]["focusedControls"][0]["fullyObscured"])
        self.assertEqual("clear", result["stableClear"]["focusedControls"][0]["status"])
        self.assertEqual(1200, result["stableClear"]["focusedControls"][0]["targetArea"])
        self.assertEqual(600, result["stableClear"]["focusedControls"][0]["coveredArea"])
        self.assertEqual("unavailable", result["unstable"]["focusCoverage"]["status"])
        self.assertEqual("unstable_fresh_replay", result["unstable"]["focusedControls"][0]["reason"])
        self.assertEqual("unavailable", result["unstableGeometry"]["focusCoverage"]["status"])
        self.assertEqual("unstable_fresh_replay_geometry", result["unstableGeometry"]["focusedControls"][0]["reason"])

    def test_geometry_classifier_fails_closed_for_non_simple_coverage(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ inspectFocusedControl }} = require({json.dumps(str(FOCUS_AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const cases = {{
    full: '#cover{{left:0;width:220px;background:rgb(20,30,40);z-index:3}}',
    partial: '#cover{{left:0;width:100px;background:rgb(20,30,40);z-index:3}}',
    transparent: '#cover{{left:0;width:220px;background:rgba(20,30,40,.5);z-index:3}}',
    behind: '#cover{{left:0;width:220px;background:rgb(20,30,40);z-index:0}}#target{{z-index:2}}',
    transformed: '#cover{{left:0;width:220px;background:rgb(20,30,40);z-index:3;transform:translateX(0)}}',
    legacyClip: '#cover{{left:0;width:220px;background:rgb(20,30,40);z-index:3;clip:rect(0px,190px,48px,0px)}}',
    blended: '#cover{{left:0;width:220px;background:rgb(20,30,40);z-index:3;mix-blend-mode:multiply}}',
    clippedBackground: '#cover{{box-sizing:border-box;left:0;width:220px;padding:10px;background:rgb(20,30,40);background-clip:content-box;z-index:3}}',
    individualTransform: '#cover{{left:0;width:220px;background:rgb(20,30,40);z-index:3;translate:0px}}',
  }};
  const results = {{}};
  for (const [name, extra] of Object.entries(cases)) {{
    const page = await browser.newPage({{ viewport: {{ width: 500, height: 300 }} }});
    await page.setContent(`<style>
      #target{{position:absolute;left:20px;top:20px;width:200px;height:48px}}
      #cover{{position:fixed;top:20px;height:48px}}${{extra}}
    </style><button id=target>Target</button><div id=cover></div>`);
    await page.locator('#target').focus();
    results[name] = await inspectFocusedControl(page, '#target');
    await page.close();
  }}
  const ancestorPage = await browser.newPage({{ viewport: {{ width: 500, height: 300 }} }});
  await ancestorPage.setContent(`<style>
    #target{{position:absolute;left:20px;top:20px;width:200px;height:48px}}
    #shell{{opacity:.5}}#cover{{position:fixed;left:0;top:20px;width:220px;height:48px;background:rgb(20,30,40);z-index:3}}
  </style><button id=target>Target</button><div id=shell><div id=cover></div></div>`);
  await ancestorPage.locator('#target').focus();
  results.ancestorOpacity = await inspectFocusedControl(ancestorPage, '#target');
  await ancestorPage.close();
  await browser.close();
  process.stdout.write(JSON.stringify(results));
}})().catch((error) => {{ console.error(error); process.exit(1); }});
"""
        completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True, check=True)
        results = json.loads(completed.stdout)
        self.assertEqual("obscured", results["full"]["status"])
        self.assertEqual("clear", results["partial"]["status"])
        self.assertEqual("unavailable", results["transparent"]["status"])
        self.assertEqual("clear", results["behind"]["status"])
        self.assertEqual("unavailable", results["transformed"]["status"])
        self.assertEqual("unavailable", results["legacyClip"]["status"])
        self.assertEqual("unavailable", results["blended"]["status"])
        self.assertEqual("unavailable", results["clippedBackground"]["status"])
        self.assertEqual("unavailable", results["individualTransform"]["status"])
        self.assertEqual("unavailable", results["ancestorOpacity"]["status"])

    def test_focus_replay_with_external_request_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "external-focus.html"
            page.write_text("""<!doctype html><button id=submit>Submit</button><script>
document.querySelector('#submit').addEventListener('focus', () => {
  fetch('https://example.invalid/focus-probe').catch(() => {});
});
</script>""", encoding="utf-8")
            source = f"""
const {{ chromium }} = require('playwright');
const {{ replayFocusTarget }} = require({json.dumps(str(FOCUS_AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const result = await replayFocusTarget(browser, new URL({json.dumps(page.as_uri())}), {{
    viewport: {{ width: 500, height: 300 }},
    screen: {{ width: 500, height: 300 }},
    deviceScaleFactor: 1,
    hasTouch: false,
    isMobile: false,
    serviceWorkers: 'block',
    locale: 'zh-TW',
    timezoneId: 'Asia/Taipei',
  }}, {{ id: 'primary-submit', stepId: 'submit', role: 'primary-action' }}, [
    {{ id: 'submit', action: 'press', selector: '#submit', value: 'Enter' }},
  ]);
  await browser.close();
  process.stdout.write(JSON.stringify(result));
}})().catch((error) => {{ console.error(error); process.exit(1); }});
"""
            completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True, check=True)
            result = json.loads(completed.stdout)
            self.assertEqual("unavailable", result["status"])
            self.assertEqual("external_request_blocked", result["reason"])

    def test_focus_geometry_budgets_fail_closed(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ inspectFocusedControl }} = require({json.dumps(str(FOCUS_AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage({{ viewport: {{ width: 500, height: 300 }} }});
  const inspect = async (markup) => {{
    await page.setContent(`<style>
      #target{{position:absolute;left:0;top:0;width:200px;height:100px;z-index:1}}
      .cover{{position:fixed;background:rgb(20,30,40);z-index:3}}
    </style>${{markup}}`);
    await page.locator('#target').focus();
    return inspectFocusedControl(page, '#target');
  }};
  const dom = await inspect(`<button id=target>Target</button><div class=cover style="left:0;top:0;width:200px;height:100px"></div>${{'<i></i>'.repeat(2001)}}`);
  const occluders = await inspect(`<button id=target>Target</button>${{Array.from({{length:13}}, (_, i) => `<div class=cover style="left:${{i}}px;top:0;width:200px;height:100px"></div>`).join('')}}`);
  const vertical = Array.from({{length:6}}, (_, i) => `<div class=cover style="left:${{10 + i * 30}}px;top:0;width:10px;height:100px"></div>`).join('');
  const horizontal = Array.from({{length:6}}, (_, i) => `<div class=cover style="left:0;top:${{5 + i * 15}}px;width:200px;height:5px"></div>`).join('');
  const partition = await inspect(`<button id=target>Target</button>${{vertical}}${{horizontal}}`);
  await browser.close();
  process.stdout.write(JSON.stringify({{ dom, occluders, partition }}));
}})().catch((error) => {{ console.error(error); process.exit(1); }});
"""
        completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True, check=True)
        results = json.loads(completed.stdout)
        self.assertEqual("dom_budget_exceeded", results["dom"]["reason"])
        self.assertEqual("occluder_budget_exceeded", results["occluders"]["reason"])
        self.assertEqual("partition_budget_exceeded", results["partition"]["reason"])

    def test_v2_reports_fully_obscured_programmatic_focus_with_one_screenshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / "focus.html"
            page.write_text("""<!doctype html><html><head><style>
body{margin:0}#secret-submit-selector{position:absolute;left:40px;top:40px;width:160px;height:48px;z-index:1}
#prefix-field{position:absolute;left:40px;top:220px}#suffix-action{position:absolute;left:40px;top:280px}
#cover{position:fixed;left:0;top:0;width:100%;height:180px;background:rgb(20,30,40);z-index:10}
</style></head><body><main id=owner><h1 id=heading>Focus fixture</h1>
<button id=secret-submit-selector>DO-NOT-LEAK-PRODUCT-COPY</button><input id=prefix-field>
<button id=suffix-action>Suffix</button></main><div id=cover></div></body></html>""", encoding="utf-8")
            spec = {
                "schemaVersion": 2,
                "caseId": "focus-case",
                "state": "interaction",
                "steps": [
                    {"id": "prepare-field", "action": "fill", "selector": "#prefix-field", "value": "prepared"},
                    {"id": "blocked-submit", "action": "click", "selector": "#secret-submit-selector"},
                    {"id": "suffix-action", "action": "click", "selector": "#suffix-action"},
                ],
                "assertions": [
                    {"id": "submit-visible", "type": "visible", "selector": "#secret-submit-selector"},
                    {"id": "secret-copy", "type": "text", "selector": "#secret-submit-selector", "value": "DO-NOT-LEAK-PRODUCT-COPY"},
                ],
                "targets": [{"id": "heading", "selector": "#heading", "ownerSelector": "#owner", "role": "heading", "mode": "product"}],
                "focusTargets": [{"id": "primary-submit", "stepId": "blocked-submit", "role": "primary-action"}],
            }
            spec_path = root / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            screenshot = root / "focus.png"
            output = root / "result.json"
            completed = subprocess.run([
                "node", str(AUDITOR), "--url", page.as_uri(), "--variant", "candidate",
                "--case-id", "focus-case", "--state", "interaction", "--profile", "desktop",
                "--engine", "chromium", "--spec", str(spec_path), "--screenshot", str(screenshot),
                "--output", str(output),
            ], cwd=ROOT, text=True, capture_output=True)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(2, completed.returncode, json.dumps(result["runtime"], indent=2))
            self.assertEqual(3, result["schemaVersion"])
            self.assertIn("focused_control_obscured", result["runtime"]["issues"])
            self.assertEqual("complete", result["runtime"]["focusCoverage"]["status"])
            self.assertEqual(2, result["runtime"]["focusCoverage"]["freshReplays"])
            self.assertEqual("confirmed", result["runtime"]["focusedControls"][0]["status"])
            self.assertEqual("blocked-submit", result["runtime"]["focusedControls"][0]["stepId"])
            self.assertEqual([
                {"id": "prepare-field", "action": "fill", "completed": True},
                {"id": "blocked-submit", "action": "click", "completed": False, "reason": "focused_control_obscured"},
                {"id": "suffix-action", "action": "click", "completed": False, "reason": "prior_step_not_completed"},
            ], result["runtime"]["interactions"])
            self.assertEqual([
                {"id": "submit-visible", "type": "visible", "evaluated": False, "reason": "interaction_state_unavailable"},
                {"id": "secret-copy", "type": "text", "evaluated": False, "reason": "interaction_state_unavailable"},
            ], result["runtime"]["assertions"])
            serialized = json.dumps(result)
            self.assertNotIn("#secret-submit-selector", serialized)
            self.assertNotIn("DO-NOT-LEAK-PRODUCT-COPY", serialized)
            self.assertNotIn("#secret-submit-selector", completed.stderr)
            self.assertNotIn("DO-NOT-LEAK-PRODUCT-COPY", completed.stderr)
            self.assertEqual([screenshot], list(root.glob("*.png")))

    def test_v2_non_click_obscuration_keeps_exact_result_schema_2(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / "press.html"
            page.write_text("""<!doctype html><style>
#submit{position:absolute;left:40px;top:40px;width:160px;height:48px}#cover{position:fixed;inset:0 0 auto 0;height:180px;background:rgb(20,30,40);z-index:10}
</style><main id=owner><h1 id=heading>Fixture</h1><button id=submit>Submit</button></main><div id=cover></div>""", encoding="utf-8")
            spec = {
                "schemaVersion": 2, "caseId": "press-case", "state": "interaction",
                "steps": [{"id": "submit", "action": "press", "selector": "#submit", "value": "Enter"}],
                "assertions": [{"id": "submit-visible", "type": "visible", "selector": "#submit"}],
                "targets": [{"id": "heading", "selector": "#heading", "ownerSelector": "#owner", "role": "heading", "mode": "product"}],
                "focusTargets": [{"id": "primary-submit", "stepId": "submit", "role": "primary-action"}],
            }
            spec_path = root / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            screenshot = root / "press.png"
            output = root / "result.json"
            completed = subprocess.run([
                "node", str(AUDITOR), "--url", page.as_uri(), "--variant", "candidate",
                "--case-id", "press-case", "--state", "interaction", "--profile", "desktop",
                "--engine", "chromium", "--spec", str(spec_path), "--screenshot", str(screenshot), "--output", str(output),
            ], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(2, completed.returncode, completed.stderr)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(2, result["schemaVersion"])
            self.assertEqual({"id": "submit", "action": "press", "completed": True}, result["runtime"]["interactions"][0])
            self.assertNotIn("stepId", result["runtime"]["focusedControls"][0])
            self.assertEqual([screenshot], list(root.glob("*.png")))


if __name__ == "__main__":
    unittest.main()
