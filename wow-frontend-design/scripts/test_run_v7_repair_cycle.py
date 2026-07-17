#!/usr/bin/env python3
"""Synthetic state-machine tests for the bounded v7 repair cycle."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "evals" / "run_v7_repair_cycle.py"
SPEC = importlib.util.spec_from_file_location("run_v7_repair_cycle", MODULE)
assert SPEC and SPEC.loader
cycle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cycle)


def _target(case_id: str = "case-one") -> dict:
    return {"variant": "candidate", "case_id": case_id, "narrow_retest": [], "feedback": "bounded"}


def _packet(*targets: dict) -> dict:
    return {"schema_version": 1, "status": "repair_required", "targets": list(targets)}


def _write_target(root: Path, body: str) -> None:
    root.mkdir()
    outputs = []
    for name in ("DESIGN.md", "index.html"):
        artifact = root / name
        artifact.write_text(body, encoding="utf-8")
        outputs.append({"path": name, "bytes": artifact.stat().st_size, "sha256": cycle._digest(artifact)})
    (root / "run-manifest.json").write_text(json.dumps({
        "schema_version": 1,
        "status": "completed",
        "outputs": outputs,
    }), encoding="utf-8")


def _rewrite_target(root: Path, body: str) -> None:
    outputs = []
    for name in ("DESIGN.md", "index.html"):
        artifact = root / name
        artifact.write_text(body, encoding="utf-8")
        outputs.append({"path": name, "bytes": artifact.stat().st_size, "sha256": cycle._digest(artifact)})
    (root / "run-manifest.json").write_text(json.dumps({
        "schema_version": 1,
        "status": "completed",
        "outputs": outputs,
    }), encoding="utf-8")


class V7RepairCycleTests(unittest.TestCase):
    def test_narrow_finding_retries_before_the_only_full_run_and_promotion(self) -> None:
        target = _target()
        generated = []
        receipts = []
        full_calls = []
        promotions = []

        def generate(item: dict, _packet_value: dict, number: int) -> dict:
            generated.append((item["case_id"], number))
            return {"root": f"/tmp/round-{number}", "receipt": {"round": number}}

        def narrow(_item: dict, _generation: dict, number: int) -> dict:
            findings = [target] if number == 1 else []
            return {"targets": findings, "packet": _packet(*findings), "receipt": {"round": number}}

        def full(staged: dict, number: int) -> dict:
            full_calls.append((dict(staged), number))
            return {
                "packet": {"status": "clean", "targets": []},
                "receipt": {"round": number},
                "verified_targets": {},
            }

        def promote(staged: dict, _verified: dict) -> dict:
            promotions.append(dict(staged))
            return {"status": "promoted"}

        result = cycle.execute_cycle(
            _packet(target),
            generate=generate,
            capture_narrow=narrow,
            run_full=full,
            promote=promote,
            write_receipt=receipts.append,
        )
        self.assertEqual([("case-one", 1), ("case-one", 2)], generated)
        self.assertEqual(1, len(full_calls))
        self.assertEqual(1, len(promotions))
        self.assertEqual(["narrow_failed", "narrow_clean", "full_clean", "completed"], [item["status"] for item in receipts])
        self.assertEqual("completed", result["status"])

    def test_repeated_narrow_finding_fuses_without_full_or_promotion(self) -> None:
        target = _target()
        full_calls = []
        promotions = []
        receipts = []

        def generate(_item: dict, _packet_value: dict, number: int) -> dict:
            return {"root": f"/tmp/round-{number}", "receipt": {"round": number}}

        def narrow(_item: dict, _generation: dict, number: int) -> dict:
            return {"targets": [target], "packet": _packet(target), "receipt": {"round": number}}

        with self.assertRaisesRegex(cycle.V7RepairCycleFuse, "bounded repair generations"):
            cycle.execute_cycle(
                _packet(target),
                generate=generate,
                capture_narrow=narrow,
                run_full=lambda *_args: full_calls.append(True),
                promote=lambda *_args: promotions.append(True),
                write_receipt=receipts.append,
                max_generations=3,
            )
        self.assertEqual([], full_calls)
        self.assertEqual([], promotions)
        self.assertEqual("PARTIALLY VERIFIED", receipts[-1]["status"])

    def test_full_finding_reenters_selective_repair_then_requires_full_clean(self) -> None:
        first = _target("case-one")
        discovered = _target("case-two")
        generated = []
        full_packets = [_packet(discovered), {"schema_version": 1, "status": "clean", "targets": []}]
        promoted = []

        def generate(item: dict, _packet_value: dict, number: int) -> dict:
            generated.append((item["case_id"], number))
            return {"root": f"/tmp/{item['case_id']}-{number}", "receipt": {"round": number}}

        result = cycle.execute_cycle(
            _packet(first),
            generate=generate,
            capture_narrow=lambda *_args: {"targets": [], "packet": {"status": "clean"}, "receipt": {}},
            run_full=lambda _staged, number: {
                "packet": full_packets[number - 1],
                "receipt": {"round": number},
                "verified_targets": {},
            },
            promote=lambda staged, _verified: promoted.append(dict(staged)) or {"status": "promoted"},
            write_receipt=lambda _value: None,
        )
        self.assertEqual([("case-one", 1), ("case-two", 1)], generated)
        self.assertEqual(2, result["full_runs"])
        self.assertEqual(1, len(promoted))

    def test_unexpected_narrow_target_fails_closed(self) -> None:
        target = _target("case-one")
        with self.assertRaisesRegex(cycle.V7RepairCycleError, "unexpected repair target"):
            cycle.execute_cycle(
                _packet(target),
                generate=lambda *_args: {"root": "/tmp/one", "receipt": {}},
                capture_narrow=lambda *_args: {
                    "targets": [_target("case-two")],
                    "packet": _packet(_target("case-two")),
                    "receipt": {},
                },
                run_full=lambda *_args: {},
                promote=lambda *_args: {},
                write_receipt=lambda _value: None,
            )

    def test_non_improving_candidate_retains_best_source_and_skips_verification(self) -> None:
        target = _target()
        receipts = []
        full_calls = []
        retained = []
        with self.assertRaisesRegex(cycle.V7RepairCycleFuse, "lexicographic ratchet"):
            cycle.execute_cycle(
                _packet(target),
                generate=lambda *_args: {
                    "root": "/tmp/worse",
                    "source_root": "/tmp/source",
                    "receipt": {},
                },
                capture_narrow=lambda *_args: {
                    "targets": [target],
                    "packet": _packet(target),
                    "receipt": {},
                },
                run_full=lambda *_args: full_calls.append(True),
                promote=lambda *_args: {},
                write_receipt=receipts.append,
                rank_source=lambda _target_value: (*([0] * 10), "a" * 64),
                rank_candidate=lambda *_args: (1, *([0] * 9), "b" * 64),
                retain_best=lambda *args: retained.append(args),
            )
        self.assertEqual([], retained)
        self.assertEqual([], full_calls)
        self.assertEqual("non_improving_artifact", receipts[-1]["outcome"])
        self.assertEqual("/tmp/source", receipts[-1]["retained_root"])

    def test_full_cohort_selection_may_discover_a_foreign_target(self) -> None:
        first = _target("case-one")
        second = _target("case-two")
        captured = []

        def capture(item: dict, *_args) -> dict:
            captured.append(item["case_id"])
            targets = [second] if item["case_id"] == "case-one" else []
            return {
                "targets": targets,
                "packet": _packet(*targets),
                "selection": {"decision": "cohort-full-matrix"},
                "receipt": {},
            }

        result = cycle.execute_cycle(
            _packet(first),
            generate=lambda item, *_args: {"root": f"/tmp/{item['case_id']}", "receipt": {}},
            capture_narrow=capture,
            run_full=lambda *_args: {
                "packet": {"status": "clean"},
                "receipt": {"mode": "affected"},
                "verified_targets": {},
            },
            promote=lambda *_args: {"status": "promoted"},
            write_receipt=lambda _value: None,
        )
        self.assertEqual(["case-one", "case-two"], captured)
        self.assertEqual(0, result["full_runs"])
        self.assertEqual(1, result["verification_runs"])

    def test_promotion_failure_rolls_back_all_canonical_targets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "archives"
            canonical = {}
            staged = {}
            for case_id, body in (("case-one", "old-one"), ("case-two", "old-two")):
                key = ("candidate", case_id)
                current = root / f"current-{case_id}"
                repair = root / f"repair-{case_id}"
                _write_target(current, body)
                _write_target(repair, f"new-{case_id}")
                canonical[key] = current
                staged[key] = repair
            real_rename = cycle.os.rename
            call_count = 0

            def fail_second_promotion(source: Path, destination: Path) -> None:
                nonlocal call_count
                call_count += 1
                if call_count == 4:
                    raise OSError("injected promotion failure")
                real_rename(source, destination)

            with mock.patch.object(cycle.os, "rename", side_effect=fail_second_promotion):
                with self.assertRaisesRegex(OSError, "injected promotion failure"):
                    cycle._promote_targets(staged, canonical, archive)
            self.assertEqual("old-one", (canonical[("candidate", "case-one")] / "DESIGN.md").read_text())
            self.assertEqual("old-two", (canonical[("candidate", "case-two")] / "DESIGN.md").read_text())

    def test_source_receipt_rejects_extra_entries_and_manifest_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            _write_target(target, "safe")
            extra = target / "unexpected"
            extra.symlink_to(target / "DESIGN.md")
            with self.assertRaisesRegex(cycle.V7RepairCycleError, "inventory"):
                cycle._source_receipt(target)
            extra.unlink()
            manifest = target / "run-manifest.json"
            backup = root / "manifest.json"
            manifest.rename(backup)
            manifest.symlink_to(backup)
            with self.assertRaisesRegex(cycle.V7RepairCycleError, "inventory"):
                cycle._source_receipt(target)

    def test_self_consistent_staged_replacement_after_full_is_not_promoted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            key = ("candidate", "case-one")
            canonical_root = root / "canonical"
            staged_root = root / "staged"
            _write_target(canonical_root, "old")
            _write_target(staged_root, "full-verified")
            canonical_receipt = cycle._source_receipt(canonical_root)
            verified_receipt = cycle._source_receipt(staged_root)
            _rewrite_target(staged_root, "replaced-after-full")
            with self.assertRaisesRegex(cycle.V7RepairCycleError, "drifted after full verification"):
                cycle._promote_targets(
                    {key: staged_root},
                    {key: canonical_root},
                    root / "archives",
                    expected_canonical={key: canonical_receipt},
                    expected_staged={key: verified_receipt},
                )
            self.assertEqual("old", (canonical_root / "DESIGN.md").read_text())

    def test_affected_selector_binds_current_artifact_and_rejects_later_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            key = ("candidate", "case-one")
            source = root / "source"
            staged = root / "staged"
            _write_target(source, "old")
            _write_target(staged, "improved")
            source_receipt = cycle._source_receipt(source)
            staged_receipt = cycle._source_receipt(staged)
            inventory = [("candidate", "case-one", "base", "mobile", "chromium")]
            target = {
                "variant": "candidate",
                "case_id": "case-one",
                "occurrences": [{
                    "state": "base",
                    "profile": "mobile",
                    "engine": "chromium",
                    "findings": [{
                        "classification": "composition",
                        "code": "a1_prose_han_orphan",
                        "locator": "copy",
                    }],
                }],
            }
            support_sha = "e" * 64
            selector = cycle.policy.select_affected_rows(
                target,
                source_receipt,
                staged_receipt,
                inventory,
                target_isolated=True,
                support_contract_sha256=support_sha,
            )
            selector_path = root / "selector.json"
            selector_path.write_text(json.dumps(selector), encoding="utf-8")
            accepted = {key: {"path": str(selector_path), "sha256": cycle._digest(selector_path)}}
            verified, bindings = cycle._verify_affected_targets(
                {key: staged},
                {key: source_receipt},
                {key: staged_receipt},
                accepted,
                inventory,
                support_sha,
            )
            self.assertEqual(staged_receipt, verified[key])
            self.assertEqual(cycle._digest(selector_path), bindings[0]["selector_sha256"])
            _rewrite_target(staged, "replaced-after-selector")
            with self.assertRaisesRegex(cycle.V7RepairCycleError, "capture receipt is stale"):
                cycle._verify_affected_targets(
                    {key: staged},
                    {key: source_receipt},
                    {key: staged_receipt},
                    accepted,
                    inventory,
                    support_sha,
                )

    def test_support_contract_drift_fails_closed(self) -> None:
        with mock.patch.object(
            cycle.policy,
            "validate_support_contract",
            return_value="b" * 64,
        ):
            with self.assertRaisesRegex(cycle.V7RepairCycleError, "drifted during the cycle"):
                cycle._require_support_contract(Path("/tmp/contract.json"), ROOT, "a" * 64)

    def test_invalid_support_contract_fails_closed(self) -> None:
        with mock.patch.object(
            cycle.policy,
            "validate_support_contract",
            side_effect=cycle.policy.V7RepairPolicyError("auditor binding is stale"),
        ):
            with self.assertRaisesRegex(cycle.V7RepairCycleError, "became invalid"):
                cycle._require_support_contract(Path("/tmp/contract.json"), ROOT, "a" * 64)

    def test_unavailable_supporting_probe_is_retained_without_blocking_visual_completion(self) -> None:
        target = _target()
        unavailable = {
            "coverage_status": "unavailable",
            "reason_code": "probe_execution_unavailable",
            "advisory_count": 0,
            "claim_boundary": cycle.supporting_probes.REGISTRY_BOUNDARY,
        }
        receipts = []
        result = cycle.execute_cycle(
            _packet(target),
            generate=lambda *_args: {
                "root": "/tmp/repaired",
                "receipt": {"supporting_probe": unavailable},
            },
            capture_narrow=lambda *_args: {
                "targets": [],
                "packet": {"status": "clean"},
                "receipt": {"supporting_probe": unavailable},
            },
            run_full=lambda *_args: {
                "packet": {"status": "clean"},
                "receipt": {
                    "mode": "affected",
                    "target_bindings": [{"target": ["candidate", "case-one"], "supporting_probe": unavailable}],
                },
                "verified_targets": {},
            },
            promote=lambda *_args: {"status": "promoted", "supporting_probe": unavailable},
            write_receipt=receipts.append,
        )
        self.assertEqual("completed", result["status"])
        self.assertEqual("unavailable", receipts[0]["generation"]["supporting_probe"]["coverage_status"])
        self.assertEqual("unavailable", receipts[0]["narrow"]["supporting_probe"]["coverage_status"])

    def test_missing_probe_receipt_is_explicitly_unavailable(self) -> None:
        bindings = [{"target": ["candidate", "case-one"]}]
        cycle._attach_supporting_probe_receipts(bindings, {})
        self.assertEqual("unavailable", bindings[0]["supporting_probe"]["coverage_status"])
        self.assertEqual("probe_receipt_missing", bindings[0]["supporting_probe"]["reason_code"])

    def test_changed_after_probe_sidecar_is_unavailable_at_final_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "target"
            root.mkdir()
            (root / "index.html").write_text("<p>copy</p>", encoding="utf-8")
            registry = cycle.supporting_probes.run_source_layout_probe(root, ROOT)
            sidecar = Path(directory) / "supporting-probe-after.json"
            sidecar.write_text(json.dumps(registry), encoding="utf-8")
            key = ("candidate", "case-one")
            receipt = {
                "path": sidecar.name,
                "sha256": cycle._digest(sidecar),
                "coverage_status": registry["coverage"]["status"],
                "reason_code": registry["coverage"]["reason_code"],
                "advisory_count": len(registry["advisories"]),
                "claim_boundary": registry["claim_boundary"],
            }
            bindings = [{"target": list(key)}]
            cycle._attach_supporting_probe_receipts(
                bindings, {key: receipt}, {key: sidecar}, {key: root}, ROOT
            )
            self.assertEqual("complete", bindings[0]["supporting_probe"]["coverage_status"])
            sidecar.write_text("{}", encoding="utf-8")
            cycle._attach_supporting_probe_receipts(
                bindings, {key: receipt}, {key: sidecar}, {key: root}, ROOT
            )
            self.assertEqual("unavailable", bindings[0]["supporting_probe"]["coverage_status"])
            self.assertEqual("probe_receipt_invalid", bindings[0]["supporting_probe"]["reason_code"])


if __name__ == "__main__":
    unittest.main()
