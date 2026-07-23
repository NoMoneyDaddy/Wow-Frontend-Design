#!/usr/bin/env python3
"""Tests for final-only current visual evidence capture."""

from __future__ import annotations

import hashlib
import json
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "evals" / "capture_current_visual_evidence.cjs"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CurrentVisualEvidenceTests(unittest.TestCase):
    def fixture(self, root: Path, *, html: str | None = None) -> tuple[Path, Path, dict]:
        target = root / "workspace"
        target.mkdir()
        brief = "建立可用且有辨識度的繁體中文產品介面。\n".encode()
        (target / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
        (target / "index.html").write_text(
            html or '<!doctype html><html lang="zh-Hant"><head><title>Current</title></head><body><main><h1>現行輸出</h1><p>Fresh evidence only.</p></main></body></html>',
            encoding="utf-8",
        )
        outputs = []
        for name in ("DESIGN.md", "index.html"):
            path = target / name
            outputs.append({
                "path": name,
                "bytes": path.stat().st_size,
                "mode": f"{stat.S_IMODE(path.stat().st_mode):04o}",
                "sha256": digest(path),
            })
        manifest = {
            "schema_version": 2,
            "status": "completed",
            "brief": {"bytes": len(brief), "sha256": hashlib.sha256(brief).hexdigest()},
            "skill_snapshot": {"tree_sha256": "a" * 64},
            "outputs": outputs,
        }
        (target / "run-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        case = {
            "schema_version": 1,
            "case_id": "private-validation-case",
            "run_id": "run-001",
            "partition": "validation",
            "brief": manifest["brief"],
            "capture_plan": {
                "locale": "zh-Hant",
                "state": "default",
                "pages": "all_html_outputs",
                "wait_condition": "load+fonts+two-raf+300ms+two-raf",
                "profiles": [
                    {"name": "desktop-default", "viewport": {"width": 1440, "height": 1000}, "reducedMotion": "no-preference", "dpr": 1},
                    {"name": "mobile-default", "viewport": {"width": 390, "height": 844}, "reducedMotion": "reduce", "dpr": 1},
                ],
            },
            "craft": {
                "rubric_version": "wow-core-craft-v1",
                "required_dimensions": ["concept-coherence", "originality", "visual-typography"],
                "feedback_policy": "aggregate-failure-families-only",
            },
        }
        case_path = root / "case.json"
        case_path.write_text(json.dumps(case), encoding="utf-8")
        return target, case_path, case

    def invoke(
        self,
        target: Path,
        case: Path,
        evidence: Path,
        convergence: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = ["node", str(CAPTURE), str(target), str(case), str(evidence)]
        if convergence is not None:
            command.append(str(convergence))
        return subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=45,
            check=False,
        )

    def test_captures_exact_fresh_desktop_and_mobile_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, case_path, _ = self.fixture(root)
            evidence = root / "evidence"
            completed = self.invoke(target, case_path, evidence)
            self.assertEqual(0, completed.returncode, completed.stderr)
            receipt = json.loads((evidence / "capture-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual("captured", receipt["status"])
            self.assertEqual({"desktop-default", "mobile-default"}, {item["profile"] for item in receipt["captures"]})
            self.assertEqual({"1440x1000", "390x844"}, {item["context"]["viewport"] for item in receipt["captures"]})
            self.assertEqual(2, len(list((evidence / "artifacts").glob("*.png"))))
            self.assertFalse((evidence / ".source-snapshot").exists())
            self.assertFalse((evidence / "macro-observations.json").exists())
            self.assertFalse((evidence / "cross-output-template-audit.json").exists())
            self.assertEqual(digest(target / "run-manifest.json"), receipt["source"]["run_manifest_sha256"])
            for item in receipt["captures"]:
                artifact = evidence / item["path"]
                self.assertEqual(item["bytes"], artifact.stat().st_size)
                self.assertEqual(item["sha256"], digest(artifact))

    def test_existing_evidence_directory_is_never_reused_or_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, case_path, _ = self.fixture(root)
            evidence = root / "evidence"
            evidence.mkdir()
            marker = evidence / "old.png"
            marker.write_bytes(b"old")
            completed = self.invoke(target, case_path, evidence)
            self.assertEqual(1, completed.returncode)
            self.assertIn("must not already exist", completed.stderr)
            self.assertEqual(b"old", marker.read_bytes())

    def test_oversized_case_is_rejected_before_json_read_or_capture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, case_path, _ = self.fixture(root)
            case_path.write_bytes(b" " * 2_000_001)
            evidence = root / "evidence"
            completed = self.invoke(target, case_path, evidence)
            self.assertEqual(1, completed.returncode)
            self.assertIn("bounded regular non-symlink", completed.stderr)
            self.assertFalse(evidence.exists())

    def test_optional_draft_convergence_uses_the_same_capture_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            target, case_path, _ = self.fixture(root)
            second = target / "other.html"
            second.write_text((target / "index.html").read_text(encoding="utf-8"), encoding="utf-8")
            manifest_path = target / "run-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["outputs"].append({
                "path": "other.html",
                "bytes": second.stat().st_size,
                "mode": f"{stat.S_IMODE(second.stat().st_mode):04o}",
                "sha256": digest(second),
            })
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            convergence = root / "convergence.json"
            convergence.write_text(json.dumps({
                "schema_version": 1,
                "cohort_id": "private-validation-case",
                "surface": "primary",
                "variants": [
                    {"id": "index", "page": "index.html"},
                    {"id": "other", "page": "other.html"},
                ],
            }), encoding="utf-8")
            evidence = root / "evidence"
            completed = self.invoke(target, case_path, evidence, convergence)
            self.assertEqual(0, completed.returncode, completed.stderr)
            observations_path = evidence / "macro-observations.json"
            audit_path = evidence / "cross-output-template-audit.json"
            observations = json.loads(observations_path.read_text(encoding="utf-8"))
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(4, len(observations["observations"]))
            self.assertEqual(digest(observations_path), audit["observations"]["sha256"])
            self.assertEqual("advisories_present", audit["result"]["status"])
            self.assertTrue(audit["result"]["advisories"])
            self.assertEqual(0o600, stat.S_IMODE(observations_path.stat().st_mode))
            self.assertEqual(0o600, stat.S_IMODE(audit_path.stat().st_mode))
            self.assertNotIn(str(root), observations_path.read_text(encoding="utf-8"))
            self.assertNotIn(str(root), audit_path.read_text(encoding="utf-8"))

    def test_draft_convergence_contract_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            target, case_path, _ = self.fixture(root)
            convergence = root / "convergence.json"
            convergence.write_text("{}", encoding="utf-8")
            linked = root / "linked-convergence.json"
            linked.symlink_to(convergence)
            evidence = root / "evidence"
            completed = self.invoke(target, case_path, evidence, linked)
            self.assertEqual(1, completed.returncode)
            self.assertIn("unaliased", completed.stderr)
            self.assertFalse(evidence.exists())

    def test_case_from_a_different_brief_fails_before_capture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, case_path, case = self.fixture(root)
            case["brief"]["sha256"] = "b" * 64
            case_path.write_text(json.dumps(case), encoding="utf-8")
            evidence = root / "evidence"
            completed = self.invoke(target, case_path, evidence)
            self.assertEqual(1, completed.returncode)
            self.assertIn("case brief does not match", completed.stderr)
            self.assertFalse(evidence.exists())

    def test_failed_fresh_replay_removes_partial_capture_cohort(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, case_path, _ = self.fixture(
                root,
                html='<!doctype html><html lang="zh-Hant"><head><title>X</title></head><body><main><h1>X</h1><img src="https://example.invalid/x.png"></main></body></html>',
            )
            evidence = root / "evidence"
            completed = self.invoke(target, case_path, evidence)
            self.assertEqual(1, completed.returncode)
            self.assertIn("fresh browser replay did not remain clean", completed.stderr)
            self.assertFalse(evidence.exists())


if __name__ == "__main__":
    unittest.main()
