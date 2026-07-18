#!/usr/bin/env python3
"""Regression tests for the generic isolated current-skill fresh-build runner."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "evals" / "run_current_skill_build.py"
CORE_PATH = ROOT / "evals" / "codex_isolated_build_core.py"
SPEC = importlib.util.spec_from_file_location("current_skill_build_core_test", CORE_PATH)
assert SPEC and SPEC.loader
core = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(core)
sys.path.insert(0, str(ROOT / "evals"))
import run_current_skill_build as policy  # noqa: E402

SAFE_HTML = "<!doctype html><html lang=\"en\"><head><title>Test</title></head><body><main><h1>Test</h1></main></body></html>"
SAFE_DESIGN = "---\nversion: alpha\nname: Runner Test\n---\n# Runner Test\n"


class CurrentSkillBuildTests(unittest.TestCase):
    def test_repository_exposes_one_documented_current_build_entry(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(
            "python3 evals/run_current_skill_build.py",
            package["scripts"]["build:current"],
        )
        documentation = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")
        self.assertIn("npm run build:current --", documentation)
        self.assertIn("runner-owned `run-manifest.json`", documentation)

    def fixture(self, root: Path, mode: str = "fresh") -> tuple[Path, Path, Path, dict[str, str]]:
        capture = root / "capture"
        capture.mkdir()
        (capture / "mode.txt").write_text(mode, encoding="utf-8")
        codex_home = root / "host-codex"
        codex_home.mkdir()
        (codex_home / "auth.json").write_text('{"fixture":"not-a-secret"}\n', encoding="utf-8")
        bin_dir = root / "bin"
        bin_dir.mkdir()
        fake_codex = bin_dir / "codex"
        fake_codex.write_text(
            f"""#!{sys.executable}
import hashlib
import json
import os
import pathlib
import sys
import time

root = pathlib.Path(__file__).resolve().parent.parent
capture = root / "capture"
mode = (capture / "mode.txt").read_text(encoding="utf-8")
if sys.argv[1:] == ["--version"]:
    print("codex-cli 9.9.9-test")
    raise SystemExit(0)
if sys.argv[1:] == ["login", "status"]:
    print("Logged in using API key" if mode == "bad-login" else "Logged in using ChatGPT")
    raise SystemExit(0)
count_path = capture / "invocation-count.txt"
attempt = int(count_path.read_text(encoding="utf-8")) + 1 if count_path.exists() else 1
count_path.write_text(str(attempt), encoding="utf-8")
args = sys.argv[1:]
stage = pathlib.Path(args[args.index("--cd") + 1])
prompt = sys.stdin.read()
isolated = pathlib.Path(os.environ["CODEX_HOME"])
skill = isolated / "skills" / "wow-frontend-design"
snapshot = {{
    "skill_md_sha256": hashlib.sha256((skill / "SKILL.md").read_bytes()).hexdigest(),
    "skill_names": sorted(path.name for path in (isolated / "skills").iterdir()),
    "codex_home": str(isolated),
    "args": args,
    "prompt": prompt,
    "environment_names": sorted(os.environ),
}}
(capture / "invocation.json").write_text(json.dumps(snapshot), encoding="utf-8")
(capture / f"invocation-{{attempt}}.json").write_text(json.dumps(snapshot), encoding="utf-8")
if mode == "timeout":
    time.sleep(10)
    raise SystemExit(0)
if mode == "invalid-utf8":
    (stage / "DESIGN.md").write_bytes(b"\\xff")
elif mode == "nul-output":
    (stage / "DESIGN.md").write_text({(SAFE_DESIGN + chr(0))!r}, encoding="utf-8")
else:
    (stage / "DESIGN.md").write_text({SAFE_DESIGN!r}, encoding="utf-8")
if mode == "output-symlink":
    (stage / "index.html").symlink_to(stage / "DESIGN.md")
elif mode == "oversized-output":
    (stage / "index.html").write_bytes({SAFE_HTML.encode()!r} + b"x" * 1048577)
elif mode == "page-error" or (mode == "page-error-repairable" and attempt == 1):
    (stage / "index.html").write_text({SAFE_HTML.replace('</main>', '<script>throw new Error("broken boot")</script></main>')!r}, encoding="utf-8")
else:
    (stage / "index.html").write_text({SAFE_HTML!r}, encoding="utf-8")
if mode == "extra-output" or (mode == "extra-on-repair" and attempt > 1):
    (stage / "extra.txt").write_text("unexpected", encoding="utf-8")
if mode == "multi-output":
    (stage / "details.html").write_text({SAFE_HTML!r}, encoding="utf-8")
if mode == "bad-trace" or (mode == "bad-trace-on-repair" and attempt > 1):
    print(json.dumps({{"type":"item.completed","item":{{"type":"command_execution","command":"npx package"}}}}))
if mode == "skill-content-drift":
    (root / "skill-source" / "SKILL.md").write_text("drifted", encoding="utf-8")
if mode == "skill-mode-drift":
    (root / "skill-source" / "SKILL.md").chmod(0o700)
print(json.dumps({{"type":"turn.completed"}}))
if mode == "exit-one" or (mode == "exit-on-repair" and attempt > 1):
    print("provider rejected the requested model", file=sys.stderr)
    raise SystemExit(1)
if mode == "exit-one-sensitive":
    print("UNIQUE-BRIEF-CONTENT /tmp/private auth token", file=sys.stderr)
    raise SystemExit(1)
""",
            encoding="utf-8",
        )
        fake_codex.chmod(0o755)
        fake_npx = bin_dir / "npx"
        fake_npx.write_text(
            f"""#!{sys.executable}
import json
import os
import pathlib
capture = pathlib.Path(__file__).resolve().parent.parent / "capture"
(capture / "npx-environment.json").write_text(json.dumps({{key: value for key, value in os.environ.items() if key.startswith("npm_config_")}}), encoding="utf-8")
print('{{"summary":{{"errors":0,"warnings":0,"infos":0}},"findings":[]}}')
""",
            encoding="utf-8",
        )
        fake_npx.chmod(0o755)
        brief = (root / "brief.md").resolve()
        brief.write_text("Build a quiet civic archive. UNIQUE-BRIEF-CONTENT\n", encoding="utf-8")
        target = (root / "target").resolve()
        target.mkdir()
        environment = os.environ.copy()
        environment.update(
            {
                "PATH": f"{bin_dir}{os.pathsep}{environment.get('PATH', '')}",
                "CODEX_HOME": str(codex_home),
                "OPENAI_API_KEY": "must-not-reach-child",
                "DATABASE_URL": "must-not-reach-child",
            }
        )
        return brief, target, capture, environment

    def invoke(
        self,
        brief: Path,
        target: Path,
        environment: dict[str, str],
        *,
        hard_seconds: int = 5,
        model: str | None = "gpt-5.6-sol",
        reasoning_effort: str | None = "high",
        outputs: tuple[str, ...] | None = None,
        log_dir: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        selected_log_dir = log_dir or Path(environment["CODEX_HOME"]).parent / "logs"
        selected_log_dir.mkdir(exist_ok=True)
        command = [
            sys.executable,
            str(RUNNER),
            "--brief",
            str(brief),
            "--target",
            str(target),
            "--log-dir",
            str(selected_log_dir),
        ]
        if model is not None:
            command.extend(("--model", model))
        if reasoning_effort is not None:
            command.extend(("--reasoning-effort", reasoning_effort))
        command.extend(("--hard-seconds", str(hard_seconds)))
        for output in outputs or ():
            command.extend(("--output", output))
        return subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )

    def test_fresh_build_publishes_only_outputs_and_privacy_safe_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root)
            completed = self.invoke(brief, target, environment, model="gpt-5.4-test")
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                {"DESIGN.md", "index.html", "run-manifest.json"},
                {path.name for path in target.iterdir()},
            )
            manifest = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("gpt-5.4-test", manifest["model"]["requested_identifier"])
            self.assertEqual("high", manifest["model"]["requested_reasoning_effort"])
            self.assertEqual("not_observed", manifest["model"]["resolution_status"])
            self.assertIsNone(manifest["model"]["resolved_backend_snapshot"])
            self.assertEqual(["DESIGN.md", "index.html"], [item["path"] for item in manifest["outputs"]])
            for output in manifest["outputs"]:
                self.assertEqual(hashlib.sha256((target / output["path"]).read_bytes()).hexdigest(), output["sha256"])
            raw_manifest = json.dumps(manifest)
            self.assertNotIn("UNIQUE-BRIEF-CONTENT", raw_manifest)
            self.assertNotIn(str(root), raw_manifest)
            self.assertNotIn("not-a-secret", raw_manifest)
            invocation = json.loads((capture / "invocation.json").read_text(encoding="utf-8"))
            self.assertNotIn("OPENAI_API_KEY", invocation["environment_names"])
            self.assertNotIn("DATABASE_URL", invocation["environment_names"])
            disabled = [
                invocation["args"][index + 1]
                for index, value in enumerate(invocation["args"][:-1])
                if value == "--disable"
            ]
            self.assertEqual(
                [
                    "apps",
                    "multi_agent",
                    "browser_use",
                    "computer_use",
                    "image_generation",
                    "plugins",
                    "shell_tool",
                    "skill_mcp_dependency_install",
                    "tool_call_mcp_elicitation",
                    "tool_suggest",
                ],
                disabled,
            )
            self.assertIn("sandbox_workspace_write.network_access=false", invocation["args"])
            self.assertFalse((capture / "npx-environment.json").exists())
            self.assertEqual("@google/design.md", manifest["design_md_gate"]["tool"]["package"])
            self.assertEqual("0.3.0", manifest["design_md_gate"]["tool"]["version"])
            self.assertEqual("passed", manifest["html_smoke_gate"]["status"])
            self.assertEqual("playwright", manifest["html_smoke_gate"]["tool"]["package"])
            self.assertEqual("@axe-core/playwright", manifest["html_smoke_gate"]["tool"]["accessibility_package"])
            self.assertIn("repair_policy", manifest["tools"])
            receipt = json.loads(
                (root / "logs" / "current-skill-build.execution.json").read_text(encoding="utf-8")
            )
            self.assertEqual("execution_passed", receipt["status"])
            self.assertEqual("publication_pending", receipt["classification"])
            self.assertEqual(manifest["execution"]["trace"], receipt["logs"]["trace"])

    def test_current_cli_defaults_to_sol_with_high_reasoning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root)
            completed = self.invoke(
                brief,
                target,
                environment,
                model=None,
                reasoning_effort=None,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            manifest = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("gpt-5.6-sol", manifest["model"]["requested_identifier"])
            self.assertEqual("high", manifest["model"]["requested_reasoning_effort"])
            invocation = json.loads((capture / "invocation.json").read_text(encoding="utf-8"))
            model_index = invocation["args"].index("--model")
            self.assertEqual("gpt-5.6-sol", invocation["args"][model_index + 1])
            self.assertIn('model_reasoning_effort="high"', invocation["args"])

    def test_repeated_output_contract_drives_prompt_validation_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root, "multi-output")
            requested = ("DESIGN.md", "index.html", "details.html")
            completed = self.invoke(brief, target, environment, outputs=requested)
            self.assertEqual(0, completed.returncode, completed.stderr)
            manifest = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(list(requested), [record["path"] for record in manifest["outputs"]])
            invocation = json.loads((capture / "invocation.json").read_text(encoding="utf-8"))
            self.assertIn("DESIGN.md, index.html, details.html", invocation["prompt"])

    def test_invalid_output_names_are_rejected_before_codex(self) -> None:
        invalid_sets = (
            ("DESIGN.md", "/index.html"),
            ("DESIGN.md", "../index.html"),
            ("DESIGN.md", "folder\\index.html"),
            ("DESIGN.md", "index.html", "index.html"),
            ("DESIGN.md", "run-manifest.json", "index.html"),
            ("DESIGN.md", "RUN-MANIFEST.JSON", "index.html"),
            ("DESIGN.md", "index.html", "INDEX.HTML"),
        )
        for outputs in invalid_sets:
            with self.subTest(outputs=outputs), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                brief, target, capture, environment = self.fixture(root)
                completed = self.invoke(brief, target, environment, outputs=outputs)
                self.assertNotEqual(0, completed.returncode)
                self.assertFalse((capture / "invocation.json").exists())
                self.assertEqual([], list(target.iterdir()))

    def test_nonempty_target_is_rejected_before_codex(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root)
            (target / "existing.txt").write_text("occupied", encoding="utf-8")
            completed = self.invoke(brief, target, environment)
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("target must be empty", completed.stderr)
            self.assertFalse((capture / "invocation.json").exists())

    def test_symlink_target_is_rejected_before_codex(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root)
            link = root / "target-link"
            link.symlink_to(target, target_is_directory=True)
            completed = self.invoke(brief, link, environment)
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("existing real directory", completed.stderr)
            self.assertFalse((capture / "invocation.json").exists())

    def test_extra_output_is_rejected_without_partial_publish(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, _, environment = self.fixture(root, "extra-output")
            completed = self.invoke(brief, target, environment)
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("output_contract_rejection", completed.stderr)
            self.assertEqual([], list(target.iterdir()))
            self.assertFalse((root / "logs" / "current-skill-build.quarantine").exists())

    def test_symlink_output_is_rejected_without_partial_publish(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, _, environment = self.fixture(root, "output-symlink")
            completed = self.invoke(brief, target, environment)
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("output_contract_rejection", completed.stderr)
            self.assertEqual([], list(target.iterdir()))

    def test_utf8_nul_and_size_contracts_fail_closed(self) -> None:
        for mode, diagnostic in (
            ("invalid-utf8", "output_contract_rejection"),
            ("nul-output", "output_contract_rejection"),
            ("oversized-output", "output_contract_rejection"),
        ):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                brief, target, _, environment = self.fixture(root, mode)
                completed = self.invoke(brief, target, environment)
                self.assertNotEqual(0, completed.returncode)
                self.assertIn(diagnostic, completed.stderr)
                self.assertEqual([], list(target.iterdir()))

    def test_hard_timeout_terminates_generation_and_keeps_target_empty(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, _, environment = self.fixture(root, "timeout")
            started = time.monotonic()
            completed = self.invoke(brief, target, environment, hard_seconds=1)
            elapsed = time.monotonic() - started
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("hard_timeout", completed.stderr)
            self.assertLess(elapsed, 5)
            self.assertEqual([], list(target.iterdir()))

    def test_exit_one_preserves_logs_and_private_failure_receipt_with_empty_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, _, environment = self.fixture(root, "exit-one-sensitive")
            completed = self.invoke(brief, target, environment)
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("generation_exit_nonzero", completed.stderr)
            self.assertNotIn(str(root), completed.stderr)
            self.assertNotIn("UNIQUE-BRIEF-CONTENT", completed.stderr)
            self.assertEqual([], list(target.iterdir()))
            log_dir = root / "logs"
            self.assertTrue((log_dir / "current-skill-build.trace.jsonl").is_file())
            self.assertTrue((log_dir / "current-skill-build.stderr.txt").is_file())
            receipt = json.loads(
                (log_dir / "current-skill-build.execution.json").read_text(encoding="utf-8")
            )
            serialized = json.dumps(receipt)
            self.assertEqual("failed", receipt["status"])
            self.assertEqual("generation_exit_nonzero", receipt["classification"])
            self.assertFalse((log_dir / "current-skill-build.publication-failure.json").exists())
            self.assertFalse((log_dir / "current-skill-build.quarantine").exists())
            self.assertFalse((log_dir / "current-skill-build.design-gate.json").exists())
            self.assertNotIn("UNIQUE-BRIEF-CONTENT", serialized)
            self.assertNotIn(str(root), serialized)
            self.assertNotIn("auth token", serialized)
            self.assertNotIn("stderr_diagnostic", receipt)

    def test_log_directory_symlink_or_run_file_collision_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root)
            real_logs = root / "real-logs"
            real_logs.mkdir()
            symlink_logs = root / "symlink-logs"
            symlink_logs.symlink_to(real_logs, target_is_directory=True)
            completed = self.invoke(brief, target, environment, log_dir=symlink_logs)
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("absolute real directory", completed.stderr)
            self.assertFalse((capture / "invocation.json").exists())

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root)
            log_dir = root / "logs"
            log_dir.mkdir()
            (log_dir / "current-skill-build.stderr.txt").write_text("owned", encoding="utf-8")
            completed = self.invoke(brief, target, environment, log_dir=log_dir)
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("collision", completed.stderr)
            self.assertFalse((capture / "invocation.json").exists())
            self.assertEqual([], list(target.iterdir()))

    def test_log_directory_and_target_must_not_contain_one_another(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root)
            completed = self.invoke(brief, target, environment, log_dir=root)
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("must not contain one another", completed.stderr)
            self.assertFalse((capture / "invocation.json").exists())
            self.assertEqual([], list(target.iterdir()))

    def test_non_chatgpt_login_is_rejected_before_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root, "bad-login")
            completed = self.invoke(brief, target, environment)
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("execution_infrastructure_failure", completed.stderr)
            self.assertFalse((capture / "invocation.json").exists())
            self.assertEqual([], list(target.iterdir()))
            receipt = json.loads(
                (root / "logs" / "current-skill-build.execution.json").read_text(encoding="utf-8")
            )
            self.assertEqual("failed", receipt["status"])
            self.assertEqual("execution_infrastructure_failure", receipt["classification"])
            self.assertEqual({}, receipt["logs"])

    def test_forbidden_trace_is_rejected_before_publish(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, _, environment = self.fixture(root, "bad-trace")
            completed = self.invoke(brief, target, environment)
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("trace_policy_rejection", completed.stderr)
            self.assertEqual([], list(target.iterdir()))
            self.assertFalse((root / "logs" / "current-skill-build.quarantine").exists())

    def test_design_rejection_quarantines_only_validated_outputs_and_full_private_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, _, environment = self.fixture(root)
            log_dir = root / "logs"
            log_dir.mkdir()
            gate = {
                "status": "rejected",
                "required_result": "zero-errors-zero-warnings",
                "summary": {"errors": 0, "warnings": 1, "infos": 0},
                "findings": [{"message": "PRIVATE orphan token detail"}],
                "input": {"bytes": len(SAFE_DESIGN.encode()), "sha256": hashlib.sha256(SAFE_DESIGN.encode()).hexdigest()},
                "tool": {"package": "@google/design.md", "version": "0.3.0"},
            }
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                policy.design_policy, "validate_local", return_value=gate
            ), self.assertRaisesRegex(policy.RunnerError, "design_gate_rejection"):
                policy.run(brief, target, hard_seconds=5, log_dir=log_dir)
            self.assertEqual([], list(target.iterdir()))
            gate_path = log_dir / "current-skill-build.design-gate.json"
            quarantine = log_dir / "current-skill-build.quarantine"
            self.assertEqual(gate, json.loads(gate_path.read_text(encoding="utf-8")))
            self.assertEqual({"DESIGN.md", "index.html"}, {path.name for path in quarantine.iterdir()})
            receipt = json.loads(
                (log_dir / "current-skill-build.execution.json").read_text(encoding="utf-8")
            )
            serialized = json.dumps(receipt)
            self.assertEqual("design_gate_rejection", receipt["classification"])
            self.assertIn("repair_policy", receipt["tools"])
            self.assertNotIn("PRIVATE orphan token detail", serialized)
            self.assertNotIn(SAFE_DESIGN, serialized)
            self.assertNotIn(str(root), serialized)
            self.assertEqual("3", (root / "capture" / "invocation-count.txt").read_text(encoding="utf-8"))
            for attempt in (2, 3):
                repair_invocation = json.loads(
                    (root / "capture" / f"invocation-{attempt}.json").read_text(encoding="utf-8")
                )
                self.assertNotIn("PRIVATE orphan token detail", repair_invocation["prompt"])
                self.assertNotIn("UNIQUE-BRIEF-CONTENT", repair_invocation["prompt"])
                self.assertIn("orphan-token", repair_invocation["prompt"])
            self.assertEqual(
                hashlib.sha256(gate_path.read_bytes()).hexdigest(),
                receipt["design_rejection"]["gate_receipt"]["sha256"],
            )
            for record in receipt["design_rejection"]["quarantine"]["outputs"]:
                self.assertEqual(
                    hashlib.sha256((quarantine / record["path"]).read_bytes()).hexdigest(), record["sha256"]
                )

    def test_design_rejection_is_repaired_then_fully_regated_before_publish(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root)
            log_dir = root / "logs"
            log_dir.mkdir()
            rejected = {
                "status": "rejected",
                "findings": [{"message": "No YAML content found."}],
            }
            passed = {"status": "passed", "findings": []}
            html_passed = {"status": "passed"}
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                policy.design_policy, "validate_local", side_effect=[rejected, passed]
            ), mock.patch.object(policy, "_run_html_smoke", return_value=html_passed):
                manifest = policy.run(brief, target, hard_seconds=5, log_dir=log_dir)
            self.assertEqual("2", (capture / "invocation-count.txt").read_text(encoding="utf-8"))
            self.assertEqual(1, manifest["repair"]["rounds_used"])
            self.assertEqual("design", manifest["repair"]["attempts"][1]["trigger"]["gate"])
            self.assertEqual("passed", manifest["design_md_gate"]["status"])
            self.assertEqual("passed", manifest["html_smoke_gate"]["status"])
            self.assertEqual(manifest["prompt"], manifest["repair"]["attempts"][-1]["prompt"])
            self.assertEqual(
                manifest["repair"]["attempts"][0]["skill_snapshot"],
                manifest["repair"]["attempts"][1]["skill_snapshot"],
            )
            receipt = json.loads((log_dir / "current-skill-build.execution.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["prompt"], receipt["prompt"])
            self.assertEqual(manifest["execution"], receipt["execution"])
            self.assertIn("repair_policy", receipt["tools"])
            self.assertTrue((target / "run-manifest.json").is_file())
            self.assertFalse((log_dir / "current-skill-build.design-gate.json").exists())

    def test_html_rejection_is_repaired_then_design_and_html_are_regated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root)
            log_dir = root / "logs"
            log_dir.mkdir()
            design_passed = {"status": "passed", "findings": []}
            html_rejected = {
                "status": "rejected",
                "results": [{
                    "status": "rejected",
                    "page": "PRIVATE-URL",
                    "selector": "PRIVATE-SELECTOR",
                    "console": ["PRIVATE-CONSOLE"],
                    "navigation": "passed",
                    "visible_main": True,
                    "visible_text": True,
                    "visible_primary_content": True,
                    "root_horizontal_overflow": False,
                    "counters": {"console_errors": 1},
                    "inspection": {"axe_rule_ids": ["heading-order"]},
                }],
            }
            html_passed = {"status": "passed"}
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                policy.design_policy, "validate_local", return_value=design_passed
            ) as design_validator, mock.patch.object(
                policy, "_run_html_smoke", side_effect=[html_rejected, html_passed]
            ):
                manifest = policy.run(brief, target, hard_seconds=5, log_dir=log_dir)
            self.assertEqual("2", (capture / "invocation-count.txt").read_text(encoding="utf-8"))
            self.assertEqual(2, design_validator.call_count)
            trigger = manifest["repair"]["attempts"][1]["trigger"]
            self.assertEqual("html", trigger["gate"])
            self.assertEqual(["axe-heading-order", "console-errors"], trigger["finding_ids"])
            repair_prompt = json.loads(
                (capture / "invocation-2.json").read_text(encoding="utf-8")
            )["prompt"]
            for private_value in ("PRIVATE-URL", "PRIVATE-SELECTOR", "PRIVATE-CONSOLE", "UNIQUE-BRIEF-CONTENT"):
                self.assertNotIn(private_value, repair_prompt)
            self.assertEqual("passed", manifest["html_smoke_gate"]["status"])

    def test_real_html_gate_converges_after_one_repair(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root, "page-error-repairable")
            completed = self.invoke(brief, target, environment)
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual("2", (capture / "invocation-count.txt").read_text(encoding="utf-8"))
            manifest = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(1, manifest["repair"]["rounds_used"])
            self.assertEqual("html", manifest["repair"]["attempts"][1]["trigger"]["gate"])
            self.assertEqual("passed", manifest["design_md_gate"]["status"])
            self.assertEqual("passed", manifest["html_smoke_gate"]["status"])
            self.assertTrue((root / "logs" / "current-skill-build.repair-01.trace.jsonl").is_file())

    def test_repair_output_contract_failure_quarantines_last_valid_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root, "extra-on-repair")
            log_dir = root / "logs"
            log_dir.mkdir()
            rejected = {"status": "rejected", "findings": [{"message": "orphan token"}]}
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                policy.design_policy, "validate_local", return_value=rejected
            ), self.assertRaisesRegex(policy.RunnerError, "output_contract_rejection"):
                policy.run(brief, target, hard_seconds=5, log_dir=log_dir)
            self.assertEqual("2", (capture / "invocation-count.txt").read_text(encoding="utf-8"))
            self.assertFalse((log_dir / "current-skill-build.repair-02.trace.jsonl").exists())
            quarantine = log_dir / "current-skill-build.quarantine"
            self.assertEqual({"DESIGN.md", "index.html"}, {item.name for item in quarantine.iterdir()})
            receipt = json.loads((log_dir / "current-skill-build.execution.json").read_text(encoding="utf-8"))
            self.assertEqual("output_contract_rejection", receipt["classification"])
            self.assertEqual(1, receipt["repair_failure"]["round"])

    def test_repair_nonzero_stops_without_consuming_another_round(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root, "exit-on-repair")
            log_dir = root / "logs"
            log_dir.mkdir()
            rejected = {"status": "rejected", "findings": [{"message": "orphan token"}]}
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                policy.design_policy, "validate_local", return_value=rejected
            ), self.assertRaisesRegex(policy.RunnerError, "generation_exit_nonzero"):
                policy.run(brief, target, hard_seconds=5, log_dir=log_dir)
            self.assertEqual("2", (capture / "invocation-count.txt").read_text(encoding="utf-8"))
            self.assertFalse((log_dir / "current-skill-build.repair-02.trace.jsonl").exists())
            self.assertTrue((log_dir / "current-skill-build.quarantine").is_dir())
            self.assertEqual([], list(target.iterdir()))

    def test_repair_pre_return_failure_keeps_receipt_on_the_active_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root, "bad-trace-on-repair")
            log_dir = root / "logs"
            log_dir.mkdir()
            rejected = {"status": "rejected", "findings": [{"message": "orphan token"}]}
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                policy.design_policy, "validate_local", return_value=rejected
            ), self.assertRaisesRegex(policy.RunnerError, "trace_policy_rejection"):
                policy.run(brief, target, hard_seconds=5, log_dir=log_dir)
            receipt = json.loads((log_dir / "current-skill-build.execution.json").read_text(encoding="utf-8"))
            repair_prompt = json.loads(
                (capture / "invocation-2.json").read_text(encoding="utf-8")
            )["prompt"].encode("utf-8")
            repair_trace = log_dir / "current-skill-build.repair-01.trace.jsonl"
            self.assertEqual("trace_policy_rejection", receipt["classification"])
            self.assertEqual(hashlib.sha256(repair_prompt).hexdigest(), receipt["prompt"]["sha256"])
            self.assertEqual(hashlib.sha256(repair_trace.read_bytes()).hexdigest(), receipt["logs"]["trace"]["sha256"])
            self.assertNotIn("execution", receipt)
            self.assertEqual(1, len(receipt["repair"]["attempts"]))
            self.assertTrue((log_dir / "current-skill-build.quarantine").is_dir())

    def test_design_gate_infrastructure_failure_after_repair_preserves_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, _, environment = self.fixture(root)
            log_dir = root / "logs"
            log_dir.mkdir()
            rejected = {"status": "rejected", "findings": [{"message": "orphan token"}]}
            failure = policy.design_policy.DesignMdInfrastructureError("validator unavailable")
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                policy.design_policy, "validate_local", side_effect=[rejected, failure]
            ), self.assertRaisesRegex(policy.RunnerError, "execution_infrastructure_failure"):
                policy.run(brief, target, hard_seconds=5, log_dir=log_dir)
            quarantine = log_dir / "current-skill-build.quarantine"
            self.assertEqual({"DESIGN.md", "index.html"}, {item.name for item in quarantine.iterdir()})
            receipt = json.loads((log_dir / "current-skill-build.execution.json").read_text(encoding="utf-8"))
            self.assertEqual("execution_infrastructure_failure", receipt["classification"])
            self.assertEqual({"DESIGN.md", "index.html"}, {
                item["path"] for item in receipt["failure_artifact"]["quarantine"]["outputs"]
            })

    def test_malformed_repair_feedback_fails_as_infrastructure_and_preserves_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root)
            log_dir = root / "logs"
            log_dir.mkdir()
            malformed = {"status": "rejected", "findings": "PRIVATE malformed finding"}
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                policy.design_policy, "validate_local", return_value=malformed
            ), self.assertRaisesRegex(policy.RunnerError, "execution_infrastructure_failure"):
                policy.run(brief, target, hard_seconds=5, log_dir=log_dir)
            self.assertEqual("1", (capture / "invocation-count.txt").read_text(encoding="utf-8"))
            self.assertTrue((log_dir / "current-skill-build.quarantine").is_dir())
            receipt = json.loads((log_dir / "current-skill-build.execution.json").read_text(encoding="utf-8"))
            self.assertEqual("execution_infrastructure_failure", receipt["classification"])
            self.assertNotIn("PRIVATE malformed finding", json.dumps(receipt))

    def test_skill_snapshot_change_between_attempts_is_rejected_and_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, _, environment = self.fixture(root)
            log_dir = root / "logs"
            log_dir.mkdir()
            skill_source = root / "skill-source"
            skill_source.mkdir()
            (skill_source / "SKILL.md").write_text("initial skill\n", encoding="utf-8")
            rejected = {"status": "rejected", "findings": [{"message": "orphan token"}]}

            def drift_then_reject(*_args: object, **_kwargs: object) -> dict[str, object]:
                (skill_source / "SKILL.md").write_text("changed skill\n", encoding="utf-8")
                return rejected

            with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                policy, "SKILL_SOURCE", skill_source
            ), mock.patch.object(
                policy.design_policy, "validate_local", side_effect=drift_then_reject
            ), self.assertRaisesRegex(policy.RunnerError, "execution_infrastructure_failure"):
                policy.run(brief, target, hard_seconds=5, log_dir=log_dir)
            receipt = json.loads((log_dir / "current-skill-build.execution.json").read_text(encoding="utf-8"))
            self.assertEqual("execution_infrastructure_failure", receipt["classification"])
            self.assertNotEqual(
                receipt["repair"]["attempts"][0]["skill_snapshot"],
                receipt["repair"]["attempts"][1]["skill_snapshot"],
            )
            self.assertTrue((log_dir / "current-skill-build.quarantine").is_dir())

    def test_html_boot_error_is_rejected_and_quarantined_before_publish(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, _, environment = self.fixture(root, "page-error")
            completed = self.invoke(brief, target, environment)
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("html_smoke_rejection", completed.stderr)
            self.assertEqual([], list(target.iterdir()))
            log_dir = root / "logs"
            gate_path = log_dir / "current-skill-build.html-smoke.json"
            gate = json.loads(gate_path.read_text(encoding="utf-8"))
            self.assertEqual("rejected", gate["status"])
            self.assertGreaterEqual(
                sum(item["counters"]["page_errors"] for item in gate["results"]),
                2,
            )
            quarantine = log_dir / "current-skill-build.quarantine"
            self.assertEqual({"DESIGN.md", "index.html"}, {path.name for path in quarantine.iterdir()})
            receipt = json.loads(
                (log_dir / "current-skill-build.execution.json").read_text(encoding="utf-8")
            )
            self.assertEqual("html_smoke_rejection", receipt["classification"])
            self.assertNotIn("broken boot", json.dumps(receipt))

    def test_html_smoke_infrastructure_failure_preserves_quarantine(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, _, environment = self.fixture(root)
            log_dir = root / "logs"
            log_dir.mkdir()
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                policy,
                "_run_html_smoke",
                side_effect=policy.RunnerError("HTML Playwright smoke gate infrastructure failure"),
            ), self.assertRaisesRegex(policy.RunnerError, "execution_infrastructure_failure"):
                policy.run(brief, target, hard_seconds=5, log_dir=log_dir)
            self.assertEqual([], list(target.iterdir()))
            quarantine = log_dir / "current-skill-build.quarantine"
            self.assertEqual({"DESIGN.md", "index.html"}, {path.name for path in quarantine.iterdir()})
            receipt = json.loads((log_dir / "current-skill-build.execution.json").read_text(encoding="utf-8"))
            self.assertEqual("execution_infrastructure_failure", receipt["classification"])
            self.assertEqual(
                {"DESIGN.md", "index.html"},
                {item["path"] for item in receipt["html_smoke_unavailable"]["quarantine"]["outputs"]},
            )

    def test_html_smoke_timeout_terminates_the_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            process = mock.Mock(pid=321, returncode=None)
            process.communicate.side_effect = [
                subprocess.TimeoutExpired(cmd="node", timeout=1),
                ("", ""),
                ("", ""),
            ]
            with mock.patch.object(policy.subprocess, "Popen", return_value=process), mock.patch.object(
                policy.os, "killpg"
            ) as killpg, self.assertRaisesRegex(policy.RunnerError, "infrastructure failure"):
                policy._run_html_smoke(stage, ("DESIGN.md", "index.html"), 1)
            self.assertEqual(
                [mock.call(321, policy.signal.SIGTERM), mock.call(321, policy.signal.SIGKILL)],
                killpg.call_args_list,
            )

    def test_process_group_timeout_removes_a_real_descendant(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pid_file = root / "child.pid"
            helper = root / "helper.py"
            helper.write_text(
                "import pathlib, subprocess, sys, time\n"
                "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
                "pathlib.Path(sys.argv[1]).write_text(str(child.pid), encoding='utf-8')\n"
                "time.sleep(60)\n",
                encoding="utf-8",
            )
            process = subprocess.Popen(
                [sys.executable, str(helper), str(pid_file)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
            deadline = time.monotonic() + 2
            while not pid_file.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(pid_file.exists())
            child_pid = int(pid_file.read_text(encoding="utf-8"))
            with self.assertRaisesRegex(policy.RunnerError, "infrastructure failure"):
                policy._communicate_process_group(process, 0.05)
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                status = subprocess.run(
                    ["ps", "-p", str(child_pid), "-o", "stat="],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if status.returncode != 0 or status.stdout.strip().startswith("Z"):
                    break
                time.sleep(0.02)
            else:
                self.fail("validator descendant survived process-group timeout cleanup")

    def test_manifest_proves_ephemeral_current_skill_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, capture, environment = self.fixture(root)
            completed = self.invoke(brief, target, environment)
            self.assertEqual(0, completed.returncode, completed.stderr)
            manifest = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
            expected = core._tree_summary(core._tree_records(ROOT / "wow-frontend-design"), "wow-frontend-design")
            self.assertEqual(expected, manifest["skill_snapshot"])
            invocation = json.loads((capture / "invocation.json").read_text(encoding="utf-8"))
            self.assertEqual(["wow-frontend-design"], invocation["skill_names"])
            self.assertNotEqual(str(root / "host-codex"), invocation["codex_home"])
            self.assertEqual(
                hashlib.sha256((ROOT / "wow-frontend-design" / "SKILL.md").read_bytes()).hexdigest(),
                invocation["skill_md_sha256"],
            )

    def test_output_content_or_mode_drift_during_gate_is_rejected(self) -> None:
        for drift in ("content", "mode"):
            with self.subTest(drift=drift), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                brief, target, _, environment = self.fixture(root)
                (root / "logs").mkdir()

                def gate(design: Path, **_: object) -> dict[str, object]:
                    if drift == "content":
                        design.write_text(SAFE_DESIGN + "changed\n", encoding="utf-8")
                    else:
                        design.chmod(0o700)
                    return {"status": "passed"}

                with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                    policy.design_policy, "validate_local", side_effect=gate
                ), self.assertRaisesRegex(policy.RunnerError, "output_contract_rejection"):
                    policy.run(brief, target, hard_seconds=5, log_dir=root / "logs")
                self.assertEqual([], list(target.iterdir()))

    def test_target_race_is_rejected_without_overwriting_racer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, _, environment = self.fixture(root)
            (root / "logs").mkdir()

            def gate(_: Path, **__: object) -> dict[str, object]:
                (target / "racer-owned.txt").write_text("preserve", encoding="utf-8")
                return {"status": "passed"}

            with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                policy.design_policy, "validate_local", side_effect=gate
            ), self.assertRaisesRegex(policy.RunnerError, "execution_infrastructure_failure"):
                policy.run(brief, target, hard_seconds=5, log_dir=root / "logs")
            self.assertEqual({"racer-owned.txt"}, {path.name for path in target.iterdir()})
            receipt = json.loads(
                (root / "logs" / "current-skill-build.execution.json").read_text(encoding="utf-8")
            )
            self.assertEqual("execution_passed", receipt["status"])
            self.assertEqual("publication_pending", receipt["classification"])
            publication = json.loads(
                (root / "logs" / "current-skill-build.publication-failure.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual("failed", publication["status"])
            self.assertEqual("publication_failed", publication["classification"])
            self.assertFalse(publication["runner_outputs_published"])
            self.assertEqual("publication_pending", publication["execution_receipt"]["state"])
            self.assertEqual(
                hashlib.sha256((root / "logs" / "current-skill-build.execution.json").read_bytes()).hexdigest(),
                publication["execution_receipt"]["sha256"],
            )

    def test_publication_failure_does_not_rebuild_execution_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, _, environment = self.fixture(root)
            (root / "logs").mkdir()
            real_receipt = policy._receipt
            receipt_calls = 0

            def receipt(**kwargs: object) -> dict[str, object]:
                nonlocal receipt_calls
                receipt_calls += 1
                if receipt_calls > 1:
                    raise AssertionError("publication failure rebuilt execution receipt")
                return real_receipt(**kwargs)

            def gate(_: Path, **__: object) -> dict[str, object]:
                (target / "racer-owned.txt").write_text("preserve", encoding="utf-8")
                return {"status": "passed"}

            with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                policy.design_policy, "validate_local", side_effect=gate
            ), mock.patch.object(policy, "_receipt", side_effect=receipt), self.assertRaisesRegex(
                policy.RunnerError, "execution_infrastructure_failure"
            ):
                policy.run(brief, target, hard_seconds=5, log_dir=root / "logs")
            self.assertEqual(1, receipt_calls)
            self.assertTrue((root / "logs" / "current-skill-build.publication-failure.json").is_file())

    def test_execution_receipt_collision_is_not_trusted_as_runner_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, _, environment = self.fixture(root)
            log_dir = root / "logs"
            log_dir.mkdir()
            real_write = policy._write_json_exclusive
            injected = b'{"status":"execution_passed","classification":"publication_pending"}\n'

            def collide(path: Path, payload: dict[str, object]) -> dict[str, object]:
                if path.name == "current-skill-build.execution.json":
                    path.write_bytes(injected)
                    raise FileExistsError("receipt collision")
                return real_write(path, payload)

            with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                policy, "_write_json_exclusive", side_effect=collide
            ), self.assertRaisesRegex(policy.RunnerError, "execution_infrastructure_failure"):
                policy.run(brief, target, hard_seconds=5, log_dir=log_dir)
            publication = json.loads(
                (log_dir / "current-skill-build.publication-failure.json").read_text(encoding="utf-8")
            )
            self.assertEqual([], list(target.iterdir()))
            self.assertEqual("invalid", publication["execution_receipt"]["state"])
            self.assertEqual(len(injected), publication["execution_receipt"]["bytes"])
            self.assertEqual(
                hashlib.sha256(injected).hexdigest(),
                publication["execution_receipt"]["sha256"],
            )

    def test_success_receipt_write_failure_keeps_target_empty(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, _, environment = self.fixture(root)
            log_dir = root / "logs"
            log_dir.mkdir()
            with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                policy, "_write_json_exclusive", side_effect=OSError("disk full")
            ), self.assertRaises(policy.RunnerError):
                policy.run(brief, target, hard_seconds=5, log_dir=log_dir)
            self.assertEqual([], list(target.iterdir()))

    def test_post_write_receipt_failure_records_publication_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, _, environment = self.fixture(root)
            log_dir = root / "logs"
            log_dir.mkdir()
            real_write = policy._write_json_exclusive

            def write_then_fail(path: Path, payload: dict[str, object]) -> dict[str, object]:
                record = real_write(path, payload)
                if path.name == "current-skill-build.execution.json":
                    raise OSError("post-fsync failure")
                return record

            with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                policy, "_write_json_exclusive", side_effect=write_then_fail
            ), self.assertRaisesRegex(policy.RunnerError, "execution_infrastructure_failure"):
                policy.run(brief, target, hard_seconds=5, log_dir=log_dir)
            self.assertEqual([], list(target.iterdir()))
            execution_path = log_dir / "current-skill-build.execution.json"
            publication = json.loads(
                (log_dir / "current-skill-build.publication-failure.json").read_text(encoding="utf-8")
            )
            self.assertEqual("publication_pending", publication["execution_receipt"]["state"])
            self.assertEqual(
                hashlib.sha256(execution_path.read_bytes()).hexdigest(),
                publication["execution_receipt"]["sha256"],
            )

    def test_successful_replace_is_the_last_fallible_policy_operation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            brief, target, _, environment = self.fixture(root)
            log_dir = root / "logs"
            log_dir.mkdir()
            events: list[str] = []
            real_write = policy._write_json_exclusive
            real_check = policy._target_unchanged
            real_replace = policy.os.replace

            def write(*args: object, **kwargs: object) -> object:
                events.append("receipt")
                return real_write(*args, **kwargs)

            def check(*args: object, **kwargs: object) -> object:
                events.append("target_check")
                return real_check(*args, **kwargs)

            def replace(*args: object, **kwargs: object) -> object:
                events.append("replace")
                return real_replace(*args, **kwargs)

            with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
                policy, "_write_json_exclusive", side_effect=write
            ), mock.patch.object(policy, "_target_unchanged", side_effect=check), mock.patch.object(
                policy.os, "replace", side_effect=replace
            ):
                manifest = policy.run(brief, target, hard_seconds=5, log_dir=log_dir)
            self.assertEqual("completed", manifest["status"])
            self.assertEqual(["receipt", "target_check", "replace"], events)
            self.assertFalse((log_dir / "current-skill-build.publication-failure.json").exists())

    def test_public_execute_isolated_retains_caller_stage_and_returns_generic_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            _, _, _, environment = self.fixture(root)
            stage = root / "stage"
            stage.mkdir()
            trace = root / "trace.jsonl"
            stderr = root / "stderr.txt"
            with mock.patch.dict(os.environ, environment, clear=True):
                receipt = core.execute_isolated(
                    core.ExecutionSpec(
                        stage=stage,
                        stdout_log=trace,
                        stderr_log=stderr,
                        skill_source=ROOT / "wow-frontend-design",
                        skill_name="wow-frontend-design",
                        prompt="Create the caller-owned outputs.",
                        hard_seconds=5,
                        inactivity_seconds=3,
                    )
                )
            self.assertTrue(stage.is_dir())
            self.assertEqual({"DESIGN.md", "index.html"}, {path.name for path in stage.iterdir()})
            self.assertTrue(trace.is_file())
            self.assertTrue(stderr.is_file())
            self.assertEqual("completed", receipt["execution"]["reason"])
            self.assertEqual(3, receipt["execution"]["inactivity_timeout_seconds"])
            self.assertTrue(receipt["trace_observed"]["successful_terminal_event"])
            self.assertFalse(receipt["configured_isolation"]["sandbox_network"])
            self.assertIsNone(receipt["model"]["resolved_backend_snapshot"])
            skill_md = next(
                record for record in receipt["skill_snapshot"]["inventory"] if record["path"] == "SKILL.md"
            )
            self.assertIn("mode", skill_md)

    def test_public_execute_isolated_accepts_and_fingerprints_seeded_stage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            _, _, _, environment = self.fixture(root)
            stage = root / "seeded-stage"
            stage.mkdir()
            (stage / "verified-seed.txt").write_text("seed", encoding="utf-8")
            with mock.patch.dict(os.environ, environment, clear=True):
                receipt = core.execute_isolated(
                    core.ExecutionSpec(
                        stage=stage,
                        stdout_log=root / "trace.jsonl",
                        stderr_log=root / "stderr.txt",
                        skill_source=ROOT / "wow-frontend-design",
                        skill_name="wow-frontend-design",
                        prompt="Repair the seeded stage.",
                        hard_seconds=5,
                    )
                )
            self.assertTrue((stage / "verified-seed.txt").is_file())
            self.assertEqual(1, receipt["execution"]["initial_stage"]["entry_count"])
            self.assertEqual(4, receipt["execution"]["initial_stage"]["bytes"])

    def test_public_execute_isolated_rejects_stage_owned_or_aliased_logs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            stage = root / "stage"
            stage.mkdir()
            cases = (
                (stage / "trace.jsonl", root / "stderr.txt"),
                (root / "combined.log", root / "combined.log"),
            )
            for stdout_log, stderr_log in cases:
                with self.subTest(stdout_log=stdout_log), self.assertRaises(core.RunnerError):
                    core.execute_isolated(
                        core.ExecutionSpec(
                            stage=stage,
                            stdout_log=stdout_log,
                            stderr_log=stderr_log,
                            skill_source=ROOT / "wow-frontend-design",
                            skill_name="wow-frontend-design",
                            prompt="Build.",
                            hard_seconds=5,
                        )
                    )

    def test_execute_isolated_rejects_skill_content_or_mode_drift(self) -> None:
        for mode in ("skill-content-drift", "skill-mode-drift"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                _, _, _, environment = self.fixture(root, mode)
                skill_source = root / "skill-source"
                skill_source.mkdir()
                (skill_source / "SKILL.md").write_text("# Stable skill\n", encoding="utf-8")
                stage = root / "stage"
                stage.mkdir()
                with mock.patch.dict(os.environ, environment, clear=True), self.assertRaisesRegex(
                    core.RunnerError, "skill snapshot provenance drifted"
                ):
                    core.execute_isolated(
                        core.ExecutionSpec(
                            stage=stage,
                            stdout_log=root / "trace.jsonl",
                            stderr_log=root / "stderr.txt",
                            skill_source=skill_source,
                            skill_name="wow-frontend-design",
                            prompt="Build.",
                            hard_seconds=5,
                        )
                    )


if __name__ == "__main__":
    unittest.main()
