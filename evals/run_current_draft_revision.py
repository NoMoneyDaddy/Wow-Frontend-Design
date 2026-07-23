#!/usr/bin/env python3
"""Render and freshly capture one bounded child of a recorded draft revision."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "wow-frontend-design"
BRIEF_LIMIT = 128 * 1024
CLAIM_BOUNDARY = "style_calibration_only"
DRAFT_EVIDENCE_POLICY = "style_calibration_only_not_release_evidence"

if str(ROOT / "evals") not in sys.path:
    sys.path.insert(0, str(ROOT / "evals"))

import record_current_draft_decision as decision  # noqa: E402
import run_current_draft_cohort as cohort  # noqa: E402
import run_current_skill_build as current_build  # noqa: E402
from validate_current_craft_acceptance import (  # noqa: E402
    CurrentCraftError,
    validate_current_capture_evidence,
)


class DraftRevisionError(ValueError):
    """Raised when a bounded draft revision cannot preserve its evidence contract."""


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _record(path: Path) -> dict[str, Any]:
    return cohort._record(path)


def _tool_records() -> list[dict[str, Any]]:
    paths = (
        Path(__file__).resolve(),
        Path(decision.__file__).resolve(),
        Path(cohort.__file__).resolve(),
        Path(current_build.__file__).resolve(),
        (ROOT / "evals" / "codex_isolated_build_core.py").resolve(),
        cohort.CAPTURE.resolve(),
        (ROOT / "evals" / "playwright_browser_runtime.cjs").resolve(),
        (ROOT / "evals" / "validate_current_craft_acceptance.py").resolve(),
    )
    return [
        {"path": path.relative_to(ROOT).as_posix(), **_record(path)}
        for path in paths
    ]


def _as_revision_error(callback: Any, *args: Any) -> Any:
    try:
        return callback(*args)
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise DraftRevisionError("draft revision source validation failed") from error


def _safe_build_failure_classification(error: BaseException) -> str:
    if isinstance(error, current_build.RunnerError):
        classification = str(error).partition(";")[0].strip()
        if classification in current_build.RECEIPT_CATEGORIES["failed"]:
            return classification
    return "execution_infrastructure_failure"


def _validate_parent(
    brief_path: Path,
    cohort_root: Path,
    cohort_log_dir: Path,
    decision_path: Path,
    decision_receipt_path: Path,
) -> dict[str, Any]:
    brief_path, brief_raw = _as_revision_error(
        cohort._regular_absolute_file, brief_path, "brief", BRIEF_LIMIT
    )
    validated = _as_revision_error(
        decision.validate_decision_receipt,
        cohort_root,
        cohort_log_dir,
        decision_path,
        decision_receipt_path,
    )
    source = _as_revision_error(decision.validate_cohort_source, cohort_root, cohort_log_dir)
    receipt = validated["receipt"]
    handoff = receipt.get("handoff", {})
    item = receipt.get("decision", {})
    variant = item.get("variant")
    if (
        receipt.get("status") != "recorded"
        or receipt.get("classification") != "draft_direction_revision_requested"
        or receipt.get("claim_boundary") != "selection_lineage_only_no_release_acceptance"
        or item.get("action") != "revise"
        or not isinstance(variant, dict)
        or not 1 <= len(item.get("adjustments", [])) <= 3
        or handoff.get("next_step") != "render_one_bounded_revision"
        or handoff.get("production_lane") is not None
        or handoff.get("required_revalidation")
        != ["one fresh desktop/mobile revision pair", "return to this decision checkpoint"]
        or handoff.get("draft_evidence_policy") != DRAFT_EVIDENCE_POLICY
    ):
        raise DraftRevisionError("draft revision requires a current recorded revise decision")
    decision_source = receipt.get("source", {})
    if (
        decision_source.get("cohort_receipt") != source["receipt_record"]
        or decision_source.get("cohort_id") != source["cohort"]["cohort_id"]
        or decision_source.get("capture_set_sha256")
        != source["capture"]["capture_set_sha256"]
        or decision_source.get("skill_tree_sha256")
        != source["receipt"]["source"]["skill_tree_sha256"]
    ):
        raise DraftRevisionError("draft revision decision and cohort provenance differ")
    base_variant_id = variant.get("id")
    base_page = handoff.get("source_page")
    if (
        not isinstance(base_variant_id, str)
        or base_page != f"directions/{base_variant_id}.html"
    ):
        raise DraftRevisionError("draft revision base page is invalid")
    cohort_source = source["receipt"]["source"]
    if cohort_source.get("base_brief") != {
        "bytes": len(brief_raw),
        "sha256": _digest_bytes(brief_raw),
    }:
        raise DraftRevisionError("draft revision brief does not match the parent cohort")
    output_records = {
        output.get("path"): output
        for output in cohort_source.get("outputs", [])
        if isinstance(output, dict)
    }
    design_record = output_records.get("DESIGN.md")
    design_path = cohort_root / "workspace" / "DESIGN.md"
    if (
        not isinstance(design_record, dict)
        or set(design_record) != {"path", "bytes", "mode", "sha256"}
        or design_record["path"] != "DESIGN.md"
    ):
        raise DraftRevisionError("draft revision design output provenance is invalid")
    _, design_raw = _as_revision_error(
        cohort._regular_absolute_file,
        design_path,
        "draft revision design output",
        current_build.FILE_LIMIT,
    )
    if (
        _record(design_path) != {
            key: design_record[key] for key in ("bytes", "mode", "sha256")
        }
        or _digest_bytes(design_raw) != design_record["sha256"]
    ):
        raise DraftRevisionError("draft revision design output drifted")
    base_record = output_records.get(base_page)
    base_path = cohort_root / "workspace" / base_page
    if (
        not isinstance(base_record, dict)
        or set(base_record) != {"path", "bytes", "mode", "sha256"}
        or base_record["path"] != base_page
    ):
        raise DraftRevisionError("draft revision base output provenance is invalid")
    _, base_raw = _as_revision_error(
        cohort._regular_absolute_file, base_path, "draft revision base page", current_build.FILE_LIMIT
    )
    if (
        _record(base_path) != {key: base_record[key] for key in ("bytes", "mode", "sha256")}
        or _digest_bytes(base_raw) != base_record["sha256"]
    ):
        raise DraftRevisionError("draft revision base page drifted")
    try:
        design_raw.decode("utf-8")
        base_raw.decode("utf-8")
        brief_text = brief_raw.decode("utf-8")
    except UnicodeError as error:
        raise DraftRevisionError("draft revision inputs must be strict UTF-8") from error
    if b"\x00" in design_raw or b"\x00" in base_raw or "\x00" in brief_text:
        raise DraftRevisionError("draft revision inputs must not contain NUL")
    skill = current_build.skill_tree_summary(SKILL_ROOT, "wow-frontend-design")
    if cohort_source.get("skill_tree_sha256") != skill["tree_sha256"]:
        raise DraftRevisionError("draft revision must use the current Skill tree")
    semantic_contract = {
        "base_variant": variant,
        "adjustments": item["adjustments"],
        "held_constant_axes": handoff["held_constant_axes"],
        "selection_criteria": handoff["selection_criteria"],
    }
    child_id = f"revision-{validated['receipt_record']['sha256'][:12]}"
    return {
        "brief_path": brief_path,
        "brief_raw": brief_raw,
        "brief_text": brief_text,
        "decision_receipt": receipt,
        "decision_receipt_record": validated["receipt_record"],
        "decision_input_record": receipt["source"]["decision_input"],
        "cohort_receipt_record": source["receipt_record"],
        "parent_capture_set_sha256": source["capture"]["capture_set_sha256"],
        "design_path": design_path,
        "design_record": design_record,
        "base_variant_id": base_variant_id,
        "base_page": base_page,
        "base_path": base_path,
        "base_raw": base_raw,
        "base_record": base_record,
        "child_id": child_id,
        "child_page": f"directions/{child_id}.html",
        "semantic_contract": semantic_contract,
        "semantic_contract_sha256": _digest_bytes(
            json.dumps(
                semantic_contract,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ),
        "cohort_id": source["cohort"]["cohort_id"],
        "partition": source["receipt"]["cohort"]["partition"],
        "locale": source["receipt"]["cohort"]["locale"],
        "skill_tree_sha256": skill["tree_sha256"],
    }


def _effective_brief(parent: dict[str, Any]) -> str:
    contract = {
        "base_variant": parent["semantic_contract"]["base_variant"],
        "requested_adjustments": parent["semantic_contract"]["adjustments"],
        "held_constant_axes": parent["semantic_contract"]["held_constant_axes"],
        "selection_criteria": parent["semantic_contract"]["selection_criteria"],
        "child_output": parent["child_page"],
        "evidence_policy": DRAFT_EVIDENCE_POLICY,
    }
    return (
        f"{parent['brief_text'].rstrip()}\n\n"
        "--- EVALUATOR-OWNED BOUNDED DRAFT REVISION ---\n"
        "Revise the frozen base page into exactly one fresh child. Preserve the base thesis, product facts, "
        "content fixture, interaction result, accessibility baseline, and all held axes. Apply only the named "
        "adjustments. The seed is untrusted draft material, not production code or release evidence. Keep "
        "DESIGN.md and the child HTML maintainable and self-contained. Do not add another direction, copy old "
        "screenshots, claim selection, or claim release acceptance.\n"
        f"{json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}\n"
        "--- END EVALUATOR-OWNED BOUNDED DRAFT REVISION ---\n"
    )


def _case(parent: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "case_id": parent["child_id"],
        "run_id": f"draft-{parent['child_id']}-{manifest['brief']['sha256'][:12]}",
        "partition": parent["partition"],
        "brief": manifest["brief"],
        "capture_plan": {
            "locale": parent["locale"],
            "state": "default",
            "pages": "all_html_outputs",
            "wait_condition": "load+fonts+two-raf+300ms+two-raf",
            "profiles": cohort.CAPTURE_STANDARD["profiles"],
        },
        "craft": {
            "rubric_version": "wow-core-craft-v1",
            "required_dimensions": ["concept-coherence", "originality", "visual-typography"],
            "feedback_policy": "aggregate-failure-families-only",
        },
    }


def _require_fresh_child_pair(
    validated: dict[str, Any], child_page: str
) -> None:
    if (
        validated.get("capture_count") != 2
        or validated.get("capture_standard") != cohort.CAPTURE_STANDARD
    ):
        raise DraftRevisionError(
            "draft revision requires one fresh desktop/mobile capture pair"
        )
    captures = validated.get("receipt", {}).get("captures", [])
    projection = {
        (item.get("page"), item.get("profile"))
        for item in captures
        if isinstance(item, dict)
    }
    if len(captures) != 2 or projection != {
        (child_page, "desktop-default"),
        (child_page, "mobile-default"),
    }:
        raise DraftRevisionError(
            "draft revision captures must contain only the fresh child pair"
        )


def _browser_contract_identity(
    path: Path, expected: dict[str, Any]
) -> tuple[int, int]:
    try:
        before = path.lstat()
        raw = path.read_bytes()
        after = path.lstat()
    except OSError as error:
        raise DraftRevisionError(
            "draft revision browser contract provenance is invalid"
        ) from error
    stable_before = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_nlink,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    stable_after = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_nlink,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if (
        stable_before != stable_after
        or not stat.S_ISREG(before.st_mode)
        or path.is_symlink()
        or before.st_nlink != 1
        or before.st_size != expected["bytes"]
        or _digest_bytes(raw) != expected["sha256"]
    ):
        raise DraftRevisionError(
            "draft revision browser contract provenance is invalid"
        )
    return before.st_dev, before.st_ino


def run(
    brief_path: Path,
    cohort_root: Path,
    cohort_log_dir: Path,
    decision_path: Path,
    decision_receipt_path: Path,
    revision_root: Path,
    revision_log_dir: Path,
    *,
    model: str = current_build.CURRENT_DEFAULT_MODEL,
    reasoning_effort: str = current_build.CURRENT_DEFAULT_REASONING_EFFORT,
    hard_seconds: int = 1800,
    inactivity_seconds: int | None = None,
    max_repair_rounds: int = current_build.MAX_REPAIR_ROUNDS,
    browser_contract: Path | None = None,
) -> dict[str, Any]:
    if (
        type(max_repair_rounds) is not int
        or not 0 <= max_repair_rounds <= current_build.MAX_REPAIR_ROUNDS
    ):
        raise DraftRevisionError(
            f"draft revision max repair rounds must be within 0..{current_build.MAX_REPAIR_ROUNDS}"
        )
    parent = _validate_parent(
        brief_path, cohort_root, cohort_log_dir, decision_path, decision_receipt_path
    )
    revision_root = _as_revision_error(
        cohort._real_empty_directory, revision_root, "revision root"
    )
    revision_log_dir = _as_revision_error(
        cohort._real_empty_directory, revision_log_dir, "revision log directory"
    )
    browser_contract_path: Path | None = None
    browser_contract_record: dict[str, Any] | None = None
    browser_contract_identity: tuple[int, int] | None = None
    if browser_contract is not None:
        try:
            (
                browser_contract_path,
                _browser_contract_data,
                browser_contract_record,
            ) = current_build._load_browser_contract(
                browser_contract, ("DESIGN.md", parent["child_page"])
            )
        except (OSError, current_build.RunnerError) as error:
            raise DraftRevisionError("draft revision browser contract is invalid") from error
        _as_revision_error(
            cohort._outside_authoring_repository,
            browser_contract_path,
            "draft revision browser contract",
        )
        browser_contract_identity = _browser_contract_identity(
            browser_contract_path, browser_contract_record
        )
    for path, label in (
        (revision_root, "revision root"),
        (revision_log_dir, "revision log directory"),
    ):
        _as_revision_error(cohort._outside_authoring_repository, path, label)
    for left, right, label in (
        (revision_root, revision_log_dir, "revision root and log directory"),
        (revision_root, cohort_root, "revision root and parent cohort"),
        (revision_log_dir, cohort_root, "revision log and parent cohort"),
        (revision_root, cohort_log_dir, "revision root and parent log"),
        (revision_log_dir, cohort_log_dir, "revision log and parent log"),
    ):
        _as_revision_error(cohort._separate, left, right, label)
    if browser_contract_path is not None:
        for boundary, label in (
            (brief_path, "brief"),
            (cohort_root, "parent cohort"),
            (cohort_log_dir, "parent log"),
            (decision_path, "decision input"),
            (decision_receipt_path, "decision receipt"),
            (revision_root, "revision root"),
            (revision_log_dir, "revision log"),
        ):
            _as_revision_error(
                cohort._separate,
                browser_contract_path,
                boundary,
                f"draft revision browser contract and {label}",
            )
    tools_before = _tool_records()

    def assert_current() -> None:
        observed = _validate_parent(
            brief_path, cohort_root, cohort_log_dir, decision_path, decision_receipt_path
        )
        if (
            observed["decision_receipt"] != parent["decision_receipt"]
            or observed["decision_receipt_record"] != parent["decision_receipt_record"]
            or observed["design_record"] != parent["design_record"]
            or observed["base_record"] != parent["base_record"]
            or observed["semantic_contract_sha256"] != parent["semantic_contract_sha256"]
            or _tool_records() != tools_before
        ):
            raise DraftRevisionError("draft revision source drifted during execution")
        try:
            current_build._browser_contract_unchanged(
                browser_contract_path, browser_contract_record
            )
        except (OSError, current_build.RunnerError) as error:
            raise DraftRevisionError(
                "draft revision browser contract drifted during execution"
            ) from error
        if (
            browser_contract_path is not None
            and browser_contract_record is not None
            and _browser_contract_identity(
                browser_contract_path, browser_contract_record
            )
            != browser_contract_identity
        ):
            raise DraftRevisionError(
                "draft revision browser contract drifted during execution"
            )

    with cohort._PinnedDirectory(revision_root, "revision root") as root_pin:
        with cohort._PinnedDirectory(revision_log_dir, "revision log directory") as log_pin:
            assert_current()
            effective_raw = _effective_brief(parent).encode("utf-8")
            if len(effective_raw) > BRIEF_LIMIT:
                raise DraftRevisionError("draft revision effective brief exceeds the build limit")
            effective_path, effective_record = log_pin.write_exclusive(
                "draft-revision-effective-brief.md", effective_raw
            )
            workspace = root_pin.mkdir("workspace")
            seed_root = Path(tempfile.mkdtemp(prefix="wow-draft-revision-seed-")).resolve()
            try:
                (seed_root / "directions").mkdir(mode=0o700)
                design_seed = seed_root / "DESIGN.md"
                shutil.copy2(parent["design_path"], design_seed)
                child_seed = seed_root / parent["child_page"]
                shutil.copy2(parent["base_path"], child_seed)
                seed_record = _record(child_seed)
                if (
                    _record(design_seed)
                    != {
                        key: parent["design_record"][key]
                        for key in ("bytes", "mode", "sha256")
                    }
                    or seed_record
                    != {
                        key: parent["base_record"][key]
                        for key in ("bytes", "mode", "sha256")
                    }
                ):
                    raise DraftRevisionError(
                        "draft revision seed provenance does not match parent outputs"
                    )
                assert_current()
                try:
                    manifest = current_build.run(
                        effective_path,
                        workspace,
                        model=model,
                        reasoning_effort=reasoning_effort,
                        hard_seconds=hard_seconds,
                        inactivity_seconds=(
                            inactivity_seconds
                            if inactivity_seconds is not None
                            else min(current_build.DEFAULT_INACTIVITY_SECONDS, hard_seconds)
                        ),
                        outputs=("DESIGN.md", parent["child_page"]),
                        log_dir=revision_log_dir,
                        max_repair_rounds=max_repair_rounds,
                        case_mode="retrofit",
                        seed_root=seed_root,
                        allow_changes=("DESIGN.md", parent["child_page"]),
                        browser_contract=browser_contract_path,
                        skill_reference="references/design-exploration.md",
                    )
                except Exception as error:
                    classification = _safe_build_failure_classification(error)
                    try:
                        assert_current()
                    except DraftRevisionError:
                        classification = "execution_infrastructure_failure"
                    raise DraftRevisionError(
                        f"draft revision build failed: {classification}"
                    ) from None
            finally:
                shutil.rmtree(seed_root, ignore_errors=True)
            assert_current()
            child_path = workspace / parent["child_page"]
            child_record = _record(child_path)
            seed_files = manifest.get("seed_snapshot", {}).get("files", [])
            if manifest.get("browser_contract") != browser_contract_record:
                raise DraftRevisionError(
                    "draft revision browser contract provenance is invalid"
                )
            if (
                child_record["sha256"] == seed_record["sha256"]
                or parent["child_page"] not in manifest.get("mutation", {}).get("observed_changes", [])
                or {
                    item.get("path")
                    for item in seed_files
                    if isinstance(item, dict)
                }
                != {"DESIGN.md", parent["child_page"]}
            ):
                raise DraftRevisionError("draft revision child did not measurably change")
            case_raw = (
                json.dumps(
                    _case(parent, manifest),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            ).encode("utf-8")
            case_path, case_record = log_pin.write_exclusive(
                "draft-revision-case.json", case_raw
            )
            evidence = revision_root / "evidence"
            assert_current()
            try:
                cohort.run_capture(workspace, case_path, evidence, None)
            except Exception:
                try:
                    assert_current()
                except DraftRevisionError:
                    pass
                raise DraftRevisionError(
                    "draft revision capture failed: execution_infrastructure_failure"
                ) from None
            assert_current()
            capture_receipt = evidence / "capture-receipt.json"
            try:
                validated = validate_current_capture_evidence(
                    workspace,
                    case_path,
                    capture_receipt,
                    workspace / "run-manifest.json",
                )
            except CurrentCraftError as error:
                raise DraftRevisionError(
                    "draft revision fresh capture provenance validation failed"
                ) from error
            _require_fresh_child_pair(validated, parent["child_page"])
            assert_current()
            manifest_path = workspace / "run-manifest.json"
            manifest_record = _record(manifest_path)
            capture_record = _record(capture_receipt)
            try:
                validated_final = validate_current_capture_evidence(
                    workspace, case_path, capture_receipt, manifest_path
                )
            except (OSError, CurrentCraftError) as error:
                raise DraftRevisionError(
                    "draft revision fresh capture provenance drifted"
                ) from error
            _require_fresh_child_pair(validated_final, parent["child_page"])
            if (
                validated_final != validated
                or _record(manifest_path) != manifest_record
                or _record(capture_receipt) != capture_record
            ):
                raise DraftRevisionError("draft revision capture drifted during finalization")
            receipt = {
                "schema_version": 1,
                "status": "captured",
                "classification": "draft_revision_captured",
                "claim_boundary": CLAIM_BOUNDARY,
                "parent": {
                    "cohort_receipt": parent["cohort_receipt_record"],
                    "decision_receipt": parent["decision_receipt_record"],
                    "decision_input": parent["decision_input_record"],
                    "base_variant_id": parent["base_variant_id"],
                    "base_page": parent["base_page"],
                    "base_output": parent["base_record"],
                    "capture_set_sha256": parent["parent_capture_set_sha256"],
                },
                "revision": {
                    "child_id": parent["child_id"],
                    "child_page": parent["child_page"],
                    "requested_adjustment_count": len(
                        parent["semantic_contract"]["adjustments"]
                    ),
                    "semantic_contract_sha256": parent["semantic_contract_sha256"],
                    "seed": seed_record,
                    "child": child_record,
                },
                "source": {
                    "brief": {
                        "bytes": len(parent["brief_raw"]),
                        "sha256": _digest_bytes(parent["brief_raw"]),
                    },
                    "effective_brief": effective_record,
                    "case": case_record,
                    "run_manifest": manifest_record,
                    "capture_receipt": capture_record,
                    "skill_tree_sha256": parent["skill_tree_sha256"],
                },
                "build": {
                    "case_mode": "retrofit",
                    "browser_contract": browser_contract_record,
                    "mutation": manifest["mutation"],
                    "repair_rounds": manifest.get("repair", {}).get("rounds_used", 0),
                },
                "evidence": {
                    "capture_count": validated["capture_count"],
                    "capture_set_sha256": validated["capture_set_sha256"],
                    "capture_standard": validated["capture_standard"],
                    "policy": "fresh_child_only_parent_capture_not_recaptured",
                },
                "handoff": {
                    "next_step": "return_to_draft_decision_checkpoint",
                    "production_lane": None,
                    "draft_evidence_policy": DRAFT_EVIDENCE_POLICY,
                },
                "tools": tools_before,
            }
            assert_current()
            root_pin.write_exclusive(
                "draft-revision-receipt.json",
                (
                    json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2)
                    + "\n"
                ).encode("utf-8"),
            )
            return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief", required=True, type=Path)
    parser.add_argument("--cohort-root", required=True, type=Path)
    parser.add_argument("--cohort-log-dir", required=True, type=Path)
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--decision-receipt", required=True, type=Path)
    parser.add_argument("--revision-root", required=True, type=Path)
    parser.add_argument("--revision-log-dir", required=True, type=Path)
    parser.add_argument("--model", default=current_build.CURRENT_DEFAULT_MODEL)
    parser.add_argument(
        "--reasoning-effort",
        choices=("low", "medium", "high", "xhigh"),
        default=current_build.CURRENT_DEFAULT_REASONING_EFFORT,
    )
    parser.add_argument("--hard-seconds", type=int, default=1800)
    parser.add_argument("--inactivity-seconds", type=int)
    parser.add_argument("--browser-contract", type=Path)
    parser.add_argument(
        "--max-repair-rounds", type=int, default=current_build.MAX_REPAIR_ROUNDS
    )
    args = parser.parse_args(argv)
    try:
        run(
            args.brief,
            args.cohort_root,
            args.cohort_log_dir,
            args.decision,
            args.decision_receipt,
            args.revision_root,
            args.revision_log_dir,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            hard_seconds=args.hard_seconds,
            inactivity_seconds=args.inactivity_seconds,
            max_repair_rounds=args.max_repair_rounds,
            browser_contract=args.browser_contract,
        )
    except (OSError, DraftRevisionError) as error:
        print(f"current draft revision failed: {error}", file=sys.stderr)
        return 1
    print("current draft revision captured")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
