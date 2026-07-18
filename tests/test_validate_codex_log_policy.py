#!/usr/bin/env python3
"""Tests for the evaluator-owned Codex trace policy."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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

    def test_command_free_mode_rejects_even_safe_local_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            trace = root / "trace.jsonl"
            trace.write_text(event("node --check app.js") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(policy.PolicyError, "command execution is forbidden"):
                policy.validate(trace, root, allow_commands=False)

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

    def test_rejects_environment_and_authentication_state_access(self) -> None:
        commands = (
            "/bin/zsh -lc 'env && true'",
            "/bin/zsh -lc 'printenv DATABASE_URL'",
            "/bin/zsh -lc 'cat \"$CODEX_HOME/auth.json\"'",
            "python3 -c 'import os; print(os.environ)'",
        )
        for command in commands:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                trace = root / "trace.jsonl"
                trace.write_text(event(command) + "\n", encoding="utf-8")
                with self.assertRaisesRegex(policy.PolicyError, "forbidden credential access"):
                    policy.validate(trace, root)

    def test_shell_obfuscation_cannot_bypass_policy(self) -> None:
        commands = (
            "/bin/zsh -lc '$(command -v curl) https://example.com'",
            'python3 -c "import os; print(os.en\"\"viron)"',
            "/bin/zsh -lc \"cat ~/.aw's'/creden'tials\"",
            "/bin/zsh -lc '${FETCHER:-curl} https://example.com'",
            "/bin/zsh -lc 'cat \"$HOME/.aw${EMPTY:-}s/creden${EMPTY:-}tials\"'",
            "/bin/zsh -lc '/usr/bin/e?v'",
        )
        for command in commands:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                trace = root / "trace.jsonl"
                trace.write_text(event(command) + "\n", encoding="utf-8")
                with self.assertRaises(policy.PolicyError):
                    policy.validate(trace, root)

    def test_allows_only_the_evaluator_stage_across_macos_var_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory).resolve()
            alias = str(stage)
            if alias.startswith("/private/var/"):
                alias = alias.removeprefix("/private")
            trace = stage / "trace.jsonl"
            trace.write_text(event(f"python3 '{alias}/check.py'") + "\n", encoding="utf-8")
            self.assertEqual(1, policy.validate(trace, stage))

    def test_rejects_external_temp_even_when_stage_is_also_present(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory).resolve()
            trace = stage / "trace.jsonl"
            trace.write_text(
                event(f"python3 '{stage}/check.py' > /tmp/outside-result.txt") + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(policy.PolicyError, "outside-result"):
                policy.validate(trace, stage)

    def test_rejects_builder_collaboration_and_gui_executables(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            trace = stage / "trace.jsonl"
            trace.write_text(
                json.dumps({"item": {"type": "collab_tool_call"}}) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(policy.PolicyError, "collab_tool_call"):
                policy.validate(trace, stage)

            trace.write_text(event("/bin/zsh -lc 'safaridriver --enable'") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(policy.PolicyError, "safaridriver"):
                policy.validate(trace, stage)


if __name__ == "__main__":
    unittest.main()
