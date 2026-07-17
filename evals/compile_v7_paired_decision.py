#!/usr/bin/env python3
"""Compile a bounded, read-only v7 paired-candidate continuation decision."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MAX_JSON_BYTES = 1_048_576
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_DEPTH = 24
SHA256 = re.compile(r"[0-9a-f]{64}")
IDENTIFIER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
DECISIONS = {
    "READY_FOR_SEALED",
    "REJECTED_STOP",
    "ELIGIBLE_FOR_EVALUATOR_ACCEPTANCE",
    "UNAVAILABLE",
}
HARD_GATES = (
    "installability",
    "security",
    "accessibility",
    "evidence_integrity",
    "design_md",
    "runtime_mapping",
    "screenshot_inventory",
    "v6_regression",
)
SEALED_GATES = ("security", "accessibility", "evidence_integrity", "screenshot_inventory")
EVIDENCE_KINDS = {
    "development-decision",
    "validation-summary",
    "paired-run",
    "sealed-test-arm",
}
EVIDENCE_RECEIPT_KEYS = {
    "schema_version",
    "kind",
    "identity",
    "payload_sha256",
    "manifest_sha256",
    "accepted_package_sha256",
    "candidate_reference_sha256",
    "evaluator_toolchain_sha256",
}
ARM_SOURCE_KEYS = {
    "generation_manifest_sha256",
    "output_inventory_sha256",
    "visual_ledger_sha256",
    "visual_result_inventory_sha256",
    "attempt_history_sha256",
    "brief_inventory_sha256",
    "input_inventory_sha256",
    "execution_contract_sha256",
}
INDEPENDENT_ARM_SOURCE_KEYS = (
    "generation_manifest_sha256",
    "output_inventory_sha256",
    "visual_ledger_sha256",
    "visual_result_inventory_sha256",
    "attempt_history_sha256",
)
SHARED_ARM_SOURCE_KEYS = (
    "brief_inventory_sha256",
    "input_inventory_sha256",
    "execution_contract_sha256",
)
CLAIM_BOUNDARY = (
    "Applies the frozen ratchet to source-bound evaluator receipts without independently parsing raw "
    "browser artifacts. It does not inspect hidden briefs, grade craft, run models or browsers, prove "
    "generalization, estimate cost, or promote a Skill."
)


def _module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


preflight = _module("v7_paired_preflight", ROOT / "evals" / "v7_preflight.py")


class V7PairedDecisionError(ValueError):
    """Raised when a decision input or output path is unsafe."""


class V7PairedDecisionUnavailable(ValueError):
    """Raised when evaluator evidence cannot support a decision."""

    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise V7PairedDecisionUnavailable("duplicate_json_key")
        value[key] = child
    return value


def _check_depth(value: Any, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise V7PairedDecisionUnavailable("json_depth_exceeded")
    if isinstance(value, dict):
        for child in value.values():
            _check_depth(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _check_depth(child, depth + 1)


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        mode = path.lstat().st_mode
    except OSError as error:
        raise V7PairedDecisionUnavailable(f"{label}_missing") from error
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode) or path.stat().st_size > MAX_JSON_BYTES:
        raise V7PairedDecisionUnavailable(f"{label}_unsafe_or_oversized")
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object_without_duplicates)
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise V7PairedDecisionUnavailable(f"{label}_invalid_json") from error
    if not isinstance(value, dict):
        raise V7PairedDecisionUnavailable(f"{label}_root_invalid")
    _check_depth(value)
    return value


def _exact_object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise V7PairedDecisionUnavailable(f"{label}_schema_changed")
    return value


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise V7PairedDecisionUnavailable(f"{label}_sha256_invalid")
    return value


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or IDENTIFIER.fullmatch(value) is None:
        raise V7PairedDecisionUnavailable(f"{label}_invalid")
    return value


def _outside_file(path: Path, repository_root: Path, label: str) -> Path:
    repository_root = repository_root.resolve(strict=True)
    try:
        mode = path.lstat().st_mode
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise V7PairedDecisionUnavailable(f"{label}_missing") from error
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode) or resolved.stat().st_size > MAX_SOURCE_BYTES:
        raise V7PairedDecisionUnavailable(f"{label}_unsafe_or_oversized")
    try:
        resolved.relative_to(repository_root)
    except ValueError:
        return resolved
    raise V7PairedDecisionUnavailable(f"{label}_must_be_evaluator_owned")


def _evidence_ids(value: Any, known: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if (
        not isinstance(value, list)
        or (not allow_empty and not value)
        or len(value) > 32
        or any(not isinstance(item, str) or item not in known for item in value)
        or len(value) != len(set(value))
    ):
        raise V7PairedDecisionUnavailable(f"{label}_invalid")
    return value


def _gates(value: Any, names: tuple[str, ...], label: str, allowed: set[str]) -> dict[str, str]:
    result = _exact_object(value, set(names), label)
    if any(result[name] not in allowed for name in names):
        raise V7PairedDecisionUnavailable(f"{label}_status_invalid")
    return result


def _gate_decision(gates: dict[str, str], names: tuple[str, ...], prefix: str) -> tuple[str, str] | None:
    for name in names:
        if gates[name] == "fail":
            return "REJECTED_STOP", f"{prefix}_{name}_failed"
    for name in names:
        if gates[name] in {"unavailable", "not_run"}:
            return "UNAVAILABLE", f"{prefix}_{name}_{gates[name]}"
    return None


def _families(value: Any, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list) or not 1 <= len(value) <= 16:
        raise V7PairedDecisionUnavailable(f"{label}_invalid")
    result: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(value):
        item = _exact_object(
            raw,
            {"id", "priority", "predesignated", "accepted_failures", "candidate_failures"},
            f"{label}_{index}",
        )
        family_id = _identifier(item["id"], f"{label}_{index}_id")
        if family_id in result:
            raise V7PairedDecisionUnavailable(f"{label}_duplicate_id")
        if (
            isinstance(item["priority"], bool)
            or not isinstance(item["priority"], int)
            or not 1 <= item["priority"] <= 16
            or type(item["predesignated"]) is not bool
            or any(
                isinstance(item[key], bool) or not isinstance(item[key], int) or not 0 <= item[key] <= 10_000
                for key in ("accepted_failures", "candidate_failures")
            )
        ):
            raise V7PairedDecisionUnavailable(f"{label}_{index}_value_invalid")
        result[family_id] = dict(item)
    return result


def _deterministic_vector(families: dict[str, dict[str, Any]]) -> tuple[str, str] | None:
    improvements = [
        item
        for item in families.values()
        if item["predesignated"] and item["candidate_failures"] < item["accepted_failures"]
    ]
    if not improvements:
        return "REJECTED_STOP", "no_strict_deterministic_improvement"
    best_priority = min(item["priority"] for item in improvements)
    if any(
        item["priority"] < best_priority and item["candidate_failures"] > item["accepted_failures"]
        for item in families.values()
    ):
        return "REJECTED_STOP", "higher_priority_deterministic_regression"
    return None


def _arm_sources(value: Any, label: str) -> dict[str, dict[str, str]]:
    arms = _exact_object(value, {"accepted", "candidate"}, label)
    result: dict[str, dict[str, str]] = {}
    for arm in ("accepted", "candidate"):
        source = _exact_object(arms[arm], ARM_SOURCE_KEYS, f"{label}_{arm}")
        result[arm] = {
            key: _sha(source[key], f"{label}_{arm}_{key}")
            for key in sorted(ARM_SOURCE_KEYS)
        }
    return result


def _validate_arm_pair(
    arms: dict[str, dict[str, str]],
    used_independent_sources: set[str],
    *,
    prefix: str,
) -> tuple[str, str, str]:
    accepted = arms["accepted"]
    candidate = arms["candidate"]
    if any(accepted[key] != candidate[key] for key in SHARED_ARM_SOURCE_KEYS):
        raise V7PairedDecisionUnavailable(f"{prefix}_arm_input_drift")
    independent = [
        source[key]
        for source in (accepted, candidate)
        for key in INDEPENDENT_ARM_SOURCE_KEYS
    ]
    if len(independent) != len(set(independent)) or set(independent) & used_independent_sources:
        raise V7PairedDecisionUnavailable(f"{prefix}_source_reused")
    used_independent_sources.update(independent)
    return tuple(accepted[key] for key in SHARED_ARM_SOURCE_KEYS)


def _decision(status: str, reason_code: str, next_action: str, subject: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    if status not in DECISIONS:
        raise AssertionError(status)
    return {
        "schema_version": 1,
        "status": status,
        "reason_code": reason_code,
        "authority": "decision-support-only-no-promotion",
        "claim_boundary": CLAIM_BOUNDARY,
        "subject": subject,
        "source": source,
        "next_action": next_action,
    }


def _validate_bindings(
    raw: Any,
    repository_root: Path,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    if not isinstance(raw, list) or not 1 <= len(raw) <= 64:
        raise V7PairedDecisionUnavailable("artifact_bindings_invalid")
    bindings: dict[str, dict[str, Any]] = {}
    resolved_paths: set[Path] = set()
    content_hashes: set[str] = set()
    receipts: list[dict[str, str]] = []
    for index, value in enumerate(raw):
        item = _exact_object(value, {"id", "path", "sha256"}, f"artifact_binding_{index}")
        artifact_id = _identifier(item["id"], f"artifact_binding_{index}_id")
        if artifact_id in bindings or not isinstance(item["path"], str) or "\x00" in item["path"]:
            raise V7PairedDecisionUnavailable("artifact_binding_identity_invalid")
        path = _outside_file(Path(item["path"]), repository_root, f"artifact_binding_{index}")
        expected = _sha(item["sha256"], f"artifact_binding_{index}")
        if _digest(path) != expected:
            raise V7PairedDecisionUnavailable("artifact_binding_hash_drift")
        if path in resolved_paths or expected in content_hashes:
            raise V7PairedDecisionUnavailable("artifact_binding_evidence_reused")
        evidence = _exact_object(_load_json(path, f"artifact_binding_{index}"), EVIDENCE_RECEIPT_KEYS, f"artifact_binding_{index}")
        if evidence["schema_version"] != 1 or evidence["kind"] not in EVIDENCE_KINDS:
            raise V7PairedDecisionUnavailable("artifact_binding_receipt_invalid")
        _identifier(evidence["identity"], f"artifact_binding_{index}_identity")
        for key in (
            "payload_sha256",
            "manifest_sha256",
            "accepted_package_sha256",
            "candidate_reference_sha256",
            "evaluator_toolchain_sha256",
        ):
            _sha(evidence[key], f"artifact_binding_{index}_{key}")
        resolved_paths.add(path)
        content_hashes.add(expected)
        bindings[artifact_id] = {"id": artifact_id, "sha256": expected, "receipt": evidence}
        receipts.append({"id": artifact_id, "sha256": expected})
    return bindings, receipts


def _required_receipt(
    bindings: dict[str, dict[str, Any]],
    evidence_id: str,
    *,
    kind: str,
    identity: str,
    payload: Any,
    manifest_sha256: str,
    accepted_package_sha256: str,
    candidate_reference_sha256: str,
    evaluator_toolchain_sha256: str,
) -> None:
    evidence = bindings[evidence_id]["receipt"]
    expected = {
        "schema_version": 1,
        "kind": kind,
        "identity": identity,
        "payload_sha256": _canonical_sha256(payload),
        "manifest_sha256": manifest_sha256,
        "accepted_package_sha256": accepted_package_sha256,
        "candidate_reference_sha256": candidate_reference_sha256,
        "evaluator_toolchain_sha256": evaluator_toolchain_sha256,
    }
    if evidence != expected:
        raise V7PairedDecisionUnavailable(f"{kind.replace('-', '_')}_receipt_drift")


def decide_bundle(
    manifest: dict[str, Any],
    bundle: dict[str, Any],
    bindings: dict[str, dict[str, Any]],
) -> tuple[str, str, str]:
    _exact_object(bundle, {
        "schema_version", "manifest_sha256", "candidate_reference_sha256", "accepted_package_sha256",
        "evaluator_toolchain_sha256", "artifact_bindings", "development", "sealed_validation", "sealed_test",
    }, "decision_bundle")
    if bundle["schema_version"] != 1:
        raise V7PairedDecisionUnavailable("decision_bundle_schema_version_unknown")
    if manifest.get("stage") != "frozen":
        raise V7PairedDecisionUnavailable("candidate_not_frozen")
    if bundle["candidate_reference_sha256"] != manifest.get("candidate", {}).get("reference_sha256"):
        raise V7PairedDecisionUnavailable("decision_bundle_candidate_drift")
    expected_accepted_sha256 = _canonical_sha256(manifest["baseline"])
    expected_toolchain_sha256 = _canonical_sha256({
        "toolchain": manifest["toolchain"],
        "evaluators": manifest["evaluators"],
    })
    if bundle["accepted_package_sha256"] != expected_accepted_sha256:
        raise V7PairedDecisionUnavailable("accepted_package_manifest_drift")
    if bundle["evaluator_toolchain_sha256"] != expected_toolchain_sha256:
        raise V7PairedDecisionUnavailable("evaluator_toolchain_manifest_drift")
    toolchain_sha256 = expected_toolchain_sha256
    known_ids = set(bindings)

    development = _exact_object(
        bundle["development"],
        {"status", "evidence_ids", "hard_gates", "failure_families", "new_case_engine_failures"},
        "development",
    )
    if development["status"] not in {"complete", "unavailable"}:
        raise V7PairedDecisionUnavailable("development_status_invalid")
    development_ids = _evidence_ids(development["evidence_ids"], known_ids, "development_evidence")
    if len(development_ids) != 1:
        raise V7PairedDecisionUnavailable("development_evidence_count_invalid")
    _required_receipt(
        bindings,
        development_ids[0],
        kind="development-decision",
        identity="development",
        payload=development,
        manifest_sha256=bundle["manifest_sha256"],
        accepted_package_sha256=expected_accepted_sha256,
        candidate_reference_sha256=bundle["candidate_reference_sha256"],
        evaluator_toolchain_sha256=expected_toolchain_sha256,
    )
    dev_gates = _gates(development["hard_gates"], HARD_GATES, "development_hard_gates", {"pass", "fail", "unavailable"})
    if development["status"] == "unavailable":
        return "UNAVAILABLE", "development_evidence_unavailable", "complete_development_evidence"
    gate_result = _gate_decision(dev_gates, HARD_GATES, "development")
    if gate_result is not None:
        return (*gate_result, "preserve_accepted_and_stop_or_complete_evidence")
    new_failures = development["new_case_engine_failures"]
    if isinstance(new_failures, bool) or not isinstance(new_failures, int) or not 0 <= new_failures <= 10_000:
        raise V7PairedDecisionUnavailable("development_new_failure_count_invalid")
    if new_failures:
        return "REJECTED_STOP", "development_new_case_or_engine_failure", "preserve_accepted_and_stop_candidate"
    dev_families = _families(development["failure_families"], "development_families")
    vector_result = _deterministic_vector(dev_families)
    if vector_result is not None:
        return (*vector_result, "preserve_accepted_and_stop_candidate")

    sealed_test = _exact_object(
        bundle["sealed_test"],
        {"status", "accepted_evidence_id", "candidate_evidence_id", "arms"},
        "sealed_test",
    )
    if sealed_test["status"] not in {"pass", "fail", "not_run", "unavailable"}:
        raise V7PairedDecisionUnavailable("sealed_test_status_invalid")
    sealed_test_ids: list[str] = []
    if sealed_test["status"] in {"pass", "fail"}:
        sealed_test_ids = _evidence_ids(
            [sealed_test["accepted_evidence_id"], sealed_test["candidate_evidence_id"]],
            known_ids,
            "sealed_test_evidence",
        )
        if len(sealed_test_ids) != 2:
            raise V7PairedDecisionUnavailable("sealed_test_arm_evidence_invalid")
        if not isinstance(sealed_test["arms"], dict):
            raise V7PairedDecisionUnavailable("sealed_test_arm_sources_missing")
    elif (
        sealed_test["accepted_evidence_id"] is not None
        or sealed_test["candidate_evidence_id"] is not None
        or sealed_test["arms"] is not None
    ):
        raise V7PairedDecisionUnavailable("sealed_test_unavailable_contract_invalid")

    validation = _exact_object(
        bundle["sealed_validation"],
        {"status", "evidence_ids", "hard_gates", "blind_craft", "budget_status", "pairs"},
        "sealed_validation",
    )
    if validation["status"] not in {"not_started", "complete", "unavailable"}:
        raise V7PairedDecisionUnavailable("sealed_validation_status_invalid")
    validation_ids = _evidence_ids(
        validation["evidence_ids"], known_ids, "sealed_validation_evidence", allow_empty=validation["status"] == "not_started"
    )
    sealed_gates = _gates(
        validation["hard_gates"], SEALED_GATES, "sealed_hard_gates", {"pass", "fail", "unavailable", "not_run"}
    )
    if validation["status"] == "not_started":
        if (
            validation_ids
            or validation["pairs"]
            or validation["blind_craft"] != "not_run"
            or validation["budget_status"] != "not_run"
            or any(value != "not_run" for value in sealed_gates.values())
            or sealed_test["status"] != "not_run"
            or sealed_test_ids
        ):
            raise V7PairedDecisionUnavailable("sealed_not_started_contract_invalid")
        return "READY_FOR_SEALED", "development_ratchet_passed", "run_frozen_sealed_validation"
    if validation["status"] == "unavailable":
        return "UNAVAILABLE", "sealed_validation_unavailable", "complete_sealed_validation_evidence"
    if len(validation_ids) != 1:
        raise V7PairedDecisionUnavailable("sealed_validation_evidence_count_invalid")
    _required_receipt(
        bindings,
        validation_ids[0],
        kind="validation-summary",
        identity="sealed-validation",
        payload=validation,
        manifest_sha256=bundle["manifest_sha256"],
        accepted_package_sha256=expected_accepted_sha256,
        candidate_reference_sha256=bundle["candidate_reference_sha256"],
        evaluator_toolchain_sha256=expected_toolchain_sha256,
    )
    gate_result = _gate_decision(sealed_gates, SEALED_GATES, "sealed")
    if gate_result is not None:
        return (*gate_result, "preserve_accepted_or_complete_sealed_evidence")
    if validation["blind_craft"] == "material_loss":
        return "REJECTED_STOP", "sealed_blind_craft_material_loss", "preserve_accepted_and_stop_candidate"
    if validation["blind_craft"] != "pass":
        return "UNAVAILABLE", "sealed_blind_craft_unavailable", "complete_blind_craft_evidence"
    if validation["budget_status"] == "exceeded":
        return "REJECTED_STOP", "sealed_budget_exceeded", "preserve_accepted_and_stop_candidate"
    if validation["budget_status"] != "within":
        return "UNAVAILABLE", "sealed_budget_unavailable", "complete_budget_evidence"
    pairs = validation["pairs"]
    if not isinstance(pairs, list) or len(pairs) != 3:
        return "UNAVAILABLE", "sealed_pair_count_incomplete", "complete_three_paired_validation_runs"
    pair_ids: set[str] = set()
    pair_evidence_ids: set[str] = set()
    pair_orders: set[str] = set()
    used_independent_sources: set[str] = set()
    validation_shared_sources: tuple[str, str, str] | None = None
    aggregate: dict[str, dict[str, Any]] = {}
    family_contract: dict[str, tuple[int, bool]] | None = None
    for index, raw in enumerate(pairs):
        pair = _exact_object(raw, {
            "id", "eligible", "order", "manifest_sha256", "accepted_package_sha256", "candidate_reference_sha256",
            "evaluator_toolchain_sha256", "evidence_ids", "arms", "failure_families", "new_case_engine_failures",
        }, f"sealed_pair_{index}")
        pair_id = _identifier(pair["id"], f"sealed_pair_{index}_id")
        if pair_id in pair_ids:
            raise V7PairedDecisionUnavailable("sealed_pair_id_duplicate")
        pair_ids.add(pair_id)
        if pair["eligible"] is not True:
            return "UNAVAILABLE", "sealed_pair_ineligible", "complete_three_paired_validation_runs"
        if pair["order"] not in {"accepted-first", "candidate-first"}:
            raise V7PairedDecisionUnavailable("sealed_pair_order_invalid")
        pair_orders.add(pair["order"])
        if (
            pair["manifest_sha256"] != bundle["manifest_sha256"]
            or pair["accepted_package_sha256"] != bundle["accepted_package_sha256"]
            or pair["candidate_reference_sha256"] != bundle["candidate_reference_sha256"]
            or pair["evaluator_toolchain_sha256"] != toolchain_sha256
        ):
            return "UNAVAILABLE", "sealed_pair_provenance_drift", "rerun_pair_under_frozen_toolchain"
        current_evidence_ids = set(
            _evidence_ids(pair["evidence_ids"], known_ids, f"sealed_pair_{index}_evidence")
        )
        if len(current_evidence_ids) != 1:
            raise V7PairedDecisionUnavailable("sealed_pair_evidence_count_invalid")
        if current_evidence_ids & pair_evidence_ids:
            return "UNAVAILABLE", "sealed_pair_evidence_reused", "provide_three_independent_pair_receipts"
        pair_evidence_ids.update(current_evidence_ids)
        _required_receipt(
            bindings,
            next(iter(current_evidence_ids)),
            kind="paired-run",
            identity=pair_id,
            payload=pair,
            manifest_sha256=bundle["manifest_sha256"],
            accepted_package_sha256=expected_accepted_sha256,
            candidate_reference_sha256=bundle["candidate_reference_sha256"],
            evaluator_toolchain_sha256=expected_toolchain_sha256,
        )
        arms = _arm_sources(pair["arms"], f"sealed_pair_{index}_arms")
        shared_sources = _validate_arm_pair(
            arms,
            used_independent_sources,
            prefix="sealed_pair",
        )
        if validation_shared_sources is None:
            validation_shared_sources = shared_sources
        elif shared_sources != validation_shared_sources:
            return "UNAVAILABLE", "sealed_pair_shared_input_drift", "rerun_pairs_with_identical_frozen_inputs"
        count = pair["new_case_engine_failures"]
        if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= 10_000:
            raise V7PairedDecisionUnavailable("sealed_pair_new_failure_count_invalid")
        if count:
            return "REJECTED_STOP", "sealed_new_case_or_engine_failure", "preserve_accepted_and_stop_candidate"
        families = _families(pair["failure_families"], f"sealed_pair_{index}_families")
        contract = {key: (item["priority"], item["predesignated"]) for key, item in families.items()}
        if family_contract is None:
            family_contract = contract
            aggregate = {
                key: {
                    "id": key,
                    "priority": item["priority"],
                    "predesignated": item["predesignated"],
                    "accepted_failures": 0,
                    "candidate_failures": 0,
                }
                for key, item in families.items()
            }
        elif contract != family_contract:
            return "UNAVAILABLE", "sealed_failure_family_contract_drift", "rerun_pair_under_frozen_failure_families"
        for key, item in families.items():
            aggregate[key]["accepted_failures"] += item["accepted_failures"]
            aggregate[key]["candidate_failures"] += item["candidate_failures"]
    if pair_orders != {"accepted-first", "candidate-first"}:
        return "UNAVAILABLE", "sealed_pair_order_unbalanced", "rerun_counterbalanced_paired_validation"
    if set(sealed_test_ids) & (set(validation_ids) | pair_evidence_ids):
        return "UNAVAILABLE", "sealed_test_evidence_reused", "provide_untouched_sealed_test_evidence"
    vector_result = _deterministic_vector(aggregate)
    if vector_result is not None:
        return (*vector_result, "preserve_accepted_and_stop_candidate")

    if sealed_test["status"] == "fail":
        sealed_test_arms = _arm_sources(sealed_test["arms"], "sealed_test_arms")
        sealed_test_shared = _validate_arm_pair(
            sealed_test_arms,
            used_independent_sources,
            prefix="sealed_test",
        )
        if validation_shared_sources is None or sealed_test_shared[2] != validation_shared_sources[2]:
            raise V7PairedDecisionUnavailable("sealed_test_execution_contract_drift")
        if any(sealed_test_shared[index] == validation_shared_sources[index] for index in (0, 1)):
            raise V7PairedDecisionUnavailable("sealed_test_not_untouched")
        for arm, evidence_id in zip(("accepted", "candidate"), sealed_test_ids):
            _required_receipt(
                bindings,
                evidence_id,
                kind="sealed-test-arm",
                identity=f"sealed-test-{arm}",
                payload=sealed_test,
                manifest_sha256=bundle["manifest_sha256"],
                accepted_package_sha256=expected_accepted_sha256,
                candidate_reference_sha256=bundle["candidate_reference_sha256"],
                evaluator_toolchain_sha256=expected_toolchain_sha256,
            )
        return "REJECTED_STOP", "sealed_test_failed", "preserve_accepted_and_stop_candidate"
    if sealed_test["status"] != "pass":
        return "UNAVAILABLE", f"sealed_test_{sealed_test['status']}", "run_untouched_sealed_test_once"
    sealed_test_arms = _arm_sources(sealed_test["arms"], "sealed_test_arms")
    sealed_test_shared = _validate_arm_pair(
        sealed_test_arms,
        used_independent_sources,
        prefix="sealed_test",
    )
    if validation_shared_sources is None or sealed_test_shared[2] != validation_shared_sources[2]:
        raise V7PairedDecisionUnavailable("sealed_test_execution_contract_drift")
    if any(sealed_test_shared[index] == validation_shared_sources[index] for index in (0, 1)):
        raise V7PairedDecisionUnavailable("sealed_test_not_untouched")
    for arm, evidence_id in zip(("accepted", "candidate"), sealed_test_ids):
        _required_receipt(
            bindings,
            evidence_id,
            kind="sealed-test-arm",
            identity=f"sealed-test-{arm}",
            payload=sealed_test,
            manifest_sha256=bundle["manifest_sha256"],
            accepted_package_sha256=expected_accepted_sha256,
            candidate_reference_sha256=bundle["candidate_reference_sha256"],
            evaluator_toolchain_sha256=expected_toolchain_sha256,
        )
    return "ELIGIBLE_FOR_EVALUATOR_ACCEPTANCE", "paired_ratchet_passed", "request_evaluator_acceptance"


def compile_decision(manifest_path: Path, bundle_path: Path | None, repository_root: Path) -> dict[str, Any]:
    repository_root = repository_root.resolve(strict=True)
    manifest_path = manifest_path.resolve(strict=True)
    try:
        manifest_path.relative_to(repository_root)
    except ValueError as error:
        raise V7PairedDecisionError("manifest must remain inside the repository") from error
    preflight.validate_manifest(manifest_path, repository_root)
    manifest = _load_json(manifest_path, "manifest")
    subject = {
        "cohort_id": manifest["cohort_id"],
        "candidate_id": manifest["candidate"]["id"],
        "manifest": {
            "path": manifest_path.relative_to(repository_root).as_posix(),
            "sha256": _digest(manifest_path),
            "stage": manifest["stage"],
        },
    }
    source: dict[str, Any] = {"bundle": {"status": "missing"}, "artifact_binding_count": 0}
    if manifest["stage"] != "frozen":
        return _decision("UNAVAILABLE", "candidate_not_frozen", "freeze_candidate_and_evaluator_before_sealed_evidence", subject, source)
    if bundle_path is None:
        return _decision("UNAVAILABLE", "decision_bundle_missing", "provide_evaluator_owned_paired_bundle", subject, source)
    try:
        bundle_path = _outside_file(bundle_path, repository_root, "decision_bundle")
        bundle = _load_json(bundle_path, "decision_bundle")
        if bundle.get("manifest_sha256") != subject["manifest"]["sha256"]:
            raise V7PairedDecisionUnavailable("decision_bundle_manifest_drift")
        candidate_sha = manifest["candidate"]["reference_sha256"]
        if bundle.get("candidate_reference_sha256") != candidate_sha:
            raise V7PairedDecisionUnavailable("decision_bundle_candidate_drift")
        bindings, binding_receipts = _validate_bindings(bundle.get("artifact_bindings"), repository_root)
        source = {
            "bundle": {"status": "bound", "sha256": _digest(bundle_path)},
            "artifact_binding_count": len(binding_receipts),
            "artifact_inventory_sha256": _canonical_sha256(binding_receipts),
        }
        status, reason_code, next_action = decide_bundle(manifest, bundle, bindings)
        return _decision(status, reason_code, next_action, subject, source)
    except V7PairedDecisionUnavailable as error:
        if bundle_path is not None and bundle_path.exists() and bundle_path.is_file() and not bundle_path.is_symlink():
            source["bundle"] = {"status": "unavailable", "sha256": _digest(bundle_path)}
        return _decision("UNAVAILABLE", error.reason_code, "repair_or_recreate_evaluator_owned_bundle", subject, source)


def _write_once(path: Path, value: dict[str, Any], repository_root: Path) -> None:
    repository_root = repository_root.resolve(strict=True)
    if path.exists() or path.is_symlink():
        raise V7PairedDecisionError("refusing to overwrite paired decision receipt")
    parent = path.parent.resolve(strict=True)
    try:
        parent.relative_to(repository_root)
    except ValueError:
        pass
    else:
        raise V7PairedDecisionError("decision output must remain evaluator-owned outside the repository")
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        root = args.repository_root.expanduser().resolve(strict=True)
        result = compile_decision(args.manifest.expanduser(), args.bundle.expanduser() if args.bundle else None, root)
        _write_once(args.output.expanduser(), result, root)
    except (OSError, preflight.PreflightError, V7PairedDecisionError) as error:
        print(f"v7 paired decision failed: {error}", file=sys.stderr)
        return 1
    print(f"v7 paired decision: {result['status']} ({result['reason_code']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
