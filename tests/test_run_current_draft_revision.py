#!/usr/bin/env python3
"""Tests for the evaluator-owned single-child draft revision wrapper."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
import tempfile
import traceback
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))

import run_current_draft_revision as revision  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(path: Path) -> dict[str, object]:
    return {
        "path": path.name,
        "bytes": path.stat().st_size,
        "mode": f"{stat.S_IMODE(path.stat().st_mode):04o}",
        "sha256": digest(path),
    }


class CurrentDraftRevisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.cohort_root = self.root / "cohort"
        self.cohort_logs = self.root / "cohort-logs"
        self.revision_root = self.root / "revision"
        self.revision_logs = self.root / "revision-logs"
        for path in (
            self.cohort_root,
            self.cohort_logs,
            self.revision_root,
            self.revision_logs,
        ):
            path.mkdir()
        self.workspace = self.cohort_root / "workspace"
        (self.workspace / "directions").mkdir(parents=True)
        self.design = self.workspace / "DESIGN.md"
        self.base_page = self.workspace / "directions" / "editorial-index.html"
        self.design.write_text("# Original draft cohort\n", encoding="utf-8")
        self.base_page.write_text(
            '<!doctype html><html lang="zh-Hant"><body><main><h1>Original</h1></main></body></html>',
            encoding="utf-8",
        )
        self.brief = self.root / "brief.md"
        self.brief.write_text("建立可信任且有辨識度的公益市集首頁。\n", encoding="utf-8")
        self.decision = self.root / "revision-decision.json"
        self.decision.write_text('{"schema_version":1}\n', encoding="utf-8")
        self.decision.chmod(0o600)
        self.decision_receipt = self.root / "revision-decision-receipt.json"
        self.decision_receipt.write_text('{"schema_version":1}\n', encoding="utf-8")
        self.decision_receipt.chmod(0o600)
        self.skill_hash = revision.current_build.skill_tree_summary(
            revision.SKILL_ROOT, "wow-frontend-design"
        )["tree_sha256"]

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def cohort_source(self) -> dict[str, object]:
        outputs = [
            {
                "path": "DESIGN.md",
                "bytes": self.design.stat().st_size,
                "mode": f"{stat.S_IMODE(self.design.stat().st_mode):04o}",
                "sha256": digest(self.design),
            },
            {
                "path": "directions/editorial-index.html",
                "bytes": self.base_page.stat().st_size,
                "mode": f"{stat.S_IMODE(self.base_page.stat().st_mode):04o}",
                "sha256": digest(self.base_page),
            },
        ]
        cohort_receipt = {
            "cohort": {
                "cohort_id": "marketplace-directions-1",
                "partition": "validation",
                "locale": "zh-Hant",
                "surface": "marketplace-home",
            },
            "source": {
                "base_brief": {"bytes": self.brief.stat().st_size, "sha256": digest(self.brief)},
                "outputs": outputs,
                "skill_tree_sha256": self.skill_hash,
            },
            "evidence": {"capture_set_sha256": "b" * 64},
        }
        return {
            "receipt": cohort_receipt,
            "receipt_record": {
                "path": "draft-cohort-receipt.json",
                "bytes": 100,
                "mode": "0600",
                "sha256": "c" * 64,
            },
            "cohort": {
                "cohort_id": "marketplace-directions-1",
                "surface": "marketplace-home",
                "held_constant_axes": [
                    "product-facts",
                    "content-fixture",
                    "functional-behavior",
                    "comparison-conditions",
                ],
                "selection_criteria": ["主要任務清晰", "品牌辨識度"],
                "variants": [
                    {
                        "id": "editorial-index",
                        "hypothesis": "以策展索引建立可信任的探索節奏。",
                        "changed_axes": ["composition", "typography"],
                        "expected_benefit": "資訊層級更清楚。",
                        "risk": "行動能見度可能降低。",
                        "disqualifier": "手機首屏看不到主要行動。",
                    }
                ],
            },
            "capture": {"capture_set_sha256": "b" * 64},
        }

    def revise_source(self) -> dict[str, object]:
        source = self.cohort_source()
        return {
            "receipt": {
                "schema_version": 1,
                "status": "recorded",
                "classification": "draft_direction_revision_requested",
                "claim_boundary": "selection_lineage_only_no_release_acceptance",
                "source": {
                    "cohort_receipt": source["receipt_record"],
                    "decision_input": {
                        "bytes": self.decision.stat().st_size,
                        "mode": "0600",
                        "sha256": digest(self.decision),
                    },
                    "cohort_id": "marketplace-directions-1",
                    "capture_set_sha256": "b" * 64,
                    "skill_tree_sha256": self.skill_hash,
                },
                "decision": {
                    "action": "revise",
                    "authority": "user_confirmed",
                    "reason": "方向成立，但主行動仍太弱。",
                    "adjustments": ["提高主行動對比。"],
                    "convergence_reviewed": True,
                    "variant": self.cohort_source()["cohort"]["variants"][0],
                    "capture_labels": [
                        "01-editorial-index-desktop-default",
                        "02-editorial-index-mobile-default",
                    ],
                },
                "handoff": {
                    "next_step": "render_one_bounded_revision",
                    "production_lane": None,
                    "base_variant_id": "editorial-index",
                    "source_page": "directions/editorial-index.html",
                    "held_constant_axes": self.cohort_source()["cohort"]["held_constant_axes"],
                    "selection_criteria": self.cohort_source()["cohort"]["selection_criteria"],
                    "draft_evidence_policy": "style_calibration_only_not_release_evidence",
                    "required_revalidation": [
                        "one fresh desktop/mobile revision pair",
                        "return to this decision checkpoint",
                    ],
                },
            },
            "receipt_record": {
                "bytes": self.decision_receipt.stat().st_size,
                "mode": "0600",
                "sha256": digest(self.decision_receipt),
            },
            "skill_tree_sha256": self.skill_hash,
        }

    def fake_build(self, brief: Path, workspace: Path, **kwargs: object) -> dict[str, object]:
        seed = Path(kwargs["seed_root"])
        child_page = next(name for name in kwargs["outputs"] if str(name).endswith(".html"))
        (workspace / "directions").mkdir(parents=True, exist_ok=True)
        (workspace / "DESIGN.md").write_text("# Bounded child revision\n", encoding="utf-8")
        (workspace / child_page).write_text(
            '<!doctype html><html lang="zh-Hant"><body><main><h1>Revised</h1></main></body></html>',
            encoding="utf-8",
        )
        outputs = []
        for name in kwargs["outputs"]:
            path = workspace / str(name)
            outputs.append({
                "path": str(name),
                "bytes": path.stat().st_size,
                "mode": f"{stat.S_IMODE(path.stat().st_mode):04o}",
                "sha256": digest(path),
            })
        manifest = {
            "schema_version": 2,
            "status": "completed",
            "case": {"mode": "retrofit", "lane_contract": "RETROFIT"},
            "brief": {"bytes": brief.stat().st_size, "sha256": digest(brief)},
            "skill_snapshot": {"tree_sha256": self.skill_hash},
            "skill_references": {
                "files": [{"path": "references/design-exploration.md", "bytes": 1, "sha256": "d" * 64}],
                "total_bytes": 1,
            },
            "seed_snapshot": {"files": [], "directories": [], "tree_sha256": "e" * 64},
            "mutation": {
                "allowed_changes": list(kwargs["allow_changes"]),
                "observed_changes": list(kwargs["allow_changes"]),
                "preserved_directories": 1,
            },
            "outputs": outputs,
        }
        if kwargs.get("browser_contract") is not None:
            _, _, browser_contract_record = revision.current_build._load_browser_contract(
                Path(kwargs["browser_contract"]), tuple(str(item) for item in kwargs["outputs"])
            )
            manifest["browser_contract"] = browser_contract_record
        manifest["seed_snapshot"]["files"] = [
            {"path": path.relative_to(seed).as_posix(), **revision._record(path)}
            for path in sorted(seed.rglob("*"))
            if path.is_file()
        ]
        (workspace / "run-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        self.assertEqual(
            {"DESIGN.md", child_page},
            {path.relative_to(seed).as_posix() for path in seed.rglob("*") if path.is_file()},
        )
        self.assertFalse(any(path.suffix == ".png" for path in seed.rglob("*")))
        return manifest

    def fake_capture(
        self,
        workspace: Path,
        case_path: Path,
        evidence: Path,
        convergence_path: Path | None = None,
    ) -> None:
        self.assertIsNone(convergence_path)
        evidence.mkdir()
        (evidence / "artifacts").mkdir()
        case = json.loads(case_path.read_text(encoding="utf-8"))
        manifest = json.loads((workspace / "run-manifest.json").read_text(encoding="utf-8"))
        page = next(record["path"] for record in manifest["outputs"] if record["path"].endswith(".html"))
        captures = [
            {
                "label": f"0{index}-{page.removesuffix('.html').replace('/', '-')}-{profile}",
                "page": page,
                "profile": profile,
                "path": f"artifacts/{index}.png",
                "bytes": 100,
                "sha256": str(index) * 64,
                "width": width,
                "height": height,
                "captured_at": "2026-07-23T00:00:00.000Z",
                "context": {},
            }
            for index, profile, width, height in (
                (1, "desktop-default", 1440, 1000),
                (2, "mobile-default", 390, 844),
            )
        ]
        receipt = {
            "schema_version": 1,
            "status": "captured",
            "case": {"case_id": case["case_id"]},
            "source": {"outputs": manifest["outputs"]},
            "runtime": {"package": "playwright", "version": "1.61.1"},
            "capture_standard": revision.cohort.CAPTURE_STANDARD,
            "captures": captures,
        }
        (evidence / "capture-receipt.json").write_text(json.dumps(receipt), encoding="utf-8")

    def validated_capture(self, workspace: Path) -> dict[str, object]:
        receipt = json.loads((self.revision_root / "evidence" / "capture-receipt.json").read_text())
        labels = [item["label"] for item in receipt["captures"]]
        return {
            "receipt": receipt,
            "manifest": json.loads((workspace / "run-manifest.json").read_text()),
            "capture_count": 2,
            "capture_set_sha256": "f" * 64,
            "capture_standard": revision.cohort.CAPTURE_STANDARD,
            "capture_labels": labels,
        }

    def browser_contract(self) -> Path:
        child_page = f"directions/revision-{digest(self.decision_receipt)[:12]}.html"
        contract = self.root / "revision-browser-contract.json"
        contract.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "cases": [
                        {
                            "id": "mobile-first-room",
                            "page": child_page,
                            "profile": "mobile",
                            "steps": [
                                {
                                    "id": "first-room-price-in-first-viewport",
                                    "action": "assert",
                                    "selector": "#room-0 [data-current-price]",
                                    "expect": "fully-visible-in-viewport",
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return contract

    def run_success(self) -> dict[str, object]:
        with (
            mock.patch.object(revision.decision, "validate_cohort_source", return_value=self.cohort_source()),
            mock.patch.object(revision.decision, "validate_decision_receipt", return_value=self.revise_source()),
            mock.patch.object(revision.current_build, "run", side_effect=self.fake_build) as build,
            mock.patch.object(revision.cohort, "run_capture", side_effect=self.fake_capture) as capture,
            mock.patch.object(
                revision,
                "validate_current_capture_evidence",
                side_effect=lambda workspace, *_args: self.validated_capture(workspace),
            ),
        ):
            result = revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
            )
        self.assertEqual(1, build.call_count)
        self.assertEqual(1, capture.call_count)
        return result

    def test_one_retrofit_child_gets_exactly_one_fresh_pair_without_convergence(self) -> None:
        result = self.run_success()
        self.assertEqual("draft_revision_captured", result["classification"])
        self.assertEqual("style_calibration_only", result["claim_boundary"])
        self.assertEqual(2, result["evidence"]["capture_count"])
        self.assertEqual(
            ["desktop-default", "mobile-default"],
            [
                item["name"]
                for item in result["evidence"]["capture_standard"]["profiles"]
            ],
        )
        self.assertFalse((self.revision_root / "evidence" / "macro-observations.json").exists())
        self.assertFalse((self.revision_root / "evidence" / "cross-output-template-audit.json").exists())
        receipt = self.revision_root / "draft-revision-receipt.json"
        self.assertEqual(0o600, stat.S_IMODE(receipt.stat().st_mode))
        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("方向成立", serialized)
        self.assertNotIn(str(self.root), serialized)

    def test_capture_pair_must_be_the_child_desktop_and_mobile(self) -> None:
        validated = {
            "capture_count": 2,
            "capture_standard": revision.cohort.CAPTURE_STANDARD,
            "receipt": {
                "captures": [
                    {"page": "directions/child.html", "profile": "desktop-default"},
                    {"page": "directions/child.html", "profile": "desktop-default"},
                ]
            },
        }
        with self.assertRaisesRegex(revision.DraftRevisionError, "fresh child pair"):
            revision._require_fresh_child_pair(validated, "directions/child.html")

    def test_build_failure_classification_is_closed_and_redacted(self) -> None:
        for classification in revision.current_build.RECEIPT_CATEGORIES["failed"]:
            with self.subTest(classification=classification):
                error = revision.current_build.RunnerError(
                    f"{classification}; logs=/private/example/secret.log"
                )
                self.assertEqual(
                    classification,
                    revision._safe_build_failure_classification(error),
                )
        self.assertEqual(
            "execution_infrastructure_failure",
            revision._safe_build_failure_classification(
                revision.current_build.RunnerError(
                    "unexpected private detail /private/example/secret.log"
                )
            ),
        )

    def test_build_failure_reports_only_the_closed_classification(self) -> None:
        error = revision.current_build.RunnerError(
            "html_smoke_rejection; logs=/private/example/secret.log"
        )
        with (
            mock.patch.object(
                revision.decision,
                "validate_cohort_source",
                return_value=self.cohort_source(),
            ),
            mock.patch.object(
                revision.decision,
                "validate_decision_receipt",
                return_value=self.revise_source(),
            ),
            mock.patch.object(revision.current_build, "run", side_effect=error),
            mock.patch.object(revision.cohort, "run_capture") as capture,
            self.assertRaises(revision.DraftRevisionError) as raised,
        ):
            revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
            )
        self.assertEqual(
            "draft revision build failed: html_smoke_rejection",
            str(raised.exception),
        )
        self.assertNotIn(
            "secret.log",
            "".join(traceback.TracebackException.from_exception(raised.exception).format()),
        )
        self.assertTrue(raised.exception.__suppress_context__)
        capture.assert_not_called()

    def test_build_failure_tool_drift_overrides_reported_classification(self) -> None:
        stable = revision._tool_records()
        drifted = [dict(item) for item in stable]
        drifted[0]["sha256"] = "0" * 64
        error = revision.current_build.RunnerError(
            "html_smoke_rejection; logs=/private/example/secret.log"
        )
        with (
            mock.patch.object(
                revision.decision,
                "validate_cohort_source",
                return_value=self.cohort_source(),
            ),
            mock.patch.object(
                revision.decision,
                "validate_decision_receipt",
                return_value=self.revise_source(),
            ),
            mock.patch.object(
                revision, "_tool_records", side_effect=[stable, stable, stable, drifted]
            ),
            mock.patch.object(revision.current_build, "run", side_effect=error),
            self.assertRaises(revision.DraftRevisionError) as raised,
        ):
            revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
            )
        self.assertEqual(
            "draft revision build failed: execution_infrastructure_failure",
            str(raised.exception),
        )
        self.assertNotIn(
            "secret.log",
            "".join(traceback.TracebackException.from_exception(raised.exception).format()),
        )

    def test_capture_failure_auditor_drift_fails_as_infrastructure(self) -> None:
        stable = revision._tool_records()
        drifted = [dict(item) for item in stable]
        drifted[-1]["sha256"] = "0" * 64
        error = RuntimeError("capture failed at /private/example/secret.png")
        with (
            mock.patch.object(
                revision.decision,
                "validate_cohort_source",
                return_value=self.cohort_source(),
            ),
            mock.patch.object(
                revision.decision,
                "validate_decision_receipt",
                return_value=self.revise_source(),
            ),
            mock.patch.object(
                revision,
                "_tool_records",
                side_effect=[stable, stable, stable, stable, stable, drifted],
            ),
            mock.patch.object(revision.current_build, "run", side_effect=self.fake_build),
            mock.patch.object(revision.cohort, "run_capture", side_effect=error),
            self.assertRaises(revision.DraftRevisionError) as raised,
        ):
            revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
            )
        self.assertEqual(
            "draft revision capture failed: execution_infrastructure_failure",
            str(raised.exception),
        )
        self.assertNotIn(
            "secret.png",
            "".join(traceback.TracebackException.from_exception(raised.exception).format()),
        )
        self.assertTrue(raised.exception.__suppress_context__)

    def test_unknown_build_exception_fails_closed_without_private_traceback(self) -> None:
        error = RuntimeError(
            "html_smoke_rejection; spoofed private detail /private/example/secret.log"
        )
        with (
            mock.patch.object(
                revision.decision,
                "validate_cohort_source",
                return_value=self.cohort_source(),
            ),
            mock.patch.object(
                revision.decision,
                "validate_decision_receipt",
                return_value=self.revise_source(),
            ),
            mock.patch.object(revision.current_build, "run", side_effect=error),
            mock.patch.object(revision.cohort, "run_capture") as capture,
            self.assertRaises(revision.DraftRevisionError) as raised,
        ):
            revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
            )
        self.assertEqual(
            "draft revision build failed: execution_infrastructure_failure",
            str(raised.exception),
        )
        self.assertNotIn(
            "secret.log",
            "".join(traceback.TracebackException.from_exception(raised.exception).format()),
        )
        self.assertTrue(raised.exception.__suppress_context__)
        capture.assert_not_called()

    def test_browser_contract_is_validated_bound_and_passed_to_the_builder(self) -> None:
        child_page = f"directions/revision-{digest(self.decision_receipt)[:12]}.html"
        contract = self.browser_contract()
        with (
            mock.patch.object(revision.decision, "validate_cohort_source", return_value=self.cohort_source()),
            mock.patch.object(revision.decision, "validate_decision_receipt", return_value=self.revise_source()),
            mock.patch.object(revision.current_build, "run", side_effect=self.fake_build) as build,
            mock.patch.object(revision.cohort, "run_capture", side_effect=self.fake_capture),
            mock.patch.object(
                revision,
                "validate_current_capture_evidence",
                side_effect=lambda workspace, *_args: self.validated_capture(workspace),
            ),
        ):
            result = revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
                browser_contract=contract,
            )
        self.assertEqual(contract, build.call_args.kwargs["browser_contract"])
        self.assertEqual(
            revision.current_build._load_browser_contract(
                contract, ("DESIGN.md", child_page)
            )[2],
            result["build"]["browser_contract"],
        )

    def test_invalid_browser_contract_fails_before_any_side_effect(self) -> None:
        contract = self.browser_contract()
        payload = json.loads(contract.read_text(encoding="utf-8"))
        payload["cases"][0]["page"] = "directions/unknown.html"
        contract.write_text(json.dumps(payload), encoding="utf-8")
        with (
            mock.patch.object(revision.decision, "validate_cohort_source", return_value=self.cohort_source()),
            mock.patch.object(revision.decision, "validate_decision_receipt", return_value=self.revise_source()),
            mock.patch.object(revision.current_build, "run") as build,
            self.assertRaisesRegex(revision.DraftRevisionError, "browser contract"),
        ):
            revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
                browser_contract=contract,
            )
        build.assert_not_called()
        self.assertEqual([], list(self.revision_root.iterdir()))
        self.assertEqual([], list(self.revision_logs.iterdir()))

    def test_hardlinked_browser_contract_fails_before_any_side_effect(self) -> None:
        contract = self.browser_contract()
        alias = self.root / "revision-browser-contract-alias.json"
        os.link(contract, alias)
        with (
            mock.patch.object(revision.decision, "validate_cohort_source", return_value=self.cohort_source()),
            mock.patch.object(revision.decision, "validate_decision_receipt", return_value=self.revise_source()),
            mock.patch.object(revision.current_build, "run") as build,
            self.assertRaisesRegex(revision.DraftRevisionError, "provenance"),
        ):
            revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
                browser_contract=contract,
            )
        build.assert_not_called()
        self.assertEqual([], list(self.revision_root.iterdir()))

    def test_browser_contract_drift_after_build_blocks_capture(self) -> None:
        contract = self.browser_contract()

        def drifting_build(
            brief: Path, workspace: Path, **kwargs: object
        ) -> dict[str, object]:
            manifest = self.fake_build(brief, workspace, **kwargs)
            contract.write_text(contract.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            return manifest

        with (
            mock.patch.object(revision.decision, "validate_cohort_source", return_value=self.cohort_source()),
            mock.patch.object(revision.decision, "validate_decision_receipt", return_value=self.revise_source()),
            mock.patch.object(revision.current_build, "run", side_effect=drifting_build),
            mock.patch.object(revision.cohort, "run_capture") as capture,
            self.assertRaisesRegex(revision.DraftRevisionError, "contract drifted"),
        ):
            revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
                browser_contract=contract,
            )
        capture.assert_not_called()
        self.assertFalse((self.revision_root / "draft-revision-receipt.json").exists())

    def test_browser_contract_must_be_bound_by_the_build_manifest(self) -> None:
        contract = self.browser_contract()

        def unbound_build(
            brief: Path, workspace: Path, **kwargs: object
        ) -> dict[str, object]:
            manifest = self.fake_build(brief, workspace, **kwargs)
            manifest.pop("browser_contract")
            (workspace / "run-manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            return manifest

        with (
            mock.patch.object(revision.decision, "validate_cohort_source", return_value=self.cohort_source()),
            mock.patch.object(revision.decision, "validate_decision_receipt", return_value=self.revise_source()),
            mock.patch.object(revision.current_build, "run", side_effect=unbound_build),
            mock.patch.object(revision.cohort, "run_capture") as capture,
            self.assertRaisesRegex(revision.DraftRevisionError, "provenance"),
        ):
            revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
                browser_contract=contract,
            )
        capture.assert_not_called()

    def test_capture_drift_before_receipt_is_rejected(self) -> None:
        first = None

        def drift_capture(workspace: Path, *_args: object) -> dict[str, object]:
            nonlocal first
            current = self.validated_capture(workspace)
            if first is None:
                first = current
                return current
            current["capture_set_sha256"] = "0" * 64
            return current

        with (
            mock.patch.object(revision.decision, "validate_cohort_source", return_value=self.cohort_source()),
            mock.patch.object(revision.decision, "validate_decision_receipt", return_value=self.revise_source()),
            mock.patch.object(revision.current_build, "run", side_effect=self.fake_build),
            mock.patch.object(revision.cohort, "run_capture", side_effect=self.fake_capture),
            mock.patch.object(
                revision, "validate_current_capture_evidence", side_effect=drift_capture
            ),
            self.assertRaisesRegex(revision.DraftRevisionError, "finalization"),
        ):
            revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
            )
        self.assertFalse((self.revision_root / "draft-revision-receipt.json").exists())

    def test_invalid_action_fails_before_output_or_builder(self) -> None:
        invalid = self.revise_source()
        invalid["receipt"]["decision"]["action"] = "select"
        with (
            mock.patch.object(revision.decision, "validate_cohort_source", return_value=self.cohort_source()),
            mock.patch.object(revision.decision, "validate_decision_receipt", return_value=invalid),
            mock.patch.object(revision.current_build, "run") as build,
            self.assertRaises(revision.DraftRevisionError),
        ):
            revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
            )
        build.assert_not_called()
        self.assertEqual([], list(self.revision_root.iterdir()))
        self.assertEqual([], list(self.revision_logs.iterdir()))

    def test_repair_rounds_cannot_exceed_existing_builder_bound(self) -> None:
        with self.assertRaisesRegex(revision.DraftRevisionError, "within 0..2"):
            revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
                max_repair_rounds=3,
            )
        self.assertEqual([], list(self.revision_root.iterdir()))

    def test_brief_drift_fails_before_output_or_builder(self) -> None:
        source = self.cohort_source()
        source["receipt"]["source"]["base_brief"]["sha256"] = "0" * 64
        with (
            mock.patch.object(revision.decision, "validate_cohort_source", return_value=source),
            mock.patch.object(revision.decision, "validate_decision_receipt", return_value=self.revise_source()),
            mock.patch.object(revision.current_build, "run") as build,
            self.assertRaisesRegex(revision.DraftRevisionError, "brief"),
        ):
            revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
            )
        build.assert_not_called()
        self.assertEqual([], list(self.revision_root.iterdir()))

    def test_unchanged_child_html_cannot_be_fresh_revision_evidence(self) -> None:
        def unchanged_build(brief: Path, workspace: Path, **kwargs: object) -> dict[str, object]:
            manifest = self.fake_build(brief, workspace, **kwargs)
            child = next(name for name in kwargs["outputs"] if str(name).endswith(".html"))
            (workspace / child).write_bytes((Path(kwargs["seed_root"]) / child).read_bytes())
            for output in manifest["outputs"]:
                path = workspace / output["path"]
                output.update(bytes=path.stat().st_size, sha256=digest(path))
            manifest["mutation"]["observed_changes"] = ["DESIGN.md"]
            (workspace / "run-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            return manifest

        with (
            mock.patch.object(revision.decision, "validate_cohort_source", return_value=self.cohort_source()),
            mock.patch.object(revision.decision, "validate_decision_receipt", return_value=self.revise_source()),
            mock.patch.object(revision.current_build, "run", side_effect=unchanged_build),
            mock.patch.object(revision.cohort, "run_capture") as capture,
            self.assertRaisesRegex(revision.DraftRevisionError, "measurably change"),
        ):
            revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
            )
        capture.assert_not_called()
        self.assertFalse((self.revision_root / "draft-revision-receipt.json").exists())

    def test_revision_seed_must_match_the_parent_output_before_build(self) -> None:
        real_copy = revision.shutil.copy2

        def corrupt_child_seed(source: Path, destination: Path) -> Path:
            copied = real_copy(source, destination)
            target = Path(destination)
            if target.suffix == ".html":
                target.write_text(
                    '<!doctype html><html lang="zh-Hant"><body><main><h1>Unbound seed</h1></main></body></html>',
                    encoding="utf-8",
                )
            return Path(copied)

        with (
            mock.patch.object(revision.decision, "validate_cohort_source", return_value=self.cohort_source()),
            mock.patch.object(revision.decision, "validate_decision_receipt", return_value=self.revise_source()),
            mock.patch.object(revision.shutil, "copy2", side_effect=corrupt_child_seed),
            mock.patch.object(revision.current_build, "run", side_effect=self.fake_build) as build,
            mock.patch.object(revision.cohort, "run_capture", side_effect=self.fake_capture) as capture,
            mock.patch.object(
                revision,
                "validate_current_capture_evidence",
                side_effect=lambda workspace, *_args: self.validated_capture(workspace),
            ),
            self.assertRaisesRegex(revision.DraftRevisionError, "seed provenance"),
        ):
            revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
            )
        build.assert_not_called()
        capture.assert_not_called()
        self.assertFalse((self.revision_root / "draft-revision-receipt.json").exists())

    def test_source_drift_before_capture_blocks_new_evidence(self) -> None:
        stable = self.cohort_source()
        drifted = self.cohort_source()
        drifted["receipt_record"] = {**drifted["receipt_record"], "sha256": "9" * 64}
        with (
            mock.patch.object(
                revision.decision,
                "validate_cohort_source",
                side_effect=[stable, stable, stable, drifted],
            ),
            mock.patch.object(
                revision.decision,
                "validate_decision_receipt",
                return_value=self.revise_source(),
            ),
            mock.patch.object(revision.current_build, "run", side_effect=self.fake_build),
            mock.patch.object(revision.cohort, "run_capture") as capture,
            self.assertRaisesRegex(revision.DraftRevisionError, "provenance"),
        ):
            revision.run(
                self.brief,
                self.cohort_root,
                self.cohort_logs,
                self.decision,
                self.decision_receipt,
                self.revision_root,
                self.revision_logs,
            )
        capture.assert_not_called()
        self.assertFalse((self.revision_root / "draft-revision-receipt.json").exists())

    def test_package_and_platform_expose_one_documented_revision_wrapper(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(
            "python3 evals/run_current_draft_revision.py",
            package["scripts"]["drafts:revise"],
        )
        documentation = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")
        self.assertIn("npm run drafts:revise --", documentation)
        platform = json.loads((ROOT / "evals" / "platform-support.json").read_text(encoding="utf-8"))
        target = next(item for item in platform["targets"] if item["id"] == "evaluator-posix-runners")
        self.assertIn("evals/run_current_draft_revision.py", target["entrypoints"])
        self.assertIn("tests/test_run_current_draft_revision.py", target["artifacts"])


if __name__ == "__main__":
    unittest.main()
