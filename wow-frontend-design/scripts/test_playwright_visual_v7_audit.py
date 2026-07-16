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
        )
        if completed.returncode != 0:
            self.fail(completed.stderr)
        return json.loads(completed.stdout)

    def test_inventory_produces_sixty_four_screenshots(self) -> None:
        source = f"""
const {{ CASE_PAGES, VIEWPORTS }} = require({json.dumps(str(AUDITOR))});
const base = Object.values(CASE_PAGES).reduce((sum, pages) => sum + pages.length * VIEWPORTS.length, 0);
const interaction = Object.keys(CASE_PAGES).length * 2;
process.stdout.write(JSON.stringify({{
  cases: Object.keys(CASE_PAGES).length,
  routes: Object.values(CASE_PAGES).flat().length,
  profiles: VIEWPORTS.map((viewport) => viewport.name),
  total: base + interaction,
}}));
"""
        result = self.run_node(source)
        self.assertEqual(8, result["cases"])
        self.assertEqual(12, result["routes"])
        self.assertEqual(
            ["desktop", "tablet", "mobile", "compact-mobile"],
            result["profiles"],
        )
        self.assertEqual(64, result["total"])

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
}}));
"""
        result = self.run_node(source)
        self.assertIn("prose_track_underfilled", result["prose"])
        self.assertIn("wide_heading_track_underfilled", result["heading"])
        self.assertIn("intro_copy_displaced_to_right_track", result["intro"])
        self.assertIn("layout_column_void", result["columnVoid"])
        self.assertIn("readable_text_below_12px", result["smallText"])
        self.assertIn("zh_hant_untranslated_interface_copy", result["locale"])

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
