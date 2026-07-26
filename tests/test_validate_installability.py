#!/usr/bin/env python3
"""Tests for validate_installability.py."""

from __future__ import annotations

import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wow-frontend-design" / "scripts"))

import validate_installability


class InstallabilityTests(unittest.TestCase):
    def _write_skill(self, root: Path, description: str) -> Path:
        skill = root / "sample"
        (skill / "agents").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: sample\ndescription: " + description + "\nlicense: MIT\n---\n",
            encoding="utf-8",
        )
        (skill / "LICENSE").write_text("MIT", encoding="utf-8")
        (skill / "agents" / "openai.yaml").write_text(
            'interface:\n  short_description: "1234567890123456789012345"\n'
            '  default_prompt: "Use $sample now."\n',
            encoding="utf-8",
        )
        return skill

    def test_block_scalar_description_uses_its_actual_content(self) -> None:
        cases = (
            (">-\n  A sufficiently explicit\n  folded sample description.", None),
            ("|-\n  ", "frontmatter description must contain 1..1024 characters"),
            (">-\n  " + "x" * 1025, "frontmatter description must contain 1..1024 characters"),
            (">2-\n  " + "x" * 1025, "unsupported YAML block scalar header"),
            ("|+\n  A sufficiently explicit sample description.", "unsupported YAML block scalar header"),
            (
                ">-\n    A sufficiently explicit sample description.\n  invalid dedent",
                "invalid YAML block scalar indentation",
            ),
            (
                ">-\n\tA sufficiently explicit sample description.",
                "invalid YAML block scalar indentation",
            ),
        )
        for description, error in cases:
            with self.subTest(description=description[:20]):
                with tempfile.TemporaryDirectory() as directory:
                    skill = self._write_skill(Path(directory), description)
                    if error is None:
                        self.assertEqual(
                            "A sufficiently explicit folded sample description.",
                            validate_installability._frontmatter(skill / "SKILL.md")["description"],
                        )
                        self.assertGreaterEqual(validate_installability.validate(skill), 0)
                    else:
                        with self.assertRaisesRegex(validate_installability.InstallabilityError, error):
                            validate_installability.validate(skill)

    def test_repository_skill_is_installable(self) -> None:
        root = Path(__file__).resolve().parents[1]
        count = validate_installability.validate(root / "wow-frontend-design", root)
        self.assertGreaterEqual(count, 35)

    def test_runtime_skill_does_not_bundle_repository_tests(self) -> None:
        root = Path(__file__).resolve().parents[1]
        bundled = sorted(
            path.relative_to(root / "wow-frontend-design").as_posix()
            for path in (root / "wow-frontend-design").rglob("test_*.py")
        )
        self.assertEqual([], bundled)
        repository_tests = {path.name for path in (root / "tests").glob("test_*.py")}
        self.assertTrue(
            {
                "test_run_current_skill_build.py",
                "test_playwright_html_smoke.py",
                "test_validate_installability.py",
            }.issubset(repository_tests)
        )

    def test_repository_openai_prompt_tracks_runtime_contract(self) -> None:
        root = Path(__file__).resolve().parents[1]
        prompt = (root / "wow-frontend-design" / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        for signal in (
            "$wow-frontend-design",
            "產出可執行成品",
            "fresh Playwright",
            "bounded repair",
        ):
            with self.subTest(signal=signal):
                self.assertIn(signal, prompt)
        self.assertNotIn("CONTRACT", prompt)
        self.assertNotIn("DISCOVERY", prompt)
        self.assertNotIn("必要時先確認方向與重構深度", prompt)

    def test_escaping_link_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "sample"
            (skill / "agents").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: sample\ndescription: A sufficiently explicit sample description.\nlicense: MIT\n---\n[bad](../outside.md)\n",
                encoding="utf-8",
            )
            (skill / "LICENSE").write_text("MIT", encoding="utf-8")
            (skill / "agents" / "openai.yaml").write_text(
                'interface:\n  short_description: "1234567890123456789012345"\n  default_prompt: "Use $sample now."\n',
                encoding="utf-8",
            )
            with self.assertRaises(validate_installability.InstallabilityError):
                validate_installability.validate(skill)

    def test_unlinked_markdown_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "sample"
            (skill / "agents").mkdir(parents=True)
            (skill / "references").mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: sample\ndescription: A sufficiently explicit sample description.\nlicense: MIT\n---\n",
                encoding="utf-8",
            )
            (skill / "LICENSE").write_text("MIT", encoding="utf-8")
            (skill / "agents" / "openai.yaml").write_text(
                'interface:\n  short_description: "1234567890123456789012345"\n  default_prompt: "Use $sample now."\n',
                encoding="utf-8",
            )
            (skill / "references" / "orphan.md").write_text("# Orphan\n", encoding="utf-8")
            with self.assertRaisesRegex(
                validate_installability.InstallabilityError,
                r"unlinked: references/orphan\.md",
            ):
                validate_installability.validate(skill)

    def test_reference_link_inside_code_does_not_satisfy_reachability(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "sample"
            (skill / "agents").mkdir(parents=True)
            (skill / "references").mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: sample\ndescription: A sufficiently explicit sample description.\nlicense: MIT\n---\n"
                "```md\n[not a route](references/orphan.md)\n```\n"
                "`[also not a route](references/orphan.md)`\n",
                encoding="utf-8",
            )
            (skill / "LICENSE").write_text("MIT", encoding="utf-8")
            (skill / "agents" / "openai.yaml").write_text(
                'interface:\n  short_description: "1234567890123456789012345"\n  default_prompt: "Use $sample now."\n',
                encoding="utf-8",
            )
            (skill / "references" / "orphan.md").write_text("# Orphan\n", encoding="utf-8")
            with self.assertRaisesRegex(validate_installability.InstallabilityError, r"unlinked"):
                validate_installability.validate(skill)

    def test_gitignored_environment_secret_is_still_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "sample"
            (skill / "agents").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: sample\ndescription: A sufficiently explicit sample description.\nlicense: MIT\n---\n",
                encoding="utf-8",
            )
            (skill / "LICENSE").write_text("MIT", encoding="utf-8")
            (skill / "agents" / "openai.yaml").write_text(
                'interface:\n  short_description: "1234567890123456789012345"\n'
                '  default_prompt: "Use $sample now."\n',
                encoding="utf-8",
            )
            (skill / ".env.production").write_text("TOKEN=do-not-package\n", encoding="utf-8")
            (root / ".gitignore").write_text("sample/.env.production\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(root)], check=True)

            with self.assertRaisesRegex(validate_installability.InstallabilityError, r"\.env\.production"):
                validate_installability.validate(skill, root)


if __name__ == "__main__":
    unittest.main()
