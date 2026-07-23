#!/usr/bin/env python3
"""Regression checks for the generation-first Skill core."""

from __future__ import annotations

import unittest
import re
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "wow-frontend-design" / "SKILL.md"
NO_VISUAL = SKILL.parent / "references" / "no-visual-first-pass.md"
QUALITY_GATES = SKILL.parent / "references" / "quality-gates.md"
MODEL_ROUTING = SKILL.parent / "references" / "model-routing.md"
COMPACT = SKILL.parent / "adapters" / "prompt-only-compact.md"
MATERIAL = SKILL.parent / "references" / "visual-material-system.md"
SVG_SYSTEM = SKILL.parent / "references" / "svg-system.md"
IMPLEMENTATION = SKILL.parent / "references" / "implementation.md"


class SkillCoreContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = SKILL.read_bytes()
        cls.text = cls.raw.decode("utf-8")

    def test_core_stays_within_progressive_disclosure_budget(self) -> None:
        self.assertLessEqual(len(self.raw), 19_800)
        for phrase in (
            "Initial reference bundle",
            "one dominant task reference",
            "A run may load more references over time",
            "at most three non-core references in one model turn",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_initial_reference_bundle_is_lane_specific(self) -> None:
        routing = self.text.split("## Route references progressively", 1)[1].split(
            "## Choose the operating lane", 1
        )[0]
        for phrase in (
            "`BUILD`, broad `RETROFIT`, or an explicitly unresolved direction",
            "`POLISH`, `REPAIR`, and `AUDIT` do not load creative direction by default",
            "Load [no-visual-first-pass.md](references/no-visual-first-pass.md) only when rendering is unavailable",
            "one dominant task reference only for a concrete decision",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, routing)
        self.assertNotIn("this core plus [creative-direction.md]", routing)

    def test_reference_lifecycle_has_one_owner(self) -> None:
        routing = MODEL_ROUTING.read_text(encoding="utf-8")
        self.assertIn("inherits the canonical reference lifecycle from `SKILL.md`", routing)
        self.assertIn("controlled external-evaluator cohort", self.text)
        self.assertIn("builder reference context stays frozen", self.text)
        self.assertNotIn("up to three when the task genuinely crosses domains", routing)
        self.assertNotIn("always-relevant creative/mobile/locale references", routing)

    def test_repair_budget_is_global_and_adapters_cannot_extend_it(self) -> None:
        compact = COMPACT.read_text(encoding="utf-8")
        quality = QUALITY_GATES.read_text(encoding="utf-8")
        for text in (self.text, compact, quality):
            self.assertIn("three total mutation attempts", text)
            self.assertIn("same-key fuse", text)
            self.assertIn("never extends", text)
        self.assertNotIn("After three consecutive failures", compact)

    def test_completion_uses_declared_affected_matrix_not_fixed_viewports(self) -> None:
        pressure = self.text.split("### 6. Pressure, repair, and replay", 1)[1].split(
            "## Implementation invariants", 1
        )[0]
        for phrase in (
            "declared affected matrix",
            "only when in scope",
            "unresolved confirmed",
            "frozen evaluator policy",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, pressure)
        self.assertNotIn("fresh desktop/mobile Playwright contexts", pressure)
        self.assertNotIn("zero runtime, egress, root-overflow, or Axe findings", pressure)

    def test_completion_routes_fresh_screenshots_to_the_user(self) -> None:
        for phrase in (
            "contract deltas",
            "check results",
            "authorized, privacy-bounded fresh screenshots",
            "when host-supported",
            "else host-safe links",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_project_verification_does_not_inherit_controlled_eval_overhead(self) -> None:
        quality = QUALITY_GATES.read_text(encoding="utf-8")
        for phrase in (
            "`PROJECT_VERIFICATION`",
            "`CONTROLLED_EVAL`",
            "catalogue, not a mandatory checklist",
            "review lenses, not three browser or capture passes",
            "Reuse one fresh evidence set",
            "Only `CONTROLLED_EVAL` requires evaluator-owned",
            "In `CONTROLLED_EVAL`, a completion claim binds `novel-discovery`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, quality)
        self.assertNotIn("| Route/state | 320 | 390 | 768 | 1024 | 1440 |", quality)
        self.assertIn("controlled external-evaluator cohort (`CONTROLLED_EVAL`)", self.text)
        self.assertIn("run the discovery probe", self.text)
        self.assertIn("In a controlled cohort, acceptance remains evaluator-owned.", self.text)

    def test_convergence_review_does_not_create_an_inverse_house_style(self) -> None:
        quality = QUALITY_GATES.read_text(encoding="utf-8")
        self.assertIn(
            "A repeated generic pattern becomes a finding only when product evidence supports a more specific alternative",
            quality,
        )
        self.assertNotIn("the page does not converge on generic card-grid SaaS output", quality)

    def test_fixed_viewports_are_only_a_fallback_when_support_is_unknown(self) -> None:
        compact = COMPACT.read_text(encoding="utf-8")
        no_visual = NO_VISUAL.read_text(encoding="utf-8")
        weak = (SKILL.parent / "references" / "weak-model-playbook.md").read_text(
            encoding="utf-8"
        )
        quality = QUALITY_GATES.read_text(encoding="utf-8")
        design_md = (SKILL.parent / "references" / "design-md-contract.md").read_text(
            encoding="utf-8"
        )
        material = MATERIAL.read_text(encoding="utf-8")
        typography = (SKILL.parent / "references" / "typographic-layout.md").read_text(
            encoding="utf-8"
        )
        webfonts = (SKILL.parent / "references" / "typography-webfonts.md").read_text(
            encoding="utf-8"
        )
        exploration = (SKILL.parent / "references" / "design-exploration.md").read_text(
            encoding="utf-8"
        )
        patterns = (SKILL.parent / "references" / "pattern-catalog.md").read_text(
            encoding="utf-8"
        )
        storytelling = (SKILL.parent / "references" / "visual-storytelling.md").read_text(
            encoding="utf-8"
        )
        award = (SKILL.parent / "references" / "award-quality-lens.md").read_text(
            encoding="utf-8"
        )
        for text in (compact, no_visual, weak):
            self.assertIn("when no support matrix is declared", text.lower())
        for text in (
            quality, design_md, material, typography, webfonts,
            exploration, patterns, storytelling, award,
        ):
            self.assertIn("declared representative viewport", text)
        self.assertIn("affected viewport profiles", quality)
        self.assertNotIn("one representative desktop and one true mobile", quality)
        self.assertNotIn("representative routes at mobile and desktop widths", quality)
        self.assertNotIn("every changed route at one representative mobile and desktop viewport", quality)
        self.assertNotIn("Design at 320/390 CSS px", compact)

    def test_compact_adapter_is_a_projection_not_a_second_standard(self) -> None:
        compact = COMPACT.read_text(encoding="utf-8")
        self.assertIn("compressed projection of the canonical core", compact)
        self.assertIn("Rejection is optional", compact)
        self.assertIn("Create only token roles consumed by the implementation", compact)
        self.assertIn("`none`, `inherited`, or `unknown`", compact)

    def test_material_and_svg_rules_share_one_asset_boundary(self) -> None:
        material = MATERIAL.read_text(encoding="utf-8")
        svg = SVG_SYSTEM.read_text(encoding="utf-8")
        self.assertIn("authorized original non-factual SVG", material)
        self.assertIn("provenance, accessibility, sanitization, fallback", material)
        self.assertIn("Do not fake factual, product, brand, evidence, or standard semantic assets", material)
        self.assertIn("authorized original non-factual", svg)

    def test_generation_first_stages_keep_their_order(self) -> None:
        headings = (
            "### 1. Evidence freeze",
            "### 2. Representation",
            "### 3. Direction",
            "### 4. System",
            "### 5. Vertical slice",
            "### 6. Pressure, repair, and replay",
        )
        offsets = [self.text.index(heading) for heading in headings]
        self.assertEqual(offsets, sorted(offsets))

    def test_requested_multi_direction_drafts_route_to_fast_style_calibration(self) -> None:
        direction = self.text.split("### 3. Direction", 1)[1].split(
            "### 4. System", 1
        )[0]
        self.assertIn("multiple direction drafts to confirm style", direction)
        self.assertIn("fast calibration pass", direction)
        self.assertIn("design-exploration.md", direction)

    def test_formal_build_uses_layered_feedback_without_skipping_release_gates(self) -> None:
        implementation = IMPLEMENTATION.read_text(encoding="utf-8")
        self.assertIn(
            "[implementation.md](references/implementation.md) during formal production",
            self.text,
        )
        for phrase in (
            "Carry the selected style contract",
            "do not restart discovery or direction",
            "dependency-ordered production pass",
            "semantics and data/state ownership",
            "responsive composition",
            "system roles and reusable primitives",
            "visual finish and admitted motion",
            "Run the cheapest owning-layer check",
            "fresh targeted Playwright replay after each coherent batch",
            "full declared affected matrix at the release candidate",
            "Never use a green narrow loop as release evidence",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, implementation)

    def test_formal_production_replays_are_bounded_to_the_selected_contract(self) -> None:
        implementation = IMPLEMENTATION.read_text(encoding="utf-8")
        for phrase in (
            "only the selected-contract axes affected by that batch",
            "the full selected style contract at the release candidate",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, implementation)

    def test_restricted_hosts_still_receive_the_minimum_design_md_contract(self) -> None:
        self.assertIn("machine-readable frontmatter", self.text)
        for field in ("version: alpha", "name:", "description:"):
            self.assertIn(field, self.text)
        ordered_sections = (
            "`Overview`",
            "`Colors`",
            "`Typography`",
            "`Layout`",
            "`Elevation & Depth`",
            "`Shapes`",
            "`Components`",
            "`Do's and Don'ts`",
        )
        system = self.text.split("### 4. System", 1)[1].split("### 5. Vertical slice", 1)[0]
        positions = [system.index(section) for section in ordered_sections]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("one coherent native role/state/keyboard model per control", self.text)
        self.assertIn("a live enabled focus target after re-render", self.text)

    def test_design_md_is_created_only_for_shared_system_governance(self) -> None:
        system = self.text.split("### 4. System", 1)[1].split("### 5. Vertical slice", 1)[0]
        for phrase in (
            "Create or update repository-root `DESIGN.md` only when",
            "one already exists",
            "the user requests the artifact",
            "shared visual system across multiple routes or reusable components",
            "For a route-local presentation change",
            "do not create a governance artifact solely to satisfy verification",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, system)
        self.assertNotIn(
            "When implementation creates or changes a visual system, create or update",
            system,
        )

    def test_responsive_task_order_stays_semantic_and_reachable(self) -> None:
        representation = self.text.split("### 2. Representation", 1)[1].split(
            "### 3. Direction", 1
        )[0]
        self.assertIn(
            "Keep responsive task order in the DOM; never fake it with CSS `order` or `*-reverse`.",
            representation,
        )

    def test_evidence_and_browser_contracts_remain_public(self) -> None:
        for status in ("`VERIFIED`", "`OBSERVED`", "`INFERRED`", "`UNVERIFIED`"):
            with self.subTest(status=status):
                self.assertIn(status, self.text)
        self.assertIn("project-pinned Playwright", self.text)
        self.assertIn("Do not use Computer Use", self.text)
        self.assertIn("Do not reuse an old screenshot, old page, stale build", self.text)

    def test_visible_state_contract_uses_rendered_text(self) -> None:
        quality = QUALITY_GATES.read_text(encoding="utf-8")
        self.assertIn("prefer `rendered-text-includes`", quality)
        self.assertIn("reads raw descendant `textContent`", quality)
        self.assertIn("may match hidden alternatives", quality)

    def test_public_metadata_and_all_markdown_routes_remain_discoverable(self) -> None:
        frontmatter = self.text.split("---", 2)[1]
        for field in (
            "name: wow-frontend-design",
            "license: MIT",
            'version: "0.3.0"',
        ):
            with self.subTest(field=field):
                self.assertIn(field, frontmatter)
        linked = {
            f"{root}/{name}"
            for root, name in re.findall(r"\]\((references|adapters)/([^\s)]+\.md)\)", self.text)
        }
        skill_root = SKILL.parent
        expected = {
            path.relative_to(skill_root).as_posix()
            for folder in (skill_root / "references", skill_root / "adapters")
            for path in folder.glob("*.md")
        }
        self.assertEqual(expected, linked)

    def test_authority_dependency_and_model_lane_boundaries_remain_explicit(self) -> None:
        for phrase in (
            "Do not branch, stash, commit, push, merge, or rewrite history",
            "Do not add a product dependency",
            "mutate a lockfile solely to satisfy verification",
            "never promote itself",
            "`AUDIT` is read-only",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)
        for mapping in (
            "greenfield request maps to `BUILD`",
            "existing-system redesign maps to `RETROFIT`",
            "user-described patch maps to `POLISH`",
            "or `REPAIR` when evidence identifies a defect",
            "Preserve every path outside that allowlist",
        ):
            with self.subTest(mapping=mapping):
                self.assertIn(mapping, self.text)

    def test_mobile_accessibility_and_repair_contracts_remain_explicit(self) -> None:
        for phrase in (
            "real mobile transformation when viewport UI is in scope",
            "keyboard and focus behavior",
            "static or reduced-motion result",
            "repair the smallest owning source surface",
            "replay the affected routes",
            "mark document validation `UNVERIFIED`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_rendered_craft_failure_families_are_prevented_at_generation_time(self) -> None:
        for phrase in (
            "encode it in perceivable content, structure, or control",
            "actual prerequisites and decision dependencies",
            "When evidence calls for identity",
            "`none` remains valid when identity would harm the task",
            "a softened or renamed version still fails source and rendered review",
            "rendered wraps preserve semantic units and intentional rhythm",
            "Never cap CJK display headings in Latin `ch`",
            "leave a one-Han final line",
            "cannot cover, bypass, or weaken required evidence",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_no_visual_first_pass_freezes_craft_decisions_before_code(self) -> None:
        text = NO_VISUAL.read_text(encoding="utf-8")
        for phrase in (
            "EVIDENCE → REQUIRED VISUAL PROPERTY",
            "ROLE-SPECIFIC MEASURE / WRAP",
            "FOCAL ANCHOR + MAJOR-REGION COMPOSITION / HIERARCHY",
            "MOTION PURPOSE + FREQUENCY + REDUCED RESULT, OR NONE",
            "neither justifies a font category, material metaphor, or palette",
            "inherit proven project values",
            "smallest task-safe, replaceable values required to render",
            "Treat fallback as scaffolding, never identity",
            "an authored distinction may remain `none`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
