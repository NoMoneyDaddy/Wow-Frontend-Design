#!/usr/bin/env python3
"""Tests for validate_installability.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_installability


class InstallabilityTests(unittest.TestCase):
    def test_repository_skill_is_installable(self) -> None:
        root = Path(__file__).resolve().parents[2]
        count = validate_installability.validate(root / "wow-frontend-design", root)
        self.assertGreaterEqual(count, 35)

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


if __name__ == "__main__":
    unittest.main()
