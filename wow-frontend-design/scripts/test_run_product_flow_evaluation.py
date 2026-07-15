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
            ):
                environment = evaluation.resolve_visual_tools(args)
            self.assertIn("PATH", environment)
            record = json.loads((root / "targets" / ".tools" / "tool-resolution.json").read_text(encoding="utf-8"))
            self.assertEqual("existing", record["playwright"]["source"])
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
                    side_effect=[
                        evaluation.EvaluationError("missing"),
                        {"version": evaluation.PLAYWRIGHT_VERSION, "executable": str(browser)},
                    ],
                ),
                mock.patch.object(evaluation, "_install_tool_with_retries", return_value=[{"attempt": 1, "exit_code": 0}]),
                mock.patch.object(evaluation.shutil, "which", return_value="/usr/bin/npm"),
            ):
                environment = evaluation.resolve_visual_tools(args)
            self.assertIn(str(root / "targets" / ".tools"), environment["NODE_PATH"])
            record = json.loads((root / "targets" / ".tools" / "tool-resolution.json").read_text(encoding="utf-8"))
            self.assertEqual("installed", record["playwright"]["source"])
            self.assertEqual("existing", record["browser"]["source"])

    def test_visual_tool_resolution_uses_real_cli_entrypoint_for_missing_browser(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cli = root / "node_modules" / "playwright" / "cli.js"
            cli.parent.mkdir(parents=True)
            cli.write_text("entrypoint", encoding="utf-8")
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
            with (
                mock.patch.object(evaluation, "ROOT", root),
                mock.patch.object(
                    evaluation,
                    "_probe_playwright",
                    side_effect=[
                        {"version": evaluation.PLAYWRIGHT_VERSION, "executable": str(missing_browser)},
                        {"version": evaluation.PLAYWRIGHT_VERSION, "executable": str(missing_browser)},
                        {"version": evaluation.PLAYWRIGHT_VERSION, "executable": str(installed_browser)},
                    ],
                ),
                mock.patch.object(evaluation, "_install_tool_with_retries", return_value=[{"attempt": 1, "exit_code": 0}]) as install,
                mock.patch.object(evaluation.shutil, "which", return_value="/usr/bin/node"),
            ):
                evaluation.resolve_visual_tools(args)
            self.assertEqual(
                ["/usr/bin/node", str(cli), "install", "chromium"],
                install.call_args.args[1],
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

    def test_visual_capture_rejects_target_base_count_mismatch(self) -> None:
        args = SimpleNamespace(chrome_executable=None, capture_timeout_seconds=30)
        with self.assertRaisesRegex(evaluation.EvaluationError, "target/base counts disagree"):
            evaluation._run_visual_attempt(args, [{}], [], Path("visual.json"), Path("screenshots"))

    def test_local_server_exposes_only_allowlisted_pages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
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
            self.assertEqual(6, evaluation.validate_visual_completion(report, screenshots, targets))

            (screenshots / "extra.png").write_bytes(fake_png(1, 1))
            with self.assertRaisesRegex(evaluation.EvaluationError, "extra PNG"):
                evaluation.validate_visual_completion(report, screenshots, targets)

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
            (target / "index.html").write_text("<main></main>", encoding="utf-8")
            ledger = Path(directory) / "generation.json"
            record = {
                "provider": "claude",
                "model": "haiku",
                "case_id": "repair-cafe-intake-v6",
                "status": "completed",
                "target": str(target),
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
            (escaped / "index.html").write_text("<main></main>", encoding="utf-8")
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
            report = Path(directory) / "design.json"
            report.write_text(
                json.dumps(
                    {
                        "linter": {"package": "@google/design.md", "version": evaluation.DESIGN_MD_VERSION},
                        "results": [
                            {
                                "provider": "claude",
                                "model": "haiku",
                                "case_id": "repair-cafe-intake-v6",
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
                    "directory": Path(directory),
                }
            ]
            with self.assertRaisesRegex(evaluation.DesignFindingsError, "repair required"):
                evaluation.validate_design_completion(report, targets)

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


if __name__ == "__main__":
    unittest.main()
