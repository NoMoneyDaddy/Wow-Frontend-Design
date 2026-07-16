#!/usr/bin/env python3
"""Validate a layered WOW quality result without self-scored acceptance."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import evidence_ledger
import score_weak_model_output


GATE_STATUSES = {"PASS", "FAIL", "UNVERIFIED", "NOT_APPLICABLE"}
CRAFT_STATUSES = {"UNVERIFIED", "CONCERN", "ACCEPTABLE", "STRONG"}
RELEASE_STATUSES = {"VERIFIED", "PARTIALLY_VERIFIED", "BLOCKED"}
CRAFT_DIMENSIONS = {
    "accessibility",
    "code-quality",
    "concept-coherence",
    "localization",
    "mobile-experience",
    "originality",
    "performance-resilience",
    "usability-content",
    "visual-typography",
}
ROOT_KEYS = {
    "schema_version",
    "run_valid",
    "run_reason",
    "hard_gates",
    "eligible",
    "coverage",
    "craft",
    "weighted_total",
    "award_lens",
    "release",
    "handoff",
}
GATE_KEYS = {"id", "required", "applicable", "status", "evidence", "reason"}
CRAFT_KEYS = {"evaluator_id", "independent", "rubric_version", "dimensions"}
DIMENSION_KEYS = {"id", "status", "evidence", "uncertainty"}
COVERAGE_KEYS = {"required_applicable", "required_passed", "evidence_items"}
AWARD_KEYS = {"program", "status", "evidence", "boundary"}
HANDOFF_KEYS = {
    "artifact",
    "launch_command",
    "rendered_evidence",
    "remaining_risks",
    "next_action",
}
RENDERED_KEYS = {"status", "paths", "reason"}
ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
MAX_INPUT_BYTES = 1_000_000


class QualityResultError(ValueError):
    """Raised when a quality result violates the layered decision contract."""


def _object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise QualityResultError(f"{label} must contain exactly {sorted(keys)}")
    return value


def _text(value: Any, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise QualityResultError(f"{label} must be a non-empty string")
    return value


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise QualityResultError(f"{label} must be an array of non-empty strings")
    if len(value) != len(set(value)):
        raise QualityResultError(f"{label} must not contain duplicates")
    return value


def validate_data(data: Any) -> int:
    root = _object(data, ROOT_KEYS, "result")
    if root["schema_version"] != 1:
        raise QualityResultError("schema_version must equal 1")
    if not isinstance(root["run_valid"], bool):
        raise QualityResultError("run_valid must be Boolean")
    _text(root["run_reason"], "run_reason")

    gates = root["hard_gates"]
    if not isinstance(gates, list) or not gates:
        raise QualityResultError("hard_gates must be a non-empty array")
    gate_ids: set[str] = set()
    required_applicable = 0
    required_passed = 0
    evidence_items = 0
    for index, raw_gate in enumerate(gates):
        label = f"hard_gates[{index}]"
        gate = _object(raw_gate, GATE_KEYS, label)
        gate_id = _text(gate["id"], f"{label}.id")
        if ID_PATTERN.fullmatch(gate_id) is None or gate_id in gate_ids:
            raise QualityResultError(f"{label}.id must be unique lowercase kebab-case")
        gate_ids.add(gate_id)
        if not isinstance(gate["required"], bool) or not isinstance(gate["applicable"], bool):
            raise QualityResultError(f"{label}.required/applicable must be Boolean")
        status = gate["status"]
        if status not in GATE_STATUSES:
            raise QualityResultError(f"{label}.status is not recognized")
        evidence = _string_list(gate["evidence"], f"{label}.evidence")
        reason = _text(gate["reason"], f"{label}.reason", allow_empty=True)
        evidence_items += len(evidence)
        if gate["applicable"] and status == "NOT_APPLICABLE":
            raise QualityResultError(f"{label} is applicable but marked NOT_APPLICABLE")
        if not gate["applicable"] and status != "NOT_APPLICABLE":
            raise QualityResultError(f"{label} is not applicable and must be NOT_APPLICABLE")
        if not gate["applicable"] and not reason.strip():
            raise QualityResultError(f"{label} needs a reason for NOT_APPLICABLE")
        if status == "PASS" and not evidence:
            raise QualityResultError(f"{label} cannot PASS without evidence")
        if gate["required"] and gate["applicable"]:
            required_applicable += 1
            if status == "PASS":
                required_passed += 1

    derived_eligible = bool(root["run_valid"] and required_applicable == required_passed)
    if root["eligible"] is not derived_eligible:
        raise QualityResultError(
            "eligible must equal run_valid AND every required applicable hard gate PASS"
        )
    if root["weighted_total"] is not None:
        raise QualityResultError(
            "weighted_total must be null; evaluator-specific calibrated scores use a separate frozen policy"
        )

    coverage = _object(root["coverage"], COVERAGE_KEYS, "coverage")
    expected_coverage = {
        "required_applicable": required_applicable,
        "required_passed": required_passed,
        "evidence_items": evidence_items,
    }
    if coverage != expected_coverage:
        raise QualityResultError(f"coverage must equal derived values {expected_coverage}")

    craft = _object(root["craft"], CRAFT_KEYS, "craft")
    evaluator_id = _text(craft["evaluator_id"], "craft.evaluator_id", allow_empty=True)
    if not isinstance(craft["independent"], bool):
        raise QualityResultError("craft.independent must be Boolean")
    _text(craft["rubric_version"], "craft.rubric_version")
    dimensions = craft["dimensions"]
    if not isinstance(dimensions, list) or len(dimensions) != len(CRAFT_DIMENSIONS):
        raise QualityResultError("craft.dimensions must contain the complete dimension vector")
    dimension_ids: set[str] = set()
    any_judged = False
    for index, raw_dimension in enumerate(dimensions):
        label = f"craft.dimensions[{index}]"
        dimension = _object(raw_dimension, DIMENSION_KEYS, label)
        dimension_id = _text(dimension["id"], f"{label}.id")
        dimension_ids.add(dimension_id)
        status = dimension["status"]
        if status not in CRAFT_STATUSES:
            raise QualityResultError(f"{label}.status is not recognized")
        evidence = _string_list(dimension["evidence"], f"{label}.evidence")
        _text(dimension["uncertainty"], f"{label}.uncertainty")
        if status != "UNVERIFIED":
            any_judged = True
            if not evidence:
                raise QualityResultError(f"{label} cannot be judged without evidence")
    if dimension_ids != CRAFT_DIMENSIONS:
        raise QualityResultError("craft dimension inventory drift")
    if any_judged and (not craft["independent"] or not evaluator_id.strip()):
        raise QualityResultError("judged craft requires a named independent evaluator")

    award = root["award_lens"]
    if award is not None:
        award = _object(award, AWARD_KEYS, "award_lens")
        _text(award["program"], "award_lens.program")
        if award["status"] not in {"OBSERVED", "UNVERIFIED"}:
            raise QualityResultError("award_lens.status must be OBSERVED or UNVERIFIED")
        evidence = _string_list(award["evidence"], "award_lens.evidence")
        _text(award["boundary"], "award_lens.boundary")
        if award["status"] == "OBSERVED" and not evidence:
            raise QualityResultError("observed award lens requires evidence")

    if root["release"] not in RELEASE_STATUSES:
        raise QualityResultError("release is not recognized")
    if root["release"] == "VERIFIED" and not derived_eligible:
        raise QualityResultError("release cannot be VERIFIED while ineligible")

    handoff = _object(root["handoff"], HANDOFF_KEYS, "handoff")
    _text(handoff["artifact"], "handoff.artifact")
    _text(handoff["launch_command"], "handoff.launch_command")
    _string_list(handoff["remaining_risks"], "handoff.remaining_risks")
    _text(handoff["next_action"], "handoff.next_action")
    rendered = _object(handoff["rendered_evidence"], RENDERED_KEYS, "handoff.rendered_evidence")
    if rendered["status"] not in {"OBSERVED", "UNVERIFIED"}:
        raise QualityResultError("rendered evidence status must be OBSERVED or UNVERIFIED")
    paths = _string_list(rendered["paths"], "handoff.rendered_evidence.paths")
    reason = _text(
        rendered["reason"], "handoff.rendered_evidence.reason", allow_empty=True
    )
    if rendered["status"] == "OBSERVED" and not paths:
        raise QualityResultError("OBSERVED rendered evidence requires paths")
    if rendered["status"] == "UNVERIFIED" and not reason.strip():
        raise QualityResultError("UNVERIFIED rendered evidence requires a reason")
    if root["release"] == "VERIFIED" and rendered["status"] != "OBSERVED":
        raise QualityResultError("VERIFIED release requires OBSERVED rendered evidence")
    return len(gates)


def validate(path: Path) -> int:
    if path.is_symlink() or not path.is_file():
        raise QualityResultError(f"result must be a regular non-symlink file: {path}")
    try:
        if path.stat().st_size > MAX_INPUT_BYTES:
            raise QualityResultError("quality result exceeds size limit")
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise QualityResultError(f"cannot read valid JSON: {error}") from error
    return validate_data(data)


def _resolve_policy_reference(
    reference: str,
    claim_type: str,
    events: dict[str, dict[str, Any]],
    policy: dict[str, Any],
    artifact_root: Path,
) -> None:
    rules = policy["evidence"]
    candidates = {reference} if reference in rules else set()
    candidates.update(
        candidate
        for candidate, rule in rules.items()
        if rule.get("kind") == "artifact" and rule.get("path") == reference
    )
    if len(candidates) != 1:
        raise QualityResultError(
            f"evidence reference is not unambiguously evaluator-approved: {reference}"
        )

    label = next(iter(candidates))
    rule = rules[label]
    event = events.get(label)
    if claim_type == "rendered_visual":
        if rule.get("kind") != "artifact":
            raise QualityResultError(f"rendered evidence {label} must be an approved artifact")
        if rule.get("path") != reference:
            raise QualityResultError(
                f"rendered evidence must reference the approved artifact path: {reference}"
            )
    if rule.get("kind") == "command":
        failure = score_weak_model_output.evidence_failure(
            label,
            claim_type,
            "VERIFIED",
            event,
            rule,
            policy["run_id"],
            artifact_root,
        )
        if failure:
            raise QualityResultError(failure)
        return

    if event is None:
        raise QualityResultError(f"evidence label has no latest event: {label}")
    try:
        evidence_ledger.validate_event(event, policy["run_id"], label)
    except evidence_ledger.LedgerError as error:
        raise QualityResultError(f"evidence event is malformed: {error}") from error
    if claim_type not in rule.get("claim_types", []):
        raise QualityResultError(f"evidence label {label} cannot prove claim_type {claim_type}")
    if rule.get("kind") != "artifact" or event.get("kind") != "artifact":
        raise QualityResultError(f"evidence {label} must be an approved artifact")
    if event.get("exists") is not True:
        raise QualityResultError(f"evidence artifact is missing: {label}")
    if event.get("artifact_kind") != rule.get("artifact_kind"):
        raise QualityResultError(f"artifact kind does not match policy: {label}")
    if event.get("path") != rule.get("path"):
        raise QualityResultError(f"artifact path does not match policy: {label}")
    expected_context = rule.get("context", {})
    actual_context = event.get("context", {})
    if not isinstance(expected_context, dict) or not isinstance(actual_context, dict) or any(
        actual_context.get(key) != value for key, value in expected_context.items()
    ):
        raise QualityResultError(f"artifact context does not match policy: {label}")
    mismatch = evidence_ledger.verify_artifact_event(event, artifact_root)
    if mismatch:
        detail = mismatch or "artifact is absent"
        raise QualityResultError(f"evidence artifact is invalid: {label} ({detail})")


def validate_with_ledger(
    result_path: Path,
    ledger_path: Path,
    workspace_root: Path,
    required_gates: tuple[str, ...] = (),
    policy_path: Path | None = None,
) -> int:
    """Validate result structure and bind every positive claim to evaluator policy and facts."""

    count = validate(result_path)
    if policy_path is None:
        raise QualityResultError("completion validation requires an evaluator-owned evidence policy")
    workspace = workspace_root.expanduser().resolve(strict=True)
    if not workspace.is_dir() or workspace.is_symlink():
        raise QualityResultError("workspace root must be a real directory")
    ledger_file = ledger_path.expanduser().resolve(strict=True)
    result_file = result_path.expanduser().resolve(strict=True)
    try:
        result_file.relative_to(workspace)
    except ValueError as error:
        raise QualityResultError("quality result must remain inside the model-writable workspace") from error
    try:
        workspace.relative_to(ledger_file.parent)
    except ValueError as error:
        raise QualityResultError("workspace root must be a child of the evaluator-owned ledger root") from error
    try:
        ledger_file.relative_to(workspace)
    except ValueError:
        pass
    else:
        raise QualityResultError("evidence ledger must remain outside the model-writable workspace")

    data = json.loads(result_path.read_text(encoding="utf-8"))
    try:
        events, policy, artifact_root = score_weak_model_output.load_evaluator_context(
            ledger_file,
            policy_path,
            workspace,
            None,
            None,
        )
    except (ValueError, evidence_ledger.LedgerError) as error:
        raise QualityResultError(f"evaluator policy is invalid: {error}") from error
    if policy is None or artifact_root is None:
        raise QualityResultError("completion validation requires an evaluator-owned evidence policy")
    if data["release"] == "VERIFIED" and policy["release_acceptance"]["decision"] != "accepted_by_evaluator":
        raise QualityResultError("VERIFIED release requires evaluator acceptance in the evidence policy")

    gates = {gate["id"]: gate for gate in data["hard_gates"]}
    effective_required_gates = set(required_gates)
    if data["release"] == "VERIFIED":
        effective_required_gates.add("novel-discovery")
    missing_gates = sorted(effective_required_gates - set(gates))
    if missing_gates:
        raise QualityResultError(f"required hard gates are missing: {missing_gates}")
    for gate_id in effective_required_gates:
        gate = gates[gate_id]
        if not gate["required"] or not gate["applicable"] or gate["status"] != "PASS":
            raise QualityResultError(f"required hard gate did not pass: {gate_id}")

    references: list[tuple[str, str]] = []
    for gate in data["hard_gates"]:
        if gate["status"] == "PASS":
            references.extend((reference, f"gate:{gate['id']}") for reference in gate["evidence"])
    for dimension in data["craft"]["dimensions"]:
        if dimension["status"] != "UNVERIFIED":
            references.extend(
                (reference, f"craft:{dimension['id']}") for reference in dimension["evidence"]
            )
    award = data["award_lens"]
    if award is not None and award["status"] == "OBSERVED":
        references.extend((reference, "award-lens") for reference in award["evidence"])
    rendered = data["handoff"]["rendered_evidence"]
    if rendered["status"] == "OBSERVED":
        references.extend((path, "rendered_visual") for path in rendered["paths"])
    for reference, claim_type in dict.fromkeys(references):
        _resolve_policy_reference(
            reference,
            claim_type,
            events,
            policy,
            artifact_root,
        )
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--workspace-root", type=Path)
    parser.add_argument("--require-gate", action="append", default=[])
    parser.add_argument(
        "--structure-only",
        action="store_true",
        help="validate the legacy JSON shape without accepting its evidence claims",
    )
    args = parser.parse_args(argv)
    try:
        if args.structure_only:
            if args.ledger is not None or args.policy is not None or args.workspace_root is not None or args.require_gate:
                raise QualityResultError("--structure-only cannot be combined with evidence options")
            count = validate(args.result.expanduser())
            print(f"quality result structure valid: {count} hard gates; evidence not checked")
            return 0
        if args.ledger is None or args.policy is None or args.workspace_root is None:
            raise QualityResultError(
                "completion validation requires --ledger, --policy, and --workspace-root; "
                "use --structure-only only for legacy shape checks"
            )
        count = validate_with_ledger(
            args.result.expanduser(),
            args.ledger,
            args.workspace_root,
            tuple(args.require_gate),
            args.policy,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, QualityResultError) as error:
        print(f"quality result invalid: {error}", file=sys.stderr)
        return 1
    print(f"quality result valid with bound evidence: {count} hard gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
