#!/usr/bin/env python3
"""Regression tests for task-safe typographic composition guidance."""

from __future__ import annotations

import unittest
from pathlib import Path


REFERENCE = (
    Path(__file__).resolve().parents[1]
    / "references"
    / "typographic-layout.md"
)


class TypographicLayoutReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = REFERENCE.read_text(encoding="utf-8")

    def test_void_repair_preserves_complete_product_flow(self) -> None:
        checkpoint = self.reference.split(
            "### A1 checkpoint: make every wide column earn its occupied area", 1
        )[1].split("## 2.", 1)[0]
        for signal in (
            "Preserve task completeness while repairing composition",
            "required comparison evidence",
            "current selection/status",
            "validation feedback",
            "primary actions",
            "resulting summary",
            "complete default-to-result flow",
        ):
            with self.subTest(signal=signal):
                self.assertIn(signal, checkpoint)

    def test_vertical_recipe_uses_the_correct_logical_axis(self) -> None:
        vertical = self.reference.split("## 4. Build real vertical writing", 1)[1]
        for signal in (
            "inline-size: fit-content",
            "max-inline-size: min(var(--verified-column-length, 28em), 70dvh)",
            "align-self: start",
            "the inline axis is physical height",
            "the block axis is physical width",
            "A `max-width` cap only constrains the vertical box's block axis",
            "grid stretch",
            "`min-height: 100%`",
            "an unrelated peer's height",
            "move the note below the article",
            "Never clip, mask, or scroll away required text",
        ):
            with self.subTest(signal=signal):
                self.assertIn(signal, vertical)

    def test_vertical_viewport_value_is_not_a_universal_preset(self) -> None:
        self.assertIn(
            "The `28em` fallback and `70dvh` cap above are candidates to compare, not universal limits",
            self.reference,
        )


if __name__ == "__main__":
    unittest.main()
