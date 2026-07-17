#!/usr/bin/env python3
"""Contract tests for the bounded v7 paired-candidate decision compiler."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "evals" / "compile_v7_paired_decision.py"
SPEC = importlib.util.spec_from_file_location("compile_v7_paired_decision", MODULE)
assert SPEC and SPEC.loader
decision = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(decision)

SHA_A = "a" * 64
SHA_B = "b" * 64
BASELINE = {"commit": "1" * 40, "package": [{"path": "SKILL.md", "sha256": "2" * 64}]}
TOOLCHAIN = {"python": "3.9.6", "playwright": "1.58.2"}
EVALUATORS = [{"path": "evals/example.py", "sha256": "3" * 64}]


def _gates(names: tuple[str, ...], status: str = "pass") -> dict[str, str]:
    return {name: status for name in names}


def _family(
    family_id: str = "typography",
    *,
    priority: int = 2,
    accepted: int = 2,
    candidate: int = 1,
    predesignated: bool = True,
) -> dict:
    return {
        "id": family_id,
        "priority": priority,
        "predesignated": predesignated,
        "accepted_failures": accepted,
        "candidate_failures": candidate,
    }


def _hash(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _arms(run_id: str, *, split: str = "validation") -> dict:
    shared = {
        "brief_inventory_sha256": _hash(f"{split}-brief"),
        "input_inventory_sha256": _hash(f"{split}-input"),
        "execution_contract_sha256": _hash("shared-execution-contract"),
    }
    return {
        arm: {
            "generation_manifest_sha256": _hash(f"{run_id}-{arm}-generation"),
            "output_inventory_sha256": _hash(f"{run_id}-{arm}-outputs"),
            "visual_ledger_sha256": _hash(f"{run_id}-{arm}-visual-ledger"),
            "visual_result_inventory_sha256": _hash(f"{run_id}-{arm}-visual-results"),
            "attempt_history_sha256": _hash(f"{run_id}-{arm}-attempts"),
            **shared,
        }
        for arm in ("accepted", "candidate")
    }


def _pair(pair_id: str, evidence_id: str, *, toolchain: str | None = None) -> dict:
    return {
        "id": pair_id,
        "eligible": True,
        "order": "accepted-first" if pair_id != "pair-two" else "candidate-first",
        "manifest_sha256": SHA_A,
        "accepted_package_sha256": _accepted_sha256(),
        "candidate_reference_sha256": SHA_B,
        "evaluator_toolchain_sha256": toolchain or _toolchain_sha256(),
        "evidence_ids": [evidence_id],
        "arms": _arms(pair_id),
        "failure_families": [_family()],
        "new_case_engine_failures": 0,
    }


def _bundle(*, sealed: bool = False) -> dict:
    validation = {
        "status": "not_started",
        "evidence_ids": [],
        "hard_gates": _gates(decision.SEALED_GATES, "not_run"),
        "blind_craft": "not_run",
        "budget_status": "not_run",
        "pairs": [],
    }
    sealed_test = {
        "status": "not_run",
        "accepted_evidence_id": None,
        "candidate_evidence_id": None,
        "arms": None,
    }
    if sealed:
        validation = {
            "status": "complete",
            "evidence_ids": ["validation"],
            "hard_gates": _gates(decision.SEALED_GATES),
            "blind_craft": "pass",
            "budget_status": "within",
            "pairs": [
                _pair("pair-one", "pair-one"),
                _pair("pair-two", "pair-two"),
                _pair("pair-three", "pair-three"),
            ],
        }
        sealed_test = {
            "status": "pass",
            "accepted_evidence_id": "sealed-test-accepted",
            "candidate_evidence_id": "sealed-test-candidate",
            "arms": _arms("sealed-test", split="test"),
        }
    return {
        "schema_version": 1,
        "manifest_sha256": SHA_A,
        "candidate_reference_sha256": SHA_B,
        "accepted_package_sha256": _accepted_sha256(),
        "evaluator_toolchain_sha256": _toolchain_sha256(),
        "artifact_bindings": [
            {"id": item, "path": f"/evaluator/{item}.json", "sha256": "e" * 64}
            for item in (
                "development",
                "validation",
                "pair-one",
                "pair-two",
                "pair-three",
                "sealed-test-accepted",
                "sealed-test-candidate",
            )
        ],
        "development": {
            "status": "complete",
            "evidence_ids": ["development"],
            "hard_gates": _gates(decision.HARD_GATES),
            "failure_families": [_family()],
            "new_case_engine_failures": 0,
        },
        "sealed_validation": validation,
        "sealed_test": sealed_test,
    }


def _manifest() -> dict:
    return {
        "schema_version": 1,
        "stage": "frozen",
        "candidate": {"reference_sha256": SHA_B},
        "baseline": copy.deepcopy(BASELINE),
        "toolchain": copy.deepcopy(TOOLCHAIN),
        "evaluators": copy.deepcopy(EVALUATORS),
    }


def _accepted_sha256() -> str:
    return decision._canonical_sha256(BASELINE)


def _toolchain_sha256() -> str:
    return decision._canonical_sha256({"toolchain": TOOLCHAIN, "evaluators": EVALUATORS})


def _receipt(kind: str, identity: str, payload: dict, bundle: dict) -> dict:
    return {
        "schema_version": 1,
        "kind": kind,
        "identity": identity,
        "payload_sha256": decision._canonical_sha256(payload),
        "manifest_sha256": bundle["manifest_sha256"],
        "accepted_package_sha256": bundle["accepted_package_sha256"],
        "candidate_reference_sha256": bundle["candidate_reference_sha256"],
        "evaluator_toolchain_sha256": bundle["evaluator_toolchain_sha256"],
    }


def _bindings(bundle: dict) -> dict[str, dict]:
    values = {
        "development": {
            "receipt": _receipt("development-decision", "development", bundle["development"], bundle)
        }
    }
    validation = bundle["sealed_validation"]
    if validation["status"] == "complete":
        values["validation"] = {
            "receipt": _receipt("validation-summary", "sealed-validation", validation, bundle)
        }
        for pair in validation["pairs"]:
            for evidence_id in pair["evidence_ids"]:
                values.setdefault(
                    evidence_id,
                    {"receipt": _receipt("paired-run", pair["id"], pair, bundle)},
                )
    sealed_test = bundle["sealed_test"]
    if sealed_test["status"] in {"pass", "fail"}:
        values.setdefault(sealed_test["accepted_evidence_id"], {
            "receipt": _receipt("sealed-test-arm", "sealed-test-accepted", sealed_test, bundle)
        })
        values.setdefault(sealed_test["candidate_evidence_id"], {
            "receipt": _receipt("sealed-test-arm", "sealed-test-candidate", sealed_test, bundle)
        })
    return values


class V7PairedDecisionTests(unittest.TestCase):
    def test_development_improvement_is_only_ready_for_sealed(self) -> None:
        bundle = _bundle()
        status, reason, action = decision.decide_bundle(_manifest(), bundle, _bindings(bundle))
        self.assertEqual("READY_FOR_SEALED", status)
        self.assertEqual("development_ratchet_passed", reason)
        self.assertEqual("run_frozen_sealed_validation", action)

    def test_no_strict_deterministic_improvement_stops_candidate(self) -> None:
        bundle = _bundle()
        bundle["development"]["failure_families"] = [_family(accepted=1, candidate=1)]
        self.assertEqual(
            ("REJECTED_STOP", "no_strict_deterministic_improvement"),
            decision.decide_bundle(_manifest(), bundle, _bindings(bundle))[:2],
        )

    def test_higher_priority_regression_cannot_be_offset(self) -> None:
        bundle = _bundle()
        bundle["development"]["failure_families"] = [
            _family("security", priority=1, accepted=0, candidate=1, predesignated=False),
            _family("typography", priority=2, accepted=2, candidate=1),
        ]
        self.assertEqual(
            "higher_priority_deterministic_regression",
            decision.decide_bundle(_manifest(), bundle, _bindings(bundle))[1],
        )

    def test_hard_gate_failure_wins_even_when_budget_is_within(self) -> None:
        bundle = _bundle(sealed=True)
        bundle["sealed_validation"]["hard_gates"]["security"] = "fail"
        bundle["sealed_validation"]["budget_status"] = "within"
        self.assertEqual(
            ("REJECTED_STOP", "sealed_security_failed"),
            decision.decide_bundle(_manifest(), bundle, _bindings(bundle))[:2],
        )

    def test_missing_gate_evidence_is_unavailable_not_clean(self) -> None:
        bundle = _bundle()
        bundle["development"]["hard_gates"]["evidence_integrity"] = "unavailable"
        self.assertEqual(
            ("UNAVAILABLE", "development_evidence_integrity_unavailable"),
            decision.decide_bundle(_manifest(), bundle, _bindings(bundle))[:2],
        )

    def test_three_complete_pairs_and_test_are_only_eligible_for_acceptance(self) -> None:
        bundle = _bundle(sealed=True)
        status, reason, action = decision.decide_bundle(_manifest(), bundle, _bindings(bundle))
        self.assertEqual("ELIGIBLE_FOR_EVALUATOR_ACCEPTANCE", status)
        self.assertEqual("paired_ratchet_passed", reason)
        self.assertEqual("request_evaluator_acceptance", action)

    def test_two_pairs_are_unavailable(self) -> None:
        bundle = _bundle(sealed=True)
        bundle["sealed_validation"]["pairs"].pop()
        self.assertEqual(
            ("UNAVAILABLE", "sealed_pair_count_incomplete"),
            decision.decide_bundle(_manifest(), bundle, _bindings(bundle))[:2],
        )

    def test_pair_toolchain_drift_is_unavailable(self) -> None:
        bundle = _bundle(sealed=True)
        bundle["sealed_validation"]["pairs"][1]["evaluator_toolchain_sha256"] = "f" * 64
        self.assertEqual(
            ("UNAVAILABLE", "sealed_pair_provenance_drift"),
            decision.decide_bundle(_manifest(), bundle, _bindings(bundle))[:2],
        )

    def test_package_and_toolchain_digests_must_derive_from_manifest(self) -> None:
        package = _bundle()
        package["accepted_package_sha256"] = "f" * 64
        with self.assertRaisesRegex(
            decision.V7PairedDecisionUnavailable, "accepted_package_manifest_drift"
        ):
            decision.decide_bundle(_manifest(), package, _bindings(package))

        toolchain = _bundle()
        toolchain["evaluator_toolchain_sha256"] = "f" * 64
        with self.assertRaisesRegex(
            decision.V7PairedDecisionUnavailable, "evaluator_toolchain_manifest_drift"
        ):
            decision.decide_bundle(_manifest(), toolchain, _bindings(toolchain))

    def test_three_pairs_cannot_reuse_one_evidence_receipt(self) -> None:
        bundle = _bundle(sealed=True)
        bundle["sealed_validation"]["pairs"][1]["evidence_ids"] = ["pair-one"]
        self.assertEqual(
            ("UNAVAILABLE", "sealed_pair_evidence_reused"),
            decision.decide_bundle(_manifest(), bundle, _bindings(bundle))[:2],
        )

    def test_three_pairs_require_both_presentation_orders(self) -> None:
        bundle = _bundle(sealed=True)
        for pair in bundle["sealed_validation"]["pairs"]:
            pair["order"] = "accepted-first"
        self.assertEqual(
            ("UNAVAILABLE", "sealed_pair_order_unbalanced"),
            decision.decide_bundle(_manifest(), bundle, _bindings(bundle))[:2],
        )

    def test_pair_arms_require_matching_inputs_and_distinct_run_sources(self) -> None:
        reused = _bundle(sealed=True)
        arms = reused["sealed_validation"]["pairs"][0]["arms"]
        arms["candidate"]["generation_manifest_sha256"] = arms["accepted"][
            "generation_manifest_sha256"
        ]
        with self.assertRaisesRegex(decision.V7PairedDecisionUnavailable, "sealed_pair_source_reused"):
            decision.decide_bundle(_manifest(), reused, _bindings(reused))

        drifted = _bundle(sealed=True)
        drifted["sealed_validation"]["pairs"][0]["arms"]["candidate"][
            "brief_inventory_sha256"
        ] = _hash("different-brief")
        with self.assertRaisesRegex(decision.V7PairedDecisionUnavailable, "sealed_pair_arm_input_drift"):
            decision.decide_bundle(_manifest(), drifted, _bindings(drifted))

    def test_pair_arm_missing_attempt_source_is_unavailable(self) -> None:
        bundle = _bundle(sealed=True)
        del bundle["sealed_validation"]["pairs"][0]["arms"]["candidate"][
            "attempt_history_sha256"
        ]
        with self.assertRaisesRegex(decision.V7PairedDecisionUnavailable, "schema_changed"):
            decision.decide_bundle(_manifest(), bundle, _bindings(bundle))

    def test_sealed_test_cannot_reuse_validation_or_pair_evidence(self) -> None:
        bundle = _bundle(sealed=True)
        bundle["sealed_test"]["accepted_evidence_id"] = "pair-one"
        self.assertEqual(
            ("UNAVAILABLE", "sealed_test_evidence_reused"),
            decision.decide_bundle(_manifest(), bundle, _bindings(bundle))[:2],
        )

    def test_sealed_test_cannot_reuse_validation_run_sources(self) -> None:
        bundle = _bundle(sealed=True)
        pair_source = bundle["sealed_validation"]["pairs"][0]["arms"]["accepted"][
            "output_inventory_sha256"
        ]
        bundle["sealed_test"]["arms"]["accepted"]["output_inventory_sha256"] = pair_source
        with self.assertRaisesRegex(decision.V7PairedDecisionUnavailable, "sealed_test_source_reused"):
            decision.decide_bundle(_manifest(), bundle, _bindings(bundle))

    def test_material_craft_loss_and_sealed_test_failure_stop(self) -> None:
        craft = _bundle(sealed=True)
        craft["sealed_validation"]["blind_craft"] = "material_loss"
        self.assertEqual(
            "sealed_blind_craft_material_loss",
            decision.decide_bundle(_manifest(), craft, _bindings(craft))[1],
        )

        test = _bundle(sealed=True)
        test["sealed_test"]["status"] = "fail"
        self.assertEqual(
            "sealed_test_failed",
            decision.decide_bundle(_manifest(), test, _bindings(test))[1],
        )

    def test_not_started_validation_cannot_hide_a_test_result(self) -> None:
        bundle = _bundle()
        bundle["sealed_test"] = {
            "status": "fail",
            "accepted_evidence_id": "sealed-test-accepted",
            "candidate_evidence_id": "sealed-test-candidate",
            "arms": _arms("sealed-test", split="test"),
        }
        with self.assertRaisesRegex(decision.V7PairedDecisionUnavailable, "sealed_not_started_contract_invalid"):
            decision.decide_bundle(_manifest(), bundle, _bindings(bundle))

    def test_pilot_manifest_returns_unavailable_without_a_bundle(self) -> None:
        pilot = {
            "cohort_id": "pilot-cohort",
            "stage": "pilot_ready",
            "candidate": {"id": "pilot-candidate", "reference_sha256": None},
        }
        with mock.patch.object(decision.preflight, "validate_manifest"), mock.patch.object(
            decision, "_load_json", return_value=pilot
        ):
            receipt = decision.compile_decision(ROOT / "package.json", None, ROOT)
        self.assertEqual("UNAVAILABLE", receipt["status"])
        self.assertEqual("candidate_not_frozen", receipt["reason_code"])
        self.assertEqual("decision-support-only-no-promotion", receipt["authority"])

    def test_artifact_hash_drift_and_symlink_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repo"
            evaluator = root / "evaluator"
            repository.mkdir()
            evaluator.mkdir()
            artifact = evaluator / "ledger.json"
            artifact.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(decision.V7PairedDecisionUnavailable, "artifact_binding_hash_drift"):
                decision._validate_bindings(
                    [{"id": "ledger", "path": str(artifact), "sha256": SHA_A}], repository
                )
            link = evaluator / "ledger-link.json"
            link.symlink_to(artifact)
            with self.assertRaisesRegex(decision.V7PairedDecisionUnavailable, "unsafe"):
                decision._validate_bindings(
                    [{"id": "ledger", "path": str(link), "sha256": decision._digest(artifact)}], repository
                )

    def test_binding_aliases_cannot_reuse_one_path_or_content_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repo"
            evaluator = root / "evaluator"
            repository.mkdir()
            evaluator.mkdir()
            bundle = _bundle()
            body = json.dumps(
                _receipt("development-decision", "development", bundle["development"], bundle),
                sort_keys=True,
            )
            first = evaluator / "first.json"
            second = evaluator / "second.json"
            first.write_text(body, encoding="utf-8")
            second.write_text(body, encoding="utf-8")
            sha256 = decision._digest(first)
            with self.assertRaisesRegex(
                decision.V7PairedDecisionUnavailable, "artifact_binding_evidence_reused"
            ):
                decision._validate_bindings(
                    [
                        {"id": "first", "path": str(first), "sha256": sha256},
                        {"id": "second", "path": str(first), "sha256": sha256},
                    ],
                    repository,
                )
            with self.assertRaisesRegex(
                decision.V7PairedDecisionUnavailable, "artifact_binding_evidence_reused"
            ):
                decision._validate_bindings(
                    [
                        {"id": "first", "path": str(first), "sha256": sha256},
                        {"id": "second", "path": str(second), "sha256": sha256},
                    ],
                    repository,
                )

    def test_receipt_is_write_once_and_cannot_enter_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repo"
            evaluator = root / "evaluator"
            repository.mkdir()
            evaluator.mkdir()
            receipt = {"schema_version": 1, "status": "UNAVAILABLE"}
            output = evaluator / "decision.json"
            decision._write_once(output, receipt, repository)
            self.assertEqual(receipt, json.loads(output.read_text(encoding="utf-8")))
            with self.assertRaisesRegex(decision.V7PairedDecisionError, "overwrite"):
                decision._write_once(output, receipt, repository)
            with self.assertRaisesRegex(decision.V7PairedDecisionError, "evaluator-owned"):
                decision._write_once(repository / "decision.json", receipt, repository)


if __name__ == "__main__":
    unittest.main()
