#!/usr/bin/env python3
"""Integration tests for current craft acceptance binding."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
sys.path.insert(0, str(ROOT / "wow-frontend-design" / "scripts"))

import evidence_ledger
import validate_current_craft_acceptance


CAPTURE = ROOT / "evals" / "capture_current_visual_evidence.cjs"
CORE = {"concept-coherence", "originality", "visual-typography"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_with_text_chunk(content: bytes) -> bytes:
    chunk_type = b"tEXt"
    payload = b"fresh-evidence\x00replacement"
    chunk = (
        struct.pack(">I", len(payload))
        + chunk_type
        + payload
        + struct.pack(">I", zlib.crc32(chunk_type + payload) & 0xFFFFFFFF)
    )
    return content[:-12] + chunk + content[-12:]


class CurrentCraftAcceptanceTests(unittest.TestCase):
    def build_fixture(
        self,
        root: Path,
        *,
        explicit_pages: list[str] | None = None,
        include_legacy_html: bool = False,
    ) -> tuple[Path, Path, Path, Path, Path, Path, Path]:
        root = root.resolve()
        workspace = root / "workspace"
        workspace.mkdir()
        brief = "建立可用且有辨識度的繁體中文產品介面。\n".encode()
        (workspace / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
        (workspace / "index.html").write_text(
            '<!doctype html><html lang="zh-Hant"><head><title>Current</title></head><body><main><h1>現行輸出</h1><p>Independent review.</p></main></body></html>',
            encoding="utf-8",
        )
        if include_legacy_html:
            (workspace / "legacy.html").write_text(
                '<!doctype html><html lang="zh-Hant"><body><main><h1>Legacy</h1></main></body></html>',
                encoding="utf-8",
            )
        for page in explicit_pages or []:
            artifact = workspace / page
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text(
                f'<!doctype html><html lang="zh-Hant"><body><main><h1>{page}</h1></main></body></html>',
                encoding="utf-8",
            )
        outputs = []
        output_names = ["DESIGN.md", "index.html"]
        if include_legacy_html:
            output_names.append("legacy.html")
        output_names.extend(explicit_pages or [])
        for name in output_names:
            artifact = workspace / name
            outputs.append({
                "path": name,
                "bytes": artifact.stat().st_size,
                "mode": f"{stat.S_IMODE(artifact.stat().st_mode):04o}",
                "sha256": digest(artifact),
            })
        manifest = {
            "schema_version": 2,
            "status": "completed",
            "brief": {"bytes": len(brief), "sha256": hashlib.sha256(brief).hexdigest()},
            "skill_snapshot": {"tree_sha256": "a" * 64},
            "outputs": outputs,
        }
        if explicit_pages is not None:
            manifest["case"] = {"mode": "retrofit", "lane_contract": "RETROFIT"}
            manifest["seed_snapshot"] = {
                "files": [],
                "directories": [],
                "tree_sha256": "a" * 64,
            }
            manifest["mutation"] = {
                "allowed_changes": ["DESIGN.md", *explicit_pages],
                "observed_changes": explicit_pages,
                "preserved_directories": 0,
            }
            manifest["html_verification"] = {
                "policy": "draft_direction_subset",
                "pages": explicit_pages,
            }
        manifest_path = workspace / "run-manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        case = {
            "schema_version": 1,
            "case_id": "private-validation-case",
            "run_id": "current-run-001",
            "partition": "validation",
            "brief": manifest["brief"],
            "capture_plan": {
                "locale": "zh-Hant",
                "state": "default",
                "pages": (
                    {
                        "policy": "draft_direction_subset",
                        "paths": explicit_pages,
                    }
                    if explicit_pages is not None
                    else "all_html_outputs"
                ),
                "wait_condition": "load+fonts+two-raf+300ms+two-raf",
                "profiles": [
                    {"name": "desktop-default", "viewport": {"width": 1440, "height": 1000}, "reducedMotion": "no-preference", "dpr": 1},
                    {"name": "mobile-default", "viewport": {"width": 390, "height": 844}, "reducedMotion": "reduce", "dpr": 1},
                ],
            },
            "craft": {
                "rubric_version": "wow-core-craft-v1",
                "required_dimensions": sorted(CORE),
                "feedback_policy": "aggregate-failure-families-only",
            },
        }
        case_path = root / "case.json"
        case_path.write_text(json.dumps(case), encoding="utf-8")
        evidence_root = root / "evidence"
        capture_command = [
            "node", str(CAPTURE), str(workspace), str(case_path), str(evidence_root)
        ]
        if explicit_pages is not None:
            convergence = root / "convergence.json"
            convergence.write_text(
                json.dumps({
                    "schema_version": 1,
                    "cohort_id": "private-validation-case",
                    "surface": "primary",
                    "variants": [
                        {
                            "id": Path(page).stem,
                            "page": page,
                        }
                        for page in explicit_pages
                    ],
                }),
                encoding="utf-8",
            )
            capture_command.append(str(convergence))
        captured = subprocess.run(
            capture_command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=45,
            check=False,
        )
        self.assertEqual(0, captured.returncode, captured.stderr)
        receipt_path = evidence_root / "capture-receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

        ledger = root / "ledger.json"
        policy_path = root / "policy.json"
        result_path = workspace / "quality-result.json"
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(0, evidence_ledger.main([
                "init", "--ledger", str(ledger), "--case-id", case["case_id"], "--run-id", case["run_id"]
            ]))

        policy_evidence: dict[str, dict] = {}
        capture_labels = [item["label"] for item in receipt["captures"]]
        ledger_paths = []
        for capture in receipt["captures"]:
            artifact = evidence_root / capture["path"]
            ledger_path = artifact.relative_to(root).as_posix()
            ledger_paths.append(ledger_path)
            context = capture["context"]
            args = [
                "artifact", "--ledger", str(ledger), "--label", capture["label"],
                "--kind", "screenshot", "--path", str(artifact),
                "--route", context["route"], "--viewport", context["viewport"],
                "--locale", context["locale"], "--state", context["state"], "--context", "dpr=1",
            ]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(0, evidence_ledger.main(args))
            claim_types = ["rendered_visual", *[f"craft:{dimension}" for dimension in sorted(CORE)]]
            if capture["profile"] == "mobile-default":
                claim_types.extend(["gate:rendered-mobile-layout", "novel-observation"])
            policy_evidence[capture["label"]] = {
                "kind": "artifact",
                "claim_types": claim_types,
                "artifact_kind": "screenshot",
                "path": ledger_path,
                "context": {
                    "route": context["route"],
                    "viewport": context["viewport"],
                    "locale": context["locale"],
                    "state": context["state"],
                    "note": "dpr=1",
                },
            }

        command = [sys.executable, "-c", "raise SystemExit(0)"]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(0, evidence_ledger.main([
                "run", "--ledger", str(ledger), "--label", "browser-critical-path",
                "--cwd", str(workspace), "--", *command,
            ]))
        policy_evidence["browser-critical-path"] = {
            "kind": "command",
            "claim_types": ["gate:primary-task"],
            "command": command,
            "command_sha256": evidence_ledger.canonical_command_sha256(command),
            "cwd": "workspace",
        }

        mobile = next(item for item in receipt["captures"] if item["profile"] == "mobile-default")
        novel = {
            "schema_version": 1,
            "status": "clean_after_probes",
            "probes": [{
                "id": "probe-current-mobile",
                "route": mobile["context"]["route"],
                "viewport": mobile["context"]["viewport"],
                "state": mobile["context"]["state"],
                "method": "fresh Playwright replay",
                "outcome": "pass",
                "evidence": [mobile["label"]],
            }],
            "findings": [],
        }
        novel_path = evidence_root / "novel-findings.json"
        novel_path.write_text(json.dumps(novel), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(0, evidence_ledger.main([
                "artifact", "--ledger", str(ledger), "--label", "novel-discovery",
                "--kind", "report", "--path", str(novel_path),
            ]))
        policy_evidence["novel-discovery"] = {
            "kind": "artifact",
            "claim_types": ["gate:novel-discovery"],
            "artifact_kind": "report",
            "path": novel_path.relative_to(root).as_posix(),
        }

        result = copy.deepcopy(json.loads(
            (ROOT / "wow-frontend-design" / "scripts" / "quality_result.example.json").read_text(encoding="utf-8")
        ))
        result["release"] = "VERIFIED"
        result["hard_gates"][0]["evidence"] = ["browser-critical-path"]
        result["hard_gates"][1]["evidence"] = [mobile["label"]]
        result["hard_gates"][2]["evidence"] = ["novel-discovery"]
        result["coverage"] = {"required_applicable": 3, "required_passed": 3, "evidence_items": 3}
        for dimension in result["craft"]["dimensions"]:
            if dimension["id"] in CORE:
                dimension["status"] = "ACCEPTABLE"
                dimension["evidence"] = capture_labels
            else:
                dimension["status"] = "UNVERIFIED"
                dimension["evidence"] = []
        result["handoff"]["rendered_evidence"] = {"status": "OBSERVED", "paths": ledger_paths, "reason": ""}
        result_path.write_text(json.dumps(result), encoding="utf-8")

        policy = {
            "schema_version": 3,
            "case_id": case["case_id"],
            "run_id": case["run_id"],
            "trust_boundary": {
                "evaluator_owned": True,
                "outside_model_write_scope": True,
                "integrity": "unsigned",
                "note": "Test evaluator boundary outside workspace.",
            },
            "release_acceptance": {
                "decision": "accepted_by_evaluator",
                "evaluator": "independent-current-reviewer",
                "record": "current-acceptance-001",
                "reason": "Fresh evidence and current output reviewed.",
            },
            "craft_review": {
                "evaluator_id": result["craft"]["evaluator_id"],
                "rubric_version": result["craft"]["rubric_version"],
                "dimensions": [copy.deepcopy(item) for item in result["craft"]["dimensions"] if item["id"] in CORE],
            },
            "evidence": policy_evidence,
        }
        policy_path.write_text(json.dumps(policy), encoding="utf-8")
        return result_path, ledger, policy_path, workspace, case_path, receipt_path, manifest_path

    def validate(self, fixture: tuple[Path, Path, Path, Path, Path, Path, Path]) -> int:
        return validate_current_craft_acceptance.validate_current_acceptance(*fixture)

    def test_accepts_only_exact_current_output_and_fresh_capture_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.build_fixture(Path(directory))
            self.assertEqual(3, self.validate(fixture))

    def test_capture_provenance_can_be_validated_before_independent_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.build_fixture(Path(directory))
            _, _, _, workspace, case_path, receipt_path, manifest_path = fixture
            observed = validate_current_craft_acceptance.validate_current_capture_evidence(
                workspace,
                case_path,
                receipt_path,
                manifest_path,
            )
            self.assertEqual(2, observed["capture_count"])

    def test_capture_provenance_accepts_an_explicit_manifest_page_subset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _, _, workspace, case, receipt, manifest = self.build_fixture(
                root,
                explicit_pages=[
                    "directions/editorial-index.html",
                    "directions/task-led-market.html",
                ],
                include_legacy_html=True,
            )

            observed = validate_current_craft_acceptance.validate_current_capture_evidence(
                workspace,
                case,
                receipt,
                manifest,
                allow_draft_subset=True,
            )

            self.assertEqual(4, observed["capture_count"])
            self.assertEqual(
                {
                    "directions/editorial-index.html",
                    "directions/task-led-market.html",
                },
                {item["page"] for item in observed["receipt"]["captures"]},
            )
            with self.assertRaisesRegex(
                validate_current_craft_acceptance.CurrentCraftError,
                "outside draft calibration",
            ):
                validate_current_craft_acceptance.validate_current_capture_evidence(
                    workspace, case, receipt, manifest
                )
            self.assertRegex(observed["capture_set_sha256"], r"^[a-f0-9]{64}$")
            self.assertEqual({"desktop-default", "mobile-default"}, {
                capture["profile"] for capture in observed["receipt"]["captures"]
            })

    def test_capture_evidence_rejects_symlink_receipt_and_duplicate_artifact_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.build_fixture(Path(directory))
            _, _, _, workspace, case_path, receipt_path, manifest_path = fixture
            linked = receipt_path.with_name("linked-receipt.json")
            linked.symlink_to(receipt_path)
            with self.assertRaisesRegex(validate_current_craft_acceptance.CurrentCraftError, "unaliased"):
                validate_current_craft_acceptance.validate_current_capture_evidence(
                    workspace, case_path, linked, manifest_path
                )

            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["captures"][1]["path"] = receipt["captures"][0]["path"]
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(validate_current_craft_acceptance.CurrentCraftError, "paths must be unique"):
                validate_current_craft_acceptance.validate_current_capture_evidence(
                    workspace, case_path, receipt_path, manifest_path
                )

    def test_capture_runtime_must_match_the_repository_playwright_pin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.build_fixture(Path(directory))
            receipt_path = fixture[5]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["runtime"]["version"] = "999.0.0-unpinned"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

            with self.assertRaisesRegex(
                validate_current_craft_acceptance.CurrentCraftError,
                "current Playwright Chromium standard",
            ):
                self.validate(fixture)

    def test_repository_playwright_pin_rejects_ranges_and_tags(self) -> None:
        for version in ("^1.61.1", "~1.61.1", "latest", "1.61"):
            with self.subTest(version=version), mock.patch.object(
                validate_current_craft_acceptance,
                "_load_json",
                return_value={"devDependencies": {"playwright": version}},
            ), self.assertRaisesRegex(
                validate_current_craft_acceptance.CurrentCraftError,
                "one exact version",
            ):
                validate_current_craft_acceptance._repository_playwright_version()

    def test_capture_evidence_rejects_parent_symlink_and_hardlink_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            fixture = self.build_fixture(root)
            _, _, _, workspace, case_path, receipt_path, manifest_path = fixture
            linked_parent = root / "linked-evidence"
            linked_parent.symlink_to(receipt_path.parent, target_is_directory=True)
            with self.assertRaisesRegex(validate_current_craft_acceptance.CurrentCraftError, "unaliased"):
                validate_current_craft_acceptance.validate_current_capture_evidence(
                    workspace,
                    case_path,
                    linked_parent / receipt_path.name,
                    manifest_path,
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            fixture = self.build_fixture(root)
            _, _, _, workspace, case_path, receipt_path, manifest_path = fixture
            hardlink = root / "hardlink-receipt.json"
            os.link(receipt_path, hardlink)
            with self.assertRaisesRegex(validate_current_craft_acceptance.CurrentCraftError, "unaliased"):
                validate_current_craft_acceptance.validate_current_capture_evidence(
                    workspace, case_path, hardlink, manifest_path
                )

    def test_capture_evidence_malformed_partition_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.build_fixture(Path(directory))
            _, _, _, workspace, case_path, receipt_path, manifest_path = fixture
            case = json.loads(case_path.read_text(encoding="utf-8"))
            case["partition"] = []
            case_path.write_text(json.dumps(case), encoding="utf-8")
            with self.assertRaisesRegex(
                validate_current_craft_acceptance.CurrentCraftError,
                "validation or test case",
            ):
                validate_current_craft_acceptance.validate_current_capture_evidence(
                    workspace, case_path, receipt_path, manifest_path
                )

    def test_capture_disappearance_fails_closed_without_private_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.build_fixture(Path(directory))
            _, _, _, workspace, case_path, receipt_path, manifest_path = fixture
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            artifact = receipt_path.parent / receipt["captures"][0]["path"]
            artifact.unlink()
            with self.assertRaises(validate_current_craft_acceptance.CurrentCraftError) as observed:
                validate_current_craft_acceptance.validate_current_capture_evidence(
                    workspace, case_path, receipt_path, manifest_path
                )
            self.assertNotIn(str(receipt_path.parent), str(observed.exception))

    def test_output_and_capture_records_are_schema_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.build_fixture(Path(directory))
            _, _, _, workspace, case_path, receipt_path, manifest_path = fixture
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            manifest["outputs"][0]["bytes"] = float(manifest["outputs"][0]["bytes"])
            manifest["outputs"][0]["mode"] = "PRIVATE"
            receipt["source"]["outputs"] = copy.deepcopy(manifest["outputs"])
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            receipt["source"]["run_manifest_sha256"] = digest(manifest_path)
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(validate_current_craft_acceptance.CurrentCraftError, "output provenance record"):
                validate_current_craft_acceptance.validate_current_capture_evidence(
                    workspace, case_path, receipt_path, manifest_path
                )

        with tempfile.TemporaryDirectory() as directory:
            fixture = self.build_fixture(Path(directory))
            _, _, _, workspace, case_path, receipt_path, manifest_path = fixture
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            manifest["outputs"].append(copy.deepcopy(manifest["outputs"][0]))
            receipt["source"]["outputs"] = copy.deepcopy(manifest["outputs"])
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            receipt["source"]["run_manifest_sha256"] = digest(manifest_path)
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(validate_current_craft_acceptance.CurrentCraftError, "paths must be unique"):
                validate_current_craft_acceptance.validate_current_capture_evidence(
                    workspace, case_path, receipt_path, manifest_path
                )

        with tempfile.TemporaryDirectory() as directory:
            fixture = self.build_fixture(Path(directory))
            _, _, _, workspace, case_path, receipt_path, manifest_path = fixture
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            capture = receipt["captures"][0]
            for field in ("bytes", "width", "height"):
                capture[field] = float(capture[field])
            capture["context"]["dpr"] = 1.0
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(validate_current_craft_acceptance.CurrentCraftError, "provenance fields"):
                validate_current_craft_acceptance.validate_current_capture_evidence(
                    workspace, case_path, receipt_path, manifest_path
                )

    def test_manifest_change_after_capture_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.build_fixture(Path(directory))
            manifest = fixture[-1]
            manifest.write_text(manifest.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(validate_current_craft_acceptance.CurrentCraftError, "changed after capture"):
                self.validate(fixture)

    def test_core_craft_cannot_ignore_one_of_the_fresh_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.build_fixture(Path(directory))
            policy_path = fixture[2]
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["craft_review"]["dimensions"][0]["evidence"] = policy["craft_review"]["dimensions"][0]["evidence"][:1]
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaisesRegex(validate_current_craft_acceptance.CurrentCraftError, "inspect every fresh capture"):
                self.validate(fixture)

    def test_capture_route_must_match_its_declared_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.build_fixture(Path(directory))
            receipt_path = fixture[5]
            policy_path = fixture[2]
            ledger_path = fixture[1]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            capture = receipt["captures"][0]
            capture["context"]["route"] = "/not-the-captured-page.html"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["evidence"][capture["label"]]["context"]["route"] = capture["context"]["route"]
            policy_path.write_text(json.dumps(policy), encoding="utf-8")

            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            event = next(item for item in ledger["events"] if item.get("label") == capture["label"])
            event["context"]["route"] = capture["context"]["route"]
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")

            with self.assertRaisesRegex(validate_current_craft_acceptance.CurrentCraftError, "route does not match"):
                self.validate(fixture)

    def test_capture_hardlink_alias_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.build_fixture(Path(directory))
            result_path, ledger_path, policy_path, _, _, receipt_path, _ = fixture
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            capture = receipt["captures"][0]
            original = receipt_path.parent / capture["path"]
            alias = original.with_name("hardlink-alias.png")
            os.link(original, alias)
            old_ledger_path = original.relative_to(ledger_path.parent).as_posix()
            new_ledger_path = alias.relative_to(ledger_path.parent).as_posix()
            capture["path"] = alias.relative_to(receipt_path.parent).as_posix()
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["evidence"][capture["label"]]["path"] = new_ledger_path
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            event = next(item for item in ledger["events"] if item.get("label") == capture["label"])
            event["path"] = new_ledger_path
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            result = json.loads(result_path.read_text(encoding="utf-8"))
            result["handoff"]["rendered_evidence"]["paths"] = [
                new_ledger_path if path == old_ledger_path else path
                for path in result["handoff"]["rendered_evidence"]["paths"]
            ]
            result_path.write_text(json.dumps(result), encoding="utf-8")

            with self.assertRaisesRegex(validate_current_craft_acceptance.CurrentCraftError, "unaliased regular file"):
                self.validate(fixture)

    def test_capture_symlink_alias_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.build_fixture(Path(directory))
            receipt_path = fixture[5]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            capture = receipt["captures"][0]
            original = receipt_path.parent / capture["path"]
            alias = original.with_name("symlink-alias.png")
            alias.symlink_to(original.name)
            capture["path"] = alias.relative_to(receipt_path.parent).as_posix()
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

            with self.assertRaisesRegex(validate_current_craft_acceptance.CurrentCraftError, "unaliased regular file"):
                self.validate(fixture)

    def test_screenshot_tampering_after_capture_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.build_fixture(Path(directory))
            receipt = json.loads(fixture[5].read_text(encoding="utf-8"))
            screenshot = fixture[5].parent / receipt["captures"][0]["path"]
            screenshot.write_bytes(screenshot.read_bytes() + b"tamper")
            with self.assertRaisesRegex(validate_current_craft_acceptance.CurrentCraftError, "provenance is invalid"):
                self.validate(fixture)

    def test_capture_receipt_and_latest_ledger_event_must_bind_the_same_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = self.build_fixture(Path(directory))
            ledger_path = fixture[1]
            receipt = json.loads(fixture[5].read_text(encoding="utf-8"))
            capture = receipt["captures"][0]
            artifact = fixture[5].parent / capture["path"]
            replacement = png_with_text_chunk(artifact.read_bytes())
            evidence_ledger.png_metadata(replacement)

            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            event = next(item for item in ledger["events"] if item.get("label") == capture["label"])
            event["bytes"] = len(replacement)
            event["sha256"] = hashlib.sha256(replacement).hexdigest()
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")

            original_load = validate_current_craft_acceptance._load_json
            swapped = False

            def swap_after_receipt_validation(path: Path, label: str) -> dict:
                nonlocal swapped
                value = original_load(path, label)
                if label == "quality result" and not swapped:
                    artifact.write_bytes(replacement)
                    swapped = True
                return value

            with mock.patch.object(
                validate_current_craft_acceptance,
                "_load_json",
                side_effect=swap_after_receipt_validation,
            ), self.assertRaisesRegex(
                validate_current_craft_acceptance.CurrentCraftError,
                "latest ledger artifact does not match the current capture receipt",
            ):
                self.validate(fixture)

    def test_validation_case_inside_authoring_repository_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory(dir=ROOT) as repository_directory:
            fixture = list(self.build_fixture(Path(directory)))
            public_case = Path(repository_directory) / "case.json"
            shutil.copyfile(fixture[4], public_case)
            fixture[4] = public_case
            with self.assertRaisesRegex(validate_current_craft_acceptance.CurrentCraftError, "outside the authoring repository"):
                self.validate(tuple(fixture))


if __name__ == "__main__":
    unittest.main()
