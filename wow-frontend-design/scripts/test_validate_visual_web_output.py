#!/usr/bin/env python3
"""Unit tests for the visual-output packaging validator."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "evals" / "validate_visual_web_output.py"
SPEC = importlib.util.spec_from_file_location("validate_visual_web_output", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class VisualWebOutputValidatorTests(unittest.TestCase):
    def test_two_file_visual_case(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
            (root / "index.html").write_text("<main></main>", encoding="utf-8")
            self.assertEqual([], validator.validate("harbor-cold-chain-v4", root))

    def test_plant_swap_requires_all_three_pages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("DESIGN.md", "index.html", "browse.html"):
                (root / name).write_text("content\n", encoding="utf-8")
            self.assertTrue(any("output set" in issue for issue in validator.validate("plant-swap-one-line-v4", root)))


if __name__ == "__main__":
    unittest.main()
