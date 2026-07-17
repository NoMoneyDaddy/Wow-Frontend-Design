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
        {"id": "void-column", "selector": "#void-column-heading", "ownerSelector": "#void-column-owner", "role": "heading", "mode": "editorial"},
        {"id": "balanced-column", "selector": "#balanced-column-heading", "ownerSelector": "#balanced-column-owner", "role": "heading", "mode": "editorial"},
        {"id": "nested-column", "selector": "#nested-column-copy", "ownerSelector": "#nested-column-owner", "role": "prose", "mode": "editorial"},
        {"id": "clip-ellipsis", "selector": "#clip-ellipsis", "ownerSelector": "#owner-clip-ellipsis", "role": "heading", "mode": "product"},
        {"id": "clip-nowrap", "selector": "#clip-nowrap", "ownerSelector": "#owner-clip-nowrap", "role": "heading", "mode": "product"},
        {"id": "clip-clamp", "selector": "#clip-clamp", "ownerSelector": "#owner-clip-clamp", "role": "prose", "mode": "product"},
        {"id": "clip-block-hidden", "selector": "#clip-block-hidden", "ownerSelector": "#owner-clip-block-hidden", "role": "prose", "mode": "product"},
        {"id": "clip-block-clip", "selector": "#clip-block-clip", "ownerSelector": "#owner-clip-block-clip", "role": "prose", "mode": "product"},
        {"id": "clip-block-normal", "selector": "#clip-block-normal", "ownerSelector": "#owner-clip-block-normal", "role": "prose", "mode": "product"},
        {"id": "clip-fit", "selector": "#clip-fit", "ownerSelector": "#owner-clip-fit", "role": "heading", "mode": "product"},
        {"id": "clip-tolerance", "selector": "#clip-tolerance", "ownerSelector": "#owner-clip-tolerance", "role": "heading", "mode": "product"},
        {"id": "clip-axis-priority", "selector": "#clip-axis-priority", "ownerSelector": "#owner-clip-axis-priority", "role": "prose", "mode": "product"},
        {"id": "clip-mixed-axis", "selector": "#clip-mixed-axis", "ownerSelector": "#owner-clip-mixed-axis", "role": "prose", "mode": "product"},
        {"id": "scroll-accessible", "selector": "#scroll-accessible", "ownerSelector": "#owner-scroll-accessible", "role": "prose", "mode": "product"},
        {"id": "scroll-advisory", "selector": "#scroll-advisory", "ownerSelector": "#owner-scroll-advisory", "role": "prose", "mode": "product"},
        {"id": "clip-editorial", "selector": "#clip-editorial", "ownerSelector": "#owner-clip-editorial", "role": "prose", "mode": "editorial"},
        {"id": "clip-display", "selector": "#clip-display", "ownerSelector": "#owner-clip-display", "role": "heading", "mode": "display"},
        {"id": "clip-transform", "selector": "#clip-transform", "ownerSelector": "#owner-clip-transform", "role": "heading", "mode": "product"},
        {"id": "clip-pseudo", "selector": "#clip-pseudo", "ownerSelector": "#owner-clip-pseudo", "role": "heading", "mode": "product"},
        {"id": "clip-path", "selector": "#clip-path", "ownerSelector": "#owner-clip-path", "role": "heading", "mode": "product"},
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

    def test_large_unfilled_side_by_side_column_is_a_hard_layout_issue(self) -> None:
        self.assertIn(("void-column", "a1_layout_column_void"), self.codes)
        self.assertGreater(self.targets["void-column"]["columnVoid"]["voidHeight"], 600)
        self.assertNotIn(("balanced-column", "a1_layout_column_void"), self.codes)
        self.assertIsNone(self.targets["balanced-column"]["columnVoid"])
        self.assertIn(("nested-column", "a1_layout_column_void"), self.codes)
        self.assertEqual("target", self.targets["nested-column"]["columnVoid"]["source"])

    def test_fonts_are_ready_before_measurement(self) -> None:
        self.assertEqual("loaded", self.result["environment"]["fontsStatus"])

    def test_direct_required_text_clipping_requires_delta_and_range_evidence(self) -> None:
        expected = {
            "clip-ellipsis": "inline_ellipsis",
            "clip-nowrap": "inline_clip",
            "clip-clamp": "line_clamp",
            "clip-block-hidden": "block_clip",
            "clip-block-clip": "block_clip",
            "clip-axis-priority": "block_clip",
            "clip-mixed-axis": "block_clip",
        }
        for target_id, mechanism in expected.items():
            with self.subTest(target_id=target_id):
                completeness = self.targets[target_id]["textCompleteness"]
                self.assertIn((target_id, "a1_required_text_clipped"), self.codes)
                self.assertEqual("clipped", completeness["status"])
                self.assertEqual(mechanism, completeness["mechanism"])
                self.assertGreater(completeness["outsideRectCount"], 0)
        self.assertEqual(2, self.targets["clip-ellipsis"]["textCompleteness"]["tolerance"])
        self.assertEqual(2, self.targets["clip-clamp"]["textCompleteness"]["tolerance"])
        self.assertLessEqual(
            self.targets["clip-axis-priority"]["textCompleteness"]["inlineDelta"],
            self.targets["clip-axis-priority"]["textCompleteness"]["tolerance"],
        )
        mixed = self.targets["clip-mixed-axis"]["textCompleteness"]
        self.assertLessEqual(mixed["inlineDelta"], mixed["tolerance"])
        self.assertGreater(mixed["blockDelta"], mixed["tolerance"])
        normal_block = self.targets["clip-block-normal"]["textCompleteness"]
        self.assertEqual("unavailable", normal_block["status"])
        self.assertEqual("line_height_unavailable", normal_block["reason"])
        self.assertNotIn(("clip-block-normal", "a1_required_text_clipped"), self.codes)

    def test_fitting_and_sub_tolerance_content_remain_clean(self) -> None:
        for target_id in ("clip-fit", "clip-tolerance"):
            with self.subTest(target_id=target_id):
                self.assertNotIn((target_id, "a1_required_text_clipped"), self.codes)
                self.assertEqual("complete", self.targets[target_id]["textCompleteness"]["status"])
        tolerance = self.targets["clip-tolerance"]["textCompleteness"]
        self.assertGreater(tolerance["inlineDelta"], 0)
        self.assertLessEqual(tolerance["inlineDelta"], tolerance["tolerance"])

    def test_scroll_regions_are_never_promoted_to_hard_clipping(self) -> None:
        accessible = self.targets["scroll-accessible"]["textCompleteness"]
        advisory = self.targets["scroll-advisory"]["textCompleteness"]
        self.assertEqual("accessible_scroll", accessible["status"])
        self.assertEqual("named_focusable_scroll_region", accessible["reason"])
        self.assertEqual("advisory", advisory["status"])
        self.assertEqual("scroll_region_not_accessibly_exposed", advisory["reason"])
        self.assertNotIn(("scroll-accessible", "a1_required_text_clipped"), self.codes)
        self.assertNotIn(("scroll-advisory", "a1_required_text_clipped"), self.codes)

    def test_non_product_and_complex_geometry_fail_closed(self) -> None:
        self.assertEqual("not_applicable", self.targets["clip-editorial"]["textCompleteness"]["status"])
        self.assertEqual("not_applicable", self.targets["clip-display"]["textCompleteness"]["status"])
        expected = {
            "clip-transform": "transformed_target",
            "clip-pseudo": "pseudo_content_present",
            "clip-path": "complex_clip_or_filter",
        }
        for target_id, reason in expected.items():
            with self.subTest(target_id=target_id):
                completeness = self.targets[target_id]["textCompleteness"]
                self.assertEqual("unavailable", completeness["status"])
                self.assertEqual(reason, completeness["reason"])
                self.assertNotIn((target_id, "a1_required_text_clipped"), self.codes)

    def test_text_completeness_does_not_emit_product_text_or_selectors(self) -> None:
        serialized = json.dumps(
            {target_id: target["textCompleteness"] for target_id, target in self.targets.items()},
            ensure_ascii=False,
        )
        self.assertNotIn("必要標題資訊", serialized)
        self.assertNotIn("#clip-ellipsis", serialized)
        self.assertNotIn("selector", serialized.lower())

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
