import copy
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from route_model import ProfileError, load_profile, route, validate_profile


def valid_profile():
    return {
        "schema_version": 1,
        "profile_id": "case-profile",
        "owner": "independent-evaluator",
        "provider": "provider",
        "model": "exact-model",
        "model_version": "2026-07-01",
        "evaluated_at": "2026-07-01",
        "valid_until": "2026-08-01",
        "skill_revision": "abc123",
        "cells": [{
            "task": "BUILD",
            "locale": "zh-Hant",
            "max_risk": "medium",
            "required_capabilities": ["write", "command", "browser"],
            "runs": 3,
            "contract_passes": 3,
            "invariant_passes": 3,
            "unsupported_claim_failures": 0,
            "independent_evaluation": True,
            "recommended_lane": "STANDARD",
        }],
    }


class RouteModelTests(unittest.TestCase):
    def test_routes_fresh_complete_profile_to_standard(self):
        profile = valid_profile()
        validate_profile(profile)
        lane, reasons, _ = route(
            profile, task="BUILD", locale="zh-Hant", risk="medium",
            capabilities={"write", "command", "browser"},
            as_of=date(2026, 7, 14), allow_exploratory=False,
        )
        self.assertEqual(lane, "STANDARD")
        self.assertIn("benchmark evidence", reasons[0])

    def test_missing_write_is_advisory(self):
        lane, _, _ = route(
            valid_profile(), task="BUILD", locale="zh-Hant", risk="low",
            capabilities={"read"}, as_of=date(2026, 7, 14),
            allow_exploratory=False,
        )
        self.assertEqual(lane, "ADVISORY")

    def test_failed_evidence_is_constrained(self):
        profile = valid_profile()
        profile["cells"][0]["unsupported_claim_failures"] = 1
        lane, reasons, _ = route(
            profile, task="BUILD", locale="zh-Hant", risk="medium",
            capabilities={"write", "command", "browser"},
            as_of=date(2026, 7, 14), allow_exploratory=False,
        )
        self.assertEqual(lane, "CONSTRAINED")
        self.assertTrue(any("unsupported" in reason for reason in reasons))

    def test_stale_profile_is_constrained(self):
        lane, reasons, _ = route(
            valid_profile(), task="RETROFIT", locale="zh-Hant", risk="low",
            capabilities={"write", "command", "browser"},
            as_of=date(2026, 9, 1), allow_exploratory=False,
        )
        self.assertEqual(lane, "CONSTRAINED")
        self.assertIn("stale", reasons[0])

    def test_exploratory_requires_caller_opt_in(self):
        profile = valid_profile()
        profile["cells"][0]["recommended_lane"] = "EXPLORATORY"
        lane, _, _ = route(
            profile, task="BUILD", locale="zh-Hant", risk="medium",
            capabilities={"write", "command", "browser"},
            as_of=date(2026, 7, 14), allow_exploratory=False,
        )
        self.assertEqual(lane, "STANDARD")

    def test_malformed_counts_fail_validation(self):
        profile = copy.deepcopy(valid_profile())
        profile["cells"][0]["runs"] = True
        with self.assertRaises(ProfileError):
            validate_profile(profile)

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
