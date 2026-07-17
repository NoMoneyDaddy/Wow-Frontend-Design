#!/usr/bin/env python3
"""Tests for validate_quality_result.py."""

from __future__ import annotations

import base64
import copy
import contextlib
import io
import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_quality_result
import evidence_ledger


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def fake_png(width: int, height: int) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    pixels = b"".join(b"\x00" + (b"\x00" * width) for _ in range(height))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b"")
NOVEL_DISCOVERY_REPORT = {
    "schema_version": 1,
    "status": "clean_after_probes",
    "probes": [
        {
            "id": "probe-default-mobile",
            "route": "/",
            "viewport": "390x844",
            "state": "default",
            "method": "Playwright DOM and screenshot replay",
            "outcome": "pass",
            "evidence": ["mobile.png", "interaction-log"],
        }
    ],
    "findings": [],
}


class QualityResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parent
        cls.example_path = cls.root / "quality_result.example.json"
        cls.example = json.loads(cls.example_path.read_text(encoding="utf-8"))

    def test_repository_example_is_valid(self) -> None:
        self.assertEqual(validate_quality_result.validate(self.example_path), 3)

    def test_checked_in_examples_are_strictly_compatible(self) -> None:
        policy_template = json.loads(
            (self.root / "evidence_policy.example.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            ledger = root / "ledger.json"
            policy_path = root / "policy.json"
            result_path = workspace / "result.json"
            policy = copy.deepcopy(policy_template)
            policy["case_id"] = "quality-example"
            policy["run_id"] = "quality-example-run-001"
            self.assertEqual(
                evidence_ledger.main(
                    [
                        "init",
                        "--ledger",
                        str(ledger),
                        "--case-id",
                        policy["case_id"],
                        "--run-id",
                        policy["run_id"],
                    ]
                ),
                0,
            )
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                for label, rule in policy["evidence"].items():
                    if rule["kind"] == "command":
                        command = [
                            sys.executable,
                            "-c",
                            f"raise SystemExit(0)  # checked-in-example:{label}",
                        ]
                        rule["command"] = command
                        rule["command_sha256"] = evidence_ledger.canonical_command_sha256(command)
                        self.assertEqual(
                            evidence_ledger.main(
                                [
                                    "run",
                                    "--ledger",
                                    str(ledger),
                                    "--label",
                                    label,
                                    "--cwd",
                                    str(workspace),
                                    "--",
                                    *command,
                                ]
                            ),
                            0,
                        )
                        continue

                    artifact = root / rule["path"]
                    artifact.parent.mkdir(parents=True, exist_ok=True)
                    if rule["artifact_kind"] == "screenshot":
                        width, height = (int(value) for value in rule["context"]["viewport"].split("x", 1))
                        artifact.write_bytes(fake_png(width, height))
                    else:
                        artifact.write_bytes(json.dumps(NOVEL_DISCOVERY_REPORT).encode("utf-8"))
                    artifact_args = [
                        "artifact",
                        "--ledger",
                        str(ledger),
                        "--label",
                        label,
                        "--kind",
                        rule["artifact_kind"],
                        "--path",
                        str(artifact),
                    ]
                    context = rule.get("context", {})
                    for field, flag in (
                        ("route", "--route"),
                        ("viewport", "--viewport"),
                        ("locale", "--locale"),
                        ("state", "--state"),
                        ("note", "--context"),
                    ):
                        if field in context:
                            artifact_args.extend([flag, context[field]])
                    self.assertEqual(evidence_ledger.main(artifact_args), 0)

            result = copy.deepcopy(self.example)
            self.assertEqual(result["release"], "PARTIALLY_VERIFIED")
            self.assertEqual(policy["release_acceptance"]["decision"], "not_accepted")
            result_path.write_text(json.dumps(result), encoding="utf-8")
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            self.assertEqual(
                validate_quality_result.validate_with_ledger(
                    result_path,
                    ledger,
                    workspace,
                    ("novel-discovery",),
                    policy_path,
                ),
                3,
            )

    def _strict_fixture(self, root: Path) -> tuple[Path, Path, Path, Path]:
        workspace = root / "workspace"
        workspace.mkdir()
        ledger = root / "ledger.json"
        policy_path = root / "policy.json"
        self.assertEqual(
            evidence_ledger.main(
                ["init", "--ledger", str(ledger), "--case-id", "quality-case", "--run-id", "quality-run-001"]
            ),
            0,
        )
        result = copy.deepcopy(self.example)
        result["release"] = "VERIFIED"
        gate_labels = ["primary-task", "rendered-mobile-layout", "novel-discovery"]
        command_labels = gate_labels[:2]
        self.assertEqual(len(result["hard_gates"]), len(gate_labels))
        for gate, label in zip(result["hard_gates"], gate_labels):
            gate["evidence"] = [label]
        result["coverage"] = {
            "required_applicable": 3,
            "required_passed": 3,
            "evidence_items": 3,
        }
        for dimension in result["craft"]["dimensions"]:
            dimension["status"] = "UNVERIFIED"
            dimension["evidence"] = []
        result["handoff"]["rendered_evidence"] = {
            "status": "OBSERVED",
            "paths": ["mobile.png"],
            "reason": "",
        }
        result_path = workspace / "result.json"
        result_path.write_text(json.dumps(result), encoding="utf-8")
        commands = {
            label: [sys.executable, "-c", f"raise SystemExit(0)  # {label}"]
            for label in command_labels
        }
        for label, command in commands.items():
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(
                    evidence_ledger.main(
                        [
                            "run",
                            "--ledger",
                            str(ledger),
                            "--label",
                            label,
                            "--cwd",
                            str(workspace),
                            "--",
                            *command,
                        ]
                    ),
                    0,
                )
        screenshot = root / "mobile.png"
        screenshot.write_bytes(fake_png(390, 844))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(
                evidence_ledger.main(
                    [
                        "artifact",
                        "--ledger",
                        str(ledger),
                        "--label",
                        "rendered-mobile",
                        "--kind",
                        "screenshot",
                        "--path",
                        str(screenshot),
                        "--route",
                        "/",
                        "--viewport",
                        "390x844",
                        "--context",
                        "dpr=1",
                        "--locale",
                        "zh-Hant",
                        "--state",
                        "default",
                    ]
                ),
                0,
            )
        evidence = {
            label: {
                "kind": "command",
                "claim_types": [f"gate:{gate['id']}"],
                "command": commands[label],
                "command_sha256": evidence_ledger.canonical_command_sha256(commands[label]),
                "cwd": "workspace",
            }
            for gate, label in zip(result["hard_gates"][:2], command_labels)
        }
        novel_report = root / "novel-findings.json"
        novel_report.write_text(json.dumps(NOVEL_DISCOVERY_REPORT), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(
                evidence_ledger.main(
                    [
                        "artifact",
                        "--ledger",
                        str(ledger),
                        "--label",
                        "novel-discovery",
                        "--kind",
                        "report",
                        "--path",
                        str(novel_report),
                    ]
                ),
                0,
            )
        evidence["novel-discovery"] = {
            "kind": "artifact",
            "claim_types": ["gate:novel-discovery"],
            "artifact_kind": "report",
            "path": "novel-findings.json",
        }
        evidence["rendered-mobile"] = {
            "kind": "artifact",
            "claim_types": ["rendered_visual"],
            "artifact_kind": "screenshot",
            "path": "mobile.png",
            "context": {
                "route": "/",
                "viewport": "390x844",
                "locale": "zh-Hant",
                "state": "default",
                "note": "dpr=1",
            },
        }
        policy = {
            "schema_version": 3,
            "case_id": "quality-case",
            "run_id": "quality-run-001",
            "trust_boundary": {
                "evaluator_owned": True,
                "outside_model_write_scope": True,
                "integrity": "unsigned",
                "note": "Unit-test policy stored outside the model-writable workspace.",
            },
            "release_acceptance": {
                "decision": "accepted_by_evaluator",
                "evaluator": "quality-test-evaluator",
                "record": "fixture-acceptance",
                "reason": "Fixture exercises exact policy and evidence binding.",
            },
            "evidence": evidence,
        }
        policy_path.write_text(json.dumps(policy), encoding="utf-8")
        return result_path, ledger, policy_path, workspace

    def test_strict_validation_binds_passes_and_discovery_to_evaluator_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result, ledger, policy, workspace = self._strict_fixture(Path(directory))
            self.assertEqual(
                validate_quality_result.validate_with_ledger(
                    result,
                    ledger,
                    workspace,
                    ("novel-discovery",),
                    policy,
                ),
                3,
            )

    def test_strict_validation_rejects_one_by_one_screenshot_for_viewport_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result, ledger, policy, workspace = self._strict_fixture(Path(directory))
            screenshot = Path(directory) / "mobile.png"
            screenshot.write_bytes(PNG_1X1)
            ledger_data = evidence_ledger.load_ledger(ledger)
            event = next(item for item in ledger_data["events"] if item["label"] == "rendered-mobile")
            event["bytes"] = len(PNG_1X1)
            event["sha256"] = evidence_ledger.sha256_bytes(PNG_1X1)
            event["width"] = 1
            event["height"] = 1
            evidence_ledger.save_ledger(ledger, ledger_data)
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "dimensions disagree with viewport/scale"):
                validate_quality_result.validate_with_ledger(
                    result,
                    ledger,
                    workspace,
                    ("novel-discovery",),
                    policy,
                )

    def test_novel_discovery_report_rejects_empty_and_unconfirmed_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "novel.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "must contain schema_version"):
                validate_quality_result._validate_novel_discovery_report(path)
            invalid = copy.deepcopy(NOVEL_DISCOVERY_REPORT)
            invalid["status"] = "findings"
            invalid["findings"] = [{
                "id": "novel:form:submit:stale-success",
                "status": "confirmed",
                "severity": "P1",
                "surface": "form",
                "state": "submit",
                "route": "/",
                "viewport": "390x844",
                "reproduction": "submit twice",
                "expected": "one result",
                "actual": "two results",
                "owner": "frontend",
                "confirmation": {"replays": 1, "evidence": ["replay-1"]},
            }]
            path.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "replays is insufficient"):
                validate_quality_result._validate_novel_discovery_report(path)
            blocked = copy.deepcopy(NOVEL_DISCOVERY_REPORT)
            blocked["probes"][0]["outcome"] = "blocked"
            path.write_text(json.dumps(blocked), encoding="utf-8")
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "every probe to pass"):
                validate_quality_result._validate_novel_discovery_report(path)
            empty_evidence = copy.deepcopy(NOVEL_DISCOVERY_REPORT)
            empty_evidence["probes"][0]["evidence"] = []
            path.write_text(json.dumps(empty_evidence), encoding="utf-8")
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "at least one evaluator observation"):
                validate_quality_result._validate_novel_discovery_report(path)

    def test_novel_discovery_cannot_use_a_command_as_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result, ledger, policy_path, workspace = self._strict_fixture(Path(directory))
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["evidence"]["novel-discovery"] = {
                "kind": "command",
                "claim_types": ["gate:novel-discovery"],
                "command": [sys.executable, "-c", "raise SystemExit(0)"],
                "command_sha256": evidence_ledger.canonical_command_sha256([sys.executable, "-c", "raise SystemExit(0)"]),
                "cwd": "workspace",
            }
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "must use an evaluator-bound report"):
                validate_quality_result.validate_with_ledger(
                    result,
                    ledger,
                    workspace,
                    ("novel-discovery",),
                    policy_path,
                )

    def test_verified_release_requires_novel_discovery_without_caller_flag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result, ledger, policy, workspace = self._strict_fixture(Path(directory))
            data = json.loads(result.read_text(encoding="utf-8"))
            data["hard_gates"] = data["hard_gates"][:-1]
            data["coverage"] = {
                "required_applicable": 2,
                "required_passed": 2,
                "evidence_items": 2,
            }
            result.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "novel-discovery"):
                validate_quality_result.validate_with_ledger(
                    result,
                    ledger,
                    workspace,
                    policy_path=policy,
                )

    def test_strict_validation_uses_latest_repair_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result, ledger, policy, workspace = self._strict_fixture(Path(directory))
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(
                    evidence_ledger.main(
                        [
                            "run",
                            "--ledger",
                            str(ledger),
                            "--label",
                            "primary-task",
                            "--cwd",
                            str(workspace),
                            "--",
                            sys.executable,
                            "-c",
                            "raise SystemExit(7)",
                        ]
                    ),
                    7,
                )
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "command failed"):
                validate_quality_result.validate_with_ledger(
                    result,
                    ledger,
                    workspace,
                    ("novel-discovery",),
                    policy,
                )

    def test_strict_validation_rejects_wrong_successful_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result, ledger, policy, workspace = self._strict_fixture(Path(directory))
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(
                    evidence_ledger.main(
                        [
                            "run",
                            "--ledger",
                            str(ledger),
                            "--label",
                            "primary-task",
                            "--cwd",
                            str(workspace),
                            "--",
                            sys.executable,
                            "-c",
                            "raise SystemExit(0)  # not-the-approved-test",
                        ]
                    ),
                    0,
                )
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "does not match policy"):
                validate_quality_result.validate_with_ledger(
                    result,
                    ledger,
                    workspace,
                    ("novel-discovery",),
                    policy,
                )

    def test_strict_validation_rejects_unbound_or_workspace_owned_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result, ledger, policy, workspace = self._strict_fixture(root)
            data = json.loads(result.read_text(encoding="utf-8"))
            data["hard_gates"][0]["evidence"] = ["not-recorded"]
            result.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "not unambiguously"):
                validate_quality_result.validate_with_ledger(
                    result,
                    ledger,
                    workspace,
                    ("novel-discovery",),
                    policy,
                )
            forged = workspace / "ledger.json"
            forged.write_bytes(ledger.read_bytes())
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "outside"):
                validate_quality_result.validate_with_ledger(
                    result,
                    forged,
                    workspace,
                    ("novel-discovery",),
                    policy,
                )

    def test_strict_validation_requires_policy_claim_and_evaluator_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result, ledger, policy_path, workspace = self._strict_fixture(Path(directory))
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "requires an evaluator-owned"):
                validate_quality_result.validate_with_ledger(
                    result,
                    ledger,
                    workspace,
                    ("novel-discovery",),
                )

            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["release_acceptance"] = {
                "decision": "not_accepted",
                "reason": "Independent acceptance is intentionally absent.",
            }
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "evaluator acceptance"):
                validate_quality_result.validate_with_ledger(
                    result,
                    ledger,
                    workspace,
                    ("novel-discovery",),
                    policy_path,
                )

            policy["release_acceptance"] = {
                "decision": "accepted_by_evaluator",
                "evaluator": "quality-test-evaluator",
                "record": "fixture-acceptance",
                "reason": "Fixture exercises exact policy and evidence binding.",
            }
            policy["evidence"]["novel-discovery"]["claim_types"] = ["gate:primary-task"]
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "cannot prove claim_type"):
                validate_quality_result.validate_with_ledger(
                    result,
                    ledger,
                    workspace,
                    ("novel-discovery",),
                    policy_path,
                )

    def test_strict_validation_rechecks_rendered_artifact_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result, ledger, policy, workspace = self._strict_fixture(root)
            (root / "mobile.png").write_bytes(PNG_1X1 + b"tampered")
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "artifact is invalid"):
                validate_quality_result.validate_with_ledger(
                    result,
                    ledger,
                    workspace,
                    ("novel-discovery",),
                    policy,
                )

    def test_rendered_path_cannot_resolve_to_a_command_label(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result, ledger, policy_path, workspace = self._strict_fixture(Path(directory))
            data = json.loads(result.read_text(encoding="utf-8"))
            data["handoff"]["rendered_evidence"]["paths"] = ["primary-task"]
            result.write_text(json.dumps(data), encoding="utf-8")
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["evidence"]["primary-task"]["claim_types"].append("rendered_visual")
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "must be an approved artifact"):
                validate_quality_result.validate_with_ledger(
                    result,
                    ledger,
                    workspace,
                    ("novel-discovery",),
                    policy_path,
                )

    def test_rendered_paths_cannot_use_an_artifact_label_alias(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result, ledger, policy, workspace = self._strict_fixture(Path(directory))
            data = json.loads(result.read_text(encoding="utf-8"))
            data["handoff"]["rendered_evidence"]["paths"] = ["rendered-mobile"]
            result.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "approved artifact path"):
                validate_quality_result.validate_with_ledger(
                    result,
                    ledger,
                    workspace,
                    policy_path=policy,
                )

    def test_cli_requires_explicit_structure_only_or_bound_evidence(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(validate_quality_result.main([str(self.example_path)]), 1)
            self.assertEqual(
                validate_quality_result.main([str(self.example_path), "--structure-only"]),
                0,
            )

    def test_cli_accepts_fully_bound_completion_and_rejects_legacy_evidence_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result, ledger, policy, workspace = self._strict_fixture(Path(directory))
            common = [
                str(result),
                "--ledger",
                str(ledger),
                "--workspace-root",
                str(workspace),
                "--require-gate",
                "novel-discovery",
            ]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(
                    validate_quality_result.main(
                        [*common, "--policy", str(policy)]
                    ),
                    0,
                )
                self.assertEqual(validate_quality_result.main(common), 1)

    def test_required_failure_makes_eligible_false_and_total_null(self) -> None:
        result = copy.deepcopy(self.example)
        result["hard_gates"][0]["status"] = "FAIL"
        result["hard_gates"][0]["evidence"] = ["failure.json"]
        result["eligible"] = False
        result["coverage"]["required_passed"] = 2
        result["release"] = "PARTIALLY_VERIFIED"
        self.assertEqual(validate_quality_result.validate_data(result), 3)

    def test_ineligible_result_cannot_claim_verified(self) -> None:
        result = copy.deepcopy(self.example)
        result["release"] = "VERIFIED"
        result["hard_gates"][0]["status"] = "UNVERIFIED"
        result["hard_gates"][0]["evidence"] = []
        result["eligible"] = False
        result["coverage"]["required_passed"] = 2
        result["coverage"]["evidence_items"] = 3
        with self.assertRaisesRegex(validate_quality_result.QualityResultError, "release cannot"):
            validate_quality_result.validate_data(result)

    def test_weighted_total_is_rejected(self) -> None:
        result = copy.deepcopy(self.example)
        result["weighted_total"] = 94
        with self.assertRaisesRegex(validate_quality_result.QualityResultError, "weighted_total"):
            validate_quality_result.validate_data(result)

    def test_builder_cannot_self_certify_craft(self) -> None:
        result = copy.deepcopy(self.example)
        result["craft"]["independent"] = False
        result["craft"]["evaluator_id"] = ""
        with self.assertRaisesRegex(validate_quality_result.QualityResultError, "independent evaluator"):
            validate_quality_result.validate_data(result)

    def test_unverified_rendering_requires_reason(self) -> None:
        result = copy.deepcopy(self.example)
        result["handoff"]["rendered_evidence"] = {
            "status": "UNVERIFIED",
            "paths": [],
            "reason": "",
        }
        with self.assertRaisesRegex(validate_quality_result.QualityResultError, "requires a reason"):
            validate_quality_result.validate_data(result)

    def test_verified_release_requires_observed_rendering(self) -> None:
        result = copy.deepcopy(self.example)
        result["release"] = "VERIFIED"
        result["handoff"]["rendered_evidence"] = {
            "status": "UNVERIFIED",
            "paths": [],
            "reason": "No rendered browser evidence was captured.",
        }
        with self.assertRaisesRegex(validate_quality_result.QualityResultError, "requires OBSERVED"):
            validate_quality_result.validate_data(result)

    def test_symlink_and_oversized_input_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real.json"
            real.write_text("{}", encoding="utf-8")
            linked = root / "linked.json"
            linked.symlink_to(real)
            with self.assertRaises(validate_quality_result.QualityResultError):
                validate_quality_result.validate(linked)
            oversized = root / "oversized.json"
            oversized.write_bytes(b" " * (validate_quality_result.MAX_INPUT_BYTES + 1))
            with self.assertRaisesRegex(validate_quality_result.QualityResultError, "size limit"):
                validate_quality_result.validate(oversized)


if __name__ == "__main__":
    unittest.main()
