#!/usr/bin/env python3
"""Tests for the bounded v7 source-layout advisory registry."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "evals" / "v7_supporting_probe_registry.py"
SPEC = importlib.util.spec_from_file_location("v7_supporting_probe_registry", MODULE)
assert SPEC and SPEC.loader
registry = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(registry)


def _finding(code: str, severity: str, line: int, evidence: str = "untrusted copy") -> dict:
    return {
        "code": code,
        "severity": severity,
        "path": "index.html",
        "line": line,
        "evidence": evidence,
        "confirmation": "untrusted confirmation",
    }


def _report(*findings: dict, truncated: bool = False) -> dict:
    return {
        "schema_version": 1,
        "status": "risks_found" if findings else "no_source_risks_observed",
        "claim_boundary": "Source risks only; rendered layout requires browser and screenshot evidence.",
        "scanned_files": 1,
        "scan_truncated": truncated,
        "finding_count": len(findings),
        "findings": list(findings),
    }


class V7SupportingProbeRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract, self.contract_sha = registry.load_contract(ROOT)
        self.subject = {"path": "index.html", "bytes": 10, "sha256": "a" * 64}

    def test_projects_only_high_allowlist_without_raw_source_data(self) -> None:
        value = registry.project_report(
            _report(
                _finding("forced_body_break", "medium", 3),
                _finding("prose_wrap_disabled", "high", 8, "secret product copy"),
                _finding("prose_wrap_disabled", "high", 4, "different secret"),
            ),
            self.contract,
            self.contract_sha,
            self.subject,
        )
        self.assertEqual("complete", value["coverage"]["status"])
        self.assertEqual(1, len(value["advisories"]))
        self.assertEqual(4, value["advisories"][0]["line"])
        serialized = json.dumps(value)
        self.assertNotIn("secret product copy", serialized)
        self.assertNotIn("confirmation", serialized)
        self.assertNotIn("selector", serialized)

    def test_unknown_or_truncated_report_is_unavailable_not_clean(self) -> None:
        cases = [
            _report(_finding("new_unknown_code", "high", 1)),
            _report(_finding("prose_wrap_disabled", "high", 1), truncated=True),
        ]
        for report in cases:
            with self.subTest(report=report):
                value = registry.project_report(report, self.contract, self.contract_sha, self.subject)
                self.assertEqual("unavailable", value["coverage"]["status"])
                self.assertEqual([], value["advisories"])

    def test_bool_counts_status_mismatch_and_malformed_text_fail_closed(self) -> None:
        cases = []
        bool_schema = _report(_finding("prose_wrap_disabled", "high", 1))
        bool_schema["schema_version"] = True
        cases.append(bool_schema)
        bool_scanned = _report(_finding("prose_wrap_disabled", "high", 1))
        bool_scanned["scanned_files"] = True
        cases.append(bool_scanned)
        bool_count = _report(_finding("prose_wrap_disabled", "high", 1))
        bool_count["finding_count"] = True
        cases.append(bool_count)
        contradictory = _report(_finding("prose_wrap_disabled", "high", 1))
        contradictory["status"] = "no_source_risks_observed"
        cases.append(contradictory)
        malformed_text = _report(_finding("prose_wrap_disabled", "high", 1))
        malformed_text["findings"][0]["evidence"] = {"raw": "copy"}
        cases.append(malformed_text)
        for report in cases:
            with self.subTest(report=report):
                value = registry.project_report(report, self.contract, self.contract_sha, self.subject)
                self.assertEqual("unavailable", value["coverage"]["status"])
                self.assertEqual([], value["advisories"])

    def test_actual_probe_and_registry_validation_bind_subject(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text(
                "<style>p { white-space: nowrap; }</style><p>copy</p>", encoding="utf-8"
            )
            value = registry.run_source_layout_probe(root, ROOT)
            feedback = registry.validate_registry(value, root, ROOT)
            self.assertEqual("complete", value["coverage"]["status"])
            self.assertIn("prose_wrap_disabled@index.html", feedback)
            self.assertIn("not rendered evidence", feedback)
            (root / "index.html").write_text("<p>changed</p>", encoding="utf-8")
            with self.assertRaisesRegex(registry.V7SupportingProbeError, "subject changed"):
                registry.validate_registry(value, root, ROOT)

    def test_execution_failure_is_explicitly_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text("<p>copy</p>", encoding="utf-8")

            def unavailable(*_args, **_kwargs):
                raise subprocess.TimeoutExpired(["probe"], 5)

            value = registry.run_source_layout_probe(root, ROOT, runner=unavailable)
            self.assertEqual("unavailable", value["coverage"]["status"])
            self.assertEqual("probe_execution_unavailable", value["coverage"]["reason_code"])
            self.assertEqual("", registry.validate_registry(value, root, ROOT))

    def test_probe_provenance_drift_after_execution_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text("<p>copy</p>", encoding="utf-8")
            original = registry.load_contract
            executed = False

            def completed(*_args, **_kwargs):
                nonlocal executed
                executed = True
                return subprocess.CompletedProcess(
                    ["probe"], 0, stdout=json.dumps(_report()), stderr=""
                )

            def drifting_contract(*args, **kwargs):
                if executed:
                    raise registry.V7SupportingProbeError("injected provenance drift")
                return original(*args, **kwargs)

            registry.load_contract = drifting_contract
            try:
                value = registry.run_source_layout_probe(root, ROOT, runner=completed)
            finally:
                registry.load_contract = original
            self.assertEqual("unavailable", value["coverage"]["status"])
            self.assertEqual("probe_provenance_drift", value["coverage"]["reason_code"])


if __name__ == "__main__":
    unittest.main()
