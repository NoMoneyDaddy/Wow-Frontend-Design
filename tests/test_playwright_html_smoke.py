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
            self.assertEqual([{
                "finding_id": "contract-mobile-primary-task-primary-in-first-viewport",
                "reason": "assertion-not-satisfied",
            }], mobile["inspection"]["browser_contract"]["failures"])

    def test_browser_contract_can_target_one_named_button_among_multiple_buttons(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="zh-Hant"><head><title>語意定位</title></head><body>
<main><h1>排程</h1><button>切換區段</button><p id="window-time">01:20–02:10</p>
<button aria-describedby="window-time">確認時窗</button></main>
<script>document.querySelector('#window-time').textContent = '02:25–03:15';</script>
</body></html>''',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 2,
                "cases": [{
                    "id": "mobile-primary-task",
                    "page": "index.html",
                    "profile": "mobile",
                    "steps": [{
                        "id": "confirmation-in-first-viewport",
                        "action": "assert",
                        "role": "button",
                        "name": "確認時窗",
                        "expect": "fully-visible-in-viewport",
                    }],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            mobile = next(item for item in receipt["results"] if item["profile"] == "mobile")
            self.assertEqual("passed", mobile["status"], mobile)
            self.assertEqual(1, mobile["inspection"]["browser_contract"]["steps_executed"])
            self.assertEqual([], mobile["inspection"]["browser_contract"]["failures"])
            self.assertNotIn("label-content-name-mismatch", mobile["inspection"]["axe_rule_ids"])

    def test_rendered_text_excludes_hidden_descendants_and_ignores_poisoned_getter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="en"><head><title>Rendered state</title></head><body>
<main><h1>Task</h1>
<p id="raw">Idle<span hidden>Ready</span></p>
<p id="hidden-child">Idle<span hidden>Ready</span></p>
<p id="visible-child">Idle <span>Ready</span></p>
<p id="hidden-parent" hidden>Ready</p>
</main>
<script>Object.defineProperty(HTMLElement.prototype, 'innerText', { configurable: true, get() { return 'Ready'; } });</script>
</body></html>''',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 2,
                "cases": [{
                    "id": "desktop-rendered-state",
                    "page": "index.html",
                    "profile": "desktop",
                    "steps": [
                        {"id": "legacy-raw", "action": "assert", "selector": "#raw", "expect": "text-includes", "value": "Ready"},
                        {"id": "hidden-child", "action": "assert", "selector": "#hidden-child", "expect": "rendered-text-includes", "value": "Ready"},
                        {"id": "visible-child", "action": "assert", "selector": "#visible-child", "expect": "rendered-text-includes", "value": "Ready"},
                        {"id": "hidden-parent", "action": "assert", "selector": "#hidden-parent", "expect": "rendered-text-includes", "value": "Ready"},
                    ],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            desktop = next(item for item in receipt["results"] if item["profile"] == "desktop")
            self.assertEqual([
                "contract-desktop-rendered-state-hidden-child",
                "contract-desktop-rendered-state-hidden-parent",
            ], desktop["inspection"]["browser_contract"]["finding_ids"])
            self.assertEqual(4, desktop["inspection"]["browser_contract"]["steps_executed"])

    def test_accessible_name_must_include_the_visible_control_label(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="en"><head><title>Label in name</title></head><body>
<main><h1>Checkout</h1><button aria-label="Submit order">Buy now</button></main>
</body></html>''',
                encoding="utf-8",
            )
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("rejected", receipt["status"])
            for result in receipt["results"]:
                self.assertIn(
                    "label-content-name-mismatch",
                    result["inspection"]["axe_rule_ids"],
                )

    def test_browser_contract_distinguishes_ambiguous_locator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '<!doctype html><html lang="en"><head><title>Ambiguous</title></head><body><main><h1>Task</h1><button>One</button><button>Two</button></main></body></html>',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 2,
                "cases": [{
                    "id": "mobile-action",
                    "page": "index.html",
                    "profile": "mobile",
                    "steps": [{"id": "button", "action": "assert", "selector": "button", "expect": "visible"}],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            mobile = next(item for item in receipt["results"] if item["profile"] == "mobile")
            self.assertEqual([{
                "finding_id": "contract-mobile-action-button",
                "reason": "locator-ambiguous",
            }], mobile["inspection"]["browser_contract"]["failures"])

            count_contract = {
                "schema_version": 2,
                "cases": [{
                    "id": "mobile-count",
                    "page": "index.html",
                    "profile": "mobile",
                    "steps": [{
                        "id": "three-buttons", "action": "assert", "selector": "button",
                        "expect": "count-equals", "count": 3,
                    }],
                }],
            }
            count_receipt = self.invoke(stage, ["index.html"], ["index.html"], count_contract)
            count_mobile = next(item for item in count_receipt["results"] if item["profile"] == "mobile")
            self.assertEqual([{
                "finding_id": "contract-mobile-count-three-buttons",
                "reason": "assertion-not-satisfied",
            }], count_mobile["inspection"]["browser_contract"]["failures"])

    def test_browser_contract_collects_independent_pre_action_failures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="en"><head><title>Preconditions</title></head><body>
<main><h1>Task</h1><button id="activate">Activate</button></main></body></html>''',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 2,
                "cases": [{
                    "id": "mobile-preconditions",
                    "page": "index.html",
                    "profile": "mobile",
                    "steps": [
                        {"id": "missing-group", "action": "assert", "selector": "fieldset", "expect": "visible"},
                        {"id": "missing-confirmation", "action": "assert", "role": "button", "name": "Confirm", "expect": "visible"},
                        {"id": "activate", "action": "click", "selector": "#activate"},
                    ],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            mobile = next(item for item in receipt["results"] if item["profile"] == "mobile")
            observed = mobile["inspection"]["browser_contract"]
            self.assertEqual([
                "contract-mobile-preconditions-missing-group",
                "contract-mobile-preconditions-missing-confirmation",
            ], observed["finding_ids"])
            self.assertEqual(2, observed["steps_executed"])

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

    def test_browser_contract_waits_for_bounded_async_state_after_action(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="en"><head><title>Async</title></head><body><main>
<h1>Task</h1><button id="primary">Continue</button><output id="state">Idle</output>
</main><script>
document.querySelector('#primary').onclick = () => {
  setTimeout(() => { document.querySelector('#state').textContent = 'Ready'; }, 80);
};
</script></body></html>''',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 1,
                "cases": [{
                    "id": "desktop-primary-task",
                    "page": "index.html",
                    "profile": "desktop",
                    "steps": [
                        {"id": "activate", "action": "click", "selector": "#primary"},
                        {"id": "ready", "action": "assert", "selector": "#state", "expect": "text-includes", "value": "Ready"},
                    ],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            desktop = next(item for item in receipt["results"] if item["profile"] == "desktop")
            self.assertEqual("passed", desktop["status"])
            self.assertEqual("passed", desktop["inspection"]["browser_contract"]["status"])

    def test_v2_browser_contract_proves_loaded_font_and_rendered_text_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="zh-Hant"><head><title>Typography proof</title><style>
#specimen { font-family: "Contract Probe", sans-serif; inline-size: 18rem; }
#specimen span { display: block; }
#specimen .clipped { block-size: 0; overflow: hidden; }
</style></head><body><main><h1>字體與排版驗證</h1>
<p id="specimen"><span>繁體中文第一行</span><span>中英混排 Design 2026</span><span style="visibility:hidden">不可冒充第三行</span><span class="clipped"><span>裁切文字不可冒充第三行</span></span></p>
</main><script>
const contractFont = new FontFace("Contract Probe", 'local("Arial")');
document.fonts.add(contractFont);
contractFont.load();
</script></body></html>''',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 2,
                "cases": [{
                    "id": "desktop-type-proof",
                    "page": "index.html",
                    "profile": "desktop",
                    "steps": [
                        {"id": "font-loaded", "action": "assert", "selector": "#specimen", "expect": "font-face-loaded", "family": "Contract Probe"},
                        {"id": "two-lines", "action": "assert", "selector": "#specimen", "expect": "line-count-between", "min_lines": 2, "max_lines": 2},
                        {"id": "healthy-last-line", "action": "assert", "selector": "#specimen", "expect": "last-line-graphemes-at-least", "count": 8},
                        {"id": "no-local-overflow", "action": "assert", "selector": "#specimen", "expect": "no-content-overflow"},
                    ],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            desktop = next(item for item in receipt["results"] if item["profile"] == "desktop")
            self.assertEqual("passed", desktop["status"], desktop)
            self.assertEqual("passed", desktop["inspection"]["browser_contract"]["status"])
            self.assertEqual(2, receipt["browser_contract"]["schema_version"])

    def test_v2_text_segment_assertion_uses_exact_rendered_line_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="zh-Hant"><head><title>Lexical line proof</title><style>
#broken span { display: block; }
#vertical { writing-mode: vertical-rl; }
</style></head><body><main><h1>排版驗證</h1>
<p id="plain">保持放行詞組</p>
<p id="inline">保持<span>切</span><span>換</span>詞組</p>
<p id="broken"><span>放</span><span>行</span></p>
<p id="missing">沒有指定內容</p>
<p id="duplicate">切換後再次切換</p>
<p id="overlap">哈哈哈</p>
<p id="vertical">保持放行詞組</p>
</main></body></html>''',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 2,
                "cases": [{
                    "id": "mobile-lexical-lines",
                    "page": "index.html",
                    "profile": "mobile",
                    "steps": [
                        {"id": "plain", "action": "assert", "selector": "#plain", "expect": "text-segment-on-one-line", "segment": "放行"},
                        {"id": "inline", "action": "assert", "selector": "#inline", "expect": "text-segment-on-one-line", "segment": "切換"},
                        {"id": "broken", "action": "assert", "selector": "#broken", "expect": "text-segment-on-one-line", "segment": "放行"},
                        {"id": "missing", "action": "assert", "selector": "#missing", "expect": "text-segment-on-one-line", "segment": "放行"},
                        {"id": "duplicate", "action": "assert", "selector": "#duplicate", "expect": "text-segment-on-one-line", "segment": "切換"},
                        {"id": "overlap", "action": "assert", "selector": "#overlap", "expect": "text-segment-on-one-line", "segment": "哈哈"},
                        {"id": "vertical", "action": "assert", "selector": "#vertical", "expect": "text-segment-on-one-line", "segment": "放行"},
                    ],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            mobile = next(item for item in receipt["results"] if item["profile"] == "mobile")
            self.assertEqual([
                "contract-mobile-lexical-lines-broken",
                "contract-mobile-lexical-lines-missing",
                "contract-mobile-lexical-lines-duplicate",
                "contract-mobile-lexical-lines-overlap",
                "contract-mobile-lexical-lines-vertical",
            ], mobile["inspection"]["browser_contract"]["finding_ids"])

    def test_v2_inline_start_alignment_uses_relative_logical_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="en"><head><title>Alignment</title><style>
.row { display: grid; grid-template-columns: 8rem 1fr; }
.field { grid-column: 2; inline-size: 12rem; }
#shifted { margin-inline-start: 12px; }
#within-tolerance { margin-inline-start: 1px; }
#outside-tolerance { margin-inline-start: 1.25px; }
#hidden-reference { display: none; }
#zero-reference { inline-size: 0; block-size: 0; }
#vertical-reference { writing-mode: vertical-rl; }
#rtl-reference { direction: rtl; }
#rtl-shifted { margin-inline-start: 12px; }
@keyframes cross-anchor { from { transform: translateX(-20px); } to { transform: translateX(20px); } }
#moving.run { animation: cross-anchor 400ms linear forwards; }
</style></head><body><main><h1>Alignment</h1>
<button id="move">Move</button>
<div class="row"><label>Anchor</label><input id="anchor" class="field"></div>
<div class="row"><label>Aligned</label><input id="aligned" class="field"></div>
<div class="row"><label>Shifted</label><input id="shifted" class="field"></div>
<div class="row"><label>Within</label><input id="within-tolerance" class="field"></div>
<div class="row"><label>Outside</label><input id="outside-tolerance" class="field"></div>
<div class="row"><label>Hidden</label><span id="hidden-reference" class="field">Hidden</span></div>
<div class="row"><label>Zero</label><span id="zero-reference" class="field"></span></div>
<div class="row"><label>Vertical</label><span id="vertical-reference" class="field">Vertical</span></div>
<div class="row"><label>RTL</label><span id="rtl-reference" class="field">RTL</span></div>
<div class="row"><label>Moving</label><input id="moving" class="field"></div>
<div class="row"><label>Shadow</label><span id="shadow-host" class="field"></span></div>
<div class="row"><label>Duplicate A</label><span class="duplicate field">A</span></div>
<div class="row"><label>Duplicate B</label><span class="duplicate field">B</span></div>
<section dir="rtl">
<div class="row"><label>مرجع</label><input id="rtl-anchor" class="field"></div>
<div class="row"><label>محاذاة</label><input id="rtl-aligned" class="field"></div>
<div class="row"><label>إزاحة</label><input id="rtl-shifted" class="field"></div>
</section>
<script>
document.querySelector('#move').onclick = () => document.querySelector('#moving').classList.add('run');
const shadow = document.querySelector('#shadow-host').attachShadow({ mode: 'open' });
shadow.innerHTML = '<span id="shadow-reference" style="display:block">Shadow</span>';
document.querySelector('#shadow-host').style.opacity = '0';
globalThis.ShadowRoot = function PoisonedShadowRoot() {};
</script>
</main></body></html>''',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 2,
                "cases": [{
                    "id": "desktop-alignment",
                    "page": "index.html",
                    "profile": "desktop",
                    "steps": [
                        {"id": "aligned", "action": "assert", "selector": "#aligned",
                         "expect": "inline-start-aligned-with", "reference_selector": "#anchor"},
                        {"id": "shifted", "action": "assert", "selector": "#shifted",
                         "expect": "inline-start-aligned-with", "reference_selector": "#anchor"},
                        {"id": "within-tolerance", "action": "assert", "selector": "#within-tolerance",
                         "expect": "inline-start-aligned-with", "reference_selector": "#anchor"},
                        {"id": "outside-tolerance", "action": "assert", "selector": "#outside-tolerance",
                         "expect": "inline-start-aligned-with", "reference_selector": "#anchor"},
                        {"id": "missing", "action": "assert", "selector": "#aligned",
                         "expect": "inline-start-aligned-with", "reference_selector": "#missing"},
                        {"id": "ambiguous", "action": "assert", "selector": "#aligned",
                         "expect": "inline-start-aligned-with", "reference_selector": ".duplicate"},
                        {"id": "hidden", "action": "assert", "selector": "#aligned",
                         "expect": "inline-start-aligned-with", "reference_selector": "#hidden-reference"},
                        {"id": "zero", "action": "assert", "selector": "#aligned",
                         "expect": "inline-start-aligned-with", "reference_selector": "#zero-reference"},
                        {"id": "vertical", "action": "assert", "selector": "#aligned",
                         "expect": "inline-start-aligned-with", "reference_selector": "#vertical-reference"},
                        {"id": "mixed-direction", "action": "assert", "selector": "#aligned",
                         "expect": "inline-start-aligned-with", "reference_selector": "#rtl-reference"},
                        {"id": "shadow-hidden", "action": "assert", "selector": "#aligned",
                         "expect": "inline-start-aligned-with", "reference_selector": "#shadow-reference"},
                        {"id": "rtl-aligned", "action": "assert", "selector": "#rtl-aligned",
                         "expect": "inline-start-aligned-with", "reference_selector": "#rtl-anchor"},
                        {"id": "rtl-shifted", "action": "assert", "selector": "#rtl-shifted",
                         "expect": "inline-start-aligned-with", "reference_selector": "#rtl-anchor"},
                    ],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            desktop = next(item for item in receipt["results"] if item["profile"] == "desktop")
            self.assertEqual([
                "contract-desktop-alignment-shifted",
                "contract-desktop-alignment-outside-tolerance",
                "contract-desktop-alignment-missing",
                "contract-desktop-alignment-ambiguous",
                "contract-desktop-alignment-hidden",
                "contract-desktop-alignment-zero",
                "contract-desktop-alignment-vertical",
                "contract-desktop-alignment-mixed-direction",
                "contract-desktop-alignment-shadow-hidden",
                "contract-desktop-alignment-rtl-shifted",
            ], desktop["inspection"]["browser_contract"]["finding_ids"])

            motion_contract = {
                "schema_version": 2,
                "cases": [{
                    "id": "desktop-moving-alignment",
                    "page": "index.html",
                    "profile": "desktop",
                    "steps": [
                        {"id": "start-moving", "action": "click", "selector": "#move"},
                        {"id": "transient-crossing", "action": "assert", "selector": "#moving",
                         "expect": "inline-start-aligned-with", "reference_selector": "#anchor"},
                    ],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], motion_contract)
            desktop = next(item for item in receipt["results"] if item["profile"] == "desktop")
            self.assertEqual(
                ["contract-desktop-moving-alignment-transient-crossing"],
                desktop["inspection"]["browser_contract"]["finding_ids"],
            )

    def test_v2_browser_contract_rejects_fragmented_last_line_and_local_overflow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="zh-Hant"><head><title>Typography risk</title><style>
#heading { font-family: "Missing Proof", sans-serif; inline-size: 8rem; overflow: hidden; }
#heading span { display: block; }
#heading .wide { inline-size: 20rem; }
</style></head><body><main><h1 id="heading"><span>完整標題首行</span><span class="wide">末</span></h1></main></body></html>''',
                encoding="utf-8",
            )
            base_case = {
                "id": "mobile-type-risk",
                "page": "index.html",
                "profile": "mobile",
                "steps": [],
            }
            fragment_contract = {
                "schema_version": 2,
                "cases": [{**base_case, "steps": [{
                    "id": "no-stranded-tail", "action": "assert", "selector": "#heading",
                    "expect": "last-line-graphemes-at-least", "count": 2,
                }]}],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], fragment_contract)
            mobile = next(item for item in receipt["results"] if item["profile"] == "mobile")
            self.assertEqual(["contract-mobile-type-risk-no-stranded-tail"], mobile["inspection"]["browser_contract"]["finding_ids"])

            overflow_contract = {
                "schema_version": 2,
                "cases": [{**base_case, "steps": [{
                    "id": "no-local-overflow", "action": "assert", "selector": "#heading",
                    "expect": "no-content-overflow",
                }]}],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], overflow_contract)
            mobile = next(item for item in receipt["results"] if item["profile"] == "mobile")
            self.assertEqual(["contract-mobile-type-risk-no-local-overflow"], mobile["inspection"]["browser_contract"]["finding_ids"])

            font_contract = {
                "schema_version": 2,
                "cases": [{**base_case, "steps": [{
                    "id": "font-loaded", "action": "assert", "selector": "#heading",
                    "expect": "font-face-loaded", "family": "Missing Proof",
                }]}],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], font_contract)
            mobile = next(item for item in receipt["results"] if item["profile"] == "mobile")
            self.assertEqual(["contract-mobile-type-risk-font-loaded"], mobile["inspection"]["browser_contract"]["finding_ids"])

    def test_v2_browser_contract_proves_bounded_motion_and_reduced_static_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="en"><head><title>Motion proof</title><style>
@keyframes reveal { from { opacity: .2; transform: translateY(8px); } to { opacity: 1; transform: none; } }
#panel.run { animation: reveal 240ms linear; }
@media (prefers-reduced-motion: reduce) { #panel.run { animation: none; } }
</style></head><body><main><h1>Motion proof</h1><button id="trigger">Reveal</button><section id="panel" data-state="idle">Ready content</section>
</main><script>
const triggerButton = document.querySelector('#trigger');
const panel = document.querySelector('#panel');
triggerButton.onclick = () => {
  panel.classList.remove('run');
  void panel.offsetWidth;
  panel.classList.add('run');
  panel.dataset.state = 'ready';
};
</script></body></html>''',
                encoding="utf-8",
            )
            desktop_contract = {
                "schema_version": 2,
                "cases": [{
                    "id": "desktop-motion-proof", "page": "index.html", "profile": "desktop",
                    "steps": [
                        {"id": "start", "action": "click", "selector": "#trigger"},
                        {"id": "running", "action": "assert", "selector": "#panel", "expect": "active-animation-count-between", "min_animations": 1, "max_animations": 1},
                        {"id": "settled", "action": "assert", "selector": "#panel", "expect": "animations-settled"},
                        {"id": "final-state", "action": "assert", "selector": "#panel", "expect": "attribute-equals", "attribute": "data-state", "value": "ready"},
                    ],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], desktop_contract)
            desktop = next(item for item in receipt["results"] if item["profile"] == "desktop")
            self.assertEqual("passed", desktop["inspection"]["browser_contract"]["status"])

            reduced_contract = {
                "schema_version": 2,
                "cases": [{
                    "id": "mobile-reduced-proof", "page": "index.html", "profile": "mobile",
                    "steps": [
                        {"id": "start", "action": "click", "selector": "#trigger"},
                        {"id": "static", "action": "assert", "selector": "#panel", "expect": "active-animation-count-between", "min_animations": 0, "max_animations": 0},
                        {"id": "final-state", "action": "assert", "selector": "#panel", "expect": "attribute-equals", "attribute": "data-state", "value": "ready"},
                    ],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], reduced_contract)
            mobile = next(item for item in receipt["results"] if item["profile"] == "mobile")
            self.assertEqual("passed", mobile["inspection"]["browser_contract"]["status"])

    def test_v2_browser_contract_can_opt_into_mobile_motion_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="en"><head><title>Mobile motion</title><style>
@keyframes select { from { transform: translateX(-8px); } to { transform: none; } }
#panel.run { animation: select 240ms linear; }
@media (prefers-reduced-motion: reduce) { #panel.run { animation: none; } }
</style></head><body><main><h1>Mobile motion</h1><button id="trigger">Select</button><section id="panel">Ready</section>
</main><script>document.querySelector('#trigger').onclick = () => document.querySelector('#panel').classList.add('run');</script>
</body></html>''',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 2,
                "cases": [{
                    "id": "mobile-motion-proof", "page": "index.html", "profile": "mobile-motion",
                    "steps": [
                        {"id": "start", "action": "click", "selector": "#trigger"},
                        {"id": "running", "action": "assert", "selector": "#panel",
                         "expect": "active-animation-count-between", "min_animations": 1, "max_animations": 1},
                    ],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            self.assertEqual(["desktop", "mobile", "mobile-motion"], [
                item["name"] for item in receipt["profiles"]
            ])
            mobile_motion = next(item for item in receipt["results"] if item["profile"] == "mobile-motion")
            self.assertEqual("passed", mobile_motion["inspection"]["browser_contract"]["status"])
            self.assertEqual("no-preference", next(
                item["reduced_motion"] for item in receipt["profiles"] if item["name"] == "mobile-motion"
            ))

    def test_v2_browser_contract_rejects_unsettled_continuous_motion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="en"><head><title>Motion loop</title><style>
@keyframes loop { to { transform: translateX(2px); } }
#ambient { animation: loop 300ms linear infinite alternate; }
</style></head><body><main><h1>Motion loop</h1><div id="ambient">Ambient</div></main></body></html>''',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 2,
                "cases": [{
                    "id": "desktop-motion-loop", "page": "index.html", "profile": "desktop",
                    "steps": [{"id": "settled", "action": "assert", "selector": "#ambient", "expect": "animations-settled"}],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            desktop = next(item for item in receipt["results"] if item["profile"] == "desktop")
            self.assertEqual(["contract-desktop-motion-loop-settled"], desktop["inspection"]["browser_contract"]["finding_ids"])

    def test_v2_browser_contract_observes_continuous_animation_inactivity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="en"><head><title>Delayed motion</title></head><body>
<main><h1>Delayed motion</h1><button id="trigger">Update</button><section id="panel">Ready</section></main>
<script>
const panel = document.querySelector('#panel');
document.querySelector('#trigger').onclick = () => {
  setTimeout(() => panel.animate(
    [{ transform: 'translateX(0)' }, { transform: 'translateX(24px)' }],
    { duration: 180, iterations: 1 }
  ), 100);
};
</script></body></html>''',
                encoding="utf-8",
            )
            delayed_contract = {
                "schema_version": 2,
                "cases": [{
                    "id": "mobile-delayed-motion", "page": "index.html", "profile": "mobile",
                    "steps": [
                        {"id": "start", "action": "click", "selector": "#trigger"},
                        {"id": "static-window", "action": "assert", "selector": "#panel",
                         "expect": "animations-inactive-for", "duration_ms": 350},
                    ],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], delayed_contract)
            mobile = next(item for item in receipt["results"] if item["profile"] == "mobile")
            self.assertEqual(
                ["contract-mobile-delayed-motion-static-window"],
                mobile["inspection"]["browser_contract"]["finding_ids"],
            )

            static_contract = {
                "schema_version": 2,
                "cases": [{
                    "id": "mobile-static-result", "page": "index.html", "profile": "mobile",
                    "steps": [{"id": "static-window", "action": "assert", "selector": "#panel",
                               "expect": "animations-inactive-for", "duration_ms": 200}],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], static_contract)
            mobile = next(item for item in receipt["results"] if item["profile"] == "mobile")
            self.assertEqual("passed", mobile["inspection"]["browser_contract"]["status"])

    def test_v2_browser_contract_uses_pre_page_geometry_and_animation_intrinsics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="en"><head><title>Adversarial proof</title><style>
@keyframes ambient { from { opacity: .8 } to { opacity: 1 } }
#overflow { width: 40px; height: 24px; overflow: auto; }
#overflow > span { display: block; width: 400px; }
#ambient { animation: ambient 20s linear infinite; }
</style></head><body><main><h1>Trusted browser reads</h1>
<button id="poison">Change page intrinsics</button><div id="overflow"><span>Wide content</span></div><div id="ambient">Moving</div>
<p id="phrase">保持<span>切</span><span>換</span>詞組</p>
<div id="anchor">Anchor</div><div id="aligned">Aligned</div>
</main><script>
window.getComputedStyle = () => ({ display: 'block', visibility: 'visible', opacity: '1', overflowX: 'visible', overflowY: 'visible' });
Element.prototype.getBoundingClientRect = () => ({ left: 0, top: 0, right: 10, bottom: 10, width: 10, height: 10 });
Element.prototype.getAnimations = () => [];
Range.prototype.getBoundingClientRect = () => ({ left: 0, top: 0, right: 0, bottom: 0, width: 0, height: 0 });
String.prototype.indexOf = () => -1;
Object.defineProperty(Element.prototype, 'scrollWidth', { configurable: true, get: () => 1 });
Object.defineProperty(Element.prototype, 'scrollHeight', { configurable: true, get: () => 1 });
Object.defineProperty(Element.prototype, 'clientWidth', { configurable: true, get: () => 1000 });
Object.defineProperty(Element.prototype, 'clientHeight', { configurable: true, get: () => 1000 });
document.querySelector('#poison').onclick = () => {
  Array.prototype.includes = () => false;
  Array.prototype.some = () => true;
};
</script></body></html>''',
                encoding="utf-8",
            )
            base_case = {"id": "desktop-trusted-read", "page": "index.html", "profile": "desktop", "steps": []}
            overflow = self.invoke(stage, ["index.html"], ["index.html"], {
                "schema_version": 2,
                "cases": [{**base_case, "steps": [{
                    "id": "overflow", "action": "assert", "selector": "#overflow", "expect": "no-content-overflow",
                }]}],
            })
            desktop = next(item for item in overflow["results"] if item["profile"] == "desktop")
            self.assertEqual(["contract-desktop-trusted-read-overflow"], desktop["inspection"]["browser_contract"]["finding_ids"])

            motion = self.invoke(stage, ["index.html"], ["index.html"], {
                "schema_version": 2,
                "cases": [{**base_case, "steps": [{
                    "id": "settled", "action": "assert", "selector": "#ambient", "expect": "animations-settled",
                }]}],
            })
            desktop = next(item for item in motion["results"] if item["profile"] == "desktop")
            self.assertEqual(["contract-desktop-trusted-read-settled"], desktop["inspection"]["browser_contract"]["finding_ids"])

            phrase = self.invoke(stage, ["index.html"], ["index.html"], {
                "schema_version": 2,
                "cases": [{**base_case, "steps": [{
                    "id": "phrase", "action": "assert", "selector": "#phrase",
                    "expect": "text-segment-on-one-line", "segment": "切換",
                }]}],
            })
            desktop = next(item for item in phrase["results"] if item["profile"] == "desktop")
            self.assertEqual("passed", desktop["inspection"]["browser_contract"]["status"])

            font = self.invoke(stage, ["index.html"], ["index.html"], {
                "schema_version": 2,
                "cases": [{**base_case, "steps": [
                    {"id": "poison", "action": "click", "selector": "#poison"},
                    {"id": "missing-font", "action": "assert", "selector": "#overflow", "expect": "font-face-loaded", "family": "Definitely Missing Font"},
                ]}],
            })
            desktop = next(item for item in font["results"] if item["profile"] == "desktop")
            self.assertEqual(["contract-desktop-trusted-read-missing-font"], desktop["inspection"]["browser_contract"]["finding_ids"])

            alignment = self.invoke(stage, ["index.html"], ["index.html"], {
                "schema_version": 2,
                "cases": [{**base_case, "steps": [
                    {"id": "poison", "action": "click", "selector": "#poison"},
                    {"id": "aligned", "action": "assert", "selector": "#aligned",
                     "expect": "inline-start-aligned-with", "reference_selector": "#anchor"},
                ]}],
            })
            desktop = next(item for item in alignment["results"] if item["profile"] == "desktop")
            self.assertEqual("passed", desktop["inspection"]["browser_contract"]["status"])

    def test_v2_last_line_segments_graphemes_across_inline_nodes_and_invalid_lang(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                '''<!doctype html><html lang="not_a_locale"><head><title>Grapheme proof</title></head>
<body><main><h1>Grapheme proof</h1><p id="tail">👩<span>‍💻</span></p></main></body></html>''',
                encoding="utf-8",
            )
            contract = {
                "schema_version": 2,
                "cases": [{
                    "id": "desktop-grapheme-proof", "page": "index.html", "profile": "desktop",
                    "steps": [{
                        "id": "single-cluster", "action": "assert", "selector": "#tail",
                        "expect": "last-line-graphemes-at-least", "count": 2,
                    }],
                }],
            }
            receipt = self.invoke(stage, ["index.html"], ["index.html"], contract)
            desktop = next(item for item in receipt["results"] if item["profile"] == "desktop")
            self.assertEqual(["contract-desktop-grapheme-proof-single-cluster"], desktop["inspection"]["browser_contract"]["finding_ids"])

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

    def test_wide_touch_height_fixed_action_covering_task_content_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html lang="en"><head><title>Covered action</title><style>
main { position: relative; min-height: 100vh; }
.required-copy { position: absolute; inset: auto 0 12px; }
.action { position: fixed; inset: auto 0 0; width: 100%; height: 44px; background: white; z-index: 3; }
</style></head><body><main><h1>Review task</h1><p class="required-copy">Required decision context</p></main>
<button class="action">Continue</button></body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("rejected", receipt["status"])
            for item in receipt["results"]:
                self.assertEqual(1, item["inspection"]["layout_hazards"]["fixed_content_obstruction_count"])

    def test_wide_touch_height_fixed_action_clear_of_task_content_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html lang="en"><head><title>Clear action</title><style>
.action { position: fixed; inset: auto 0 0; width: 100%; height: 44px; background: white; z-index: 3; }
</style></head><body><main><h1>Review task</h1><p>Decision context remains clear.</p></main>
<button class="action">Continue</button></body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("passed", receipt["status"])
            for item in receipt["results"]:
                self.assertEqual(0, item["inspection"]["layout_hazards"]["fixed_content_obstruction_count"])

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
