#!/usr/bin/env python3
"""Regression tests for the isolated Claude evaluation runner."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evals" / "run_claude_case.sh"
VALIDATOR = ROOT / "evals" / "validate_visual_web_output.py"
CONTEXT_PATHS = (
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
SAFE_HTML = """<!doctype html><html lang="zh-Hant"><head><title>Runner test</title>
<style>body { color: #111; background: #fff; }</style></head>
<body><main id="main"><a href="#main">Main</a></main><script>void 0;</script></body></html>"""
SAFE_CSS = "body { color: #111; background: #fff; }"
SAFE_JS = "document.querySelector('a').addEventListener('click', () => {});"
SAFE_DESIGN = """---
version: alpha
name: Runner Test
colors:
  primary: \"#111111\"
typography:
  body:
    fontFamily: sans-serif
---
# Runner Test
## Overview
Test visual system.
"""


def fixed_target(root: Path, model: str, case_id: str) -> Path:
    return root / "evals" / f"claude-{model}-{case_id}"


class ClaudeRunnerTests(unittest.TestCase):
    @contextmanager
    def fixture(self) -> Iterator[tuple[Path, Path, Path]]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = root / "evals" / "run_claude_case.sh"
            runner.parent.mkdir(parents=True)
            shutil.copy2(RUNNER, runner)
            shutil.copy2(VALIDATOR, root / "evals" / "validate_visual_web_output.py")

            for model in ("haiku", "sonnet", "opus"):
                showcase_target = fixed_target(root, model, "showcase")
                showcase_target.mkdir()
                (showcase_target / "BRIEF.md").write_text("# Fixed showcase test brief\n", encoding="utf-8")
                fixed_target(root, model, "product-dashboard").mkdir()
                fixed_target(root, model, "harbor-cold-chain-v4").mkdir()
                fixed_target(root, model, "island-sound-archive-v4").mkdir()
                fixed_target(root, model, "plant-swap-one-line-v4").mkdir()
            fixed_target(root, "haiku", "product-dashboard-remake").mkdir()
            shared_brief = root / "evals" / "briefs" / "product-dashboard.md"
            shared_brief.parent.mkdir()
            shared_brief.write_text("# Shared product dashboard test brief\n", encoding="utf-8")
            (root / "evals" / "briefs" / "harbor-cold-chain-v4.md").write_text("# Harbor cold-chain test brief\n", encoding="utf-8")
            (root / "evals" / "briefs" / "island-sound-archive-v4.md").write_text("# Island sound archive test brief\n", encoding="utf-8")
            (root / "evals" / "briefs" / "plant-swap-one-line-v4.md").write_text("Build a plant swap website.\n", encoding="utf-8")
            target = fixed_target(root, "haiku", "showcase")
            for relative in CONTEXT_PATHS:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"# {path.name}\n", encoding="utf-8")

            capture = root / "capture"
            capture.mkdir()
            binary = root / "bin" / "claude"
            binary.parent.mkdir()
            binary.write_text(
                """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "--version" ]]; then
  printf '%s\\n' '2.1.999 (Claude Code test stub)'
  exit 0
fi
/usr/bin/env | sort > "$RUNNER_TEST_CAPTURE/env.txt"
printf '%s\\n' "$@" > "$RUNNER_TEST_CAPTURE/args.txt"
command cat > "$RUNNER_TEST_CAPTURE/prompt.txt"
printf '%s' "${RUNNER_TEST_HTML}" > index.html
if [[ "${RUNNER_TEST_CASE_ID}" == *-v4 ]]; then
  printf '%s' "${RUNNER_TEST_DESIGN}" > DESIGN.md
fi
if [[ "${RUNNER_TEST_CASE_ID}" == "plant-swap-one-line-v4" ]]; then
  printf '%s' "${RUNNER_TEST_HTML}" > browse.html
  printf '%s' "${RUNNER_TEST_HTML}" > listing.html
fi
""",
                encoding="utf-8",
            )
            binary.chmod(0o755)
            yield root, target, capture

    def run_case(
        self,
        root: Path,
        target: Path,
        capture: Path,
        *,
        auth_mode: str = "official",
        html: str = SAFE_HTML,
        css: str = SAFE_CSS,
        js: str = SAFE_JS,
        model: str = "haiku",
        case_id: str | None = None,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(
            {
                "PATH": f"{root / 'bin'}{os.pathsep}{environment.get('PATH', '')}",
                "CLAUDE_AUTH_MODE": auth_mode,
                "CLAUDE_RUN_ID": "test-run-001",
                "RUNNER_TEST_CAPTURE": str(capture),
                "RUNNER_TEST_HTML": html,
                "RUNNER_TEST_DESIGN": SAFE_DESIGN,
                "RUNNER_TEST_CASE_ID": case_id or "showcase",
                "RUNNER_TEST_CSS": css,
                "RUNNER_TEST_JS": js,
            }
        )
        if extra_env:
            environment.update(extra_env)
        arguments = [str(root / "evals" / "run_claude_case.sh"), model]
        if case_id is None:
            arguments.append(str(target))
        else:
            arguments.extend(("--case", case_id))
        return subprocess.run(
            arguments,
            cwd=root,
            env=environment,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )

    @staticmethod
    def captured_environment(path: Path) -> dict[str, str]:
        return {
            key: value
            for line in path.read_text(encoding="utf-8").splitlines()
            if "=" in line
            for key, value in [line.split("=", 1)]
        }

    def test_official_mode_clears_provider_environment_but_preserves_oauth(self) -> None:
        contaminated = {
            "ANTHROPIC_API_KEY": "dummy-api-key",
            "ANTHROPIC_AUTH_TOKEN": "dummy-auth-token",
            "ANTHROPIC_BASE_URL": "http://127.0.0.1:9999",
            "ANTHROPIC_MODEL": "dummy-model",
            "ANTHROPIC_CUSTOM_MODEL_OPTION": "dummy-custom-model",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": "dummy-haiku",
            "CLAUDE_CODE_USE_VERTEX": "1",
            "CLAUDE_CODE_USE_BEDROCK": "1",
            "CLAUDE_CODE_USE_MANTLE": "1",
            "CLAUDE_CODE_USE_FOUNDRY": "1",
            "CLAUDE_CODE_USE_ANTHROPIC_AWS": "1",
            "CLAUDE_CODE_EFFORT_LEVEL": "xhigh",
            "CLAUDE_CODE_DISABLE_THINKING": "0",
            "MAX_THINKING_TOKENS": "64000",
            "ANTHROPIC_AWS_API_KEY": "dummy-aws-platform-key",
            "AWS_BEARER_TOKEN_BEDROCK": "dummy-bedrock-key",
            "ANTHROPIC_FOUNDRY_AUTH_TOKEN": "dummy-foundry-token",
            "AWS_ACCESS_KEY_ID": "dummy-aws",
            "GOOGLE_APPLICATION_CREDENTIALS": "/tmp/dummy-google.json",
            "AZURE_CLIENT_SECRET": "dummy-azure",
            "CLAUDE_CODE_OAUTH_TOKEN": "dummy-official-oauth",
        }
        with self.fixture() as (root, target, capture):
            completed = self.run_case(root, target, capture, extra_env=contaminated)
            self.assertEqual(0, completed.returncode, completed.stderr)
            captured = self.captured_environment(capture / "env.txt")
            for name in contaminated:
                if name not in {"CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_EFFORT_LEVEL", "CLAUDE_CODE_DISABLE_THINKING"}:
                    self.assertNotIn(name, captured)
            self.assertEqual("dummy-official-oauth", captured["CLAUDE_CODE_OAUTH_TOKEN"])
            self.assertEqual("auto", captured["CLAUDE_CODE_EFFORT_LEVEL"])
            self.assertEqual("1", captured["CLAUDE_CODE_DISABLE_THINKING"])
            self.assertNotIn("MAX_THINKING_TOKENS", captured)
            self.assertIn("exactly one self-contained index.html", (capture / "prompt.txt").read_text(encoding="utf-8"))

            manifest = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("test-run-001", manifest["run_id"])
            self.assertEqual("official", manifest["auth_mode"])
            self.assertEqual("2.1.999 (Claude Code test stub)", manifest["cli"]["version"])
            self.assertEqual("haiku", manifest["model"]["requested_alias"])
            self.assertEqual(
                {"id": "showcase", "target": "evals/claude-haiku-showcase"},
                manifest["case"],
            )
            self.assertIsNone(manifest["model"]["resolved_exact_model"])
            self.assertEqual("not_reported_by_cli", manifest["model"]["resolution_status"])
            self.assertTrue(manifest["environment"]["official_oauth_state_preserved"])
            self.assertEqual("model_default_auto", manifest["invocation"]["effort"])
            self.assertFalse(manifest["invocation"]["extended_thinking"])
            self.assertIn("ANTHROPIC_API_KEY", manifest["environment"]["cleared_variable_names"])
            self.assertNotIn("CLAUDE_CODE_OAUTH_TOKEN", manifest["environment"]["cleared_variable_names"])
            self.assertEqual(len(CONTEXT_PATHS), len(manifest["context"]["trusted_files"]))
            self.assertTrue(all(len(item["sha256"]) == 64 for item in manifest["context"]["trusted_files"]))
            self.assertEqual(
                hashlib.sha256((root / "evals" / "run_claude_case.sh").read_bytes()).hexdigest(),
                manifest["runner"]["sha256"],
            )
            self.assertEqual(
                hashlib.sha256((root / "evals" / "validate_visual_web_output.py").read_bytes()).hexdigest(),
                manifest["output_validator"]["sha256"],
            )
            self.assertEqual({"index.html"}, {item["path"] for item in manifest["outputs"]})
            for output in manifest["outputs"]:
                self.assertEqual(
                    hashlib.sha256((target / output["path"]).read_bytes()).hexdigest(),
                    output["sha256"],
                )

    def test_inherited_mode_keeps_intentional_api_environment(self) -> None:
        with self.fixture() as (root, target, capture):
            completed = self.run_case(
                root,
                target,
                capture,
                auth_mode="inherited",
                extra_env={"ANTHROPIC_API_KEY": "intentional", "CLAUDE_CODE_USE_VERTEX": "1"},
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            captured = self.captured_environment(capture / "env.txt")
            self.assertEqual("intentional", captured["ANTHROPIC_API_KEY"])
            self.assertEqual("1", captured["CLAUDE_CODE_USE_VERTEX"])
            self.assertEqual("auto", captured["CLAUDE_CODE_EFFORT_LEVEL"])
            self.assertEqual("1", captured["CLAUDE_CODE_DISABLE_THINKING"])
            manifest = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual([], manifest["environment"]["cleared_variable_names"])
            self.assertFalse(manifest["environment"]["official_oauth_state_preserved"])

    def test_matrix_can_isolate_outputs_under_an_evaluator_target_root(self) -> None:
        with self.fixture() as (root, _, capture):
            target_root = root / "independent-run"
            target_root.mkdir()
            target = target_root / "claude-sonnet-island-sound-archive-v4"
            target.mkdir()
            completed = self.run_case(
                root,
                target,
                capture,
                model="sonnet",
                case_id="island-sound-archive-v4",
                extra_env={"PRODUCT_FLOW_TARGET_ROOT": str(target_root)},
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                {"DESIGN.md", "index.html", "run-manifest.json"},
                {path.name for path in target.iterdir()},
            )
            self.assertFalse((fixed_target(root, "sonnet", "island-sound-archive-v4") / "index.html").exists())

    def test_legacy_two_argument_call_keeps_fixed_alias_and_safe_mode(self) -> None:
        with self.fixture() as (root, target, capture):
            completed = self.run_case(root, target, capture)
            self.assertEqual(0, completed.returncode, completed.stderr)
            arguments = (capture / "args.txt").read_text(encoding="utf-8").splitlines()
            self.assertIn("--safe-mode", arguments)
            self.assertEqual("haiku", arguments[arguments.index("--model") + 1])
            self.assertEqual("Write", arguments[arguments.index("--allowedTools") + 1])

    def test_explicit_product_dashboard_case_maps_each_model_to_fixed_target(self) -> None:
        for model in ("haiku", "opus"):
            with self.subTest(model=model), self.fixture() as (root, _, capture):
                target = fixed_target(root, model, "product-dashboard")
                completed = self.run_case(
                    root,
                    target,
                    capture,
                    model=model,
                    case_id="product-dashboard",
                )
                self.assertEqual(0, completed.returncode, completed.stderr)
                self.assertIn(
                    "# Shared product dashboard test brief",
                    (capture / "prompt.txt").read_text(encoding="utf-8"),
                )
                manifest = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(model, manifest["model"]["requested_alias"])
                self.assertEqual(
                    {
                        "id": "product-dashboard",
                        "target": f"evals/claude-{model}-product-dashboard",
                    },
                    manifest["case"],
                )
                self.assertEqual(
                    "evals/briefs/product-dashboard.md",
                    manifest["context"]["brief"]["path"],
                )
                self.assertEqual(
                    {"index.html", "run-manifest.json"},
                    {path.name for path in target.iterdir()},
                )

    def test_single_remake_maps_only_haiku_to_fresh_target_and_shared_brief(self) -> None:
        with self.fixture() as (root, _, capture):
            target = fixed_target(root, "haiku", "product-dashboard-remake")
            completed = self.run_case(
                root,
                target,
                capture,
                model="haiku",
                case_id="product-dashboard-remake",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            manifest = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                {
                    "id": "product-dashboard-remake",
                    "target": "evals/claude-haiku-product-dashboard-remake",
                },
                manifest["case"],
            )
            self.assertEqual(
                "evals/briefs/product-dashboard.md",
                manifest["context"]["brief"]["path"],
            )
            self.assertIn(
                "wow-frontend-design/references/anti-ai-slop.md",
                {item["path"] for item in manifest["context"]["trusted_files"]},
            )

        with self.fixture() as (root, _, capture):
            rejected = self.run_case(
                root,
                fixed_target(root, "haiku", "product-dashboard-remake"),
                capture,
                model="opus",
                case_id="product-dashboard-remake",
            )
            self.assertEqual(2, rejected.returncode, rejected.stderr)
            self.assertIn("single approved haiku remediation run", rejected.stderr)
            self.assertFalse((capture / "args.txt").exists())

    def test_flow_themes_map_every_model_to_their_fixed_brief(self) -> None:
        for case_id, expected_text in (
            ("harbor-cold-chain-v4", "# Harbor cold-chain test brief"),
            ("island-sound-archive-v4", "# Island sound archive test brief"),
            ("plant-swap-one-line-v4", "Build a plant swap website."),
        ):
            for model in ("haiku", "sonnet", "opus"):
                with self.subTest(case_id=case_id, model=model), self.fixture() as (root, _, capture):
                    target = fixed_target(root, model, case_id)
                    completed = self.run_case(root, target, capture, model=model, case_id=case_id)
                    self.assertEqual(0, completed.returncode, completed.stderr)
                    manifest = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
                    self.assertEqual(case_id, manifest["case"]["id"])
                    self.assertEqual(f"evals/briefs/{case_id}.md", manifest["context"]["brief"]["path"])
                    self.assertIn(
                        expected_text,
                        (capture / "prompt.txt").read_text(encoding="utf-8"),
                    )
                    expected_outputs = {"DESIGN.md", "index.html", "run-manifest.json"}
                    if case_id == "plant-swap-one-line-v4":
                        expected_outputs.update({"browse.html", "listing.html"})
                    self.assertEqual(expected_outputs, {path.name for path in target.iterdir()})

    def test_case_and_legacy_target_reject_traversal_or_arbitrary_paths(self) -> None:
        with self.fixture() as (root, target, capture):
            attempts = (
                (target, "../product-dashboard"),
                (root / "evals" / "missing" / ".." / "claude-haiku-showcase", None),
                (fixed_target(root, "opus", "showcase"), None),
            )
            for attempted_target, case_id in attempts:
                with self.subTest(target=str(attempted_target), case_id=case_id):
                    completed = self.run_case(
                        root,
                        attempted_target,
                        capture,
                        case_id=case_id,
                    )
                    self.assertEqual(2, completed.returncode, completed.stderr)
            self.assertFalse((capture / "args.txt").exists())

if __name__ == "__main__":
    unittest.main()
