#!/usr/bin/env python3
"""Record one human-owned decision against a freshly captured draft cohort."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DECISION_LIMIT = 32 * 1024
RECEIPT_LIMIT = 256 * 1024
CLAIM_BOUNDARY = "selection_lineage_only_no_release_acceptance"
DECISION_KEYS = {
    "schema_version", "cohort_id", "action", "variant_id", "authority",
    "reason", "adjustments", "convergence_reviewed",
}
RECEIPT_KEYS = {
    "schema_version", "status", "classification", "claim_boundary", "cohort",
    "source", "configuration", "evidence", "decision_checkpoint", "tools",
}
DECISION_RECEIPT_KEYS = {
    "schema_version", "status", "classification", "claim_boundary", "source",
    "decision", "handoff", "tools",
}
COHORT_KEYS = {
    "cohort_id", "partition", "locale", "surface", "decision_question",
    "held_constant_axes", "selection_criteria", "variant_count", "variants",
}
SOURCE_KEYS = {
    "plan", "base_brief", "effective_brief", "case", "convergence_config",
    "run_manifest", "capture_receipt", "skill_tree_sha256", "outputs",
}
CONFIGURATION_KEYS = {
    "model", "reasoning_effort", "max_repair_rounds", "browser_contract",
    "skill_reference", "capture_standard",
}
EVIDENCE_KEYS = {"capture_count", "capture_set_sha256", "capture_standard", "convergence"}
CONVERGENCE_KEYS = {
    "status", "result", "policy", "profiles", "observation_count", "advisory_count",
    "advisory_counts", "affected_variant_ids", "review_required", "observations",
    "audit", "claim_boundary",
}
DECISION_CHECKPOINT_KEYS = {
    "schema_version", "claim_boundary", "variants", "allowed_actions",
    "reply_grammar",
}

if str(ROOT / "evals") not in sys.path:
    sys.path.insert(0, str(ROOT / "evals"))

import run_current_draft_cohort as cohort  # noqa: E402
from validate_current_craft_acceptance import (  # noqa: E402
    CurrentCraftError,
    validate_current_capture_evidence,
)


class DraftDecisionError(ValueError):
    """Raised when a draft decision cannot be bound to current evidence."""


def _exact(value: object, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise DraftDecisionError(f"{label} schema is invalid")
    return value


def _browser_contract_record(value: object) -> dict[str, Any] | None:
    if value is None:
        return None
    record = _exact(
        value,
        {"schema_version", "bytes", "sha256", "case_count", "step_count"},
        "cohort receipt.configuration.browser_contract",
    )
    sha256 = record["sha256"]
    if (
        type(record["schema_version"]) is not int
        or record["schema_version"] not in {1, 2}
        or type(record["bytes"]) is not int
        or not 1 <= record["bytes"] <= 32 * 1024
        or not isinstance(sha256, str)
        or len(sha256) != 64
        or any(character not in "0123456789abcdef" for character in sha256)
        or type(record["case_count"]) is not int
        or not 1 <= record["case_count"] <= 4
        or type(record["step_count"]) is not int
        or not record["case_count"] <= record["step_count"] <= 96
    ):
        raise DraftDecisionError(
            "cohort receipt.configuration.browser_contract is invalid"
        )
    return record


def _as_decision_error(callable_: Any, *args: Any) -> Any:
    try:
        return callable_(*args)
    except (OSError, TypeError, KeyError, cohort.DraftCohortError) as error:
        raise DraftDecisionError(str(error)) from error


def _digest_record(path: Path) -> dict[str, Any]:
    info = path.stat()
    return {
        "bytes": info.st_size,
        "mode": f"{stat.S_IMODE(info.st_mode):04o}",
        "sha256": cohort._digest(path),
    }


def _decision_tool_records() -> dict[str, dict[str, Any]]:
    return {
        "recorder": {
            "path": "evals/record_current_draft_decision.py",
            **_digest_record(Path(__file__).resolve()),
        },
        "capture_validator": {
            "path": "evals/validate_current_craft_acceptance.py",
            **_digest_record(ROOT / "evals" / "validate_current_craft_acceptance.py"),
        },
    }


def _real_directory(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise DraftDecisionError(f"{label} must be an absolute real directory")
    try:
        info = path.lstat()
        canonical = path.resolve(strict=True)
    except OSError as error:
        raise DraftDecisionError(f"{label} must be an absolute real directory") from error
    if not stat.S_ISDIR(info.st_mode) or path.is_symlink() or canonical != path:
        raise DraftDecisionError(f"{label} must be an absolute real directory")
    _as_decision_error(cohort._outside_authoring_repository, path, label)
    return path


def _read_json(path: Path, label: str, limit: int) -> tuple[dict[str, Any], bytes]:
    try:
        path, raw = cohort._regular_absolute_file(path, label, limit)
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, cohort.DraftCohortError) as error:
        raise DraftDecisionError(f"{label} must be bounded strict UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise DraftDecisionError(f"{label} must be a JSON object")
    return value, raw


def _assert_record(
    path: Path,
    expected: object,
    label: str,
    *,
    has_mode: bool,
    expected_path: str | None = None,
) -> None:
    keys = {"bytes", "sha256", *( ("mode",) if has_mode else () )}
    if not isinstance(expected, dict):
        raise DraftDecisionError(f"{label} provenance is invalid")
    if "path" in expected:
        keys.add("path")
    if set(expected) != keys:
        raise DraftDecisionError(f"{label} provenance schema is invalid")
    if expected_path is not None and expected.get("path") != expected_path:
        raise DraftDecisionError(f"{label} provenance path is invalid")
    try:
        _, raw = cohort._regular_absolute_file(path, label, RECEIPT_LIMIT)
        mode = f"{stat.S_IMODE(path.stat().st_mode):04o}"
    except cohort.DraftCohortError as error:
        raise DraftDecisionError(f"{label} provenance is invalid") from error
    actual = {"bytes": len(raw), "sha256": cohort._digest_bytes(raw)}
    if has_mode:
        actual["mode"] = mode
    elif mode != "0600":
        raise DraftDecisionError(f"{label} must use private mode 0600")
    if any(expected.get(key) != value for key, value in actual.items()):
        raise DraftDecisionError(f"{label} provenance is invalid")


def _normalize_cohort(receipt: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    metadata = _exact(receipt["cohort"], COHORT_KEYS, "cohort receipt.cohort")
    variants_raw = metadata["variants"]
    if not isinstance(variants_raw, list) or not 2 <= len(variants_raw) <= 3:
        raise DraftDecisionError("cohort variants are invalid")
    variants = []
    for index, raw in enumerate(variants_raw):
        variant = _exact(raw, cohort.VARIANT_KEYS, f"cohort variant[{index}]")
        variants.append({
            "id": _as_decision_error(cohort._identifier, variant["id"], f"variant[{index}].id"),
            "hypothesis": _as_decision_error(cohort._bounded_text, variant["hypothesis"], f"variant[{index}].hypothesis"),
            "changed_axes": _as_decision_error(cohort._identifier_list, variant["changed_axes"], f"variant[{index}].changed_axes", 2, 6),
            "expected_benefit": _as_decision_error(cohort._bounded_text, variant["expected_benefit"], f"variant[{index}].expected_benefit"),
            "risk": _as_decision_error(cohort._bounded_text, variant["risk"], f"variant[{index}].risk"),
            "disqualifier": _as_decision_error(cohort._bounded_text, variant["disqualifier"], f"variant[{index}].disqualifier"),
        })
    if len({variant["id"] for variant in variants}) != len(variants) or metadata["variant_count"] != len(variants):
        raise DraftDecisionError("cohort variant identity is invalid")
    normalized = {
        "cohort_id": _as_decision_error(cohort._identifier, metadata["cohort_id"], "cohort id"),
        "surface": _as_decision_error(cohort._identifier, metadata["surface"], "cohort surface"),
        "held_constant_axes": _as_decision_error(cohort._identifier_list, metadata["held_constant_axes"], "held constant axes", 4, 16),
        "selection_criteria": _as_decision_error(cohort._text_list, metadata["selection_criteria"], "selection criteria", 2, 8),
        "variants": variants,
    }
    source = _exact(receipt["source"], SOURCE_KEYS, "cohort receipt.source")
    configuration = _exact(
        receipt["configuration"],
        CONFIGURATION_KEYS,
        "cohort receipt.configuration",
    )
    _browser_contract_record(configuration["browser_contract"])
    evidence = _exact(receipt["evidence"], EVIDENCE_KEYS, "cohort receipt.evidence")
    _exact(evidence["convergence"], CONVERGENCE_KEYS, "cohort convergence")
    checkpoint = _exact(
        receipt["decision_checkpoint"],
        DECISION_CHECKPOINT_KEYS,
        "cohort decision checkpoint",
    )
    checkpoint_variants = checkpoint["variants"]
    if (
        checkpoint["schema_version"] != 1
        or checkpoint["claim_boundary"]
        != "fresh_capture_navigation_only_not_selection_or_release"
        or checkpoint["allowed_actions"] != ["select", "revise", "stop"]
        or checkpoint["reply_grammar"] != cohort.DECISION_CHECKPOINT_REPLY_GRAMMAR
        or not isinstance(checkpoint_variants, list)
        or len(checkpoint_variants) != len(variants)
    ):
        raise DraftDecisionError("cohort decision checkpoint is invalid")
    for expected_variant, checkpoint_variant in zip(
        variants,
        checkpoint_variants,
    ):
        checkpoint_variant = _exact(
            checkpoint_variant,
            {"variant_id", "desktop", "mobile"},
            "cohort decision checkpoint variant",
        )
        if checkpoint_variant["variant_id"] != expected_variant["id"]:
            raise DraftDecisionError("cohort decision checkpoint order drifted")
        for profile in ("desktop", "mobile"):
            capture = _exact(
                checkpoint_variant[profile],
                {"label", "path"},
                "cohort decision checkpoint capture",
            )
            path = capture["path"]
            if (
                not isinstance(capture["label"], str)
                or cohort.ID_PATTERN.fullmatch(capture["label"]) is None
                or not isinstance(path, str)
                or not path.startswith("evidence/artifacts/")
                or not path.endswith(".png")
                or "\\" in path
                or any(part in {"", ".", ".."} for part in path.split("/"))
            ):
                raise DraftDecisionError("cohort decision checkpoint capture is invalid")
    if (
        receipt["configuration"]["skill_reference"] != "references/design-exploration.md"
        or receipt["configuration"]["capture_standard"] != cohort.CAPTURE_STANDARD
        or evidence["capture_standard"] != cohort.CAPTURE_STANDARD
        or evidence["capture_count"] != len(variants) * 2
        or evidence["convergence"]["policy"] != "advisory_only"
        or type(evidence["convergence"]["review_required"]) is not bool
    ):
        raise DraftDecisionError("cohort evidence contract is invalid")
    return normalized, source


def validate_cohort_source(cohort_root: Path, log_dir: Path) -> dict[str, Any]:
    root = _real_directory(cohort_root, "cohort root")
    logs = _real_directory(log_dir, "cohort log directory")
    _as_decision_error(cohort._separate, root, logs, "cohort root and log directory")
    receipt_path = root / "draft-cohort-receipt.json"
    receipt, raw_before = _read_json(receipt_path, "cohort receipt", RECEIPT_LIMIT)
    if stat.S_IMODE(receipt_path.stat().st_mode) != 0o600:
        raise DraftDecisionError("cohort receipt must use private mode 0600")
    receipt = _exact(receipt, RECEIPT_KEYS, "cohort receipt")
    if (
        type(receipt["schema_version"]) is not int or receipt["schema_version"] != 1
        or receipt["status"] != "captured"
        or receipt["classification"] != "draft_cohort_captured"
        or receipt["claim_boundary"] != cohort.CLAIM_BOUNDARY
    ):
        raise DraftDecisionError("cohort receipt identity is invalid")
    metadata, source = _normalize_cohort(receipt)
    if receipt["tools"] != cohort._tool_records():
        raise DraftDecisionError("current draft cohort tool provenance drifted")

    _assert_record(logs / "draft-cohort-effective-brief.md", source["effective_brief"], "effective brief", has_mode=False)
    _assert_record(logs / "draft-cohort-case.json", source["case"], "draft cohort case", has_mode=False)
    _assert_record(logs / "draft-cohort-convergence.json", source["convergence_config"], "draft convergence contract", has_mode=False)
    manifest_path = root / "workspace" / "run-manifest.json"
    capture_path = root / "evidence" / "capture-receipt.json"
    _assert_record(
        manifest_path,
        source["run_manifest"],
        "run manifest",
        has_mode=True,
        expected_path="workspace/run-manifest.json",
    )
    _assert_record(
        capture_path,
        source["capture_receipt"],
        "capture receipt",
        has_mode=True,
        expected_path="evidence/capture-receipt.json",
    )
    case_value, _ = _read_json(
        logs / "draft-cohort-case.json",
        "draft cohort case",
        RECEIPT_LIMIT,
    )
    allow_subset = isinstance(
        case_value.get("capture_plan", {}).get("pages")
        if isinstance(case_value.get("capture_plan"), dict)
        else None,
        dict,
    )
    validation_arguments = {"allow_draft_subset": True} if allow_subset else {}
    try:
        validated = validate_current_capture_evidence(
            root / "workspace",
            logs / "draft-cohort-case.json",
            capture_path,
            manifest_path,
            **validation_arguments,
        )
    except CurrentCraftError as error:
        raise DraftDecisionError("current draft capture provenance is invalid") from error
    evidence = receipt["evidence"]
    if any(validated[key] != evidence[key] for key in ("capture_count", "capture_set_sha256", "capture_standard")):
        raise DraftDecisionError("current draft capture evidence drifted")
    captures = validated.get("receipt", {}).get("captures")
    if not isinstance(captures, list):
        raise DraftDecisionError("current draft capture matrix is invalid")
    capture_by_identity = {
        (capture.get("page"), capture.get("profile")): {
            "label": capture.get("label"),
            "path": f"evidence/{capture.get('path')}",
        }
        for capture in captures
        if isinstance(capture, dict)
    }
    checkpoint_variants = receipt["decision_checkpoint"]["variants"]
    for variant, checkpoint_variant in zip(
        metadata["variants"],
        checkpoint_variants,
    ):
        page = f"directions/{variant['id']}.html"
        expected = {
            "variant_id": variant["id"],
            "desktop": capture_by_identity.get((page, "desktop-default")),
            "mobile": capture_by_identity.get((page, "mobile-default")),
        }
        if checkpoint_variant != expected:
            raise DraftDecisionError(
                "cohort decision checkpoint drifted from validated captures"
            )
    manifest = validated["manifest"]
    if (
        manifest.get("outputs") != source["outputs"]
        or manifest.get("skill_snapshot", {}).get("tree_sha256") != source["skill_tree_sha256"]
        or manifest.get("browser_contract")
        != receipt["configuration"]["browser_contract"]
    ):
        raise DraftDecisionError("cohort receipt and validated manifest projection drifted")
    try:
        convergence = cohort._convergence_summary(metadata, root / "evidence")
    except cohort.DraftCohortError as error:
        raise DraftDecisionError("current draft convergence evidence is invalid") from error
    if convergence != evidence["convergence"]:
        raise DraftDecisionError("current draft convergence evidence drifted")
    cohort_seed_snapshot = None
    if allow_subset:
        cohort_seed_snapshot = _exact(
            manifest.get("seed_snapshot"),
            {"tree_sha256", "files", "directories"},
            "seeded cohort manifest.seed_snapshot",
        )
        seed_tree = {
            "directories": cohort_seed_snapshot["directories"],
            "files": cohort_seed_snapshot["files"],
        }
        if (
            not isinstance(cohort_seed_snapshot["files"], list)
            or not cohort_seed_snapshot["files"]
            or not isinstance(cohort_seed_snapshot["directories"], list)
            or cohort_seed_snapshot["tree_sha256"]
            != cohort._digest_bytes(
                json.dumps(
                    seed_tree,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
        ):
            raise DraftDecisionError("seeded cohort snapshot provenance is invalid")
    receipt_after, raw_after = _read_json(receipt_path, "cohort receipt", RECEIPT_LIMIT)
    if raw_after != raw_before or receipt_after != receipt:
        raise DraftDecisionError("cohort receipt drifted during decision validation")
    return {
        "receipt": receipt,
        "receipt_record": {"path": "draft-cohort-receipt.json", **_digest_record(receipt_path)},
        "cohort": metadata,
        "capture": validated,
        "automatic_production_lane": "RETROFIT" if allow_subset else "BUILD",
        "cohort_seed_snapshot": cohort_seed_snapshot,
    }


def _normalize_decision(item: object) -> dict[str, Any]:
    item = _exact(item, DECISION_KEYS, "draft decision")
    action = item["action"]
    if (
        type(item["schema_version"]) is not int
        or item["schema_version"] != 1
        or not isinstance(action, str)
        or action not in {"select", "revise", "stop"}
    ):
        raise DraftDecisionError("draft decision identity is invalid")
    if (
        not isinstance(item["authority"], str)
        or item["authority"] not in {"user_confirmed", "human_reviewer_confirmed", "user_delegated"}
    ):
        raise DraftDecisionError("draft decision requires human authority or explicit user delegation")
    if action == "stop":
        if item["variant_id"] is not None:
            raise DraftDecisionError("stop decisions cannot name a variant")
        variant_id = None
    else:
        variant_id = _as_decision_error(cohort._identifier, item["variant_id"], "decision variant id")
    adjustments = _as_decision_error(cohort._text_list, item["adjustments"], "decision adjustments", 0, 3)
    if action == "revise" and not adjustments:
        raise DraftDecisionError("revise decisions require at least one bounded adjustment")
    if action == "stop" and adjustments:
        raise DraftDecisionError("stop decisions cannot include adjustments")
    if type(item["convergence_reviewed"]) is not bool:
        raise DraftDecisionError("convergence_reviewed must be boolean")
    return {
        "action": action,
        "cohort_id": _as_decision_error(cohort._identifier, item["cohort_id"], "decision cohort id"),
        "variant_id": variant_id,
        "authority": item["authority"],
        "reason": _as_decision_error(cohort._bounded_text, item["reason"], "decision reason"),
        "adjustments": adjustments,
        "convergence_reviewed": item["convergence_reviewed"],
    }


def load_decision(path: Path) -> dict[str, Any]:
    item, _ = _read_json(path, "draft decision", DECISION_LIMIT)
    return _normalize_decision(item)


def write_structured_decision(
    output_root: Path,
    *,
    cohort_id: str,
    action: str,
    variant_id: str | None,
    authority: str,
    reason: str,
    adjustments: list[str],
    convergence_reviewed: bool,
) -> Path:
    payload = {
        "schema_version": 1,
        "cohort_id": cohort_id,
        "action": action,
        "variant_id": variant_id,
        "authority": authority,
        "reason": reason,
        "adjustments": adjustments,
        "convergence_reviewed": convergence_reviewed,
    }
    _normalize_decision(payload)
    output_root = cohort._real_empty_directory(
        output_root,
        "draft decision output root",
    )
    parent = cohort._real_directory(
        output_root.parent,
        "draft decision input parent",
    )
    decision_path = output_root.with_name(f"{output_root.name}.input.json")
    cohort._outside_authoring_repository(
        output_root,
        "generated draft decision input parent",
    )
    encoded = (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    if len(encoded) > DECISION_LIMIT:
        raise DraftDecisionError("generated draft decision exceeds its size limit")
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    nofollow_flag = getattr(os, "O_NOFOLLOW", 0)
    if directory_flag == 0 or nofollow_flag == 0:
        raise DraftDecisionError(
            "platform requires O_DIRECTORY and O_NOFOLLOW"
        )
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | directory_flag
        | nofollow_flag
    )
    output_flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | nofollow_flag
    )
    parent_descriptor = -1
    descriptor = -1
    created = False
    created_identity: tuple[int, int] | None = None
    try:
        parent_descriptor = os.open(parent, directory_flags)
        pinned_parent = os.fstat(parent_descriptor)
        current_parent = parent.lstat()
        if (
            not stat.S_ISDIR(pinned_parent.st_mode)
            or (pinned_parent.st_dev, pinned_parent.st_ino)
            != (current_parent.st_dev, current_parent.st_ino)
        ):
            raise OSError("draft decision input parent identity changed")
        descriptor = os.open(
            decision_path.name,
            output_flags,
            0o600,
            dir_fd=parent_descriptor,
        )
        created = True
        opened = os.fstat(descriptor)
        created_identity = (opened.st_dev, opened.st_ino)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise OSError("generated decision input is not a regular file")
        os.fchmod(descriptor, 0o600)
        written = 0
        while written < len(encoded):
            count = os.write(descriptor, encoded[written:])
            if count <= 0:
                raise OSError("short write while creating draft decision input")
            written += count
        os.fsync(descriptor)
        final = os.fstat(descriptor)
        current_parent = parent.lstat()
        current = os.stat(
            decision_path.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        if (
            (current_parent.st_dev, current_parent.st_ino)
            != (pinned_parent.st_dev, pinned_parent.st_ino)
            or
            (current.st_dev, current.st_ino) != created_identity
            or not stat.S_ISREG(current.st_mode)
            or current.st_nlink != 1
            or final.st_size != len(encoded)
            or stat.S_IMODE(final.st_mode) != 0o600
        ):
            raise OSError("generated decision input provenance is invalid")
    except OSError as error:
        if (
            created
            and parent_descriptor >= 0
            and created_identity is not None
        ):
            try:
                current = os.stat(
                    decision_path.name,
                    dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
                if (current.st_dev, current.st_ino) == created_identity:
                    os.unlink(
                        decision_path.name,
                        dir_fd=parent_descriptor,
                    )
            except OSError:
                pass
        raise DraftDecisionError(
            "generated draft decision input could not be created exclusively"
        ) from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if parent_descriptor >= 0:
            os.close(parent_descriptor)
    return decision_path


def _decision_receipt_payload(
    source: dict[str, Any], item: dict[str, Any], decision_record: dict[str, Any],
    tools: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    variants = {variant["id"]: variant for variant in source["cohort"]["variants"]}
    variant = None if item["variant_id"] is None else variants.get(item["variant_id"])
    if item["variant_id"] is not None and variant is None:
        raise DraftDecisionError("draft decision variant does not exist in the cohort")
    convergence = source["receipt"]["evidence"]["convergence"]
    if item["action"] != "stop" and convergence["review_required"] and not item["convergence_reviewed"]:
        raise DraftDecisionError("the advisory-only convergence finding must be reviewed before proceeding")
    page = None if variant is None else f"directions/{variant['id']}.html"
    labels = sorted(
        capture["label"] for capture in source["capture"]["receipt"]["captures"]
        if capture.get("page") == page
    ) if page else []
    if page and len(labels) != 2:
        raise DraftDecisionError("selected variant lacks a fresh desktop/mobile capture pair")
    classification = {
        "select": "draft_direction_selected",
        "revise": "draft_direction_revision_requested",
        "stop": "draft_direction_stopped",
    }[item["action"]]
    next_step = {
        "select": "implement_selected_direction",
        "revise": "render_one_bounded_revision",
        "stop": "stop_before_production",
    }[item["action"]]
    revalidation = {
        "select": [
            (
                "production implementation"
                if source["automatic_production_lane"] == "BUILD"
                else "formal RETROFIT implementation"
            ),
            "fresh Playwright capture",
            "affected release matrix",
        ],
        "revise": ["one fresh desktop/mobile revision pair", "return to this decision checkpoint"],
        "stop": [],
    }[item["action"]]
    return {
        "schema_version": 1,
        "status": "recorded",
        "classification": classification,
        "claim_boundary": CLAIM_BOUNDARY,
        "source": {
            "cohort_receipt": source["receipt_record"],
            "decision_input": decision_record,
            "cohort_id": source["cohort"]["cohort_id"],
            "capture_set_sha256": source["receipt"]["evidence"]["capture_set_sha256"],
            "skill_tree_sha256": source["receipt"]["source"]["skill_tree_sha256"],
            "convergence": {
                "policy": "advisory_only",
                "review_required": convergence["review_required"],
                "advisory_counts": convergence["advisory_counts"],
                "affected_variant_ids": convergence["affected_variant_ids"],
            },
        },
        "decision": {
            "action": item["action"], "authority": item["authority"], "reason": item["reason"],
            "adjustments": item["adjustments"], "convergence_reviewed": item["convergence_reviewed"],
            "variant": variant, "capture_labels": labels,
        },
        "handoff": {
            "next_step": next_step,
            "production_lane": (
                source["automatic_production_lane"]
                if item["action"] == "select"
                else None
            ),
            "base_variant_id": item["variant_id"], "source_page": page,
            "held_constant_axes": source["cohort"]["held_constant_axes"],
            "selection_criteria": source["cohort"]["selection_criteria"],
            "draft_evidence_policy": "style_calibration_only_not_release_evidence",
            "required_revalidation": revalidation,
        },
        "tools": tools,
    }


def validate_decision_receipt(
    cohort_root: Path, log_dir: Path, decision_path: Path, receipt_path: Path,
) -> dict[str, Any]:
    """Revalidate a recorded draft decision and every mutable source it binds."""
    tools_before = _decision_tool_records()
    source = validate_cohort_source(cohort_root, log_dir)
    decision_record = _digest_record(decision_path)
    if decision_record["mode"] != "0600":
        raise DraftDecisionError("draft decision must use private mode 0600")
    item = load_decision(decision_path)
    if item["cohort_id"] != source["cohort"]["cohort_id"]:
        raise DraftDecisionError("draft decision does not match the cohort")
    expected = _decision_receipt_payload(source, item, decision_record, tools_before)
    receipt, receipt_raw_before = _read_json(receipt_path, "draft decision receipt", RECEIPT_LIMIT)
    _as_decision_error(cohort._outside_authoring_repository, receipt_path, "draft decision receipt")
    if stat.S_IMODE(receipt_path.stat().st_mode) != 0o600:
        raise DraftDecisionError("draft decision receipt must use private mode 0600")
    receipt = _exact(receipt, DECISION_RECEIPT_KEYS, "draft decision receipt")
    if receipt != expected:
        raise DraftDecisionError("draft decision receipt provenance is invalid")
    receipt_record = {
        "bytes": len(receipt_raw_before),
        "mode": "0600",
        "sha256": cohort._digest_bytes(receipt_raw_before),
    }

    source_again = validate_cohort_source(cohort_root, log_dir)
    _, decision_raw_after = _read_json(decision_path, "draft decision", DECISION_LIMIT)
    receipt_after, receipt_raw_after = _read_json(receipt_path, "draft decision receipt", RECEIPT_LIMIT)
    if (
        source_again["receipt"] != source["receipt"]
        or source_again["receipt_record"] != source["receipt_record"]
        or source_again["capture"]["capture_set_sha256"] != source["capture"]["capture_set_sha256"]
        or _digest_record(decision_path) != decision_record
        or cohort._digest_bytes(decision_raw_after) != decision_record["sha256"]
        or receipt_raw_after != receipt_raw_before
        or receipt_after != receipt
        or _digest_record(receipt_path) != receipt_record
        or _decision_tool_records() != tools_before
    ):
        raise DraftDecisionError("draft decision source drifted during validation")
    return {
        "receipt": receipt,
        "receipt_record": receipt_record,
        "skill_tree_sha256": receipt["source"]["skill_tree_sha256"],
        "cohort_seed_snapshot": source["cohort_seed_snapshot"],
    }


def run(cohort_root: Path, log_dir: Path, decision_path: Path, output_root: Path) -> dict[str, Any]:
    decision_path, _ = _as_decision_error(
        cohort._regular_absolute_file,
        decision_path,
        "draft decision",
        DECISION_LIMIT,
    )
    _as_decision_error(
        cohort._outside_authoring_repository,
        decision_path,
        "draft decision",
    )
    resolved_cohort_root = _real_directory(cohort_root, "cohort root")
    resolved_log_dir = _real_directory(log_dir, "cohort log directory")
    resolved_output_root = _as_decision_error(
        cohort._real_empty_directory,
        output_root,
        "draft decision output root",
    )
    for boundary, label in (
        (resolved_cohort_root, "cohort root"),
        (resolved_log_dir, "cohort log directory"),
        (resolved_output_root, "decision output root"),
    ):
        _as_decision_error(
            cohort._separate,
            decision_path,
            boundary,
            f"draft decision and {label}",
        )
    tools_before = _decision_tool_records()
    source = validate_cohort_source(cohort_root, log_dir)
    decision_before = _digest_record(decision_path)
    if decision_before["mode"] != "0600":
        raise DraftDecisionError("draft decision must use private mode 0600")
    item = load_decision(decision_path)
    if item["cohort_id"] != source["cohort"]["cohort_id"]:
        raise DraftDecisionError("draft decision does not match the cohort")
    _, decision_raw_after = _read_json(decision_path, "draft decision", DECISION_LIMIT)
    if _digest_record(decision_path) != decision_before or cohort._digest_bytes(decision_raw_after) != decision_before["sha256"]:
        raise DraftDecisionError("draft decision drifted during validation")

    receipt = _decision_receipt_payload(source, item, decision_before, tools_before)
    source_again = validate_cohort_source(cohort_root, log_dir)
    if (
        source_again["receipt"] != source["receipt"]
        or source_again["receipt_record"] != source["receipt_record"]
        or source_again["capture"]["capture_set_sha256"] != source["capture"]["capture_set_sha256"]
    ):
        raise DraftDecisionError("current draft cohort drifted before decision finalization")
    _, decision_raw_final = _read_json(decision_path, "draft decision", DECISION_LIMIT)
    if _digest_record(decision_path) != decision_before or cohort._digest_bytes(decision_raw_final) != decision_before["sha256"]:
        raise DraftDecisionError("draft decision drifted before finalization")
    if _decision_tool_records() != tools_before:
        raise DraftDecisionError("draft decision tool provenance drifted before finalization")
    encoded = (json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    try:
        with cohort._PinnedDirectory(resolved_output_root, "draft decision output root") as output:
            cohort._outside_authoring_repository(output.path, "draft decision output root")
            cohort._separate(output.path, resolved_cohort_root, "decision output and cohort root")
            cohort._separate(output.path, resolved_log_dir, "decision output and log directory")
            output.write_exclusive("draft-decision-receipt.json", encoded)
    except (OSError, cohort.DraftCohortError) as error:
        try:
            tools_after_failure = _decision_tool_records()
        except OSError as provenance_error:
            raise DraftDecisionError("draft decision tool provenance failed during finalization") from provenance_error
        if tools_after_failure != tools_before:
            raise DraftDecisionError("draft decision tool provenance drifted during failed finalization") from error
        raise DraftDecisionError("draft decision receipt could not be created") from error
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort-root", required=True, type=Path)
    parser.add_argument("--log-dir", required=True, type=Path)
    parser.add_argument("--decision", type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--cohort-id")
    parser.add_argument("--action", choices=("select", "revise", "stop"))
    parser.add_argument("--variant-id")
    parser.add_argument(
        "--authority",
        choices=(
            "user_confirmed",
            "human_reviewer_confirmed",
            "user_delegated",
        ),
    )
    parser.add_argument("--reason")
    parser.add_argument("--adjustment", action="append", default=[])
    parser.add_argument("--convergence-reviewed", action="store_true")
    args = parser.parse_args(argv)
    try:
        structured_used = (
            any(
                value is not None
                for value in (
                    args.cohort_id,
                    args.action,
                    args.variant_id,
                    args.authority,
                    args.reason,
                )
            )
            or bool(args.adjustment)
            or args.convergence_reviewed
        )
        if args.decision is not None and structured_used:
            raise DraftDecisionError(
                "--decision cannot be combined with structured decision flags"
            )
        decision_path = args.decision
        if decision_path is None:
            if any(
                value is None
                for value in (
                    args.cohort_id,
                    args.action,
                    args.authority,
                    args.reason,
                )
            ):
                raise DraftDecisionError(
                    "structured decision requires cohort id, action, authority, and reason"
                )
            decision_path = write_structured_decision(
                args.output_root,
                cohort_id=args.cohort_id,
                action=args.action,
                variant_id=args.variant_id,
                authority=args.authority,
                reason=args.reason,
                adjustments=args.adjustment,
                convergence_reviewed=args.convergence_reviewed,
            )
        run(args.cohort_root, args.log_dir, decision_path, args.output_root)
    except (OSError, DraftDecisionError) as error:
        print(f"current draft decision failed: {error}", file=sys.stderr)
        return 1
    print("current draft decision recorded")
    if args.decision is None:
        print(f"draft decision input: {decision_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
