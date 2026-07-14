#!/usr/bin/env python3
"""Tests for lottie_asset_audit.py."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lottie_asset_audit


def clean_lottie() -> dict[str, object]:
    return {"v": "5.12.0", "fr": 30, "ip": 0, "op": 60, "w": 800, "h": 600, "layers": []}


class LottieAssetAuditTests(unittest.TestCase):
    def test_ignores_unrelated_json_and_accepts_minimal_lottie(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text('{"name":"demo"}', encoding="utf-8")
            (root / "scene.json").write_text(json.dumps(clean_lottie()), encoding="utf-8")
            findings, audited = lottie_asset_audit.audit(root)
            self.assertEqual(audited, 1)
            self.assertEqual(findings, [])

    def test_external_assets_frames_and_text_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = clean_lottie()
            value.update(
                {
                    "fr": 0,
                    "assets": [{"u": "https://example.test/", "p": "image.png"}],
                    "fonts": {"list": [{"fName": "Unknown"}]},
                }
            )
            (root / "unsafe.json").write_text(json.dumps(value), encoding="utf-8")
            rules = {item.rule for item in lottie_asset_audit.audit(root)[0]}
            self.assertTrue({"LOTTIE002", "LOTTIE006", "LOTTIE010"}.issubset(rules))

    def test_non_finite_json_numbers_are_rejected(self) -> None:
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "invalid.json").write_text(
                    '{"v":"5.12.0","fr":%s,"ip":0,"op":60,"w":800,"h":600,"layers":[]}'
                    % constant,
                    encoding="utf-8",
                )
                rules = {item.rule for item in lottie_asset_audit.audit(root)[0]}
                self.assertIn("LOTTIE011", rules)

    def test_boolean_dimensions_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = clean_lottie()
            value["w"] = True
            (root / "invalid.json").write_text(json.dumps(value), encoding="utf-8")
            rules = {item.rule for item in lottie_asset_audit.audit(root)[0]}
            self.assertIn("LOTTIE003", rules)

    def test_dotlottie_requires_safe_paths_and_expected_documents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "unsafe.lottie"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("../escape.json", "{}")
            rules = {item.rule for item in lottie_asset_audit.audit(root)[0]}
            self.assertIn("LOTTIE015", rules)
            self.assertIn("LOTTIE019", rules)

    def test_valid_dotlottie_audits_embedded_animation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "scene.lottie"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("manifest.json", '{"animations":[{"id":"main"}]}')
                archive.writestr("animations/main.json", json.dumps(clean_lottie()))
            findings, audited = lottie_asset_audit.audit(root)
            self.assertEqual(audited, 1)
            self.assertEqual(findings, [])

    def test_oversized_embedded_animation_cannot_pass_unaudited(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "oversized.lottie"
            pad = "".join(hashlib.sha256(str(index).encode()).hexdigest() for index in range(82_000))
            value = clean_lottie()
            value["pad"] = pad
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("manifest.json", '{"animations":[{"id":"main"}]}')
                archive.writestr("animations/main.json", json.dumps(value))

            self.assertLess(archive_path.stat().st_size, lottie_asset_audit.MAX_ASSET_BYTES)
            rules = {item.rule for item in lottie_asset_audit.audit(root)[0]}
            self.assertIn("LOTTIE012", rules)

    def test_symlink_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            target = base / "target"
            target.mkdir()
            link = base / "link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(lottie_asset_audit.AuditError):
                lottie_asset_audit.audit(link)


if __name__ == "__main__":
    unittest.main()
