#!/usr/bin/env python3
"""Tests for the evaluator-owned fast multi-direction draft cohort."""

from __future__ import annotations

import hashlib
import json
import signal
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))

import run_current_draft_cohort as cohort  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CurrentDraftCohortTests(unittest.TestCase):
    def valid_plan(self) -> dict:
        return {
            "schema_version": 1,
            "cohort_id": "marketplace-directions-1",
            "partition": "validation",
            "locale": "zh-Hant",
            "surface": "marketplace-home",
            "decision_question": "哪一種資訊層級最能建立可信任且易探索的市集入口？",
            "held_constant_axes": [
                "product-facts",
                "content-fixture",
                "functional-behavior",
                "comparison-conditions",
            ],
            "selection_criteria": ["主要任務清晰", "品牌辨識度", "手機轉化成立"],
            "variants": [
                {
                    "id": "editorial-index",
                    "hypothesis": "以編輯策展與清楚索引建立可信任的探索節奏。",
                    "changed_axes": ["composition", "typography", "density"],
                    "expected_benefit": "讓大量內容仍保有可信來源與閱讀層級。",
                    "risk": "策展層級可能壓低立即行動的能見度。",
                    "disqualifier": "主要分類或第一個行動在手機首屏不可見。",
                },
                {
                    "id": "task-led-market",
                    "hypothesis": "先以使用者任務與快速比較縮短選擇路徑。",
                    "changed_axes": ["information-hierarchy", "interaction-emphasis", "mobile-transformation"],
                    "expected_benefit": "更快抵達可比較且可採取行動的結果。",
                    "risk": "任務導向可能降低品牌敘事的記憶點。",
                    "disqualifier": "方向退化成一般 SaaS dashboard 或卡片牆。",
                },
            ],
        }

    def write_inputs(self, root: Path) -> tuple[Path, Path, Path, Path]:
        plan = root / "plan.json"
        plan.write_text(json.dumps(self.valid_plan(), ensure_ascii=False), encoding="utf-8")
        brief = root / "brief.md"
        brief.write_text("建立可信任且有辨識度的繁體中文公益市集首頁。\n", encoding="utf-8")
        cohort_root = root / "cohort"
        cohort_root.mkdir()
        logs = root / "logs"
        logs.mkdir()
        return plan, brief, cohort_root, logs

    def fake_build(self, brief: Path, workspace: Path, **kwargs: object) -> dict:
        outputs = list(kwargs["outputs"])
        (workspace / "DESIGN.md").write_text("# Draft directions\n", encoding="utf-8")
        for output in outputs:
            if output.endswith(".html"):
                artifact = workspace / output
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_text(
                    f'<!doctype html><html lang="zh-Hant"><body><main><h1>{output}</h1></main></body></html>',
                    encoding="utf-8",
                )
        records = []
        for output in outputs:
            artifact = workspace / output
            records.append({
                "path": output,
                "bytes": artifact.stat().st_size,
                "mode": f"{stat.S_IMODE(artifact.stat().st_mode):04o}",
                "sha256": digest(artifact),
            })
        manifest = {
            "schema_version": 2,
            "status": "completed",
            "brief": {"bytes": brief.stat().st_size, "sha256": digest(brief)},
            "skill_snapshot": {"tree_sha256": "a" * 64},
            "skill_references": {
                "files": [{"path": "references/design-exploration.md", "bytes": 1, "sha256": "b" * 64}],
                "total_bytes": 1,
            },
            "outputs": records,
        }
        (workspace / "run-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return manifest

    def fake_capture(
        self,
        workspace: Path,
        case_path: Path,
        evidence: Path,
        convergence_path: Path | None = None,
    ) -> None:
        evidence.mkdir()
        (evidence / "artifacts").mkdir()
        case = json.loads(case_path.read_text(encoding="utf-8"))
        manifest_path = workspace / "run-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        receipt = {
            "schema_version": 1,
            "status": "captured",
            "case": {
                "case_id": case["case_id"],
                "run_id": case["run_id"],
                "partition": case["partition"],
                "case_sha256": digest(case_path),
            },
            "source": {
                "run_manifest_sha256": digest(manifest_path),
                "brief": manifest["brief"],
                "skill_tree_sha256": manifest["skill_snapshot"]["tree_sha256"],
                "outputs": manifest["outputs"],
            },
            "runtime": {
                "package": "playwright",
                "version": "1.61.1",
                "browser": "chromium",
                "browser_version": "test",
                "headless": True,
            },
            "capture_standard": cohort.CAPTURE_STANDARD,
            "captures": [],
        }
        (evidence / "capture-receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
        if convergence_path is not None:
            convergence = json.loads(convergence_path.read_text(encoding="utf-8"))
            observations = {
                "schemaVersion": 1,
                "cohort": convergence["cohort_id"],
                "observations": [
                    {
                        "caseId": variant["id"],
                        "route": f"/{variant['page']}",
                        "surface": convergence["surface"],
                        "viewport": profile,
                        "state": "default",
                        "macroFingerprint": {
                            "version": 2,
                            "landmarks": [],
                            "mainFlow": {
                                "display": "block",
                                "flexDirection": "row",
                                "gridTracks": [],
                                "gap": 0,
                            },
                            "regions": [],
                            "representationHistogram": [],
                            "visualGrammar": {
                                "displayFamily": "sans",
                                "displayScale": "display",
                                "majorRadius": "large",
                                "pillDensity": "many",
                            },
                        },
                    }
                    for variant in convergence["variants"]
                    for profile in ("desktop-default", "mobile-default")
                ],
            }
            observations_raw = (
                json.dumps(observations, ensure_ascii=False, indent=2) + "\n"
            ).encode("utf-8")
            observations_path = evidence / "macro-observations.json"
            observations_path.write_bytes(observations_raw)
            observations_path.chmod(0o600)
            audit = {
                "schema_version": 1,
                "observations": {
                    "bytes": len(observations_raw),
                    "sha256": hashlib.sha256(observations_raw).hexdigest(),
                },
                "result": cohort._recompute_template_audit(observations_raw),
            }
            audit_path = evidence / "cross-output-template-audit.json"
            audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            audit_path.chmod(0o600)

    def test_plan_is_schema_closed_and_build_contract_has_two_distinct_directions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan_path, _, _, _ = self.write_inputs(root)
            plan, record = cohort.load_plan(plan_path.resolve())
            self.assertEqual(2, len(plan["variants"]))
            self.assertEqual(digest(plan_path), record["sha256"])
            outputs = cohort.direction_outputs(plan)
            self.assertEqual(
                ("DESIGN.md", "directions/editorial-index.html", "directions/task-led-market.html"),
                outputs,
            )
            effective = cohort.effective_brief("共同產品需求", plan)
            self.assertIn("共同產品需求", effective)
            self.assertIn("editorial-index", effective)
            self.assertIn("task-led-market", effective)
            self.assertIn('"locale":"zh-Hant"', effective)
            self.assertIn('"surface":"marketplace-home"', effective)
            self.assertIn("Do not build production integrations", effective)

            invalid = self.valid_plan()
            invalid["private"] = True
            plan_path.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaisesRegex(cohort.DraftCohortError, "plan schema"):
                cohort.load_plan(plan_path.resolve())

    def test_package_exposes_one_documented_draft_wrapper(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(
            "python3 evals/run_current_draft_cohort.py",
            package["scripts"]["drafts:current"],
        )
        documentation = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")
        self.assertIn("`drafts:current` 是 `build:current` 的 style-calibration wrapper", documentation)
        self.assertIn("npm run drafts:current --", documentation)
        self.assertIn("草稿 PNG 只能支持這次方向選擇", documentation)

    def test_plan_rejects_invalid_counts_duplicate_ids_and_weak_axis_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan_path, _, _, _ = self.write_inputs(root)
            mutations = []
            one = self.valid_plan()
            one["variants"] = one["variants"][:1]
            mutations.append(one)
            four = self.valid_plan()
            four["variants"] = four["variants"] * 2
            mutations.append(four)
            duplicate = self.valid_plan()
            duplicate["variants"][1]["id"] = duplicate["variants"][0]["id"]
            mutations.append(duplicate)
            path_like = self.valid_plan()
            path_like["variants"][0]["id"] = "../escape"
            mutations.append(path_like)
            weak = self.valid_plan()
            weak["variants"][0]["changed_axes"] = ["color"]
            mutations.append(weak)
            overlap = self.valid_plan()
            overlap["variants"][0]["changed_axes"] = ["composition", "product-facts"]
            mutations.append(overlap)
            for payload in mutations:
                with self.subTest(payload=payload["variants"]):
                    plan_path.write_text(json.dumps(payload), encoding="utf-8")
                    with self.assertRaises(cohort.DraftCohortError):
                        cohort.load_plan(plan_path.resolve())

            for field, value in (("schema_version", True), ("partition", []), ("locale", [])):
                with self.subTest(field=field):
                    invalid_type = self.valid_plan()
                    invalid_type[field] = value
                    plan_path.write_text(json.dumps(invalid_type), encoding="utf-8")
                    with self.assertRaises(cohort.DraftCohortError):
                        cohort.load_plan(plan_path.resolve())

    def test_one_build_produces_fresh_cohort_receipt_without_release_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            plan, brief, cohort_root, logs = self.write_inputs(root)
            validated = {
                "capture_count": 4,
                "capture_set_sha256": "c" * 64,
                "capture_standard": cohort.CAPTURE_STANDARD,
            }
            with (
                mock.patch.object(cohort.current_build, "run", side_effect=self.fake_build) as build,
                mock.patch.object(cohort, "run_capture", side_effect=self.fake_capture) as capture,
                mock.patch.object(cohort, "validate_current_capture_evidence", return_value=validated) as validate,
            ):
                receipt = cohort.run(plan, brief, cohort_root, logs, max_repair_rounds=1)
            self.assertEqual(1, build.call_count)
            self.assertEqual(1, capture.call_count)
            self.assertEqual(2, validate.call_count)
            self.assertEqual("captured", receipt["status"])
            self.assertEqual("draft_cohort_captured", receipt["classification"])
            self.assertEqual("style_calibration_only", receipt["claim_boundary"])
            self.assertEqual(2, receipt["cohort"]["variant_count"])
            self.assertEqual("advisory_only", receipt["evidence"]["convergence"]["policy"])
            self.assertTrue(receipt["evidence"]["convergence"]["review_required"])
            self.assertEqual(
                "references/design-exploration.md",
                build.call_args.kwargs["skill_reference"],
            )
            self.assertNotIn("release", json.dumps(receipt).lower())
            receipt_path = cohort_root / "draft-cohort-receipt.json"
            self.assertTrue(receipt_path.is_file())
            self.assertEqual(0o600, stat.S_IMODE(receipt_path.stat().st_mode))

    def test_failed_build_never_creates_success_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            plan, brief, cohort_root, logs = self.write_inputs(root)
            with mock.patch.object(
                cohort.current_build,
                "run",
                side_effect=cohort.current_build.RunnerError("design_gate_rejection"),
            ):
                with self.assertRaisesRegex(cohort.DraftCohortError, "build failed"):
                    cohort.run(plan, brief, cohort_root, logs)
            self.assertFalse((cohort_root / "draft-cohort-receipt.json").exists())

    def test_rendered_convergence_advisory_requires_review_but_does_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            plan, brief, cohort_root, logs = self.write_inputs(root)
            validated = {
                "capture_count": 4,
                "capture_set_sha256": "c" * 64,
                "capture_standard": cohort.CAPTURE_STANDARD,
            }

            def advisory_capture(*args: object, **kwargs: object) -> None:
                self.fake_capture(*args, **kwargs)

            with (
                mock.patch.object(cohort.current_build, "run", side_effect=self.fake_build),
                mock.patch.object(cohort, "run_capture", side_effect=advisory_capture),
                mock.patch.object(cohort, "validate_current_capture_evidence", return_value=validated),
            ):
                receipt = cohort.run(plan, brief, cohort_root, logs)
            convergence = receipt["evidence"]["convergence"]
            self.assertEqual("captured", receipt["status"])
            self.assertTrue(convergence["review_required"])
            self.assertGreaterEqual(convergence["advisory_count"], 2)
            self.assertEqual(
                2,
                convergence["advisory_counts"]["cross_output_visual_grammar_candidate"],
            )
            self.assertEqual(
                ["editorial-index", "task-led-market"],
                convergence["affected_variant_ids"],
            )

    def test_unknown_convergence_category_cannot_be_reported_as_clean(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            plan, brief, cohort_root, logs = self.write_inputs(root)
            validated = {
                "capture_count": 4,
                "capture_set_sha256": "c" * 64,
                "capture_standard": cohort.CAPTURE_STANDARD,
            }

            def invalid_capture(*args: object, **kwargs: object) -> None:
                self.fake_capture(*args, **kwargs)
                audit_path = Path(args[2]) / "cross-output-template-audit.json"
                audit = json.loads(audit_path.read_text(encoding="utf-8"))
                audit["result"]["status"] = "advisories_present"
                audit["result"]["advisories"] = [{
                    "code": "unknown_convergence_score",
                    "caseIds": ["editorial-index", "task-led-market"],
                }]
                audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
                audit_path.chmod(0o600)

            with (
                mock.patch.object(cohort.current_build, "run", side_effect=self.fake_build),
                mock.patch.object(cohort, "run_capture", side_effect=invalid_capture),
                mock.patch.object(cohort, "validate_current_capture_evidence", return_value=validated),
            ):
                with self.assertRaisesRegex(cohort.DraftCohortError, "does not match the recomputed"):
                    cohort.run(plan, brief, cohort_root, logs)
            self.assertFalse((cohort_root / "draft-cohort-receipt.json").exists())

    def test_forged_convergence_claim_is_recomputed_and_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            plan, brief, cohort_root, logs = self.write_inputs(root)
            validated = {
                "capture_count": 4,
                "capture_set_sha256": "c" * 64,
                "capture_standard": cohort.CAPTURE_STANDARD,
            }

            def forged_capture(*args: object, **kwargs: object) -> None:
                self.fake_capture(*args, **kwargs)
                audit_path = Path(args[2]) / "cross-output-template-audit.json"
                audit = json.loads(audit_path.read_text(encoding="utf-8"))
                audit["result"]["claimBoundary"] = "award-winning and release approved"
                audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
                audit_path.chmod(0o600)

            with (
                mock.patch.object(cohort.current_build, "run", side_effect=self.fake_build),
                mock.patch.object(cohort, "run_capture", side_effect=forged_capture),
                mock.patch.object(cohort, "validate_current_capture_evidence", return_value=validated),
            ):
                with self.assertRaisesRegex(cohort.DraftCohortError, "does not match the recomputed"):
                    cohort.run(plan, brief, cohort_root, logs)
            self.assertFalse((cohort_root / "draft-cohort-receipt.json").exists())

    def test_post_validation_receipt_disappearance_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            plan, brief, cohort_root, logs = self.write_inputs(root)
            validated = {
                "capture_count": 4,
                "capture_set_sha256": "c" * 64,
                "capture_standard": cohort.CAPTURE_STANDARD,
            }

            def validate_then_remove(
                workspace: Path,
                case_path: Path,
                receipt_path: Path,
                manifest_path: Path,
            ) -> dict:
                receipt_path.unlink()
                return validated

            with (
                mock.patch.object(cohort.current_build, "run", side_effect=self.fake_build),
                mock.patch.object(cohort, "run_capture", side_effect=self.fake_capture),
                mock.patch.object(
                    cohort,
                    "validate_current_capture_evidence",
                    side_effect=validate_then_remove,
                ),
            ):
                with self.assertRaises(cohort.DraftCohortError) as observed:
                    cohort.run(plan, brief, cohort_root, logs)
            self.assertIn("final provenance validation failed", str(observed.exception))
            self.assertNotIn(str(root), str(observed.exception))
            self.assertFalse((cohort_root / "draft-cohort-receipt.json").exists())

    def test_plan_symlink_existing_output_and_excess_repair_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            plan, brief, cohort_root, logs = self.write_inputs(root)
            linked = root / "linked-plan.json"
            linked.symlink_to(plan)
            with self.assertRaisesRegex(cohort.DraftCohortError, "unaliased regular file"):
                cohort.load_plan(linked)

            (cohort_root / "old.png").write_bytes(b"old")
            with self.assertRaisesRegex(cohort.DraftCohortError, "cohort root must be empty"):
                cohort.run(plan, brief, cohort_root, logs)

            (cohort_root / "old.png").unlink()
            with self.assertRaisesRegex(cohort.DraftCohortError, "repair rounds"):
                cohort.run(plan, brief, cohort_root, logs, max_repair_rounds=2)

    def test_capture_timeout_is_bounded_and_does_not_expose_private_paths(self) -> None:
        private = Path("/private/tmp/private-cohort-secret")
        process = mock.Mock(pid=1234, returncode=None)
        process.communicate.side_effect = [
            subprocess.TimeoutExpired(["node", str(private)], 180),
            ("", ""),
        ]
        with (
            mock.patch.object(cohort.subprocess, "Popen", return_value=process),
            mock.patch.object(cohort.os, "killpg") as kill_group,
        ):
            with self.assertRaises(cohort.DraftCohortError) as observed:
                cohort.run_capture(private, private / "case.json", private / "evidence")
        kill_group.assert_called_once_with(1234, signal.SIGKILL)
        self.assertNotIn(str(private), str(observed.exception))

    def test_directory_identity_drift_never_creates_success_receipt(self) -> None:
        for target in ("cohort", "logs"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                plan, brief, cohort_root, logs = self.write_inputs(root)
                victim = cohort_root if target == "cohort" else logs
                original = root / f"{target}-original"
                redirect = root / f"{target}-redirect"

                def swapping_build(
                    brief_path: Path, workspace: Path, **kwargs: object
                ) -> dict:
                    victim.rename(original)
                    redirect.mkdir()
                    victim.symlink_to(redirect, target_is_directory=True)
                    return self.fake_build(brief_path, workspace, **kwargs)

                with mock.patch.object(
                    cohort.current_build, "run", side_effect=swapping_build
                ):
                    with self.assertRaisesRegex(cohort.DraftCohortError, "identity drifted"):
                        cohort.run(plan, brief, cohort_root, logs)
                self.assertFalse((redirect / "draft-cohort-receipt.json").exists())


if __name__ == "__main__":
    unittest.main()
