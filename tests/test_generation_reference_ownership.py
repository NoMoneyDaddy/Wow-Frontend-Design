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
        cls.exploration = (ROOT / "design-exploration.md").read_text(encoding="utf-8")
        cls.discovery = (ROOT / "product-discovery-usability.md").read_text(encoding="utf-8")
        cls.tokens = (ROOT / "design-token-portability.md").read_text(encoding="utf-8")
        cls.visual = (ROOT / "visual-regression-evidence.md").read_text(encoding="utf-8")

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

    def test_thin_briefs_allow_one_reversible_authored_hypothesis(self) -> None:
        for phrase in (
            "one reversible authored hypothesis",
            "`HYPOTHESIS`, never as product fact",
            "identity carrier → expected task/content benefit → failure signal",
            "cheapest disconfirming check → replacement rule",
            "must not invent product facts, research, rights, assets, or user preference",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.creative)

    def test_direction_claims_stay_within_the_observable_comparison_set(self) -> None:
        for phrase in (
            "Name the observable comparison set",
            "do not claim cross-run novelty or difference from unseen generations",
            "Without a supplied baseline, cohort, or lineage",
            "trace the current choice to product evidence",
            "product-supported alternative inside the current decision",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.creative)

    def test_external_methods_are_distilled_into_bounded_mother_rules(self) -> None:
        for phrase in (
            "reference instance → rhythm | density | navigation | type | material | imagery | motion",
            "top user job → surface archetype → page thesis → protagonist",
            "a composition abstraction is earned only by repeated task roles",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.creative)
        self.assertIn("immutable baseline", self.exploration)
        self.assertIn("Every candidate records its parent and changed axes", self.exploration)
        self.assertIn("method → can answer → cannot answer", self.discovery)
        self.assertIn("Cross-channel journey evidence", self.discovery)
        self.assertIn("runtime/framework adapter consumes the resolved semantic", self.tokens)
        self.assertIn("fresh source-bound artifacts under neutral candidate IDs", self.visual)
        self.assertIn("rendered geometry/computed styles, and a stable semantic locator", self.visual)

    def test_exploration_supports_fast_multi_direction_style_calibration(self) -> None:
        for phrase in (
            "fast multi-direction draft pass",
            "coherent direction group, not a colorway or a single tile",
            "representative route at a declared desktop profile",
            "mobile transformation of that route",
            "one decision-critical state or interaction specimen",
            "Do not build three production implementations",
            "budget the vertical stack before styling",
            "brand, value statement, required decision context, and primary action",
            "Defer every non-required block below that action",
            "repeated summary cards displace it",
            "rendered candidate directions in the same frozen comparison cohort",
            "whether produced in one batch or isolated runs",
            "scripts/cross_output_template_audit.cjs",
            "matched surface, viewport, and state",
            "paired rendered review",
            "never make a match a release blocker or a non-match proof of originality",
            "Only a confirmed paired-render failure excludes a candidate",
            "replace it at most once when the explicit comparison count still matters",
            "present fewer honest directions",
            "stop the calibration instead of padding the set",
            "Run the full affected state and viewport matrix only for the selected direction",
            "fresh project-pinned Playwright captures",
            "selected style contract",
            "Author the schema-closed variant manifest from the frozen contract",
            "Do not ask the user to write evaluator JSON",
            "explicitly delegates selection",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.exploration)

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

    def test_fresh_screenshots_are_shown_when_the_host_can_render_them(self) -> None:
        for phrase in (
            "authorized for user-visible handoff",
            "privacy-bounded",
            "show the actual fresh screenshots",
            "do not make the user ask for them",
            "smallest representative set",
            "host-safe links or evaluator-root-relative artifact paths",
            "Do not expose private evaluator roots",
            "Never present a stale, prior, or reference capture as current evidence",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.research)
        self.assertNotIn("desktop/mobile pair", self.research)
        self.assertNotIn("provide exact artifact paths", self.research)


if __name__ == "__main__":
    unittest.main()
