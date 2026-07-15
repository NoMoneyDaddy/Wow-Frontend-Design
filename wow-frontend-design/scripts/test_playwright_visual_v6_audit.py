#!/usr/bin/env python3
"""Regression tests for the v6 multi-profile visual auditor."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDITOR = ROOT / "evals" / "playwright_visual_v6_audit.cjs"


class PlaywrightVisualV6AuditTests(unittest.TestCase):
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

    def test_traditional_chinese_language_variants_are_accepted(self) -> None:
        source = f"""
const {{ issueCodes }} = require({json.dumps(str(AUDITOR))});
const base = {{
  interaction: {{ failures: [] }}, contractIssues: [], hasMain: true, visibleMainCount: 1,
  hasHeading: true, horizontalOverflow: false, outsideViewport: [], shortActionFailures: [],
  clippedText: [], criticalTextCollisions: [], fixedStickyObstructions: [], viewport: 'mobile',
  smallTouchTargets: [], readingRhythm: {{ tooTight: [], tooWide: [] }}, narrowTextColumns: [],
  bodyFlow: {{ forcedLineBreaks: [], nonWrappingProse: [] }},
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
}};
process.stdout.write(JSON.stringify({{
  forced: issueCodes({{ ...base, bodyFlow: {{ forcedLineBreaks: [{{ breakCount: 1 }}], nonWrappingProse: [] }} }}),
  nowrap: issueCodes({{ ...base, bodyFlow: {{ forcedLineBreaks: [], nonWrappingProse: [{{ whiteSpace: 'nowrap' }}] }} }}),
}}));
"""
        result = self.run_node(source)
        self.assertIn("forced_body_line_break", result["forced"])
        self.assertIn("body_copy_normal_wrap_disabled", result["nowrap"])


if __name__ == "__main__":
    unittest.main()
