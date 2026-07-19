#!/usr/bin/env python3
"""Keep generation references small and single-purpose."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "wow-frontend-design" / "references"


class GenerationReferenceOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.creative = (ROOT / "creative-direction.md").read_text(encoding="utf-8")
        cls.components = (ROOT / "component-composition.md").read_text(encoding="utf-8")
        cls.review = (ROOT / "anti-ai-slop.md").read_text(encoding="utf-8")
        cls.behavioral = (ROOT / "behavioral-design-evidence.md").read_text(encoding="utf-8")
        cls.weak = (ROOT / "weak-model-playbook.md").read_text(encoding="utf-8")
        cls.research = (ROOT / "research-validation-loop.md").read_text(encoding="utf-8")

    def test_references_keep_bounded_responsibility_sections(self) -> None:
        for heading in (
            "## 1. Freeze product evidence",
            "## 2. Form the direction",
            "## 4. Create, preserve, improve, or omit authored identity",
            "## 5. Prove the direction in a runnable slice",
        ):
            self.assertIn(heading, self.creative)
        for heading in (
            "## 2. Choose representation from product evidence",
            "## 3. Freeze the behavior contract",
            "## 5. Keep one identity across desktop and mobile",
            "## 6. Verify the component-specific contract",
        ):
            self.assertIn(heading, self.components)
        self.assertIn("# Product-specific post-render review", self.review)

    def test_creative_direction_has_no_style_catalogue_or_numeric_taste_score(self) -> None:
        for stale_section in (
            "## 4. Define the visual grammar",
            "## 5. Compose with hierarchy",
            "## 7. Avoid convergence",
        ):
            with self.subTest(stale_section=stale_section):
                self.assertNotIn(stale_section, self.creative)

    def test_attention_dominant_grammar_requires_evidence_without_novelty_pressure(self) -> None:
        for phrase in (
            "attention-dominant display-type category, major-surface shape, and repeated control silhouette",
            "A subject noun, mood, or claim of polish is not evidence",
            "inherit a proven project rule or leave it unresolved",
            "not a requirement to make these choices unusual or different",
            "attention-dominant grammar jobs or unresolved choices",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.creative)

    def test_component_reference_owns_behavior_not_visual_or_agent_orchestration(self) -> None:
        for stale_section in (
            "## 6. Build material and surface hierarchy",
            "## 8. Weak-model assembly rules",
        ):
            with self.subTest(stale_section=stale_section):
                self.assertNotIn(stale_section, self.components)
        self.assertIn("[interaction-audit.md](interaction-audit.md)", self.components)
        self.assertIn("[frontend-security.md](frontend-security.md)", self.components)

    def test_post_render_review_does_not_become_an_inverse_style_recipe(self) -> None:
        for stale_section in (
            "## Seven failure classes",
            "## Weak-model repair order",
            "### Optional cross-output convergence telemetry",
        ):
            with self.subTest(stale_section=stale_section):
                self.assertNotIn(stale_section, self.review)
        for gate in ("**Truth**", "**Product swap**", "**Earned region**", "**Evidence ceiling**"):
            with self.subTest(gate=gate):
                self.assertIn(gate, self.review)

    def test_consumers_route_to_the_new_canonical_owners(self) -> None:
        self.assertIn("[component-composition.md](component-composition.md)", self.behavioral)
        self.assertIn("post-render product-swap and earned-region review", self.behavioral)
        self.assertNotIn("fixed order from [anti-ai-slop.md]", self.weak)
        self.assertIn("Repair confirmed findings by dependency and ownership", self.weak)
        self.assertIn("[creative-direction.md](creative-direction.md)", self.weak)
        self.assertIn("[component-composition.md](component-composition.md)", self.weak)
        self.assertNotIn("## 3. Derive a grammar", self.weak)
        for heading in (
            "### Editorial narrative",
            "### Precision instrument",
            "### Material craft",
            "### Archive and index",
            "### Kinetic type",
            "### Spatial exhibition",
        ):
            self.assertNotIn(heading, self.weak)
        self.assertIn("scripts/cross_output_template_audit.cjs", self.research)
        self.assertIn("evaluator-only advisory telemetry", self.research)


if __name__ == "__main__":
    unittest.main()
