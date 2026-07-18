import copy
import json
import tempfile
import unittest
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wow-frontend-design" / "scripts"))

from route_model import (
    ProfileError,
    load_profile,
    route,
    runtime_mismatches,
    validate_profile,
)


def valid_profile():
    return {
        "schema_version": 2,
        "profile_id": "case-profile",
        "owner": "independent-evaluator",
        "provider": "provider",
        "model": "exact-model",
        "model_version": "2026-07-01",
        "adapter_revision": "agent-wrapper@1.2.3",
        "toolchain_revision": "tools-sha256",
        "evaluator_revision": "evaluator-sha256",
        "evaluated_at": "2026-07-01",
        "valid_until": "2026-08-01",
        "skill_revision": "abc123",
        "cells": [{
            "task": "BUILD",
            "locale": "zh-Hant",
            "surface": "product-ui",
            "max_risk": "medium",
            "required_capabilities": ["write", "command", "browser"],
            "attempts": 3,
            "eligible_runs": 3,
            "contract_passes": 3,
            "invariant_passes": 3,
            "unsupported_claim_failures": 0,
            "infrastructure_failures": 0,
            "independent_evaluation": True,
            "recommended_lane": "STANDARD",
        }],
    }


class RouteModelTests(unittest.TestCase):
    def test_routes_fresh_complete_profile_to_standard(self):
        profile = valid_profile()
        validate_profile(profile)
        lane, reasons, _ = route(
            profile, task="BUILD", locale="zh-Hant", surface="product-ui",
            risk="medium",
            capabilities={"write", "command", "browser"},
            as_of=date(2026, 7, 14), allow_exploratory=False,
        )
        self.assertEqual(lane, "STANDARD")
        self.assertIn("benchmark evidence", reasons[0])

    def test_missing_write_is_advisory(self):
        lane, _, _ = route(
            valid_profile(), task="BUILD", locale="zh-Hant", surface="product-ui",
            risk="low",
            capabilities={"read"}, as_of=date(2026, 7, 14),
            allow_exploratory=False,
        )
        self.assertEqual(lane, "ADVISORY")

    def test_failed_evidence_is_constrained(self):
        profile = valid_profile()
        profile["cells"][0]["unsupported_claim_failures"] = 1
        lane, reasons, _ = route(
            profile, task="BUILD", locale="zh-Hant", surface="product-ui",
            risk="medium",
            capabilities={"write", "command", "browser"},
            as_of=date(2026, 7, 14), allow_exploratory=False,
        )
        self.assertEqual(lane, "CONSTRAINED")
        self.assertTrue(any("unsupported" in reason for reason in reasons))

    def test_stale_profile_is_constrained(self):
        lane, reasons, _ = route(
            valid_profile(), task="RETROFIT", locale="zh-Hant", surface="product-ui",
            risk="low",
            capabilities={"write", "command", "browser"},
            as_of=date(2026, 9, 1), allow_exploratory=False,
        )
        self.assertEqual(lane, "CONSTRAINED")
        self.assertIn("stale", reasons[0])

    def test_exploratory_requires_caller_opt_in(self):
        profile = valid_profile()
        profile["cells"][0]["recommended_lane"] = "EXPLORATORY"
        lane, _, _ = route(
            profile, task="BUILD", locale="zh-Hant", surface="product-ui",
            risk="medium",
            capabilities={"write", "command", "browser"},
            as_of=date(2026, 7, 14), allow_exploratory=False,
        )
        self.assertEqual(lane, "STANDARD")

    def test_malformed_counts_fail_validation(self):
        profile = copy.deepcopy(valid_profile())
        profile["cells"][0]["eligible_runs"] = True
        with self.assertRaises(ProfileError):
            validate_profile(profile)

    def test_infrastructure_failures_do_not_count_as_eligible_runs(self):
        profile = valid_profile()
        profile["cells"][0].update(
            attempts=4,
            eligible_runs=2,
            infrastructure_failures=2,
            contract_passes=2,
            invariant_passes=2,
        )
        validate_profile(profile)
        lane, reasons, _ = route(
            profile, task="BUILD", locale="zh-Hant", surface="product-ui",
            risk="medium", capabilities={"write", "command", "browser"},
            as_of=date(2026, 7, 14), allow_exploratory=False,
        )
        self.assertEqual(lane, "CONSTRAINED")
        self.assertTrue(any("eligible" in reason for reason in reasons))

    def test_surface_mismatch_does_not_reuse_unrelated_evidence(self):
        lane, reasons, cell = route(
            valid_profile(), task="BUILD", locale="zh-Hant", surface="marketing",
            risk="medium", capabilities={"write", "command", "browser"},
            as_of=date(2026, 7, 14), allow_exploratory=False,
        )
        self.assertEqual(lane, "CONSTRAINED")
        self.assertIsNone(cell)
        self.assertTrue(any("matching" in reason for reason in reasons))

    def test_profile_rejects_unexpected_fields(self):
        profile = valid_profile()
        profile["self_reported_tier"] = "strong"
        with self.assertRaisesRegex(ProfileError, "unexpected"):
            validate_profile(profile)

    def test_duplicate_capabilities_are_rejected(self):
        profile = valid_profile()
        profile["cells"][0]["required_capabilities"].append("browser")
        with self.assertRaisesRegex(ProfileError, "unique"):
            validate_profile(profile)

    def test_runtime_revision_mismatch_is_detected(self):
        profile = valid_profile()
        runtime = {key: profile[key] for key in (
            "provider", "model", "model_version", "skill_revision",
            "adapter_revision", "toolchain_revision", "evaluator_revision",
        )}
        self.assertEqual([], runtime_mismatches(profile, runtime))
        runtime["adapter_revision"] = "changed-wrapper"
        self.assertEqual(["adapter_revision"], runtime_mismatches(profile, runtime))

    def test_symlink_profile_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real.json"
            real.write_text(json.dumps(valid_profile()), encoding="utf-8")
            link = root / "profile.json"
            link.symlink_to(real)
            with self.assertRaises(ProfileError):
                load_profile(link)


if __name__ == "__main__":
    unittest.main()
