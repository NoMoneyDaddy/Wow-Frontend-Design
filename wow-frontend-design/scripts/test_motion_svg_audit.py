#!/usr/bin/env python3
"""Tests for motion_svg_audit.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import motion_svg_audit


class MotionSvgAuditTests(unittest.TestCase):
    def write(self, root: Path, name: str, content: str) -> None:
        (root / name).write_text(content, encoding="utf-8")

    def rules(self, root: Path) -> set[str]:
        findings, _ = motion_svg_audit.audit(root)
        return {item.rule for item in findings}

    def test_clean_motion_and_svg_have_no_high_findings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "index.html",
                '<button aria-label="搜尋"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M0 0"/></svg></button>',
            )
            self.write(
                root,
                "styles.css",
                ".button { transition: opacity 180ms ease; }\n"
                "@media (prefers-reduced-motion: reduce) { .button { transition: none; } }",
            )
            findings, count = motion_svg_audit.audit(root)
            self.assertEqual(count, 2)
            self.assertFalse(any(item.severity == "high" for item in findings))

    def test_motion_without_reduced_path_and_transition_all_are_found(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "styles.css", ".card { transition: all 300ms; animation: pulse 2s infinite; }")
            rules = self.rules(root)
            self.assertIn("MOTION001", rules)
            self.assertIn("MOTION002", rules)
            self.assertIn("MOTION003", rules)

    def test_comment_cannot_fake_reduced_motion_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "styles.css",
                "/* @media (prefers-reduced-motion: reduce) {} */\n.card { animation: pulse 1s; }",
            )

            self.assertIn("MOTION001", self.rules(root))

    def test_javascript_runtime_requires_runtime_preference_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "app.js",
                "requestAnimationFrame(tick);",
            )
            self.write(
                root,
                "styles.css",
                "@media (prefers-reduced-motion: reduce) { * { animation: none; } }",
            )

            self.assertIn("MOTION007", self.rules(root))

    def test_arbitrary_raf_callback_and_empty_reduced_query_do_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "app.js", "requestAnimationFrame(updateScene);")
            self.write(root, "styles.css", "@media (prefers-reduced-motion: reduce) {}")

            rules = self.rules(root)
            self.assertIn("MOTION001", rules)
            self.assertIn("MOTION007", rules)

    def test_large_file_reports_incomplete_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "large.css", " " * (motion_svg_audit.MAX_FILE_BYTES + 1))

            self.assertIn("AUDIT001", self.rules(root))

    def test_semantic_and_unsafe_svg_failures_are_found(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "unsafe.html",
                '<svg role="img"><script>alert(1)</script><foreignObject>bad</foreignObject>'
                '<path id="shape" onload="bad()"/><path id="shape"/></svg>',
            )
            rules = self.rules(root)
            self.assertIn("SVG001", rules)
            self.assertIn("SVG002", rules)
            self.assertIn("SVG004", rules)
            self.assertIn("SVG005", rules)

    def test_data_id_is_not_treated_as_html_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "index.html",
                '<button data-id="item-1">收藏</button><span data-id="item-1">0</span>',
            )
            self.write(
                root,
                "app.js",
                'document.querySelector(`[data-id="${id}"]`);',
            )

            self.assertNotIn("SVG005", self.rules(root))

    def test_svg_img_alt_and_active_document_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "index.html", '<img src="chart.svg"><object data="upload.svg"></object>')
            rules = self.rules(root)
            self.assertIn("SVG006", rules)
            self.assertIn("SVG008", rules)

    def test_protocol_relative_svg_asset_is_not_blankened_as_a_comment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "unsafe.html",
                '<svg viewBox="0 0 10 10"><image href="//evil.example/image.png"/></svg>',
            )

            self.assertIn("SVG004", self.rules(root))

    def test_symlink_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            target = base / "target"
            target.mkdir()
            link = base / "link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(motion_svg_audit.AuditError):
                motion_svg_audit.audit(link)


if __name__ == "__main__":
    unittest.main()
