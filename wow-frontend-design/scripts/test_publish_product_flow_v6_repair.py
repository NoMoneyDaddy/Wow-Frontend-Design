#!/usr/bin/env python3
"""Security regression tests for transactional v6 evidence publication."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "evals" / "publish_product_flow_v6_repair.py"
SPEC = importlib.util.spec_from_file_location("publish_product_flow_v6_repair", MODULE_PATH)
assert SPEC and SPEC.loader
publish = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publish)


class ProductFlowPublicationTests(unittest.TestCase):
    def test_repository_provenance_rejects_symlinked_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real.json"
            linked = root / "linked.json"
            real.write_text("{}\n", encoding="utf-8")
            linked.symlink_to(real)
            with mock.patch.object(publish, "ROOT", root):
                with self.assertRaisesRegex(publish.PublishError, "symlinked"):
                    publish._repository_file("linked.json", "ledger input")

    def test_visual_preflight_rejects_unbound_non_png_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "visual.json"
            screenshots = root / "screenshots"
            screenshots.mkdir()
            (screenshots / "forged.png").write_bytes(b"NOT-A-PNG")
            report.write_text(
                json.dumps(
                    {
                        "results": [{"screenshot": str(screenshots / "forged.png")}],
                        "summary": {"targetsWithObservedIssues": 0, "verdict": "no_observed_issues"},
                    }
                ),
                encoding="utf-8",
            )
            generation = root / "generation.json"
            generation.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(publish.PublishError, "visual evidence validation failed"):
                publish._prepare_visual(report, screenshots, generation, [])

    def test_build_plan_does_not_mutate_before_all_preflight_stages_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generation = root / publish.GENERATION_PATH
            generation.parent.mkdir(parents=True)
            generation.write_text("{}\n", encoding="utf-8")
            destination = root / "destination.json"
            destination.write_text("old\n", encoding="utf-8")
            with (
                mock.patch.object(publish, "ROOT", root),
                mock.patch.object(publish, "_generation_targets", return_value=([], {})),
                mock.patch.object(
                    publish,
                    "_prepare_visual",
                    return_value=({destination: b"new\n"}, {}),
                ),
                mock.patch.object(publish, "_prepare_manifests", side_effect=publish.PublishError("late preflight")),
            ):
                with self.assertRaisesRegex(publish.PublishError, "late preflight"):
                    publish.build_publication_plan(root / "visual.json", root / "screenshots")
            self.assertEqual("old\n", destination.read_text(encoding="utf-8"))

    def test_final_visual_report_binds_exact_final_generation_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generation = b'{"status":"completed"}\n'
            with mock.patch.object(publish, "ROOT", root):
                report = json.loads(publish._finalize_visual({"results": []}, generation))
            self.assertEqual(
                {
                    "path": publish.GENERATION_PATH.as_posix(),
                    "sha256": hashlib.sha256(generation).hexdigest(),
                },
                report["generation_ledger"],
            )

    def test_staged_validation_rejects_stale_generation_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case_id = "case-v6"
            manifest = b'{}\n'
            generation = json.dumps(
                {
                    "results": [
                        {
                            "case_id": case_id,
                            "receipt": {"manifest_sha256": hashlib.sha256(manifest).hexdigest()},
                        }
                    ]
                }
            ).encode()
            generation_path = root / publish.GENERATION_PATH
            visual_path = root / publish.VISUAL_PATH
            manifest_path = root / publish.TARGET_ROOT / f"{publish.ALIAS}-{case_id}" / "run-manifest.json"
            report = json.dumps(
                {"generation_ledger": {"path": publish.GENERATION_PATH.as_posix(), "sha256": "0" * 64}, "results": []}
            ).encode()
            with mock.patch.object(publish, "ROOT", root), mock.patch.object(
                publish, "CASES", {case_id: ("DESIGN.md", "index.html")}
            ):
                with self.assertRaisesRegex(publish.PublishError, "final generation ledger"):
                    publish._validate_publication_plan(
                        {generation_path: generation, visual_path: report, manifest_path: manifest}
                    )

    def test_transaction_rolls_back_every_destination_after_mid_commit_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.json"
            second = root / "second.json"
            first.write_bytes(b"old-first")
            second.write_bytes(b"old-second")
            real_replace = publish.os.replace
            calls = 0

            def fail_fourth_replace(source: object, destination: object) -> None:
                nonlocal calls
                calls += 1
                if calls == 4:
                    raise OSError("injected commit failure")
                real_replace(source, destination)

            with mock.patch.object(publish, "ROOT", root), mock.patch.object(
                publish.os, "replace", side_effect=fail_fourth_replace
            ):
                with self.assertRaisesRegex(publish.PublishError, "rolled back"):
                    publish.commit_publication({first: b"new-first", second: b"new-second"})
            self.assertEqual(b"old-first", first.read_bytes())
            self.assertEqual(b"old-second", second.read_bytes())

    def test_transaction_commits_complete_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.json"
            second = root / "second.json"
            first.write_bytes(b"old-first")
            second.write_bytes(b"old-second")
            with mock.patch.object(publish, "ROOT", root):
                publish.commit_publication({first: b"new-first", second: b"new-second"})
            self.assertEqual(b"new-first", first.read_bytes())
            self.assertEqual(b"new-second", second.read_bytes())


if __name__ == "__main__":
    unittest.main()
