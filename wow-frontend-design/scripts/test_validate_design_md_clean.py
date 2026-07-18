#!/usr/bin/env python3
"""Unit tests for the pinned DESIGN.md clean gate."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "evals" / "validate_design_md_clean.py"
SPEC = importlib.util.spec_from_file_location("validate_design_md_clean", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class DesignMdCleanGateTests(unittest.TestCase):
    def fixture(self, root: Path) -> tuple[Path, Path, Path]:
        package = root / "node_modules" / "@google" / "design.md"
        entry = package / "dist" / "index.js"
        entry.parent.mkdir(parents=True)
        entry.write_text("#!/usr/bin/env node\n", encoding="utf-8")
        entry.chmod(0o755)
        (package / "package.json").write_text(
            json.dumps(
                {
                    "name": "@google/design.md",
                    "version": "0.3.0",
                    "main": "./dist/index.js",
                    "bin": {"design.md": "./dist/index.js", "designmd": "./dist/index.js"},
                }
            ),
            encoding="utf-8",
        )
        (root / "package-lock.json").write_text(
            json.dumps(
                {
                    "packages": {
                        "node_modules/@google/design.md": {
                            "version": "0.3.0",
                            "integrity": "sha512-" + "A" * 40,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        node = root / "canonical-node"
        node.write_bytes(b"node-fixture")
        node.chmod(0o755)
        design = root / "DESIGN.md"
        design.write_text("---\nversion: alpha\nname: Test\n---\n# Test\n", encoding="utf-8")
        return design, node, entry

    def test_accepts_integer_summary(self) -> None:
        self.assertEqual((0, 0, 1), validator.clean_summary({"summary": {"errors": 0, "warnings": 0, "infos": 1}}))

    def test_rejects_bool_or_missing_summary_values(self) -> None:
        for payload in (
            {"summary": {"errors": False, "warnings": 0, "infos": 0}},
            {"summary": {"errors": 0, "warnings": 0}},
            {},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                validator.clean_summary(payload)

    def test_local_validator_runs_canonical_node_and_never_npx(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            design, node, entry = self.fixture(root)
            calls: list[list[str]] = []

            def completed(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                calls.append(command)
                if command[-1] == "--version":
                    return subprocess.CompletedProcess(command, 0, stdout="v22.1.0\n", stderr="")
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout='{"summary":{"errors":0,"warnings":0,"infos":1},"findings":[]}',
                    stderr="",
                )

            with mock.patch.object(validator.shutil, "which", return_value=str(node)), mock.patch.object(
                validator.subprocess, "run", side_effect=completed
            ):
                receipt = validator.validate_local(design, repository_root=root)
            lint_calls = [command for command in calls if command[-1] != "--version"]
            self.assertEqual([[str(node), str(entry), "lint", str(design)]], lint_calls)
            self.assertFalse(any("npx" in argument for command in calls for argument in command))
            self.assertEqual("passed", receipt["status"])
            self.assertEqual({"errors": 0, "warnings": 0, "infos": 1}, receipt["summary"])
            self.assertEqual([], receipt["findings"])
            self.assertEqual("@google/design.md", receipt["tool"]["package"])
            self.assertEqual(validator._digest(design), receipt["input"]["sha256"])

    def test_local_validator_returns_structured_rejected_findings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            design, node, _ = self.fixture(root)

            def completed(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                if command[-1] == "--version":
                    return subprocess.CompletedProcess(command, 0, stdout="v22.1.0\n", stderr="")
                return subprocess.CompletedProcess(
                    command,
                    1,
                    stdout=json.dumps(
                        {
                            "summary": {"errors": 0, "warnings": 1, "infos": 0},
                            "findings": [{"message": "orphan token", "rule": "tokens/orphan"}],
                        }
                    ),
                    stderr="",
                )

            with mock.patch.object(validator.shutil, "which", return_value=str(node)), mock.patch.object(
                validator.subprocess, "run", side_effect=completed
            ):
                receipt = validator.validate_local(design, repository_root=root)
            self.assertEqual("rejected", receipt["status"])
            self.assertEqual([{"message": "orphan token", "rule": "tokens/orphan"}], receipt["findings"])

    def test_local_validator_rejects_content_or_mode_drift(self) -> None:
        for drift in ("content", "mode"):
            with self.subTest(drift=drift), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                design, node, entry = self.fixture(root)

                def completed(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                    if command[-1] == "--version":
                        return subprocess.CompletedProcess(command, 0, stdout="v22.1.0\n", stderr="")
                    if drift == "content":
                        entry.write_text("changed\n", encoding="utf-8")
                    else:
                        entry.chmod(0o700)
                    return subprocess.CompletedProcess(
                        command,
                        0,
                        stdout='{"summary":{"errors":0,"warnings":0,"infos":0},"findings":[]}',
                        stderr="",
                    )

                with mock.patch.object(validator.shutil, "which", return_value=str(node)), mock.patch.object(
                    validator.subprocess, "run", side_effect=completed
                ), self.assertRaisesRegex(validator.DesignMdInfrastructureError, "drifted"):
                    validator.validate_local(design, repository_root=root)

    def test_missing_local_tool_fails_closed_even_with_fake_npx_on_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            design = root / "DESIGN.md"
            design.write_text("# Test\n", encoding="utf-8")
            fake_npx = root / "npx"
            fake_npx.write_text("success\n", encoding="utf-8")
            fake_npx.chmod(0o755)
            with mock.patch.object(validator.shutil, "which", return_value=None), self.assertRaises(
                validator.DesignMdInfrastructureError
            ):
                validator.validate_local(design, repository_root=root)


if __name__ == "__main__":
    unittest.main()
