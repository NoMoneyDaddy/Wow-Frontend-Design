#!/usr/bin/env python3
"""Focused regression tests for the isolated v7 Codex runner."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "evals" / "run_v7_codex_case.py"
SPEC = importlib.util.spec_from_file_location("run_v7_codex_case", MODULE)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class V7CodexRunnerTests(unittest.TestCase):
    def _git(self, root: Path, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True).stdout.strip()

    def test_candidate_materialization_changes_only_allowed_reference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "wow-frontend-design"
            (package / "references").mkdir(parents=True)
            (package / "SKILL.md").write_text("---\nname: wow\n---\n", encoding="utf-8")
            accepted_text = "# Accepted\n"
            (package / "references" / "typographic-layout.md").write_text(accepted_text, encoding="utf-8")
            self._git(root, "init", "-q")
            self._git(root, "config", "user.name", "Test")
            self._git(root, "config", "user.email", "test@example.invalid")
            self._git(root, "add", ".")
            self._git(root, "commit", "-qm", "baseline")
            commit = self._git(root, "rev-parse", "HEAD")
            records = []
            for path in sorted(package.rglob("*")):
                if path.is_file():
                    body = path.read_bytes()
                    records.append({
                        "path": path.relative_to(root).as_posix(),
                        "mode": "100644",
                        "bytes": len(body),
                        "sha256": hashlib.sha256(body).hexdigest(),
                    })
            manifest = {"baseline": {"commit": commit, "files": records, "tree_sha256": "a" * 64}}
            candidate = root / "candidate.md"
            candidate.write_text("# Candidate\n", encoding="utf-8")
            destination = root / "materialized"
            result = runner.materialize_package(manifest, "candidate", candidate, destination, root)
            self.assertEqual([runner.EDITABLE_PATH], result["changed_paths"])
            self.assertEqual("a" * 64, result["source_baseline_tree_sha256"])
            self.assertEqual("# Candidate\n", (destination / "references" / "typographic-layout.md").read_text())
            self.assertEqual((package / "SKILL.md").read_bytes(), (destination / "SKILL.md").read_bytes())

    def test_accepted_variant_rejects_candidate_reference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "candidate.md"
            candidate.write_text("x", encoding="utf-8")
            with self.assertRaisesRegex(runner.V7CodexRunnerError, "cannot receive"):
                runner.materialize_package({}, "accepted", candidate, root / "output", root)

    def test_prompt_activates_skill_without_revealing_variant(self) -> None:
        prompt = runner.build_prompt("建立公民決策摘要。", "前次 timeout")
        self.assertIn("$wow-frontend-design", prompt)
        self.assertIn("UNTRUSTED PRODUCT BRIEF", prompt)
        self.assertIn("UNTRUSTED PRIOR ATTEMPT DIAGNOSTIC", prompt)
        self.assertNotIn("candidate", prompt.casefold())
        self.assertNotIn("accepted", prompt.casefold())
        self.assertIn("file-change tools only", prompt)

    def test_valid_codex_output_events_count_as_progress(self) -> None:
        lines = [
            json.dumps({"type": "thread.started", "thread_id": "test"}),
            json.dumps({"type": "turn.started"}),
            json.dumps({"type": "item.completed", "item": {"type": "agent_message"}}),
            json.dumps({"type": "item.started", "item": {"type": "command_execution"}}),
            json.dumps({"type": "item.completed", "item": {"type": "command_execution"}}),
            json.dumps({"type": "item.completed", "item": {"type": "file_change"}}),
            "not-json",
        ]
        self.assertEqual(6, runner.meaningful_event_count(lines))

    def test_host_runner_rejects_sealed_case_split(self) -> None:
        manifest = {
            "splits": {
                "development": [{"id": "dev-case"}],
                "sealed_validation": [{"id": "sealed-case"}],
                "sealed_test": [],
            }
        }
        self.assertEqual("development", runner._case_split(manifest, "dev-case"))
        self.assertEqual("sealed_validation", runner._case_split(manifest, "sealed-case"))
        with self.assertRaisesRegex(runner.V7CodexRunnerError, "exactly once"):
            runner._case_split(manifest, "missing-case")

    def test_login_status_accepts_codex_stderr_channel(self) -> None:
        result = subprocess.CompletedProcess(
            args=["codex", "login", "status"],
            returncode=0,
            stdout="",
            stderr="Logged in using ChatGPT\n",
        )
        self.assertIsNone(runner._validate_first_party_login(result))

    def test_login_status_rejects_ambiguous_or_failed_output(self) -> None:
        ambiguous = subprocess.CompletedProcess(
            args=["codex", "login", "status"],
            returncode=0,
            stdout="Logged in using ChatGPT\n",
            stderr="warning\n",
        )
        with self.assertRaisesRegex(runner.V7CodexRunnerError, "not first-party"):
            runner._validate_first_party_login(ambiguous)
        failed = subprocess.CompletedProcess(
            args=["codex", "login", "status"],
            returncode=1,
            stdout="",
            stderr="Logged in using ChatGPT\n",
        )
        with self.assertRaisesRegex(runner.V7CodexRunnerError, "not first-party"):
            runner._validate_first_party_login(failed)

    def test_design_lint_uses_preinstalled_locked_tool(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            shutil.copy2(ROOT / "wow-frontend-design" / "assets" / "DESIGN.template.md", stage / "DESIGN.md")
            clean, diagnostic, tool = runner._design_lint(stage, 30)
            self.assertTrue(clean)
            self.assertEqual("", diagnostic)
            self.assertEqual("@google/design.md", tool["package"])
            self.assertEqual(64, len(tool["cli_sha256"]))
        self.assertNotIn("npx", runner._design_lint.__code__.co_names)


if __name__ == "__main__":
    unittest.main()
