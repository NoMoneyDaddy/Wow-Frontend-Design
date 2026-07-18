#!/usr/bin/env python3
"""Conservative affected-matrix selection and repair-artifact ranking for v7."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class V7RepairPolicyError(ValueError):
    """Raised when a repair policy input cannot support a bounded decision."""


KNOWN_ISSUE_CLASSES = {"composition", "interaction", "runtime"}
ROW_FIELDS = ("variant", "case_id", "state", "profile", "engine")
SUPPORT_CONTRACT = {
    "schema_version": 2,
    "scope": "target-root",
    "target_inventory": ["DESIGN.md", "index.html", "run-manifest.json"],
    "rendered_entry": "index.html",
    "isolation": {
        "capture": "opaque-copy-single-entry",
        "external_requests": "blocked-and-reported",
        "shared_runtime_files": False,
    },
    "issue_scope": {
        "composition": "target-full-on-rendered-change",
        "interaction": "target-full-on-rendered-change",
        "runtime": "target-full-on-rendered-change",
        "unknown": "cohort-full",
    },
}
SUPPORT_DEPENDENCY_PATHS = (
    "evals/v7_a1_typography_metrics.cjs",
    "evals/v7_focus_obscuration.cjs",
    "evals/v7_accessible_name.cjs",
    "evals/v7_dialog_focus.cjs",
    "evals/v7_disclosure_state.cjs",
    "evals/v7_invalid_feedback.cjs",
    "evals/v7_invalid_input_preservation.cjs",
    "evals/v7_stale_completion.cjs",
)


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_support_contract(path: Path, repository_root: Path) -> str:
    """Bind target isolation to frozen capture, auditor, and direct dependency bytes."""
    root = repository_root.resolve(strict=True)
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 64 * 1024:
        raise V7RepairPolicyError("repair support contract is missing, unsafe or oversized")
    try:
        resolved_contract = path.resolve(strict=True)
        resolved_contract.relative_to(root)
    except (OSError, ValueError) as error:
        raise V7RepairPolicyError("repair support contract escapes the repository") from error
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise V7RepairPolicyError(f"cannot read repair support contract: {error}") from error
    if not isinstance(value, dict) or set(value) != set(SUPPORT_CONTRACT) | {"capture_module", "auditor", "dependencies"}:
        raise V7RepairPolicyError("repair support contract schema changed")
    for key, expected in SUPPORT_CONTRACT.items():
        if value.get(key) != expected:
            raise V7RepairPolicyError(f"repair support contract changed: {key}")
    dependencies = value.get("dependencies")
    if (
        not isinstance(dependencies, list)
        or [record.get("path") for record in dependencies if isinstance(record, dict)]
        != list(SUPPORT_DEPENDENCY_PATHS)
    ):
        raise V7RepairPolicyError("repair support dependency inventory changed")
    for label, record in (
        ("capture_module", value.get("capture_module")),
        ("auditor", value.get("auditor")),
        *((f"dependency[{index}]", record) for index, record in enumerate(dependencies)),
    ):
        if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
            raise V7RepairPolicyError(f"repair support {label} binding is malformed")
        raw = record.get("path")
        if not isinstance(raw, str) or not raw or raw.startswith("/") or ".." in Path(raw).parts:
            raise V7RepairPolicyError(f"repair support {label} path is unsafe")
        candidate = root / raw
        current = root
        for part in Path(raw).parts:
            current = current / part
            if current.is_symlink():
                raise V7RepairPolicyError(f"repair support {label} path traverses a symlink")
        dependency = candidate.resolve(strict=True)
        try:
            dependency.relative_to(root)
        except ValueError as error:
            raise V7RepairPolicyError(f"repair support {label} escapes the repository") from error
        if dependency.is_symlink() or not dependency.is_file() or _file_sha256(dependency) != record["sha256"]:
            raise V7RepairPolicyError(f"repair support {label} binding is stale")
    return _file_sha256(path)


def _row(value: dict[str, Any], label: str) -> tuple[str, str, str, str, str]:
    if not isinstance(value, dict) or any(not isinstance(value.get(field), str) for field in ROW_FIELDS):
        raise V7RepairPolicyError(f"{label} is malformed")
    return tuple(value[field] for field in ROW_FIELDS)  # type: ignore[return-value]


def _output_map(receipt: dict[str, Any], label: str) -> dict[str, dict[str, Any]]:
    outputs = receipt.get("outputs") if isinstance(receipt, dict) else None
    if not isinstance(outputs, list) or len(outputs) != 2:
        raise V7RepairPolicyError(f"{label} output receipt is malformed")
    mapped = {
        item.get("path"): item
        for item in outputs
        if isinstance(item, dict) and set(item) == {"path", "bytes", "sha256"}
    }
    if set(mapped) != {"DESIGN.md", "index.html"}:
        raise V7RepairPolicyError(f"{label} output receipt is incomplete")
    return mapped


def select_affected_rows(
    target: dict[str, Any],
    source_receipt: dict[str, Any],
    repaired_receipt: dict[str, Any],
    full_inventory: list[tuple[str, str, str, str, str]],
    *,
    target_isolated: bool,
    support_contract_sha256: str | None = None,
) -> dict[str, Any]:
    """Select only a mechanically justified subset of the frozen full matrix."""
    identity = (target.get("variant"), target.get("case_id"))
    if any(not isinstance(value, str) for value in identity):
        raise V7RepairPolicyError("repair target identity is malformed")
    if target_isolated and (
        not isinstance(support_contract_sha256, str)
        or len(support_contract_sha256) != 64
        or any(character not in "0123456789abcdef" for character in support_contract_sha256)
    ):
        raise V7RepairPolicyError("target isolation lacks a frozen support contract")
    inventory = sorted(set(full_inventory))
    if not inventory or len(inventory) != len(full_inventory):
        raise V7RepairPolicyError("declared full matrix is empty or duplicated")
    occurrences = target.get("occurrences")
    if not isinstance(occurrences, list) or not occurrences:
        raise V7RepairPolicyError("repair target has no validated occurrences")
    original_rows = sorted({
        (identity[0], identity[1], occurrence.get("state"), occurrence.get("profile"), occurrence.get("engine"))
        for occurrence in occurrences
        if isinstance(occurrence, dict)
    })
    if (
        not original_rows
        or any(any(not isinstance(value, str) for value in row) for row in original_rows)
        or any(row not in inventory for row in original_rows)
    ):
        raise V7RepairPolicyError("original failure rows are outside the declared full matrix")
    issue_class_values: set[Any] = set()
    for occurrence in occurrences:
        findings = occurrence.get("findings") if isinstance(occurrence, dict) else None
        if not isinstance(findings, list):
            raise V7RepairPolicyError("repair occurrence findings are malformed")
        for finding in findings:
            if not isinstance(finding, dict):
                raise V7RepairPolicyError("repair finding is malformed")
            issue_class_values.add(finding.get("classification"))
    issue_classes = sorted(value for value in issue_class_values if isinstance(value, str))
    if len(issue_classes) != len(issue_class_values):
        issue_classes.append("<invalid>")
    source_outputs = _output_map(source_receipt, "source")
    repaired_outputs = _output_map(repaired_receipt, "repaired")
    changed_files = sorted(
        name for name in source_outputs if source_outputs[name] != repaired_outputs[name]
    )
    target_rows = [row for row in inventory if row[:2] == identity]
    fallback_reason = None
    if not issue_classes or any(value not in KNOWN_ISSUE_CLASSES for value in issue_classes):
        selected = inventory
        decision = "cohort-full-matrix"
        fallback_reason = "unknown-issue-class"
    elif "index.html" not in changed_files:
        selected = original_rows
        decision = "original-failure-rows"
    elif target_isolated and target_rows:
        selected = target_rows
        decision = "target-full-matrix"
    else:
        selected = inventory
        decision = "cohort-full-matrix"
        fallback_reason = "target-isolation-unproven"
    if any(row not in inventory for row in selected) or any(row not in selected for row in original_rows):
        raise V7RepairPolicyError("affected selection escaped or omitted the declared matrix")
    diff_record = {
        "changed_files": changed_files,
        "classification": (
            "rendered-surface" if "index.html" in changed_files else
            "documentation-only" if changed_files else "byte-identical"
        ),
        "sha256": _canonical_sha256({
            "source": source_outputs,
            "repaired": repaired_outputs,
        }),
    }
    return {
        "schema_version": 1,
        "target": list(identity),
        "source_outputs": [source_outputs[name] for name in sorted(source_outputs)],
        "repaired_outputs": [repaired_outputs[name] for name in sorted(repaired_outputs)],
        "source_receipt_sha256": _canonical_sha256(source_receipt),
        "repaired_receipt_sha256": _canonical_sha256(repaired_receipt),
        "diff": diff_record,
        "issue_classes": issue_classes,
        "original_failure_rows": [list(row) for row in original_rows],
        "selected_rows": [list(row) for row in selected],
        "selected_rows_sha256": _canonical_sha256([list(row) for row in selected]),
        "declared_matrix_sha256": _canonical_sha256([list(row) for row in inventory]),
        "support_contract_sha256": support_contract_sha256,
        "decision": decision,
        "fallback_reason": fallback_reason,
    }


def verify_selector_binding(
    selector: dict[str, Any],
    identity: tuple[str, str],
    current_receipt: dict[str, Any],
    full_inventory: list[tuple[str, str, str, str, str]],
    support_contract_sha256: str | None,
) -> dict[str, Any]:
    """Verify that an accepted selector still names the current artifact and frozen rows."""
    expected_keys = {
        "schema_version", "target", "source_outputs", "repaired_outputs",
        "source_receipt_sha256", "repaired_receipt_sha256", "diff", "issue_classes",
        "original_failure_rows", "selected_rows", "selected_rows_sha256",
        "declared_matrix_sha256", "support_contract_sha256", "decision", "fallback_reason",
    }
    if not isinstance(selector, dict) or set(selector) != expected_keys or selector.get("schema_version") != 1:
        raise V7RepairPolicyError("accepted selector schema changed")
    if selector.get("target") != list(identity):
        raise V7RepairPolicyError("accepted selector target changed")
    inventory = sorted(set(full_inventory))
    inventory_lists = [list(row) for row in inventory]
    if (
        not inventory
        or len(inventory) != len(full_inventory)
        or selector.get("declared_matrix_sha256") != _canonical_sha256(inventory_lists)
    ):
        raise V7RepairPolicyError("accepted selector declared matrix changed")
    selected_raw = selector.get("selected_rows")
    original_raw = selector.get("original_failure_rows")
    if not isinstance(selected_raw, list) or not isinstance(original_raw, list):
        raise V7RepairPolicyError("accepted selector rows are malformed")
    if any(
        not isinstance(value, list)
        or len(value) != 5
        or any(not isinstance(part, str) for part in value)
        for value in selected_raw + original_raw
    ):
        raise V7RepairPolicyError("accepted selector rows are malformed")
    selected = [tuple(value) for value in selected_raw]
    original = [tuple(value) for value in original_raw]
    if (
        not selected
        or len(selected) != len(set(selected))
        or any(len(row) != 5 or row not in inventory for row in selected)
        or any(row not in selected for row in original)
        or selector.get("selected_rows_sha256") != _canonical_sha256(selected_raw)
    ):
        raise V7RepairPolicyError("accepted selector rows changed or escaped the matrix")
    decision = selector.get("decision")
    changed_files = selector.get("diff", {}).get("changed_files") if isinstance(selector.get("diff"), dict) else None
    if not isinstance(changed_files, list) or any(value not in {"DESIGN.md", "index.html"} for value in changed_files):
        raise V7RepairPolicyError("accepted selector diff changed")
    target_rows = [row for row in inventory if row[:2] == identity]
    if decision == "target-full-matrix":
        if support_contract_sha256 is None or selector.get("support_contract_sha256") != support_contract_sha256:
            raise V7RepairPolicyError("accepted target selector lost its support contract")
        if sorted(selected) != target_rows:
            raise V7RepairPolicyError("accepted target selector is incomplete")
        if "index.html" not in changed_files:
            raise V7RepairPolicyError("accepted target selector has no rendered diff")
    elif decision == "cohort-full-matrix":
        if sorted(selected) != inventory:
            raise V7RepairPolicyError("accepted cohort selector is incomplete")
    elif decision == "original-failure-rows":
        if sorted(selected) != sorted(original):
            raise V7RepairPolicyError("accepted original-row selector expanded inconsistently")
        if "index.html" in changed_files:
            raise V7RepairPolicyError("accepted original-row selector hides a rendered diff")
    else:
        raise V7RepairPolicyError("accepted selector decision changed")
    if selector.get("repaired_receipt_sha256") != _canonical_sha256(current_receipt):
        raise V7RepairPolicyError("accepted selector artifact receipt is stale")
    outputs = _output_map(current_receipt, "current")
    if selector.get("repaired_outputs") != [outputs[name] for name in sorted(outputs)]:
        raise V7RepairPolicyError("accepted selector output receipt is stale")
    return {
        "target": list(identity),
        "decision": decision,
        "artifact_receipt_sha256": _canonical_sha256(current_receipt),
        "declared_matrix_sha256": selector["declared_matrix_sha256"],
        "selected_rows_sha256": selector["selected_rows_sha256"],
        "selected_row_count": len(selected),
        "support_contract_sha256": selector["support_contract_sha256"],
    }


def _finding_records(target: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if target is None:
        return {}
    records: dict[str, dict[str, Any]] = {}
    occurrences = target.get("occurrences")
    if not isinstance(occurrences, list):
        raise V7RepairPolicyError("rank target occurrences are malformed")
    for occurrence in occurrences:
        if not isinstance(occurrence, dict) or not isinstance(occurrence.get("findings"), list):
            raise V7RepairPolicyError("rank occurrence is malformed")
        row = {field: occurrence.get(field) for field in ("state", "profile", "engine")}
        if any(not isinstance(value, str) for value in row.values()):
            raise V7RepairPolicyError("rank occurrence identity is malformed")
        for finding in occurrence["findings"]:
            if (
                not isinstance(finding, dict)
                or finding.get("classification") not in KNOWN_ISSUE_CLASSES
                or not isinstance(finding.get("code"), str)
                or not isinstance(finding.get("locator"), str)
            ):
                raise V7RepairPolicyError("rank finding is malformed")
            record = {
                **row,
                "classification": finding["classification"],
                "code": finding["code"],
                "locator": finding["locator"],
            }
            records[_canonical_sha256(record)] = record
    return records


def artifact_rank(
    baseline_target: dict[str, Any],
    candidate_target: dict[str, Any] | None,
    *,
    changed_bytes: int,
    artifact_sha256: str,
) -> tuple[Any, ...]:
    """Return a stable lexicographic rank; lower is better and hard regressions lead."""
    if (
        changed_bytes < 0
        or not isinstance(artifact_sha256, str)
        or len(artifact_sha256) != 64
        or any(character not in "0123456789abcdef" for character in artifact_sha256)
    ):
        raise V7RepairPolicyError("artifact rank provenance is malformed")
    baseline = _finding_records(baseline_target)
    candidate = _finding_records(candidate_target)
    baseline_keys = set(baseline)
    candidate_keys = set(candidate)

    def count(keys: set[str], classification: str) -> int:
        return sum(candidate[key]["classification"] == classification for key in keys)

    new_keys = candidate_keys - baseline_keys
    unresolved = candidate_keys & baseline_keys
    return (
        count(new_keys, "interaction"),
        count(new_keys, "runtime"),
        count(unresolved, "interaction"),
        count(unresolved, "runtime"),
        count(new_keys, "composition"),
        len(unresolved),
        count(candidate_keys, "interaction"),
        count(candidate_keys, "runtime"),
        count(candidate_keys, "composition"),
        changed_bytes,
        artifact_sha256,
    )


def is_strict_improvement(candidate: tuple[Any, ...], incumbent: tuple[Any, ...]) -> bool:
    """Require deterministic quality improvement; bytes and digest are receipt-only ties."""
    if len(candidate) != 11 or len(incumbent) != 11:
        raise V7RepairPolicyError("artifact rank vector changed")
    return candidate[:-2] < incumbent[:-2]


def rank_receipt(rank: tuple[Any, ...]) -> dict[str, Any]:
    if len(rank) != 11:
        raise V7RepairPolicyError("artifact rank vector changed")
    return {
        "schema_version": 1,
        "ordering": [
            "new_interaction", "new_runtime", "unresolved_interaction", "unresolved_runtime",
            "new_composition", "unresolved_original", "interaction_residual", "runtime_residual",
            "composition_residual", "changed_bytes", "artifact_sha256",
        ],
        "vector": list(rank),
    }
