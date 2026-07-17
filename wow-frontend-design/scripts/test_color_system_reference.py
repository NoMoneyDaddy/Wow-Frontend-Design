#!/usr/bin/env python3
"""Regression tests for the product-specific color authorship contract."""

from __future__ import annotations

import unittest
from pathlib import Path


REFERENCE = (
    Path(__file__).resolve().parents[1]
    / "references"
    / "color-system-psychology.md"
)


class ColorSystemReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = REFERENCE.read_text(encoding="utf-8")

    def test_palette_thesis_is_product_derived_and_counterfactual(self) -> None:
        for signal in (
            "## Author a product-specific color structure, not a trend preset",
            "PRODUCT EVIDENCE:",
            "COLOR STRUCTURE:",
            "SPECIFICITY:",
            "Product-swap",
            "unrelated product",
        ):
            with self.subTest(signal=signal):
                self.assertIn(signal, self.reference)
        self.assertIn("composition lenses, not required layers", self.reference)
        self.assertIn("Do not require exploration for a repair", self.reference)

    def test_product_swap_does_not_randomize_shared_semantics(self) -> None:
        product_swap = self.reference.split("- **Product-swap:**", 1)[1].split("\n", 1)[0]
        self.assertIn("identity-bearing authorship", product_swap)
        self.assertIn("not access or status roles", product_swap)
        self.assertIn("preserve a shared convention or deliberate restraint", product_swap)

    def test_current_color_technology_is_not_aesthetic_proof(self) -> None:
        for signal in (
            "Current color spaces and functions expand implementation choices, not aesthetic proof.",
            "Do not require wide gamut",
            "Claim ceiling",
            "never conclusions from hue count, color distance, or a passing contrast tool",
        ):
            with self.subTest(signal=signal):
                self.assertIn(signal, self.reference)
        modern_css = self.reference.split("Modern CSS can express", 1)[1].split("\n", 1)[0]
        self.assertIn("CSS Color Module Level 4", modern_css)
        self.assertIn("defines `oklch()`", modern_css)
        self.assertIn("CSS Color Module Level 5 Working Draft", modern_css)
        self.assertIn("extends that foundation with `color-mix()`", modern_css)

    def test_palette_contract_does_not_require_numeric_novelty(self) -> None:
        section = self.reference.split(
            "## Author a product-specific color structure, not a trend preset", 1
        )[1].split("## Appearance is a composition", 1)[0]
        for forbidden in (
            "at least two hues",
            "at least three colors",
            "must use OKLCH",
            "must use wide gamut",
            "minimum color distance",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, section)

    def test_safe_fallback_is_not_a_finished_identity(self) -> None:
        self.assertIn(
            "neutrals plus one action color is a safe provisional baseline, not a finished identity",
            self.reference,
        )
        self.assertIn(
            "Missing psychological evidence lowers only the psychological claim",
            self.reference,
        )


if __name__ == "__main__":
    unittest.main()
