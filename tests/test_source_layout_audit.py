#!/usr/bin/env python3
"""Tests for source_layout_audit.py."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wow-frontend-design" / "scripts"))

import source_layout_audit


class SourceLayoutAuditTests(unittest.TestCase):
    def test_detects_bounded_source_risks_with_locations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text(
                """<style>
body { word-break: break-all; }
p.copy { white-space: nowrap; }
h1 { max-inline-size: 12ch; }
p.clipped { height: 40px; overflow: hidden; }
</style>
<p>這是一般正文<br>不應由來源碼控制斷行。</p>
""",
                encoding="utf-8",
            )
            report = source_layout_audit.audit(root)

        codes = {item["code"] for item in report["findings"]}
        self.assertEqual(
            {
                "fixed_text_clipping",
                "forced_body_break",
                "global_emergency_breaking",
                "heading_latin_ch_measure",
                "prose_wrap_disabled",
            },
            codes,
        )
        self.assertTrue(all(item["path"] == "index.html" and item["line"] >= 1 for item in report["findings"]))
        self.assertIn("rendered layout requires browser", report["claim_boundary"])

    def test_nearby_valid_patterns_remain_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "styles.css").write_text(
                """.tag { white-space: nowrap; }
.data { overflow-wrap: anywhere; }
h1 { max-inline-size: 18rem; }
.card { min-height: 20rem; overflow: visible; }
""",
                encoding="utf-8",
            )
            (root / "index.html").write_text(
                '<p class="poem">第一行<br>第二行</p>', encoding="utf-8"
            )

            report = source_layout_audit.audit(root)

        self.assertEqual("no_source_risks_observed", report["status"])
        self.assertEqual([], report["findings"])

    def test_cli_can_fail_only_on_high_confidence_findings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "styles.css").write_text("h1 { width: 10ch; }", encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                medium_status = source_layout_audit.main([
                    str(root), "--authorized-root", str(root), "--fail-on", "high",
                ])
            self.assertEqual(0, medium_status)
            self.assertEqual(1, json.loads(output.getvalue())["finding_count"])

            (root / "styles.css").write_text("p { white-space: nowrap; }", encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                high_status = source_layout_audit.main([
                    str(root), "--authorized-root", str(root), "--fail-on", "high",
                ])
            self.assertEqual(1, high_status)

    @unittest.skipUnless(
        source_layout_audit.project_scan.DESCRIPTOR_ANCHORING_AVAILABLE,
        "requires descriptor-relative project I/O",
    )
    def test_audit_does_not_follow_directory_replaced_after_collection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "project"
            styles = root / "styles"
            outside_styles = base / "outside" / "styles"
            styles.mkdir(parents=True)
            outside_styles.mkdir(parents=True)
            (styles / "site.css").write_text("p { color: inherit; }", encoding="utf-8")
            (outside_styles / "site.css").write_text(
                "p { white-space: nowrap; }", encoding="utf-8"
            )
            original_collect = source_layout_audit.project_scan.ProjectTree.collect_files

            def collect_then_swap(tree, *args, **kwargs):
                result = original_collect(tree, *args, **kwargs)
                styles.rename(root / "styles-original")
                styles.symlink_to(outside_styles, target_is_directory=True)
                return result

            with mock.patch.object(
                source_layout_audit.project_scan.ProjectTree,
                "collect_files",
                autospec=True,
                side_effect=collect_then_swap,
            ):
                report = source_layout_audit.audit(root)

        self.assertEqual([], report["findings"])
        self.assertEqual(0, report["scanned_files"])
        self.assertGreaterEqual(report["unsafe_entries_skipped"], 1)
        self.assertEqual("descriptor_anchored", report["io_protection"])


if __name__ == "__main__":
    unittest.main()
