#!/usr/bin/env python3
"""Regression tests for the v6 multi-profile visual auditor."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDITOR = ROOT / "evals" / "playwright_visual_v7_audit.cjs"


class PlaywrightVisualV7AuditTests(unittest.TestCase):
    def run_node(self, source: str) -> object:
        completed = subprocess.run(
            ["node", "-e", source],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        if completed.returncode != 0:
            self.fail(completed.stderr)
        return json.loads(completed.stdout)

    def test_inventory_replays_every_route_interaction(self) -> None:
        source = f"""
const {{ CASE_PAGES, INTERACTION_PAGES, VIEWPORTS, expectedScreenshotCount, interactionPageNames }} = require({json.dumps(str(AUDITOR))});
const base = Object.values(CASE_PAGES).reduce((sum, pages) => sum + pages.length * VIEWPORTS.length, 0);
const interaction = Object.values(INTERACTION_PAGES).reduce((sum, pages) => sum + pages.length * 2, 0);
process.stdout.write(JSON.stringify({{
  cases: Object.keys(CASE_PAGES).length,
  routes: Object.values(CASE_PAGES).flat().length,
  profiles: VIEWPORTS.map((viewport) => viewport.name),
  total: base + interaction,
  expected: expectedScreenshotCount(Object.keys(CASE_PAGES).map((caseId) => ({{ caseId }}))),
  packagingInteractionPages: interactionPageNames('packaging-configurator-v6'),
  oralHistoryInteractionPages: interactionPageNames('oral-history-archive-v6'),
}}));
"""
        result = self.run_node(source)
        self.assertEqual(8, result["cases"])
        self.assertEqual(12, result["routes"])
        self.assertEqual(
            ["desktop", "tablet", "mobile", "compact-mobile"],
            result["profiles"],
        )
        self.assertEqual(66, result["total"])
        self.assertEqual(66, result["expected"])
        self.assertEqual(["index.html", "materials.html", "summary.html"], result["packagingInteractionPages"])
        self.assertEqual([], result["oralHistoryInteractionPages"])

    def test_interaction_coverage_counts_rows_separately_from_captures(self) -> None:
        source = f"""
const {{ CASE_PAGES, INTERACTION_MANIFEST, INTERACTION_PAGES, buildInteractionCoverage }} = require({json.dumps(str(AUDITOR))});
const targets = Object.keys(CASE_PAGES).map((caseId) => ({{ caseId, alias: 'pilot' }}));
const results = [];
const stateA = {{ writingMode: 'horizontal-tb', ariaPressed: 'false' }};
const stateB = {{ writingMode: 'vertical-rl', ariaPressed: 'true' }};
const sampledB = {{ actual: stateB, samples: [stateB, stateB, stateB], matches: true }};
for (const [caseId, pages] of Object.entries(INTERACTION_PAGES)) {{
  for (const page of pages) {{
    for (const viewport of ['desktop', 'mobile']) {{
      const manifest = INTERACTION_MANIFEST[`${{caseId}}:${{page}}`];
      results.push({{
        caseId, alias: 'pilot', page, viewport, state: 'interaction', screenshot: `${{caseId}}-${{page}}-${{viewport}}.png`, visualIssues: [],
        interaction: manifest ? {{
          attempted: true, page, manifestId: manifest.id, manifestCoverage: 'declared-pilot-row', failures: [],
          hooks: {{ controlCount: 1, stateCount: 1, controlVisible: true, controlEnabled: true }},
          A: stateA, B: stateB, restoredA: stateA, returnPath: manifest.returnAction, finalB: stateB,
          roundTripVerified: true,
          screenshotState: {{ expected: 'B', before: sampledB, after: sampledB, verified: true }},
        }} : {{ failures: [] }},
      }});
    }}
  }}
}}
process.stdout.write(JSON.stringify(buildInteractionCoverage(targets, results)));
"""
        result = self.run_node(source)
        summary = result["summary"]
        self.assertEqual("target-row", summary["unit"])
        self.assertEqual(9, summary["applicable"])
        self.assertEqual(1, summary["declared"])
        self.assertEqual(1, summary["verified"])
        self.assertEqual(8, summary["undeclared"])
        self.assertEqual(2, summary["declaredExpectedCaptures"])
        self.assertEqual(2, summary["declaredVerifiedCaptures"])
        self.assertEqual(16, summary["legacyExecutedCaptures"])
        self.assertEqual("1/9", summary["declarationCoverage"])
        self.assertEqual("pilot_complete", summary["status"])
        self.assertEqual("not_applicable", result["byTarget"]["oral-history-archive-v6:pilot"]["status"])

    def test_interaction_coverage_keeps_failed_and_missing_dimensions(self) -> None:
        source = f"""
const {{ buildInteractionCoverage }} = require({json.dumps(str(AUDITOR))});
const target = {{ caseId: 'type-foundry-specimen-v6', alias: 'pilot' }};
const results = [{{
  ...target, page: 'index.html', viewport: 'desktop', state: 'interaction', screenshot: 'desktop.png',
  visualIssues: ['type_writing_mode_round_trip_failed'],
  interaction: {{
    manifestId: 'type-foundry-writing-mode-toggle', manifestCoverage: 'declared-pilot-row',
    roundTripVerified: false, screenshotState: {{ verified: true }}, failures: ['type_writing_mode_round_trip_failed'],
  }},
}}];
process.stdout.write(JSON.stringify(buildInteractionCoverage([target], results)));
"""
        result = self.run_node(source)
        target = result["byTarget"]["type-foundry-specimen-v6:pilot"]
        self.assertEqual("failed_incomplete", target["rows"][0]["status"])
        self.assertEqual(["desktop"], target["rows"][0]["failedViewports"])
        self.assertEqual(["mobile"], target["rows"][0]["missingViewports"])
        self.assertEqual(1, target["failedDeclared"])
        self.assertEqual(1, target["incompleteDeclared"])

    def test_interaction_coverage_does_not_trust_flags_or_hide_legacy_failures(self) -> None:
        source = f"""
const {{ buildInteractionCoverage }} = require({json.dumps(str(AUDITOR))});
const typeTarget = {{ caseId: 'type-foundry-specimen-v6', alias: 'pilot' }};
const windTarget = {{ caseId: 'wind-maintenance-dispatch-v6', alias: 'pilot' }};
const results = ['desktop', 'mobile'].flatMap((viewport) => [
  {{
    ...typeTarget, page: 'index.html', viewport, state: 'interaction', screenshot: `type-${{viewport}}.png`, visualIssues: [],
    interaction: {{ manifestId: 'type-foundry-writing-mode-toggle', manifestCoverage: 'declared-pilot-row', roundTripVerified: true, screenshotState: {{ verified: true }}, failures: [] }},
  }},
  {{
    ...windTarget, page: 'index.html', viewport, state: 'interaction', screenshot: `wind-${{viewport}}.png`, visualIssues: viewport === 'desktop' ? ['wind_filter_count_failed'] : [],
    interaction: {{ failures: viewport === 'desktop' ? ['wind_filter_count_failed'] : [] }},
  }},
]);
process.stdout.write(JSON.stringify(buildInteractionCoverage([typeTarget, windTarget], results)));
"""
        result = self.run_node(source)
        self.assertEqual(0, result["byTarget"]["type-foundry-specimen-v6:pilot"]["verified"])
        wind = result["byTarget"]["wind-maintenance-dispatch-v6:pilot"]
        self.assertEqual("undeclared", wind["rows"][0]["status"])
        self.assertEqual(["desktop"], wind["rows"][0]["failedViewports"])
        self.assertEqual(["wind_filter_count_failed"], wind["rows"][0]["failuresByViewport"]["desktop"])
        self.assertEqual(1, result["summary"]["legacyFailedRows"])
        self.assertEqual(1, result["summary"]["legacyFailedCaptures"])

    def test_interaction_coverage_preserves_duplicate_capture_records_and_failures(self) -> None:
        source = f"""
const {{ buildInteractionCoverage }} = require({json.dumps(str(AUDITOR))});
const target = {{ caseId: 'wind-maintenance-dispatch-v6', alias: 'pilot' }};
const capture = (viewport, suffix, issue = null) => ({{
  ...target, page: 'index.html', viewport, state: 'interaction', screenshot: `${{viewport}}-${{suffix}}.png`,
  visualIssues: issue ? [issue] : [], interaction: {{ failures: [] }},
}});
const results = [
  capture('desktop', 'pass'),
  capture('desktop', 'fail', 'wind_filter_count_failed'),
  capture('mobile', 'pass'),
];
process.stdout.write(JSON.stringify(buildInteractionCoverage([target], results)));
"""
        result = self.run_node(source)
        target = result["byTarget"]["wind-maintenance-dispatch-v6:pilot"]
        row = target["rows"][0]
        self.assertEqual(["desktop"], row["duplicateViewports"])
        self.assertEqual(["desktop"], row["failedViewports"])
        self.assertEqual(["wind_filter_count_failed"], row["failuresByViewport"]["desktop"])
        self.assertEqual(["desktop-pass.png", "desktop-fail.png"], row["screenshotsByViewport"]["desktop"])
        self.assertEqual(3, target["legacyExecutedCaptures"])
        self.assertEqual(1, target["legacyFailedCaptures"])

    def test_declared_duplicate_capture_is_not_verified_and_keeps_failures(self) -> None:
        source = f"""
const {{ buildInteractionCoverage }} = require({json.dumps(str(AUDITOR))});
const target = {{ caseId: 'type-foundry-specimen-v6', alias: 'pilot' }};
const results = [
  {{ ...target, page: 'index.html', viewport: 'desktop', state: 'interaction', screenshot: 'one.png', visualIssues: [], interaction: {{ failures: [] }} }},
  {{ ...target, page: 'index.html', viewport: 'desktop', state: 'interaction', screenshot: 'two.png', visualIssues: ['type_writing_mode_duplicate_failed'], interaction: {{ failures: [] }} }},
  {{ ...target, page: 'index.html', viewport: 'mobile', state: 'interaction', screenshot: 'mobile.png', visualIssues: [], interaction: {{ failures: [] }} }},
];
process.stdout.write(JSON.stringify(buildInteractionCoverage([target], results)));
"""
        result = self.run_node(source)
        target = result["byTarget"]["type-foundry-specimen-v6:pilot"]
        row = target["rows"][0]
        self.assertEqual("failed_incomplete", row["status"])
        self.assertEqual([], row["verifiedViewports"])
        self.assertEqual(["desktop"], row["duplicateViewports"])
        self.assertEqual(["desktop", "mobile"], row["failedViewports"])
        self.assertEqual(["type_writing_mode_duplicate_failed"], row["failuresByViewport"]["desktop"])
        self.assertEqual(3, target["declaredObservedCaptures"])
        self.assertEqual(3, target["declaredFailedCaptures"])

    def test_packaging_material_recovery_handler_is_required(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ runCaseInteraction }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent(`
    <label data-eval="material-option"><input type="radio" name="material" value="double" checked></label>
    <label data-eval="material-option"><input type="radio" name="material" value="light"></label>
    <div id="status-pill" class="status status--ok"></div>
    <div data-eval="conflict-message"></div>
    <button data-action="load-stress" type="button">stress</button>
    <button data-action="apply-recovery" type="button" hidden>recover</button>
    <script>
      const status = document.querySelector('#status-pill');
      const recovery = document.querySelector('[data-action="apply-recovery"]');
      document.querySelector('[data-action="load-stress"]').addEventListener('click', () => {{
        status.className = 'status status--warn';
        recovery.hidden = false;
      }});
      // Recovery listener intentionally omitted: the evaluator must fail this fixture.
    </script>
  `);
  const evidence = await runCaseInteraction(page, 'packaging-configurator-v6', {{ name: 'desktop' }}, 'materials.html');
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertIn("packaging_material_recovery_failed", result["failures"])

    def test_type_foundry_manifest_proves_round_trip_and_preserves_interaction_state(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ INTERACTION_MANIFEST, runCaseInteraction }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent(`
    <button data-eval="writing-toggle" type="button" aria-pressed="false">切換</button>
    <div data-eval="specimen" style="writing-mode:horizontal-tb">字樣</div>
    <script>
      const toggle = document.querySelector('[data-eval="writing-toggle"]');
      const specimen = document.querySelector('[data-eval="specimen"]');
      toggle.addEventListener('click', () => {{
        const active = toggle.getAttribute('aria-pressed') === 'true';
        toggle.setAttribute('aria-pressed', String(!active));
        specimen.style.writingMode = active ? 'horizontal-tb' : 'vertical-rl';
      }});
    </script>
  `);
  const evidence = await runCaseInteraction(page, 'type-foundry-specimen-v6', {{ name: 'desktop' }}, 'index.html');
  const finalState = {{
    writingMode: await page.locator('[data-eval="specimen"]').evaluate((node) => getComputedStyle(node).writingMode),
    ariaPressed: await page.locator('[data-eval="writing-toggle"]').getAttribute('aria-pressed'),
  }};
  await browser.close();
  process.stdout.write(JSON.stringify({{ manifest: INTERACTION_MANIFEST['type-foundry-specimen-v6:index.html'], evidence, finalState }}));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertEqual("none", result["manifest"]["sideEffect"])
        self.assertEqual(
            {"writingMode": "horizontal-tb", "ariaPressed": "false"},
            result["manifest"]["expectedStates"]["A"],
        )
        self.assertEqual(
            {"writingMode": "vertical-rl", "ariaPressed": "true"},
            result["manifest"]["expectedStates"]["B"],
        )
        self.assertEqual("type-foundry-writing-mode-toggle", result["evidence"]["manifestId"])
        self.assertEqual("declared-pilot-row", result["evidence"]["manifestCoverage"])
        self.assertEqual([], result["evidence"]["failures"])
        self.assertTrue(result["evidence"]["roundTripVerified"])
        self.assertEqual(result["evidence"]["A"], result["evidence"]["restoredA"])
        self.assertEqual(result["evidence"]["B"], result["evidence"]["finalB"])
        self.assertEqual(result["evidence"]["B"], result["finalState"])

    def test_type_foundry_round_trip_rejects_one_way_toggle(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ runCaseInteraction }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent(`
    <button data-eval="writing-toggle" type="button" aria-pressed="false">切換</button>
    <div data-eval="specimen" style="writing-mode:horizontal-tb">字樣</div>
    <script>
      const toggle = document.querySelector('[data-eval="writing-toggle"]');
      const specimen = document.querySelector('[data-eval="specimen"]');
      toggle.addEventListener('click', () => {{
        toggle.setAttribute('aria-pressed', 'true');
        specimen.style.writingMode = 'vertical-rl';
      }});
    </script>
  `);
  const evidence = await runCaseInteraction(page, 'type-foundry-specimen-v6', {{ name: 'desktop' }}, 'index.html');
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertIn("type_writing_mode_round_trip_failed", result["failures"])

    def test_type_foundry_capture_rejects_delayed_reversion(self) -> None:
        source = f"""
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {{ chromium }} = require('playwright');
const {{ captureAuditedScreenshot, runCaseInteraction }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent(`
    <button data-eval="writing-toggle" type="button" aria-pressed="false">切換</button>
    <div data-eval="specimen" style="writing-mode:horizontal-tb">字樣</div>
    <script>
      const toggle = document.querySelector('[data-eval="writing-toggle"]');
      const specimen = document.querySelector('[data-eval="specimen"]');
      let clicks = 0;
      toggle.addEventListener('click', () => {{
        clicks += 1;
        const active = toggle.getAttribute('aria-pressed') === 'true';
        toggle.setAttribute('aria-pressed', String(!active));
        specimen.style.writingMode = active ? 'horizontal-tb' : 'vertical-rl';
        if (clicks === 3) setTimeout(() => {{
          toggle.setAttribute('aria-pressed', 'false');
          specimen.style.writingMode = 'horizontal-tb';
        }}, 50);
      }});
    </script>
  `);
  const evidence = await runCaseInteraction(page, 'type-foundry-specimen-v6', {{ name: 'desktop' }}, 'index.html');
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'wow-round-trip-'));
  await captureAuditedScreenshot(page, path.join(directory, 'capture.png'), evidence);
  await browser.close();
  fs.rmSync(directory, {{ recursive: true, force: true }});
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertIn("type_writing_mode_screenshot_state_failed", result["failures"])
        self.assertFalse(result["screenshotState"]["verified"])

    def test_packaging_summary_replays_reset_then_resubmits(self) -> None:
        source = AUDITOR.read_text(encoding="utf-8")
        start = source.index('} else if (caseId === "packaging-configurator-v6" && pageName === "summary.html")')
        end = source.index('} else if (caseId === "oral-history-archive-v6")', start)
        summary_flow = source[start:end]
        submit = 'await page.locator(\'#submit-action\').click();'
        self.assertGreaterEqual(summary_flow.count(submit), 2)
        first_submit = summary_flow.index(submit)
        reset = summary_flow.index('reset.click()', first_submit)
        restore = summary_flow.index('await page.goto(summaryUrl', reset)
        second_submit = summary_flow.index(submit, restore)
        self.assertLess(first_submit, reset)
        self.assertLess(reset, restore)
        self.assertLess(restore, second_submit)
        self.assertIn("evidence.postResetSubmitted", summary_flow)
        self.assertIn("packaging_summary_post_reset_state_failed", summary_flow)

    def test_noninteractive_page_is_not_reported_as_behavioral_pass(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ runCaseInteraction }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent('<div data-eval="archive-shell">靜態內容</div>');
  const evidence = await runCaseInteraction(page, 'oral-history-archive-v6', {{ name: 'desktop' }}, 'archive.html');
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertIn("interaction_not_applicable", result["failures"])

    def test_mobile_profiles_use_real_mobile_emulation_signals(self) -> None:
        source = f"""
const {{ VIEWPORTS }} = require({json.dumps(str(AUDITOR))});
process.stdout.write(JSON.stringify(VIEWPORTS.filter((viewport) => viewport.name.includes('mobile'))));
"""
        profiles = self.run_node(source)
        self.assertEqual(2, len(profiles))
        for profile in profiles:
            self.assertTrue(profile["isMobile"])
            self.assertTrue(profile["hasTouch"])
            self.assertEqual(3, profile["deviceScaleFactor"])
            self.assertIn("Android", profile["userAgent"])

    def test_readable_text_roots_include_top_layer_and_portal_dialogs(self) -> None:
        source = f"""
const {{ PRODUCT_TEXT_ROOT_SELECTOR }} = require({json.dumps(str(AUDITOR))});
process.stdout.write(JSON.stringify(PRODUCT_TEXT_ROOT_SELECTOR));
"""
        selector = self.run_node(source)
        self.assertIn("main", selector)
        self.assertIn("dialog[open]", selector)
        self.assertIn("[role='dialog'][aria-modal='true']", selector)
        auditor_source = AUDITOR.read_text(encoding="utf-8")
        self.assertNotIn('querySelectorAll("main p, main li")', auditor_source)
        self.assertIn('const readableNodes = productTextNodes("p, li")', auditor_source)
        self.assertIn('const narrowTextColumns = productTextNodes("p, li")', auditor_source)
        self.assertIn('const bodyFlowNodes = productTextNodes("p, li")', auditor_source)
        self.assertIn('...productTextNodes("p")', auditor_source)
        self.assertIn('!isolatedBehindModal(root)', auditor_source)
        self.assertIn('!isolatedBehindModal(node)', auditor_source)

    def test_grant_interaction_follows_mobile_case_navigation(self) -> None:
        source = f"""
const {{ grantInteractionPlan }} = require({json.dumps(str(AUDITOR))});
process.stdout.write(JSON.stringify({{
  desktop: grantInteractionPlan('desktop'),
  mobile: grantInteractionPlan('mobile'),
}}));
"""
        result = self.run_node(source)
        self.assertFalse(result["desktop"]["usesCaseNavigation"])
        self.assertEqual(6, result["desktop"]["expectedVisibleRecords"])
        self.assertTrue(result["mobile"]["usesCaseNavigation"])
        self.assertEqual(1, result["mobile"]["expectedVisibleRecords"])

    def test_grant_interaction_rejects_modal_without_recovery_contract(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ runCaseInteraction }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent(`
    <main data-eval="grant-board">
      <div data-eval="proposal-row" data-record-id="a">
        <button data-eval="shortlist-action">加入 A</button>
        <button data-eval="compare-a-action">比較 A</button>
        <button data-eval="compare-b-action">比較 B</button>
      </div>
      <div data-eval="proposal-row" data-record-id="b">
        <button data-eval="shortlist-action">加入 B</button>
        <button data-eval="compare-a-action">比較 A</button>
        <button data-eval="compare-b-action">比較 B</button>
      </div>
      <div data-eval="compare-panel"></div>
      <button data-eval="decision-action">開啟決策</button>
    </main>
    <div data-eval="decision-modal" hidden>
      <button type="button">送出</button>
    </div>
    <button data-eval="retry-action" hidden>重試</button>
    <script>
      document.querySelector('[data-eval="decision-action"]').addEventListener('click', () =>
        document.querySelector('[data-eval="decision-modal"]').hidden = false
      );
    </script>
  `);
  const evidence = await runCaseInteraction(page, 'grant-review-board-v6', {{ name: 'desktop' }}, 'index.html');
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertIn("grant_modal_accessible_name_missing", result["failures"])
        self.assertIn("grant_modal_focus_containment_failed", result["failures"])
        self.assertIn("grant_decision_retry_state_failed", result["failures"])

    def test_interaction_settle_waits_for_two_rendered_frames(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ waitForRenderedStateToSettle }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent('<style>#control {{ transition: transform 0.01ms linear }} #control.done {{ transform: translateY(-1px) }}</style><button id="control">原始狀態</button><span id="delayed"></span><span id="repeated"></span><span id="paused"></span><span id="zero-rate"></span><span id="slow-rate"></span>');
  await page.evaluate(() => {{
    const control = document.querySelector('#control');
    void control.offsetWidth;
    control.classList.add('done');
    window.__delayedAnimation = document.querySelector('#delayed').animate(
      [{{ opacity: 0 }}, {{ opacity: 1 }}],
      {{ duration: 1, delay: 500 }},
    );
    window.__repeatedAnimation = document.querySelector('#repeated').animate(
      [{{ opacity: 0 }}, {{ opacity: 1 }}],
      {{ duration: 10, iterations: 60 }},
    );
    window.__pausedAnimation = document.querySelector('#paused').animate(
      [{{ opacity: 0 }}, {{ opacity: 1 }}],
      {{ duration: 1 }},
    );
    window.__pausedAnimation.pause();
    window.__zeroRateAnimation = document.querySelector('#zero-rate').animate(
      [{{ opacity: 0 }}, {{ opacity: 1 }}],
      {{ duration: 1 }},
    );
    window.__zeroRateAnimation.playbackRate = 0;
    window.__slowRateAnimation = document.querySelector('#slow-rate').animate(
      [{{ opacity: 0 }}, {{ opacity: 1 }}],
      {{ duration: 1 }},
    );
    window.__slowRateAnimation.playbackRate = 0.001;
  }});
  await waitForRenderedStateToSettle(page);
  const result = await page.evaluate(() => ({{
    animations: document.getAnimations().length,
    delayedPlayState: window.__delayedAnimation.playState,
    pausedPlayState: window.__pausedAnimation.playState,
    repeatedPlayState: window.__repeatedAnimation.playState,
    slowRatePlayState: window.__slowRateAnimation.playState,
    transform: getComputedStyle(document.querySelector('#control')).transform,
    zeroRatePlayState: window.__zeroRateAnimation.playState,
  }}));
  await browser.close();
  process.stdout.write(JSON.stringify(result));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        completed = subprocess.run(
            ["node", "-e", source],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(5, result["animations"])
        self.assertEqual("running", result["delayedPlayState"])
        self.assertEqual("paused", result["pausedPlayState"])
        self.assertEqual("running", result["repeatedPlayState"])
        self.assertEqual("running", result["slowRatePlayState"])
        self.assertNotEqual("none", result["transform"])
        self.assertEqual("running", result["zeroRatePlayState"])

    def test_interaction_settle_uses_an_isolated_world(self) -> None:
        source = f"""
const {{ performance }} = require('node:perf_hooks');
const {{ chromium }} = require('playwright');
const {{ waitForRenderedStateToSettle }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent('<style>#control {{ transition: transform 0.01ms linear }} #control.done {{ transform: translateY(-1px) }}</style><span id="control"></span>');
  await page.evaluate(() => {{
    const control = document.querySelector('#control');
    void control.offsetWidth;
    control.classList.add('done');
    document.getAnimations = () => [{{ finished: new Promise(() => {{}}) }}];
    window.requestAnimationFrame = () => 0;
  }});
  const startedAt = performance.now();
  await waitForRenderedStateToSettle(page);
  const elapsedMs = performance.now() - startedAt;
  const transform = await page.locator('#control').evaluate((node) => getComputedStyle(node).transform);
  await browser.close();
  process.stdout.write(JSON.stringify({{ elapsedMs, transform }}));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        completed = subprocess.run(
            ["node", "-e", source],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
        result = json.loads(completed.stdout)
        self.assertLess(result["elapsedMs"], 250)
        self.assertNotEqual("none", result["transform"])

    def test_novel_focus_probe_reports_missing_indicator(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ runKeyboardFocusProbe }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent('<style>button:focus {{ outline: none; box-shadow: none; }}</style><button>送出</button>');
  const evidence = await runKeyboardFocusProbe(page, 'index.html', 'desktop', 1);
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertEqual("candidate", result["outcome"])
        self.assertIn("focus-style-changed:false", result["evidence"])

    def test_novel_focus_probe_checks_all_controls_and_ignores_color_only_delta(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ runKeyboardFocusProbe }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent(`
    <style>
      button:focus-visible {{ outline: 3px solid currentColor; outline-offset: 2px; }}
      button:nth-of-type(2):focus-visible {{ outline: none; color: rgb(0, 0, 1); }}
    </style>
    <button>有 focus 框</button><button>只有顏色差</button>
  `);
  const evidence = await runKeyboardFocusProbe(page, 'index.html', 'desktop', 1);
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertEqual("candidate", result["outcome"])
        self.assertIn("focus-observations:3", result["evidence"])
        self.assertIn("focus-missing-indicators:1", result["evidence"])

    def test_novel_focus_probe_rejects_transparent_focus_paint(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ runKeyboardFocusProbe }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent('<style>button:focus-visible {{ outline: 3px solid transparent; outline-offset: 2px; }}</style><button>不可見 focus</button>');
  const evidence = await runKeyboardFocusProbe(page, 'index.html', 'desktop', 1);
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertEqual("candidate", result["outcome"])
        self.assertIn("focus-missing-indicators:1", result["evidence"])

    def test_novel_focus_probe_rejects_tab_cycle_that_skips_a_control(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ runKeyboardFocusProbe }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent(`
    <style>button:focus-visible {{ outline: 3px solid currentColor; outline-offset: 2px; }}</style>
    <button id="reachable">可達</button><button id="skipped">被跳過</button>
    <script>document.addEventListener('keydown', (event) => {{ if (event.key === 'Tab') {{ event.preventDefault(); document.querySelector('#reachable').focus(); }} }});</script>
  `);
  const evidence = await runKeyboardFocusProbe(page, 'index.html', 'desktop', 1);
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertEqual("candidate", result["outcome"])
        self.assertIn("focus-uncovered-controls:1", result["evidence"])

    def test_novel_focus_probe_includes_native_media_controls(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ runKeyboardFocusProbe }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent(`
    <style>button:focus-visible, audio:focus-visible {{ outline: 3px solid currentColor; outline-offset: 2px; }} audio.bad:focus-visible {{ outline: none; }}</style>
    <button>按鈕</button><audio controls></audio><audio class="bad" controls></audio>
  `);
  const evidence = await runKeyboardFocusProbe(page, 'index.html', 'desktop', 1);
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertEqual("candidate", result["outcome"])
        self.assertIn("focusable-count:3", result["evidence"])
        self.assertIn("focus-uncovered-controls:1", result["evidence"])

    def test_novel_focus_probe_rejects_focus_paint_without_contrast(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ runKeyboardFocusProbe }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent(`<style>body {{ background: white; }} button:focus-visible {{ outline: 4px solid white; outline-offset: 2px; }}</style><button>白底白框</button>`);
  const evidence = await runKeyboardFocusProbe(page, 'index.html', 'desktop', 1);
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertEqual("candidate", result["outcome"])
        self.assertIn("focus-missing-indicators:1", result["evidence"])

    def test_novel_focus_probe_rejects_low_contrast_focus_paint(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ runKeyboardFocusProbe }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent(`<style>body {{ background: rgb(118,118,118); }} button:focus-visible {{ outline: 4px solid rgb(100,100,100); }}</style><button>低對比</button>`);
  const evidence = await runKeyboardFocusProbe(page, 'index.html', 'desktop', 1);
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertEqual("candidate", result["outcome"])
        self.assertIn("focus-missing-indicators:1", result["evidence"])

    def test_novel_focus_probe_composites_translucent_ancestor_background(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ runKeyboardFocusProbe }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent(`<style>html,body {{ background: white; }} .panel {{ background: rgba(0,0,0,.5); padding: 8px; }} button:focus-visible {{ outline: 4px solid black; outline-offset: 3px; }}</style><div class="panel"><button>半透明面板</button></div>`);
  const evidence = await runKeyboardFocusProbe(page, 'index.html', 'desktop', 1);
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertEqual("pass", result["outcome"])
        self.assertIn("focus-missing-indicators:0", result["evidence"])

    def test_novel_focus_probe_accounts_for_ancestor_opacity(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ runKeyboardFocusProbe }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent(`<style>body {{ background: white; }} .panel {{ opacity: .5; }} button:focus-visible {{ outline: 4px solid rgb(100,100,100); }}</style><div class="panel"><button>半透明 focus</button></div>`);
  const evidence = await runKeyboardFocusProbe(page, 'index.html', 'desktop', 1);
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertEqual("candidate", result["outcome"])
        self.assertIn("focus-missing-indicators:1", result["evidence"])

    def test_novel_focus_probe_excludes_nonsequential_controls_from_coverage(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ runKeyboardFocusProbe }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent(`
    <style>button:focus-visible {{ outline: 3px solid currentColor; outline-offset: 2px; }}</style>
    <button id="reachable">可達</button><button id="disabled" disabled>停用</button>
    <button id="hidden" hidden>隱藏</button><button id="negative" tabindex="-2">負索引</button>
  `);
  const evidence = await runKeyboardFocusProbe(page, 'index.html', 'desktop', 1);
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertEqual("pass", result["outcome"])
        self.assertIn("focusable-count:1", result["evidence"])
        self.assertNotIn("focus-uncovered-controls", " ".join(result["evidence"]))

    def test_novel_focus_probe_rejects_suppressed_paint_and_zero_geometry_shadow(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ runKeyboardFocusProbe }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setContent(`
    <style>
      button:focus-visible {{ outline: none; box-shadow: 0 0 0 0 rgb(0 0 0); }}
      #suppressed {{ opacity: 0; outline: 3px solid black; }}
      #clipped {{ clip-path: inset(100%); outline: 3px solid black; }}
    </style>
    <button id="suppressed">透明 focus</button><button id="zero-shadow">零幾何</button><button id="clipped">裁切 focus</button>
  `);
  const evidence = await runKeyboardFocusProbe(page, 'index.html', 'desktop', 1);
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertEqual("candidate", result["outcome"])
        self.assertIn("focus-missing-indicators:3", result["evidence"])

    def test_novel_discovery_uses_fresh_context_for_each_replay(self) -> None:
        source = AUDITOR.read_text(encoding="utf-8")
        start = source.index("async function runNovelDiscovery")
        end = source.index("async function", start + len("async function"))
        function = source[start:end]
        pass_loop = function.index("for (let pass = 1; pass <= 2; pass += 1)")
        self.assertGreater(function.index("browser.newContext(contextOptions)", pass_loop), pass_loop)
        self.assertIn("finally {\n        if (context) await context.close();", function[pass_loop:])

    def test_font_evidence_rejects_hidden_active_typography_animations(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ collectFontEvidence, waitForRenderedStateToSettle }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const context = await browser.newContext();
  const page = await context.newPage();
  async function probe(property, fromValue, toValue) {{
    await page.setContent('<h1 style="font-family:Arial,sans-serif">繁中 ABC 動態排版</h1>');
    await page.evaluate(({{ property, fromValue, toValue }}) => {{
      document.querySelector('h1').animate(
        [{{ [property]: fromValue }}, {{ [property]: toValue }}],
        {{ duration: 10000, iterations: Infinity }},
      );
      document.getAnimations = () => [];
      window.requestAnimationFrame = (callback) => queueMicrotask(() => callback(performance.now()));
    }}, {{ property, fromValue, toValue }});
    await waitForRenderedStateToSettle(page);
    const evidence = await collectFontEvidence(context, page);
    return {{ status: evidence.status, error: evidence.error }};
  }}
  async function shadowProbe(mode) {{
    await page.setContent('<h1>繁中 ABC 標題</h1><main><button id="control">儲存</button></main>');
    await page.evaluate((mode) => {{
      const host = document.createElement('x-shadow');
      document.querySelector('#control').append(host);
      const root = host.attachShadow({{ mode }});
      const span = document.createElement('span');
      span.textContent = '影子 ABC';
      root.append(span);
      span.animate(
        [{{ fontSize: '16px' }}, {{ fontSize: '32px' }}],
        {{ duration: 10000, iterations: Infinity }},
      );
      document.getAnimations = () => [];
    }}, mode);
    await waitForRenderedStateToSettle(page);
    const evidence = await collectFontEvidence(context, page);
    return {{ status: evidence.status, error: evidence.error }};
  }}
  async function slotProbe() {{
    await page.setContent('<h1>繁中 ABC 標題</h1><main><button id="control">儲存</button></main>');
    await page.evaluate(() => {{
      const host = document.createElement('x-slot');
      host.innerHTML = '<span>插槽 ABC</span>';
      document.querySelector('#control').append(host);
      const root = host.attachShadow({{ mode: 'open' }});
      root.innerHTML = '<slot></slot>';
      root.querySelector('slot').animate(
        [{{ transform: 'none' }}, {{ transform: 'translateX(20px)' }}],
        {{ duration: 10000, iterations: Infinity }},
      );
      document.getAnimations = () => [];
    }});
    await waitForRenderedStateToSettle(page);
    const evidence = await collectFontEvidence(context, page);
    return {{ status: evidence.status, error: evidence.error }};
  }}
  async function pseudoProbe(mode) {{
    await page.setContent('<h1>繁中 ABC 標題</h1><main><button id="control">儲存</button></main>');
    await page.evaluate((mode) => {{
      const css = `
        @keyframes pseudo-shift {{ from {{ transform: none }} to {{ transform: translateX(20px) }} }}
        span::before {{ content: "偽元素 ABC"; animation: pseudo-shift 10s linear infinite }}
      `;
      if (mode === 'light') {{
        const style = document.createElement('style');
        style.textContent = css;
        document.head.append(style);
        document.querySelector('#control').append(document.createElement('span'));
      }} else {{
        const host = document.createElement('x-pseudo');
        document.querySelector('#control').append(host);
        const root = host.attachShadow({{ mode: 'closed' }});
        const style = document.createElement('style');
        style.textContent = css;
        root.append(style, document.createElement('span'));
      }}
      document.getAnimations = () => [];
    }}, mode);
    await waitForRenderedStateToSettle(page);
    const evidence = await collectFontEvidence(context, page);
    return {{ status: evidence.status, error: evidence.error }};
  }}
  async function shadowControlProbe(mode, animated) {{
    await page.setContent('<h1>繁中 ABC 標題</h1><main><x-button></x-button></main>');
    await page.evaluate(({{ mode, animated }}) => {{
      const root = document.querySelector('x-button').attachShadow({{ mode }});
      root.innerHTML = '<button>影子操作 ABC</button>';
      if (animated) {{
        root.querySelector('button').animate(
          [{{ transform: 'translateX(0)' }}, {{ transform: 'translateX(80px)' }}],
          {{ duration: 10000, iterations: Infinity }},
        );
      }}
    }}, {{ mode, animated }});
    const evidence = await collectFontEvidence(context, page);
    return {{
      status: evidence.status,
      error: evidence.error,
      shadowRole: evidence.roles.some((role) => role.role === 'interface-control' && role.text.includes('影子操作 ABC')),
    }};
  }}
  async function decorativePseudoProbe(mode, content = '\"\"', quotes = 'auto') {{
    await page.setContent('<h1>繁中 ABC 標題</h1><main><button id="control">儲存</button></main>');
    await page.evaluate(({{ mode, content, quotes }}) => {{
      const css = `
        @keyframes icon-spin {{ from {{ transform: none }} to {{ transform: rotate(360deg) }} }}
        span::before {{ content: ${{content}}; quotes: ${{quotes}}; display: block; position: absolute; width: 10px; height: 10px;
          background: red; animation: icon-spin 10s linear infinite }}
      `;
      if (mode === 'light') {{
        const style = document.createElement('style');
        style.textContent = css;
        document.head.append(style);
        document.querySelector('#control').append(document.createElement('span'));
      }} else {{
        const host = document.createElement('x-icon');
        document.querySelector('#control').append(host);
        const root = host.attachShadow({{ mode }});
        const style = document.createElement('style');
        style.textContent = css;
        root.append(style, document.createElement('span'));
      }}
    }}, {{ mode, content, quotes }});
    const evidence = await collectFontEvidence(context, page);
    return {{ status: evidence.status, error: evidence.error }};
  }}
  async function hiddenRoleProbe(mode, hiddenStyle = 'display:none', animatedProperty = 'transform') {{
    await page.setContent('<h1>可見標題 ABC</h1><main id="main"></main>');
    await page.evaluate(({{ mode, hiddenStyle, animatedProperty }}) => {{
      let button;
      if (mode === 'light') {{
        button = document.createElement('button');
        document.querySelector('#main').append(button);
      }} else {{
        const host = document.createElement('x-hidden');
        document.querySelector('#main').append(host);
        const root = host.attachShadow({{ mode }});
        button = document.createElement('button');
        root.append(button);
      }}
      button.textContent = '隱藏操作 ABC';
      button.style.cssText = hiddenStyle;
      button.animate(
        animatedProperty === 'color'
          ? [{{ color: 'red' }}, {{ color: 'blue' }}]
          : [{{ transform: 'translateX(0)' }}, {{ transform: 'translateX(80px)' }}],
        {{ duration: 10000, iterations: Infinity }},
      );
    }}, {{ mode, hiddenStyle, animatedProperty }});
    const evidence = await collectFontEvidence(context, page);
    return {{ status: evidence.status, error: evidence.error }};
  }}
  async function hiddenTextProbe(hiddenStyle) {{
    await page.setContent('<h1>可見標題 ABC</h1><main><button id="control">儲存<span>隱藏 ABC</span></button></main>');
    await page.evaluate((hiddenStyle) => {{
      const span = document.querySelector('span');
      span.style.cssText = `display:inline-block;${{hiddenStyle}}`;
      span.animate(
        [{{ transform: 'translateX(0)' }}, {{ transform: 'translateX(80px)' }}],
        {{ duration: 10000, iterations: Infinity }},
      );
    }}, hiddenStyle);
    const evidence = await collectFontEvidence(context, page);
    return {{ status: evidence.status, error: evidence.error }};
  }}
  async function visibilityOverrideProbe() {{
    await page.setContent('<h1>可見標題 ABC</h1><main><button id="control">儲存<span id="box"><span>文字 ABC</span></span></button></main>');
    await page.evaluate(() => {{
      const box = document.querySelector('#box');
      box.style.cssText = 'display:inline-block;visibility:hidden';
      box.firstElementChild.style.visibility = 'visible';
      box.animate(
        [{{ transform: 'translateX(0)' }}, {{ transform: 'translateX(80px)' }}],
        {{ duration: 10000, iterations: Infinity }},
      );
    }});
    const evidence = await collectFontEvidence(context, page);
    return {{ status: evidence.status, error: evidence.error }};
  }}
  async function noOpProbe() {{
    await page.setContent('<h1>繁中 ABC 標題</h1><main><button id="control">儲存</button></main>');
    await page.evaluate(() => {{
      document.querySelector('#control').animate(
        [{{ transform: 'none' }}, {{ transform: 'none' }}],
        {{ duration: 10000, iterations: Infinity }},
      );
    }});
    const evidence = await collectFontEvidence(context, page);
    return {{ status: evidence.status, error: evidence.error }};
  }}
  async function decorativeIconProbe() {{
    await page.setContent('<h1>繁中 ABC 標題</h1><main><button id="control">儲存<svg aria-hidden="true" style="position:absolute" viewBox="0 0 10 10"><circle cx="5" cy="5" r="4"></circle></svg></button></main>');
    await page.evaluate(() => {{
      document.querySelector('svg').animate(
        [{{ transform: 'rotate(0deg)' }}, {{ transform: 'rotate(360deg)' }}],
        {{ duration: 10000, iterations: Infinity }},
      );
    }});
    const evidence = await collectFontEvidence(context, page);
    return {{ status: evidence.status, error: evidence.error }};
  }}
  const evidence = {{
    closedShadow: await shadowProbe('closed'),
    decorativePseudoClosed: await decorativePseudoProbe('closed'),
    decorativePseudoAltOnly: await decorativePseudoProbe('light', '\"\" / \"替代文字\"'),
    decorativePseudoLight: await decorativePseudoProbe('light'),
    decorativePseudoNoOpenClosed: await decorativePseudoProbe('closed', 'no-open-quote'),
    decorativePseudoNoOpenLight: await decorativePseudoProbe('light', 'no-open-quote'),
    decorativePseudoNoOpenOpen: await decorativePseudoProbe('open', 'no-open-quote'),
    decorativePseudoOpen: await decorativePseudoProbe('open'),
    decorativePseudoOpenQuoteNone: await decorativePseudoProbe('light', 'open-quote', 'none'),
    decorativeIcon: await decorativeIconProbe(),
    fontFamily: await probe('fontFamily', 'Arial, sans-serif', 'serif'),
    fontSizeAdjust: await probe('fontSizeAdjust', 'none', '0.5'),
    hiddenRoleClosed: await hiddenRoleProbe('closed'),
    hiddenRoleLight: await hiddenRoleProbe('light'),
    hiddenRoleOpen: await hiddenRoleProbe('open'),
    hiddenRoleClip: await hiddenRoleProbe('light', 'clip-path:inset(50%)'),
    hiddenRoleFilter: await hiddenRoleProbe('light', 'filter:opacity(0)'),
    hiddenRoleScaleX: await hiddenRoleProbe('light', 'transform:scaleX(0)', 'color'),
    hiddenTextOpacity: await hiddenTextProbe('opacity:0'),
    hiddenTextVisibility: await hiddenTextProbe('visibility:hidden'),
    noOp: await noOpProbe(),
    openShadow: await shadowProbe('open'),
    pseudoClosedShadow: await pseudoProbe('closed'),
    pseudoLight: await pseudoProbe('light'),
    shadowControlClosed: await shadowControlProbe('closed', true),
    shadowControlOpen: await shadowControlProbe('open', true),
    shadowControlStaticClosed: await shadowControlProbe('closed', false),
    shadowControlStaticOpen: await shadowControlProbe('open', false),
    slot: await slotProbe(),
    textAlign: await probe('textAlign', 'left', 'right'),
    transform: await probe('transform', 'translateX(0)', 'translateX(40px)'),
    visibilityOverride: await visibilityOverrideProbe(),
    verticalAlign: await probe('verticalAlign', 'baseline', '20px'),
    wordSpacing: await probe('wordSpacing', '0px', '40px'),
  }};
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        completed = subprocess.run(
            ["node", "-e", source],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        result = json.loads(completed.stdout)
        for property_name in (
            "closedShadow", "fontFamily", "fontSizeAdjust", "openShadow", "pseudoClosedShadow",
            "pseudoLight", "shadowControlClosed", "shadowControlOpen", "slot", "textAlign",
            "transform", "verticalAlign", "visibilityOverride", "wordSpacing",
        ):
            self.assertEqual("unavailable", result[property_name]["status"], property_name)
            self.assertIn("active rendered-text animation", result[property_name]["error"], result)
        self.assertEqual("captured", result["noOp"]["status"])
        self.assertEqual("captured", result["decorativeIcon"]["status"])
        for probe_name in (
            "decorativePseudoAltOnly", "decorativePseudoClosed", "decorativePseudoLight",
            "decorativePseudoNoOpenClosed", "decorativePseudoNoOpenLight",
            "decorativePseudoNoOpenOpen", "decorativePseudoOpen", "decorativePseudoOpenQuoteNone",
            "hiddenRoleClosed", "hiddenRoleLight", "hiddenRoleOpen",
            "hiddenRoleClip", "hiddenRoleFilter", "hiddenRoleScaleX",
            "hiddenTextOpacity", "hiddenTextVisibility",
            "shadowControlStaticClosed", "shadowControlStaticOpen",
        ):
            self.assertEqual("captured", result[probe_name]["status"], (probe_name, result))
        self.assertTrue(result["shadowControlStaticClosed"]["shadowRole"])
        self.assertTrue(result["shadowControlStaticOpen"]["shadowRole"])

    def test_audit_keeps_unstable_font_evidence_as_structured_issue(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ captureFontEvidenceForAudit, waitForRenderedStateToSettle }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.setContent('<h1 style="font-family:Arial,sans-serif">繁中 ABC 動態排版</h1>');
  await page.locator('h1').evaluate((node) => node.animate(
    [{{ fontSize: '16px' }}, {{ fontSize: '32px' }}],
    {{ duration: 10000, iterations: Infinity }},
  ));
  await waitForRenderedStateToSettle(page);
  const evidence = await captureFontEvidenceForAudit(context, page, 'fixture/desktop/interaction');
  await browser.close();
  process.stdout.write(JSON.stringify(evidence));
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertEqual("unavailable", result["status"])
        self.assertIn("active rendered-text animation", result["error"])

    def test_actual_font_mismatch_requires_a_failed_declared_face(self) -> None:
        source = f"""
const {{ assertFontEvidenceComplete, classifyPrimaryFontUsage, firstDeclaredFontFamily, primaryFontMismatch }} = require({json.dumps(str(AUDITOR))});
const actualNoto = [{{ familyName: 'Noto Serif TC', glyphCount: 12 }}];
const actualSongti = [{{ familyName: 'Songti TC', glyphCount: 12 }}];
const failedFace = [{{ family: 'Noto Serif TC', status: 'error' }}];
const loadedAlias = [{{ family: 'BrandAlias', status: 'loaded' }}];
let unavailableThrows = false;
try {{ assertFontEvidenceComplete({{ status: 'unavailable', error: 'cdp failed', roles: [] }}); }} catch {{ unavailableThrows = true; }}
process.stdout.write(JSON.stringify({{
  parsed: firstDeclaredFontFamily('"Noto Serif TC", "Source Han Serif TC", serif'),
  parsedComma: firstDeclaredFontFamily('"Example, Serif", serif'),
  fallback: classifyPrimaryFontUsage({{ declaredPrimary: 'Noto Serif TC', text: '繁中 ABC 2026', actualFonts: actualSongti }}),
  failed: primaryFontMismatch({{ declaredPrimary: 'Noto Serif TC', declaredFaceCheck: false, declaredFaceSelectionFailed: true, text: '繁中 ABC 2026', actualFonts: actualSongti, fontFaces: failedFace }}),
  alias: classifyPrimaryFontUsage({{ declaredPrimary: 'BrandAlias', text: '繁中 ABC 2026', actualFonts: [{{ familyName: 'Arial', glyphCount: 12 }}], fontFaces: loadedAlias }}),
  weight400: classifyPrimaryFontUsage({{ declaredPrimary: 'MultiFace', declaredFaceCheck: true, fontStyle: 'normal', fontWeight: '400', fontStretch: '100%', text: '繁中 ABC', actualFonts: actualSongti, fontFaces: [{{ family: 'MultiFace', style: 'normal', weight: '400', stretch: 'normal', status: 'loaded' }}, {{ family: 'MultiFace', style: 'normal', weight: '700', stretch: 'normal', status: 'error' }}] }}),
  weight700: classifyPrimaryFontUsage({{ declaredPrimary: 'MultiFace', declaredFaceCheck: false, declaredFaceSelectionFailed: true, fontStyle: 'normal', fontWeight: '700', fontStretch: '100%', text: '繁中 ABC', actualFonts: actualSongti, fontFaces: [{{ family: 'MultiFace', style: 'normal', weight: '400', stretch: 'normal', status: 'loaded' }}, {{ family: 'MultiFace', style: 'normal', weight: '700', stretch: 'normal', status: 'error' }}] }}),
  styleNormal: classifyPrimaryFontUsage({{ declaredPrimary: 'StyleFace', declaredFaceCheck: true, fontStyle: 'normal', fontWeight: '400', text: '繁中 ABC', actualFonts: actualSongti, fontFaces: [{{ family: 'StyleFace', style: 'normal', weight: '400', status: 'loaded' }}, {{ family: 'StyleFace', style: 'italic', weight: '400', status: 'error' }}] }}),
  styleItalic: classifyPrimaryFontUsage({{ declaredPrimary: 'StyleFace', declaredFaceCheck: false, declaredFaceSelectionFailed: true, fontStyle: 'italic', fontWeight: '400', text: '繁中 ABC', actualFonts: actualSongti, fontFaces: [{{ family: 'StyleFace', style: 'normal', weight: '400', status: 'loaded' }}, {{ family: 'StyleFace', style: 'italic', weight: '400', status: 'error' }}] }}),
  rendered: primaryFontMismatch({{ declaredPrimary: 'Noto Serif TC', text: '繁中 ABC 2026', actualFonts: actualNoto }}),
  postScript: primaryFontMismatch({{ declaredPrimary: 'SFMono-Regular', text: '繁中 ABC 2026', actualFonts: [{{ familyName: 'SF Mono', postScriptName: 'SFMono-Regular', glyphCount: 8 }}] }}),
  emojiFallback: primaryFontMismatch({{ declaredPrimary: 'Noto Serif TC', text: '繁中 ABC 2026 😀', actualFonts: [...actualNoto, {{ familyName: 'Apple Color Emoji', glyphCount: 1 }}] }}),
  zeroGlyph: primaryFontMismatch({{ declaredPrimary: 'Noto Serif TC', text: '繁中 ABC 2026', actualFonts: [{{ familyName: 'Songti TC', glyphCount: 0 }}] }}),
  noEvidence: primaryFontMismatch({{ declaredPrimary: 'Noto Serif TC', text: '繁中 ABC 2026', actualFonts: [] }}),
  generic: primaryFontMismatch({{ declaredPrimary: 'serif', text: '繁中 ABC 2026', actualFonts: actualSongti }}),
  quotedGeneric: classifyPrimaryFontUsage({{ declaredPrimary: 'serif', declaredPrimaryQuoted: true, text: '繁中 ABC 2026', actualFonts: actualSongti }}),
  genericFunction: primaryFontMismatch({{ declaredPrimary: 'generic(fangsong)', text: '繁中 ABC 2026', actualFonts: actualSongti }}),
  singleScript: primaryFontMismatch({{ declaredPrimary: 'Noto Serif TC', text: '繁體中文', actualFonts: actualSongti }}),
  emojiOnly: primaryFontMismatch({{ declaredPrimary: 'Noto Serif TC', text: '😀', actualFonts: [{{ familyName: 'Apple Color Emoji', glyphCount: 1 }}] }}),
  emojiFailed: primaryFontMismatch({{ declaredPrimary: 'Noto Serif TC', declaredFaceCheck: false, declaredFaceSelectionFailed: false, text: '😀', actualFonts: [{{ familyName: 'Apple Color Emoji', glyphCount: 1 }}], fontFaces: failedFace }}),
  unavailableThrows,
}}));
"""
        result = self.run_node(source)
        self.assertEqual("Noto Serif TC", result["parsed"])
        self.assertEqual("Example, Serif", result["parsedComma"])
        self.assertEqual("fallback_rendered", result["fallback"])
        self.assertTrue(result["failed"])
        self.assertEqual("unverified_alias", result["alias"])
        self.assertEqual("unverified_alias", result["weight400"])
        self.assertEqual("failed_font_face", result["weight700"])
        self.assertEqual("unverified_alias", result["styleNormal"])
        self.assertEqual("failed_font_face", result["styleItalic"])
        self.assertFalse(result["rendered"])
        self.assertFalse(result["postScript"])
        self.assertFalse(result["emojiFallback"])
        self.assertFalse(result["zeroGlyph"])
        self.assertFalse(result["noEvidence"])
        self.assertFalse(result["generic"])
        self.assertEqual("fallback_rendered", result["quotedGeneric"])
        self.assertFalse(result["genericFunction"])
        self.assertFalse(result["singleScript"])
        self.assertFalse(result["emojiOnly"])
        self.assertFalse(result["emojiFailed"])
        self.assertTrue(result["unavailableThrows"])
        self.assertGreaterEqual(
            AUDITOR.read_text(encoding="utf-8").count("await page.evaluate(() => document.fonts.ready)"),
            2,
        )

    def test_font_evidence_browser_probe_handles_fallback_alias_failure_and_empty_scope(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ collectFontEvidence }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const context = await browser.newContext();
  const page = await context.newPage();
  async function probe(html) {{
    await page.setContent(html);
    await page.evaluate(() => document.fonts.ready);
    return collectFontEvidence(context, page);
  }}
  const fallback = await probe(`<style>h1{{font-family:"Absent Named Face",serif}}</style><h1>繁中 ABC 2026</h1>`);
  const alias = await probe(`<style>@font-face{{font-family:BrandAlias;src:local("Arial")}}h1{{font-family:BrandAlias,serif}}</style><h1>繁中 ABC 2026</h1>`);
  const failed = await probe(`<style>@font-face{{font-family:BrokenFace;src:url("data:font/woff2;base64,AA==")}}h1{{font-family:BrokenFace,serif}}</style><h1>繁中 ABC 2026</h1>`);
  const weights = await probe(`<style>@font-face{{font-family:WeightFace;src:local("Arial");font-weight:400}}@font-face{{font-family:WeightFace;src:url("data:font/woff2;base64,AA==");font-weight:700}}h1,p{{font-family:WeightFace,serif}}h1{{font-weight:400}}p{{font-weight:700}}</style><h1>繁中 ABC 正常</h1><main><p>繁中 ABC 壞粗體</p></main>`);
  const laterFailure = await probe(`<style>@font-face{{font-family:LaterBroken;src:url("data:font/woff2;base64,AA==")}}p{{font-family:serif}}p:nth-child(5),button{{font-family:LaterBroken,serif}}</style><h1>正常標題</h1><main><p>第一段 ABC 正常</p><p>第二段 ABC 正常</p><p>第三段 ABC 正常</p><p>第四段 ABC 正常</p><p>第五段 ABC 壞字體</p><button>儲存 ABC</button></main>`);
  const textarea = await probe(`<style>h1{{font-family:serif}}textarea{{font-family:"Absent Textarea Face",serif}}</style><h1>正常標題</h1><main><textarea>繁中 ABC 輸入</textarea></main>`);
  const scrollingTextarea = await probe(`<style>h1{{font-family:serif}}textarea{{display:block;width:12rem;height:2rem;overflow:auto;font-family:"Absent Textarea Face",serif}}</style><h1>正常標題</h1><main><textarea>第一行繁中 ABC\n第二行繁中 ABC\n第三行繁中 ABC</textarea></main>`);
  const hiddenOverflowTextarea = await probe(`<style>h1{{font-family:serif}}textarea{{display:block;width:12rem;height:2rem;overflow:hidden;font-family:"Absent Textarea Face",serif}}</style><h1>正常標題</h1><main><textarea>第一行繁中 ABC\n第二行繁中 ABC\n第三行繁中 ABC</textarea></main>`);
  const brokenTextarea = await probe(`<style>@font-face{{font-family:BrokenTextarea;src:url("data:font/woff2;base64,AA==")}}h1{{font-family:serif}}textarea{{font-family:BrokenTextarea,serif}}</style><h1>正常標題</h1><main><textarea>繁中 ABC 輸入</textarea></main>`);
  const brokenInput = await probe(`<style>@font-face{{font-family:BrokenInput;src:url("data:font/woff2;base64,AA==")}}h1{{font-family:serif}}input{{font-family:BrokenInput,serif}}</style><h1>正常標題</h1><main><input value="繁中 ABC 2026"></main>`);
  const stretch = await probe(`<style>@font-face{{font-family:StretchFace;src:local("Arial");font-stretch:normal}}@font-face{{font-family:StretchFace;src:url("data:font/woff2;base64,AA==");font-stretch:condensed}}h1,p{{font-family:StretchFace,serif}}h1{{font-stretch:condensed}}p{{font-stretch:normal}}</style><h1>繁中 ABC 壓縮</h1><main><p>繁中 ABC 正常</p></main>`);
  const stretch80 = await probe(`<style>@font-face{{font-family:Stretch80;src:local("Arial");font-stretch:normal}}@font-face{{font-family:Stretch80;src:url("data:font/woff2;base64,AA==");font-stretch:80%}}h1,p{{font-family:Stretch80,serif;font-weight:400}}h1{{font-stretch:80%}}p{{font-stretch:normal}}</style><h1>繁中 ABC 壓縮</h1><main><p>繁中 ABC 正常</p></main>`);
  const stretch80Loaded = await probe(`<style>@font-face{{font-family:StretchLoaded;src:url("data:font/woff2;base64,AA==");font-stretch:condensed}}@font-face{{font-family:StretchLoaded;src:local("Arial");font-stretch:80%}}h1{{font-family:StretchLoaded,serif;font-stretch:80%;font-weight:400}}</style><h1>繁中 ABC 正常</h1>`);
  const unicodeRange = await probe(`<style>@font-face{{font-family:RangeFace;src:local("Arial");font-stretch:normal}}@font-face{{font-family:RangeFace;src:url("data:font/woff2;base64,AA==");font-stretch:80%;unicode-range:U+0000-007F}}h1,p{{font-family:RangeFace,serif;font-weight:400}}h1{{font-stretch:80%}}p{{font-stretch:normal}}</style><h1>純繁體中文</h1><main><p>繁中 ABC 正常</p></main>`);
  const splitRange = await probe(`<style>@font-face{{font-family:Range80;src:local("Arial");font-stretch:80%;unicode-range:U+0-7F}}@font-face{{font-family:Range80;src:url("data:font/woff2;base64,AA==");font-stretch:80%;unicode-range:U+4E00-9FFF}}h1{{font-family:Range80,serif;font-stretch:80%;font-weight:400}}</style><h1>繁中 ABC 八成寬</h1>`);
  const punctuationRange = await probe(`<style>@font-face{{font-family:PunctuationFace;src:local("Arial");unicode-range:U+4E00-9FFF}}@font-face{{font-family:PunctuationFace;src:url("data:font/woff2;base64,AA==");unicode-range:U+3000-303F}}h1{{font-family:PunctuationFace,serif;font-weight:400}}</style><h1>繁體中文。標點</h1>`);
  const emojiRange = await probe(`<style>@font-face{{font-family:EmojiRange;src:local("Arial");unicode-range:U+4E00-9FFF}}@font-face{{font-family:EmojiRange;src:url("data:font/woff2;base64,AA==");unicode-range:U+1F600-1F64F}}h1{{font-family:EmojiRange,serif;font-weight:400}}</style><h1>繁體中文😀</h1>`);
  const nearestWeight = await probe(`<style>@font-face{{font-family:WeightStretch;src:local("Arial");font-stretch:normal;font-weight:700}}@font-face{{font-family:WeightStretch;src:local("Arial");font-stretch:80%;font-weight:400}}@font-face{{font-family:WeightStretch;src:url("data:font/woff2;base64,AA==");font-stretch:80%;font-weight:600}}h1,p{{font-family:WeightStretch,serif;font-weight:700}}h1{{font-stretch:80%}}p{{font-stretch:normal}}</style><h1>繁中 ABC 八成寬</h1><main><p>繁中 ABC 正常</p></main>`);
  const obliqueAngles = await probe(`<style>@font-face{{font-family:AngleFace;src:local("Arial");font-style:oblique 10deg}}@font-face{{font-family:AngleFace;src:url("data:font/woff2;base64,AA==");font-style:oblique 20deg}}h1,p{{font-family:AngleFace,serif;font-weight:400}}h1{{font-style:oblique 20deg}}p{{font-style:oblique 10deg}}</style><h1>繁中 ABC 二十度</h1><main><p>繁中 ABC 十度</p></main>`);
  const obliqueTurn = await probe(`<style>@font-face{{font-family:UnitAngle;src:local("Arial");font-style:oblique 14deg}}@font-face{{font-family:UnitAngle;src:url("data:font/woff2;base64,AA==");font-style:oblique .1turn}}h1,p{{font-family:UnitAngle,serif;font-weight:400}}h1{{font-style:oblique .1turn}}p{{font-style:oblique 14deg}}</style><h1>繁中 ABC 三十六度</h1><main><p>繁中 ABC 十四度</p></main>`);
  const obliqueRad = await probe(`<style>@font-face{{font-family:RadAngle;src:local("Arial");font-style:oblique 14deg}}@font-face{{font-family:RadAngle;src:url("data:font/woff2;base64,AA==");font-style:oblique .2rad}}h1{{font-family:RadAngle,serif;font-style:oblique .2rad;font-weight:400}}</style><h1>繁中 ABC 弧度</h1>`);
  const obliqueNearHigh = await probe(`<style>@font-face{{font-family:NearHigh;src:local("Arial");font-stretch:80%;font-style:oblique 30deg}}@font-face{{font-family:NearHigh;src:url("data:font/woff2;base64,AA==");font-stretch:80%;font-style:oblique 10deg}}h1{{font-family:NearHigh,serif;font-stretch:80%;font-style:oblique 12deg;font-weight:400}}</style><h1>繁中 ABC 近角度</h1>`);
  const obliqueRangeGap = await probe(`<style>@font-face{{font-family:RangeGap;src:local("Arial");font-style:oblique 20deg 30deg}}@font-face{{font-family:RangeGap;src:url("data:font/woff2;base64,AA==");font-style:oblique 5deg 10deg}}h1{{font-family:RangeGap,serif;font-style:oblique 12deg;font-weight:400}}</style><h1>繁中 ABC 角度區間</h1>`);
  const obliqueNegative = await probe(`<style>@font-face{{font-family:NegativeAngle;src:local("Arial");font-style:oblique -30deg}}@font-face{{font-family:NegativeAngle;src:url("data:font/woff2;base64,AA==");font-style:oblique -10deg}}h1{{font-family:NegativeAngle,serif;font-style:oblique -12deg;font-weight:400}}</style><h1>繁中 ABC 負角度</h1>`);
  const obliqueNormal = await probe(`<style>@font-face{{font-family:NormalAngle;src:local("Arial");font-style:oblique 10deg}}@font-face{{font-family:NormalAngle;src:url("data:font/woff2;base64,AA==");font-style:normal}}h1{{font-family:NormalAngle,serif;font-style:oblique 5deg;font-weight:400}}</style><h1>繁中 ABC 近正常</h1>`);
  const obliquePrecision = await probe(`<style>@font-face{{font-family:PrecisionGreen;src:local("Arial");font-style:oblique 11.4591deg}}@font-face{{font-family:PrecisionGreen;src:url("data:font/woff2;base64,AA==");font-style:oblique .2rad}}h1{{font-family:PrecisionGreen,serif;font-style:oblique .2rad;font-weight:400}}</style><h1>繁中 ABC 精度</h1>`);
  const longIgnoredPrefix = await probe(`<style>@font-face{{font-family:LongPrefix;src:url("data:font/woff2;base64,AA==");unicode-range:U+4E00-9FFF}}h1{{font-family:LongPrefix,serif}}</style><h1>${{' '.repeat(300)}}漢</h1>`);
  const crossStretch = await probe(`<style>@font-face{{font-family:CrossStretch;src:url("data:font/woff2;base64,AA==");font-stretch:normal}}@font-face{{font-family:CrossStretch;src:local("Arial");font-stretch:80%}}h1,span{{font-family:CrossStretch,serif}}h1{{font-stretch:80%}}span{{font-stretch:normal}}</style><h1>繁中 ABC 八成寬正常</h1><span>繁中 ABC 觸發失敗 face</span>`);
  const currencySubset = await probe(`<style>@font-face{{font-family:CurrencySubset;src:local("Arial");unicode-range:U+0-7F}}@font-face{{font-family:CurrencySubset;src:url("data:font/woff2;base64,AA==");unicode-range:U+00A5}}h1{{font-family:CurrencySubset,serif}}</style><h1>價格 ABC ¥100</h1>`);
  const currencyOnly = await probe(`<style>@font-face{{font-family:CurrencyOnly;src:url("data:font/woff2;base64,AA==");unicode-range:U+00A5}}button{{font-family:CurrencyOnly,serif}}</style><h1>正常標題</h1><main><button>¥</button></main>`);
  const degreeSubset = await probe(`<style>@font-face{{font-family:DegreeSubset;src:local("Arial");unicode-range:U+0-7F}}@font-face{{font-family:DegreeSubset;src:url("data:font/woff2;base64,AA==");unicode-range:U+00B0}}h1{{font-family:DegreeSubset,serif}}</style><h1>室溫 25°C</h1>`);
  const emojiVariation = await probe(`<style>@font-face{{font-family:EmojiVariation;src:local("Arial");unicode-range:U+0-7F}}@font-face{{font-family:EmojiVariation;src:url("data:font/woff2;base64,AA==");unicode-range:U+00A9}}h1{{font-family:EmojiVariation,serif}}</style><h1>ABC ©️</h1>`);
  const keycapVariation = await probe(`<style>@font-face{{font-family:KeycapVariation;src:local("Arial");unicode-range:U+41-5A}}@font-face{{font-family:KeycapVariation;src:url("data:font/woff2;base64,AA==");unicode-range:U+0031}}h1{{font-family:KeycapVariation,serif}}</style><h1>ABC 1️⃣</h1>`);
  const textVariation = await probe(`<style>@font-face{{font-family:TextVariation;src:local("Arial");unicode-range:U+0-7F}}@font-face{{font-family:TextVariation;src:url("data:font/woff2;base64,AA==");unicode-range:U+231A}}h1{{font-family:TextVariation,serif}}</style><h1>ABC ⌚︎</h1>`);
  const invalidTextVariation = await probe(`<style>@font-face{{font-family:InvalidVariation;src:url("data:font/woff2;base64,AA==")}}h1{{font-family:InvalidVariation,serif}}</style><h1>A️B️C️</h1>`);
  const normalBeforeItalic = await probe(`<style>@font-face{{font-family:SyntheticOblique;src:local("Arial");font-style:normal}}@font-face{{font-family:SyntheticOblique;src:url("data:font/woff2;base64,AA==");font-style:italic}}h1,span{{font-family:SyntheticOblique,serif}}h1{{font-style:oblique 12deg}}span{{font-style:italic}}</style><h1>繁中 ABC 合成斜體</h1><span>繁中 ABC 觸發壞 italic</span>`);
  const normalBeforeOblique = await probe(`<style>@font-face{{font-family:LowOblique;src:local("Arial");font-style:normal}}@font-face{{font-family:LowOblique;src:url("data:font/woff2;base64,AA==");font-style:oblique 14deg}}h1,span{{font-family:LowOblique,serif}}h1{{font-style:oblique 12deg}}span{{font-style:oblique 14deg}}</style><h1>繁中 ABC 十二度合成</h1><span>繁中 ABC 觸發壞十四度</span>`);
  const italicAtTwenty = await probe(`<style>@font-face{{font-family:HighOblique;src:url("data:font/woff2;base64,AA==");font-style:normal}}@font-face{{font-family:HighOblique;src:local("Arial");font-style:italic}}h1,span{{font-family:HighOblique,serif}}h1{{font-style:oblique 20deg}}span{{font-style:normal}}</style><h1>繁中 ABC 二十度斜體</h1><span>繁中 ABC 觸發壞 normal</span>`);
  const arbitraryItalicAtTwenty = await probe(`<style>@font-face{{font-family:WideSynthesis;src:local("Arial");font-stretch:80%;font-style:normal}}@font-face{{font-family:WideSynthesis;src:url("data:font/woff2;base64,AA==");font-stretch:80%;font-style:italic}}@font-face{{font-family:WideSynthesis;src:local("Arial");font-stretch:normal;font-style:normal}}h1,p,span{{font-family:WideSynthesis,serif}}h1{{font-stretch:80%;font-style:oblique 20deg}}p{{font-stretch:80%;font-style:normal}}span{{font-stretch:normal;font-style:normal}}</style><h1>繁中 ABC 八成寬二十度</h1><main><p>繁中 ABC 八成寬正常</p></main><span>繁中 ABC normal stretch</span>`);
  const arbitraryObliqueAtTwenty = await probe(`<style>@font-face{{font-family:WideOblique;src:local("Arial");font-stretch:80%;font-style:italic}}@font-face{{font-family:WideOblique;src:url("data:font/woff2;base64,AA==");font-stretch:80%;font-style:oblique 30deg}}@font-face{{font-family:WideOblique;src:local("Arial");font-stretch:normal;font-style:normal}}h1,p,span{{font-family:WideOblique,serif}}h1{{font-stretch:80%;font-style:oblique 20deg}}p{{font-stretch:80%;font-style:italic}}span{{font-stretch:normal;font-style:normal}}</style><h1>繁中 ABC 八成寬二十度 oblique</h1><main><p>繁中 ABC 八成寬 italic</p></main><span>繁中 ABC normal stretch</span>`);
  const astralBoundary = await probe(`<style>@font-face{{font-family:AstralBoundary;src:local("Arial");unicode-range:U+10400-1044F}}@font-face{{font-family:AstralBoundary;src:url("data:font/woff2;base64,AA==");unicode-range:U+4E00-9FFF}}h1{{font-family:AstralBoundary,serif}}</style><h1>${{'𐐀'.repeat(120)}}漢</h1>`);
  const modifierBypass = await probe(`<style>@font-face{{font-family:ModifierBypass;src:url("data:font/woff2;base64,AA==")}}h1{{font-family:ModifierBypass,serif}}</style><h1>A🏽B🏽C🏽</h1>`);
  const validSkinToneEmoji = await probe(`<style>@font-face{{font-family:SkinToneEmoji;src:local("Arial");unicode-range:U+0-7F}}@font-face{{font-family:SkinToneEmoji;src:url("data:font/woff2;base64,AA==");unicode-range:U+1F3FB-1F3FF,U+1F44D}}h1{{font-family:SkinToneEmoji,serif}}</style><h1>ABC 👍🏽</h1>`);
  const flagEmoji = await probe(`<style>@font-face{{font-family:FlagEmoji;src:local("Arial");unicode-range:U+0-7F}}@font-face{{font-family:FlagEmoji;src:url("data:font/woff2;base64,AA==");unicode-range:U+1F1E6-1F1FF}}h1{{font-family:FlagEmoji,serif}}</style><h1>ABC 🇹🇼</h1>`);
  const singleRegionalIndicator = await probe(`<style>@font-face{{font-family:SingleFlag;src:url("data:font/woff2;base64,AA==");unicode-range:U+1F1F9}}h1{{font-family:SingleFlag,serif}}</style><h1>🇹</h1>`);
  const invalidModifierSequence = await probe(`<style>@font-face{{font-family:InvalidModifier;src:local("Arial");unicode-range:U+0-7F}}@font-face{{font-family:InvalidModifier;src:url("data:font/woff2;base64,AA==");unicode-range:U+00A9,U+1F3FB-1F3FF}}h1{{font-family:InvalidModifier,serif}}</style><h1>ABC ©🏽</h1>`);
  const negativeObliqueAtTwenty = await probe(`<style>@font-face{{font-family:NegativeCross;src:local("Arial");font-stretch:80%;font-style:oblique -30deg}}@font-face{{font-family:NegativeCross;src:url("data:font/woff2;base64,AA==");font-stretch:80%;font-style:normal}}@font-face{{font-family:NegativeCross;src:local("Arial");font-stretch:normal;font-style:normal}}h1,p,span{{font-family:NegativeCross,serif}}h1{{font-stretch:80%;font-style:oblique 20deg}}p{{font-stretch:80%;font-style:oblique -30deg}}span{{font-stretch:normal;font-style:normal}}</style><h1>繁中 ABC 正角請求</h1><main><p>繁中 ABC 負角載入</p></main><span>繁中 ABC normal stretch</span>`);
  const positiveLowCrossStyle = await probe(`<style>@font-face{{font-family:PositiveLowCross;src:local("Arial");font-stretch:80%;font-style:oblique -30deg}}@font-face{{font-family:PositiveLowCross;src:url("data:font/woff2;base64,AA==");font-stretch:80%;font-style:italic}}@font-face{{font-family:PositiveLowCross;src:local("Arial");font-stretch:normal;font-style:normal}}h1,p,span{{font-family:PositiveLowCross,serif}}h1{{font-stretch:80%;font-style:oblique 12deg}}p{{font-stretch:80%;font-style:oblique -30deg}}span{{font-stretch:normal;font-style:normal}}</style><h1>繁中 ABC 正低角</h1><main><p>繁中 ABC 負角載入</p></main><span>繁中 ABC normal stretch</span>`);
  const negativeLowCrossStyle = await probe(`<style>@font-face{{font-family:NegativeLowCross;src:local("Arial");font-stretch:80%;font-style:oblique 30deg}}@font-face{{font-family:NegativeLowCross;src:url("data:font/woff2;base64,AA==");font-stretch:80%;font-style:italic}}@font-face{{font-family:NegativeLowCross;src:local("Arial");font-stretch:normal;font-style:normal}}h1,p,span{{font-family:NegativeLowCross,serif}}h1{{font-stretch:80%;font-style:oblique -12deg}}p{{font-stretch:80%;font-style:oblique 30deg}}span{{font-stretch:normal;font-style:normal}}</style><h1>繁中 ABC 負低角</h1><main><p>繁中 ABC 正角載入</p></main><span>繁中 ABC normal stretch</span>`);
  const negativeHighFallsBackToItalic = await probe(`<style>@font-face{{font-family:NegativeHigh;src:local("Arial");font-stretch:80%;font-style:italic}}@font-face{{font-family:NegativeHigh;src:url("data:font/woff2;base64,AA==");font-stretch:80%;font-style:oblique 30deg}}@font-face{{font-family:NegativeHigh;src:local("Arial");font-stretch:normal;font-style:normal}}h1,span{{font-family:NegativeHigh,serif}}h1{{font-stretch:80%;font-style:oblique -20deg}}span.trigger{{font-stretch:80%;font-style:oblique 30deg}}</style><h1>繁中 ABC 負高角</h1><span class="trigger">觸發壞正角</span>`);
  const directionalOblique = await probe(`<style>@font-face{{font-family:Directional;src:local("Arial");font-stretch:80%;font-style:oblique 14deg}}@font-face{{font-family:Directional;src:url("data:font/woff2;base64,AA==");font-stretch:80%;font-style:oblique 30deg}}@font-face{{font-family:Directional;src:local("Arial");font-stretch:normal;font-style:normal}}h1,p{{font-family:Directional,serif}}h1{{font-stretch:80%;font-style:oblique 20deg}}p{{font-stretch:80%;font-style:oblique 14deg}}</style><h1>ABC 2026</h1><main><p>ABC loaded</p></main>`);
  const negativeCrossCategory = await probe(`<style>@font-face{{font-family:NegativeCategory;src:local("Arial");font-stretch:80%;font-style:italic}}@font-face{{font-family:NegativeCategory;src:url("data:font/woff2;base64,AA==");font-stretch:80%;font-style:oblique 10deg}}@font-face{{font-family:NegativeCategory;src:local("Arial");font-stretch:normal;font-style:normal}}h1,span{{font-family:NegativeCategory,serif}}h1{{font-stretch:80%;font-style:oblique -5deg}}span{{font-stretch:normal}}</style><h1>ABC negative</h1><span>normal control</span>`);
  const highCrossCategory = await probe(`<style>@font-face{{font-family:HighCategory;src:local("Arial");font-stretch:80%;font-style:oblique 10deg}}@font-face{{font-family:HighCategory;src:url("data:font/woff2;base64,AA==");font-stretch:80%;font-style:italic}}@font-face{{font-family:HighCategory;src:local("Arial");font-stretch:normal;font-style:normal}}h1,span{{font-family:HighCategory,serif}}h1{{font-stretch:80%;font-style:oblique 20deg}}span{{font-stretch:normal}}</style><h1>ABC high</h1><span>normal control</span>`);
  const fourteenBoundary = await probe(`<style>@font-face{{font-family:BoundaryCategory;src:local("Arial");font-stretch:80%;font-style:oblique 30deg}}@font-face{{font-family:BoundaryCategory;src:url("data:font/woff2;base64,AA==");font-stretch:80%;font-style:italic}}@font-face{{font-family:BoundaryCategory;src:local("Arial");font-stretch:normal;font-style:normal}}h1,p,button,span{{font-family:BoundaryCategory,serif}}h1{{font-stretch:80%;font-style:normal}}p{{font-stretch:80%;font-style:oblique 5deg}}button{{font-stretch:80%;font-style:oblique 12deg}}span{{font-stretch:normal}}</style><h1>ABC normal request</h1><main><p>ABC five</p><button>ABC twelve</button></main><span>normal control</span>`);
  const patchedBrowserCheck = await probe(`<style>@font-face{{font-family:PatchedCheck;src:local("Arial");unicode-range:U+0041}}@font-face{{font-family:PatchedCheck;src:url("data:font/woff2;base64,AA==");unicode-range:U+6F22}}h1{{font-family:PatchedCheck,serif}}</style><h1>漢</h1><script>document.fonts.check = () => true;<\\/script>`);
  const generatedControlLabels = await probe(`<style>@font-face{{font-family:BrokenControl;src:url("data:font/woff2;base64,AA==")}}input{{font-family:BrokenControl,serif}}</style><h1 style="font-family:serif">正常標題</h1><main><input type="submit" aria-label="A"><input type="reset"></main>`);
  const emojiOnlyHeading = await probe(`<h1>😀</h1>`);
  const emojiOnlyControl = await probe(`<h1>正常標題</h1><main><button>😀 🇹🇼 1️⃣ ©️</button></main>`);
  const whitespaceOnlyControls = await probe(`<h1>正常標題</h1><main><button>&nbsp;</button><button>　</button><button>﻿</button><button>   </button></main>`);
  const passwordMask = await probe(`<style>@font-face{{font-family:PassFace;src:local("Arial");unicode-range:U+0041}}@font-face{{font-family:PassFace;src:url("data:font/woff2;base64,AA==");unicode-range:U+2022,U+25CF}}input{{font-family:PassFace,serif}}</style><h1 style="font-family:serif">正常</h1><main><input type="password" value="A"></main>`);
  const localizedNativeInputs = await probe(`<style>@font-face{{font-family:LocalizedFace;src:local("Arial")}}input{{font-family:LocalizedFace,serif}}</style><h1>正常標題</h1><main><input type="date" value="2026-07-17"><input type="month" value="2026-07"><input type="time" value="12:34"></main>`);
  const nativeNonTextInputs = await probe(`<h1>正常標題</h1><main><input type="checkbox"><input type="radio"><input type="range"><input type="color"></main>`);
  const pseudoContent = await probe(`<style>@font-face{{font-family:PseudoFace;src:local("Arial");unicode-range:U+0041}}@font-face{{font-family:PseudoFace;src:url("data:font/woff2;base64,AA==");unicode-range:U+6F22}}button{{font-family:PseudoFace,serif}}button::before{{content:"漢"}}</style><h1>正常標題</h1><main><button>A</button></main>`);
  const emptyPseudoContent = await probe(`<style>@font-face{{font-family:EmptyPseudo;src:local("Arial")}}button{{font-family:EmptyPseudo,serif}}button::before{{content:""}}</style><h1>正常標題</h1><main><button>A</button></main>`);
  const pseudoImage = await probe(`<style>@font-face{{font-family:ImagePseudo;src:local("Arial")}}button{{font-family:ImagePseudo,serif}}button::before{{content:url("data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==")}}</style><h1>正常標題</h1><main><button>A</button></main>`);
  const pseudoImageAlt = await probe(`<style>@font-face{{font-family:ImagePseudoAlt;src:local("Arial")}}button{{font-family:ImagePseudoAlt,serif}}button::before{{content:url("data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==") / "icon"}}</style><h1>正常標題</h1><main><button>A</button></main>`);
  const pseudoImageAndText = await probe(`<style>@font-face{{font-family:ImagePseudoText;src:local("Arial")}}button{{font-family:ImagePseudoText,serif}}button::before{{content:url("data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==") "icon"}}</style><h1>正常標題</h1><main><button>A</button></main>`);
  const hiddenPseudoContent = await probe(`<style>@font-face{{font-family:HiddenPseudo;src:local("Arial")}}button{{font-family:HiddenPseudo,serif}}button::before{{content:"X"}}button:nth-child(1)::before{{display:none}}button:nth-child(2)::before{{visibility:hidden}}button:nth-child(3)::before{{font-size:0}}</style><h1>正常標題</h1><main><button>A</button><button>B</button><button>C</button></main>`);
  const transparentPseudoContent = await probe(`<style>@font-face{{font-family:TransparentPseudo;src:local("Arial")}}button{{font-family:TransparentPseudo,serif}}button::before{{content:"X";opacity:0}}</style><h1>正常標題</h1><main><button>A</button></main>`);
  const clippedPseudoContent = await probe(`<style>@font-face{{font-family:ClippedPseudo;src:local("Arial")}}button{{font-family:ClippedPseudo,serif}}button::before{{content:"X";display:inline-block;width:0;height:0;overflow:hidden}}</style><h1>正常標題</h1><main><button>A</button></main>`);
  const inactiveQuoteContent = await probe(`<style>@font-face{{font-family:InactiveQuote;src:local("Arial")}}button{{font-family:InactiveQuote,serif}}button:nth-child(1)::before{{content:no-open-quote}}button:nth-child(2)::before{{content:no-close-quote}}button:nth-child(3)::before{{content:open-quote;quotes:none}}</style><h1>正常標題</h1><main><button>A</button><button>B</button><button>C</button></main>`);
  const emptyQuoteContent = await probe(`<style>@font-face{{font-family:EmptyQuote;src:local("Arial")}}button{{font-family:EmptyQuote,serif}}button::before{{content:open-quote;quotes:"" ""}}</style><h1>正常標題</h1><main><button>A</button></main>`);
  const quoteDepthContent = await probe(`<style>@font-face{{font-family:QuoteDepth;src:local("Arial")}}button{{font-family:QuoteDepth,serif}}button:nth-child(1)::before{{content:close-quote}}button:nth-child(2)::before{{content:open-quote;quotes:"" "" "X" "Y"}}</style><h1>正常標題</h1><main><button>A</button><button>B</button></main>`);
  const visibleQuoteContent = await probe(`<style>@font-face{{font-family:VisibleQuote;src:local("Arial")}}button{{font-family:VisibleQuote,serif;quotes:"Q" "Q"}}button::before{{content:open-quote}}</style><h1>正常標題</h1><main><button>A</button></main>`);
  const counterPseudoContent = await probe(`<style>@font-face{{font-family:CounterPseudo;src:local("Arial")}}main{{counter-reset:item 7}}button{{font-family:CounterPseudo,serif}}button::before{{content:counter(item)}}</style><h1>正常標題</h1><main><button>A</button></main>`);
  const clippedPseudoVariants = await probe(`<style>@font-face{{font-family:ClippedVariants;src:local("Arial")}}button{{font-family:ClippedVariants,serif}}button::before{{content:"X";display:inline-block;width:0;height:0}}button:nth-child(1)::before{{overflow:auto}}button:nth-child(2)::before{{overflow:scroll}}button:nth-child(3)::before{{overflow:hidden;border:1px solid}}</style><h1>正常標題</h1><main><button>A</button><button>B</button><button>C</button></main>`);
  const paintSuppressedPseudo = await probe(`<style>@font-face{{font-family:PaintSuppressed;src:local("Arial")}}button{{font-family:PaintSuppressed,serif}}button::before{{content:"X"}}button:nth-child(1)::before{{filter:opacity(0)}}button:nth-child(2)::before{{transform:scale(0)}}button:nth-child(3)::before{{clip-path:inset(50%)}}</style><h1>正常標題</h1><main><button>A</button><button>B</button><button>C</button></main>`);
  const ancestorSuppressedPseudo = await probe(`<style>@font-face{{font-family:AncestorSuppressed;src:local("Arial")}}button{{font-family:AncestorSuppressed,serif}}button::before{{content:"X"}}div:nth-child(1){{opacity:0}}div:nth-child(2){{filter:opacity(0)}}</style><h1>正常標題</h1><main><div><button>A</button></div><div><button>B</button></div></main>`);
  await page.setContent(`<style>@font-face{{font-family:VendorImage;src:local("Arial")}}button{{font-family:VendorImage,serif}}button:nth-child(1)::before{{content:-webkit-gradient(linear,left top,right bottom,from(red),to(blue))}}button:nth-child(2)::before{{content:-webkit-cross-fade(url("data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="),url("data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="),50%)}}</style><h1>正常標題</h1><main><button>A</button><button>B</button></main>`);
  await page.evaluate(() => document.fonts.ready);
  const vendorImageFunctionsRecognized = await page.evaluate(() => [...document.querySelectorAll('button')].map((button) => getComputedStyle(button, '::before').content.startsWith('-webkit-')));
  const vendorImageContent = await collectFontEvidence(context, page);
  const selectLabel = await probe(`<style>@font-face{{font-family:SelectLabel;src:local("Arial");unicode-range:U+0041-0043}}@font-face{{font-family:SelectLabel;src:url("data:font/woff2;base64,AA==");unicode-range:U+0058}}select{{font-family:SelectLabel,serif}}</style><h1>正常標題</h1><main><select><option selected label="X">ABC</option></select></main>`);
  const selectMultiple = await probe(`<style>@font-face{{font-family:SelectMultiple;src:local("Arial");unicode-range:U+0041-0046}}@font-face{{font-family:SelectMultiple;src:url("data:font/woff2;base64,AA==");unicode-range:U+0058}}select{{font-family:SelectMultiple,serif}}</style><h1>正常標題</h1><main><select multiple size="2"><option selected>ABC</option><option label="X">DEF</option></select></main>`);
  const selectListboxGroup = await probe(`<style>@font-face{{font-family:SelectGroup;src:local("Arial");unicode-range:U+0041-0043}}@font-face{{font-family:SelectGroup;src:url("data:font/woff2;base64,AA==");unicode-range:U+0058}}select{{font-family:SelectGroup,serif}}</style><h1>正常標題</h1><main><select size="2"><optgroup label="X"><option selected>ABC</option></optgroup></select></main>`);
  const selectOptionStyle = await probe(`<style>@font-face{{font-family:OptionStyle;src:url("data:font/woff2;base64,AA==");unicode-range:U+0058}}select{{font-family:Arial,sans-serif}}option.bad{{font-family:OptionStyle,serif}}</style><h1>正常標題</h1><main><select size="2"><option selected>ABC</option><option class="bad" label="X">DEF</option></select></main>`);
  const selectHiddenOption = await probe(`<style>@font-face{{font-family:HiddenOption;src:url("data:font/woff2;base64,AA==");unicode-range:U+0058}}select{{font-family:Arial,sans-serif}}option.bad{{font-family:HiddenOption,serif}}</style><h1>正常標題</h1><main><select size="2"><option selected>ABC</option><option class="bad" label="X" hidden>DEF</option></select></main>`);
  const genericUncertainMapping = await probe(`<style>h1,input{{font-family:sans-serif}}h1::before{{content:"X"}}</style><h1>正常標題</h1><main><input type="password" value="A"><input type="date" value="2026-07-17"></main>`);
  const lateRelevantGlyph = await probe(`<style>@font-face{{font-family:LateGlyph;src:local("Arial");unicode-range:U+0-7F}}@font-face{{font-family:LateGlyph;src:url("data:font/woff2;base64,AA==");unicode-range:U+4E00-9FFF}}h1{{font-family:LateGlyph,serif}}</style><h1>${{'A'.repeat(240)}}漢</h1>`);
  const overflowGlyphs = Array.from({{ length: 2049 }}, (_, index) => String.fromCodePoint(0x3400 + index)).join('');
  const probeOverflow = await probe(`<style>h1{{font-family:MissingOverflow,serif}}</style><h1>${{overflowGlyphs}}</h1>`);
  const laterUnavailable = await probe(`<style>@font-face{{font-family:LaterPrecision;src:local("Arial");font-style:oblique 11.4591deg}}@font-face{{font-family:LaterPrecision;src:url("data:font/woff2;base64,AA==");font-style:oblique .2rad}}p{{font-family:serif}}p.bad{{font-family:LaterPrecision,serif;font-style:oblique .2rad}}</style><h1>正常標題</h1><main><p>第一段繁中 ABC 正常</p><p>第二段繁中 ABC 正常</p><p>第三段繁中 ABC 正常</p><p class="bad">第四段繁中 ABC 壞精確 face</p></main>`);
  await page.setContent(`<style>@font-face{{font-family:RaceFace;src:local("Arial");unicode-range:U+0041}}@font-face{{font-family:RaceFace;src:url("data:font/woff2;base64,AA==");unicode-range:U+6F22}}input{{font-family:RaceFace,serif}}</style><h1>正常標題</h1><main><input id="race-font" value="漢"></main>`);
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => {{
    const descriptor = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');
    window.__fontProbeValueDescriptor = descriptor;
    let reads = 0;
    Object.defineProperty(HTMLInputElement.prototype, 'value', {{
      configurable: true,
      get() {{
        if (this.id === 'race-font') return reads++ === 0 ? '漢' : 'A';
        return descriptor.get.call(this);
      }},
      set: descriptor.set,
    }});
  }});
  const atomicProbe = await collectFontEvidence(context, page);
  await page.evaluate(() => Object.defineProperty(HTMLInputElement.prototype, 'value', window.__fontProbeValueDescriptor));
  const blankHeadings = '<h1>&nbsp;</h1>'.repeat(120);
  await page.setContent(`<style>h1{{display:block}}</style>${{blankHeadings}}<h1 id="late-inventory">漢</h1>`);
  await page.evaluate(() => {{
    setTimeout(() => {{
      const style = document.createElement('style');
      style.textContent = '@font-face{{font-family:LateInventory;src:url("data:font/woff2;base64,AA==");unicode-range:U+6F22}}#late-inventory{{font-family:LateInventory,serif}}';
      document.head.append(style);
    }}, 10);
  }});
  const inventoryRace = await collectFontEvidence(context, page);
  const proseRows = '<p>穩定段落 ABC</p>'.repeat(80);
  await page.setContent(`<style>@font-face{{font-family:GlobalAlias;src:local("Arial")}}#late-global{{display:none;font-family:GlobalAlias,serif}}p{{font-family:GlobalAlias,serif}}</style><h1 id="late-global">稍後顯示</h1><main>${{proseRows}}</main>`);
  await page.evaluate(() => document.fonts.load('16px GlobalAlias', 'AB'));
  await page.evaluate(() => setTimeout(() => {{ document.querySelector('#late-global').style.display = 'block'; }}, 30));
  const globalVisibilityRace = await collectFontEvidence(context, page);
  const empty = await probe(`<main><div>沒有角色節點</div></main>`);
  process.stdout.write(JSON.stringify({{
    fallback: fallback.roles[0]?.classification,
    fallbackMismatch: fallback.primaryMismatches.length,
    alias: alias.roles[0]?.classification,
    aliasMismatch: alias.primaryMismatches.length,
    failed: failed.roles[0]?.classification,
    failedMismatch: failed.primaryMismatches.length,
    weights: weights.roles.filter((role) => ['page-heading', 'lead-prose'].includes(role.role)).map((role) => ({{ role: role.role, classification: role.classification, weight: role.fontWeight }})),
    laterFailure: laterFailure.primaryMismatches.map((role) => ({{ role: role.role, sampleIndex: role.sampleIndex }})),
    textarea: textarea.roles.find((role) => role.role === 'interface-control')?.classification,
    textareaStatus: textarea.status,
    textareaText: textarea.roles.find((role) => role.role === 'interface-control')?.text,
    textareaGlyphs: textarea.roles.find((role) => role.role === 'interface-control')?.actualFonts.reduce((total, font) => total + font.glyphCount, 0),
    scrollingTextarea: scrollingTextarea.roles.find((role) => role.role === 'interface-control')?.classification,
    scrollingTextareaStatus: scrollingTextarea.status,
    hiddenOverflowTextarea: hiddenOverflowTextarea.roles.find((role) => role.role === 'interface-control')?.classification,
    hiddenOverflowTextareaStatus: hiddenOverflowTextarea.status,
    brokenTextarea: brokenTextarea.primaryMismatches.map((role) => role.role),
    brokenInput: brokenInput.primaryMismatches.map((role) => ({{ role: role.role, text: role.text }})),
    stretch: stretch.primaryMismatches.map((role) => ({{ role: role.role, stretch: role.fontStretch }})),
    stretch80: stretch80.primaryMismatches.map((role) => ({{ role: role.role, stretch: role.fontStretch }})),
    stretch80Loaded: stretch80Loaded.primaryMismatches.length,
    unicodeRange: unicodeRange.primaryMismatches.length,
    splitRange: splitRange.primaryMismatches.map((role) => ({{ role: role.role, stretch: role.fontStretch }})),
    punctuationRange: punctuationRange.primaryMismatches.map((role) => role.role),
    emojiRange: emojiRange.primaryMismatches.length,
    nearestWeight: nearestWeight.primaryMismatches.map((role) => ({{ role: role.role, stretch: role.fontStretch, weight: role.fontWeight }})),
    obliqueAngles: obliqueAngles.roles.filter((role) => ['page-heading', 'lead-prose'].includes(role.role)).map((role) => ({{ role: role.role, style: role.fontStyle, classification: role.classification }})),
    obliqueTurn: obliqueTurn.roles.filter((role) => ['page-heading', 'lead-prose'].includes(role.role)).map((role) => ({{ role: role.role, style: role.fontStyle, classification: role.classification }})),
    obliqueRad: obliqueRad.roles.filter((role) => role.role === 'page-heading').map((role) => ({{ role: role.role, style: role.fontStyle, classification: role.classification }})),
    obliqueBoundaryMismatches: [obliqueNearHigh, obliqueRangeGap, obliqueNegative, obliqueNormal].map((evidence) => evidence.primaryMismatches.length),
    obliquePrecision: {{ status: obliquePrecision.status, classifications: obliquePrecision.roles.map((role) => role.classification) }},
    longIgnoredPrefix: longIgnoredPrefix.primaryMismatches.length,
    crossStretch: crossStretch.roles.filter((role) => role.role === 'page-heading').map((role) => ({{ classification: role.classification, reliable: role.declaredFaceCheckReliable }})),
    currencySubset: currencySubset.primaryMismatches.length,
    currencyOnly: currencyOnly.primaryMismatches.map((role) => ({{ role: role.role, hasLettersOrNumbers: role.probeHasLetterOrNumber, hasRelevantGlyph: role.probeHasRelevantGlyph }})),
    degreeSubset: degreeSubset.primaryMismatches.length,
    emojiVariations: [emojiVariation, keycapVariation].map((evidence) => evidence.primaryMismatches.length),
    textVariation: textVariation.primaryMismatches.length,
    invalidTextVariation: invalidTextVariation.primaryMismatches.length,
    normalBeforeItalic: normalBeforeItalic.roles.filter((role) => role.role === 'page-heading').map((role) => role.classification),
    normalBeforeOblique: normalBeforeOblique.roles.filter((role) => role.role === 'page-heading').map((role) => role.classification),
    italicAtTwenty: italicAtTwenty.roles.filter((role) => role.role === 'page-heading').map((role) => role.classification),
    arbitraryItalicAtTwenty: arbitraryItalicAtTwenty.primaryMismatches.map((role) => role.role),
    arbitraryObliqueAtTwenty: arbitraryObliqueAtTwenty.primaryMismatches.map((role) => role.role),
    astralBoundary: astralBoundary.primaryMismatches.length,
    modifierBypass: modifierBypass.primaryMismatches.length,
    validSkinToneEmoji: validSkinToneEmoji.primaryMismatches.length,
    flagEmoji: flagEmoji.primaryMismatches.length,
    singleRegionalIndicator: singleRegionalIndicator.primaryMismatches.length,
    invalidModifierSequence: invalidModifierSequence.primaryMismatches.length,
    negativeObliqueAtTwenty: negativeObliqueAtTwenty.primaryMismatches.map((role) => role.role),
    positiveLowCrossStyle: positiveLowCrossStyle.primaryMismatches.map((role) => role.role),
    negativeLowCrossStyle: negativeLowCrossStyle.primaryMismatches.map((role) => role.role),
    negativeHighFallsBackToItalic: negativeHighFallsBackToItalic.primaryMismatches.length,
    directionalOblique: directionalOblique.primaryMismatches.map((role) => role.role),
    negativeCrossCategory: negativeCrossCategory.primaryMismatches.map((role) => role.role),
    highCrossCategory: highCrossCategory.primaryMismatches.map((role) => role.role),
    fourteenBoundary: fourteenBoundary.primaryMismatches.map((role) => role.role),
    patchedBrowserCheck: patchedBrowserCheck.primaryMismatches.map((role) => role.role),
    generatedControlLabels: {{
      status: generatedControlLabels.status,
      roles: generatedControlLabels.roles.filter((role) => role.browserGeneratedTextUnavailable).map((role) => ({{ role: role.role, text: role.text, classification: role.classification }})),
    }},
    emojiOnly: [emojiOnlyHeading, emojiOnlyControl].map((evidence) => ({{
      status: evidence.status,
      classifications: evidence.roles.map((role) => role.classification),
    }})),
    whitespaceOnlyStatus: whitespaceOnlyControls.status,
    passwordMask: {{
      status: passwordMask.status,
      roles: passwordMask.roles.filter((role) => role.renderedTextMappingUnavailable).map((role) => ({{ role: role.role, text: role.text, classification: role.classification }})),
    }},
    localizedNative: {{
      status: localizedNativeInputs.status,
      roles: localizedNativeInputs.roles.map((role) => ({{ role: role.role, mappingUnavailable: role.renderedTextMappingUnavailable, classification: role.classification, text: role.text }})),
    }},
    nativeNonTextStatus: nativeNonTextInputs.status,
    pseudoContent: {{
      status: pseudoContent.status,
      roles: pseudoContent.roles.filter((role) => role.role.endsWith('-pseudo')).map((role) => ({{ role: role.role, text: role.text, classification: role.classification }})),
    }},
    emptyPseudoStatus: emptyPseudoContent.status,
    pseudoImageStatus: pseudoImage.status,
    pseudoImageAltStatus: pseudoImageAlt.status,
    pseudoImageAndText: {{
      status: pseudoImageAndText.status,
      roles: pseudoImageAndText.roles.filter((role) => role.role.endsWith('-pseudo')).map((role) => ({{ role: role.role, text: role.text, classification: role.classification }})),
    }},
    hiddenPseudoStatus: hiddenPseudoContent.status,
    transparentPseudoStatus: transparentPseudoContent.status,
    clippedPseudoStatus: clippedPseudoContent.status,
    inactiveQuoteStatus: inactiveQuoteContent.status,
    emptyQuoteStatus: emptyQuoteContent.status,
    quoteDepthStatus: quoteDepthContent.status,
    visibleQuote: {{ status: visibleQuoteContent.status, pseudoRoles: visibleQuoteContent.roles.filter((role) => role.role.endsWith('-pseudo')).map((role) => role.classification) }},
    counterPseudo: {{ status: counterPseudoContent.status, pseudoRoles: counterPseudoContent.roles.filter((role) => role.role.endsWith('-pseudo')).map((role) => ({{ classification: role.classification, complete: role.probeTextComplete }})) }},
    clippedPseudoVariantsStatus: clippedPseudoVariants.status,
    paintSuppressedPseudoStatus: paintSuppressedPseudo.status,
    ancestorSuppressedPseudoStatus: ancestorSuppressedPseudo.status,
    vendorImage: {{ status: vendorImageContent.status, recognized: vendorImageFunctionsRecognized }},
    selectMapping: [selectLabel, selectMultiple, selectListboxGroup, selectOptionStyle].map((evidence) => ({{
      status: evidence.status,
      roles: evidence.roles.filter((role) => role.role.startsWith('interface-control')).map((role) => ({{ role: role.role, text: role.text, classification: role.classification }})),
    }})),
    selectHiddenOption: {{ status: selectHiddenOption.status, mismatches: selectHiddenOption.primaryMismatches.map((role) => role.role) }},
    genericUncertainMapping: {{
      status: genericUncertainMapping.status,
      roles: genericUncertainMapping.roles.filter((role) => role.pseudoTextMappingUnavailable || role.renderedTextMappingUnavailable).map((role) => role.classification),
    }},
    lateRelevantGlyph: lateRelevantGlyph.primaryMismatches.length,
    probeOverflow: {{ status: probeOverflow.status, roles: probeOverflow.roles.filter((role) => role.probeRelevantGlyphOverflow).map((role) => ({{ role: role.role, classification: role.classification }})) }},
    laterUnavailable: {{ status: laterUnavailable.status, roles: laterUnavailable.roles.filter((role) => role.classification === 'evidence_unavailable').map((role) => ({{ role: role.role, sampleIndex: role.sampleIndex }})) }},
    atomicProbe: {{
      status: atomicProbe.status,
      mismatches: atomicProbe.primaryMismatches.map((role) => role.role),
      roles: atomicProbe.roles.map((role) => ({{
        role: role.role,
        classification: role.classification,
        text: role.text,
        declaredFaceCheck: role.declaredFaceCheck,
      }})),
    }},
    inventoryRaceBlocked: inventoryRace.status !== 'captured' || inventoryRace.primaryMismatches.some((role) => role.text === '漢'),
    globalVisibilityRace: globalVisibilityRace.status,
    emptyStatus: empty.status,
  }}));
  await browser.close();
}})().catch((error) => {{ process.stderr.write(String(error.stack || error)); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertIn("fallback", result, result)
        self.assertEqual("fallback_rendered", result["fallback"])
        self.assertEqual(0, result["fallbackMismatch"])
        self.assertEqual("unverified_alias", result["alias"])
        self.assertEqual(0, result["aliasMismatch"])
        self.assertEqual("failed_font_face", result["failed"])
        self.assertEqual(1, result["failedMismatch"])
        self.assertIn({"role": "page-heading", "classification": "unverified_alias", "weight": "400"}, result["weights"])
        self.assertIn({"role": "lead-prose", "classification": "failed_font_face", "weight": "700"}, result["weights"])
        self.assertIn({"role": "lead-prose", "sampleIndex": 4}, result["laterFailure"])
        self.assertIn({"role": "interface-control", "sampleIndex": 0}, result["laterFailure"])
        self.assertEqual("fallback_rendered", result["textarea"])
        self.assertEqual("captured", result["textareaStatus"])
        self.assertEqual("[textarea value present]", result["textareaText"])
        self.assertGreater(result["textareaGlyphs"], 0)
        self.assertEqual("fallback_rendered", result["scrollingTextarea"])
        self.assertEqual("captured", result["scrollingTextareaStatus"])
        self.assertEqual("evidence_unavailable", result["hiddenOverflowTextarea"])
        self.assertEqual("unavailable", result["hiddenOverflowTextareaStatus"])
        self.assertIn("interface-control", result["brokenTextarea"])
        self.assertIn({"role": "interface-control", "text": "[input value present]"}, result["brokenInput"])
        self.assertIn({"role": "page-heading", "stretch": "75%"}, result["stretch"])
        self.assertIn({"role": "page-heading", "stretch": "80%"}, result["stretch80"])
        self.assertEqual(0, result["stretch80Loaded"])
        self.assertEqual(0, result["unicodeRange"])
        self.assertIn({"role": "page-heading", "stretch": "80%"}, result["splitRange"])
        self.assertIn("page-heading", result["punctuationRange"])
        self.assertEqual(0, result["emojiRange"])
        self.assertIn({"role": "page-heading", "stretch": "80%", "weight": "700"}, result["nearestWeight"])
        self.assertIn({"role": "page-heading", "style": "oblique 20deg", "classification": "failed_font_face"}, result["obliqueAngles"])
        self.assertIn({"role": "lead-prose", "style": "oblique 10deg", "classification": "unverified_alias"}, result["obliqueAngles"])
        self.assertIn({"role": "page-heading", "style": "oblique 36deg", "classification": "failed_font_face"}, result["obliqueTurn"])
        self.assertIn({"role": "lead-prose", "style": "italic", "classification": "unverified_alias"}, result["obliqueTurn"])
        self.assertIn({"role": "page-heading", "style": "oblique 11.25deg", "classification": "failed_font_face"}, result["obliqueRad"])
        self.assertEqual([1, 1, 1, 1], result["obliqueBoundaryMismatches"])
        self.assertEqual("unavailable", result["obliquePrecision"]["status"])
        self.assertIn("evidence_unavailable", result["obliquePrecision"]["classifications"])
        self.assertEqual(1, result["longIgnoredPrefix"])
        self.assertIn({"classification": "unverified_alias", "reliable": False}, result["crossStretch"])
        self.assertEqual(1, result["currencySubset"])
        self.assertIn({"role": "interface-control", "hasLettersOrNumbers": False, "hasRelevantGlyph": True}, result["currencyOnly"])
        self.assertEqual(1, result["degreeSubset"])
        self.assertEqual([0, 0], result["emojiVariations"])
        self.assertEqual(1, result["textVariation"])
        self.assertEqual(1, result["invalidTextVariation"])
        self.assertIn("unverified_alias", result["normalBeforeItalic"])
        self.assertIn("unverified_alias", result["normalBeforeOblique"])
        self.assertIn("unverified_alias", result["italicAtTwenty"])
        self.assertIn("page-heading", result["arbitraryItalicAtTwenty"])
        self.assertIn("page-heading", result["arbitraryObliqueAtTwenty"])
        self.assertEqual(1, result["astralBoundary"])
        self.assertEqual(1, result["modifierBypass"])
        self.assertEqual(0, result["validSkinToneEmoji"])
        self.assertEqual(0, result["flagEmoji"])
        self.assertEqual(0, result["singleRegionalIndicator"])
        self.assertEqual(1, result["invalidModifierSequence"])
        self.assertIn("page-heading", result["negativeObliqueAtTwenty"])
        self.assertIn("page-heading", result["positiveLowCrossStyle"])
        self.assertIn("page-heading", result["negativeLowCrossStyle"])
        self.assertEqual(0, result["negativeHighFallsBackToItalic"])
        self.assertIn("page-heading", result["directionalOblique"])
        self.assertIn("page-heading", result["negativeCrossCategory"])
        self.assertIn("page-heading", result["highCrossCategory"])
        self.assertIn("page-heading", result["fourteenBoundary"])
        self.assertIn("lead-prose", result["fourteenBoundary"])
        self.assertIn("interface-control", result["fourteenBoundary"])
        self.assertIn("page-heading", result["patchedBrowserCheck"])
        self.assertEqual("unavailable", result["generatedControlLabels"]["status"])
        self.assertEqual(1, len(result["generatedControlLabels"]["roles"]))
        self.assertTrue(all(role == {"role": "interface-control", "text": "[browser-generated control label unavailable]", "classification": "evidence_unavailable"} for role in result["generatedControlLabels"]["roles"]))
        self.assertEqual(["captured", "captured"], [evidence["status"] for evidence in result["emojiOnly"]])
        self.assertTrue(all("not_applicable" in evidence["classifications"] for evidence in result["emojiOnly"]))
        self.assertEqual("captured", result["whitespaceOnlyStatus"])
        self.assertEqual("unavailable", result["passwordMask"]["status"])
        self.assertIn({"role": "interface-control", "text": "[input value present]", "classification": "evidence_unavailable"}, result["passwordMask"]["roles"])
        self.assertEqual("unavailable", result["localizedNative"]["status"], result["localizedNative"])
        self.assertEqual("captured", result["nativeNonTextStatus"])
        self.assertEqual("captured", result["pseudoContent"]["status"])
        self.assertIn({"role": "interface-control-pseudo", "text": "[generated content]", "classification": "failed_font_face"}, result["pseudoContent"]["roles"])
        self.assertEqual("captured", result["emptyPseudoStatus"])
        self.assertEqual("captured", result["pseudoImageStatus"])
        self.assertEqual("captured", result["pseudoImageAltStatus"])
        self.assertEqual("captured", result["pseudoImageAndText"]["status"])
        self.assertIn({"role": "interface-control-pseudo", "text": "[generated content]", "classification": "unverified_alias"}, result["pseudoImageAndText"]["roles"])
        self.assertEqual("captured", result["hiddenPseudoStatus"])
        self.assertEqual("captured", result["transparentPseudoStatus"])
        self.assertEqual("captured", result["clippedPseudoStatus"])
        self.assertEqual("captured", result["inactiveQuoteStatus"])
        self.assertEqual("captured", result["emptyQuoteStatus"])
        self.assertEqual("captured", result["quoteDepthStatus"])
        self.assertEqual({"status": "unavailable", "pseudoRoles": ["evidence_unavailable"]}, result["visibleQuote"])
        self.assertEqual({"status": "unavailable", "pseudoRoles": [{"classification": "evidence_unavailable", "complete": False}]}, result["counterPseudo"])
        self.assertEqual("captured", result["clippedPseudoVariantsStatus"])
        self.assertEqual("captured", result["paintSuppressedPseudoStatus"])
        self.assertEqual("captured", result["ancestorSuppressedPseudoStatus"])
        self.assertEqual({"status": "captured", "recognized": [True, True]}, result["vendorImage"])
        self.assertTrue(all(evidence["status"] == "captured" for evidence in result["selectMapping"]), result["selectMapping"])
        self.assertIn({"role": "interface-control", "text": "X", "classification": "failed_font_face"}, result["selectMapping"][0]["roles"])
        self.assertTrue(any(role["classification"] == "failed_font_face" for role in result["selectMapping"][1]["roles"]), result["selectMapping"])
        self.assertTrue(any(role["classification"] == "failed_font_face" for role in result["selectMapping"][2]["roles"]), result["selectMapping"])
        self.assertIn({"role": "interface-control-option", "text": "X", "classification": "failed_font_face"}, result["selectMapping"][3]["roles"])
        self.assertEqual({"status": "captured", "mismatches": []}, result["selectHiddenOption"])
        self.assertEqual("captured", result["genericUncertainMapping"]["status"])
        self.assertTrue(result["genericUncertainMapping"]["roles"])
        self.assertTrue(all(classification == "not_applicable" for classification in result["genericUncertainMapping"]["roles"]))
        self.assertEqual(1, result["lateRelevantGlyph"])
        self.assertEqual("unavailable", result["probeOverflow"]["status"])
        self.assertIn({"role": "page-heading", "classification": "evidence_unavailable"}, result["probeOverflow"]["roles"])
        self.assertEqual("unavailable", result["laterUnavailable"]["status"])
        self.assertIn({"role": "lead-prose", "sampleIndex": 3}, result["laterUnavailable"]["roles"])
        self.assertEqual("captured", result["atomicProbe"]["status"])
        self.assertIn("interface-control", result["atomicProbe"]["mismatches"], result["atomicProbe"])
        self.assertTrue(result["inventoryRaceBlocked"])
        self.assertEqual("unavailable", result["globalVisibilityRace"])
        self.assertEqual("unavailable", result["emptyStatus"])

    def test_font_evidence_rejects_author_shadow_text_races(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ collectFontEvidence }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.setContent(`
    <style>
      @font-face {{ font-family: RaceFace; src: url("data:font/woff2;base64,AA=="); unicode-range: U+0041; }}
      @font-face {{ font-family: RaceFace; src: local("Arial"); unicode-range: U+0042; }}
      h1, button {{ font-family: RaceFace, serif; }}
    </style>
    <h1>Stable B</h1><main><button><x-race></x-race></button></main>
    <script>
      customElements.define('x-race', class extends HTMLElement {{
        constructor() {{
          super();
          this.attachShadow({{ mode: 'open' }}).innerHTML = '<span>A</span>';
        }}
      }});
    <\/script>
  `);
  const nativeNewCdpSession = context.newCDPSession.bind(context);
  context.newCDPSession = async (target) => {{
    const session = await nativeNewCdpSession(target);
    const nativeSend = session.send.bind(session);
    let mutated = false;
    session.send = async (method, params) => {{
      const result = await nativeSend(method, params);
      if (!mutated && method === 'DOM.describeNode' && result.node?.localName === 'button') {{
        mutated = true;
        await page.evaluate(() => {{
          document.querySelector('x-race').shadowRoot.querySelector('span').firstChild.data = 'B';
        }});
      }}
      return result;
    }};
    return session;
  }};
  const evidence = await collectFontEvidence(context, page);
  process.stdout.write(JSON.stringify({{
    status: evidence.status,
    error: evidence.error,
    liveText: await page.locator('x-race').evaluate((node) => node.shadowRoot.textContent),
  }}));
  await browser.close();
}})().catch((error) => {{ process.stderr.write(String(error.stack || error)); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertEqual("B", result["liveText"])
        self.assertEqual("unavailable", result["status"])
        self.assertIn("font selector state changed during capture", result["error"])

    def test_font_evidence_rejects_shadow_cssom_aba_races(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ collectFontEvidence }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{ headless: true }});
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.setContent(`
    <style id="rules">
      @font-face {{ font-family: CssomBroken; src: url("data:font/woff2;base64,AA=="); unicode-range: U+0041; }}
      h1 {{ font-family: Arial, sans-serif; }}
      button {{ --shadow-font: Arial; }}
    </style>
    <h1>Stable B</h1><main><button><x-css></x-css></button></main>
    <script>
      customElements.define('x-css', class extends HTMLElement {{
        constructor() {{
          super();
          this.attachShadow({{ mode: 'open' }}).innerHTML =
            '<style>span {{ font-family: var(--shadow-font), serif; }}</style><span>A</span>';
        }}
      }});
    <\/script>
  `);
  const nativeNewCdpSession = context.newCDPSession.bind(context);
  context.newCDPSession = async (target) => {{
    const session = await nativeNewCdpSession(target);
    const nativeSend = session.send.bind(session);
    let buttonDescriptions = 0;
    session.send = async (method, params) => {{
      const result = await nativeSend(method, params);
      if (method === 'DOM.describeNode' && result.node?.localName === 'button') {{
        buttonDescriptions += 1;
        if (buttonDescriptions === 1) {{
          await page.evaluate(() => [...document.querySelector('#rules').sheet.cssRules].find((rule) => rule.selectorText === 'button').style.setProperty('--shadow-font', 'CssomBroken'));
        }} else if (buttonDescriptions === 2) {{
          await page.evaluate(() => [...document.querySelector('#rules').sheet.cssRules].find((rule) => rule.selectorText === 'button').style.setProperty('--shadow-font', 'Arial'));
        }}
      }}
      return result;
    }};
    return session;
  }};
  const evidence = await collectFontEvidence(context, page);
  process.stdout.write(JSON.stringify({{
    status: evidence.status,
    error: evidence.error,
    liveFont: await page.locator('x-css').evaluate((node) => getComputedStyle(node.shadowRoot.querySelector('span')).fontFamily),
  }}));
  await browser.close();
}})().catch((error) => {{ process.stderr.write(String(error.stack || error)); process.exitCode = 1; }});
"""
        result = self.run_node(source)
        self.assertIn("Arial", result["liveFont"])
        self.assertEqual("unavailable", result["status"])
        self.assertIn("font role evidence changed during collection", result["error"])

    def test_font_evidence_requires_painted_stable_pseudo_glyphs(self) -> None:
        source = """
const { chromium } = require('playwright');
const { collectFontEvidence } = require(__AUDITOR__);
(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  async function probe(html) {
    await page.setContent(html);
    await page.evaluate(() => document.fonts.ready);
    return collectFontEvidence(context, page);
  }
  const hiddenHost = await probe(`<style>@font-face{font-family:BrokenVisible;src:url("data:font/woff2;base64,AA==")}button{visibility:hidden;font-family:BrokenVisible,serif}button::before{content:"X";visibility:visible}</style><h1>正常</h1><main><button></button></main>`);
  const zeroHost = await probe(`<style>@font-face{font-family:BrokenZero;src:url("data:font/woff2;base64,AA==")}button{appearance:none;position:relative;width:0;height:0;padding:0;border:0;font-family:BrokenZero,serif}button::before{content:"X";position:absolute;display:block;width:20px;height:20px;overflow:visible}</style><h1>正常</h1><main><button></button></main>`);
  const contentsHost = await probe(`<style>@font-face{font-family:BrokenContents;src:url("data:font/woff2;base64,AA==")}h1{display:contents;font-family:BrokenContents,serif}h1::before{content:"X";display:block}</style><h1></h1><main><p>正常</p></main>`);
  const paintSuppressed = await probe(`<style>@font-face{font-family:InvisibleBroken;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button::before{content:"X";font-family:InvisibleBroken,serif}button:nth-child(1)::before{opacity:0}button:nth-child(2)::before{color:transparent}button:nth-child(3)::before{filter:opacity(0)}button:nth-child(4)::before{clip-path:inset(50%)}button:nth-child(5)::before{transform:scale(0)}button:nth-child(6)::before{display:inline-block;width:0;height:0;padding:0;overflow:hidden;border:10px solid}button:nth-child(7)::before{font-size:0;padding:10px}button:nth-child(8)::before{color:transparent;text-shadow:0 0 2px transparent}button:nth-child(9)::before{color:transparent;-webkit-text-stroke:2px transparent}button:nth-child(10)::before{color:transparent;background:none;background-clip:text}button:nth-child(11)::before{clip-path:polygon(0 0,0 0,0 0)}button:nth-child(12)::before{position:absolute;clip:rect(0 0 0 0)}button:nth-child(13)::before{mask-image:linear-gradient(transparent,transparent)}button:nth-child(14)::before{mask-image:linear-gradient(black,black);mask-mode:luminance}button:nth-child(15)::before{clip-path:ellipse(10px 0 at center)}</style><h1>正常</h1><main><button>A</button><button>B</button><button>C</button><button>D</button><button>E</button><button>F</button><button>G</button><button>H</button><button>I</button><button>J</button><button>K</button><button>L</button><button>M</button><button>N</button><button>O</button></main>`);
  const paintVisibleEffects = await probe(`<style>@font-face{font-family:VisibleEffectBroken;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button::before{content:"X";font-family:VisibleEffectBroken,serif;color:transparent}button:nth-child(1)::before{text-shadow:0 0 2px red}button:nth-child(2)::before{-webkit-text-stroke:2px red}button:nth-child(3)::before{background:red;background-clip:text}</style><h1>正常</h1><main><button>A</button><button>B</button><button>C</button></main>`);
  const unknownShapeEffects = await probe(`<style>@font-face{font-family:UnknownShapeBroken;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button::before{content:"X";font-family:UnknownShapeBroken,serif;color:red}button:nth-child(1)::before{clip-path:circle(closest-side at 0 0)}button:nth-child(2)::before{clip-path:circle(10px at -100px -100px)}button:nth-child(3)::before{clip-path:ellipse(10px 10px at -100px -100px)}button:nth-child(4)::before{clip-path:polygon(200% 200%,300% 200%,200% 300%)}button:nth-child(5)::before{clip-path:polygon(0 0,100% 100%,0 100%,100% 0)}</style><h1>正常</h1><main><button>A</button><button>B</button><button>C</button><button>D</button><button>E</button></main>`);
  const visibleGeometryEffects = await probe(`<style>@font-face{font-family:VisibleGeometryBroken;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button::before{content:"X";font-family:VisibleGeometryBroken,serif;color:red}button:nth-child(1)::before{mask-image:linear-gradient(black,black);mask-size:100% 100%;mask-position:0 0;mask-repeat:no-repeat}button:nth-child(2)::before{color:transparent;background-image:linear-gradient(red,red);background-size:100% 100%;background-position:0 0;background-repeat:no-repeat;background-clip:text}</style><h1>正常</h1><main><button>A</button><button>B</button></main>`);
  const unknownPathPaint = await probe(`<style>@font-face{font-family:UnknownPath;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button::before{content:"X";font-family:UnknownPath,serif;clip-path:path("M 0 0")}</style><h1>正常</h1><main><button>A</button></main>`);
  const unknownCompositePaint = await probe(`<style>@font-face{font-family:UnknownComposite;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button::before{content:"X";font-family:UnknownComposite,serif;mask-image:linear-gradient(black,black),linear-gradient(black,black);mask-composite:exclude}</style><h1>正常</h1><main><button>A</button></main>`);
  const unknownExternalPaint = await probe(`<style>@font-face{font-family:UnknownExternal;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button::before{content:"X";font-family:UnknownExternal,serif;color:transparent;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1' height='1'/%3E");background-clip:text}</style><h1>正常</h1><main><button>A</button></main>`);
  const unknownMaskGeometry = await probe(`<style>@font-face{font-family:UnknownMaskGeometry;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button::before{content:"X";font-family:UnknownMaskGeometry,serif;mask-image:linear-gradient(black,black);mask-size:0 0;mask-repeat:no-repeat}</style><h1>正常</h1><main><button>A</button></main>`);
  const unknownMaskPosition = await probe(`<style>@font-face{font-family:UnknownMaskPosition;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button::before{content:"X";font-family:UnknownMaskPosition,serif;mask-image:linear-gradient(black,black);mask-size:10px 10px;mask-position:1000px 1000px;mask-repeat:no-repeat}</style><h1>正常</h1><main><button>A</button></main>`);
  const unknownBackgroundGeometry = await probe(`<style>@font-face{font-family:UnknownBackgroundGeometry;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button::before{content:"X";font-family:UnknownBackgroundGeometry,serif;color:transparent;background-image:linear-gradient(red,red);background-size:0 0;background-repeat:no-repeat;background-clip:text}</style><h1>正常</h1><main><button>A</button></main>`);
  const unknownBackgroundPosition = await probe(`<style>@font-face{font-family:UnknownBackgroundPosition;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button::before{content:"X";font-family:UnknownBackgroundPosition,serif;color:transparent;background-image:linear-gradient(red,red);background-size:10px 10px;background-position:1000px 1000px;background-repeat:no-repeat;background-clip:text}</style><h1>正常</h1><main><button>A</button></main>`);
  const unknownMaskOrigin = await probe(`<style>@font-face{font-family:UnknownMaskOrigin;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button::before{content:"X";font-family:UnknownMaskOrigin,serif;display:block;width:0;height:0;padding:20px;mask-image:linear-gradient(black,black);mask-origin:content-box;mask-clip:content-box;mask-size:auto;mask-repeat:no-repeat}</style><h1>正常</h1><main><button>A</button></main>`);
  const unknownBackgroundOrigin = await probe(`<style>@font-face{font-family:UnknownBackgroundOrigin;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button::before{content:"X";font-family:UnknownBackgroundOrigin,serif;display:block;width:0;height:0;padding:20px;color:transparent;background-image:linear-gradient(red,red);background-origin:content-box;background-size:auto;background-repeat:no-repeat;background-clip:text}</style><h1>正常</h1><main><button>A</button></main>`);
  const unknownLegacyClip = await probe(`<style>@font-face{font-family:UnknownLegacyClip;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button::before{content:"X";font-family:UnknownLegacyClip,serif;position:absolute;clip:rect(0 10px 10px 0)}</style><h1>正常</h1><main><button>A</button></main>`);
  const ancestorSuppressed = await probe(`<style>@font-face{font-family:AncestorBroken;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button::before{content:"X";font-family:AncestorBroken,serif}.opacity{opacity:0}.filter{filter:opacity(0)}.transform{transform:scale(0)}.clip{clip-path:inset(50%)}</style><h1>正常</h1><main><div class="opacity"><button>A</button></div><div class="filter"><button>B</button></div><div class="transform"><button>C</button></div><div class="clip"><button>D</button></div></main>`);
  const emptyLoaded = await probe(`<style>@font-face{font-family:EmptyLoaded;src:local("Arial")}button{font-family:EmptyLoaded,serif}button::before{content:"A"}</style><h1>正常</h1><main><button></button></main>`);
  const hostWithoutPseudo = await probe(`<style>button{font-family:Arial,sans-serif}</style><h1>正常</h1><main><button>漢</button></main>`);
  const hostWithPseudo = await probe(`<style>button{font-family:Arial,sans-serif}button::before{content:"X"}</style><h1>正常</h1><main><button>漢</button></main>`);
  const overriddenOnly = await probe(`<style>@font-face{font-family:BrokenHost;src:url("data:font/woff2;base64,AA==")}button{font-family:BrokenHost,serif}button span.override{font-family:Arial,sans-serif}</style><h1>正常</h1><main><button><span class="override">ABC</span></button></main>`);
  const mixedOverride = await probe(`<style>@font-face{font-family:BrokenHost;src:url("data:font/woff2;base64,AA==")}button{font-family:BrokenHost,serif}button span.override{font-family:Arial,sans-serif}</style><h1>正常</h1><main><button>X<span class="override">ABC</span>Y</button></main>`);
  const inheritedSpan = await probe(`<style>button{font-family:Arial,sans-serif}</style><h1>正常</h1><main><button>X<span>ABC</span>Y</button></main>`);
  const displayContentsText = await probe(`<style>@font-face{font-family:BrokenContentsText;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button span{display:contents;font-family:BrokenContentsText,serif}</style><h1>正常</h1><main><button><span>XYZ</span></button></main>`);
  const displayContentsOverflowHidden = await probe(`<style>@font-face{font-family:BrokenContentsHidden;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button span{display:contents;overflow:hidden;font-family:BrokenContentsHidden,serif}</style><h1>正常</h1><main><button><span>XYZ</span></button></main>`);
  const displayContentsOverflowClip = await probe(`<style>@font-face{font-family:BrokenContentsClip;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button span{display:contents;overflow:clip;font-family:BrokenContentsClip,serif}</style><h1>正常</h1><main><button><span>XYZ</span></button></main>`);
  const nonContiguousText = await probe(`<style>@font-face{font-family:BrokenSymbol;src:url("data:font/woff2;base64,AA==");unicode-range:U+00A9}button{font-family:BrokenSymbol,serif}button span{font-family:Arial,sans-serif}</style><h1>正常</h1><main><button>©<span>X</span>️ A</button></main>`);
  const transparentSeparatorText = await probe(`<style>@font-face{font-family:BrokenTransparentSymbol;src:url("data:font/woff2;base64,AA==");unicode-range:U+00A9}button{font-family:BrokenTransparentSymbol,serif}button span{color:transparent}</style><h1>正常</h1><main><button>©<span>X</span>️ A</button></main>`);
  const breakSeparatorText = await probe(`<style>@font-face{font-family:BrokenBreakSymbol;src:url("data:font/woff2;base64,AA==");unicode-range:U+00A9}button{font-family:BrokenBreakSymbol,serif}</style><h1>正常</h1><main><button>©<br>️ A</button></main>`);
  const pseudoSeparatorText = await probe(`<style>@font-face{font-family:BrokenPseudoSeparator;src:url("data:font/woff2;base64,AA==");unicode-range:U+00A9}button{font-family:BrokenPseudoSeparator,serif}button span::before{content:"X";font-family:Arial,sans-serif}</style><h1>正常</h1><main><button>©<span></span>️ A</button></main>`);
  const nestedPseudoText = await probe(`<style>@font-face{font-family:BrokenNestedPseudo;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button span::before{content:"XYZ";font-family:BrokenNestedPseudo,serif}</style><h1>正常</h1><main><button><span></span></button></main>`);
  const selfClippedText = await probe(`<style>@font-face{font-family:HiddenBroken;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button span{display:inline-block;width:0;overflow:hidden;white-space:nowrap;font-family:HiddenBroken,serif}</style><h1>正常</h1><main><button><span>XYZ</span></button></main>`);
  const offscreenText = await probe(`<style>@font-face{font-family:OffscreenBroken;src:url("data:font/woff2;base64,AA==")}button{font-family:Arial,sans-serif}button span{position:fixed;left:-10000px;font-family:OffscreenBroken,serif}</style><h1>正常</h1><main><button><span>XYZ</span></button></main>`);
  const fixedOutsideWideCanvas = await probe(`<style>@font-face{font-family:WideCanvasBroken;src:url("data:font/woff2;base64,AA==")}body{width:2500px;height:2050px}button{font-family:Arial,sans-serif}button span{position:fixed;left:1600px;top:0;font-family:WideCanvasBroken,serif}</style><h1>正常</h1><main><button><span>XYZ</span></button></main>`);
  const fixedOutsideTallCanvas = await probe(`<style>@font-face{font-family:TallCanvasBroken;src:url("data:font/woff2;base64,AA==")}body{width:2500px;height:2050px}button{font-family:Arial,sans-serif}button span{position:fixed;left:0;top:1200px;font-family:TallCanvasBroken,serif}</style><h1>正常</h1><main><button><span>XYZ</span></button></main>`);
  const transformedFixedText = await probe(`<style>@font-face{font-family:TransformedFixedBroken;src:url("data:font/woff2;base64,AA==")}body{height:2050px}button{font-family:Arial,sans-serif}.containing-block{transform:translateZ(0)}button span{position:fixed;left:0;top:1200px;font-family:TransformedFixedBroken,serif}</style><h1>正常</h1><main><div class="containing-block"><button><span>XYZ</span></button></div></main>`);
  const unknownFirstLetter = await probe(`<style>@font-face{font-family:BrokenFirstLetter;src:url("data:font/woff2;base64,AA==")}h1{font-family:Arial,sans-serif}h1::first-letter{font-family:BrokenFirstLetter,serif}</style><h1>XYZ</h1><main><p>正常</p></main>`);
  const unknownFirstLine = await probe(`<style>@font-face{font-family:BrokenFirstLine;src:url("data:font/woff2;base64,AA==")}h1{font-family:Arial,sans-serif}main p{font-family:Arial,sans-serif}main p::first-line{font-family:BrokenFirstLine,serif}</style><h1>正常</h1><main><p>XYZ</p></main>`);
  const unknownTextTransform = await probe(`<style>@font-face{font-family:BrokenUpper;src:url("data:font/woff2;base64,AA==");unicode-range:U+0041}h1{font-family:BrokenUpper,serif;text-transform:uppercase}</style><h1>a</h1><main><p>正常</p></main>`);
  const unknownPseudoTextTransform = await probe(`<style>@font-face{font-family:BrokenPseudoUpper;src:url("data:font/woff2;base64,AA==");unicode-range:U+0049}button{font-family:Arial,sans-serif}button::before{content:"i";font-family:BrokenPseudoUpper,serif;text-transform:uppercase}</style><h1>正常</h1><main><button>A</button></main>`);
  const unchangedTextTransform = await probe(`<style>h1{font-family:Arial,sans-serif;text-transform:uppercase}</style><h1>繁體中文</h1><main><p>正常</p></main>`);
  const unknownPlaceholder = await probe(`<style>@font-face{font-family:PlaceholderBroken;src:url("data:font/woff2;base64,AA==")}input{font-family:Arial,sans-serif}input::placeholder{font-family:PlaceholderBroken,serif}</style><h1>正常</h1><main><input placeholder="XYZ"></main>`);
  const unknownTextSecurity = await probe(`<style>@font-face{font-family:BrokenMasked;src:url("data:font/woff2;base64,AA==");unicode-range:U+005A}input{font-family:BrokenMasked,serif;-webkit-text-security:disc}</style><h1>正常</h1><main><input type="text" value="Z"></main>`);
  const unknownPartialClip = await probe(`<style>@font-face{font-family:BrokenTail;src:url("data:font/woff2;base64,AA==");unicode-range:U+005A}h1{font-family:Arial,sans-serif}button{font-family:Arial,sans-serif}button span{display:inline-block;width:40px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:BrokenTail,serif}</style><h1>正常</h1><main><button><span>AAAAAZ</span></button></main>`);
  const unknownPartialNativeClip = await probe(`<style>@font-face{font-family:BrokenInputTail;src:url("data:font/woff2;base64,AA==");unicode-range:U+005A}input{box-sizing:border-box;width:54px;font-family:BrokenInputTail,serif}</style><h1>正常</h1><main><input type="text" value="AAAAAZ"></main>`);

  await page.setContent(`<style>@font-face{font-family:CounterStable;src:local("Arial")}main{counter-reset:item 7}button{font-family:CounterStable,serif}button::before{content:counter(item)}</style><h1>正常</h1><main><button>A</button></main>`);
  await page.evaluate(() => document.fonts.ready);
  const nativeNewCDPSession = context.newCDPSession.bind(context);
  context.newCDPSession = async (...args) => {
    const session = await nativeNewCDPSession(...args);
    const nativeSend = session.send.bind(session);
    const pseudoNodeIds = new Set();
    const pseudoFontReads = new Map();
    session.send = async (method, params) => {
      const result = await nativeSend(method, params);
      if (method === 'DOM.describeNode') {
        for (const pseudo of result.node?.pseudoElements || []) pseudoNodeIds.add(pseudo.nodeId);
      }
      if (method === 'CSS.getPlatformFontsForNode' && pseudoNodeIds.has(params.nodeId)) {
        const reads = (pseudoFontReads.get(params.nodeId) || 0) + 1;
        pseudoFontReads.set(params.nodeId, reads);
        if (reads === 2 && result.fonts?.length) {
          result.fonts = result.fonts.map((font, index) => index === 0 ? { ...font, glyphCount: font.glyphCount + 1 } : font);
        }
      }
      return result;
    };
    return session;
  };
  const platformRace = await collectFontEvidence(context, page);
  context.newCDPSession = nativeNewCDPSession;

  await page.setContent(`<style id="global-race-style">@font-face{font-family:GlobalRace;src:local("Arial")}h1{font-family:GlobalRace,serif}</style><h1>ABC</h1>`);
  await page.evaluate(() => document.fonts.ready);
  let headingSnapshots = 0;
  context.newCDPSession = async (...args) => {
    const session = await nativeNewCDPSession(...args);
    const nativeSend = session.send.bind(session);
    session.send = async (method, params) => {
      const result = await nativeSend(method, params);
      if (method === 'Runtime.evaluate' && String(params.expression).includes('captureFontSelectorSnapshot') && String(params.expression).endsWith(')("h1")')) {
        headingSnapshots += 1;
        if (headingSnapshots === 3) {
          await page.evaluate(() => {
            document.querySelector('#global-race-style').textContent = '@font-face{font-family:GlobalRace;src:local("Courier New")}h1{font-family:GlobalRace,serif}';
          });
          await page.evaluate(() => document.fonts.load('16px GlobalRace', 'ABC'));
        }
      }
      return result;
    };
    return session;
  };
  const globalInventoryRace = await collectFontEvidence(context, page);
  context.newCDPSession = nativeNewCDPSession;

  const summarize = (evidence) => ({
    status: evidence.status,
    mismatches: evidence.primaryMismatches.map((role) => role.role),
    pseudoRoles: evidence.roles.filter((role) => role.role.endsWith('-pseudo')).map((role) => ({
      role: role.role,
      classification: role.classification,
      stable: role.platformFontsStable,
    })),
    generatedUnavailable: evidence.roles.filter((role) => role.browserGeneratedTextUnavailable).length,
  });
  const summarizeTextRuns = (evidence) => ({
    status: evidence.status,
    mismatches: evidence.primaryMismatches.map((role) => role.declaredPrimary),
    runs: evidence.roles.filter((role) => role.role === 'interface-control' && role.source === 'dom-text').map((role) => ({
      declaredPrimary: role.declaredPrimary,
      classification: role.classification,
      text: role.text,
      textRunIndex: role.textRunIndex,
      textNodeCount: role.textNodeCount,
    })).sort((left, right) => left.textRunIndex - right.textRunIndex),
  });
  process.stdout.write(JSON.stringify({
    visibleHosts: [hiddenHost, zeroHost, contentsHost].map(summarize),
    paintSuppressed: summarize(paintSuppressed),
    paintVisibleEffects: summarize(paintVisibleEffects),
    unknownShapeEffects: summarize(unknownShapeEffects),
    visibleGeometryEffects: summarize(visibleGeometryEffects),
    unknownEffects: [unknownShapeEffects, unknownPathPaint, unknownCompositePaint, unknownExternalPaint, unknownMaskGeometry, unknownMaskPosition, unknownBackgroundGeometry, unknownBackgroundPosition, unknownMaskOrigin, unknownBackgroundOrigin, unknownLegacyClip].map(summarize),
    ancestorSuppressed: summarize(ancestorSuppressed),
    emptyLoaded: summarize(emptyLoaded),
    hostClassifications: [hostWithoutPseudo, hostWithPseudo].map((evidence) => evidence.roles.find((role) => role.role === 'interface-control')?.classification),
    hostTextRuns: [overriddenOnly, mixedOverride, inheritedSpan].map(summarizeTextRuns),
    displayContentsText: summarizeTextRuns(displayContentsText),
    displayContentsOverflow: [displayContentsOverflowHidden, displayContentsOverflowClip].map(summarizeTextRuns),
    nonContiguousText: summarizeTextRuns(nonContiguousText),
    transparentSeparatorText: summarizeTextRuns(transparentSeparatorText),
    boundaryText: [breakSeparatorText, pseudoSeparatorText].map(summarizeTextRuns),
    nestedPseudoText: {
      status: nestedPseudoText.status,
      mismatches: nestedPseudoText.primaryMismatches.map((role) => role.declaredPrimary),
      roles: nestedPseudoText.roles.filter((role) => role.source === 'pseudo').map((role) => ({
        declaredPrimary: role.declaredPrimary,
        classification: role.classification,
        pseudoDescendant: role.pseudoDescendant,
      })),
    },
    invisibleTextRuns: [selfClippedText, offscreenText, fixedOutsideWideCanvas, fixedOutsideTallCanvas].map(summarizeTextRuns),
    transformedFixedText: summarizeTextRuns(transformedFixedText),
    unknownTextMapping: [unknownFirstLetter, unknownFirstLine, unknownTextTransform, unknownPseudoTextTransform, unknownPlaceholder, unknownTextSecurity].map((evidence) => ({
      status: evidence.status,
      mismatches: evidence.primaryMismatches.map((role) => role.declaredPrimary),
      classifications: evidence.roles.map((role) => role.classification),
    })),
    unknownPartialClip: {
      status: unknownPartialClip.status,
      mismatches: unknownPartialClip.primaryMismatches.map((role) => role.declaredPrimary),
      classifications: unknownPartialClip.roles.map((role) => role.classification),
    },
    unknownPartialNativeClip: {
      status: unknownPartialNativeClip.status,
      mismatches: unknownPartialNativeClip.primaryMismatches.map((role) => role.declaredPrimary),
      classifications: unknownPartialNativeClip.roles.map((role) => role.classification),
    },
    unchangedTextTransform: summarize(unchangedTextTransform),
    platformRace: { ...summarize(platformRace), error: platformRace.error || null },
    globalInventoryRace: { status: globalInventoryRace.status, headingSnapshots },
  }));
  await browser.close();
})().catch((error) => { process.stderr.write(String(error.stack || error)); process.exitCode = 1; });
""".replace("__AUDITOR__", json.dumps(str(AUDITOR)))
        result = self.run_node(source)
        self.assertTrue(all(evidence["status"] == "captured" for evidence in result["visibleHosts"]), result)
        self.assertTrue(all(evidence["mismatches"] for evidence in result["visibleHosts"]), result)
        self.assertTrue(all(evidence["pseudoRoles"][0]["classification"] == "failed_font_face" for evidence in result["visibleHosts"]), result)
        self.assertEqual({"status": "captured", "mismatches": [], "pseudoRoles": [], "generatedUnavailable": 0}, result["paintSuppressed"])
        self.assertEqual("captured", result["paintVisibleEffects"]["status"])
        self.assertEqual(["interface-control-pseudo"] * 3, result["paintVisibleEffects"]["mismatches"])
        self.assertTrue(all(role["classification"] == "failed_font_face" for role in result["paintVisibleEffects"]["pseudoRoles"]), result)
        self.assertEqual("unavailable", result["unknownShapeEffects"]["status"])
        self.assertEqual([], result["unknownShapeEffects"]["mismatches"])
        self.assertEqual(["interface-control-pseudo"] * 2, result["visibleGeometryEffects"]["mismatches"])
        self.assertTrue(all(role["classification"] == "failed_font_face" for role in result["visibleGeometryEffects"]["pseudoRoles"]), result)
        self.assertTrue(all(evidence["status"] == "unavailable" for evidence in result["unknownEffects"]), result)
        self.assertTrue(all(evidence["mismatches"] == [] for evidence in result["unknownEffects"]), result)
        self.assertTrue(all(evidence["pseudoRoles"][0]["classification"] == "evidence_unavailable" for evidence in result["unknownEffects"]), result)
        self.assertEqual({"status": "captured", "mismatches": [], "pseudoRoles": [], "generatedUnavailable": 0}, result["ancestorSuppressed"])
        self.assertEqual("captured", result["emptyLoaded"]["status"])
        self.assertEqual(0, result["emptyLoaded"]["generatedUnavailable"])
        self.assertIn({"role": "interface-control-pseudo", "classification": "unverified_alias", "stable": True}, result["emptyLoaded"]["pseudoRoles"])
        self.assertEqual(["fallback_rendered", "fallback_rendered"], result["hostClassifications"])
        self.assertEqual(
            {
                "status": "captured",
                "mismatches": [],
                "runs": [{"declaredPrimary": "Arial", "classification": "rendered", "text": "ABC", "textRunIndex": 0, "textNodeCount": 1}],
            },
            result["hostTextRuns"][0],
        )
        self.assertEqual("captured", result["hostTextRuns"][1]["status"])
        self.assertEqual(["BrokenHost", "BrokenHost"], result["hostTextRuns"][1]["mismatches"])
        self.assertEqual(
            [
                {"declaredPrimary": "BrokenHost", "classification": "failed_font_face", "text": "X", "textRunIndex": 0, "textNodeCount": 1},
                {"declaredPrimary": "Arial", "classification": "rendered", "text": "ABC", "textRunIndex": 1, "textNodeCount": 1},
                {"declaredPrimary": "BrokenHost", "classification": "failed_font_face", "text": "Y", "textRunIndex": 2, "textNodeCount": 1},
            ],
            result["hostTextRuns"][1]["runs"],
        )
        self.assertEqual(
            {
                "status": "captured",
                "mismatches": [],
                "runs": [
                    {"declaredPrimary": "Arial", "classification": "rendered", "text": "X", "textRunIndex": 0, "textNodeCount": 1},
                    {"declaredPrimary": "Arial", "classification": "rendered", "text": "ABC", "textRunIndex": 1, "textNodeCount": 1},
                    {"declaredPrimary": "Arial", "classification": "rendered", "text": "Y", "textRunIndex": 2, "textNodeCount": 1},
                ],
            },
            result["hostTextRuns"][2],
        )
        self.assertEqual("captured", result["displayContentsText"]["status"])
        self.assertEqual(["BrokenContentsText"], result["displayContentsText"]["mismatches"])
        self.assertEqual("XYZ", result["displayContentsText"]["runs"][0]["text"])
        self.assertEqual([["BrokenContentsHidden"], ["BrokenContentsClip"]], [evidence["mismatches"] for evidence in result["displayContentsOverflow"]])
        self.assertEqual("captured", result["nonContiguousText"]["status"])
        self.assertEqual(["BrokenSymbol"], result["nonContiguousText"]["mismatches"])
        self.assertEqual(["©", "X", "️ A"], [run["text"] for run in result["nonContiguousText"]["runs"]])
        self.assertEqual(["BrokenTransparentSymbol"], result["transparentSeparatorText"]["mismatches"])
        self.assertEqual([["BrokenBreakSymbol"], ["BrokenPseudoSeparator"]], [evidence["mismatches"] for evidence in result["boundaryText"]])
        self.assertEqual(
            {
                "status": "captured",
                "mismatches": ["BrokenNestedPseudo"],
                "roles": [{"declaredPrimary": "BrokenNestedPseudo", "classification": "failed_font_face", "pseudoDescendant": True}],
            },
            result["nestedPseudoText"],
        )
        self.assertTrue(all(evidence == {"status": "captured", "mismatches": [], "runs": []} for evidence in result["invisibleTextRuns"]), result)
        self.assertEqual(["TransformedFixedBroken"], result["transformedFixedText"]["mismatches"])
        self.assertTrue(all(evidence["status"] == "unavailable" for evidence in result["unknownTextMapping"]), result)
        self.assertTrue(all(evidence["mismatches"] == [] for evidence in result["unknownTextMapping"]), result)
        self.assertTrue(all("evidence_unavailable" in evidence["classifications"] for evidence in result["unknownTextMapping"]), result)
        self.assertEqual("unavailable", result["unknownPartialClip"]["status"])
        self.assertEqual([], result["unknownPartialClip"]["mismatches"])
        self.assertIn("evidence_unavailable", result["unknownPartialClip"]["classifications"])
        self.assertEqual("unavailable", result["unknownPartialNativeClip"]["status"])
        self.assertEqual([], result["unknownPartialNativeClip"]["mismatches"])
        self.assertIn("evidence_unavailable", result["unknownPartialNativeClip"]["classifications"])
        self.assertEqual("captured", result["unchangedTextTransform"]["status"])
        self.assertEqual([], result["unchangedTextTransform"]["mismatches"])
        self.assertEqual("unavailable", result["platformRace"]["status"])
        self.assertEqual([], result["platformRace"]["pseudoRoles"])
        self.assertIn("font role evidence changed during collection", result["platformRace"]["error"])
        self.assertEqual("unavailable", result["globalInventoryRace"]["status"])
        self.assertGreaterEqual(result["globalInventoryRace"]["headingSnapshots"], 4)

    def test_interactions_use_only_public_brief_hooks(self) -> None:
        source = AUDITOR.read_text(encoding="utf-8")
        brief = (ROOT / "evals" / "briefs" / "grant-review-board-v6.md").read_text(encoding="utf-8")
        self.assertNotIn('[data-action="compare"]', source)
        self.assertNotIn("#nextCase", source)
        self.assertNotIn('input[value="s"]', source)
        for hook in ('data-eval="compare-a-action"', 'data-eval="compare-b-action"', 'data-eval="next-proposal"'):
            self.assertIn(hook, source)
            self.assertIn(hook, brief)

    def test_traditional_chinese_language_variants_are_accepted(self) -> None:
        source = f"""
const {{ issueCodes }} = require({json.dumps(str(AUDITOR))});
const base = {{
  interaction: {{ failures: [] }}, contractIssues: [], hasMain: true, visibleMainCount: 1,
  hasHeading: true, horizontalOverflow: false, outsideViewport: [], shortActionFailures: [],
  clippedText: [], criticalTextCollisions: [], fixedStickyObstructions: [], viewport: 'mobile',
  smallTouchTargets: [], readingRhythm: {{ tooTight: [], tooWide: [] }}, narrowTextColumns: [],
  bodyFlow: {{ forcedLineBreaks: [], nonWrappingProse: [], underfilledProseBlocks: [] }},
  textScale: {{ undersizedReadableText: [] }},
  headingFlow: {{ compressedCjkHeadings: [], orphanedCjkHeadingLines: [], underfilledWideHeadings: [] }},
  layoutFlow: {{ domOrderReversals: [], displacedIntroCopy: [], unfilledColumnVoids: [] }},
  localeFlow: {{ untranslatedInterfaceCopy: [] }},
  reducedMotionAnimations: [], consoleErrors: [], externalRequests: [], badResponses: [],
  caseId: 'wind-maintenance-dispatch-v6',
}};
process.stdout.write(JSON.stringify({{
  hant: issueCodes({{ ...base, lang: 'zh-Hant' }}),
  taiwan: issueCodes({{ ...base, lang: 'zh-Hant-TW' }}),
  wrong: issueCodes({{ ...base, lang: 'en' }}),
}}));
"""
        result = self.run_node(source)
        self.assertNotIn("document_lang_not_zh_hant", result["hant"])
        self.assertNotIn("document_lang_not_zh_hant", result["taiwan"])
        self.assertIn("document_lang_not_zh_hant", result["wrong"])

    def test_body_flow_defects_become_repair_codes(self) -> None:
        source = f"""
const {{ issueCodes }} = require({json.dumps(str(AUDITOR))});
const base = {{
  interaction: {{ failures: [] }}, contractIssues: [], lang: 'zh-Hant-TW', hasMain: true,
  visibleMainCount: 1, hasHeading: true, horizontalOverflow: false, outsideViewport: [],
  shortActionFailures: [], clippedText: [], criticalTextCollisions: [], fixedStickyObstructions: [],
  viewport: 'desktop', smallTouchTargets: [], readingRhythm: {{ tooTight: [], tooWide: [] }},
  narrowTextColumns: [], reducedMotionAnimations: [], consoleErrors: [], externalRequests: [], badResponses: [],
  headingFlow: {{ compressedCjkHeadings: [], orphanedCjkHeadingLines: [], underfilledWideHeadings: [] }},
  layoutFlow: {{ domOrderReversals: [], displacedIntroCopy: [] }},
  localeFlow: {{ untranslatedInterfaceCopy: [] }},
}};
process.stdout.write(JSON.stringify({{
  forced: issueCodes({{ ...base, bodyFlow: {{ forcedLineBreaks: [{{ breakCount: 1 }}], nonWrappingProse: [] }} }}),
  nowrap: issueCodes({{ ...base, bodyFlow: {{ forcedLineBreaks: [], nonWrappingProse: [{{ whiteSpace: 'nowrap' }}] }} }}),
  cjk: issueCodes({{ ...base, bodyFlow: {{ forcedLineBreaks: [], nonWrappingProse: [] }}, headingFlow: {{ compressedCjkHeadings: [{{ lineCount: 5 }}] }} }}),
  orphan: issueCodes({{ ...base, bodyFlow: {{ forcedLineBreaks: [], nonWrappingProse: [] }}, headingFlow: {{ orphanedCjkHeadingLines: [{{ lineCount: 2, lastLineText: '策' }}] }} }}),
  reorder: issueCodes({{ ...base, bodyFlow: {{ forcedLineBreaks: [], nonWrappingProse: [] }}, layoutFlow: {{ domOrderReversals: [{{ upwardShift: 120 }}] }} }}),
}}));
"""
        result = self.run_node(source)
        self.assertIn("forced_body_line_break", result["forced"])
        self.assertIn("body_copy_normal_wrap_disabled", result["nowrap"])
        self.assertIn("cjk_heading_overcompressed", result["cjk"])
        self.assertIn("cjk_heading_orphan_line", result["orphan"])
        self.assertIn("visual_order_reverses_dom_flow", result["reorder"])

    def test_track_utilization_intro_alignment_and_locale_become_repair_codes(self) -> None:
        source = f"""
const {{ issueCodes }} = require({json.dumps(str(AUDITOR))});
const base = {{
  interaction: {{ failures: [] }}, contractIssues: [], lang: 'zh-Hant-TW', hasMain: true,
  visibleMainCount: 1, hasHeading: true, horizontalOverflow: false, outsideViewport: [],
  shortActionFailures: [], clippedText: [], criticalTextCollisions: [], fixedStickyObstructions: [],
  viewport: 'desktop', smallTouchTargets: [], readingRhythm: {{ tooTight: [], tooWide: [] }},
  narrowTextColumns: [], reducedMotionAnimations: [], consoleErrors: [], externalRequests: [], badResponses: [],
  bodyFlow: {{ forcedLineBreaks: [], nonWrappingProse: [], underfilledProseBlocks: [] }},
  headingFlow: {{ compressedCjkHeadings: [], orphanedCjkHeadingLines: [], underfilledWideHeadings: [] }},
  layoutFlow: {{ domOrderReversals: [], displacedIntroCopy: [] }},
  localeFlow: {{ untranslatedInterfaceCopy: [] }},
}};
process.stdout.write(JSON.stringify({{
  prose: issueCodes({{ ...base, bodyFlow: {{ ...base.bodyFlow, underfilledProseBlocks: [{{ ratio: 0.48 }}] }} }}),
  heading: issueCodes({{ ...base, headingFlow: {{ ...base.headingFlow, underfilledWideHeadings: [{{ ratio: 0.42 }}] }} }}),
  intro: issueCodes({{ ...base, layoutFlow: {{ ...base.layoutFlow, displacedIntroCopy: [{{ startRatio: 0.57 }}] }} }}),
  columnVoid: issueCodes({{ ...base, layoutFlow: {{ ...base.layoutFlow, unfilledColumnVoids: [{{ voidHeight: 936, threshold: 300 }}] }} }}),
  smallText: issueCodes({{ ...base, textScale: {{ undersizedReadableText: [{{ fontSize: 11 }}] }} }}),
  locale: issueCodes({{ ...base, localeFlow: {{ untranslatedInterfaceCopy: [{{ text: 'Current configuration' }}] }} }}),
  fontMismatch: issueCodes({{ ...base, fontEvidence: {{ status: 'captured', primaryMismatches: [{{ role: 'specimen' }}] }} }}),
  fontUnavailable: issueCodes({{ ...base, fontEvidence: {{ status: 'unavailable', error: 'active rendered-text animation prevented stable evidence' }} }}),
  fontUnavailableWithMismatch: issueCodes({{ ...base, fontEvidence: {{ status: 'unavailable', primaryMismatches: [{{ role: 'specimen' }}] }} }}),
}}));
"""
        result = self.run_node(source)
        self.assertIn("prose_track_underfilled", result["prose"])
        self.assertIn("wide_heading_track_underfilled", result["heading"])
        self.assertIn("intro_copy_displaced_to_right_track", result["intro"])
        self.assertIn("layout_column_void", result["columnVoid"])
        self.assertIn("readable_text_below_12px", result["smallText"])
        self.assertIn("zh_hant_untranslated_interface_copy", result["locale"])
        self.assertIn("declared_primary_font_not_rendered", result["fontMismatch"])
        self.assertIn("font_evidence_unavailable", result["fontUnavailable"])
        self.assertIn("font_evidence_unavailable", result["fontUnavailableWithMismatch"])
        self.assertNotIn("declared_primary_font_not_rendered", result["fontUnavailableWithMismatch"])

    def test_column_void_gate_requires_sparse_content_and_preserves_advisories(self) -> None:
        source = AUDITOR.read_text(encoding="utf-8")
        self.assertIn("const unfilledColumnAdvisories = [];", source)
        self.assertIn('confidence: "sparse-column"', source)
        self.assertIn('confidence: "dense-independent-column"', source)
        self.assertIn("const sparseContent = contentNodes.length <= 2", source)
        self.assertIn("unfilledColumnAdvisories", source)

    def test_locale_rule_keeps_terms_codes_and_names_but_rejects_raw_ui_copy(self) -> None:
        source = f"""
const {{ hasUnexplainedEnglish }} = require({json.dumps(str(AUDITOR))});
process.stdout.write(JSON.stringify({{
  explained: hasUnexplainedEnglish('等寬數字（tabular figures）格式'),
  dispatch: hasUnexplainedEnglish('TW-OFW-204 葉片前緣補片 · T-14'),
  namedAmount: hasUnexplainedEnglish('EchoWave NT$ 310,000'),
  untranslated: hasUnexplainedEnglish('開啟決策 modal'),
}}));
"""
        result = self.run_node(source)
        self.assertFalse(result["explained"])
        self.assertFalse(result["dispatch"])
        self.assertFalse(result["namedAmount"])
        self.assertTrue(result["untranslated"])


if __name__ == "__main__":
    unittest.main()
