#!/usr/bin/env python3
"""Regression tests for the proportional DESIGN.md decision-trace contract."""

from __future__ import annotations

import unittest
from pathlib import Path


REFERENCE = (
    Path(__file__).resolve().parents[1]
    / "wow-frontend-design"
    / "references"
    / "design-md-contract.md"
)
TEMPLATE = Path(__file__).resolve().parents[1] / "wow-frontend-design" / "assets" / "DESIGN.template.md"


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

    def test_route_local_work_does_not_create_system_governance(self) -> None:
        self.assertIn(
            "A route-local presentation change without an existing contract keeps its consumed roles in runtime code and the task handoff",
            self.reference,
        )
        self.assertIn("does not create `DESIGN.md`", self.reference)


class DesignMdTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.template = TEMPLATE.read_text(encoding="utf-8")
        cls.frontmatter = cls.template.split("---", 2)[1]

    def test_template_has_no_portable_visual_defaults(self) -> None:
        for token_group in ("colors:", "typography:", "rounded:", "spacing:", "components:"):
            with self.subTest(token_group=token_group):
                self.assertNotIn(token_group, self.frontmatter)
        for legacy_default in ("#1A1C1E", "#F7F5F2", "system-ui", "48px", "16px", "button-primary", "base-surface"):
            with self.subTest(legacy_default=legacy_default):
                self.assertNotIn(legacy_default, self.template)

    def test_optional_systems_allow_none_or_inherited(self) -> None:
        for heading in ("## Elevation & Depth", "## Shapes", "## Components"):
            section = self.template.split(heading, 1)[1].split("\n## ", 1)[0]
            with self.subTest(heading=heading):
                self.assertIn("`none`", section)
                self.assertIn("`inherited`", section)


if __name__ == "__main__":
    unittest.main()
