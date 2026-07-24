#!/usr/bin/env python3
"""Tests for manifest-derived current craft case preparation."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
PREPARER = ROOT / "evals" / "prepare_current_craft_case.py"
sys.path.insert(0, str(PREPARER.parent))

import prepare_current_craft_case as preparer  # noqa: E402


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PrepareCurrentCraftCaseTests(unittest.TestCase):
    def fixture(
        self,
        root: Path,
        *,
        status: str = "completed",
        include_html: bool = True,
    ) -> tuple[Path, Path, bytes]:
        workspace = root / "workspace"
        workspace.mkdir()
        outputs = []
        names = ["DESIGN.md"]
        if include_html:
            names.append("index.html")
        for name in names:
            path = workspace / name
            path.write_text(
                "<!doctype html><title>Current</title>" if name.endswith(".html") else "# Design\n",
                encoding="utf-8",
            )
            raw = path.read_bytes()
            outputs.append(
                {
                    "path": name,
                    "bytes": len(raw),
                    "mode": f"{stat.S_IMODE(path.stat().st_mode):04o}",
                    "sha256": digest(raw),
                }
            )
        brief = "建立繁體中文產品介面。\n".encode()
        manifest = {
            "schema_version": 2,
            "status": status,
            "brief": {"bytes": len(brief), "sha256": digest(brief)},
            "outputs": outputs,
        }
        raw_manifest = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
        manifest_path = workspace / "run-manifest.json"
        manifest_path.write_bytes(raw_manifest)
        return workspace, manifest_path, raw_manifest

    def invoke(
        self,
        workspace: Path | str,
        output: Path,
        *extra: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(PREPARER),
                "--workspace-root",
                str(workspace),
                "--output",
                str(output),
                *extra,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )

    def test_prepares_default_case_from_completed_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            workspace, _, raw_manifest = self.fixture(root)
            output = root / "current-craft-case.json"

            completed = self.invoke(workspace, output)

            self.assertEqual(0, completed.returncode, completed.stderr)
            case = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("current-production", case["case_id"])
            self.assertEqual(f"current-{digest(raw_manifest)}", case["run_id"])
            self.assertEqual("validation", case["partition"])
            self.assertEqual("all_html_outputs", case["capture_plan"]["pages"])
            self.assertEqual("zh-Hant", case["capture_plan"]["locale"])
            self.assertEqual(
                ["desktop-default", "mobile-default"],
                [profile["name"] for profile in case["capture_plan"]["profiles"]],
            )
            self.assertEqual(
                ["concept-coherence", "originality", "visual-typography"],
                case["craft"]["required_dimensions"],
            )
            self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))

    def test_accepts_explicit_safe_case_partition_and_locale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            workspace, manifest_path, _ = self.fixture(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            output = root / "test-case.json"

            completed = self.invoke(
                workspace,
                output,
                "--case-id",
                "held-out-01",
                "--partition",
                "test",
                "--locale",
                "en",
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            case = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("held-out-01", case["case_id"])
            self.assertEqual("test", case["partition"])
            self.assertEqual("en", case["capture_plan"]["locale"])
            self.assertEqual(manifest["brief"], case["brief"])

    def test_prepares_opt_in_consequential_state_case(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            workspace, manifest_path, _ = self.fixture(root)
            contract = root / "browser-contract.json"
            payload = {
                "schema_version": 2,
                "cases": [{
                    "id": "open-details",
                    "page": "index.html",
                    "profile": "desktop",
                    "steps": [
                        {
                            "id": "open",
                            "action": "click",
                            "selector": "#open",
                        },
                        {
                            "id": "visible",
                            "action": "assert",
                            "selector": "#details",
                            "expect": "visible",
                        },
                    ],
                }],
            }
            contract.write_text(json.dumps(payload), encoding="utf-8")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["browser_contract"] = {
                "schema_version": 2,
                "bytes": contract.stat().st_size,
                "sha256": digest(contract.read_bytes()),
                "case_count": 1,
                "step_count": 2,
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            output = root / "case.json"

            completed = self.invoke(
                workspace,
                output,
                "--browser-contract",
                str(contract),
                "--contract-case-id",
                "open-details",
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            case = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(2, case["schema_version"])
            self.assertEqual(
                {"contract_case_id": "open-details"},
                case["capture_plan"]["consequential_state"],
            )
            self.assertEqual(
                manifest["browser_contract"],
                case["browser_contract"],
            )

    def test_consequential_state_case_requires_paired_matching_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            workspace, _, _ = self.fixture(root)
            output = root / "case.json"

            completed = self.invoke(
                workspace,
                output,
                "--contract-case-id",
                "open-details",
            )

            self.assertNotEqual(0, completed.returncode)
            self.assertIn("provided together", completed.stderr)
            self.assertFalse(output.exists())

    def test_rejects_relative_workspace_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            workspace, _, _ = self.fixture(root)
            output = root / "case.json"

            completed = self.invoke(workspace.name, output)

            self.assertNotEqual(0, completed.returncode)
            self.assertIn("absolute", completed.stderr)
            self.assertFalse(output.exists())

    def test_rejects_incomplete_manifest_and_manifest_without_html(self) -> None:
        for status, include_html, expected in (
            ("failed", True, "completed"),
            ("completed", False, "HTML"),
        ):
            with self.subTest(status=status, include_html=include_html):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory).resolve()
                    workspace, _, _ = self.fixture(
                        root,
                        status=status,
                        include_html=include_html,
                    )
                    output = root / "case.json"

                    completed = self.invoke(workspace, output)

                    self.assertNotEqual(0, completed.returncode)
                    self.assertIn(expected, completed.stderr)
                    self.assertFalse(output.exists())

    def test_rejects_symlinked_and_hardlinked_manifest(self) -> None:
        for alias_kind in ("symlink", "hardlink"):
            with self.subTest(alias_kind=alias_kind):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory).resolve()
                    workspace, manifest_path, _ = self.fixture(root)
                    source = root / "manifest-source.json"
                    manifest_path.replace(source)
                    if alias_kind == "symlink":
                        manifest_path.symlink_to(source)
                    else:
                        os.link(source, manifest_path)
                    output = root / "case.json"

                    completed = self.invoke(workspace, output)

                    self.assertNotEqual(0, completed.returncode)
                    self.assertIn("unaliased", completed.stderr)
                    self.assertFalse(output.exists())

    def test_rejects_missing_tampered_or_aliased_manifest_output(self) -> None:
        for failure in ("missing", "tampered", "symlink", "hardlink"):
            with self.subTest(failure=failure):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory).resolve()
                    workspace, _, _ = self.fixture(root)
                    html = workspace / "index.html"
                    if failure == "missing":
                        html.unlink()
                    elif failure == "tampered":
                        html.write_text("tampered", encoding="utf-8")
                    else:
                        source = root / "index-source.html"
                        html.replace(source)
                        if failure == "symlink":
                            html.symlink_to(source)
                        else:
                            os.link(source, html)
                    output = root / "case.json"

                    completed = self.invoke(workspace, output)

                    self.assertNotEqual(0, completed.returncode)
                    self.assertIn("actual output", completed.stderr)
                    self.assertFalse(output.exists())

    def test_rejects_workspace_or_output_inside_authoring_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            authoring = root / "authoring"
            authoring.mkdir()
            external = root / "external"
            external.mkdir()
            external_workspace, _, _ = self.fixture(external)
            inside_workspace, _, _ = self.fixture(authoring)
            with mock.patch.object(preparer, "ROOT", authoring):
                with self.assertRaisesRegex(preparer.CraftCaseError, "authoring repository"):
                    preparer.prepare_case(inside_workspace, root / "outside.json")
                with self.assertRaisesRegex(preparer.CraftCaseError, "authoring repository"):
                    preparer.prepare_case(external_workspace, authoring / "case.json")

    def test_existing_output_and_symlink_are_never_overwritten(self) -> None:
        for existing_kind in ("file", "symlink"):
            with self.subTest(existing_kind=existing_kind):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory).resolve()
                    workspace, _, _ = self.fixture(root)
                    target = root / "sentinel.json"
                    target.write_text("sentinel", encoding="utf-8")
                    output = root / "case.json"
                    if existing_kind == "file":
                        output.write_text("existing", encoding="utf-8")
                    else:
                        output.symlink_to(target)

                    completed = self.invoke(workspace, output)

                    self.assertNotEqual(0, completed.returncode)
                    self.assertEqual("sentinel", target.read_text(encoding="utf-8"))
                    if existing_kind == "file":
                        self.assertEqual("existing", output.read_text(encoding="utf-8"))
                    else:
                        self.assertTrue(output.is_symlink())

    def test_failed_write_removes_only_the_partial_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            workspace, _, _ = self.fixture(root)
            output = root / "case.json"
            with mock.patch.object(preparer.os, "write", side_effect=OSError("disk full")):
                with self.assertRaisesRegex(preparer.CraftCaseError, "created"):
                    preparer.prepare_case(workspace, output)
            self.assertFalse(output.exists())

    def test_package_and_platform_snapshot_expose_the_preparer(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(
            "python3 evals/prepare_current_craft_case.py",
            package["scripts"]["case:current"],
        )
        platform = json.loads(
            (ROOT / "evals" / "platform-support.json").read_text(encoding="utf-8")
        )
        target = next(
            item
            for item in platform["targets"]
            if item["id"] == "evaluator-posix-runners"
        )
        self.assertIn("evals/prepare_current_craft_case.py", target["entrypoints"])
        self.assertIn("tests/test_prepare_current_craft_case.py", target["artifacts"])
        documentation = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")
        self.assertIn("npm run case:current --", documentation)


if __name__ == "__main__":
    unittest.main()
