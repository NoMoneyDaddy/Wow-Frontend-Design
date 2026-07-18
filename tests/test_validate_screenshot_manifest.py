#!/usr/bin/env python3
"""Tests for validate_screenshot_manifest.py."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wow-frontend-design" / "scripts"))

import validate_screenshot_manifest


@unittest.skip("legacy screenshot evidence intentionally cleared; current evidence is validated by the v6 cohort")
class ScreenshotManifestTests(unittest.TestCase):
    def test_repository_release_captures_are_fresh_and_decodable(self) -> None:
        root = Path(__file__).resolve().parents[1]
        count = validate_screenshot_manifest.validate(root / "assets" / "screenshots.json", root)
        self.assertEqual(4, count)

    def test_stale_hash_is_rejected(self) -> None:
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root / "assets" / "screenshots.json").read_text(encoding="utf-8"))
        data["captures"][0]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "screenshots.json"
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(validate_screenshot_manifest.ScreenshotManifestError, "stale"):
                validate_screenshot_manifest.validate(manifest, root)

    def test_null_commit_requires_explicit_hash_boundary(self) -> None:
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root / "assets" / "screenshots.json").read_text(encoding="utf-8"))
        data["source_binding"] = "captured before release without a commit"
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "screenshots.json"
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(validate_screenshot_manifest.ScreenshotManifestError, "commit-independent"):
                validate_screenshot_manifest.validate(manifest, root)


if __name__ == "__main__":
    unittest.main()
