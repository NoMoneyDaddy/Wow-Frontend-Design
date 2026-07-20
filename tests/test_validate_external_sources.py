#!/usr/bin/env python3
"""Tests for validate_external_sources.py."""

from __future__ import annotations

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
        self.assertEqual(count, 98)

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
