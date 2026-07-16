#!/usr/bin/env python3
"""Tests for the published Codex v6 evidence validator."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_product_flow_v6_evidence


class ProductFlowV6EvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.visual = self.root / "evals/product-flow-v6-visual-results.json"
        self.generation = self.root / "evals/product-flow-v6-repaired-v2-generation-results.json"

    @staticmethod
    def _write(data: dict[str, object], directory: str, name: str) -> Path:
        path = Path(directory) / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_repository_v6_evidence_is_integrity_bound(self) -> None:
        self.assertEqual(8, validate_product_flow_v6_evidence.validate(self.visual, self.root))

    def test_stale_screenshot_hash_is_rejected(self) -> None:
        data = json.loads(self.visual.read_text(encoding="utf-8"))
        data["results"][0]["screenshotSha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(data, directory, "visual.json")
            with self.assertRaisesRegex(validate_product_flow_v6_evidence.ProductFlowV6EvidenceError, "screenshot hash is stale"):
                validate_product_flow_v6_evidence._validate_visual(self.root, path, self.generation)

    def test_body_flow_finding_cannot_be_hidden(self) -> None:
        data = json.loads(self.visual.read_text(encoding="utf-8"))
        data["results"][0]["bodyFlow"]["forcedLineBreaks"] = [{"breakCount": 1}]
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(data, directory, "visual.json")
            with self.assertRaisesRegex(validate_product_flow_v6_evidence.ProductFlowV6EvidenceError, "body flow repair finding remains"):
                validate_product_flow_v6_evidence._validate_visual(self.root, path, self.generation)

    def test_heading_and_layout_flow_findings_cannot_be_hidden(self) -> None:
        for field, value, message in (
            (
                "headingFlow",
                {
                    "compressedCjkHeadings": [{"lineCount": 5}],
                    "orphanedCjkHeadingLines": [],
                    "underfilledWideHeadings": [],
                },
                "heading flow repair finding remains",
            ),
            (
                "layoutFlow",
                {"domOrderReversals": [{"upwardShift": 120}], "displacedIntroCopy": []},
                "layout flow repair finding remains",
            ),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                data = json.loads(self.visual.read_text(encoding="utf-8"))
                data["results"][0][field] = value
                path = self._write(data, directory, "visual.json")
                with self.assertRaisesRegex(validate_product_flow_v6_evidence.ProductFlowV6EvidenceError, message):
                    validate_product_flow_v6_evidence._validate_visual(self.root, path, self.generation)

    def test_underfilled_heading_intro_and_locale_findings_cannot_be_hidden(self) -> None:
        for field, value, message in (
            (
                "headingFlow",
                {
                    "compressedCjkHeadings": [],
                    "orphanedCjkHeadingLines": [],
                    "underfilledWideHeadings": [{"ratio": 0.42}],
                },
                "heading flow repair finding remains",
            ),
            (
                "layoutFlow",
                {"domOrderReversals": [], "displacedIntroCopy": [{"startRatio": 0.56}]},
                "layout flow repair finding remains",
            ),
            (
                "layoutFlow",
                {
                    "domOrderReversals": [],
                    "displacedIntroCopy": [],
                    "unfilledColumnVoids": [{"target": "article-copy", "voidHeight": 936}],
                },
                "layout flow repair finding remains",
            ),
            (
                "localeFlow",
                {"untranslatedInterfaceCopy": [{"text": "Current configuration"}]},
                "locale flow repair finding remains",
            ),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                data = json.loads(self.visual.read_text(encoding="utf-8"))
                data["results"][0][field] = value
                path = self._write(data, directory, "visual.json")
                with self.assertRaisesRegex(validate_product_flow_v6_evidence.ProductFlowV6EvidenceError, message):
                    validate_product_flow_v6_evidence._validate_visual(self.root, path, self.generation)

    def test_exact_model_cohort_cannot_change(self) -> None:
        data = json.loads(self.generation.read_text(encoding="utf-8"))
        data["selection"]["model"] = "gpt-5.4"
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(data, directory, "generation.json")
            with self.assertRaisesRegex(validate_product_flow_v6_evidence.ProductFlowV6EvidenceError, "exact Codex v6 mini cohort"):
                validate_product_flow_v6_evidence.validate(self.visual, self.root, generation_path=path)

    def test_latest_skill_repair_provenance_cannot_be_hidden(self) -> None:
        data = json.loads(self.generation.read_text(encoding="utf-8"))
        repair = data["results"][0]
        manifest = self.root / repair["manifest"]
        original = json.loads(manifest.read_text(encoding="utf-8"))
        changed = json.loads(json.dumps(original))
        changed["skill_repair"]["visual_report"]["bound_by"] = "builder_claim"
        original_load = validate_product_flow_v6_evidence._load

        def fake_load(path: Path, label: str) -> dict[str, object]:
            if path.resolve() == manifest.resolve():
                return changed
            return original_load(path, label)

        with mock.patch.object(validate_product_flow_v6_evidence, "_load", side_effect=fake_load):
            with self.assertRaisesRegex(validate_product_flow_v6_evidence.ProductFlowV6EvidenceError, "repair visual report .* provenance changed"):
                validate_product_flow_v6_evidence._validate_generation(self.root, self.generation, self.visual)

    def test_changed_outputs_must_equal_source_digest_delta(self) -> None:
        data = json.loads(self.generation.read_text(encoding="utf-8"))
        manifest = self.root / data["results"][0]["manifest"]
        changed = json.loads(manifest.read_text(encoding="utf-8"))
        changed["skill_repair"]["changed_outputs"] = [None]
        original_load = validate_product_flow_v6_evidence._load

        def fake_load(path: Path, label: str) -> dict[str, object]:
            if path.resolve() == manifest.resolve():
                return changed
            return original_load(path, label)

        with mock.patch.object(validate_product_flow_v6_evidence, "_load", side_effect=fake_load):
            with self.assertRaisesRegex(
                validate_product_flow_v6_evidence.ProductFlowV6EvidenceError,
                "changed-output inventory is invalid",
            ):
                validate_product_flow_v6_evidence._validate_generation(
                    self.root,
                    self.generation,
                    self.visual,
                )

    def test_repair_source_manifest_path_is_canonical(self) -> None:
        data = json.loads(self.generation.read_text(encoding="utf-8"))
        manifest = self.root / data["results"][0]["manifest"]
        changed = json.loads(manifest.read_text(encoding="utf-8"))
        alternate = self.root / "evals/product-flow-v6-repaired-generation-results.json"
        changed["skill_repair"]["source_manifest"] = {
            "path": str(alternate.relative_to(self.root)),
            "sha256": validate_product_flow_v6_evidence._digest(alternate),
        }
        original_load = validate_product_flow_v6_evidence._load

        def fake_load(path: Path, label: str) -> dict[str, object]:
            if path.resolve() == manifest.resolve():
                return changed
            return original_load(path, label)

        with mock.patch.object(validate_product_flow_v6_evidence, "_load", side_effect=fake_load):
            with self.assertRaisesRegex(
                validate_product_flow_v6_evidence.ProductFlowV6EvidenceError,
                "source manifest .* provenance is missing",
            ):
                validate_product_flow_v6_evidence._validate_generation(
                    self.root,
                    self.generation,
                    self.visual,
                )

    def test_alternate_visual_report_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            alternate = Path(directory) / "visual.json"
            alternate.write_bytes(self.visual.read_bytes())
            with self.assertRaisesRegex(
                validate_product_flow_v6_evidence.ProductFlowV6EvidenceError,
                "not the published report",
            ):
                validate_product_flow_v6_evidence.validate(alternate, self.root)


if __name__ == "__main__":
    unittest.main()
