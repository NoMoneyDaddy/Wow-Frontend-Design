#!/usr/bin/env python3
"""Synthetic tests for the v7 affected selector and artifact ratchet."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "evals" / "v7_repair_policy.py"
SPEC = importlib.util.spec_from_file_location("v7_repair_policy", MODULE)
assert SPEC and SPEC.loader
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)


def _receipt(design: str, index: str) -> dict:
    return {"outputs": [
        {"path": "DESIGN.md", "bytes": 1, "sha256": design * 64},
        {"path": "index.html", "bytes": 1, "sha256": index * 64},
    ]}


def _target(classification: str = "composition", code: str = "a1_prose_han_orphan") -> dict:
    return {
        "variant": "candidate",
        "case_id": "case-one",
        "occurrences": [{
            "state": "base",
            "profile": "mobile",
            "engine": "chromium",
            "findings": [{"classification": classification, "code": code, "locator": "copy"}],
        }],
    }


class V7RepairPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = [
            ("candidate", "case-one", state, profile, engine)
            for state, profile, engine in (
                ("base", "desktop", "chromium"),
                ("base", "mobile", "chromium"),
                ("interaction", "desktop", "firefox"),
            )
        ] + [("baseline", "case-two", "base", "mobile", "chromium")]

    def test_rendered_diff_selects_complete_target_matrix_and_keeps_original_row(self) -> None:
        result = policy.select_affected_rows(
            _target(), _receipt("a", "b"), _receipt("c", "d"), self.inventory,
            target_isolated=True, support_contract_sha256="e" * 64,
        )
        self.assertEqual("target-full-matrix", result["decision"])
        self.assertEqual(3, len(result["selected_rows"]))
        self.assertIn(["candidate", "case-one", "base", "mobile", "chromium"], result["selected_rows"])

    def test_document_only_diff_reruns_original_failure_rows(self) -> None:
        result = policy.select_affected_rows(
            _target(), _receipt("a", "b"), _receipt("c", "b"), self.inventory,
            target_isolated=True, support_contract_sha256="e" * 64,
        )
        self.assertEqual("original-failure-rows", result["decision"])
        self.assertEqual(result["original_failure_rows"], result["selected_rows"])

    def test_unknown_issue_or_unproven_isolation_falls_back_to_full_cohort(self) -> None:
        unknown = _target("unknown")
        first = policy.select_affected_rows(
            unknown, _receipt("a", "b"), _receipt("c", "d"), self.inventory,
            target_isolated=True, support_contract_sha256="e" * 64,
        )
        second = policy.select_affected_rows(
            _target(), _receipt("a", "b"), _receipt("c", "d"), self.inventory, target_isolated=False
        )
        self.assertEqual("cohort-full-matrix", first["decision"])
        self.assertEqual("unknown-issue-class", first["fallback_reason"])
        self.assertEqual("cohort-full-matrix", second["decision"])
        self.assertEqual(len(self.inventory), len(second["selected_rows"]))

    def test_isolation_claim_without_frozen_contract_is_rejected(self) -> None:
        with self.assertRaisesRegex(policy.V7RepairPolicyError, "support contract"):
            policy.select_affected_rows(
                _target(), _receipt("a", "b"), _receipt("c", "d"), self.inventory,
                target_isolated=True,
            )

    def test_repository_support_contract_is_bound_to_capture_and_auditor_bytes(self) -> None:
        digest = policy.validate_support_contract(
            ROOT / "evals" / "v7-repair-support-contract.json",
            ROOT,
        )
        self.assertEqual(64, len(digest))

    def test_rank_rejects_new_core_regression_even_when_composition_count_falls(self) -> None:
        baseline = _target()
        baseline["occurrences"][0]["findings"].extend([
            {"classification": "composition", "code": f"composition-{number}", "locator": "copy"}
            for number in range(5)
        ])
        regressed = _target("runtime", "page_errors")
        baseline_rank = policy.artifact_rank(baseline, baseline, changed_bytes=0, artifact_sha256="a" * 64)
        regressed_rank = policy.artifact_rank(baseline, regressed, changed_bytes=1, artifact_sha256="b" * 64)
        clean_rank = policy.artifact_rank(baseline, None, changed_bytes=2, artifact_sha256="c" * 64)
        self.assertGreater(regressed_rank, baseline_rank)
        self.assertLess(clean_rank, baseline_rank)

    def test_rank_improvement_is_decided_before_cost_or_hash(self) -> None:
        baseline = _target("interaction", "interaction_assertion_failed")
        improved = _target("composition", "a1_prose_han_orphan")
        baseline_rank = policy.artifact_rank(baseline, baseline, changed_bytes=0, artifact_sha256="a" * 64)
        improved_rank = policy.artifact_rank(baseline, improved, changed_bytes=99999, artifact_sha256="f" * 64)
        self.assertLess(improved_rank, baseline_rank)
        self.assertTrue(policy.is_strict_improvement(improved_rank, baseline_rank))

    def test_digest_tie_break_cannot_promote_equal_quality(self) -> None:
        target = _target()
        incumbent = policy.artifact_rank(target, target, changed_bytes=0, artifact_sha256="f" * 64)
        arbitrary_digest_winner = policy.artifact_rank(target, target, changed_bytes=0, artifact_sha256="a" * 64)
        self.assertLess(arbitrary_digest_winner, incumbent)
        self.assertFalse(policy.is_strict_improvement(arbitrary_digest_winner, incumbent))

    def test_smaller_changed_surface_cannot_promote_equal_quality(self) -> None:
        target = _target()
        incumbent = policy.artifact_rank(target, target, changed_bytes=500, artifact_sha256="f" * 64)
        smaller = policy.artifact_rank(target, target, changed_bytes=1, artifact_sha256="a" * 64)
        self.assertLess(smaller, incumbent)
        self.assertFalse(policy.is_strict_improvement(smaller, incumbent))


if __name__ == "__main__":
    unittest.main()
