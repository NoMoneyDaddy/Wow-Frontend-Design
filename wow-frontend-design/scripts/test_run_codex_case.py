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
CONTEXTS = (
    "wow-frontend-design/SKILL.md",
    "wow-frontend-design/references/creative-direction.md",
    "wow-frontend-design/references/anti-ai-slop.md",
    "wow-frontend-design/references/mobile-responsive.md",
    "wow-frontend-design/references/localization.md",
    "wow-frontend-design/references/typography-webfonts.md",
    "wow-frontend-design/references/implementation.md",
    "wow-frontend-design/references/component-composition.md",
    "wow-frontend-design/references/quality-gates.md",
    "wow-frontend-design/references/weak-model-playbook.md",
    "wow-frontend-design/references/color-system-psychology.md",
    "wow-frontend-design/references/design-md-contract.md",
    "wow-frontend-design/assets/DESIGN.template.md",
)
SAFE_HTML = '<!doctype html><html lang="zh-Hant"><head><title>Test</title><style>body{color:#111}</style></head><body><main id="main"><a href="#main">Main</a></main><script>void 0;</script></body></html>'
SAFE_CSS = "body { color: #111; background: #fff; }"
SAFE_JS = "document.querySelector('a').addEventListener('click', () => {});"
SAFE_DESIGN = "---\nversion: alpha\nname: Runner Test\ncolors:\n  primary: \"#111111\"\n---\n# Runner Test\n## Overview\nTest.\n"


class CodexRunnerTests(unittest.TestCase):
    def fixture(self, root: Path) -> Path:
        (root / "evals" / "briefs").mkdir(parents=True)
        shutil.copy2(RUNNER, root / "evals" / "run_codex_case.sh")
        shutil.copy2(VALIDATOR, root / "evals" / "validate_visual_web_output.py")
        (root / "evals" / "briefs" / "mountain-rescue-flow-v3.md").write_text("# Mountain rescue flow brief\n", encoding="utf-8")
        (root / "evals" / "briefs" / "city-poetry-festival-v3.md").write_text("# City poetry festival brief\n", encoding="utf-8")
        (root / "evals" / "briefs" / "bookstore-one-line-v3.md").write_text("Build a bookstore website.\n", encoding="utf-8")
        for model in ("gpt-5.4-mini", "gpt-5.4", "gpt-5.5"):
            for case_id in ("mountain-rescue-flow-v3", "city-poetry-festival-v3", "bookstore-one-line-v3"):
                (root / "evals" / f"codex-{model}-{case_id}").mkdir()
        for relative in CONTEXTS:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {path.name}\n", encoding="utf-8")
        capture = root / "capture"
        capture.mkdir()
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
/usr/bin/env | sort > "$RUNNER_TEST_CAPTURE/env.txt"
printf '%s\n' "$@" > "$RUNNER_TEST_CAPTURE/args.txt"
command cat > "$RUNNER_TEST_CAPTURE/prompt.txt"
args=("$@")
stage=""
for ((i=0; i<${#args[@]}; i++)); do
  if [[ "${args[$i]}" == "--cd" ]]; then stage="${args[$((i+1))]}"; fi
done
if [[ -z "$stage" ]]; then exit 9; fi
printf '%s' "$RUNNER_TEST_HTML" > "$stage/index.html"
printf '%s' "$RUNNER_TEST_DESIGN" > "$stage/DESIGN.md"
if [[ "$RUNNER_TEST_CASE_ID" == "bookstore-one-line-v3" ]]; then
  printf '%s' "$RUNNER_TEST_HTML" > "$stage/catalog.html"
  printf '%s' "$RUNNER_TEST_HTML" > "$stage/book.html"
fi
""",
            encoding="utf-8",
        )
        binary.chmod(0o755)
        return capture

    def run_case(self, root: Path, capture: Path, model: str, case_id: str = "mountain-rescue-flow-v3", js: str = SAFE_JS) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(
            {
                "PATH": f"{root / 'bin'}{os.pathsep}{environment.get('PATH', '')}",
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
            }
        )
        return subprocess.run(
            [str(root / "evals" / "run_codex_case.sh"), model, "--case", case_id],
            cwd=root,
            env=environment,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )

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
                self.assertIn('model_reasoning_summary="none"', arguments)
                self.assertNotIn("model_reasoning_effort", "\n".join(arguments))
                prompt = (capture / "prompt.txt").read_text(encoding="utf-8")
                self.assertIn("# Mountain rescue flow brief", prompt)
                self.assertIn("Create exactly DESIGN.md and one self-contained index.html", prompt)
                target = root / "evals" / f"codex-{model}-mountain-rescue-flow-v3"
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
                self.assertEqual(len(CONTEXTS), len(manifest["context"]["trusted_files"]))
                self.assertEqual(
                    hashlib.sha256((root / "evals" / "run_codex_case.sh").read_bytes()).hexdigest(),
                    manifest["runner"]["sha256"],
                )
                self.assertEqual(
                    hashlib.sha256((root / "evals" / "validate_visual_web_output.py").read_bytes()).hexdigest(),
                    manifest["output_validator"]["sha256"],
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
            for arguments in (("gpt-unknown", "mountain-rescue-flow-v3"), ("gpt-5.4", "../escape")):
                completed = self.run_case(root, capture, arguments[0], arguments[1])
                self.assertEqual(2, completed.returncode, completed.stderr)
            self.assertFalse((capture / "args.txt").exists())


if __name__ == "__main__":
    unittest.main()
