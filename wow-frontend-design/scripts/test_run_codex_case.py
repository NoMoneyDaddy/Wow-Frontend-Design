#!/usr/bin/env python3
"""Regression tests for the isolated Codex model-matrix runner."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evals" / "run_codex_case.sh"
VALIDATOR = ROOT / "evals" / "validate_visual_web_output.py"
DESIGN_VALIDATOR = ROOT / "evals" / "validate_design_md_clean.py"
TRACE_VALIDATOR = ROOT / "evals" / "validate_codex_log_policy.py"
RESOURCE_MONITOR = ROOT / "evals" / "monitor_codex_progress.py"
CONTEXTS = (
    "wow-frontend-design/SKILL.md",
    "wow-frontend-design/references/creative-direction.md",
    "wow-frontend-design/references/anti-ai-slop.md",
    "wow-frontend-design/references/mobile-responsive.md",
    "wow-frontend-design/references/localization.md",
    "wow-frontend-design/references/typography-webfonts.md",
    "wow-frontend-design/references/typographic-layout.md",
    "wow-frontend-design/references/implementation.md",
    "wow-frontend-design/references/component-composition.md",
    "wow-frontend-design/references/quality-gates.md",
    "wow-frontend-design/references/weak-model-playbook.md",
    "wow-frontend-design/references/color-system-psychology.md",
    "wow-frontend-design/references/design-md-contract.md",
    "wow-frontend-design/assets/DESIGN.template.md",
)
BASE_CONTEXTS = (
    "wow-frontend-design/SKILL.md",
    "wow-frontend-design/references/creative-direction.md",
    "wow-frontend-design/references/anti-ai-slop.md",
    "wow-frontend-design/references/mobile-responsive.md",
    "wow-frontend-design/references/localization.md",
    "wow-frontend-design/references/typographic-layout.md",
    "wow-frontend-design/references/implementation.md",
    "wow-frontend-design/references/design-md-contract.md",
    "wow-frontend-design/assets/DESIGN.template.md",
)
SAFE_HTML = '<!doctype html><html lang="zh-Hant"><head><title>Test</title><style>body{color:#111}</style></head><body><main id="main"><a href="#main">Main</a></main><script>void 0;</script></body></html>'
SAFE_CSS = "body { color: #111; background: #fff; }"
SAFE_JS = "document.querySelector('a').addEventListener('click', () => {});"
SAFE_DESIGN = "---\nversion: alpha\nname: Runner Test\ncolors:\n  primary: \"#111111\"\n---\n# Runner Test\n## Overview\nTest.\n"
V6_CASES = (
    "wind-maintenance-dispatch-v6",
    "type-foundry-specimen-v6",
    "repair-cafe-intake-v6",
    "night-market-allergen-v6",
    "royalty-statement-v6",
    "packaging-configurator-v6",
    "oral-history-archive-v6",
    "grant-review-board-v6",
)


class CodexRunnerTests(unittest.TestCase):
    def fixture(self, root: Path) -> Path:
        (root / "evals" / "briefs").mkdir(parents=True)
        shutil.copy2(RUNNER, root / "evals" / "run_codex_case.sh")
        shutil.copy2(VALIDATOR, root / "evals" / "validate_visual_web_output.py")
        shutil.copy2(DESIGN_VALIDATOR, root / "evals" / "validate_design_md_clean.py")
        shutil.copy2(TRACE_VALIDATOR, root / "evals" / "validate_codex_log_policy.py")
        shutil.copy2(RESOURCE_MONITOR, root / "evals" / "monitor_codex_progress.py")
        shutil.copy2(ROOT / "package-lock.json", root / "package-lock.json")
        (root / "evals" / "briefs" / "harbor-cold-chain-v4.md").write_text("# Harbor cold-chain brief\n", encoding="utf-8")
        (root / "evals" / "briefs" / "island-sound-archive-v4.md").write_text("# Island sound archive brief\n", encoding="utf-8")
        (root / "evals" / "briefs" / "plant-swap-one-line-v4.md").write_text("Build a plant swap website.\n", encoding="utf-8")
        (root / "evals" / "briefs" / "rail-rebooking-v5.md").write_text("# Rail rebooking v5 brief\n", encoding="utf-8")
        (root / "evals" / "briefs" / "subscription-audit-v5.md").write_text("# Subscription audit v5 brief\n", encoding="utf-8")
        (root / "evals" / "briefs" / "community-translation-v5.md").write_text("# Community translation v5 brief\n", encoding="utf-8")
        (root / "evals" / "briefs" / "ceramics-festival-one-line-v5.md").write_text("Build a ceramics festival website.\n", encoding="utf-8")
        for case_id in V6_CASES:
            (root / "evals" / "briefs" / f"{case_id}.md").write_text(f"# {case_id} brief\n", encoding="utf-8")
        for model in ("gpt-5.4-mini", "gpt-5.4", "gpt-5.5"):
            for case_id in (
                "harbor-cold-chain-v4",
                "island-sound-archive-v4",
                "plant-swap-one-line-v4",
                "rail-rebooking-v5",
                "subscription-audit-v5",
                "community-translation-v5",
                "ceramics-festival-one-line-v5",
                *V6_CASES,
            ):
                (root / "evals" / f"codex-{model}-{case_id}").mkdir()
        for relative in CONTEXTS:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {path.name}\n", encoding="utf-8")
        capture = root / "capture"
        capture.mkdir()
        codex_home = root / "codex-home"
        codex_home.mkdir()
        (codex_home / "auth.json").write_text("{}\n", encoding="utf-8")
        binary = root / "bin" / "codex"
        binary.parent.mkdir()
        binary.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "--version" ]]; then
  echo 'codex-cli 9.9.9-test'
  exit 0
fi
if [[ "${1:-}" == "login" && "${2:-}" == "status" ]]; then
  echo 'Logged in using ChatGPT'
  exit 0
fi
TEST_ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
CAPTURE="$TEST_ROOT/capture"
/usr/bin/env | sort > "$CAPTURE/env.txt"
printf '%s\n' "$@" > "$CAPTURE/args.txt"
command cat > "$CAPTURE/prompt.txt"
args=("$@")
stage=""
model=""
for ((i=0; i<${#args[@]}; i++)); do
  if [[ "${args[$i]}" == "--cd" ]]; then stage="${args[$((i+1))]}"; fi
  if [[ "${args[$i]}" == "--model" ]]; then model="${args[$((i+1))]}"; fi
done
if [[ -z "$stage" || -z "$model" ]]; then exit 9; fi
html='<!doctype html><html lang="zh-Hant"><head><title>Test</title><style>body{color:#111}</style></head><body><main id="main"><a href="#main">Main</a></main><script>void 0;</script></body></html>'
design=$'---\nversion: alpha\nname: Runner Test\ncolors:\n  primary: "#111111"\n---\n# Runner Test\n## Overview\nTest.\n'
printf '%s' "$html" > "$stage/index.html"
printf '%s' "$design" > "$stage/DESIGN.md"
if grep -Fq 'browse.html' "$CAPTURE/prompt.txt"; then
  printf '%s' "$html" > "$stage/browse.html"
  printf '%s' "$html" > "$stage/listing.html"
fi
if grep -Fq 'program.html' "$CAPTURE/prompt.txt"; then
  printf '%s' "$html" > "$stage/program.html"
  printf '%s' "$html" > "$stage/visit.html"
fi
if grep -Fq 'materials.html' "$CAPTURE/prompt.txt"; then
  printf '%s' "$html" > "$stage/materials.html"
  printf '%s' "$html" > "$stage/summary.html"
fi
if grep -Fq 'archive.html' "$CAPTURE/prompt.txt"; then
  printf '%s' "$html" > "$stage/archive.html"
  printf '%s' "$html" > "$stage/story.html"
fi
if [[ -f "$CAPTURE/oversized-output" ]]; then
  dd if=/dev/zero of="$stage/index.html" bs=1048576 count=2 2>/dev/null
  for part in 1 2 3 4; do
    dd if=/dev/zero of="$stage/quota-$part.tmp" bs=1048576 count=2 2>/dev/null
  done
  sleep 5
fi
if [[ -f "$CAPTURE/codex-log-line.txt" ]]; then
  command cat "$CAPTURE/codex-log-line.txt"
fi
""",
            encoding="utf-8",
        )
        binary.chmod(0o755)
        npx = root / "bin" / "npx"
        npx.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
if [[ -n "${RUNNER_TEST_DESIGN_LINT_JSON:-}" ]]; then
  printf '%s\n' "$RUNNER_TEST_DESIGN_LINT_JSON"
else
  printf '%s\n' '{"summary":{"errors":0,"warnings":0,"infos":0},"findings":[]}'
fi
""",
            encoding="utf-8",
        )
        npx.chmod(0o755)
        return capture

    def run_case(
        self,
        root: Path,
        capture: Path,
        model: str,
        case_id: str = "harbor-cold-chain-v4",
        js: str = SAFE_JS,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(
            {
                "PATH": f"{root / 'bin'}{os.pathsep}{environment.get('PATH', '')}",
                "CODEX_HOME": str(root / "codex-home"),
                "CODEX_RUN_ID": "codex-test-run-001",
                "RUNNER_TEST_CAPTURE": str(capture),
                "RUNNER_TEST_HTML": SAFE_HTML,
                "RUNNER_TEST_DESIGN": SAFE_DESIGN,
                "RUNNER_TEST_CASE_ID": case_id,
                "RUNNER_TEST_CSS": SAFE_CSS,
                "RUNNER_TEST_JS": js,
                "OPENAI_API_KEY": "must-be-cleared",
                "OPENAI_BASE_URL": "https://must-be-cleared.invalid",
                "OPENAI_API_BASE": "https://must-also-be-cleared.invalid",
                "CODEX_API_KEY": "must-be-cleared",
                "DATABASE_URL": "postgres://must-not-reach-codex-process",
            }
        )
        if extra_env:
            environment.update(extra_env)
            log_line = extra_env.get("RUNNER_TEST_CODEX_LOG")
            if log_line is not None:
                (capture / "codex-log-line.txt").write_text(log_line + "\n", encoding="utf-8")
        return subprocess.run(
            [str(root / "evals" / "run_codex_case.sh"), model, "--case", case_id],
            cwd=root,
            env=environment,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )

    def test_matrix_can_isolate_outputs_under_an_evaluator_target_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = self.fixture(root)
            target_root = root / "independent-run"
            target_root.mkdir()
            target = target_root / "codex-gpt-5.4-island-sound-archive-v4"
            target.mkdir()
            completed = self.run_case(
                root,
                capture,
                "gpt-5.4",
                "island-sound-archive-v4",
                extra_env={"PRODUCT_FLOW_TARGET_ROOT": str(target_root)},
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                {"DESIGN.md", "index.html", "run-manifest.json"},
                {path.name for path in target.iterdir()},
            )
            self.assertFalse((root / "evals" / "codex-gpt-5.4-island-sound-archive-v4" / "index.html").exists())
            manifest = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("independent-run/codex-gpt-5.4-island-sound-archive-v4", manifest["case"]["target"])

    def test_all_requested_models_share_isolation_contract(self) -> None:
        for model in ("gpt-5.4-mini", "gpt-5.4", "gpt-5.5"):
            with self.subTest(model=model), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                capture = self.fixture(root)
                completed = self.run_case(root, capture, model)
                self.assertEqual(0, completed.returncode, completed.stderr)
                arguments = (capture / "args.txt").read_text(encoding="utf-8").splitlines()
                self.assertEqual(model, arguments[arguments.index("--model") + 1])
                self.assertIn("workspace-write", arguments)
                self.assertIn("--ignore-user-config", arguments)
                self.assertIn("--ignore-rules", arguments)
                self.assertIn("--strict-config", arguments)
                enabled = [arguments[index + 1] for index, value in enumerate(arguments[:-1]) if value == "--enable"]
                disabled = [arguments[index + 1] for index, value in enumerate(arguments[:-1]) if value == "--disable"]
                self.assertEqual([], enabled)
                self.assertEqual(
                    [
                        "apps",
                        "multi_agent",
                        "browser_use",
                        "computer_use",
                        "image_generation",
                        "plugins",
                        "skill_mcp_dependency_install",
                        "tool_call_mcp_elicitation",
                        "tool_suggest",
                    ],
                    disabled,
                )
                self.assertIn('model_reasoning_summary="none"', arguments)
                self.assertIn('shell_environment_policy.inherit="none"', arguments)
                self.assertTrue(any(value.startswith("shell_environment_policy.set={PATH=") for value in arguments))
                self.assertNotIn("model_reasoning_effort", "\n".join(arguments))
                prompt = (capture / "prompt.txt").read_text(encoding="utf-8")
                self.assertIn("# Harbor cold-chain brief", prompt)
                self.assertIn("Create exactly DESIGN.md and one self-contained index.html", prompt)
                self.assertIn("Do not spawn subagents", prompt)
                self.assertIn("do not run git status, git diff", prompt)
                self.assertIn("Do not discover or read installed skills", prompt)
                self.assertIn("the independent evaluator owns browser interaction", prompt)
                self.assertIn("Every executed shell command must use literal arguments and literal filenames", prompt)
                self.assertIn(
                    "Dollar signs, asterisks, question marks, square brackets, curly braces, and backticks are forbidden anywhere in the command string, including quoted code or regular expressions",
                    prompt,
                )
                self.assertIn("Do not use inline python -c, node -e, heredocs", prompt)
                self.assertIn("skip that optional check and leave it to the evaluator-owned post-run gates", prompt)
                target = root / "evals" / f"codex-{model}-harbor-cold-chain-v4"
                manifest = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(model, manifest["model"]["requested_identifier"])
                self.assertEqual("openai-first-party-chatgpt-oauth", manifest["provider"])
                self.assertEqual("Logged in using ChatGPT", manifest["authentication"]["status"])
                self.assertEqual(
                    {"effort": "model_default", "summary": "none", "internal_reasoning_disable_supported": False},
                    manifest["reasoning"],
                )
                captured_environment = (capture / "env.txt").read_text(encoding="utf-8")
                self.assertNotIn("OPENAI_API_KEY=", captured_environment)
                self.assertNotIn("OPENAI_BASE_URL=", captured_environment)
                self.assertNotIn("OPENAI_API_BASE=", captured_environment)
                self.assertNotIn("CODEX_API_KEY=", captured_environment)
                self.assertNotIn("DATABASE_URL=", captured_environment)
                self.assertNotIn("RUNNER_TEST_", captured_environment)
                self.assertIn("/wow-codex-home.", captured_environment)
                self.assertNotIn("node_modules/.bin", captured_environment)
                self.assertTrue(manifest["environment"]["user_skills_hidden_by_isolated_home"])
                self.assertEqual("passed", manifest["environment"]["forbidden_host_path_audit"])
                self.assertEqual("none", manifest["environment"]["process_environment_inheritance"])
                self.assertEqual("none", manifest["environment"]["model_shell_environment_inheritance"])
                self.assertFalse(manifest["isolation"]["builder_subagents"])
                self.assertFalse(manifest["isolation"]["builder_browser_tools"])
                self.assertFalse(manifest["isolation"]["builder_computer_tools"])
                self.assertTrue(manifest["isolation"]["independent_visual_evaluator_required"])
                expected_count = len(BASE_CONTEXTS) + 1 + (1 if model == "gpt-5.4-mini" else 0)
                self.assertEqual(expected_count, len(manifest["context"]["trusted_files"]))
                self.assertEqual(
                    {
                        "policy": "caller_model_and_case",
                        "lane": "CONSTRAINED",
                        "selected_file_count": expected_count,
                    },
                    manifest["context"]["routing"],
                )
                selected_context = {item["path"] for item in manifest["context"]["trusted_files"]}
                self.assertIn("wow-frontend-design/references/component-composition.md", selected_context)
                self.assertNotIn("wow-frontend-design/references/quality-gates.md", selected_context)
                self.assertEqual(
                    model == "gpt-5.4-mini",
                    "wow-frontend-design/references/weak-model-playbook.md" in selected_context,
                )
                self.assertEqual(
                    hashlib.sha256((root / "evals" / "run_codex_case.sh").read_bytes()).hexdigest(),
                    manifest["runner"]["sha256"],
                )
                self.assertEqual(
                    hashlib.sha256((root / "evals" / "validate_visual_web_output.py").read_bytes()).hexdigest(),
                    manifest["output_validator"]["sha256"],
                )
                self.assertEqual(
                    "zero_errors_zero_warnings",
                    manifest["design_linter_gate"]["required_result"],
                )
                self.assertEqual(
                    "no_forbidden_commands_or_tools",
                    manifest["trace_policy_gate"]["required_result"],
                )
                self.assertEqual(
                    {"DESIGN.md", "index.html", "run-manifest.json"},
                    {path.name for path in target.iterdir()},
                )
                for output in manifest["outputs"]:
                    self.assertEqual(hashlib.sha256((target / output["path"]).read_bytes()).hexdigest(), output["sha256"])

    def test_arbitrary_model_or_case_is_rejected_before_cli_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = self.fixture(root)
            for arguments in (("gpt-unknown", "harbor-cold-chain-v4"), ("gpt-5.4", "../escape")):
                completed = self.run_case(root, capture, arguments[0], arguments[1])
                self.assertEqual(2, completed.returncode, completed.stderr)
            self.assertFalse((capture / "args.txt").exists())

    def test_v5_ceramics_case_publishes_exact_three_page_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = self.fixture(root)
            completed = self.run_case(root, capture, "gpt-5.4", "ceramics-festival-one-line-v5")
            self.assertEqual(0, completed.returncode, completed.stderr)
            target = root / "evals" / "codex-gpt-5.4-ceramics-festival-one-line-v5"
            self.assertEqual(
                {"DESIGN.md", "index.html", "program.html", "visit.html", "run-manifest.json"},
                {path.name for path in target.iterdir()},
            )
            manifest = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                {"DESIGN.md", "index.html", "program.html", "visit.html"},
                {item["path"] for item in manifest["outputs"]},
            )

    def test_v6_packaging_case_publishes_exact_three_page_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = self.fixture(root)
            completed = self.run_case(root, capture, "gpt-5.4-mini", "packaging-configurator-v6")
            self.assertEqual(0, completed.returncode, completed.stderr)
            target = root / "evals" / "codex-gpt-5.4-mini-packaging-configurator-v6"
            self.assertEqual(
                {"DESIGN.md", "index.html", "materials.html", "summary.html", "run-manifest.json"},
                {path.name for path in target.iterdir()},
            )
            manifest = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                {"DESIGN.md", "index.html", "materials.html", "summary.html"},
                {item["path"] for item in manifest["outputs"]},
            )
            selected_context = {item["path"] for item in manifest["context"]["trusted_files"]}
            self.assertIn("wow-frontend-design/references/component-composition.md", selected_context)
            self.assertIn("wow-frontend-design/references/color-system-psychology.md", selected_context)
            self.assertNotIn("wow-frontend-design/references/typography-webfonts.md", selected_context)

    def test_type_case_routes_font_reference_without_component_reference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = self.fixture(root)
            completed = self.run_case(root, capture, "gpt-5.4-mini", "type-foundry-specimen-v6")
            self.assertEqual(0, completed.returncode, completed.stderr)
            target = root / "evals" / "codex-gpt-5.4-mini-type-foundry-specimen-v6"
            manifest = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
            selected_context = {item["path"] for item in manifest["context"]["trusted_files"]}
            self.assertIn("wow-frontend-design/references/typography-webfonts.md", selected_context)
            self.assertNotIn("wow-frontend-design/references/component-composition.md", selected_context)

    def test_design_md_findings_are_rejected_before_publish(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = self.fixture(root)
            completed = self.run_case(
                root,
                capture,
                "gpt-5.4",
                extra_env={
                    "RUNNER_TEST_DESIGN_LINT_JSON": json.dumps(
                        {
                            "summary": {"errors": 0, "warnings": 1, "infos": 0},
                            "findings": [{"message": "orphan color"}],
                        }
                    )
                },
            )
            self.assertEqual(1, completed.returncode, completed.stderr)
            self.assertIn("clean gate rejected findings", completed.stderr)
            target = root / "evals" / "codex-gpt-5.4-harbor-cold-chain-v4"
            self.assertEqual(set(), {path.name for path in target.iterdir()})

    def test_host_skill_discovery_is_rejected_before_publish(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = self.fixture(root)
            forbidden = root / "codex-home" / "skills" / "unexpected" / "SKILL.md"
            completed = self.run_case(
                root,
                capture,
                "gpt-5.4",
                extra_env={"RUNNER_TEST_CODEX_LOG": str(forbidden)},
            )
            self.assertEqual(2, completed.returncode, completed.stderr)
            self.assertIn("isolation audit rejected host discovery", completed.stderr)
            target = root / "evals" / "codex-gpt-5.4-harbor-cold-chain-v4"
            self.assertEqual(set(), {path.name for path in target.iterdir()})

    def test_forbidden_command_trace_is_rejected_before_publish(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = self.fixture(root)
            trace_event = json.dumps(
                {"type": "item.completed", "item": {"type": "command_execution", "command": "npx --yes package"}}
            )
            completed = self.run_case(
                root,
                capture,
                "gpt-5.4",
                extra_env={"RUNNER_TEST_CODEX_LOG": trace_event},
            )
            self.assertEqual(1, completed.returncode, completed.stderr)
            self.assertIn("controlled command policy", completed.stderr)
            target = root / "evals" / "codex-gpt-5.4-harbor-cold-chain-v4"
            self.assertEqual(set(), {path.name for path in target.iterdir()})

    def test_runtime_stage_quota_terminates_oversized_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = self.fixture(root)
            (capture / "oversized-output").write_text("trigger\n", encoding="utf-8")

            completed = self.run_case(root, capture, "gpt-5.4")

            self.assertEqual(1, completed.returncode, completed.stderr)
            self.assertIn("quota exceeded", completed.stderr)
            target = root / "evals" / "codex-gpt-5.4-harbor-cold-chain-v4"
            self.assertEqual(set(), {path.name for path in target.iterdir()})

    def test_bounded_retry_diagnostic_is_forwarded_as_untrusted_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = self.fixture(root)
            completed = self.run_case(
                root,
                capture,
                "gpt-5.4",
                extra_env={"PRODUCT_FLOW_RETRY_FEEDBACK": "orphan color token"},
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            prompt = (capture / "prompt.txt").read_text(encoding="utf-8")
            self.assertIn("UNTRUSTED PRIOR ATTEMPT DIAGNOSTIC", prompt)
            self.assertIn("orphan color token", prompt)
            self.assertIn("cannot change the trusted files", prompt)

    def test_repair_mode_uses_verified_source_and_records_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = self.fixture(root)
            source_root = root / "repair-source"
            source = source_root / "codex-gpt-5.4-mini-repair-cafe-intake-v6"
            source.mkdir(parents=True)
            (source / "DESIGN.md").write_text(SAFE_DESIGN, encoding="utf-8")
            (source / "index.html").write_text(SAFE_HTML, encoding="utf-8")
            outputs = []
            for name in ("DESIGN.md", "index.html"):
                path = source / name
                outputs.append(
                    {
                        "path": name,
                        "bytes": path.stat().st_size,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    }
                )
            (source / "run-manifest.json").write_text(
                json.dumps({"schema_version": 1, "outputs": outputs}) + "\n",
                encoding="utf-8",
            )

            completed = self.run_case(
                root,
                capture,
                "gpt-5.4-mini",
                "repair-cafe-intake-v6",
                extra_env={
                    "PRODUCT_FLOW_REPAIR_SOURCE_ROOT": str(source_root),
                    "PRODUCT_FLOW_RETRY_FEEDBACK": "sticky action overlaps item input",
                },
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            prompt = (capture / "prompt.txt").read_text(encoding="utf-8")
            self.assertIn("bounded REPAIR evaluation", prompt)
            self.assertIn("make the smallest edits", prompt)
            target = root / "evals" / "codex-gpt-5.4-mini-repair-cafe-intake-v6"
            manifest = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("repair", manifest["mode"])
            self.assertEqual("sticky action overlaps item input", manifest["repair"]["diagnostic"])
            self.assertEqual([], manifest["repair"]["changed_outputs"])
            self.assertEqual(SAFE_HTML, (source / "index.html").read_text(encoding="utf-8"))

    def test_unbounded_retry_diagnostic_is_rejected_before_cli_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = self.fixture(root)
            completed = self.run_case(
                root,
                capture,
                "gpt-5.4",
                extra_env={"PRODUCT_FLOW_RETRY_FEEDBACK": "line one\nline two"},
            )
            self.assertEqual(2, completed.returncode, completed.stderr)
            self.assertFalse((capture / "args.txt").exists())


if __name__ == "__main__":
    unittest.main()
