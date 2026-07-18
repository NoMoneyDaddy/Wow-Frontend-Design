#!/usr/bin/env python3
"""Compile validated v7 Playwright findings into a bounded repair packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "wow-frontend-design" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import validate_v7_evidence as evidence  # noqa: E402


MAX_PACKET_BYTES = 256 * 1024
MAX_FINDINGS_PER_TARGET = 64
MAX_FEEDBACK_CHARS = 500
ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
TYPOGRAPHY_CODES = {
    "a1_heading_han_orphan",
    "a1_heading_track_void",
    "a1_layout_column_void",
    "a1_prose_han_orphan",
    "a1_prose_track_void",
    "a1_required_text_clipped",
    "a1_target_contract_unresolved",
}
RUNTIME_CODES = {
    "accessible_name_verification_unavailable",
    "declared_control_accessible_name_mismatch",
    "declared_dialog_focus_lifecycle_mismatch",
    "dialog_focus_verification_unavailable",
    "declared_invalid_feedback_unlinked",
    "invalid_feedback_verification_unavailable",
    "declared_invalid_input_lost",
    "invalid_input_preservation_unavailable",
    "external_requests",
    "focus_obscuration_verification_unavailable",
    "focused_control_obscured",
    "fonts_not_ready",
    "interaction_assertion_failed",
    "page_capture_area_exceeded",
    "page_errors",
    "page_horizontal_overflow",
    "runtime_event_limit_exceeded",
    "stale_async_completion",
    "stale_completion_verification_unavailable",
    "console_errors",
}
NUMERIC_EVIDENCE = {
    "lineCount",
    "trackRatio",
    "inlineStartGap",
    "inlineEndGap",
    "ownerWidth",
    "trackWidth",
    "nodeCount",
    "ownerCount",
    "voidHeight",
    "threshold",
    "ownerHeight",
    "peerHeight",
    "parentWidth",
    "count",
}


class RepairPacketError(ValueError):
    """Raised when validated evidence cannot safely become repair feedback."""


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 4 * 1024 * 1024:
        raise RepairPacketError(f"{label} is missing, unsafe or oversized")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RepairPacketError(f"cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise RepairPacketError(f"{label} root must be an object")
    return value


def _record_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or ID_PATTERN.fullmatch(value) is None:
        raise RepairPacketError(f"{label} must be lowercase kebab-case")
    return value


def _safe_route(value: Any) -> str:
    if not isinstance(value, str) or "\x00" in value or "\\" in value:
        raise RepairPacketError("result route is invalid")
    route = PurePosixPath(value)
    if route.is_absolute() or not route.parts or "." in route.parts or ".." in route.parts:
        raise RepairPacketError("result route is unsafe")
    if route.suffix.lower() not in {".html", ".htm"}:
        raise RepairPacketError("result route is not an HTML document")
    return route.as_posix()


def _bounded_number(value: Any, label: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise RepairPacketError(f"{label} must be a finite number")
    if abs(value) > 10_000_000:
        raise RepairPacketError(f"{label} exceeds the repair evidence bound")
    return value if isinstance(value, int) else round(value, 4)


def _measurement(issue: dict[str, Any], code: str) -> dict[str, int | float | str]:
    source = issue.get("measurement")
    if source is None:
        source = issue
    if not isinstance(source, dict):
        raise RepairPacketError("typography issue measurement is malformed")
    selected: dict[str, int | float | str] = {}
    for name in NUMERIC_EVIDENCE:
        if name in source:
            selected[name] = _bounded_number(source[name], f"measurement.{name}")
    column_void = source.get("columnVoid")
    if column_void is not None:
        if not isinstance(column_void, dict):
            raise RepairPacketError("column void measurement is malformed")
        for name in ("voidHeight", "threshold", "ownerHeight", "peerHeight", "parentWidth"):
            if name in column_void:
                selected[name] = _bounded_number(column_void[name], f"columnVoid.{name}")
        for name in ("source", "parentDisplay"):
            value = column_void.get(name)
            if value is not None:
                allowed = {"owner", "target"} if name == "source" else {
                    "grid", "inline-grid", "flex", "inline-flex",
                }
                if value not in allowed:
                    raise RepairPacketError(f"columnVoid.{name} is invalid")
                selected[name] = value
    if code == "a1_required_text_clipped":
        completeness = source.get("textCompleteness")
        required_keys = {
            "status", "reason", "mechanism", "tolerance", "inlineDelta",
            "blockDelta", "graphemeCount", "outsideRectCount",
        }
        if not isinstance(completeness, dict) or set(completeness) != required_keys:
            raise RepairPacketError("text completeness measurement is malformed")
        mechanism = completeness.get("mechanism")
        if (
            completeness.get("status") != "clipped"
            or completeness.get("reason") != "direct_text_outside_client_box"
            or mechanism not in {"inline_ellipsis", "inline_clip", "line_clamp", "block_clip"}
        ):
            raise RepairPacketError("text completeness finding is inconsistent")
        tolerance = _bounded_number(completeness.get("tolerance"), "textCompleteness.tolerance")
        inline_delta = _bounded_number(completeness.get("inlineDelta"), "textCompleteness.inlineDelta")
        block_delta = _bounded_number(completeness.get("blockDelta"), "textCompleteness.blockDelta")
        grapheme_count = _bounded_number(completeness.get("graphemeCount"), "textCompleteness.graphemeCount")
        outside_count = _bounded_number(completeness.get("outsideRectCount"), "textCompleteness.outsideRectCount")
        if (
            tolerance <= 0
            or inline_delta < 0
            or block_delta < 0
            or type(grapheme_count) is not int
            or not 1 <= grapheme_count <= 4096
            or type(outside_count) is not int
            or not 1 <= outside_count <= 4096
        ):
            raise RepairPacketError("text completeness bounds are invalid")
        axis = "inline" if mechanism in {"inline_ellipsis", "inline_clip"} else "block"
        relevant_delta = inline_delta if axis == "inline" else block_delta
        if relevant_delta <= tolerance:
            raise RepairPacketError("text completeness delta does not exceed tolerance")
        selected.update({
            "clipAxis": axis,
            "clipMechanism": mechanism,
            "inlineDelta": inline_delta,
            "blockDelta": block_delta,
            "tolerance": tolerance,
            "outsideRectCount": outside_count,
        })
    return dict(sorted(selected.items()))


def _finding(code: str, classification: str, locator: str, values: dict[str, Any]) -> dict[str, Any]:
    return {
        "code": code,
        "classification": classification,
        "locator": _record_id(locator, "finding locator"),
        "evidence": values,
    }


def extract_findings(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Project a validated result onto a prompt-safe, actionable finding set."""
    runtime = result.get("runtime")
    typography = result.get("typography")
    if not isinstance(runtime, dict) or not isinstance(typography, dict):
        raise RepairPacketError("result runtime or typography evidence is malformed")
    findings: list[dict[str, Any]] = []
    for issue in typography.get("issues", []):
        if not isinstance(issue, dict) or set(issue).difference({"code", "targetId", "measurement", "nodeCount", "ownerCount"}):
            raise RepairPacketError("typography issue contract changed")
        code = issue.get("code")
        if code not in TYPOGRAPHY_CODES:
            raise RepairPacketError(f"unknown typography issue code: {code!r}")
        if code == "a1_target_contract_unresolved":
            raise RepairPacketError(
                "unresolved hidden target is an evaluator contract defect, not an automatic product repair"
            )
        findings.append(_finding(code, "composition", issue.get("targetId"), _measurement(issue, code)))

    runtime_issues = runtime.get("issues", [])
    if not isinstance(runtime_issues, list):
        raise RepairPacketError("runtime issue inventory is malformed")
    for code in runtime_issues:
        if code not in RUNTIME_CODES:
            raise RepairPacketError(f"unknown runtime issue code: {code!r}")
        if code == "focus_obscuration_verification_unavailable":
            raise RepairPacketError("focus obscuration verification is unavailable, not a product repair")
        if code == "accessible_name_verification_unavailable":
            raise RepairPacketError("accessible name verification is unavailable, not a product repair")
        if code == "dialog_focus_verification_unavailable":
            raise RepairPacketError("dialog focus verification is unavailable, not a product repair")
        if code == "invalid_feedback_verification_unavailable":
            raise RepairPacketError("invalid feedback verification is unavailable, not a product repair")
        if code == "invalid_input_preservation_unavailable":
            raise RepairPacketError("invalid input preservation verification is unavailable, not a product repair")
        if code == "stale_completion_verification_unavailable":
            raise RepairPacketError("stale completion verification is unavailable, not a product repair")
        if code in {
            "focused_control_obscured", "stale_async_completion", "declared_control_accessible_name_mismatch",
            "declared_dialog_focus_lifecycle_mismatch", "declared_invalid_feedback_unlinked", "declared_invalid_input_lost",
        }:
            continue
        findings.append(_finding(code, "runtime", "page", {}))
    focused_controls = runtime.get("focusedControls", [])
    if not isinstance(focused_controls, list):
        raise RepairPacketError("focused control evidence is malformed")
    confirmed_focus = []
    for record in focused_controls:
        if not isinstance(record, dict):
            raise RepairPacketError("focused control record is malformed")
        if record.get("status") != "confirmed":
            continue
        confirmed_focus.append(record)
        findings.append(_finding("focused_control_obscured", "runtime", record.get("id"), {
            "occluderCount": _bounded_number(record.get("occluderCount"), "focusedControl.occluderCount"),
            "targetArea": _bounded_number(record.get("targetArea"), "focusedControl.targetArea"),
            "coveredArea": _bounded_number(record.get("coveredArea"), "focusedControl.coveredArea"),
        }))
    if ("focused_control_obscured" in runtime_issues) != bool(confirmed_focus):
        raise RepairPacketError("focused control issue and evidence disagree")
    accessible_name_controls = runtime.get("accessibleNameControls", [])
    if not isinstance(accessible_name_controls, list):
        raise RepairPacketError("accessible name control evidence is malformed")
    accessible_name_roles = {"textbox", "searchbox", "spinbutton", "combobox", "listbox"}
    accessible_name_unavailable_reasons = {
        "accessibility_tree_unavailable",
        "control_not_rendered",
        "external_request_blocked",
        "replay_unstable",
        "runtime_unavailable",
    }
    confirmed_accessible_names = []
    unavailable_accessible_names = []
    for record in accessible_name_controls:
        if not isinstance(record, dict):
            raise RepairPacketError("accessible name control record is malformed")
        status = record.get("status")
        expected_keys = {"id", "role", "status", "replays"}
        if status == "unavailable":
            expected_keys.add("reason")
        if set(record) != expected_keys or record.get("role") not in accessible_name_roles or record.get("replays") != 2:
            raise RepairPacketError("accessible name control evidence is inconsistent")
        _record_id(record.get("id"), "accessible name control id")
        if status == "unavailable":
            if record.get("reason") not in accessible_name_unavailable_reasons:
                raise RepairPacketError("accessible name unavailable reason is invalid")
            unavailable_accessible_names.append(record)
            continue
        if status == "clear":
            continue
        if status != "confirmed":
            raise RepairPacketError("accessible name control status is invalid")
        confirmed_accessible_names.append(record)
        findings.append(_finding("declared_control_accessible_name_mismatch", "runtime", record["id"], {
            "role": record["role"],
        }))
    if ("declared_control_accessible_name_mismatch" in runtime_issues) != bool(confirmed_accessible_names):
        raise RepairPacketError("accessible name issue and evidence disagree")
    if ("accessible_name_verification_unavailable" in runtime_issues) != bool(unavailable_accessible_names):
        raise RepairPacketError("accessible name unavailable issue and evidence disagree")
    if unavailable_accessible_names:
        raise RepairPacketError("accessible name verification is unavailable, not a product repair")
    dialog_focus_lifecycles = runtime.get("dialogFocusLifecycles", [])
    if not isinstance(dialog_focus_lifecycles, list):
        raise RepairPacketError("dialog focus lifecycle evidence is malformed")
    dialog_focus_unavailable_reasons = {
        "dialog_contract_unavailable",
        "external_request_blocked",
        "replay_unstable",
        "runtime_unavailable",
    }
    confirmed_dialog_focus = []
    unavailable_dialog_focus = []
    for record in dialog_focus_lifecycles:
        if not isinstance(record, dict):
            raise RepairPacketError("dialog focus lifecycle record is malformed")
        status = record.get("status")
        expected_keys = {"id", "status", "replays", "openFocus", "returnFocus"}
        if status == "unavailable":
            expected_keys = {"id", "status", "replays", "reason"}
        if set(record) != expected_keys or record.get("replays") != 2:
            raise RepairPacketError("dialog focus lifecycle evidence is inconsistent")
        _record_id(record.get("id"), "dialog focus lifecycle id")
        if status == "unavailable":
            if record.get("reason") not in dialog_focus_unavailable_reasons:
                raise RepairPacketError("dialog focus unavailable reason is invalid")
            unavailable_dialog_focus.append(record)
            continue
        if status not in {"clear", "confirmed"} or type(record.get("openFocus")) is not bool or type(record.get("returnFocus")) is not bool:
            raise RepairPacketError("dialog focus lifecycle status is invalid")
        if (status == "clear") != (record["openFocus"] and record["returnFocus"]):
            raise RepairPacketError("dialog focus lifecycle derivation is inconsistent")
        if status == "confirmed":
            confirmed_dialog_focus.append(record)
            findings.append(_finding("declared_dialog_focus_lifecycle_mismatch", "runtime", record["id"], {
                "openFocus": record["openFocus"], "returnFocus": record["returnFocus"],
            }))
    if ("declared_dialog_focus_lifecycle_mismatch" in runtime_issues) != bool(confirmed_dialog_focus):
        raise RepairPacketError("dialog focus issue and evidence disagree")
    if ("dialog_focus_verification_unavailable" in runtime_issues) != bool(unavailable_dialog_focus):
        raise RepairPacketError("dialog focus unavailable issue and evidence disagree")
    if unavailable_dialog_focus:
        raise RepairPacketError("dialog focus verification is unavailable, not a product repair")
    invalid_feedback_targets = runtime.get("invalidFeedbackTargets", [])
    if not isinstance(invalid_feedback_targets, list):
        raise RepairPacketError("invalid feedback evidence is malformed")
    invalid_feedback_unavailable_reasons = {
        "feedback_contract_unavailable",
        "external_request_blocked",
        "replay_unstable",
        "runtime_unavailable",
    }
    confirmed_invalid_feedback = []
    unavailable_invalid_feedback = []
    for record in invalid_feedback_targets:
        if not isinstance(record, dict):
            raise RepairPacketError("invalid feedback record is malformed")
        status = record.get("status")
        expected_keys = {"id", "status", "replays", "relation"}
        if status == "unavailable":
            expected_keys = {"id", "status", "replays", "reason"}
        if set(record) != expected_keys or record.get("replays") != 2:
            raise RepairPacketError("invalid feedback evidence is inconsistent")
        _record_id(record.get("id"), "invalid feedback target id")
        if status == "unavailable":
            if record.get("reason") not in invalid_feedback_unavailable_reasons:
                raise RepairPacketError("invalid feedback unavailable reason is invalid")
            unavailable_invalid_feedback.append(record)
            continue
        relation = record.get("relation")
        if status not in {"clear", "confirmed"} or relation not in {"describedby", "errormessage", "both", "missing"}:
            raise RepairPacketError("invalid feedback status is invalid")
        if (status == "confirmed") != (relation == "missing"):
            raise RepairPacketError("invalid feedback derivation is inconsistent")
        if status == "confirmed":
            confirmed_invalid_feedback.append(record)
            findings.append(_finding("declared_invalid_feedback_unlinked", "runtime", record["id"], {"relation": "missing"}))
    if ("declared_invalid_feedback_unlinked" in runtime_issues) != bool(confirmed_invalid_feedback):
        raise RepairPacketError("invalid feedback issue and evidence disagree")
    if ("invalid_feedback_verification_unavailable" in runtime_issues) != bool(unavailable_invalid_feedback):
        raise RepairPacketError("invalid feedback unavailable issue and evidence disagree")
    if unavailable_invalid_feedback:
        raise RepairPacketError("invalid feedback verification is unavailable, not a product repair")
    invalid_input_targets = runtime.get("invalidInputPreservationTargets", [])
    if not isinstance(invalid_input_targets, list):
        raise RepairPacketError("invalid input preservation evidence is malformed")
    invalid_input_unavailable_reasons = {
        "preservation_contract_unavailable",
        "external_request_blocked",
        "replay_unstable",
        "runtime_unavailable",
    }
    invalid_input_native_kinds = {
        "input-text", "input-search", "input-email", "input-tel", "input-url", "input-number", "textarea", "select-one",
    }
    confirmed_invalid_input = []
    unavailable_invalid_input = []
    for record in invalid_input_targets:
        if not isinstance(record, dict):
            raise RepairPacketError("invalid input preservation record is malformed")
        status = record.get("status")
        expected_keys = {"id", "status", "replays", "nativeKind", "retained"}
        if status == "unavailable":
            expected_keys = {"id", "status", "replays", "reason"}
        if set(record) != expected_keys or record.get("replays") != 2:
            raise RepairPacketError("invalid input preservation evidence is inconsistent")
        _record_id(record.get("id"), "invalid input preservation target id")
        if status == "unavailable":
            if record.get("reason") not in invalid_input_unavailable_reasons:
                raise RepairPacketError("invalid input preservation unavailable reason is invalid")
            unavailable_invalid_input.append(record)
            continue
        native_kind = record.get("nativeKind")
        retained = record.get("retained")
        if status not in {"clear", "confirmed"} or native_kind not in invalid_input_native_kinds or type(retained) is not bool:
            raise RepairPacketError("invalid input preservation status is invalid")
        if (status == "confirmed") != (retained is False):
            raise RepairPacketError("invalid input preservation derivation is inconsistent")
        if status == "confirmed":
            confirmed_invalid_input.append(record)
            findings.append(_finding("declared_invalid_input_lost", "runtime", record["id"], {
                "nativeKind": native_kind, "retained": False,
            }))
    if ("declared_invalid_input_lost" in runtime_issues) != bool(confirmed_invalid_input):
        raise RepairPacketError("invalid input preservation issue and evidence disagree")
    if ("invalid_input_preservation_unavailable" in runtime_issues) != bool(unavailable_invalid_input):
        raise RepairPacketError("invalid input preservation unavailable issue and evidence disagree")
    if unavailable_invalid_input:
        raise RepairPacketError("invalid input preservation verification is unavailable, not a product repair")
    async_completions = runtime.get("asyncCompletions", [])
    if not isinstance(async_completions, list):
        raise RepairPacketError("async completion evidence is malformed")
    confirmed_async = []
    for record in async_completions:
        if not isinstance(record, dict):
            raise RepairPacketError("async completion record is malformed")
        if record.get("status") != "confirmed":
            continue
        if record.get("staleCompletion") is not True or record.get("mainReplay") != "stale" or record.get("freshReplay") != "stale":
            raise RepairPacketError("confirmed stale completion evidence is inconsistent")
        confirmed_async.append(record)
        findings.append(_finding("stale_async_completion", "runtime", record.get("id"), {}))
    if ("stale_async_completion" in runtime_issues) != bool(confirmed_async):
        raise RepairPacketError("stale completion issue and evidence disagree")
    if runtime.get("fontsReady") is not True:
        findings.append(_finding("fonts_not_ready", "runtime", "page", {}))
    assertions = runtime.get("assertions")
    if not isinstance(assertions, list):
        raise RepairPacketError("runtime assertions are malformed")
    for assertion in assertions:
        if isinstance(assertion, dict) and assertion.get("passed") is False:
            findings.append(_finding("interaction_assertion_failed", "interaction", assertion.get("id"), {
                "count": _bounded_number(assertion.get("count"), "assertion.count"),
            }))
    event_counts = runtime.get("eventCounts")
    if not isinstance(event_counts, dict):
        raise RepairPacketError("runtime event counts are malformed")
    for field, code in (
        ("consoleErrors", "console_errors"),
        ("pageErrors", "page_errors"),
        ("externalRequests", "external_requests"),
    ):
        count = _bounded_number(event_counts.get(field), f"eventCounts.{field}")
        if count:
            findings.append(_finding(code, "runtime", "page", {"count": count}))
    return findings


def _detail(occurrence: dict[str, Any], finding: dict[str, Any]) -> str:
    where = f"{occurrence['state']}/{occurrence['profile']}/{occurrence['engine']}"
    detail = f"{finding['code']}@{where} target={finding['locator']}"
    if finding["evidence"]:
        measurements = ",".join(f"{key}={value}" for key, value in finding["evidence"].items())
        detail += f" {measurements}"
    return detail


def _feedback(occurrences: list[dict[str, Any]], total: int) -> str:
    focus_repair = any(
        finding.get("code") == "focused_control_obscured"
        for occurrence in occurrences
        for finding in occurrence["findings"]
    )
    clip_repair = any(
        finding.get("code") == "a1_required_text_clipped"
        for occurrence in occurrences
        for finding in occurrence["findings"]
    )
    async_repair = any(
        finding.get("code") == "stale_async_completion"
        for occurrence in occurrences
        for finding in occurrence["findings"]
    )
    accessible_name_repair = any(
        finding.get("code") == "declared_control_accessible_name_mismatch"
        for occurrence in occurrences
        for finding in occurrence["findings"]
    )
    dialog_open_repair = any(
        finding.get("code") == "declared_dialog_focus_lifecycle_mismatch"
        and finding.get("evidence", {}).get("openFocus") is False
        for occurrence in occurrences
        for finding in occurrence["findings"]
    )
    dialog_return_repair = any(
        finding.get("code") == "declared_dialog_focus_lifecycle_mismatch"
        and finding.get("evidence", {}).get("returnFocus") is False
        for occurrence in occurrences
        for finding in occurrence["findings"]
    )
    invalid_feedback_repair = any(
        finding.get("code") == "declared_invalid_feedback_unlinked"
        for occurrence in occurrences
        for finding in occurrence["findings"]
    )
    invalid_input_preservation_repair = any(
        finding.get("code") == "declared_invalid_input_lost"
        for occurrence in occurrences
        for finding in occurrence["findings"]
    )
    suffix = " Preserve passed behavior and required content;"
    if focus_repair:
        suffix += " for focus obscuration, preserve the control and reserve space or reposition the affected fixed/sticky layer;"
    if clip_repair:
        suffix += " for clipped required text, preserve the full copy and remove direct clipping or recompose its text track;"
    if async_repair:
        suffix += " for stale completion, preserve the latest declared user intent and prevent an older completion from overwriting newer state;"
    if accessible_name_repair:
        suffix += " for declared-control accessible-name mismatch, preserve visible copy and make the computed name match by correcting the existing native or ARIA naming source;"
    if dialog_open_repair:
        suffix += " when opening the dialog, move focus to its declared dialog descendant;"
    if dialog_return_repair:
        suffix += " when closing the dialog, restore focus to the declared workflow target;"
    if invalid_feedback_repair:
        suffix += " for invalid feedback, preserve visible error and input, keep aria-invalid=true in the invalid state, retain the existing error stable id, and link it with aria-describedby or aria-errormessage;"
    if invalid_input_preservation_repair:
        suffix += " for invalid input preservation, keep the invalid state and the user-entered input; clear it only after success or an explicit reset;"
    suffix += " change only affected composition; do not edit the evaluator."
    message = f"REPAIR REQUIRED: {total} validated finding(s)."
    seen: set[str] = set()
    for occurrence in occurrences:
        for finding in occurrence["findings"]:
            detail = _detail(occurrence, finding)
            if detail in seen:
                continue
            seen.add(detail)
            separator = " Evidence: " if len(seen) == 1 else "; "
            if len(message) + len(separator) + len(detail) + len(suffix) > MAX_FEEDBACK_CHARS:
                return message + suffix
            message += separator + detail
    return message + suffix


def _narrow_retest(occurrences: list[dict[str, Any]]) -> list[dict[str, str]]:
    states = sorted({item["state"] for item in occurrences})
    selected = {(state, profile, "chromium") for state in states for profile in evidence.FAST_PROFILES}
    selected.update((item["state"], item["profile"], item["engine"]) for item in occurrences)
    return [
        {"state": state, "profile": profile, "engine": engine}
        for state, profile, engine in sorted(selected)
    ]


def _completed_attempts(ledger: dict[str, Any]) -> dict[tuple[str, str, str, str, str], dict[str, Any]]:
    completed: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for record in ledger["attempts"]:
        identity = record["key"]
        key = tuple(identity[name] for name in ("variant", "case_id", "state", "profile", "engine"))
        completed[key] = record["attempts"][-1]
    return completed


def _append_occurrence(
    grouped: dict[tuple[str, str], list[dict[str, Any]]],
    target_key: tuple[str, str],
    occurrence: dict[str, Any],
) -> None:
    occurrences = grouped.setdefault(target_key, [])
    current_count = sum(len(item["findings"]) for item in occurrences)
    if current_count + len(occurrence["findings"]) > MAX_FINDINGS_PER_TARGET:
        raise RepairPacketError(
            f"repair target exceeds {MAX_FINDINGS_PER_TARGET} findings; split the evaluator run before automatic repair"
        )
    occurrences.append(occurrence)


def _targets_from_grouped(
    grouped: dict[tuple[str, str], list[dict[str, Any]]],
    total_by_target: dict[tuple[str, str], int],
) -> list[dict[str, Any]]:
    targets = []
    for (variant, case_id), occurrences in sorted(grouped.items()):
        total = total_by_target[(variant, case_id)]
        targets.append({
            "variant": variant,
            "case_id": case_id,
            "finding_count": total,
            "occurrences": occurrences,
            "narrow_retest": _narrow_retest(occurrences),
            "feedback": _feedback(occurrences, total),
        })
    return targets


def targets_from_validated_attempts(
    attempts: list[dict[str, Any]],
    result_dir: Path,
    screenshot_dir: Path,
) -> tuple[list[dict[str, Any]], int]:
    """Project an exact, already captured row subset through the canonical repair rules."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    total_by_target: dict[tuple[str, str], int] = {}
    seen: set[tuple[str, str, str, str, str]] = set()
    finding_runs = 0
    for record in attempts:
        if not isinstance(record, dict) or set(record) != {"key", "attempts"}:
            raise RepairPacketError("narrow attempt record is malformed")
        identity = record["key"]
        if not isinstance(identity, dict) or set(identity) != {"variant", "case_id", "state", "profile", "engine"}:
            raise RepairPacketError("narrow attempt identity is malformed")
        key = tuple(identity[name] for name in ("variant", "case_id", "state", "profile", "engine"))
        if (
            key in seen
            or key[0] not in evidence.VARIANTS
            or any(not isinstance(value, str) for value in key)
        ):
            raise RepairPacketError("narrow attempt identity is invalid or duplicated")
        seen.add(key)
        history = record["attempts"]
        if not isinstance(history, list) or not history or not isinstance(history[-1], dict):
            raise RepairPacketError("narrow attempt history is incomplete")
        final = history[-1]
        if final.get("status") != "completed" or final.get("exit_code") not in {0, 2}:
            raise RepairPacketError("narrow attempt did not complete")
        stem = evidence.artifact_stem(key)
        if final.get("result") != f"{stem}.json" or final.get("screenshot") != f"{stem}.png":
            raise RepairPacketError("narrow artifact name changed")
        result_path = result_dir / final["result"]
        screenshot_path = screenshot_dir / final["screenshot"]
        if (
            not result_path.is_file()
            or result_path.is_symlink()
            or result_path.resolve().parent != result_dir.resolve(strict=True)
            or not screenshot_path.is_file()
            or screenshot_path.is_symlink()
            or screenshot_path.resolve().parent != screenshot_dir.resolve(strict=True)
        ):
            raise RepairPacketError("narrow artifact is missing or unsafe")
        try:
            verdict = evidence._validate_result(
                key,
                result_path,
                screenshot_path,
                final.get("result_sha256"),
                final.get("screenshot_sha256"),
                final.get("spec_sha256"),
            )
        except evidence.V7EvidenceError as error:
            raise RepairPacketError(f"narrow evidence is invalid: {error}") from error
        if (verdict == "clean") != (final["exit_code"] == 0):
            raise RepairPacketError("narrow exit code and verdict disagree")
        if verdict == "clean":
            continue
        result = _load(result_path, "narrow visual result")
        findings = extract_findings(result)
        if not findings:
            raise RepairPacketError(f"narrow finding verdict has no actionable projection: {stem}")
        finding_runs += 1
        target_key = (key[0], key[1])
        total_by_target[target_key] = total_by_target.get(target_key, 0) + len(findings)
        _append_occurrence(grouped, target_key, {
            "state": key[2],
            "profile": key[3],
            "engine": key[4],
            "route": _safe_route(result["input"].get("route")),
            "result": {"path": final["result"], "sha256": final["result_sha256"]},
            "screenshot": {"path": final["screenshot"], "sha256": final["screenshot_sha256"]},
            "findings": findings,
        })
    return _targets_from_grouped(grouped, total_by_target), finding_runs


def build_packet(
    manifest_path: Path,
    ledger_path: Path,
    result_dir: Path,
    screenshot_dir: Path,
    repository_root: Path,
    gate: str,
) -> dict[str, Any]:
    first_validation = evidence.validate(
        manifest_path, ledger_path, result_dir, screenshot_dir, repository_root, gate
    )
    screenshot_count, finding_run_count = first_validation
    initial_ledger_sha256 = _digest(ledger_path)
    initial_manifest_sha256 = _digest(manifest_path)
    ledger = _load(ledger_path, "visual ledger")
    manifest = _load(manifest_path, "cohort manifest")
    attempts = _completed_attempts(ledger)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    total_by_target: dict[tuple[str, str], int] = {}
    for key in evidence.expected_inventory(manifest, ledger["split"], gate):
        attempt = attempts[key]
        result_path = result_dir / attempt["result"]
        if _digest(result_path) != attempt["result_sha256"]:
            raise RepairPacketError(f"visual result changed after validation: {evidence.artifact_stem(key)}")
        result = _load(result_path, "visual result")
        if result.get("verdict") == "clean":
            continue
        findings = extract_findings(result)
        if not findings:
            raise RepairPacketError(f"finding verdict has no actionable projection: {evidence.artifact_stem(key)}")
        target_key = (key[0], key[1])
        total_by_target[target_key] = total_by_target.get(target_key, 0) + len(findings)
        occurrence = {
            "state": key[2],
            "profile": key[3],
            "engine": key[4],
            "route": _safe_route(result["input"].get("route")),
            "result": {"path": attempt["result"], "sha256": attempt["result_sha256"]},
            "screenshot": {"path": attempt["screenshot"], "sha256": attempt["screenshot_sha256"]},
            "findings": findings,
        }
        _append_occurrence(grouped, target_key, occurrence)

    targets = _targets_from_grouped(grouped, total_by_target)
    second_validation = evidence.validate(
        manifest_path, ledger_path, result_dir, screenshot_dir, repository_root, gate
    )
    if (
        second_validation != first_validation
        or _digest(ledger_path) != initial_ledger_sha256
        or _digest(manifest_path) != initial_manifest_sha256
    ):
        raise RepairPacketError("v7 evidence changed while compiling the repair packet")
    return {
        "schema_version": 1,
        "status": "repair_required" if targets else "clean",
        "source": {
            "cohort_manifest": ledger["cohort_manifest"],
            "ledger": {"path": ledger_path.name, "sha256": initial_ledger_sha256},
            "compiler": {"path": Path(__file__).resolve().relative_to(repository_root).as_posix(), "sha256": _digest(Path(__file__))},
            "split": ledger["split"],
            "gate": gate,
            "input_inventory_sha256": ledger["input_inventory_sha256"],
            "screenshot_count": screenshot_count,
            "finding_run_count": finding_run_count,
        },
        "targets": targets,
    }


def write_once(path: Path, packet: dict[str, Any], repository_root: Path) -> None:
    requested = Path(os.path.abspath(path.expanduser()))
    if requested.name in {"", ".", ".."} or os.path.lexists(requested) and requested.is_symlink():
        raise RepairPacketError("repair packet output path is invalid or a symlink")
    parent = requested.parent.resolve(strict=True)
    if parent != requested.parent:
        raise RepairPacketError("repair packet output parent must not traverse a symlink")
    output = parent / requested.name
    try:
        parent.relative_to(repository_root)
    except ValueError:
        pass
    else:
        raise RepairPacketError("repair packet must remain evaluator-owned outside the repository")
    if os.path.lexists(output):
        raise RepairPacketError(f"refusing to overwrite repair packet: {output.name}")
    body = (json.dumps(packet, ensure_ascii=False, indent=2) + "\n").encode()
    if len(body) > MAX_PACKET_BYTES:
        raise RepairPacketError("repair packet exceeds the byte limit")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, output)
        except FileExistsError as error:
            raise RepairPacketError(f"refusing to overwrite repair packet: {output.name}") from error
        os.unlink(temporary)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--result-dir", required=True, type=Path)
    parser.add_argument("--screenshot-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    parser.add_argument("--gate", choices=evidence.GATES, default="full")
    args = parser.parse_args()
    try:
        root = args.repository_root.resolve(strict=True)
        packet = build_packet(
            args.manifest.resolve(strict=True),
            args.ledger.resolve(strict=True),
            args.result_dir.resolve(strict=True),
            args.screenshot_dir.resolve(strict=True),
            root,
            args.gate,
        )
        write_once(args.output, packet, root)
    except (OSError, RepairPacketError, evidence.V7EvidenceError, evidence.preflight.PreflightError) as error:
        print(f"v7 repair packet failed: {error}", file=sys.stderr)
        return 1
    print(f"v7 repair packet {packet['status']}: {len(packet['targets'])} target(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
