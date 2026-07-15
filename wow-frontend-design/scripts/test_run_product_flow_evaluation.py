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
                    "case_id": "harbor-cold-chain-v4",
                    "alias": "claude-sonnet",
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
                    "case_id": "harbor-cold-chain-v4",
                    "alias": "claude-sonnet",
                    "directory": root,
                }
            ]
            results = []
            for viewport, profile in evaluation.VIEWPORTS.items():
                width = int(profile["width"])
                height = int(profile["height"])
                scale = int(profile["deviceScaleFactor"])
                screenshot = screenshots / f"harbor-cold-chain-v4-claude-sonnet-index-{viewport}.png"
                screenshot.write_bytes(fake_png(width * scale, height * scale))
                results.append(
                    {
                        "caseId": "harbor-cold-chain-v4",
                        "alias": "claude-sonnet",
                        "page": "index.html",
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
                                "caseId": "harbor-cold-chain-v4",
                                "alias": "claude-sonnet",
                            }
                        ],
                        "results": results,
                        "summary": {"checkedPages": 2},
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(2, evaluation.validate_visual_completion(report, screenshots, targets))

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
                                "model": "sonnet",
                                "case_id": "island-sound-archive-v4",
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
            target = artifact_root / "claude-sonnet-island-sound-archive-v4"
            target.mkdir()
            (target / "index.html").write_text("<main></main>", encoding="utf-8")
            ledger = Path(directory) / "generation.json"
            record = {
                "provider": "claude",
                "model": "sonnet",
                "case_id": "island-sound-archive-v4",
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

            escaped = Path(directory) / "claude-sonnet-island-sound-archive-v4"
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
                        "linter": {"package": "@google/design.md", "version": "0.2.0"},
                        "results": [
                            {
                                "provider": "claude",
                                "model": "sonnet",
                                "case_id": "island-sound-archive-v4",
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
                    "case_id": "island-sound-archive-v4",
                    "alias": "claude-sonnet",
                    "directory": Path(directory),
                }
            ]
            with self.assertRaisesRegex(evaluation.DesignFindingsError, "clean gate rejected"):
                evaluation.validate_design_completion(report, targets)

    def test_visual_findings_separate_execution_from_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "visual.json"
            report.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "caseId": "harbor-cold-chain-v4",
                                "alias": "codex-gpt-5.5",
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
                {"harbor-cold-chain-v4:codex-gpt-5.5": ["critical_text_collision"]},
                evaluation.blocking_visual_findings(report),
            )


if __name__ == "__main__":
    unittest.main()
