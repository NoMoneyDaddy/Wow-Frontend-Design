#!/usr/bin/env python3
"""Browser-backed regression tests for the v7-A1 typography gate."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
METRICS = ROOT / "evals" / "v7_a1_typography_metrics.cjs"
FIXTURE = ROOT / "evals" / "fixtures" / "v7-a1-typography.html"


class V7A1TypographyMetricsTests(unittest.TestCase):
    maxDiff = None

    SPECS = [
        {"id": "orphan", "selector": "#heading-orphan", "ownerSelector": "#owner-orphan", "role": "heading", "mode": "product"},
        {"id": "valid-line", "selector": "#heading-valid-line", "ownerSelector": "#owner-valid-line", "role": "heading", "mode": "product"},
        {"id": "display", "selector": "#heading-display", "ownerSelector": "#owner-display", "role": "heading", "mode": "display"},
        {"id": "vertical", "selector": "#heading-vertical", "ownerSelector": "#owner-vertical", "role": "heading", "mode": "product"},
        {"id": "title-59", "selector": "#title-59", "ownerSelector": "#owner-title-59", "role": "heading", "mode": "product"},
        {"id": "title-60", "selector": "#title-60", "ownerSelector": "#owner-title-60", "role": "heading", "mode": "product"},
        {"id": "balanced", "selector": "#title-balanced", "ownerSelector": "#owner-balanced", "role": "heading", "mode": "product"},
        {"id": "peer", "selector": "#title-peer", "ownerSelector": "#owner-peer", "peerSelector": "#task-peer", "role": "heading", "mode": "product"},
        {"id": "prose-void", "selector": "#prose-void", "ownerSelector": "#owner-prose", "role": "prose", "mode": "product"},
        {"id": "prose-narrow", "selector": "#prose-narrow", "ownerSelector": "#owner-prose-narrow", "role": "prose", "mode": "product"},
        {"id": "editorial", "selector": "#prose-editorial", "ownerSelector": "#owner-editorial", "role": "prose", "mode": "editorial"},
        {"id": "editorial-clean", "selector": "#prose-editorial-clean", "ownerSelector": "#owner-editorial-clean", "role": "prose", "mode": "editorial"},
        {"id": "gap-280", "selector": "#gap-280", "ownerSelector": "#owner-gap-280", "role": "heading", "mode": "product"},
        {"id": "gap-281", "selector": "#gap-281", "ownerSelector": "#owner-gap-281", "role": "heading", "mode": "product"},
        {"id": "control", "selector": "#control-heading", "ownerSelector": "#owner-control", "role": "heading", "mode": "product"},
        {"id": "ruby", "selector": "#ruby-heading", "ownerSelector": "#owner-ruby", "role": "heading", "mode": "product"},
    ]

    @classmethod
    def setUpClass(cls) -> None:
        source = """
const { chromium } = require("playwright");
const { auditV7A1Typography, validateSpecs } = require(process.argv[1]);
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
  await page.goto(new URL(`file://${process.argv[2]}`).href, { waitUntil: "load" });
  await page.evaluate(() => document.fonts.ready);
  const specs = validateSpecs(JSON.parse(process.argv[3]));
  const result = await page.evaluate(auditV7A1Typography, specs);
  await browser.close();
  process.stdout.write(JSON.stringify(result));
})().catch((error) => { console.error(error); process.exit(1); });
"""
        completed = subprocess.run(
            ["node", "-e", source, str(METRICS), str(FIXTURE), json.dumps(cls.SPECS)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr)
        cls.result = json.loads(completed.stdout)
        cls.codes = {(item["targetId"], item["code"]) for item in cls.result["issues"]}
        cls.targets = {item["id"]: item for item in cls.result["targets"]}
        cls.observations = {item["targetId"]: item for item in cls.result["observations"]}

    def test_single_han_with_terminal_punctuation_is_a_hard_issue(self) -> None:
        self.assertIn(("orphan", "a1_heading_han_orphan"), self.codes)
        self.assertEqual("核。", self.targets["orphan"]["lastLineText"])
        self.assertNotIn(("valid-line", "a1_heading_han_orphan"), self.codes)

    def test_display_and_vertical_intent_cannot_hard_fail(self) -> None:
        self.assertNotIn(("display", "a1_heading_han_orphan"), self.codes)
        self.assertEqual("display-intent", self.observations["display"]["reason"])
        self.assertNotIn(("vertical", "a1_heading_han_orphan"), self.codes)
        self.assertEqual("vertical-writing", self.observations["vertical"]["reason"])

    def test_track_ratio_boundary_is_strict(self) -> None:
        self.assertIn(("title-59", "a1_heading_track_void"), self.codes)
        self.assertNotIn(("title-60", "a1_heading_track_void"), self.codes)
        self.assertAlmostEqual(0.59, self.targets["title-59"]["trackRatio"], places=2)
        self.assertAlmostEqual(0.60, self.targets["title-60"]["trackRatio"], places=2)

    def test_full_track_rag_and_task_peer_are_valid(self) -> None:
        self.assertNotIn(("balanced", "a1_heading_track_void"), self.codes)
        self.assertNotIn(("peer", "a1_heading_track_void"), self.codes)
        self.assertTrue(self.targets["peer"]["hasTaskPeer"])

    def test_prose_owner_and_editorial_mode_prevent_false_blocks(self) -> None:
        self.assertIn(("prose-void", "a1_prose_track_void"), self.codes)
        self.assertNotIn(("prose-narrow", "a1_prose_track_void"), self.codes)
        self.assertNotIn(("editorial", "a1_prose_track_void"), self.codes)
        self.assertEqual("editorial-intent", self.observations["editorial"]["reason"])
        self.assertEqual("editorial-intent", self.observations["editorial-clean"]["reason"])
        self.assertEqual([], self.observations["editorial-clean"]["codes"])

    def test_inline_end_gap_boundary_is_strict(self) -> None:
        self.assertNotIn(("gap-280", "a1_heading_track_void"), self.codes)
        self.assertIn(("gap-281", "a1_heading_track_void"), self.codes)
        self.assertAlmostEqual(280, self.targets["gap-280"]["inlineEndGap"], delta=0.1)
        self.assertAlmostEqual(281, self.targets["gap-281"]["inlineEndGap"], delta=0.1)

    def test_control_and_ruby_annotation_are_excluded(self) -> None:
        self.assertEqual("interactive-control", self.observations["control"]["reason"])
        self.assertNotIn(("control", "a1_heading_han_orphan"), self.codes)
        self.assertEqual("驗證", self.targets["ruby"]["lastLineText"])
        self.assertNotIn(("ruby", "a1_heading_han_orphan"), self.codes)

    def test_fonts_are_ready_before_measurement(self) -> None:
        self.assertEqual("loaded", self.result["environment"]["fontsStatus"])

    def test_invalid_manifest_specs_fail_closed(self) -> None:
        source = f"""
const {{ validateSpecs }} = require({json.dumps(str(METRICS))});
try {{ validateSpecs([{{ id: 'bad', selector: '#x', ownerSelector: '#y', role: 'heading', mode: 'guessed' }}]); }}
catch (error) {{ process.stdout.write(error.message); process.exit(0); }}
process.exit(1);
"""
        completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, completed.returncode)
        self.assertIn("invalid mode", completed.stdout)


if __name__ == "__main__":
    unittest.main()
