#!/usr/bin/env python3
"""Regression tests for the generic public-Playwright fresh-output smoke gate."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "evals" / "playwright_html_smoke.cjs"


class PlaywrightHtmlSmokeTests(unittest.TestCase):
    def invoke(self, stage: Path, pages: list[str], outputs: list[str], contract: dict | None = None) -> dict:
        command = ["node", str(SMOKE), str(stage), json.dumps(pages), json.dumps(outputs)]
        if contract is not None:
            command.append(json.dumps(contract))
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)

    def test_browser_contract_rejects_mobile_task_below_first_viewport_without_autoscroll(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="en"><head><title>Fold</title></head><body>
<main><h1>Task</h1><div style="height:850px"></div><button id="primary">Continue</button></main>
</body></html>''',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 1,
                "cases": [{
                    "id": "mobile-primary-task",
                    "page": "index.html",
                    "profile": "mobile",
                    "steps": [{
                        "id": "primary-in-first-viewport",
                        "action": "assert",
                        "selector": "#primary",
                        "expect": "fully-visible-in-viewport",
                    }],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            self.assertEqual("rejected", receipt["status"])
            desktop = next(item for item in receipt["results"] if item["profile"] == "desktop")
            mobile = next(item for item in receipt["results"] if item["profile"] == "mobile")
            self.assertEqual("passed", desktop["status"])
            self.assertEqual("rejected", mobile["status"])
            self.assertEqual(
                ["contract-mobile-primary-task-primary-in-first-viewport"],
                mobile["inspection"]["browser_contract"]["finding_ids"],
            )

    def test_browser_contract_rejects_viewport_element_clipped_by_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="en"><head><title>Clip</title><style>
.clip { height: 32px; overflow: hidden; }
#primary { height: 64px; }
</style></head><body><main><h1>Task</h1><div class="clip"><button id="primary">Continue</button></div></main></body></html>''',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 1,
                "cases": [{
                    "id": "mobile-primary-task",
                    "page": "index.html",
                    "profile": "mobile",
                    "steps": [{
                        "id": "primary-fully-visible",
                        "action": "assert",
                        "selector": "#primary",
                        "expect": "fully-visible-in-viewport",
                    }],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            mobile = next(item for item in receipt["results"] if item["profile"] == "mobile")
            self.assertEqual("rejected", mobile["status"])
            self.assertEqual(
                ["contract-mobile-primary-task-primary-fully-visible"],
                mobile["inspection"]["browser_contract"]["finding_ids"],
            )

    def test_browser_contract_rejects_subpixel_ancestor_clipping(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="en"><head><title>Clip</title><style>
.clip { width: 299.8px; overflow: hidden; }
#primary { display: block; width: 300px; height: 64px; }
</style></head><body><main><h1>Task</h1><div class="clip"><button id="primary">Continue</button></div></main></body></html>''',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 1,
                "cases": [{
                    "id": "mobile-primary-task",
                    "page": "index.html",
                    "profile": "mobile",
                    "steps": [{
                        "id": "primary-fully-visible",
                        "action": "assert",
                        "selector": "#primary",
                        "expect": "fully-visible-in-viewport",
                    }],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            mobile = next(item for item in receipt["results"] if item["profile"] == "mobile")
            self.assertEqual("rejected", mobile["status"])

    def test_browser_contract_observes_delayed_error_after_final_step(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="en"><head><title>Delayed</title></head><body><main>
<h1>Task</h1><button id="primary">Continue</button>
</main><script>document.querySelector('#primary').onclick=()=>setTimeout(()=>{console.error('PRIVATE delayed');throw new Error('PRIVATE delayed')},80)</script></body></html>''',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 1,
                "cases": [{
                    "id": "desktop-primary-task",
                    "page": "index.html",
                    "profile": "desktop",
                    "steps": [{"id": "activate", "action": "click", "selector": "#primary"}],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            desktop = next(item for item in receipt["results"] if item["profile"] == "desktop")
            self.assertEqual("rejected", desktop["status"])
            self.assertGreater(desktop["counters"]["page_errors"], 0)
            self.assertGreater(desktop["counters"]["console_errors"], 0)
            self.assertNotIn("PRIVATE delayed", json.dumps(receipt))

    def test_browser_contract_runs_all_declarative_actions_and_assertions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="en"><head><title>Flow</title></head><body><main>
<h1>Configure</h1><label>Name <input id="name"></label>
<label>Plan <select id="plan"><option value="basic">Basic</option><option value="pro">Pro</option></select></label>
<button id="activate" aria-pressed="false">Activate</button><output id="state">Idle</output>
</main><script>
const nameInput = document.querySelector('#name');
const planSelect = document.querySelector('#plan');
const stateOutput = document.querySelector('#state');
const activateButton = document.querySelector('#activate');
nameInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') stateOutput.textContent = `${nameInput.value}:${planSelect.value}`;
});
activateButton.onclick = () => activateButton.setAttribute('aria-pressed', 'true');
</script></body></html>''',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 1,
                "cases": [{
                    "id": "desktop-primary-flow",
                    "page": "index.html",
                    "profile": "desktop",
                    "steps": [
                        {"id": "name-visible", "action": "assert", "selector": "#name", "expect": "visible"},
                        {"id": "name-first-viewport", "action": "assert", "selector": "#name", "expect": "fully-visible-in-viewport"},
                        {"id": "fill-name", "action": "fill", "selector": "#name", "value": "Ada"},
                        {"id": "select-plan", "action": "select", "selector": "#plan", "value": "pro"},
                        {"id": "submit-key", "action": "press", "selector": "#name", "key": "Enter"},
                        {"id": "state-text", "action": "assert", "selector": "#state", "expect": "text-includes", "value": "Ada:pro"},
                        {"id": "activate", "action": "click", "selector": "#activate"},
                        {"id": "activated", "action": "assert", "selector": "#activate", "expect": "attribute-equals", "attribute": "aria-pressed", "value": "true"},
                        {"id": "single-state", "action": "assert", "selector": "#state", "expect": "count-equals", "count": 1},
                    ],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            self.assertEqual("passed", receipt["status"])
            desktop = next(item for item in receipt["results"] if item["profile"] == "desktop")
            self.assertEqual("passed", desktop["inspection"]["browser_contract"]["status"])
            self.assertEqual(9, desktop["inspection"]["browser_contract"]["steps_executed"])

    def test_browser_contract_exercises_role_state_and_reports_runtime_error_without_raw_details(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="en"><head><title>Role</title></head><body><main>
<button id="buyer" aria-pressed="false">Buyer</button><section id="detail">Manager</section>
</main><script>buyer.onclick=()=>{throw new Error('PRIVATE buyer crash')}</script></body></html>''',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 1,
                "cases": [{
                    "id": "buyer-role",
                    "page": "index.html",
                    "profile": "desktop",
                    "steps": [
                        {"id": "activate", "action": "click", "selector": "#buyer"},
                        {"id": "pressed", "action": "assert", "selector": "#buyer", "expect": "attribute-equals", "attribute": "aria-pressed", "value": "true"},
                    ],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            result = next(item for item in receipt["results"] if item["profile"] == "desktop")
            self.assertEqual("rejected", result["status"])
            self.assertGreater(result["counters"]["page_errors"], 0)
            self.assertEqual(["contract-buyer-role-pressed"], result["inspection"]["browser_contract"]["finding_ids"])
            self.assertNotIn("PRIVATE buyer crash", json.dumps(receipt))

    def test_launch_failure_closes_server_and_exits_quickly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text('<!doctype html><html lang="en"><head><title>X</title></head><body><main><h1>X</h1></main></body></html>', encoding="utf-8")
            environment = os.environ.copy()
            environment["PLAYWRIGHT_BROWSERS_PATH"] = str(stage / "missing-browsers")
            completed = subprocess.run(
                ["node", str(SMOKE), str(stage), '["index.html"]', '["index.html"]'],
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
                timeout=5,
                check=False,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("html smoke infrastructure failure", completed.stderr)

    def test_clean_multi_page_output_passes_both_fresh_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "app.js").write_text("document.querySelector('main').dataset.ready = 'true';\n", encoding="utf-8")
            html = '<!doctype html><html lang="en"><head><title>Ready</title></head><body><main><h1>Ready</h1></main><script src="app.js"></script></body></html>'
            (stage / "index.html").write_text(html, encoding="utf-8")
            (stage / "details.html").write_text(html.replace("Ready", "Details"), encoding="utf-8")
            outputs = ["index.html", "details.html", "app.js"]
            receipt = self.invoke(stage, ["index.html", "details.html"], outputs)
            self.assertEqual("passed", receipt["status"])
            self.assertEqual(
                {("index.html", "desktop"), ("index.html", "mobile"), ("details.html", "desktop"), ("details.html", "mobile")},
                {(item["page"], item["profile"]) for item in receipt["results"]},
            )
            self.assertTrue(all(item["status"] == "passed" for item in receipt["results"]))

    def test_runtime_accessibility_overflow_and_external_failures_are_observed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html><head><title>Broken</title></head><body>
<main><div style="width:2000px">Broken</div><img src="https://example.invalid/a.png"><script>throw new Error("boot")</script></main>
</body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("rejected", receipt["status"])
            for item in receipt["results"]:
                self.assertEqual("rejected", item["status"])
                self.assertTrue(item["root_horizontal_overflow"])
                self.assertGreater(item["counters"]["page_errors"], 0)
                self.assertGreater(item["counters"]["blocked_external_requests"], 0)
                self.assertGreater(item["inspection"]["axe_violation_count"], 0)
                self.assertNotIn("boot", json.dumps(item))

    def test_delayed_failures_and_transient_popup_are_observed_within_settle_window(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html lang="en"><head><title>Delayed</title></head><body>
<main><h1>Delayed</h1></main><script>
setTimeout(() => {
  document.querySelector('main').style.width = '2000px';
  fetch('https://example.invalid/delayed').catch(() => {});
  const popup = window.open('about:blank', '_blank');
  popup?.close();
  throw new Error('delayed boot');
}, 80);
</script></body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual(300, receipt["settle_ms"])
            self.assertEqual("rejected", receipt["status"])
            for item in receipt["results"]:
                self.assertGreater(item["counters"]["page_errors"], 0)
                self.assertGreater(item["counters"]["blocked_external_requests"], 0)
                self.assertGreater(item["counters"]["unexpected_pages"], 0)
                self.assertTrue(item["root_horizontal_overflow"])

    def test_clipped_body_content_does_not_impersonate_root_scroll_overflow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html lang="en"><head><title>Rail</title><style>
html, body { overflow-x: clip; }
.rail { max-width: 100%; overflow-x: auto; }
.track { width: 720px; }
</style></head><body><main><h1>Rail</h1><div class="rail"><div class="track">Scrollable child</div></div></main></body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("passed", receipt["status"])
            self.assertTrue(all(not item["root_horizontal_overflow"] for item in receipt["results"]))

    def test_text_outside_empty_main_does_not_satisfy_primary_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '<!doctype html><html lang="en"><head><title>Empty</title></head><body><main></main><footer><h1>Outside</h1></footer></body></html>'
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("rejected", receipt["status"])
            for item in receipt["results"]:
                self.assertTrue(item["visible_text"])
                self.assertFalse(item["visible_primary_content"])

    def test_visible_hidden_attribute_and_large_fixed_obstruction_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html lang="en"><head><title>Obstructed</title><style>
[hidden] { display: flex; }
.unexpected { height: 24px; }
.fixed-summary { position: fixed; inset: auto 0 0; min-height: 150px; background: white; z-index: 3; }
.occluded { position: absolute; top: 900px; }
@media (max-width: 780px) { .occluded { top: 720px; } }
</style></head><body><main><h1>Choose a service</h1><p class="occluded">Required task content</p></main>
<div class="unexpected" hidden>Should stay hidden</div><aside class="fixed-summary">Summary and action</aside></body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("rejected", receipt["status"])
            for item in receipt["results"]:
                hazards = item["inspection"]["layout_hazards"]
                self.assertEqual(1, hazards["hidden_attribute_visible_count"])
                self.assertEqual(1, hazards["fixed_content_obstruction_count"])

    def test_small_fixed_control_and_correctly_hidden_element_pass_layout_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html lang="en"><head><title>Clear</title><style>
.help { position: fixed; right: 12px; bottom: 12px; width: 48px; height: 48px; }
</style></head><body><main><h1>Clear task</h1><p style="min-height:900px">Content</p></main>
<div hidden>Hidden note</div><button class="help" aria-label="Help">?</button></body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("passed", receipt["status"])
            for item in receipt["results"]:
                hazards = item["inspection"]["layout_hazards"]
                self.assertEqual(0, hazards["hidden_attribute_visible_count"])
                self.assertEqual(0, hazards["fixed_content_obstruction_count"])

    def test_transparent_portal_and_transparent_ancestor_do_not_impersonate_layout_hazards(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html lang="en"><head><title>Transparent</title><style>
.portal { position: fixed; inset: 0; pointer-events: none; }
.transparent { opacity: 0; }
.transparent [hidden] { display: block; width: 40px; height: 40px; }
</style></head><body><main><h1>Visible task</h1><p style="min-height:900px">Content</p></main>
<div class="portal"></div><div class="transparent" aria-hidden="true"><div hidden>Not visible</div></div></body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("passed", receipt["status"])
            for item in receipt["results"]:
                self.assertEqual(
                    {"hidden_attribute_visible_count": 0, "fixed_content_obstruction_count": 0},
                    item["inspection"]["layout_hazards"],
                )

    def test_fixed_overlay_inside_main_still_obstructs_direct_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html lang="en"><head><title>Inside</title><style>
.cover { position: fixed; inset: 0; background: white; }
</style></head><body><main>Required direct task text<div class="cover">Blocking overlay</div></main></body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("rejected", receipt["status"])
            for item in receipt["results"]:
                self.assertEqual(1, item["inspection"]["layout_hazards"]["fixed_content_obstruction_count"])

    def test_opaque_rgb_fixed_overlay_is_not_mistaken_for_zero_alpha(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html lang="en"><head><title>RGB</title><style>
.occluded { position: absolute; top: 900px; }
.cover { position: fixed; inset: auto 0 0; height: 150px; background: rgb(255, 0, 0); }
@media (max-width: 780px) { .occluded { top: 720px; } }
</style></head><body><main><h1>Task</h1><p class="occluded">Required content</p></main><div class="cover"></div></body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("rejected", receipt["status"])
            for item in receipt["results"]:
                self.assertEqual(1, item["inspection"]["layout_hazards"]["fixed_content_obstruction_count"])

    def test_thin_fixed_border_and_invisible_main_text_do_not_create_obstruction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html lang="en"><head><title>Edges</title><style>
.hidden-copy { position: absolute; top: 720px; opacity: 0; }
.border-only { position: fixed; inset: 0; border: 1px solid black; pointer-events: none; }
.bar { position: fixed; inset: auto 0 0; height: 150px; background: white; }
</style></head><body><main><h1>Visible task</h1><p class="hidden-copy">Invisible content</p></main>
<div class="border-only"></div><div class="bar"></div></body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("passed", receipt["status"])
            for item in receipt["results"]:
                self.assertEqual(0, item["inspection"]["layout_hazards"]["fixed_content_obstruction_count"])

    def test_negative_z_index_fixed_background_is_not_reported_as_obstruction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html lang="en"><head><title>Behind</title><style>
main { position: relative; min-height: 100vh; background: white; }
.behind { position: fixed; inset: 0; z-index: -1; background: red; }
</style></head><body><div class="behind"></div><main><h1>Foreground task</h1></main></body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("passed", receipt["status"])
            for item in receipt["results"]:
                self.assertEqual(0, item["inspection"]["layout_hazards"]["fixed_content_obstruction_count"])

    def test_noopener_popup_is_attributed_to_the_primary_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html lang="en"><head><title>Popup</title></head><body>
<main><h1>Popup</h1></main><script>
setTimeout(() => window.open('about:blank', '_blank', 'noopener'), 80);
</script></body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("rejected", receipt["status"])
            for item in receipt["results"]:
                self.assertGreater(item["counters"]["unexpected_pages"], 0)


if __name__ == "__main__":
    unittest.main()
