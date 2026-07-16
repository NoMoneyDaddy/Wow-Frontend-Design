#!/usr/bin/env python3
"""Tests for the fail-closed v7 public cohort freeze."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "evals" / "v7_preflight.py"
SPEC = importlib.util.spec_from_file_location("v7_preflight", MODULE_PATH)
assert SPEC and SPEC.loader
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


class V7PreflightTests(unittest.TestCase):
    def _git(self, root: Path, *arguments: str) -> str:
        return subprocess.run(
            ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()

    def _repository(self, directory: str) -> tuple[Path, Path, dict[str, object], str]:
        root = Path(directory)
        (root / "wow-frontend-design" / "references").mkdir(parents=True)
        (root / "evals").mkdir()
        (root / "wow-frontend-design" / "SKILL.md").write_text(
            "---\nname: wow-frontend-design\ndescription: test\n---\n", encoding="utf-8"
        )
        (root / "wow-frontend-design" / "references" / "typographic-layout.md").write_text(
            "# Typography\n", encoding="utf-8"
        )
        for name in ("runner.py", "auditor.py", "evidence.py"):
            (root / "evals" / name).write_text(f"# {name}\n", encoding="utf-8")
        package_lock = {
            "packages": {
                "node_modules/playwright": {
                    "version": "1.2.3",
                    "resolved": "https://registry.npmjs.org/playwright/-/playwright-1.2.3.tgz",
                    "integrity": "sha512-playwright",
                },
                "node_modules/@google/design.md": {
                    "version": "0.3.0",
                    "resolved": "https://registry.npmjs.org/@google/design.md/-/design.md-0.3.0.tgz",
                    "integrity": "sha512-designmd",
                },
            }
        }
        (root / "package-lock.json").write_text(json.dumps(package_lock), encoding="utf-8")
        self._git(root, "init", "-q")
        self._git(root, "config", "user.name", "Test")
        self._git(root, "config", "user.email", "test@example.invalid")
        self._git(root, "add", ".")
        self._git(root, "commit", "-qm", "baseline")
        commit = self._git(root, "rev-parse", "HEAD")
        cases = []
        split_specs = (("development", 2), ("sealed_validation", 4), ("sealed_test", 2))
        splits: dict[str, list[dict[str, object]]] = {}
        serial = 0
        for split, count in split_specs:
            split_cases = []
            for _ in range(count):
                serial += 1
                case = {
                    "id": f"case-{serial}",
                    "family": f"Family number {serial}",
                    "primary_task": f"Complete the bounded primary task for public case {serial}.",
                    "pressures": ["繁中長標題", "混合語系資料"],
                    "required_states": ["base", "interaction"],
                }
                cases.append(case)
                split_cases.append(case)
            splits[split] = split_cases
        config: dict[str, object] = {
            "schema_version": 1,
            "cohort_id": "v7-a1-test-cohort",
            "stage": "pilot_ready",
            "baseline_commit": commit,
            "candidate": {
                "id": "v7-a1",
                "hypothesis": "A bounded Traditional Chinese wrapping contract reduces accidental orphan lines and wasted title tracks without flattening intentional editorial composition.",
                "editable_paths": ["wow-frontend-design/references/typographic-layout.md"],
                "reference_sha256": None,
                "forbidden_families": [
                    "intrinsic-layout",
                    "native-controls",
                    "color",
                    "motion",
                    "framework-adapter",
                    "registry-security",
                ],
            },
            "model": {"provider": "codex", "requested": "gpt-5.4-mini", "silent_fallback": False},
            "timeouts": {
                "generation": {"inactivity_seconds": 60, "hard_seconds": 600, "source": "provisional-before-pilot"},
                "lint": {"inactivity_seconds": 30, "hard_seconds": 120, "source": "provisional-before-pilot"},
                "capture": {"inactivity_seconds": 30, "hard_seconds": 180, "source": "provisional-before-pilot"},
            },
            "splits": splits,
            "screenshots": {
                "required_profiles": ["desktop", "mobile"],
                "affected_profiles": [
                    "desktop",
                    "standard-desktop",
                    "short-desktop",
                    "tablet",
                    "mobile",
                    "compact-mobile",
                ],
                "engine_parity": ["chromium", "firefox", "webkit"],
                "required_states": ["base", "interaction"],
                "before_after_on_finding": True,
                "blind_review": True,
            },
            "hidden_material_policy": {
                "storage": "evaluator-owned-outside-repository",
                "forbidden_keys": sorted(preflight.FORBIDDEN_HIDDEN_KEYS),
            },
            "evaluator_paths": ["evals/runner.py", "evals/auditor.py", "evals/evidence.py"],
        }
        path = root / "evals" / "v7-public-config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        return root, path, config, commit

    def test_freeze_and_validate_complete_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, config_path, _, _ = self._repository(directory)
            manifest = preflight.build_manifest(config_path, root, "2026-07-16T00:00:00Z")
            manifest_path = root / "evals" / "manifest.json"
            preflight._write_manifest(manifest_path, manifest)
            self.assertEqual(preflight.validate_manifest(manifest_path, root), (2, 3))
            self.assertEqual(manifest["baseline"]["file_count"], 2)

    def test_hidden_prompt_and_selector_are_rejected(self) -> None:
        for key in ("prompt", "selector", "expected_dom", "weights"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                root, config_path, config, _ = self._repository(directory)
                config["splits"]["sealed_validation"][0][key] = "secret"
                config_path.write_text(json.dumps(config), encoding="utf-8")
                with self.assertRaisesRegex(preflight.PreflightError, "hidden evaluation material"):
                    preflight.build_manifest(config_path, root, "2026-07-16T00:00:00Z")

    def test_second_candidate_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, config_path, config, _ = self._repository(directory)
            config["candidate"]["editable_paths"].append("wow-frontend-design/SKILL.md")
            config_path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(preflight.PreflightError, "editable path"):
                preflight.build_manifest(config_path, root, "2026-07-16T00:00:00Z")

    def test_candidate_id_allows_positive_iteration_number(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, config_path, config, _ = self._repository(directory)
            config["candidate"]["id"] = "v7-a2"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            manifest = preflight.build_manifest(config_path, root, "2026-07-16T00:00:00Z")
            self.assertEqual("v7-a2", manifest["candidate"]["id"])
            config["candidate"]["id"] = "v7-a0"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(preflight.PreflightError, "positive integer"):
                preflight.build_manifest(config_path, root, "2026-07-16T00:00:00Z")

    def test_pilot_can_use_observed_timeout_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, config_path, config, _ = self._repository(directory)
            for timeout in config["timeouts"].values():
                timeout["source"] = "observed-after-pilot"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            manifest = preflight.build_manifest(config_path, root, "2026-07-16T00:00:00Z")
            self.assertEqual("observed-after-pilot", manifest["timeouts"]["generation"]["source"])

    def test_evaluator_drift_invalidates_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, config_path, _, _ = self._repository(directory)
            manifest = preflight.build_manifest(config_path, root, "2026-07-16T00:00:00Z")
            manifest_path = root / "evals" / "manifest.json"
            preflight._write_manifest(manifest_path, manifest)
            (root / "evals" / "auditor.py").write_text("# drift\n", encoding="utf-8")
            with self.assertRaisesRegex(preflight.PreflightError, "evaluator bytes drifted"):
                preflight.validate_manifest(manifest_path, root)

    def test_tampered_package_snapshot_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, config_path, _, _ = self._repository(directory)
            manifest = preflight.build_manifest(config_path, root, "2026-07-16T00:00:00Z")
            manifest["baseline"]["files"][0]["sha256"] = "0" * 64
            manifest_path = root / "evals" / "manifest.json"
            preflight._write_manifest(manifest_path, manifest)
            with self.assertRaisesRegex(preflight.PreflightError, "package snapshot"):
                preflight.validate_manifest(manifest_path, root)

    def test_frozen_stage_requires_pilot_timeouts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, config_path, config, _ = self._repository(directory)
            config["stage"] = "frozen"
            candidate = root / "wow-frontend-design" / "references" / "typographic-layout.md"
            config["candidate"]["reference_sha256"] = preflight._sha256_bytes(candidate.read_bytes())
            config_path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(preflight.PreflightError, "provisional timeout"):
                preflight.build_manifest(config_path, root, "2026-07-16T00:00:00Z")

    def test_config_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, config_path, _, _ = self._repository(directory)
            link = root / "evals" / "linked-config.json"
            link.symlink_to(config_path)
            with self.assertRaisesRegex(preflight.PreflightError, "non-symlink"):
                preflight.build_manifest(link, root, "2026-07-16T00:00:00Z")

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, config_path, _, _ = self._repository(directory)
            text = config_path.read_text(encoding="utf-8")
            config_path.write_text(text[:-1] + ', "schema_version": 1}', encoding="utf-8")
            with self.assertRaisesRegex(preflight.PreflightError, "duplicate JSON key"):
                preflight.build_manifest(config_path, root, "2026-07-16T00:00:00Z")

    def test_config_outside_repository_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root, config_path, _, _ = self._repository(directory)
            external = Path(outside) / "config.json"
            external.write_bytes(config_path.read_bytes())
            with self.assertRaisesRegex(preflight.PreflightError, "inside the repository"):
                preflight.build_manifest(external, root, "2026-07-16T00:00:00Z")

    def test_split_count_and_duplicate_case_are_rejected(self) -> None:
        mutations = (
            lambda config: config["splits"]["sealed_test"].pop(),
            lambda config: config["splits"]["sealed_test"][0].update(
                id=config["splits"]["development"][0]["id"]
            ),
        )
        for mutation in mutations:
            with tempfile.TemporaryDirectory() as directory:
                root, config_path, original, _ = self._repository(directory)
                config = copy.deepcopy(original)
                mutation(config)
                config_path.write_text(json.dumps(config), encoding="utf-8")
                with self.assertRaises(preflight.PreflightError):
                    preflight.build_manifest(config_path, root, "2026-07-16T00:00:00Z")

    def test_frozen_candidate_byte_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, config_path, config, _ = self._repository(directory)
            candidate = root / "wow-frontend-design" / "references" / "typographic-layout.md"
            config["stage"] = "frozen"
            config["candidate"]["reference_sha256"] = preflight._sha256_bytes(candidate.read_bytes())
            for timeout in config["timeouts"].values():
                timeout["source"] = "frozen-after-pilot"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            manifest = preflight.build_manifest(config_path, root, "2026-07-16T00:00:00Z")
            manifest_path = root / "evals" / "manifest.json"
            preflight._write_manifest(manifest_path, manifest)
            candidate.write_text("# drift\n", encoding="utf-8")
            with self.assertRaisesRegex(preflight.PreflightError, "candidate reference bytes drifted"):
                preflight.validate_manifest(manifest_path, root)


if __name__ == "__main__":
    unittest.main()
