#!/usr/bin/env python3
"""Tests for runtime_downgrade.py."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wow-frontend-design" / "scripts"))

from runtime_downgrade import (
    RuntimeDowngradeError,
    _load,
    apply_events,
    cap_lane,
    validate,
)


def payload(initial_lane="STANDARD", events=None, max_mutation_attempts=3):
    return {
        "schema_version": 2,
        "run_id": "case-run",
        "initial_lane": initial_lane,
        "max_mutation_attempts": max_mutation_attempts,
        "events": events or [],
    }


def event(
    sequence,
    code,
    consecutive=1,
    progress=False,
    failure_key=None,
    mutation_attempts_used=1,
):
    return {
        "sequence": sequence,
        "code": code,
        "failure_key": failure_key or code.lower().replace("_", "-"),
        "consecutive": consecutive,
        "progress_observed": progress,
        "mutation_attempts_used": mutation_attempts_used,
    }


class RuntimeDowngradeTests(unittest.TestCase):
    def test_packaged_example_matches_schema_v2(self):
        example = json.loads(
            (ROOT / "wow-frontend-design" / "scripts" / "runtime_events.example.json").read_text(
                encoding="utf-8"
            )
        )
        validate(example)
        self.assertEqual(2, apply_events(example)["schema_version"])

    def test_cap_lane_never_promotes(self):
        self.assertEqual("CONSTRAINED", cap_lane("CONSTRAINED", "STANDARD"))
        self.assertEqual("STANDARD", cap_lane("EXPLORATORY", "STANDARD"))

    def test_progress_extends_timeout_without_downgrade(self):
        result = apply_events(payload(events=[
            event(1, "INACTIVITY_TIMEOUT", progress=True),
        ]))
        self.assertEqual("STANDARD", result["final_lane"])
        self.assertEqual("EXTEND_TIMEOUT", result["transitions"][0]["action"])

    def test_inactive_timeout_retries_before_fuse(self):
        result = apply_events(payload(events=[
            event(1, "INACTIVITY_TIMEOUT"),
        ]))
        self.assertEqual("STANDARD", result["final_lane"])
        self.assertEqual("RETRY", result["transitions"][0]["action"])

    def test_same_repair_finding_retries_then_hands_off_best(self):
        result = apply_events(payload(initial_lane="EXPLORATORY", events=[
            event(1, "REPAIR_FINDING", 1),
            event(2, "REPAIR_FINDING", 2),
            event(3, "REPAIR_FINDING", 3),
        ]))
        self.assertEqual("CONSTRAINED", result["final_lane"])
        self.assertEqual("REPAIR_AND_RECHECK", result["transitions"][1]["action"])
        self.assertEqual("HAND_OFF_BEST", result["transitions"][2]["action"])
        self.assertFalse(result["automatic_upgrade_permitted"])

    def test_contract_failure_caps_lane_and_continues(self):
        result = apply_events(payload(initial_lane="EXPLORATORY", events=[
            event(1, "OUTPUT_CONTRACT_FAILED"),
        ]))
        self.assertEqual("CONSTRAINED", result["final_lane"])
        self.assertEqual("NARROW_AND_CONTINUE", result["transitions"][0]["action"])

    def test_third_transient_tool_failure_hands_off_best(self):
        result = apply_events(payload(events=[
            event(1, "TRANSIENT_TOOL_FAILURE", 1),
            event(2, "TRANSIENT_TOOL_FAILURE", 2),
            event(3, "TRANSIENT_TOOL_FAILURE", 3),
        ]))
        self.assertEqual("CONSTRAINED", result["final_lane"])
        self.assertEqual("HAND_OFF_BEST", result["transitions"][2]["action"])

    def test_immediate_downgrade_policies(self):
        cases = {
            "PRESERVE_INVARIANT_FAILED": ("CONSTRAINED", "RESTORE_AND_RECHECK"),
            "UNSUPPORTED_CLAIM": ("CONSTRAINED", "REMOVE_CLAIM_AND_RECHECK"),
            "VERIFICATION_CAPABILITY_MISSING": ("CONSTRAINED", "CONTINUE_WITH_UNVERIFIED_GATE"),
            "EVALUATOR_BOUNDARY_VIOLATION": ("CONSTRAINED", "RESTART_ISOLATED"),
            "SECURITY_PERMISSION_BLOCK": ("ADVISORY", "STOP_MUTATION"),
        }
        for code, (lane, action) in cases.items():
            with self.subTest(code=code):
                result = apply_events(payload(initial_lane="EXPLORATORY", events=[event(1, code)]))
                self.assertEqual(lane, result["final_lane"])
                self.assertEqual(action, result["transitions"][0]["action"])

    def test_missing_mutation_capability_becomes_advisory(self):
        result = apply_events(payload(events=[
            event(1, "MUTATION_CAPABILITY_MISSING"),
        ]))
        self.assertEqual("ADVISORY", result["final_lane"])
        self.assertEqual("STOP_MUTATION", result["transitions"][0]["action"])

    def test_inconsistent_consecutive_count_is_rejected(self):
        data = payload(events=[
            event(1, "TRANSIENT_TOOL_FAILURE", 1),
            event(2, "TRANSIENT_TOOL_FAILURE", 3),
        ])
        with self.assertRaisesRegex(RuntimeDowngradeError, "consecutive"):
            validate(data)

    def test_different_repair_findings_do_not_share_a_fuse(self):
        result = apply_events(payload(events=[
            event(1, "REPAIR_FINDING", failure_key="layout:route-a"),
            event(2, "REPAIR_FINDING", failure_key="layout:route-b"),
        ]))
        self.assertEqual("STANDARD", result["final_lane"])
        self.assertEqual([1, 1], [item["consecutive"] for item in result["transitions"]])

    def test_interleaved_failure_keys_do_not_reset_global_mutation_budget(self):
        result = apply_events(payload(events=[
            event(1, "REPAIR_FINDING", 1, failure_key="layout:route-a", mutation_attempts_used=1),
            event(2, "REPAIR_FINDING", 1, failure_key="layout:route-b", mutation_attempts_used=2),
            event(3, "REPAIR_FINDING", 1, failure_key="layout:route-a", mutation_attempts_used=3),
        ]))
        self.assertEqual("CONSTRAINED", result["final_lane"])
        self.assertEqual("HAND_OFF_BEST", result["transitions"][-1]["action"])
        self.assertIn("global mutation budget", result["transitions"][-1]["reason"])

    def test_mutation_attempt_count_must_be_monotonic_and_within_budget(self):
        cases = (
            [event(1, "REPAIR_FINDING", mutation_attempts_used=2),
             event(2, "REPAIR_FINDING", 2, mutation_attempts_used=1)],
            [event(1, "REPAIR_FINDING", mutation_attempts_used=4)],
        )
        for events in cases:
            with self.subTest(events=events), self.assertRaisesRegex(
                RuntimeDowngradeError, "mutation_attempts_used"
            ):
                validate(payload(events=events))

    def test_mutation_budget_cannot_exceed_canonical_limit(self):
        for maximum in (0, 4, True):
            with self.subTest(maximum=maximum), self.assertRaisesRegex(
                RuntimeDowngradeError, "max_mutation_attempts"
            ):
                validate(payload(max_mutation_attempts=maximum))

    def test_mutating_contract_action_hands_off_when_budget_is_exhausted(self):
        result = apply_events(payload(events=[
            event(1, "OUTPUT_CONTRACT_FAILED", mutation_attempts_used=3),
        ]))
        self.assertEqual("CONSTRAINED", result["final_lane"])
        self.assertEqual("HAND_OFF_BEST", result["transitions"][0]["action"])

    def test_progress_extension_does_not_consume_timeout_streak(self):
        result = apply_events(payload(events=[
            event(1, "INACTIVITY_TIMEOUT", 1, progress=True, failure_key="generation:case-a"),
            event(2, "INACTIVITY_TIMEOUT", 1, failure_key="generation:case-a"),
            event(3, "INACTIVITY_TIMEOUT", 2, failure_key="generation:case-a"),
        ]))
        self.assertEqual("STANDARD", result["final_lane"])
        self.assertEqual("RETRY", result["transitions"][-1]["action"])

    def test_progress_signal_is_timeout_only(self):
        with self.assertRaisesRegex(RuntimeDowngradeError, "only valid"):
            validate(payload(events=[event(1, "REPAIR_FINDING", progress=True)]))

    def test_symlink_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real.json"
            real.write_text(json.dumps(payload()), encoding="utf-8")
            link = root / "events.json"
            link.symlink_to(real)
            with self.assertRaises(RuntimeDowngradeError):
                _load(link)


if __name__ == "__main__":
    unittest.main()
