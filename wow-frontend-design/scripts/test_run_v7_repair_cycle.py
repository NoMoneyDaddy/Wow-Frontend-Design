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


if __name__ == "__main__":
    unittest.main()
