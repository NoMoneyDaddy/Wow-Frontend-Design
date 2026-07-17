#!/usr/bin/env python3
"""Regression tests for the proportional DESIGN.md decision-trace contract."""

from __future__ import annotations

import unittest
from pathlib import Path


REFERENCE = (
    Path(__file__).resolve().parents[1]
    / "references"
    / "design-md-contract.md"
)


class DesignMdReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = REFERENCE.read_text(encoding="utf-8")
        cls.trace = cls.reference.split(
            "## Persist material decision traces without a new DSL", 1
        )[1].split("## Required shape", 1)[0]

    def test_trace_binds_decision_source_surface_and_validation(self) -> None:
        for signal in (
            "exact requirement/evidence locator",
            "explicit/observed/inferred/unknown",
            "affected token/component/route/state",
            "validation evidence or UNVERIFIED",
            "preserve `unknown` instead of inventing provenance",
        ):
            with self.subTest(signal=signal):
                self.assertIn(signal, self.trace)

    def test_trace_is_conditional_and_proportional(self) -> None:
        for signal in (
            "When implementation creates or changes a material visual-system decision",
            "no minimum row count, fixed identifier scheme, new section, or separate trace file is required",
            "an inherited convention needs no entry",
            "a focused repair records only the affected system decision",
        ):
            with self.subTest(signal=signal):
                self.assertIn(signal, self.trace)

    def test_trace_does_not_replace_other_owners_or_prove_quality(self) -> None:
        self.assertIn("site/wireframe plan, interaction manifest, and tests", self.trace)
        self.assertIn("does not prove implementation, browser behavior, accessibility, product fit, or aesthetic quality", self.trace)
        self.assertIn("The pinned DESIGN.md linter validates supported syntax; it does not validate trace truth", self.trace)


if __name__ == "__main__":
    unittest.main()
