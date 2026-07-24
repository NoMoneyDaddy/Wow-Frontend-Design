#!/usr/bin/env python3
"""Regression tests for the post-capture draft decision checkpoint."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))

import record_current_draft_decision as decision  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CurrentDraftDecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.cohort_root = self.root / "cohort"
        self.log_dir = self.root / "logs"
        self.output_root = self.root / "decision"
        self.cohort_root.mkdir()
        self.log_dir.mkdir()
        self.output_root.mkdir()
        (self.cohort_root / "workspace").mkdir()
        (self.cohort_root / "evidence").mkdir()
        self.case_path = self.log_dir / "draft-cohort-case.json"
        self.case_path.write_text("{}\n", encoding="utf-8")
        self.case_path.chmod(0o600)
        self.effective_path = self.log_dir / "draft-cohort-effective-brief.md"
        self.effective_path.write_text("brief\n", encoding="utf-8")
        self.effective_path.chmod(0o600)
        self.convergence_config_path = self.log_dir / "draft-cohort-convergence.json"
        self.convergence_config_path.write_text("{}\n", encoding="utf-8")
        self.convergence_config_path.chmod(0o600)
        self.manifest_path = self.cohort_root / "workspace" / "run-manifest.json"
        self.manifest_path.write_text("{}\n", encoding="utf-8")
        self.capture_path = self.cohort_root / "evidence" / "capture-receipt.json"
        self.capture_path.write_text("{}\n", encoding="utf-8")
        self.capture_path.chmod(0o600)
        self.decision_path = self.root / "input.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def variant(self, identifier: str) -> dict:
        return {
            "id": identifier,
            "hypothesis": f"{identifier} hypothesis",
            "changed_axes": ["composition", "typography"],
            "expected_benefit": "讓主要任務更清楚。",
            "risk": "可能降低資訊密度。",
            "disqualifier": "主要行動不可見。",
        }

    def convergence(self, review_required: bool = True) -> dict:
        counts = {
            "cross_output_partial_visual_grammar_candidate": 0,
            "cross_output_template_candidate": 0,
            "cross_output_visual_grammar_candidate": 1 if review_required else 0,
            "near_cross_output_template_candidate": 0,
        }
        return {
            "status": "completed",
            "result": "advisories_present" if review_required else "no_exact_template_candidates",
            "policy": "advisory_only",
            "profiles": ["desktop-default", "mobile-default"],
            "observation_count": 4,
            "advisory_count": 1 if review_required else 0,
            "advisory_counts": counts,
            "affected_variant_ids": ["editorial-index", "task-led-market"] if review_required else [],
            "review_required": review_required,
            "observations": {"path": "evidence/macro-observations.json", "bytes": 1, "mode": "0600", "sha256": "a" * 64},
            "audit": {"path": "evidence/cross-output-template-audit.json", "bytes": 1, "mode": "0600", "sha256": "b" * 64},
            "claim_boundary": "advisory only",
        }

    def cohort_receipt(self, review_required: bool = True, held_axes: list[str] | None = None) -> dict:
        return {
            "schema_version": 1,
            "status": "captured",
            "classification": "draft_cohort_captured",
            "claim_boundary": "style_calibration_only",
            "cohort": {
                "cohort_id": "marketplace-directions-1",
                "partition": "validation",
                "locale": "zh-Hant",
                "surface": "marketplace-home",
                "decision_question": "哪一組最能支援主要任務？",
                "held_constant_axes": held_axes or [
                    "product-facts",
                    "content-fixture",
                    "functional-behavior",
                    "comparison-conditions",
                ],
                "selection_criteria": ["主要任務清晰", "品牌辨識度"],
                "variant_count": 2,
                "variants": [self.variant("editorial-index"), self.variant("task-led-market")],
            },
            "source": {
                "plan": {"bytes": 10, "sha256": "1" * 64},
                "base_brief": {"bytes": 10, "sha256": "2" * 64},
                "effective_brief": {"bytes": self.effective_path.stat().st_size, "sha256": digest(self.effective_path)},
                "case": {"bytes": self.case_path.stat().st_size, "sha256": digest(self.case_path)},
                "convergence_config": {"bytes": self.convergence_config_path.stat().st_size, "sha256": digest(self.convergence_config_path)},
                "run_manifest": {"path": "workspace/run-manifest.json", "bytes": self.manifest_path.stat().st_size, "mode": "0644", "sha256": digest(self.manifest_path)},
                "capture_receipt": {"path": "evidence/capture-receipt.json", "bytes": self.capture_path.stat().st_size, "mode": "0600", "sha256": digest(self.capture_path)},
                "skill_tree_sha256": "5" * 64,
                "outputs": [
                    {"path": "DESIGN.md", "bytes": 10, "mode": "0644", "sha256": "6" * 64},
                    {"path": "directions/editorial-index.html", "bytes": 10, "mode": "0644", "sha256": "7" * 64},
                    {"path": "directions/task-led-market.html", "bytes": 10, "mode": "0644", "sha256": "8" * 64},
                ],
            },
            "configuration": {
                "model": "gpt-5.4-mini",
                "reasoning_effort": "high",
                "max_repair_rounds": 1,
                "browser_contract": None,
                "skill_reference": "references/design-exploration.md",
                "capture_standard": decision.cohort.CAPTURE_STANDARD,
            },
            "evidence": {
                "capture_count": 4,
                "capture_set_sha256": "9" * 64,
                "capture_standard": decision.cohort.CAPTURE_STANDARD,
                "convergence": self.convergence(review_required),
            },
            "tools": [{"path": "evals/run_current_draft_cohort.py", "bytes": 1, "mode": "0644", "sha256": "0" * 64}],
        }

    def validated_capture(self) -> dict:
        captures = []
        for variant in ("editorial-index", "task-led-market"):
            for profile in ("desktop-default", "mobile-default"):
                captures.append({
                    "label": f"{variant}-{profile}",
                    "page": f"directions/{variant}.html",
                    "profile": profile,
                })
        return {
            "receipt": {"captures": captures},
            "manifest": {
                "skill_snapshot": {"tree_sha256": "5" * 64},
                "outputs": self.cohort_receipt()["source"]["outputs"],
            },
            "capture_count": 4,
            "capture_set_sha256": "9" * 64,
            "capture_standard": decision.cohort.CAPTURE_STANDARD,
        }

    def write_cohort_receipt(self, review_required: bool = True, payload: dict | None = None) -> Path:
        path = self.cohort_root / "draft-cohort-receipt.json"
        path.write_text(
            json.dumps(payload or self.cohort_receipt(review_required), ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        path.chmod(0o600)
        return path

    def valid_decision(self, **updates: object) -> dict:
        value = {
            "schema_version": 1,
            "cohort_id": "marketplace-directions-1",
            "action": "select",
            "variant_id": "editorial-index",
            "authority": "user_confirmed",
            "reason": "資訊層級最清楚。",
            "adjustments": ["主操作再突出。"],
            "convergence_reviewed": True,
        }
        value.update(updates)
        return value

    def run_with_source(
        self,
        payload: dict,
        review_required: bool = True,
        cohort_payload: dict | None = None,
    ) -> dict:
        receipt_value = cohort_payload or self.cohort_receipt(review_required)
        receipt_path = self.write_cohort_receipt(review_required, receipt_value)
        self.decision_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        self.decision_path.chmod(0o600)
        with (
            mock.patch.object(decision, "validate_current_capture_evidence", return_value=self.validated_capture()),
            mock.patch.object(decision.cohort, "_convergence_summary", return_value=self.convergence(review_required)),
            mock.patch.object(decision.cohort, "_tool_records", return_value=receipt_value["tools"]),
        ):
            result = decision.run(self.cohort_root, self.log_dir, self.decision_path, self.output_root)
        self.assertEqual(digest(receipt_path), result["source"]["cohort_receipt"]["sha256"])
        return result

    def test_valid_select_is_bound_to_fresh_variant_evidence_and_private(self) -> None:
        result = self.run_with_source(self.valid_decision())
        output = self.output_root / "draft-decision-receipt.json"
        self.assertEqual("draft_direction_selected", result["classification"])
        self.assertEqual("selection_lineage_only_no_release_acceptance", result["claim_boundary"])
        self.assertEqual("editorial-index", result["decision"]["variant"]["id"])
        self.assertEqual(
            ["editorial-index-desktop-default", "editorial-index-mobile-default"],
            result["decision"]["capture_labels"],
        )
        self.assertEqual("implement_selected_direction", result["handoff"]["next_step"])
        self.assertEqual("BUILD", result["handoff"]["production_lane"])
        self.assertEqual("0600", result["source"]["decision_input"]["mode"])
        self.assertEqual(
            {"schema_version", "status", "classification", "claim_boundary", "source", "decision", "handoff", "tools"},
            set(result),
        )
        self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))

    def test_seeded_subset_selection_is_manual_retrofit_input_not_build_handoff(self) -> None:
        self.case_path.write_text(
            json.dumps({
                "capture_plan": {
                    "pages": {
                        "policy": "draft_direction_subset",
                        "paths": [
                            "directions/editorial-index.html",
                            "directions/task-led-market.html",
                        ],
                    }
                }
            }),
            encoding="utf-8",
        )

        result = self.run_with_source(self.valid_decision())

        self.assertIsNone(result["handoff"]["production_lane"])
        self.assertEqual(
            "carry_selected_direction_to_retrofit_brief",
            result["handoff"]["next_step"],
        )
        self.assertIn(
            "formal RETROFIT implementation",
            result["handoff"]["required_revalidation"],
        )

    def test_public_validator_rechecks_receipt_and_original_sources(self) -> None:
        receipt_value = self.cohort_receipt()
        self.write_cohort_receipt(payload=receipt_value)
        self.decision_path.write_text(json.dumps(self.valid_decision()), encoding="utf-8")
        self.decision_path.chmod(0o600)
        with (
            mock.patch.object(decision, "validate_current_capture_evidence", return_value=self.validated_capture()),
            mock.patch.object(decision.cohort, "_convergence_summary", return_value=self.convergence()),
            mock.patch.object(decision.cohort, "_tool_records", return_value=receipt_value["tools"]),
        ):
            recorded = decision.run(self.cohort_root, self.log_dir, self.decision_path, self.output_root)
            validated = decision.validate_decision_receipt(
                self.cohort_root,
                self.log_dir,
                self.decision_path,
                self.output_root / "draft-decision-receipt.json",
            )
        self.assertEqual(recorded, validated["receipt"])
        self.assertEqual("0600", validated["receipt_record"]["mode"])

        self.decision_path.write_text(json.dumps(self.valid_decision(reason="另一個理由。")), encoding="utf-8")
        self.decision_path.chmod(0o600)
        with (
            mock.patch.object(decision, "validate_current_capture_evidence", return_value=self.validated_capture()),
            mock.patch.object(decision.cohort, "_convergence_summary", return_value=self.convergence()),
            mock.patch.object(decision.cohort, "_tool_records", return_value=receipt_value["tools"]),
            self.assertRaisesRegex(decision.DraftDecisionError, "receipt provenance"),
        ):
            decision.validate_decision_receipt(
                self.cohort_root,
                self.log_dir,
                self.decision_path,
                self.output_root / "draft-decision-receipt.json",
            )

    def test_browser_contract_record_is_closed_and_matches_validated_manifest(self) -> None:
        valid_record = {
            "schema_version": 2,
            "bytes": 100,
            "sha256": "c" * 64,
            "case_count": 2,
            "step_count": 4,
        }
        receipt_value = self.cohort_receipt()
        receipt_value["configuration"]["browser_contract"] = valid_record
        self.write_cohort_receipt(payload=receipt_value)
        validated = self.validated_capture()
        validated["manifest"]["browser_contract"] = valid_record
        with (
            mock.patch.object(
                decision,
                "validate_current_capture_evidence",
                return_value=validated,
            ),
            mock.patch.object(
                decision.cohort,
                "_convergence_summary",
                return_value=self.convergence(),
            ),
            mock.patch.object(
                decision.cohort,
                "_tool_records",
                return_value=receipt_value["tools"],
            ),
        ):
            observed = decision.validate_cohort_source(
                self.cohort_root,
                self.log_dir,
            )
        self.assertEqual(
            valid_record,
            observed["receipt"]["configuration"]["browser_contract"],
        )

        validated["manifest"].pop("browser_contract")
        with (
            mock.patch.object(
                decision,
                "validate_current_capture_evidence",
                return_value=validated,
            ),
            mock.patch.object(
                decision.cohort,
                "_tool_records",
                return_value=receipt_value["tools"],
            ),
            self.assertRaisesRegex(
                decision.DraftDecisionError,
                "manifest projection drifted",
            ),
        ):
            decision.validate_cohort_source(self.cohort_root, self.log_dir)

        malformed = dict(valid_record)
        malformed["bytes"] = True
        receipt_value["configuration"]["browser_contract"] = malformed
        self.write_cohort_receipt(payload=receipt_value)
        validated["manifest"]["browser_contract"] = malformed
        with (
            mock.patch.object(
                decision,
                "validate_current_capture_evidence",
                return_value=validated,
            ),
            mock.patch.object(
                decision.cohort,
                "_tool_records",
                return_value=receipt_value["tools"],
            ),
            self.assertRaisesRegex(
                decision.DraftDecisionError,
                "browser_contract is invalid",
            ),
        ):
            decision.validate_cohort_source(self.cohort_root, self.log_dir)

    def test_revise_and_stop_have_bounded_distinct_handoffs(self) -> None:
        revise = self.run_with_source(self.valid_decision(action="revise", adjustments=["改變資訊層級。"]))
        self.assertEqual("draft_direction_revision_requested", revise["classification"])
        self.assertEqual("render_one_bounded_revision", revise["handoff"]["next_step"])
        self.assertIsNone(revise["handoff"]["production_lane"])

        with tempfile.TemporaryDirectory() as directory:
            self.output_root = Path(directory).resolve()
            stop = self.run_with_source(self.valid_decision(action="stop", variant_id=None, adjustments=[]))
        self.assertEqual("draft_direction_stopped", stop["classification"])
        self.assertEqual("stop_before_production", stop["handoff"]["next_step"])
        self.assertIsNone(stop["handoff"]["production_lane"])

    def test_action_shape_and_human_authority_fail_closed(self) -> None:
        invalid = (
            self.valid_decision(action="revise", adjustments=[]),
            self.valid_decision(action="stop", variant_id="editorial-index"),
            self.valid_decision(action="select", variant_id=None),
            self.valid_decision(authority="automatic"),
            self.valid_decision(authority=[]),
            self.valid_decision(schema_version=True),
            self.valid_decision(action=[]),
            self.valid_decision(action="stop", variant_id=None, adjustments=["不應存在。"]),
            self.valid_decision(extra=True),
        )
        for payload in invalid:
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as directory:
                self.output_root = Path(directory).resolve()
                with self.assertRaises(decision.DraftDecisionError):
                    self.run_with_source(payload)

    def test_unknown_variant_and_unreviewed_convergence_are_rejected(self) -> None:
        for payload in (
            self.valid_decision(variant_id="missing"),
            self.valid_decision(convergence_reviewed=False),
        ):
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as directory:
                self.output_root = Path(directory).resolve()
                with self.assertRaises(decision.DraftDecisionError):
                    self.run_with_source(payload)

    def test_no_advisory_does_not_require_false_review_claim(self) -> None:
        result = self.run_with_source(
            self.valid_decision(convergence_reviewed=False), review_required=False
        )
        self.assertFalse(result["decision"]["convergence_reviewed"])

    def test_cohort_axis_bounds_round_trip_without_schema_drift(self) -> None:
        held_axes = [f"constant-{index}" for index in range(13)]
        receipt = self.cohort_receipt(held_axes=held_axes)
        result = self.run_with_source(self.valid_decision(), cohort_payload=receipt)
        self.assertEqual(held_axes, result["handoff"]["held_constant_axes"])

        receipt = self.cohort_receipt()
        receipt["cohort"]["variants"][0]["changed_axes"] = [f"axis-{index}" for index in range(7)]
        with tempfile.TemporaryDirectory() as directory:
            self.output_root = Path(directory).resolve()
            with self.assertRaisesRegex(decision.DraftDecisionError, "2..6"):
                self.run_with_source(self.valid_decision(), cohort_payload=receipt)

    def test_receipt_and_nested_schema_are_closed(self) -> None:
        receipt = self.cohort_receipt()
        receipt["extra"] = True
        path = self.cohort_root / "draft-cohort-receipt.json"
        path.write_text(json.dumps(receipt), encoding="utf-8")
        path.chmod(0o600)
        self.decision_path.write_text(json.dumps(self.valid_decision()), encoding="utf-8")
        self.decision_path.chmod(0o600)
        with self.assertRaisesRegex(decision.DraftDecisionError, "cohort receipt schema"):
            decision.run(self.cohort_root, self.log_dir, self.decision_path, self.output_root)

    def test_source_record_drift_is_rejected(self) -> None:
        self.write_cohort_receipt()
        self.manifest_path.write_text('{"tampered":true}\n', encoding="utf-8")
        self.decision_path.write_text(json.dumps(self.valid_decision()), encoding="utf-8")
        self.decision_path.chmod(0o600)
        with (
            mock.patch.object(decision.cohort, "_tool_records", return_value=self.cohort_receipt()["tools"]),
            self.assertRaisesRegex(decision.DraftDecisionError, "run manifest provenance"),
        ):
            decision.run(self.cohort_root, self.log_dir, self.decision_path, self.output_root)

    def test_receipt_output_projection_cannot_drift_from_validated_manifest(self) -> None:
        receipt = self.cohort_receipt()
        receipt["source"]["outputs"][1]["sha256"] = "f" * 64
        path = self.cohort_root / "draft-cohort-receipt.json"
        path.write_text(json.dumps(receipt), encoding="utf-8")
        path.chmod(0o600)
        self.decision_path.write_text(json.dumps(self.valid_decision()), encoding="utf-8")
        self.decision_path.chmod(0o600)
        with (
            mock.patch.object(decision, "validate_current_capture_evidence", return_value=self.validated_capture()),
            mock.patch.object(decision.cohort, "_convergence_summary", return_value=self.convergence()),
            mock.patch.object(decision.cohort, "_tool_records", return_value=self.cohort_receipt()["tools"]),
            self.assertRaisesRegex(decision.DraftDecisionError, "manifest projection"),
        ):
            decision.run(self.cohort_root, self.log_dir, self.decision_path, self.output_root)

    def test_existing_or_symlink_output_is_never_overwritten(self) -> None:
        self.write_cohort_receipt()
        self.decision_path.write_text(json.dumps(self.valid_decision()), encoding="utf-8")
        self.decision_path.chmod(0o600)
        output = self.output_root / "draft-decision-receipt.json"
        output.write_text("keep", encoding="utf-8")
        with self.assertRaises(decision.DraftDecisionError):
            self.run_with_source(self.valid_decision())
        self.assertEqual("keep", output.read_text(encoding="utf-8"))

    def test_symlink_and_hardlink_decision_inputs_are_rejected(self) -> None:
        self.decision_path.write_text(json.dumps(self.valid_decision()), encoding="utf-8")
        self.decision_path.chmod(0o600)
        symlink = self.root / "decision-symlink.json"
        symlink.symlink_to(self.decision_path)
        hardlink = self.root / "decision-hardlink.json"
        os.link(self.decision_path, hardlink)
        for path in (symlink, hardlink):
            with self.subTest(path=path), self.assertRaises(decision.DraftDecisionError):
                decision.load_decision(path)

    def test_cohort_tool_provenance_is_revalidated(self) -> None:
        self.write_cohort_receipt()
        self.decision_path.write_text(json.dumps(self.valid_decision()), encoding="utf-8")
        self.decision_path.chmod(0o600)
        with self.assertRaisesRegex(decision.DraftDecisionError, "tool provenance"):
            decision.run(self.cohort_root, self.log_dir, self.decision_path, self.output_root)

    def test_fixed_source_paths_cannot_be_forged(self) -> None:
        receipt = self.cohort_receipt()
        receipt["source"]["run_manifest"]["path"] = "workspace/other.json"
        path = self.cohort_root / "draft-cohort-receipt.json"
        path.write_text(json.dumps(receipt), encoding="utf-8")
        path.chmod(0o600)
        self.decision_path.write_text(json.dumps(self.valid_decision()), encoding="utf-8")
        self.decision_path.chmod(0o600)
        with (
            mock.patch.object(decision.cohort, "_tool_records", return_value=receipt["tools"]),
            self.assertRaisesRegex(decision.DraftDecisionError, "provenance path"),
        ):
            decision.run(self.cohort_root, self.log_dir, self.decision_path, self.output_root)

    def test_source_drift_after_first_validation_blocks_finalization(self) -> None:
        self.write_cohort_receipt()
        self.decision_path.write_text(json.dumps(self.valid_decision()), encoding="utf-8")
        self.decision_path.chmod(0o600)
        calls = 0

        def validate_and_drift(*_args: object) -> dict:
            nonlocal calls
            calls += 1
            if calls == 1:
                self.manifest_path.write_text('{"drifted":true}\n', encoding="utf-8")
            return self.validated_capture()

        with (
            mock.patch.object(decision, "validate_current_capture_evidence", side_effect=validate_and_drift),
            mock.patch.object(decision.cohort, "_convergence_summary", return_value=self.convergence()),
            mock.patch.object(decision.cohort, "_tool_records", return_value=self.cohort_receipt()["tools"]),
            self.assertRaisesRegex(decision.DraftDecisionError, "run manifest provenance"),
        ):
            decision.run(self.cohort_root, self.log_dir, self.decision_path, self.output_root)
        self.assertFalse((self.output_root / "draft-decision-receipt.json").exists())

    def test_decision_hardlink_added_after_read_blocks_finalization(self) -> None:
        original = decision.load_decision

        def load_and_link(path: Path) -> dict:
            value = original(path)
            os.link(path, self.root / "late-hardlink.json")
            return value

        with mock.patch.object(decision, "load_decision", side_effect=load_and_link):
            with self.assertRaises(decision.DraftDecisionError):
                self.run_with_source(self.valid_decision())
        self.assertFalse((self.output_root / "draft-decision-receipt.json").exists())

    @unittest.skipUnless(Path("/dev/fd").is_dir(), "requires POSIX descriptor inspection")
    def test_rejected_nested_output_does_not_leak_directory_descriptors(self) -> None:
        nested = self.cohort_root / "nested-output"
        nested.mkdir()
        self.output_root = nested
        before = len(list(Path("/dev/fd").iterdir()))
        for _ in range(12):
            with self.assertRaises(decision.DraftDecisionError):
                self.run_with_source(self.valid_decision())
        after = len(list(Path("/dev/fd").iterdir()))
        self.assertEqual(before, after)

    def test_decision_tool_drift_blocks_finalization(self) -> None:
        stable = decision._decision_tool_records()
        drifted = json.loads(json.dumps(stable))
        drifted["recorder"]["sha256"] = "f" * 64
        with (
            mock.patch.object(decision, "_decision_tool_records", side_effect=[stable, drifted]),
            self.assertRaisesRegex(decision.DraftDecisionError, "tool provenance drifted"),
        ):
            self.run_with_source(self.valid_decision())
        self.assertFalse((self.output_root / "draft-decision-receipt.json").exists())

    def test_output_failure_rechecks_decision_tool_provenance(self) -> None:
        stable = decision._decision_tool_records()
        drifted = json.loads(json.dumps(stable))
        drifted["capture_validator"]["sha256"] = "e" * 64
        with (
            mock.patch.object(decision, "_decision_tool_records", side_effect=[stable, stable, drifted]),
            mock.patch.object(decision.cohort, "_PinnedDirectory", side_effect=OSError("output failed")),
            self.assertRaisesRegex(decision.DraftDecisionError, "drifted during failed finalization"),
        ):
            self.run_with_source(self.valid_decision())

    def test_package_exposes_one_documented_decision_checkpoint(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(
            "python3 evals/record_current_draft_decision.py",
            package["scripts"]["drafts:decide"],
        )
        documentation = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")
        self.assertIn("npm run drafts:decide --", documentation)
        self.assertIn("兩分鐘", documentation)


if __name__ == "__main__":
    unittest.main()
