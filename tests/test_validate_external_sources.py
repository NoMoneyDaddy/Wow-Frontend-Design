#!/usr/bin/env python3
"""Tests for validate_external_sources.py."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wow-frontend-design" / "scripts"))

import validate_external_sources


class SourceLockTests(unittest.TestCase):
    def test_repository_lock_is_valid(self) -> None:
        root = Path(__file__).resolve().parents[1]
        count = validate_external_sources.validate(
            root / "wow-frontend-design" / "references" / "external-sources.lock.json"
        )
        self.assertEqual(count, 100)

    def test_user_provided_repositories_have_review_decisions(self) -> None:
        root = Path(__file__).resolve().parents[1]
        lock = validate_external_sources.load(
            root / "wow-frontend-design" / "references" / "external-sources.lock.json"
        )
        reviewed = {source["repository"] for source in lock["sources"]}
        expected = {
            "AlmogBaku/debug-skill",
            "AugmentedAJ/skills",
            "Dammyjay93/interface-design",
            "Leonxlnx/taste-skill",
            "Lombiq/Tailwind-Agent-Skills",
            "Mindrally/skills",
            "MengTo/Skills",
            "Xialiang98/design-visual-frontend",
            "akseolabs-seo/cinematic-ui",
            "anthropics/claude-cookbooks",
            "anthropics/claude-plugins-official",
            "anthropics/skills",
            "biomejs/biome",
            "buildermethods/design-os",
            "carmahhawwari/ui-design-brain",
            "chenglou/pretext",
            "colbymchenry/frontend-audit-skill",
            "daniruiz/skeuos-gtk",
            "dceoy/ai-coding-agent-skills",
            "design-token-kit/design-token-kit",
            "dylantarre/animation-principles",
            "eachlabs/skills",
            "emilkowalski/skills",
            "facebook/astryx",
            "figma/mcp-server-guide",
            "garrytan/gstack",
            "github/awesome-copilot",
            "hamen/material-3-skill",
            "ibelick/ui-skills",
            "jamiemill/layers-skills",
            "jezweb/claude-skills",
            "justinwetch/skills",
            "majiayu000/claude-skill-registry",
            "mastepanoski/claude-skills",
            "mattpocock/skills",
            "microsoft/GitHubCopilot_Customized",
            "microsoft/skills",
            "mikemai2awesome/agent-skills",
            "mitang-ai/frontend-distill",
            "moondesignsystem/react",
            "moondesignsystem/ui",
            "MoizIbnYousaf/Ai-Agent-Skills",
            "multica-ai/andrej-karpathy-skills",
            "neonwatty/css-animation-skill",
            "nexu-io/open-design",
            "pm7y/pm7y-marketplace",
            "sleekdotdesign/agent-skills",
            "sickn33/agentic-awesome-skills",
            "stylelint/stylelint",
            "superdesigndev/superdesign",
            "superdesigndev/superdesign-skill",
            "szymdzum/browser-debugger-cli",
            "tigerless-labs/design-harness",
            "tommyjepsen/awesome-ux-skills",
            "vercel-labs/agent-skills",
            "w3c/css-validator",
            "web-platform-tests/wpt",
            "xntj-ai/ppvi",
            "rknall/claude-skills",
        }
        self.assertEqual(set(), expected - reviewed)
        integration = (
            root / "wow-frontend-design" / "references" / "curated-skill-integration.md"
        ).read_text(encoding="utf-8")
        self.assertIn("`Amandeepwazir/UX-Designer` was empty", integration)
        self.assertIn("`ThepExcel/agent-skills` was unavailable", integration)
        self.assertIn("`sickn33/antigravity-awesome-skills` redirected", integration)
        self.assertIn("`skillcreatorai/ai-agent-skills` redirected", integration)

    def test_mengto_subskills_have_complete_review_receipts(self) -> None:
        root = Path(__file__).resolve().parents[1]
        references = root / "wow-frontend-design" / "references"
        audit = json.loads(
            (references / "mengto-skills-audit.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            set(audit),
            {
                "schema_version",
                "repository",
                "revision",
                "reviewed_at",
                "inventory",
                "skills",
            },
        )
        self.assertEqual(audit["schema_version"], 1)
        self.assertEqual(audit["repository"], "MengTo/Skills")
        self.assertEqual(
            audit["inventory"],
            {
                "readme_claimed_skill_count": 118,
                "observed_skill_count": 121,
                "skill_paths_sha256": "7ec5c3e9aad104800b616ee6a4a3743242e04e9846d1086cffe7ac4241c8f183",
                "category_counts": {
                    "codex": 18,
                    "customer-support": 2,
                    "game-development": 19,
                    "media": 2,
                    "ui": 1,
                    "web-design": 79,
                },
            },
        )
        skills = audit["skills"]
        self.assertEqual(len(skills), 121)
        paths = [item["path"] for item in skills]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(121, len({item["name"] for item in skills}))
        path_receipt = hashlib.sha256(
            ("\n".join(sorted(paths)) + "\n").encode("utf-8")
        ).hexdigest()
        self.assertEqual(
            "7ec5c3e9aad104800b616ee6a4a3743242e04e9846d1086cffe7ac4241c8f183",
            path_receipt,
        )
        category_counts = {
            category: sum(item["category"] == category for item in skills)
            for category in audit["inventory"]["category_counts"]
        }
        self.assertEqual(audit["inventory"]["category_counts"], category_counts)
        self.assertEqual(
            [],
            [
                item["path"]
                for item in skills
                if item["category"] == "web-design"
                and item["disposition"] == "out_of_scope"
            ],
        )
        allowed_dispositions = {
            "integrated",
            "covered",
            "style_reference_only",
            "out_of_scope",
            "rejected",
        }
        for item in skills:
            self.assertEqual(
                set(item),
                {
                    "path",
                    "name",
                    "category",
                    "disposition",
                    "owner_reference",
                    "rationale",
                },
            )
            self.assertTrue(item["path"].startswith(f"agent-skills/{item['category']}/"))
            self.assertTrue(item["path"].endswith("/SKILL.md"))
            self.assertNotIn("..", Path(item["path"]).parts)
            self.assertIn(item["disposition"], allowed_dispositions)
            self.assertTrue(20 <= len(item["rationale"]) <= 240)
            owner = item["owner_reference"]
            if item["disposition"] in {"integrated", "covered"}:
                self.assertIsInstance(owner, str)
                self.assertTrue((references / owner).is_file())
            else:
                self.assertIsNone(owner)

        lock = validate_external_sources.load(
            references / "external-sources.lock.json"
        )
        source = next(
            item for item in lock["sources"] if item["repository"] == "MengTo/Skills"
        )
        self.assertEqual(audit["revision"], source["revision"])
        self.assertEqual(
            source["review"]["owner_reference"], "curated-skill-integration.md"
        )
        locked_skill_paths = {
            path
            for path in source["paths"]
            if path.startswith("agent-skills/") and path.endswith("/SKILL.md")
        }
        self.assertEqual(set(paths), locked_skill_paths)
        self.assertEqual(
            {
                item["path"]: item["owner_reference"]
                for item in skills
                if item["disposition"] == "integrated"
            },
            {
                "agent-skills/codex/stitched-full-page-capture/SKILL.md": "visual-regression-evidence.md",
                "agent-skills/web-design/landing-page/SKILL.md": "pattern-catalog.md",
                "agent-skills/web-design/operational-enterprise-ai/SKILL.md": "pattern-catalog.md",
                "agent-skills/web-design/pricing-page/SKILL.md": "pattern-catalog.md",
                "agent-skills/web-design/product-proof-saas/SKILL.md": "pattern-catalog.md",
                "agent-skills/web-design/scroll-progress-timeline/SKILL.md": "motion-system.md",
                "agent-skills/web-design/scroll-scrubbed-visual-sequence/SKILL.md": "motion-system.md",
                "agent-skills/web-design/scroll-world-storytelling/SKILL.md": "motion-system.md",
            },
        )

    def test_short_revision_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lock.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "retrieved_at": "2026-07-14",
                        "policy": "Pinned research only; verify before any use.",
                        "sources": [
                            {
                                "repository": "example/repo",
                                "revision": "deadbeef",
                                "license": "MIT",
                                "paths": ["SKILL.md"],
                                "review": {
                                    "disposition": "no_integration",
                                    "reviewed_revision": "deadbeef",
                                    "no_integration_reason": "Reviewed only as a fixture; no portable rule was adopted.",
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(validate_external_sources.SourceLockError):
                validate_external_sources.validate(path)

    def test_oversized_and_deep_locks_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            oversized = root / "oversized.json"
            oversized.write_bytes(b" " * (validate_external_sources.MAX_LOCK_BYTES + 1))
            with self.assertRaisesRegex(validate_external_sources.SourceLockError, "exceeds"):
                validate_external_sources.load(oversized)

            deep = root / "deep.json"
            deep.write_text("[" * 1_100 + "]" * 1_100, encoding="utf-8")
            with self.assertRaises(validate_external_sources.SourceLockError):
                validate_external_sources.load(deep)

            bracket_text = root / "bracket-text.json"
            bracket_text.write_text(json.dumps({"value": "[" * 1_100}), encoding="utf-8")
            self.assertEqual("[" * 1_100, validate_external_sources.load(bracket_text)["value"])

    def test_review_revision_must_match_pin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "lock.json"
            owner = root / "owner.md"
            owner.write_text("# Owner\n", encoding="utf-8")
            revision = "a" * 40
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "retrieved_at": "2026-07-20",
                        "policy": "Pinned research only; a review decision is required before use.",
                        "sources": [
                            {
                                "repository": "example/repo",
                                "revision": revision,
                                "license": "MIT",
                                "paths": ["SKILL.md"],
                                "review": {
                                    "disposition": "integrated",
                                    "reviewed_revision": "b" * 40,
                                    "owner_reference": "owner.md",
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(validate_external_sources.SourceLockError, "must equal revision"):
                validate_external_sources.validate(path)

    def test_integrated_review_requires_existing_owned_reference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "lock.json"
            revision = "a" * 40
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "retrieved_at": "2026-07-20",
                        "policy": "Pinned research only; a review decision is required before use.",
                        "sources": [
                            {
                                "repository": "example/repo",
                                "revision": revision,
                                "license": "MIT",
                                "paths": ["SKILL.md"],
                                "review": {
                                    "disposition": "integrated",
                                    "reviewed_revision": revision,
                                    "owner_reference": "missing.md",
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(validate_external_sources.SourceLockError, "owned reference"):
                validate_external_sources.validate(path)

    def test_integrated_review_rejects_backslash_owner_reference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "lock.json"
            revision = "a" * 40
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "retrieved_at": "2026-07-20",
                        "policy": "Pinned research only; a review decision is required before use.",
                        "sources": [
                            {
                                "repository": "example/repo",
                                "revision": revision,
                                "license": "MIT",
                                "paths": ["SKILL.md"],
                                "review": {
                                    "disposition": "integrated",
                                    "reviewed_revision": revision,
                                    "owner_reference": "..\\owner.md",
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(validate_external_sources.SourceLockError, "safe Markdown"):
                validate_external_sources.validate(path)

    def test_no_integration_review_rejects_owner_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "lock.json"
            revision = "a" * 40
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "retrieved_at": "2026-07-20",
                        "policy": "Pinned research only; a review decision is required before use.",
                        "sources": [
                            {
                                "repository": "example/repo",
                                "revision": revision,
                                "license": "MIT",
                                "paths": ["SKILL.md"],
                                "review": {
                                    "disposition": "no_integration",
                                    "reviewed_revision": revision,
                                    "no_integration_reason": "Reviewed; no portable rule was adopted from this source.",
                                    "owner_reference": "owner.md",
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(validate_external_sources.SourceLockError, "exactly"):
                validate_external_sources.validate(path)


if __name__ == "__main__":
    unittest.main()
