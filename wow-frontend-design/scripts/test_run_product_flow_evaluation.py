#!/usr/bin/env python3
"""Unit tests for the fail-closed product-flow evaluation runner."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from urllib.error import HTTPError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[2]
EVALS = ROOT / "evals"
sys.path.insert(0, str(EVALS))
MODULE_PATH = EVALS / "run_product_flow_evaluation.py"
SPEC = importlib.util.spec_from_file_location("run_product_flow_evaluation", MODULE_PATH)
assert SPEC and SPEC.loader
evaluation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluation)


def fake_png(width: int, height: int) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    pixels = b"".join(b"\x00" + (b"\x00" * width) for _ in range(height))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b"")


def write_completed_manifest(target: Path, provider: str, model: str, case_id: str) -> dict[str, object]:
    outputs = []
    for name in ("DESIGN.md", *evaluation.CASE_PAGES[case_id]):
        path = target / name
        outputs.append({"path": name, "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    runner_name = "run_claude_case.sh" if provider == "claude" else "run_codex_case.sh"
    runner = EVALS / runner_name
    validator = EVALS / "validate_visual_web_output.py"
    manifest = {
        "schema_version": 1,
        "status": "completed",
        "case": {"id": case_id, "target": str(target.resolve())},
        "model": {"requested_alias" if provider == "claude" else "requested_identifier": model},
        "runner": {"path": f"evals/{runner_name}", "sha256": hashlib.sha256(runner.read_bytes()).hexdigest()},
        "output_validator": {
            "path": "evals/validate_visual_web_output.py",
            "sha256": hashlib.sha256(validator.read_bytes()).hexdigest(),
        },
        "outputs": outputs,
    }
    if provider == "codex":
        manifest["provider"] = "openai-first-party-chatgpt-oauth"
    path = target / "run-manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return evaluation.matrix._manifest_receipt(target, manifest)


class ProductFlowEvaluationTests(unittest.TestCase):
    def test_visual_tool_resolution_reuses_pinned_package_and_provided_browser(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            chrome = root / "chrome"
            chrome.write_text("binary", encoding="utf-8")
            args = SimpleNamespace(
                target_root=root / "targets",
                chrome_executable=chrome,
                tool_install_max_attempts=3,
                capture_timeout_seconds=30,
                retry_delay_seconds=0,
            )
            with mock.patch.object(
                evaluation,
                "_probe_playwright",
                return_value={"version": evaluation.PLAYWRIGHT_VERSION, "executable": str(root / "unused")},
            ), mock.patch.object(
                evaluation, "_install_tool_with_retries", return_value=[{"attempt": 1, "exit_code": 0}]
            ), mock.patch.object(evaluation.shutil, "which", return_value="/usr/bin/npm"):
                environment = evaluation.resolve_visual_tools(args)
            self.assertIn("PATH", environment)
            record = json.loads((root / "targets" / ".tools" / "tool-resolution.json").read_text(encoding="utf-8"))
            self.assertEqual("installed_from_repository_lock", record["playwright"]["source"])
            self.assertEqual(evaluation.PLAYWRIGHT_LOCK["integrity"], record["playwright"]["lock"]["integrity"])
            self.assertEqual("provided", record["browser"]["source"])

    def test_visual_tool_resolution_installs_missing_package_in_evaluator_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            browser = root / "chromium"
            browser.write_text("binary", encoding="utf-8")
            args = SimpleNamespace(
                target_root=root / "targets",
                chrome_executable=None,
                tool_install_max_attempts=3,
                capture_timeout_seconds=30,
                retry_delay_seconds=0,
            )
            with (
                mock.patch.object(
                    evaluation,
                    "_probe_playwright",
                    return_value={"version": evaluation.PLAYWRIGHT_VERSION, "executable": str(browser)},
                ),
                mock.patch.object(evaluation, "_install_tool_with_retries", return_value=[{"attempt": 1, "exit_code": 0}]),
                mock.patch.object(evaluation.shutil, "which", return_value="/usr/bin/npm"),
            ):
                environment = evaluation.resolve_visual_tools(args)
            self.assertIn(str(root / "targets" / ".tools"), environment["NODE_PATH"])
            record = json.loads((root / "targets" / ".tools" / "tool-resolution.json").read_text(encoding="utf-8"))
            self.assertEqual("installed_from_repository_lock", record["playwright"]["source"])
            self.assertEqual("existing", record["browser"]["source"])

    def test_visual_tool_resolution_uses_real_cli_entrypoint_for_missing_browser(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing_browser = root / "missing-chromium"
            installed_browser = root / "chromium"
            installed_browser.write_text("binary", encoding="utf-8")
            args = SimpleNamespace(
                target_root=root / "targets",
                chrome_executable=None,
                tool_install_max_attempts=3,
                capture_timeout_seconds=30,
                retry_delay_seconds=0,
            )

            def fake_install(_args: object, command: list[str], _environment: object, _label: str) -> list[dict[str, int]]:
                if "ci" in command:
                    package_root = Path(command[command.index("--prefix") + 1])
                    cli = package_root / "node_modules" / "playwright" / "cli.js"
                    cli.parent.mkdir(parents=True)
                    cli.write_text("entrypoint", encoding="utf-8")
                return [{"attempt": 1, "exit_code": 0}]

            with (
                mock.patch.object(
                    evaluation,
                    "_probe_playwright",
                    side_effect=[
                        {"version": evaluation.PLAYWRIGHT_VERSION, "executable": str(missing_browser)},
                        {"version": evaluation.PLAYWRIGHT_VERSION, "executable": str(missing_browser)},
                        {"version": evaluation.PLAYWRIGHT_VERSION, "executable": str(installed_browser)},
                    ],
                ),
                mock.patch.object(evaluation, "_install_tool_with_retries", side_effect=fake_install) as install,
                mock.patch.object(evaluation.shutil, "which", return_value="/usr/bin/node"),
            ):
                evaluation.resolve_visual_tools(args)
            browser_command = install.call_args.args[1]
            self.assertEqual(["/usr/bin/node", browser_command[1], "install", "chromium"], browser_command)
            self.assertTrue(
                Path(browser_command[1]).resolve().is_relative_to((root / "targets" / ".tools").resolve())
            )
            record = json.loads((root / "targets" / ".tools" / "tool-resolution.json").read_text(encoding="utf-8"))
            self.assertEqual("installed", record["browser"]["source"])

    def test_tool_install_retries_transient_failure(self) -> None:
        args = SimpleNamespace(
            tool_install_max_attempts=2,
            capture_timeout_seconds=30,
            retry_delay_seconds=0,
        )
        outcomes = [
            evaluation.subprocess.CompletedProcess(["tool"], 1, "", "temporary registry error"),
            evaluation.subprocess.CompletedProcess(["tool"], 0, "installed", ""),
        ]
        with mock.patch.object(evaluation.matrix, "run_isolated", side_effect=outcomes):
            attempts = evaluation._install_tool_with_retries(args, ["tool"], {}, "tool")
        self.assertEqual([1, 0], [attempt["exit_code"] for attempt in attempts])

    def test_tool_record_write_does_not_follow_fixed_temporary_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tool_root = root / ".tools"
            tool_root.mkdir()
            victim = root / "victim.txt"
            victim.write_text("unchanged", encoding="utf-8")
            (tool_root / ".tool-resolution.json.tmp").symlink_to(victim)
            evaluation._write_tool_record(tool_root, {"status": "safe"})
            self.assertEqual("unchanged", victim.read_text(encoding="utf-8"))
            self.assertFalse((tool_root / "tool-resolution.json").is_symlink())
            self.assertEqual({"status": "safe"}, json.loads((tool_root / "tool-resolution.json").read_text()))

    def test_visual_capture_rejects_target_base_count_mismatch(self) -> None:
        args = SimpleNamespace(chrome_executable=None, capture_timeout_seconds=30)
        with self.assertRaisesRegex(evaluation.EvaluationError, "target/base counts disagree"):
            evaluation._run_visual_attempt(args, [{}], [], Path("visual.json"), Path("screenshots"))

    def test_local_server_exposes_only_allowlisted_pages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
            (target / "index.html").write_text("<main>allowed</main>", encoding="utf-8")
            (target / "secret.txt").write_text("not served", encoding="utf-8")
            targets = [
                {
                    "case_id": "wind-maintenance-dispatch-v6",
                    "alias": "claude-haiku",
                    "directory": target,
                }
            ]
            with evaluation.serve_targets(targets) as bases:
                with urlopen(f"{bases[0]}index.html", timeout=2) as response:
                    self.assertEqual(b"<main>allowed</main>", response.read())
                with self.assertRaises(HTTPError) as missing:
                    urlopen(f"{bases[0]}secret.txt", timeout=2)
                self.assertEqual(404, missing.exception.code)

    def test_visual_completion_requires_exact_screenshot_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            screenshots = root / "screenshots"
            screenshots.mkdir()
            targets = [
                {
                    "case_id": "wind-maintenance-dispatch-v6",
                    "alias": "claude-haiku",
                    "directory": root,
                }
            ]
            results = []
            for state, viewport in [
                *[("base", name) for name in evaluation.VIEWPORTS],
                ("interaction", "desktop"),
                ("interaction", "mobile"),
            ]:
                profile = evaluation.VIEWPORTS[viewport]
                width = int(profile["width"])
                height = int(profile["height"])
                scale = int(profile["deviceScaleFactor"])
                screenshot = screenshots / f"wind-maintenance-dispatch-v6-claude-haiku-index-{state}-{viewport}.png"
                screenshot.write_bytes(fake_png(width * scale, height * scale))
                results.append(
                    {
                        "caseId": "wind-maintenance-dispatch-v6",
                        "alias": "claude-haiku",
                        "page": "index.html",
                        "state": state,
                        "viewport": viewport,
                        "size": f"{width}x{height}",
                        "screenshot": str(screenshot),
                        "screenshotSha256": hashlib.sha256(screenshot.read_bytes()).hexdigest(),
                        "visualIssues": [],
                        "fontEvidence": {
                            "status": "captured",
                            "roles": [
                                {
                                    "role": "page-heading",
                                    "selector": "h1",
                                    "source": "dom-text",
                                    "pseudoDescendant": False,
                                    "textRunIndex": 0,
                                    "textNodeCount": 1,
                                    "declaredPrimary": "serif",
                                    "declaredPrimaryQuoted": False,
                                    "classification": "not_applicable",
                                    "fontStretch": "100%",
                                    "fontStyle": "normal",
                                    "fontWeight": "400",
                                    "probeSourceTextEmpty": False,
                                    "pseudoTextMappingUnavailable": False,
                                    "renderedTextMappingUnavailable": False,
                                    "probeTextComplete": True,
                                    "probeHasLetterOrNumber": True,
                                    "probeHasRelevantGlyph": True,
                                    "probeRelevantGlyphOverflow": False,
                                    "probeCodePoints": [65],
                                    "fontPaintVisible": True,
                                    "fontPaintEvidenceReliable": True,
                                    "fontProbeStable": True,
                                    "fontInventoryStable": True,
                                    "platformFontsStable": True,
                                    "browserGeneratedTextUnavailable": False,
                                    "declaredFaceCheck": True,
                                    "declaredFaceCheckReliable": True,
                                    "declaredFaceSelectionFailed": False,
                                    "declaredFaceSelectionUnavailable": False,
                                    "fontFaces": [],
                                    "actualFonts": [
                                        {
                                            "familyName": "Songti TC",
                                            "postScriptName": "SongtiTC-Regular",
                                            "glyphCount": 8,
                                        }
                                    ],
                                }
                            ],
                            "primaryMismatches": [],
                        },
                    }
                )
            report = root / "visual.json"
            generation = root / "generation.json"
            generation.write_text('{"status":"completed"}\n', encoding="utf-8")
            report.write_text(
                json.dumps(
                    {
                        "auditor": {
                            "sha256": hashlib.sha256(evaluation.VISUAL_AUDITOR.read_bytes()).hexdigest(),
                        },
                        "viewports": [
                            {"name": name, **profile}
                            for name, profile in evaluation.VIEWPORTS.items()
                        ],
                        "targets": [
                            {
                                "caseId": "wind-maintenance-dispatch-v6",
                                "alias": "claude-haiku",
                            }
                        ],
                        "results": results,
                        "summary": {"checkedPages": 6},
                    }
                ),
                encoding="utf-8",
            )
            (root / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
            (root / "index.html").write_text("<main></main>\n", encoding="utf-8")
            evaluation.bind_visual_report(report, generation, targets)
            self.assertEqual(6, evaluation.validate_visual_completion(report, screenshots, targets, generation))

            valid_payload = json.loads(report.read_text(encoding="utf-8"))
            unavailable_payload = json.loads(json.dumps(valid_payload))
            unavailable_result = unavailable_payload["results"][0]
            unavailable_result["fontEvidence"] = {
                "status": "unavailable",
                "error": "active rendered-text animation prevented stable evidence",
                "roles": [],
                "primaryMismatches": [],
            }
            unavailable_result["visualIssues"] = ["font_evidence_unavailable"]
            report.write_text(json.dumps(unavailable_payload), encoding="utf-8")
            self.assertEqual(6, evaluation.validate_visual_completion(report, screenshots, targets, generation))
            report.write_text(json.dumps(valid_payload), encoding="utf-8")
            generic_native = json.loads(json.dumps(valid_payload))
            generic_role = generic_native["results"][0]["fontEvidence"]["roles"][0]
            generic_role["declaredPrimary"] = "sans-serif"
            generic_role["classification"] = "not_applicable"
            generic_role["browserGeneratedTextUnavailable"] = True
            generic_role["renderedTextMappingUnavailable"] = True
            generic_role["pseudoTextMappingUnavailable"] = True
            generic_role["declaredFaceSelectionUnavailable"] = True
            report.write_text(json.dumps(generic_native), encoding="utf-8")
            self.assertEqual(6, evaluation.validate_visual_completion(report, screenshots, targets, generation))
            report.write_text(json.dumps(valid_payload), encoding="utf-8")
            invalid_payloads = []
            missing = json.loads(json.dumps(valid_payload))
            missing["results"][0].pop("fontEvidence")
            invalid_payloads.append(missing)
            unavailable = json.loads(json.dumps(valid_payload))
            unavailable["results"][0]["fontEvidence"]["status"] = "unavailable"
            invalid_payloads.append(unavailable)
            captured_gap = json.loads(json.dumps(valid_payload))
            captured_gap["results"][0]["visualIssues"] = ["font_evidence_unavailable"]
            invalid_payloads.append(captured_gap)
            empty_roles = json.loads(json.dumps(valid_payload))
            empty_roles["results"][0]["fontEvidence"]["roles"] = []
            invalid_payloads.append(empty_roles)
            unknown_classification = json.loads(json.dumps(valid_payload))
            unknown_classification["results"][0]["fontEvidence"]["roles"][0]["classification"] = "unknown"
            invalid_payloads.append(unknown_classification)
            unstable_probe = json.loads(json.dumps(valid_payload))
            unstable_probe["results"][0]["fontEvidence"]["roles"][0]["fontProbeStable"] = False
            invalid_payloads.append(unstable_probe)
            unstable_inventory = json.loads(json.dumps(valid_payload))
            unstable_inventory["results"][0]["fontEvidence"]["roles"][0]["fontInventoryStable"] = False
            invalid_payloads.append(unstable_inventory)
            invisible_paint = json.loads(json.dumps(valid_payload))
            invisible_paint["results"][0]["fontEvidence"]["roles"][0]["fontPaintVisible"] = False
            invalid_payloads.append(invisible_paint)
            unreliable_paint = json.loads(json.dumps(valid_payload))
            unreliable_paint["results"][0]["fontEvidence"]["roles"][0]["fontPaintEvidenceReliable"] = False
            invalid_payloads.append(unreliable_paint)
            unstable_platform_fonts = json.loads(json.dumps(valid_payload))
            unstable_platform_fonts["results"][0]["fontEvidence"]["roles"][0]["platformFontsStable"] = False
            invalid_payloads.append(unstable_platform_fonts)
            boolean_glyph_count = json.loads(json.dumps(valid_payload))
            boolean_glyph_count["results"][0]["fontEvidence"]["roles"][0]["actualFonts"][0]["glyphCount"] = True
            invalid_payloads.append(boolean_glyph_count)
            malformed_font_face = json.loads(json.dumps(valid_payload))
            malformed_font_face["results"][0]["fontEvidence"]["roles"][0]["fontFaces"] = ["not-a-font-face"]
            invalid_payloads.append(malformed_font_face)
            missing_text_run_source = json.loads(json.dumps(valid_payload))
            missing_text_run_source["results"][0]["fontEvidence"]["roles"][0].pop("source")
            invalid_payloads.append(missing_text_run_source)
            boolean_text_node_count = json.loads(json.dumps(valid_payload))
            boolean_text_node_count["results"][0]["fontEvidence"]["roles"][0]["textNodeCount"] = True
            invalid_payloads.append(boolean_text_node_count)
            semantic_font_tamper = json.loads(json.dumps(valid_payload))
            semantic_tamper_role = semantic_font_tamper["results"][0]["fontEvidence"]["roles"][0]
            semantic_tamper_role["declaredPrimary"] = "BrokenFace"
            semantic_tamper_role["declaredPrimaryQuoted"] = False
            semantic_tamper_role["classification"] = "rendered"
            semantic_tamper_role["declaredFaceSelectionFailed"] = True
            semantic_tamper_role["fontFaces"] = [{
                "family": "BrokenFace",
                "status": "error",
                "stretch": "normal",
                "style": "normal",
                "unicodeRange": "U+0-10FFFF",
                "weight": "400",
            }]
            invalid_payloads.append(semantic_font_tamper)
            consistent_semantic_tamper = json.loads(json.dumps(valid_payload))
            consistent_tamper_role = consistent_semantic_tamper["results"][0]["fontEvidence"]["roles"][0]
            consistent_tamper_role["declaredPrimary"] = "BrokenFace"
            consistent_tamper_role["declaredPrimaryQuoted"] = False
            consistent_tamper_role["classification"] = "fallback_rendered"
            consistent_tamper_role["declaredFaceCheck"] = False
            consistent_tamper_role["fontFaces"] = [{
                "family": "BrokenFace",
                "status": "error",
                "stretch": "normal",
                "style": "normal",
                "unicodeRange": "U+0-10FFFF",
                "weight": "400",
            }]
            invalid_payloads.append(consistent_semantic_tamper)
            hidden_unavailable_selection = json.loads(json.dumps(valid_payload))
            hidden_unavailable_selection["results"][0]["fontEvidence"]["roles"][0]["declaredFaceSelectionUnavailable"] = True
            invalid_payloads.append(hidden_unavailable_selection)
            missing_control_label = json.loads(json.dumps(valid_payload))
            missing_control_label_role = missing_control_label["results"][0]["fontEvidence"]["roles"][0]
            missing_control_label_role["classification"] = "rendered"
            missing_control_label_role["browserGeneratedTextUnavailable"] = True
            invalid_payloads.append(missing_control_label)
            uncertain_native_mapping = json.loads(json.dumps(valid_payload))
            uncertain_native_role = uncertain_native_mapping["results"][0]["fontEvidence"]["roles"][0]
            uncertain_native_role["classification"] = "rendered"
            uncertain_native_role["renderedTextMappingUnavailable"] = True
            invalid_payloads.append(uncertain_native_mapping)
            uncertain_pseudo_mapping = json.loads(json.dumps(valid_payload))
            uncertain_pseudo_role = uncertain_pseudo_mapping["results"][0]["fontEvidence"]["roles"][0]
            uncertain_pseudo_role["classification"] = "rendered"
            uncertain_pseudo_role["pseudoTextMappingUnavailable"] = True
            invalid_payloads.append(uncertain_pseudo_mapping)
            platform_unavailable = json.loads(json.dumps(valid_payload))
            platform_unavailable["results"][0]["fontEvidence"]["roles"][0]["classification"] = "platform_fonts_unavailable"
            invalid_payloads.append(platform_unavailable)
            stale_mismatch = json.loads(json.dumps(valid_payload))
            stale_mismatch["results"][0]["fontEvidence"]["primaryMismatches"] = [
                stale_mismatch["results"][0]["fontEvidence"]["roles"][0]
            ]
            invalid_payloads.append(stale_mismatch)
            missing_issue = json.loads(json.dumps(valid_payload))
            failed_role = missing_issue["results"][0]["fontEvidence"]["roles"][0]
            failed_role["classification"] = "failed_font_face"
            missing_issue["results"][0]["fontEvidence"]["primaryMismatches"] = [failed_role]
            invalid_payloads.append(missing_issue)
            stale_issue = json.loads(json.dumps(valid_payload))
            stale_issue["results"][0]["visualIssues"] = ["declared_primary_font_not_rendered"]
            invalid_payloads.append(stale_issue)
            for invalid_payload in invalid_payloads:
                report.write_text(json.dumps(invalid_payload), encoding="utf-8")
                with self.assertRaisesRegex(evaluation.EvaluationError, "font evidence"):
                    evaluation.validate_visual_completion(report, screenshots, targets, generation)
            report.write_text(json.dumps(valid_payload), encoding="utf-8")

            (screenshots / "extra.png").write_bytes(fake_png(1, 1))
            with self.assertRaisesRegex(evaluation.EvaluationError, "extra PNG"):
                evaluation.validate_visual_completion(report, screenshots, targets, generation)

    def test_visual_completion_rejects_stale_target_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.mkdir()
            (target / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
            (target / "index.html").write_text("<main>before</main>\n", encoding="utf-8")
            generation = root / "generation.json"
            generation.write_text('{"status":"completed"}\n', encoding="utf-8")
            report = root / "visual.json"
            report.write_text("{}\n", encoding="utf-8")
            targets = [{"case_id": "wind-maintenance-dispatch-v6", "alias": "claude-haiku", "directory": target}]
            evaluation.bind_visual_report(report, generation, targets)
            (target / "index.html").write_text("<main>after</main>\n", encoding="utf-8")
            with self.assertRaisesRegex(evaluation.EvaluationError, "target-input hashes disagree"):
                evaluation._validate_input_bindings(evaluation._load_json(report, "report"), generation, targets)

    def test_incomplete_generation_cannot_reach_visual_capture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "generation.json"
            ledger.write_text(
                json.dumps(
                    {
                        "status": "partial",
                        "selection": {"count": 1},
                        "results": [
                            {
                                "provider": "claude",
                                "model": "haiku",
                                "case_id": "repair-cafe-intake-v6",
                                "status": "timeout",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(evaluation.EvaluationError, "matrix is incomplete"):
                evaluation.completed_targets(ledger)

    def test_completed_targets_accepts_only_direct_children_of_artifact_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact_root = Path(directory) / "targets"
            artifact_root.mkdir()
            target = artifact_root / "claude-haiku-repair-cafe-intake-v6"
            target.mkdir()
            (target / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
            (target / "index.html").write_text("<main></main>", encoding="utf-8")
            receipt = write_completed_manifest(target, "claude", "haiku", "repair-cafe-intake-v6")
            ledger = Path(directory) / "generation.json"
            record = {
                "provider": "claude",
                "model": "haiku",
                "case_id": "repair-cafe-intake-v6",
                "status": "completed",
                "target": str(target),
                "receipt": receipt,
            }
            ledger.write_text(
                json.dumps(
                    {
                        "status": "completed",
                        "contract": {"artifact_root": str(artifact_root)},
                        "selection": {"count": 1},
                        "results": [record],
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(target.resolve(), evaluation.completed_targets(ledger)[0]["directory"])

            escaped = Path(directory) / "claude-haiku-repair-cafe-intake-v6"
            escaped.mkdir()
            (escaped / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
            (escaped / "index.html").write_text("<main></main>", encoding="utf-8")
            record["receipt"] = write_completed_manifest(escaped, "claude", "haiku", "repair-cafe-intake-v6")
            record["target"] = str(escaped)
            ledger.write_text(
                json.dumps(
                    {
                        "status": "completed",
                        "contract": {"artifact_root": str(artifact_root)},
                        "selection": {"count": 1},
                        "results": [record],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(evaluation.EvaluationError, "escapes the artifact root"):
                evaluation.completed_targets(ledger)

    def test_design_completion_rejects_findings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            design = target / "DESIGN.md"
            design.write_text("# Design\n", encoding="utf-8")
            generation = target / "generation.json"
            generation.write_text('{"status":"completed"}\n', encoding="utf-8")
            report = target / "design.json"
            report.write_text(
                json.dumps(
                    {
                        "generation_ledger": {
                            "path": str(generation.resolve()),
                            "sha256": hashlib.sha256(generation.read_bytes()).hexdigest(),
                        },
                        "linter": {"package": "@google/design.md", "version": evaluation.DESIGN_MD_VERSION},
                        "results": [
                            {
                                "provider": "claude",
                                "model": "haiku",
                                "case_id": "repair-cafe-intake-v6",
                                "path": str(design.resolve()),
                                "sha256": hashlib.sha256(design.read_bytes()).hexdigest(),
                                "status": "findings",
                                "summary": {"errors": 0, "warnings": 1, "infos": 0},
                                "findings": [{"severity": "warning", "message": "needs repair"}],
                            }
                        ],
                        "summary": {
                            "checked": 1,
                            "clean": 0,
                            "with_findings": 1,
                            "infrastructure_failures": 0,
                        },
                    }
                ),
                encoding="utf-8",
            )
            targets = [
                {
                    "case_id": "repair-cafe-intake-v6",
                    "alias": "claude-haiku",
                    "directory": target,
                }
            ]
            with self.assertRaisesRegex(evaluation.DesignFindingsError, "repair required"):
                evaluation.validate_design_completion(report, targets, generation)

    def test_design_findings_are_forwarded_as_bounded_repair_feedback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            design = target / "DESIGN.md"
            design.write_text("# Design\n", encoding="utf-8")
            generation = target / "generation.json"
            generation.write_text('{"status":"completed"}\n', encoding="utf-8")
            report = target / "design.json"
            report.write_text(
                json.dumps(
                    {
                        "generation_ledger": {
                            "path": str(generation.resolve()),
                            "sha256": hashlib.sha256(generation.read_bytes()).hexdigest(),
                        },
                        "linter": {"package": "@google/design.md", "version": evaluation.DESIGN_MD_VERSION},
                        "results": [
                            {
                                "provider": "claude",
                                "model": "haiku",
                                "case_id": "repair-cafe-intake-v6",
                                "path": str(design.resolve()),
                                "sha256": hashlib.sha256(design.read_bytes()).hexdigest(),
                                "status": "findings",
                                "summary": {"errors": 1, "warnings": 0, "infos": 0},
                                "findings": [
                                    {"severity": "error", "message": "A" * 600},
                                ],
                            }
                        ],
                        "summary": {
                            "checked": 1,
                            "clean": 0,
                            "with_findings": 1,
                            "infrastructure_failures": 0,
                        },
                    }
                ),
                encoding="utf-8",
            )
            targets = [{"case_id": "repair-cafe-intake-v6", "alias": "claude-haiku", "directory": target}]
            with self.assertRaises(evaluation.DesignFindingsError) as raised:
                evaluation.validate_design_completion(report, targets, generation)
            findings = raised.exception.findings
            self.assertIn("repair-cafe-intake-v6:claude-haiku", findings)
            feedback = evaluation._design_repair_feedback(findings)
            self.assertIn("repair-cafe-intake-v6:claude-haiku", feedback)
            self.assertLessEqual(len(feedback["repair-cafe-intake-v6:claude-haiku"]), 500)
            self.assertIn("error:", feedback["repair-cafe-intake-v6:claude-haiku"])

    def test_design_status_must_match_summary_and_findings_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            design = target / "DESIGN.md"
            design.write_text("# Design\n", encoding="utf-8")
            generation = target / "generation.json"
            generation.write_text('{"status":"completed"}\n', encoding="utf-8")
            report = target / "design.json"
            report.write_text(
                json.dumps(
                    {
                        "generation_ledger": {
                            "path": str(generation.resolve()),
                            "sha256": hashlib.sha256(generation.read_bytes()).hexdigest(),
                        },
                        "linter": {"package": "@google/design.md", "version": evaluation.DESIGN_MD_VERSION},
                        "results": [
                            {
                                "provider": "claude",
                                "model": "haiku",
                                "case_id": "repair-cafe-intake-v6",
                                "path": str(design.resolve()),
                                "sha256": hashlib.sha256(design.read_bytes()).hexdigest(),
                                "status": "clean",
                                "summary": {"errors": 1, "warnings": 0, "infos": 0},
                                "findings": [{"severity": "error", "message": "invalid"}],
                            }
                        ],
                        "summary": {"checked": 1, "clean": 1, "with_findings": 0, "infrastructure_failures": 0},
                    }
                ),
                encoding="utf-8",
            )
            targets = [{"case_id": "repair-cafe-intake-v6", "alias": "claude-haiku", "directory": target}]
            with self.assertRaisesRegex(evaluation.EvaluationError, "status disagrees"):
                evaluation.validate_design_completion(report, targets, generation)

            payload = json.loads(report.read_text(encoding="utf-8"))
            payload["results"][0]["status"] = "findings"
            payload["results"][0]["findings"] = [{"severity": True, "message": "invalid"}]
            payload["summary"] = {"checked": 1, "clean": 0, "with_findings": 1, "infrastructure_failures": 0}
            report.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(evaluation.EvaluationError, "findings are malformed"):
                evaluation.validate_design_completion(report, targets, generation)

            payload["results"][0]["findings"] = [{"severity": "error", "message": "MUST_NOT_PASS"}]
            payload["results"][0]["summary"] = {"errors": 0, "warnings": 0, "infos": 0}
            payload["results"][0]["status"] = "clean"
            payload["summary"] = {"checked": 1, "clean": 1, "with_findings": 0, "infrastructure_failures": 0}
            report.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(evaluation.EvaluationError, "findings disagree"):
                evaluation.validate_design_completion(report, targets, generation)

            payload["results"][0]["findings"] = [{"severity": [], "message": "x"}]
            report.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(evaluation.EvaluationError, "findings are malformed"):
                evaluation.validate_design_completion(report, targets, generation)

    def test_design_repair_archives_evidence_and_starts_fresh_round(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target_root = root / "targets"
            target_root.mkdir()
            (target_root / "target.txt").write_text("original target", encoding="utf-8")
            generation = root / "generation.json"
            design = root / "design.json"
            for path in (generation, design):
                path.write_text("{}\n", encoding="utf-8")
            args = SimpleNamespace(
                provider="codex",
                model="gpt-5.4-mini",
                theme="all",
                target_root=target_root,
                generation_output=generation,
                design_output=design,
                visual_output=root / "visual.json",
                screenshot_dir=root / "screenshots",
                timeout_seconds=1800,
                max_attempts=3,
                retry_delay_seconds=0,
                capture_max_attempts=3,
                capture_timeout_seconds=300,
                lint_max_attempts=3,
                lint_timeout_seconds=180,
                tool_install_max_attempts=3,
                design_repair_max_rounds=2,
                design_repair_round=0,
                visual_repair_max_rounds=2,
                visual_repair_round=0,
                chrome_executable=None,
            )
            process = mock.Mock()
            process.wait.return_value = 0
            findings = {"repair-cafe-intake-v6:codex-gpt-5.4-mini": ["error: missing tokens"]}
            with (
                mock.patch.object(evaluation, "_prepare_selective_repair_state", return_value=0) as prepare,
                mock.patch.object(evaluation.subprocess, "Popen", return_value=process) as popen,
            ):
                status = evaluation._run_design_repair(args, findings, generation, design, target_root)
            self.assertEqual(0, status)
            for path in (target_root, generation, design):
                self.assertFalse(path.exists())
                self.assertTrue(path.with_name(f"{path.name}.failed-design-attempt-1").exists())
            environment = popen.call_args.kwargs["env"]
            self.assertEqual("1", environment["PRODUCT_FLOW_DESIGN_REPAIR_ROUND"])
            self.assertEqual(
                str(target_root.with_name("targets.failed-design-attempt-1")),
                environment["PRODUCT_FLOW_REPAIR_SOURCE_ROOT"],
            )
            feedback = json.loads(environment["PRODUCT_FLOW_RETRY_FEEDBACK_BY_CASE"])
            self.assertIn("missing tokens", feedback["repair-cafe-intake-v6:codex-gpt-5.4-mini"])
            command = popen.call_args.args[0]
            self.assertEqual("1", command[command.index("--design-repair-round") + 1])
            self.assertIn("--resume", command)
            prepare.assert_called_once()

    def test_design_completion_rejects_stale_design_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            design = target / "DESIGN.md"
            design.write_text("# Before\n", encoding="utf-8")
            generation = target / "generation.json"
            generation.write_text('{"status":"completed"}\n', encoding="utf-8")
            report = target / "design.json"
            report.write_text(
                json.dumps(
                    {
                        "generation_ledger": {
                            "path": str(generation.resolve()),
                            "sha256": hashlib.sha256(generation.read_bytes()).hexdigest(),
                        },
                        "linter": {"package": "@google/design.md", "version": evaluation.DESIGN_MD_VERSION},
                        "results": [
                            {
                                "provider": "claude",
                                "model": "haiku",
                                "case_id": "repair-cafe-intake-v6",
                                "path": str(design.resolve()),
                                "sha256": hashlib.sha256(design.read_bytes()).hexdigest(),
                                "status": "clean",
                                "summary": {"errors": 0, "warnings": 0, "infos": 0},
                            }
                        ],
                        "summary": {"checked": 1, "clean": 1, "with_findings": 0, "infrastructure_failures": 0},
                    }
                ),
                encoding="utf-8",
            )
            design.write_text("# After\n", encoding="utf-8")
            targets = [{"case_id": "repair-cafe-intake-v6", "alias": "claude-haiku", "directory": target}]
            with self.assertRaisesRegex(evaluation.EvaluationError, "input hash disagrees"):
                evaluation.validate_design_completion(report, targets, generation)

    def test_visual_findings_separate_execution_from_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "visual.json"
            report.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "caseId": "wind-maintenance-dispatch-v6",
                                "alias": "codex-gpt-5.4",
                                "visualIssues": ["critical_text_collision"],
                            }
                        ],
                        "crossPageComparisons": [],
                        "summary": {"verdict": "observed_issues"},
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                {"wind-maintenance-dispatch-v6:codex-gpt-5.4": ["critical_text_collision"]},
                evaluation.blocking_visual_findings(report),
            )
            self.assertEqual(
                "wind-maintenance-dispatch-v6:codex-gpt-5.4=critical_text_collision",
                evaluation.repair_summary(evaluation.blocking_visual_findings(report)),
            )

    def test_visual_evidence_gaps_are_unverified_not_product_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "visual.json"
            gap = {
                "page": "index.html",
                "state": "interaction",
                "viewport": "desktop",
                "screenshot": "/tmp/font-gap.png",
                "error": "active rendered-text animation prevented stable evidence",
            }
            report.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "caseId": "wind-maintenance-dispatch-v6",
                                "alias": "codex-gpt-5.4",
                                "page": "index.html",
                                "state": "interaction",
                                "viewport": "desktop",
                                "screenshot": gap["screenshot"],
                                "visualIssues": ["font_evidence_unavailable"],
                                "fontEvidence": {
                                    "status": "unavailable",
                                    "error": gap["error"],
                                    "roles": [],
                                    "primaryMismatches": [],
                                },
                            }
                        ],
                        "crossPageComparisons": [],
                        "summary": {
                            "verdict": "evidence_unavailable",
                            "advisoryCount": 0,
                            "targetsWithAdvisories": 0,
                            "advisoriesByTarget": {},
                            "evidenceGapCount": 1,
                            "targetsWithEvidenceGaps": 1,
                            "evidenceGapsByTarget": {
                                "wind-maintenance-dispatch-v6:codex-gpt-5.4": [gap]
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual({}, evaluation.blocking_visual_findings(report))
            self.assertEqual(
                {"wind-maintenance-dispatch-v6:codex-gpt-5.4": [gap]},
                evaluation.visual_evidence_gaps(report),
            )

    def test_evidence_only_issue_cannot_hide_in_cross_page_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "visual.json"
            report.write_text(
                json.dumps(
                    {
                        "results": [],
                        "crossPageComparisons": [
                            {
                                "caseId": "wind-maintenance-dispatch-v6",
                                "alias": "codex-gpt-5.4",
                                "visualIssues": ["font_evidence_unavailable"],
                            }
                        ],
                        "summary": {
                            "verdict": "no_observed_issues",
                            "evidenceGapCount": 0,
                            "targetsWithEvidenceGaps": 0,
                            "evidenceGapsByTarget": {},
                        },
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                evaluation.EvaluationError,
                "evidence-only visual issue must be attached to a page result",
            ):
                evaluation.blocking_visual_findings(report)

    def test_visual_advisories_are_disclosed_without_becoming_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "visual.json"
            advisory = {
                "page": "index.html",
                "state": "base",
                "viewport": "desktop",
                "screenshot": "/tmp/advisory.png",
                "confidence": "dense-independent-column",
                "voidHeight": 640,
            }
            report.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "caseId": "wind-maintenance-dispatch-v6",
                                "alias": "codex-gpt-5.4",
                                "page": "index.html",
                                "state": "base",
                                "viewport": "desktop",
                                "screenshot": "/tmp/advisory.png",
                                "visualIssues": [],
                                "layoutFlow": {"unfilledColumnAdvisories": [advisory]},
                            }
                        ],
                        "crossPageComparisons": [],
                        "summary": {
                            "verdict": "advisories_present",
                            "advisoryCount": 1,
                            "targetsWithAdvisories": 1,
                            "advisoriesByTarget": {
                                "wind-maintenance-dispatch-v6:codex-gpt-5.4": [advisory]
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual({}, evaluation.blocking_visual_findings(report))
            self.assertEqual(1, evaluation.visual_advisory_count(report))
            data = json.loads(report.read_text(encoding="utf-8"))
            data["summary"]["verdict"] = "no_observed_issues"
            report.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(evaluation.EvaluationError, "advisory count disagrees|advisory evidence disagrees|verdict disagrees"):
                evaluation.blocking_visual_findings(report)

    def test_visual_findings_archive_evidence_and_start_fresh_repair(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target_root = root / "targets"
            screenshot_dir = root / "screenshots"
            target_root.mkdir()
            screenshot_dir.mkdir()
            (target_root / "target.txt").write_text("original target", encoding="utf-8")
            (screenshot_dir / "screen.png").write_bytes(fake_png(2, 2))
            generation = root / "generation.json"
            design = root / "design.json"
            visual = root / "visual.json"
            for path in (generation, design, visual):
                path.write_text("{}\n", encoding="utf-8")
            args = SimpleNamespace(
                provider="codex",
                model="gpt-5.4-mini",
                theme="all",
                target_root=target_root,
                generation_output=generation,
                design_output=design,
                visual_output=visual,
                screenshot_dir=screenshot_dir,
                timeout_seconds=1800,
                max_attempts=3,
                retry_delay_seconds=0,
                capture_max_attempts=3,
                capture_timeout_seconds=300,
                lint_max_attempts=3,
                lint_timeout_seconds=180,
                tool_install_max_attempts=3,
                visual_repair_max_rounds=2,
                visual_repair_round=0,
                chrome_executable=None,
            )
            process = mock.Mock()
            process.wait.return_value = 0
            findings = {"repair-cafe-intake-v6:codex-gpt-5.4-mini": ["repair_failed"]}
            with (
                mock.patch.object(evaluation, "_prepare_selective_repair_state", return_value=0) as prepare,
                mock.patch.object(evaluation.subprocess, "Popen", return_value=process) as popen,
            ):
                status = evaluation._run_visual_repair(
                    args,
                    findings,
                    generation,
                    design,
                    visual,
                    screenshot_dir,
                    target_root,
                )
            self.assertEqual(0, status)
            for path in (target_root, generation, design, visual, screenshot_dir):
                self.assertFalse(path.exists())
                self.assertTrue(path.with_name(f"{path.name}.failed-visual-attempt-1").exists())
            command = popen.call_args.args[0]
            environment = popen.call_args.kwargs["env"]
            self.assertEqual("1", environment["PRODUCT_FLOW_VISUAL_REPAIR_ROUND"])
            self.assertEqual(
                str(target_root.with_name("targets.failed-visual-attempt-1")),
                environment["PRODUCT_FLOW_REPAIR_SOURCE_ROOT"],
            )
            feedback = json.loads(environment["PRODUCT_FLOW_RETRY_FEEDBACK_BY_CASE"])
            self.assertIn("repair-cafe-intake-v6:codex-gpt-5.4-mini", feedback)
            self.assertIn("repair_failed", feedback["repair-cafe-intake-v6:codex-gpt-5.4-mini"])
            self.assertNotIn("PRODUCT_FLOW_RETRY_FEEDBACK", environment)
            self.assertEqual("1", command[command.index("--visual-repair-round") + 1])
            self.assertIn("--resume", command)
            prepare.assert_called_once()

    def test_selective_visual_repair_preserves_passing_target_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target_root = root / "targets"
            target_root.mkdir()
            case_ids = ("wind-maintenance-dispatch-v6", "repair-cafe-intake-v6")
            results = []
            for case_id in case_ids:
                target = target_root / f"codex-gpt-5.4-mini-{case_id}"
                target.mkdir()
                (target / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
                (target / "index.html").write_text("<main>verified</main>\n", encoding="utf-8")
                receipt = write_completed_manifest(target, "codex", "gpt-5.4-mini", case_id)
                results.append(
                    {
                        "provider": "codex",
                        "model": "gpt-5.4-mini",
                        "case_id": case_id,
                        "target": str(target),
                        "status": "completed",
                        "receipt": receipt,
                    }
                )
            generation = root / "generation.json"
            generation.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "status": "completed",
                        "finished_at": "2026-07-15T00:00:00Z",
                        "contract": {"artifact_root": str(target_root)},
                        "selection": {"count": 2},
                        "results": results,
                        "summary": {"completed": 2},
                    }
                ),
                encoding="utf-8",
            )
            archived_targets = root / "targets.failed-attempt-1"
            archived_generation = root / "generation.json.failed-attempt-1"
            target_root.rename(archived_targets)
            generation.rename(archived_generation)
            preserved = evaluation._prepare_selective_repair_state(
                archived_targets,
                archived_generation,
                target_root,
                generation,
                {"wind-maintenance-dispatch-v6:codex-gpt-5.4-mini": ["wind_record_inventory_invalid"]},
            )
            ledger = json.loads(generation.read_text(encoding="utf-8"))
            passing = target_root / "codex-gpt-5.4-mini-repair-cafe-intake-v6"
            failing = target_root / "codex-gpt-5.4-mini-wind-maintenance-dispatch-v6"
            self.assertEqual(1, preserved)
            self.assertTrue(passing.is_dir())
            self.assertFalse(failing.exists())
            self.assertEqual(["repair-cafe-intake-v6"], [result["case_id"] for result in ledger["results"]])
            self.assertEqual("existing_completed", ledger["results"][0]["status"])
            self.assertNotIn("summary", ledger)
            evaluation.matrix.verified_existing(
                passing,
                "codex",
                "gpt-5.4-mini",
                "repair-cafe-intake-v6",
                expected_receipt=ledger["results"][0]["receipt"],
            )

    def test_visual_repair_fuse_preserves_current_evidence(self) -> None:
        args = SimpleNamespace(visual_repair_round=2, visual_repair_max_rounds=2)
        with mock.patch.object(evaluation, "_archive_visual_repair_state") as archive:
            status = evaluation._run_visual_repair(
                args,
                {"case:model": ["same_failure"]},
                Path("generation.json"),
                Path("design.json"),
                Path("visual.json"),
                Path("screenshots"),
                Path("targets"),
            )
        self.assertEqual(1, status)
        archive.assert_not_called()

    def test_design_and_visual_repair_archives_use_distinct_namespaces(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [root / "targets", root / "generation.json", root / "design.json"]
            paths[0].mkdir()
            for path in paths[1:]:
                path.write_text("{}\n", encoding="utf-8")
            design_archive = evaluation._archive_visual_repair_state(paths, 1, phase="design")
            for path in paths:
                if path.suffix:
                    path.write_text("new\n", encoding="utf-8")
                else:
                    path.mkdir()
            visual_paths = [*paths, root / "visual.json", root / "screenshots"]
            visual_paths[-2].write_text("{}\n", encoding="utf-8")
            visual_paths[-1].mkdir()
            visual_archive = evaluation._archive_visual_repair_state(visual_paths, 1, phase="visual")
            self.assertNotEqual(design_archive[paths[0]], visual_archive[paths[0]])
            self.assertTrue(design_archive[paths[0]].name.endswith("failed-design-attempt-1"))
            self.assertTrue(visual_archive[paths[0]].name.endswith("failed-visual-attempt-1"))

    def test_visual_repair_feedback_includes_bounded_rendered_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "visual.json"
            report.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "caseId": "oral-history-archive-v6",
                                "page": "archive.html",
                                "viewport": "desktop",
                                "state": "base",
                                "visualIssues": ["prose_track_underfilled"],
                                "bodyFlow": {
                                    "underfilledProseBlocks": [
                                        {
                                            "text": "受訪者說，那一年最先記住的是繩索磨過木樁的聲音。",
                                            "trackRatio": 0.51,
                                            "unusedInline": 544,
                                        }
                                    ]
                                },
                            },
                            {
                                "caseId": "packaging-configurator-v6",
                                "page": "summary.html",
                                "viewport": "desktop",
                                "state": "base",
                                "visualIssues": ["fixed_or_sticky_content_obstruction"],
                                "fixedStickyObstructions": [
                                    {
                                        "position": "sticky",
                                        "overlaps": [{"text": "目前配置"}],
                                    }
                                ],
                            },
                            {
                                "caseId": "layout-void-v6",
                                "page": "story.html",
                                "viewport": "desktop",
                                "state": "base",
                                "visualIssues": ["layout_column_void"],
                                "layoutFlow": {
                                    "unfilledColumnVoids": [
                                        {
                                            "target": "article-copy",
                                            "voidHeight": 936,
                                            "threshold": 300,
                                            "parentDisplay": "grid",
                                            "parentWidth": 1180,
                                        }
                                    ]
                                },
                            },
                            {
                                "caseId": "small-text-v7",
                                "page": "details.html",
                                "viewport": "mobile",
                                "state": "base",
                                "visualIssues": ["readable_text_below_12px"],
                                "textScale": {
                                    "undersizedReadableText": [
                                        {"text": "這是一段需要持續閱讀的產品說明。", "fontSize": 11, "hook": "details"}
                                    ]
                                },
                            },
                            {
                                "caseId": "grant-review-board-v6",
                                "page": "index.html",
                                "viewport": "tablet",
                                "state": "base",
                                "visualIssues": ["paragraph_measure_too_wide"],
                                "readingRhythm": {
                                    "tooWide": [
                                        {
                                            "text": "港口木船記憶工坊偏向材料可追蹤，河岸口述史錄音站偏向記錄方式清楚。",
                                            "script": "cjk",
                                            "estimatedCharacters": 51,
                                            "limit": 48,
                                        }
                                    ]
                                },
                            },
                            {
                                "caseId": "type-foundry-specimen-v6",
                                "page": "index.html",
                                "viewport": "desktop",
                                "state": "base",
                                "visualIssues": ["declared_primary_font_not_rendered"],
                                "fontEvidence": {
                                    "primaryMismatches": [
                                        {
                                            "role": "specimen",
                                            "selector": "[data-eval='specimen'] p",
                                            "text": "繁中標點 ABC 0123 一起校對",
                                            "declaredPrimary": "BrokenFace",
                                            "actualFonts": [
                                                {
                                                    "familyName": "PingFang TC",
                                                    "postScriptName": "PingFangTC-Regular",
                                                }
                                            ],
                                        }
                                    ]
                                },
                            },
                        ],
                        "crossPageComparisons": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            feedback = evaluation.visual_repair_feedback(
                {
                    "oral-history-archive-v6:codex-gpt-5.4-mini": ["prose_track_underfilled"],
                    "packaging-configurator-v6:codex-gpt-5.4-mini": ["fixed_or_sticky_content_obstruction"],
                    "layout-void-v6:codex-gpt-5.4-mini": ["layout_column_void"],
                    "small-text-v7:codex-gpt-5.4-mini": ["readable_text_below_12px"],
                    "grant-review-board-v6:codex-gpt-5.4-mini": ["paragraph_measure_too_wide"],
                    "type-foundry-specimen-v6:codex-gpt-5.4-mini": ["declared_primary_font_not_rendered"],
                },
                report,
            )
        oral = feedback["oral-history-archive-v6:codex-gpt-5.4-mini"]
        packaging = feedback["packaging-configurator-v6:codex-gpt-5.4-mini"]
        layout_void = feedback["layout-void-v6:codex-gpt-5.4-mini"]
        small_text = feedback["small-text-v7:codex-gpt-5.4-mini"]
        grant = feedback["grant-review-board-v6:codex-gpt-5.4-mini"]
        font = feedback["type-foundry-specimen-v6:codex-gpt-5.4-mini"]
        self.assertIn("archive.html/desktop/base", oral)
        self.assertIn("trackRatio=0.51", oral)
        self.assertIn("summary.html/desktop/base", packaging)
        self.assertIn("overlaps='目前配置'", packaging)
        self.assertIn("story.html/desktop/base", layout_void)
        self.assertIn("voidHeight=936", layout_void)
        self.assertIn("target='article-copy'", layout_void)
        self.assertIn("details.html/mobile/base", small_text)
        self.assertIn("fontSize=11", small_text)
        self.assertIn("index.html/tablet/base", grant)
        self.assertIn("text='港口木船記憶工坊偏向材料可追蹤", grant)
        self.assertIn("script=cjk", grant)
        self.assertIn("estimatedCharacters=51", grant)
        self.assertIn("limit=48", grant)
        self.assertIn("narrow only this text element's inline measure", grant)
        self.assertIn("do not shorten its copy or change unrelated prose", grant)
        self.assertIn("role='specimen'", font)
        self.assertIn("declaredPrimary='BrokenFace'", font)
        self.assertIn("PingFang TC/PingFangTC-Regular", font)
        self.assertIn("fix this local @font-face", font)
        self.assertIn("keep fallbacks and copy unchanged", font)
        self.assertTrue(all(len(value) <= 500 and "\n" not in value for value in feedback.values()))

    def test_visual_repair_feedback_normalizes_long_interaction_exception(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "visual.json"
            issue = "interaction_exception:" + ("locator.click timeout\nCall log: \x1b[2mwaiting " * 80)
            report.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "caseId": "night-market-allergen-v6",
                                "page": "index.html",
                                "viewport": "desktop",
                                "state": "interaction",
                                "visualIssues": [issue],
                            }
                        ],
                        "crossPageComparisons": [],
                    }
                ),
                encoding="utf-8",
            )
            feedback = evaluation.visual_repair_feedback(
                {"night-market-allergen-v6:codex-gpt-5.4-mini": [issue]},
                report,
            )["night-market-allergen-v6:codex-gpt-5.4-mini"]
        self.assertLessEqual(len(feedback), 500)
        self.assertNotIn("\n", feedback)
        self.assertNotIn("\x1b", feedback)
        self.assertIn("REPAIR REQUIRED: interaction_exception.", feedback)
        self.assertIn("interaction_exception@index.html/desktop/interaction", feedback)


if __name__ == "__main__":
    unittest.main()
