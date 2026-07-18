#!/usr/bin/env python3
"""Regression checks for the generation-first Skill core."""

from __future__ import annotations

import unittest
import re
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


class SkillCoreContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = SKILL.read_bytes()
        cls.text = cls.raw.decode("utf-8")

    def test_core_stays_within_progressive_disclosure_budget(self) -> None:
        self.assertLessEqual(len(self.raw), 20_000)
        self.assertIn("On the initial reference pass", self.text)
        self.assertIn("at most one task-specific reference", self.text)

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

    def test_evidence_and_browser_contracts_remain_public(self) -> None:
        for status in ("`VERIFIED`", "`OBSERVED`", "`INFERRED`", "`UNVERIFIED`"):
            with self.subTest(status=status):
                self.assertIn(status, self.text)
        self.assertIn("project-pinned Playwright", self.text)
        self.assertIn("Do not use Computer Use", self.text)
        self.assertIn("Do not reuse an old screenshot, old page, stale build", self.text)

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


if __name__ == "__main__":
    unittest.main()
