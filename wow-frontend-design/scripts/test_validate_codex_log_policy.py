#!/usr/bin/env python3
"""Tests for the evaluator-owned Codex trace policy."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "evals" / "validate_codex_log_policy.py"
SPEC = importlib.util.spec_from_file_location("validate_codex_log_policy", MODULE_PATH)
assert SPEC and SPEC.loader
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)


def event(command: str) -> str:
    return json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": command}})


class CodexLogPolicyTests(unittest.TestCase):
    def test_allows_local_static_checks_and_capability_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            trace = root / "trace.jsonl"
            trace.write_text(
                "\n".join(
                    (
                        event("/bin/zsh -lc 'which npx || true'"),
                        event("/bin/zsh -lc 'node --check app.js'"),
                        event("/bin/zsh -lc \"rg 'https://|http://' index.html\""),
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(3, policy.validate(trace, root))

    def test_rejects_package_manager_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            trace = root / "trace.jsonl"
            trace.write_text(event("/bin/zsh -lc 'which npx || npx --yes package lint file'") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(policy.PolicyError, "forbidden executable.*npx"):
                policy.validate(trace, root)

    def test_rejects_network_git_and_external_temp_access(self) -> None:
        commands = (
            "/bin/zsh -lc 'curl https://example.com'",
            "/bin/zsh -lc 'git status --short'",
            "/bin/zsh -lc 'find /var/folders/example -delete'",
        )
        for command in commands:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                trace = root / "trace.jsonl"
                trace.write_text(event(command) + "\n", encoding="utf-8")
                with self.assertRaises(policy.PolicyError):
                    policy.validate(trace, root)


if __name__ == "__main__":
    unittest.main()
