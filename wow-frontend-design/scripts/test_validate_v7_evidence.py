#!/usr/bin/env python3
"""Focused contract tests for the v7 evidence inventory."""

from __future__ import annotations

import copy
import importlib.util
import hashlib
import contextlib
import io
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "wow-frontend-design" / "scripts" / "validate_v7_evidence.py"
SPEC = importlib.util.spec_from_file_location("validate_v7_evidence", MODULE)
assert SPEC and SPEC.loader
evidence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evidence)


class V7EvidenceTests(unittest.TestCase):
    @staticmethod
    def png(width: int = 1440, height: int = 1000) -> bytes:
        def chunk(name: bytes, body: bytes) -> bytes:
            return struct.pack(">I", len(body)) + name + body + struct.pack(">I", zlib.crc32(name + body) & 0xFFFFFFFF)

        header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
        row = b"\x00" + b"\x00\x00\x00\xff" * width
        pixels = zlib.compress(row * height)
        return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", pixels) + chunk(b"IEND", b"")

    def manifest(self, count: int) -> dict[str, object]:
        cases = [
            {"id": f"case-{index}", "required_states": ["base", "interaction"]}
            for index in range(1, count + 1)
        ]
        return {"splits": {"development": cases}}

    def test_each_case_requires_thirty_variant_screenshots(self) -> None:
        inventory = evidence.expected_inventory(self.manifest(2), "development")
        self.assertEqual(60, len(inventory))
        self.assertEqual(30, len([item for item in inventory if item[1] == "case-1"]))

    def test_fast_gate_requires_exact_development_inventory(self) -> None:
        inventory = evidence.expected_inventory(self.manifest(2), "development", "fast")
        self.assertEqual(16, len(inventory))
        self.assertEqual({"accepted", "candidate"}, {item[0] for item in inventory})
        self.assertEqual({"base", "interaction"}, {item[2] for item in inventory})
        self.assertEqual({"desktop", "mobile"}, {item[3] for item in inventory})
        self.assertEqual({"chromium"}, {item[4] for item in inventory})

    def test_unknown_gate_fails_closed(self) -> None:
        with self.assertRaisesRegex(evidence.V7EvidenceError, "unknown visual gate"):
            evidence.expected_inventory(self.manifest(2), "development", "partial")

    def test_cli_without_required_arguments_fails_closed(self) -> None:
        with mock.patch("sys.argv", [str(MODULE)]), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                evidence.main()
        self.assertEqual(raised.exception.code, 2)

    def test_validator_rejects_mixed_gate_before_artifact_scan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manifest_path = root / "manifest.json"
            manifest_path.write_text("{}", encoding="utf-8")
            ledger_path = root / "ledger.json"
            ledger_path.write_text("{}", encoding="utf-8")
            result_dir = root / "results"
            screenshot_dir = root / "screenshots"
            result_dir.mkdir()
            screenshot_dir.mkdir()
            manifest = self.manifest(2)
            ledger = {
                "schema_version": 1,
                "cohort_manifest": {
                    "path": "manifest.json",
                    "sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                },
                "split": "development",
                "gate": "fast",
                "status": "completed",
                "variants": list(evidence.VARIANTS),
                "expected_count": 16,
                "hidden_matrix_sha256": "0" * 64,
                "input_inventory_sha256": "0" * 64,
                "attempts": [],
            }
            with (
                mock.patch.object(evidence.preflight, "validate_manifest"),
                mock.patch.object(evidence, "_load", side_effect=[manifest, ledger]),
                self.assertRaisesRegex(evidence.V7EvidenceError, "gate does not match"),
            ):
                evidence.validate(
                    manifest_path,
                    ledger_path,
                    result_dir,
                    screenshot_dir,
                    root,
                    "full",
                )

    def test_base_uses_six_chromium_profiles(self) -> None:
        inventory = evidence.expected_inventory(self.manifest(1), "development")
        accepted_base = [item for item in inventory if item[0] == "accepted" and item[2] == "base"]
        self.assertEqual(6, len(accepted_base))
        self.assertEqual({"chromium"}, {item[4] for item in accepted_base})
        self.assertEqual(set(evidence.BASE_PROFILES), {item[3] for item in accepted_base})

    def test_interaction_uses_three_profiles_and_engines(self) -> None:
        inventory = evidence.expected_inventory(self.manifest(1), "development")
        accepted = [item for item in inventory if item[0] == "accepted" and item[2] == "interaction"]
        self.assertEqual(9, len(accepted))
        self.assertEqual(set(evidence.PARITY_PROFILES), {item[3] for item in accepted})
        self.assertEqual(set(evidence.PARITY_ENGINES), {item[4] for item in accepted})

    def test_missing_required_state_fails_closed(self) -> None:
        manifest = self.manifest(1)
        manifest["splits"]["development"][0]["required_states"] = ["base", "hover"]
        with self.assertRaisesRegex(evidence.V7EvidenceError, "base and interaction"):
            evidence.expected_inventory(manifest, "development")

    def test_real_decoded_png_and_matching_result_are_accepted(self) -> None:
        with self.subTest("full PNG decode"), tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            key = ("accepted", "case-one", "base", "desktop", "chromium")
            screenshot = root / f"{evidence.artifact_stem(key)}.png"
            screenshot.write_bytes(self.png())
            screenshot_hash = hashlib.sha256(screenshot.read_bytes()).hexdigest()
            result = root / f"{evidence.artifact_stem(key)}.json"
            payload = {
                "schemaVersion": 1,
                "identity": {"variant": "accepted", "caseId": "case-one", "state": "base", "profile": "desktop", "engine": "chromium"},
                "input": {"scheme": "file", "route": "index.html", "specSha256": "0" * 64},
                "browser": {
                    "playwright": "1.61.1",
                    "engineVersion": "test",
                    "profile": {
                        "width": 1440,
                        "height": 1000,
                        "hasTouch": False,
                        "isMobile": False,
                        "deviceScaleFactor": 1,
                        "fullMobileEmulation": False,
                        "userAgent": "test",
                    },
                },
                "runtime": {
                    "fontsReady": True,
                    "interactions": [],
                    "assertions": [],
                    "consoleErrors": [],
                    "pageErrors": [],
                    "externalRequests": [],
                    "pageBounds": {"width": 1440, "height": 1000},
                    "devicePixelArea": 1440000,
                    "horizontalOverflow": False,
                    "eventOverflow": False,
                    "eventCounts": {"consoleErrors": 0, "pageErrors": 0, "externalRequests": 0},
                    "issues": [],
                },
                "typography": {"schemaVersion": 1, "issues": [], "observations": [], "targets": [], "environment": {}},
                "verdict": "clean",
                "screenshot": {
                    "path": screenshot.name,
                    "fullPage": True,
                    "width": 1440,
                    "height": 1000,
                    "bytes": screenshot.stat().st_size,
                    "sha256": screenshot_hash,
                },
            }
            result.write_text(json.dumps(payload), encoding="utf-8")
            result_hash = hashlib.sha256(result.read_bytes()).hexdigest()
            self.assertEqual(
                "clean",
                evidence._validate_result(key, result, screenshot, result_hash, screenshot_hash, "0" * 64, "1.61.1"),
            )
            unavailable_focus = copy.deepcopy(payload)
            unavailable_focus["schemaVersion"] = 2
            unavailable_focus["runtime"].update({
                "focusCoverage": {
                    "status": "unavailable",
                    "reason": "focus_targets_not_declared",
                    "declaredTargets": 0,
                    "completedTargets": 0,
                    "freshReplays": 0,
                    "claimBoundary": evidence.FOCUS_CLAIM_BOUNDARY,
                },
                "focusedControls": [],
            })
            result.write_text(json.dumps(unavailable_focus), encoding="utf-8")
            unavailable_hash = hashlib.sha256(result.read_bytes()).hexdigest()
            with self.assertRaisesRegex(evidence.V7EvidenceError, "at least one target"):
                evidence._validate_result(key, result, screenshot, unavailable_hash, screenshot_hash, "0" * 64, "1.61.1")
            unavailable_focus = copy.deepcopy(payload)
            unavailable_focus["schemaVersion"] = 2
            unavailable_focus["runtime"].update({
                "focusCoverage": {
                    "status": "unavailable",
                    "reason": "one_or_more_targets_unavailable",
                    "declaredTargets": 1,
                    "completedTargets": 0,
                    "freshReplays": 2,
                    "claimBoundary": evidence.FOCUS_CLAIM_BOUNDARY,
                },
                "focusedControls": [{
                    "id": "primary-submit",
                    "role": "primary-action",
                    "status": "unavailable",
                    "fullyObscured": False,
                    "replays": 2,
                    "reason": "external_request_blocked",
                }],
                "issues": ["focus_obscuration_verification_unavailable"],
            })
            unavailable_focus["verdict"] = "findings"
            result.write_text(json.dumps(unavailable_focus), encoding="utf-8")
            unavailable_focus_hash = hashlib.sha256(result.read_bytes()).hexdigest()
            self.assertEqual(
                "findings",
                evidence._validate_result(
                    key, result, screenshot, unavailable_focus_hash, screenshot_hash, "0" * 64, "1.61.1",
                ),
            )
            clear_focus = copy.deepcopy(payload)
            clear_focus["schemaVersion"] = 2
            clear_focus["runtime"].update({
                "focusCoverage": {
                    "status": "complete",
                    "reason": None,
                    "declaredTargets": 1,
                    "completedTargets": 1,
                    "freshReplays": 2,
                    "claimBoundary": evidence.FOCUS_CLAIM_BOUNDARY,
                },
                "focusedControls": [{
                    "id": "primary-submit",
                    "role": "primary-action",
                    "status": "clear",
                    "fullyObscured": False,
                    "replays": 2,
                    "occluderCount": 1,
                    "targetArea": 2400,
                    "coveredArea": 1200,
                }],
            })
            result.write_text(json.dumps(clear_focus), encoding="utf-8")
            clear_hash = hashlib.sha256(result.read_bytes()).hexdigest()
            self.assertEqual(
                "clean",
                evidence._validate_result(key, result, screenshot, clear_hash, screenshot_hash, "0" * 64, "1.61.1"),
            )
            forged_clear = copy.deepcopy(clear_focus)
            forged_clear["runtime"]["focusedControls"][0]["coveredArea"] = 2400
            result.write_text(json.dumps(forged_clear), encoding="utf-8")
            forged_clear_hash = hashlib.sha256(result.read_bytes()).hexdigest()
            with self.assertRaisesRegex(evidence.V7EvidenceError, "clear focused control is fully covered"):
                evidence._validate_result(key, result, screenshot, forged_clear_hash, screenshot_hash, "0" * 64, "1.61.1")
            obscured_focus = copy.deepcopy(payload)
            obscured_focus["schemaVersion"] = 2
            obscured_focus["runtime"].update({
                "focusCoverage": {
                    "status": "complete",
                    "reason": None,
                    "declaredTargets": 1,
                    "completedTargets": 1,
                    "freshReplays": 2,
                    "claimBoundary": evidence.FOCUS_CLAIM_BOUNDARY,
                },
                "focusedControls": [{
                    "id": "primary-submit",
                    "role": "primary-action",
                    "status": "confirmed",
                    "fullyObscured": True,
                    "replays": 2,
                    "occluderCount": 1,
                    "targetArea": 2400,
                    "coveredArea": 2400,
                }],
                "issues": ["focused_control_obscured"],
            })
            obscured_focus["verdict"] = "findings"
            result.write_text(json.dumps(obscured_focus), encoding="utf-8")
            obscured_hash = hashlib.sha256(result.read_bytes()).hexdigest()
            self.assertEqual(
                "findings",
                evidence._validate_result(key, result, screenshot, obscured_hash, screenshot_hash, "0" * 64, "1.61.1"),
            )
            forged_focus = copy.deepcopy(obscured_focus)
            forged_focus["runtime"]["focusedControls"][0]["coveredArea"] = 1200
            result.write_text(json.dumps(forged_focus), encoding="utf-8")
            forged_hash = hashlib.sha256(result.read_bytes()).hexdigest()
            with self.assertRaisesRegex(evidence.V7EvidenceError, "not fully covered"):
                evidence._validate_result(key, result, screenshot, forged_hash, screenshot_hash, "0" * 64, "1.61.1")
            interaction_key = ("accepted", "case-one", "interaction", "desktop", "chromium")
            payload["identity"]["state"] = "interaction"
            result.write_text(json.dumps(payload), encoding="utf-8")
            empty_interaction_hash = hashlib.sha256(result.read_bytes()).hexdigest()
            with self.assertRaisesRegex(evidence.V7EvidenceError, "interaction evidence must record"):
                evidence._validate_result(
                    interaction_key,
                    result,
                    screenshot,
                    empty_interaction_hash,
                    screenshot_hash,
                    "0" * 64,
                    "1.61.1",
                )
            payload["runtime"]["interactions"] = [{"id": "open-dialog", "action": "click", "completed": True}]
            payload["runtime"]["assertions"] = [{"id": "dialog-visible", "type": "visible", "count": 1, "passed": True}]
            result.write_text(json.dumps(payload), encoding="utf-8")
            passing_interaction_hash = hashlib.sha256(result.read_bytes()).hexdigest()
            self.assertEqual(
                "clean",
                evidence._validate_result(
                    interaction_key,
                    result,
                    screenshot,
                    passing_interaction_hash,
                    screenshot_hash,
                    "0" * 64,
                    "1.61.1",
                ),
            )
            payload["runtime"]["assertions"][0]["passed"] = False
            payload["verdict"] = "findings"
            result.write_text(json.dumps(payload), encoding="utf-8")
            failing_interaction_hash = hashlib.sha256(result.read_bytes()).hexdigest()
            self.assertEqual(
                "findings",
                evidence._validate_result(
                    interaction_key,
                    result,
                    screenshot,
                    failing_interaction_hash,
                    screenshot_hash,
                    "0" * 64,
                    "1.61.1",
                ),
            )
            payload["runtime"]["interactions"][0]["completed"] = False
            result.write_text(json.dumps(payload), encoding="utf-8")
            malformed_interaction_hash = hashlib.sha256(result.read_bytes()).hexdigest()
            with self.assertRaisesRegex(evidence.V7EvidenceError, "interaction step evidence is malformed"):
                evidence._validate_result(
                    interaction_key,
                    result,
                    screenshot,
                    malformed_interaction_hash,
                    screenshot_hash,
                    "0" * 64,
                    "1.61.1",
                )
            payload["identity"]["state"] = "base"
            payload["runtime"]["interactions"] = []
            payload["runtime"]["assertions"] = []
            payload["verdict"] = "clean"
            payload["typography"]["issues"] = [{"code": "tampered-finding"}]
            result.write_text(json.dumps(payload), encoding="utf-8")
            tampered_hash = hashlib.sha256(result.read_bytes()).hexdigest()
            with self.assertRaisesRegex(evidence.V7EvidenceError, "verdict does not match"):
                evidence._validate_result(key, result, screenshot, tampered_hash, screenshot_hash, "0" * 64, "1.61.1")


if __name__ == "__main__":
    unittest.main()
