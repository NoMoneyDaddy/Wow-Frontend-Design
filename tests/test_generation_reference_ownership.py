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
        cls.motion = (ROOT / "motion-system.md").read_text(encoding="utf-8")
        cls.typography = (ROOT / "typographic-layout.md").read_text(encoding="utf-8")
        cls.skill = (ROOT.parent / "SKILL.md").read_text(encoding="utf-8")

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

    def test_repeated_record_actions_keep_unique_visible_semantics(self) -> None:
        phrase = "stable, human-readable identity"
        self.assertIn(phrase, self.components)
        self.assertIn("exactly one live control", self.components)

    def test_persistent_actions_name_the_current_transition(self) -> None:
        self.assertIn(
            "every action control that remains available must name the actual next or return outcome",
            self.components,
        )
        self.assertIn("Re-check every surviving action label against the current state", self.motion)

    def test_evaluator_hooks_do_not_replace_native_form_state(self) -> None:
        self.assertIn(
            "they never replace the native control or explicit state owner",
            self.components,
        )
        self.assertIn("hooks locate surfaces, not form values", self.skill)

    def test_visible_default_selection_matches_its_owned_state(self) -> None:
        self.assertIn(
            "A visible default selection must be the owning state",
            self.components,
        )

    def test_selection_dependent_actions_expose_unavailable_state(self) -> None:
        self.assertIn(
            "actions whose prerequisite selection is empty must expose an unavailable state",
            self.components,
        )

    def test_failure_states_require_a_reachable_recovery_action(self) -> None:
        self.assertIn(
            "visible enabled recovery/retry control that changes outcome",
            self.skill,
        )
        self.assertIn("a covering browser contract asserts it", self.skill)

    def test_vertical_slice_requires_bounded_builder_self_test(self) -> None:
        for phrase in (
            "Before expansion, pass the bounded self-test",
            "quality-gates.md",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.skill)
        for phrase in (
            "bounded builder self-test",
            "fresh project-pinned Playwright context",
            "early diagnostic, not acceptance evidence",
            "keep the affected claim `UNVERIFIED`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, (ROOT / "quality-gates.md").read_text(encoding="utf-8"))
        self.assertIn("Vibe Code Bench", self.research)
        self.assertIn("Pearson `r=0.72`", self.research)
        self.assertIn("benchmark itself lists those dimensions as out of scope", self.research)

    def test_quality_gates_require_semantic_html_validation(self) -> None:
        quality = (ROOT / "quality-gates.md").read_text(encoding="utf-8")
        for phrase in (
            "project-pinned semantic validator",
            "npm run audit:html -- <html-output>",
            "Pass only HTML paths",
            "REPAIR REQUIRED",
            "Playwright behavior and Axe results cannot substitute for valid HTML semantics",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, quality)

    def test_cjk_display_copy_preserves_semantic_wrap_units(self) -> None:
        for phrase in (
            "semantic wrap unit",
            "compact lexical unit",
            "never apply `word-break: keep-all` globally",
            "Verify the fallback at adjacent widths",
            "rerun the narrowest declared viewport",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.typography)

    def test_action_hooks_identify_their_own_live_control(self) -> None:
        self.assertIn(
            "action hook must identify the one live control that performs that action",
            self.components,
        )

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
        self.assertIn("run the pinned Axe check after the result assertion in that same replay", self.visual)
        self.assertIn("bounded Axe count/rule IDs", self.visual)
        self.assertIn("capture settled viewport slices in document order", self.visual)
        self.assertIn("bounded full-document composition evidence only", self.visual)
        self.assertIn("one clamped normalized value", (ROOT / "motion-system.md").read_text())
        patterns = (ROOT / "pattern-catalog.md").read_text()
        self.assertIn("included quantity, limits/overage, eligibility", patterns)
        self.assertIn("Product Demos, Samples, AI Workflow Proof", patterns)

    def test_task_screen_narrow_type_requires_a_parallel_earned_track(self) -> None:
        self.assertIn(
            "adjacent track carries a parallel decision, proof, or task context",
            self.creative,
        )

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
            "compare matched captures against only each candidate's declared changed axes",
            "An advisory records a review question, not a style verdict or release gate",
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

    def test_post_render_review_catches_structural_ai_slop_without_style_bans(self) -> None:
        for phrase in (
            "Text/container disagreement",
            "Decorative grid without a content model",
            "State reduced to ornament",
            "Viewport treated as a crop mask",
            "Surface vocabulary outruns product vocabulary",
            "diagnostic hypotheses, not a reverse style catalogue",
            "fresh evidence are explicit",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review)

    def test_post_render_review_names_the_four_panel_convergence_signals(self) -> None:
        for phrase in (
            "The supplied four-panel meme is a pattern collage",
            "Side-tab accent card",
            "Letter-spacing theatre",
            "Pill/status reflex",
            "Card shell repetition",
            "one font used everywhere",
            "motion without a task or state purpose",
            "current [Impeccable slop catalogue](https://impeccable.style/slop/)",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review)

    def test_post_render_review_tracks_mainstream_model_priors_without_banning_them(self) -> None:
        for phrase in (
            "Mainstream model-prior inventory",
            "centered headline, eyebrow, two CTAs",
            "three/four identical feature cards",
            "sidebar + top bar + dashboard cards",
            "Inter/Geist/Space Grotesk",
            "hover-scale imagery, pulsing status dot, auto marquee",
            "generic marketing cadence",
            "approved asset provenance",
            "The inventory is a review queue, not a style ban",
            "productive friction before implementation",
            "Interrogating Design Homogenization in Web Vibe Coding",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review)

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
