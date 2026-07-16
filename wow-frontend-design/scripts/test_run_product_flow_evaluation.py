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
                self.assertTrue(path.with_name(f"{path.name}.failed-attempt-1").exists())
            command = popen.call_args.args[0]
            environment = popen.call_args.kwargs["env"]
            self.assertEqual("1", environment["PRODUCT_FLOW_VISUAL_REPAIR_ROUND"])
            self.assertEqual(
                str(target_root.with_name("targets.failed-attempt-1")),
                environment["PRODUCT_FLOW_REPAIR_SOURCE_ROOT"],
            )
            feedback = json.loads(environment["PRODUCT_FLOW_RETRY_FEEDBACK_BY_CASE"])
            self.assertIn("repair-cafe-intake-v6", feedback)
            self.assertIn("repair_failed", feedback["repair-cafe-intake-v6"])
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
                },
                report,
            )
        oral = feedback["oral-history-archive-v6"]
        packaging = feedback["packaging-configurator-v6"]
        self.assertIn("archive.html/desktop/base", oral)
        self.assertIn("trackRatio=0.51", oral)
        self.assertIn("summary.html/desktop/base", packaging)
        self.assertIn("overlaps='目前配置'", packaging)
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
            )["night-market-allergen-v6"]
        self.assertLessEqual(len(feedback), 500)
        self.assertNotIn("\n", feedback)
        self.assertNotIn("\x1b", feedback)
        self.assertIn("REPAIR REQUIRED: interaction_exception.", feedback)
        self.assertIn("interaction_exception@index.html/desktop/interaction", feedback)


if __name__ == "__main__":
    unittest.main()
