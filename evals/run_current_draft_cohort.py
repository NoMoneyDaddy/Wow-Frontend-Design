#!/usr/bin/env python3
"""Build and freshly capture one evaluator-owned multi-direction draft cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import stat
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "wow-frontend-design"
CAPTURE = ROOT / "evals" / "capture_current_visual_evidence.cjs"
CROSS_OUTPUT_AUDITOR = SKILL_ROOT / "scripts" / "cross_output_template_audit.cjs"
PLAN_LIMIT = 64 * 1024
BRIEF_LIMIT = 128 * 1024
TEXT_LIMIT = 2 * 1024
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PLAN_KEYS = {
    "schema_version",
    "cohort_id",
    "partition",
    "locale",
    "surface",
    "decision_question",
    "held_constant_axes",
    "selection_criteria",
    "variants",
}
VARIANT_KEYS = {
    "id",
    "hypothesis",
    "changed_axes",
    "expected_benefit",
    "risk",
    "disqualifier",
}
CAPTURE_STANDARD = {
    "profiles": [
        {
            "name": "desktop-default",
            "viewport": {"width": 1440, "height": 1000},
            "reducedMotion": "no-preference",
            "dpr": 1,
        },
        {
            "name": "mobile-default",
            "viewport": {"width": 390, "height": 844},
            "reducedMotion": "reduce",
            "dpr": 1,
        },
    ],
    "screenshot_mode": "viewport",
    "animations": "disabled",
    "caret": "hide",
    "network": "local-output-only",
}
CLAIM_BOUNDARY = "style_calibration_only"
CONVERGENCE_CODES = {
    "cross_output_template_candidate",
    "near_cross_output_template_candidate",
    "cross_output_visual_grammar_candidate",
    "cross_output_partial_visual_grammar_candidate",
}
AUDIT_RECOMPUTE_SOURCE = (
    "const fs=require('node:fs');"
    "const {auditCrossOutputTemplates}=require(process.argv[1]);"
    "const input=JSON.parse(fs.readFileSync(0,'utf8'));"
    "process.stdout.write(JSON.stringify(auditCrossOutputTemplates(input)));"
)

if str(ROOT / "evals") not in sys.path:
    sys.path.insert(0, str(ROOT / "evals"))

import run_current_skill_build as current_build  # noqa: E402
from validate_current_craft_acceptance import (  # noqa: E402
    CORE_CRAFT,
    CurrentCraftError,
    validate_current_capture_evidence,
)


class DraftCohortError(ValueError):
    """Raised when a draft cohort cannot preserve its comparison contract."""


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _record(path: Path) -> dict[str, Any]:
    info = path.stat()
    return {
        "bytes": info.st_size,
        "mode": f"{stat.S_IMODE(info.st_mode):04o}",
        "sha256": _digest(path),
    }


def _browser_contract_identity(
    path: Path, expected: dict[str, Any]
) -> tuple[int, int]:
    try:
        before = path.lstat()
        raw = path.read_bytes()
        after = path.lstat()
    except OSError as error:
        raise DraftCohortError("draft browser contract provenance is invalid") from error
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
        raise DraftCohortError("draft browser contract provenance is invalid")
    return before.st_dev, before.st_ino


def _regular_absolute_file(path: Path, label: str, limit: int) -> tuple[Path, bytes]:
    if not path.is_absolute():
        raise DraftCohortError(f"{label} must be an absolute regular file")
    try:
        info = path.lstat()
        canonical = path.resolve(strict=True)
    except OSError as error:
        raise DraftCohortError(f"{label} must be an absolute regular file") from error
    if (
        not stat.S_ISREG(info.st_mode)
        or path.is_symlink()
        or canonical != path
        or info.st_nlink != 1
        or not 1 <= info.st_size <= limit
    ):
        raise DraftCohortError(f"{label} must be a bounded unaliased regular file")
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise DraftCohortError(f"{label} could not be read") from error
    if len(raw) != info.st_size:
        raise DraftCohortError(f"{label} changed while being read")
    return path, raw


def _real_empty_directory(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise DraftCohortError(f"{label} must be an absolute real directory")
    try:
        info = path.lstat()
        canonical = path.resolve(strict=True)
    except OSError as error:
        raise DraftCohortError(f"{label} must be an absolute real directory") from error
    if not stat.S_ISDIR(info.st_mode) or path.is_symlink() or canonical != path:
        raise DraftCohortError(f"{label} must be an absolute real directory")
    if next(path.iterdir(), None) is not None:
        raise DraftCohortError(f"{label} must be empty")
    return path


class _PinnedDirectory:
    """Hold a directory identity while path-based child tools execute."""

    def __init__(self, path: Path, label: str) -> None:
        self.path = _real_empty_directory(path, label)
        self.label = label
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            self.descriptor = os.open(self.path, flags)
            info = os.fstat(self.descriptor)
        except OSError as error:
            raise DraftCohortError(f"{label} could not be pinned") from error
        self.identity = (info.st_dev, info.st_ino)
        self.assert_current()

    def close(self) -> None:
        if self.descriptor >= 0:
            os.close(self.descriptor)
            self.descriptor = -1

    def __enter__(self) -> "_PinnedDirectory":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def assert_current(self) -> None:
        try:
            info = self.path.lstat()
        except OSError as error:
            raise DraftCohortError(f"{self.label} identity drifted") from error
        if (
            not stat.S_ISDIR(info.st_mode)
            or self.path.is_symlink()
            or (info.st_dev, info.st_ino) != self.identity
        ):
            raise DraftCohortError(f"{self.label} identity drifted")

    def mkdir(self, name: str) -> Path:
        if not ID_PATTERN.fullmatch(name):
            raise DraftCohortError("pinned child directory name is invalid")
        try:
            os.mkdir(name, 0o700, dir_fd=self.descriptor)
        except OSError as error:
            raise DraftCohortError(f"{self.label} child directory could not be created") from error
        self.assert_current()
        child = self.path / name
        info = child.lstat()
        if not stat.S_ISDIR(info.st_mode) or child.is_symlink():
            raise DraftCohortError(f"{self.label} child directory identity is invalid")
        return child

    def write_exclusive(self, name: str, data: bytes) -> tuple[Path, dict[str, Any]]:
        if "/" in name or "\\" in name or not name or name in {".", ".."}:
            raise DraftCohortError("pinned output name is invalid")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(name, flags, 0o600, dir_fd=self.descriptor)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as error:
            raise DraftCohortError(f"{self.label} output could not be created") from error
        self.assert_current()
        return self.path / name, {"bytes": len(data), "sha256": _digest_bytes(data)}


def _outside_authoring_repository(path: Path, label: str) -> None:
    canonical = path.resolve(strict=True)
    repository = ROOT.resolve(strict=True)
    skill = SKILL_ROOT.resolve(strict=True)
    if canonical == repository or repository in canonical.parents or canonical == skill or skill in canonical.parents:
        raise DraftCohortError(f"{label} must remain outside the authoring repository")


def _separate(left: Path, right: Path, label: str) -> None:
    if left == right or left in right.parents or right in left.parents:
        raise DraftCohortError(f"{label} must not contain one another")


def _bounded_text(value: object, label: str) -> str:
    if not isinstance(value, str) or value != value.strip() or not value:
        raise DraftCohortError(f"{label} must be non-empty trimmed text")
    if len(value.encode("utf-8")) > TEXT_LIMIT or any(
        unicodedata.category(character).startswith("C") for character in value
    ):
        raise DraftCohortError(f"{label} must be bounded text without control characters")
    return value


def _identifier(value: object, label: str) -> str:
    text = _bounded_text(value, label)
    if len(text) > 64 or ID_PATTERN.fullmatch(text) is None:
        raise DraftCohortError(f"{label} must be bounded kebab-case")
    return text


def _identifier_list(value: object, label: str, minimum: int, maximum: int) -> list[str]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise DraftCohortError(f"{label} must contain {minimum}..{maximum} identifiers")
    result = [_identifier(item, f"{label}[{index}]") for index, item in enumerate(value)]
    if len(set(result)) != len(result):
        raise DraftCohortError(f"{label} must not contain duplicates")
    return result


def _text_list(value: object, label: str, minimum: int, maximum: int) -> list[str]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise DraftCohortError(f"{label} must contain {minimum}..{maximum} entries")
    result = [_bounded_text(item, f"{label}[{index}]") for index, item in enumerate(value)]
    if len(set(result)) != len(result):
        raise DraftCohortError(f"{label} must not contain duplicates")
    return result


def load_plan(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    path, raw = _regular_absolute_file(path, "plan", PLAN_LIMIT)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise DraftCohortError("plan must be strict UTF-8 JSON") from error
    if not isinstance(value, dict) or set(value) != PLAN_KEYS:
        raise DraftCohortError(f"plan schema must contain exactly {sorted(PLAN_KEYS)}")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise DraftCohortError("plan schema_version must be 1")
    cohort_id = _identifier(value["cohort_id"], "cohort_id")
    if not isinstance(value["partition"], str) or value["partition"] not in {"validation", "test"}:
        raise DraftCohortError("partition must be validation or test")
    if not isinstance(value["locale"], str) or value["locale"] not in {"zh-Hant", "en"}:
        raise DraftCohortError("locale must be zh-Hant or en")
    surface = _identifier(value["surface"], "surface")
    decision_question = _bounded_text(value["decision_question"], "decision_question")
    held_axes = _identifier_list(value["held_constant_axes"], "held_constant_axes", 4, 16)
    criteria = _text_list(value["selection_criteria"], "selection_criteria", 2, 8)
    variants = value["variants"]
    if not isinstance(variants, list) or not 2 <= len(variants) <= 3:
        raise DraftCohortError("variants must contain 2..3 directions")
    normalized_variants: list[dict[str, Any]] = []
    ids: set[str] = set()
    hypotheses: set[str] = set()
    contracts: set[str] = set()
    for index, item in enumerate(variants):
        if not isinstance(item, dict) or set(item) != VARIANT_KEYS:
            raise DraftCohortError(f"variants[{index}] schema must contain exactly {sorted(VARIANT_KEYS)}")
        identifier = _identifier(item["id"], f"variants[{index}].id")
        hypothesis = _bounded_text(item["hypothesis"], f"variants[{index}].hypothesis")
        changed_axes = _identifier_list(item["changed_axes"], f"variants[{index}].changed_axes", 2, 6)
        overlap = sorted(set(changed_axes) & set(held_axes))
        if overlap:
            raise DraftCohortError(
                f"variants[{index}].changed_axes overlap held_constant_axes: {', '.join(overlap)}"
            )
        normalized = {
            "id": identifier,
            "hypothesis": hypothesis,
            "changed_axes": changed_axes,
            "expected_benefit": _bounded_text(item["expected_benefit"], f"variants[{index}].expected_benefit"),
            "risk": _bounded_text(item["risk"], f"variants[{index}].risk"),
            "disqualifier": _bounded_text(item["disqualifier"], f"variants[{index}].disqualifier"),
        }
        contract = _digest_bytes(json.dumps(normalized, ensure_ascii=False, sort_keys=True).encode("utf-8"))
        if identifier in ids or hypothesis in hypotheses or contract in contracts:
            raise DraftCohortError("variant identities and hypotheses must be distinct")
        ids.add(identifier)
        hypotheses.add(hypothesis)
        contracts.add(contract)
        normalized_variants.append(normalized)
    normalized_plan = {
        "schema_version": 1,
        "cohort_id": cohort_id,
        "partition": value["partition"],
        "locale": value["locale"],
        "surface": surface,
        "decision_question": decision_question,
        "held_constant_axes": held_axes,
        "selection_criteria": criteria,
        "variants": normalized_variants,
    }
    return normalized_plan, {"bytes": len(raw), "sha256": _digest_bytes(raw)}


def direction_outputs(plan: dict[str, Any]) -> tuple[str, ...]:
    return ("DESIGN.md", *(f"directions/{variant['id']}.html" for variant in plan["variants"]))


def _validate_interaction_witnesses(
    plan: dict[str, Any],
    browser_contract: dict[str, Any] | None,
) -> None:
    interactive_pages = {
        f"directions/{variant['id']}.html"
        for variant in plan["variants"]
        if "interaction-emphasis" in variant["changed_axes"]
    }
    if not interactive_pages:
        return
    cases = browser_contract.get("cases", []) if isinstance(browser_contract, dict) else []
    for page in sorted(interactive_pages):
        witnessed = False
        for case in cases:
            if case["page"] != page:
                continue
            action_seen = False
            for step in case["steps"]:
                if step["action"] == "assert":
                    witnessed = witnessed or action_seen
                else:
                    action_seen = True
        if not witnessed:
            raise DraftCohortError(
                f"interaction-emphasis requires an action followed by a result assertion: {page}"
            )


def effective_brief(base_brief: str, plan: dict[str, Any]) -> str:
    payload = {
        "cohort_id": plan["cohort_id"],
        "locale": plan["locale"],
        "surface": plan["surface"],
        "decision_question": plan["decision_question"],
        "held_constant_axes": plan["held_constant_axes"],
        "selection_criteria": plan["selection_criteria"],
        "variants": plan["variants"],
    }
    return (
        f"{base_brief.rstrip()}\n\n"
        "--- EVALUATOR-OWNED DRAFT COHORT CONTRACT ---\n"
        "Create the exact requested outputs as one fast style-calibration cohort. Keep all held constants "
        "identical across directions. Give every direction a materially different, product-grounded composition, "
        "responsive transformation, typography hierarchy, and interaction emphasis according to its changed axes. "
        "For each variant, freeze a composition proof in DESIGN.md: protagonist, first-viewport region order, "
        "primary interaction placement, and mobile transformation. Every pair of variants must differ materially "
        "in at least two of those four fields. The same facts and functions do not require the same region order "
        "or shell; do not reuse one hero-selector-summary sequence and merely restyle it. "
        "Each HTML file must be a self-contained responsive specimen for the same representative product surface "
        "and include one bounded decision-critical interaction or state. DESIGN.md must record each direction's "
        "hypothesis, changed axes, held constants, expected benefit, risk, and disqualifier. Keep design rationale "
        "in DESIGN.md only. HTML copy must address the product audience; it must not discuss variants, page strategy, "
        "CTA visibility, design decisions, evaluation, or the implementation process. Do not build production "
        "integrations, duplicate a production application, add dependencies, or claim that a draft is selected, "
        "release-ready, original, or award-winning.\n"
        f"{json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}\n"
        "--- END EVALUATOR-OWNED DRAFT COHORT CONTRACT ---\n"
    )


def run_capture(
    workspace: Path,
    case_path: Path,
    evidence: Path,
    convergence_path: Path | None = None,
) -> None:
    command = ["node", str(CAPTURE), str(workspace), str(case_path), str(evidence)]
    if convergence_path is not None:
        command.append(str(convergence_path))
    try:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        try:
            _, _ = process.communicate(timeout=180)
        except subprocess.TimeoutExpired as error:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise DraftCohortError(
                "fresh capture execution failed; inspect the private evaluator workspace"
            ) from error
    except OSError as error:
        raise DraftCohortError("fresh capture execution failed; inspect the private evaluator workspace") from error
    if process.returncode != 0:
        raise DraftCohortError("fresh capture failed; inspect the private evaluator workspace")


def _tool_records() -> list[dict[str, Any]]:
    records = []
    for path in (
        Path(__file__).resolve(),
        Path(current_build.__file__).resolve(),
        CAPTURE.resolve(),
        CROSS_OUTPUT_AUDITOR.resolve(),
        (ROOT / "evals" / "playwright_browser_runtime.cjs").resolve(),
        (ROOT / "evals" / "validate_current_craft_acceptance.py").resolve(),
    ):
        records.append({"path": path.relative_to(ROOT).as_posix(), **_record(path)})
    return records


def _exact_object(value: object, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise DraftCohortError(f"{label} schema is invalid")
    return value


def _recompute_template_audit(observations_raw: bytes) -> dict[str, Any]:
    try:
        process = subprocess.Popen(
            ["node", "-e", AUDIT_RECOMPUTE_SOURCE, str(CROSS_OUTPUT_AUDITOR)],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        try:
            stdout, _ = process.communicate(input=observations_raw, timeout=30)
        except subprocess.TimeoutExpired as error:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise DraftCohortError("template audit recomputation failed") from error
    except OSError as error:
        raise DraftCohortError("template audit recomputation failed") from error
    if process.returncode != 0 or not 1 <= len(stdout) <= 2_000_000:
        raise DraftCohortError("template audit recomputation failed")
    try:
        value = json.loads(stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise DraftCohortError("template audit recomputation returned invalid JSON") from error
    if not isinstance(value, dict):
        raise DraftCohortError("template audit recomputation returned an invalid result")
    return value


def _convergence_summary(plan: dict[str, Any], evidence: Path) -> dict[str, Any]:
    observations_path, observations_raw = _regular_absolute_file(
        evidence / "macro-observations.json", "macro observations", 2_000_000
    )
    audit_path, audit_raw = _regular_absolute_file(
        evidence / "cross-output-template-audit.json", "template audit", 2_000_000
    )
    try:
        observation_mode = stat.S_IMODE(observations_path.stat().st_mode)
        audit_mode = stat.S_IMODE(audit_path.stat().st_mode)
    except OSError as error:
        raise DraftCohortError("draft convergence evidence identity drifted") from error
    if observation_mode != 0o600 or audit_mode != 0o600:
        raise DraftCohortError("draft convergence evidence must be private mode 0600")
    try:
        observations = json.loads(observations_raw.decode("utf-8"))
        audit_envelope = json.loads(audit_raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise DraftCohortError("draft convergence evidence must be strict UTF-8 JSON") from error
    observations = _exact_object(
        observations, {"schemaVersion", "cohort", "observations"}, "macro observations"
    )
    if (
        type(observations["schemaVersion"]) is not int
        or observations["schemaVersion"] != 1
        or observations["cohort"] != plan["cohort_id"]
        or not isinstance(observations["observations"], list)
    ):
        raise DraftCohortError("macro observation identity is invalid")
    variants = {variant["id"]: f"directions/{variant['id']}.html" for variant in plan["variants"]}
    expected_matrix = {
        (identifier, page, profile)
        for identifier, page in variants.items()
        for profile in ("desktop-default", "mobile-default")
    }
    observed_matrix: set[tuple[str, str, str]] = set()
    for index, item in enumerate(observations["observations"]):
        item = _exact_object(
            item,
            {"caseId", "route", "surface", "viewport", "state", "macroFingerprint"},
            f"macro observations[{index}]",
        )
        if any(
            not isinstance(item[field], str)
            for field in ("caseId", "route", "surface", "viewport", "state")
        ):
            raise DraftCohortError("draft convergence observation identity is invalid")
        identifier = item["caseId"]
        page = variants.get(identifier)
        identity = (identifier, page or "", item["viewport"])
        if (
            page is None
            or item["route"] != f"/{page}"
            or item["surface"] != plan["surface"]
            or item["state"] != "default"
            or item["viewport"] not in {"desktop-default", "mobile-default"}
            or not isinstance(item["macroFingerprint"], dict)
            or identity in observed_matrix
        ):
            raise DraftCohortError("draft convergence observation matrix is invalid")
        observed_matrix.add(identity)
    if observed_matrix != expected_matrix:
        raise DraftCohortError("draft convergence observation matrix is incomplete")

    audit_envelope = _exact_object(
        audit_envelope, {"schema_version", "observations", "result"}, "template audit envelope"
    )
    observation_record = _exact_object(
        audit_envelope["observations"], {"bytes", "sha256"}, "template audit observations"
    )
    if (
        type(audit_envelope["schema_version"]) is not int
        or audit_envelope["schema_version"] != 1
        or observation_record != {
            "bytes": len(observations_raw),
            "sha256": _digest_bytes(observations_raw),
        }
    ):
        raise DraftCohortError("template audit does not bind the macro observations")
    result = _exact_object(
        audit_envelope["result"],
        {"schemaVersion", "cohort", "status", "observationCount", "advisories", "claimBoundary"},
        "template audit result",
    )
    if (
        type(result["schemaVersion"]) is not int
        or result["schemaVersion"] != 1
        or result["cohort"] != plan["cohort_id"]
        or type(result["observationCount"]) is not int
        or result["observationCount"] != len(expected_matrix)
        or not isinstance(result["advisories"], list)
        or len(result["advisories"]) > 100
        or not isinstance(result["claimBoundary"], str)
        or not result["claimBoundary"].strip()
    ):
        raise DraftCohortError("template audit result identity is invalid")
    if result != _recompute_template_audit(observations_raw):
        raise DraftCohortError("template audit does not match the recomputed current result")
    counts = {code: 0 for code in sorted(CONVERGENCE_CODES)}
    affected: set[str] = set()
    detail_keys = {
        "cross_output_template_candidate": {
            "code", "caseIds", "fingerprintSha256", "observations", "confirmation"
        },
        "near_cross_output_template_candidate": {
            "code", "caseIds", "dominantFingerprintSha256", "exactFingerprintCount", "observations", "confirmation"
        },
        "cross_output_visual_grammar_candidate": {
            "code", "caseIds", "visualGrammarSha256", "observations", "confirmation"
        },
        "cross_output_partial_visual_grammar_candidate": {
            "code", "caseIds", "sharedAxes", "observations", "confirmation"
        },
    }
    for index, raw_advisory in enumerate(result["advisories"]):
        if not isinstance(raw_advisory, dict) or raw_advisory.get("code") not in CONVERGENCE_CODES:
            raise DraftCohortError("template audit advisory category is invalid")
        code = raw_advisory["code"]
        advisory = _exact_object(raw_advisory, detail_keys[code], f"template advisory[{index}]")
        case_ids = advisory["caseIds"]
        if (
            not isinstance(case_ids, list)
            or len(case_ids) < 2
            or any(not isinstance(identifier, str) for identifier in case_ids)
            or any(identifier not in variants for identifier in case_ids)
            or len(set(case_ids)) != len(case_ids)
        ):
            raise DraftCohortError("template audit advisory variants are invalid")
        counts[code] += 1
        affected.update(case_ids)
    expected_status = "advisories_present" if result["advisories"] else "no_exact_template_candidates"
    if result["status"] != expected_status:
        raise DraftCohortError("template audit status is inconsistent")
    return {
        "status": "completed",
        "result": result["status"],
        "policy": "advisory_only",
        "profiles": ["desktop-default", "mobile-default"],
        "observation_count": len(expected_matrix),
        "advisory_count": len(result["advisories"]),
        "advisory_counts": counts,
        "affected_variant_ids": sorted(affected),
        "review_required": bool(result["advisories"]),
        "observations": {
            "path": "evidence/macro-observations.json",
            "bytes": len(observations_raw),
            "mode": "0600",
            "sha256": _digest_bytes(observations_raw),
        },
        "audit": {
            "path": "evidence/cross-output-template-audit.json",
            "bytes": len(audit_raw),
            "mode": "0600",
            "sha256": _digest_bytes(audit_raw),
        },
        "claim_boundary": result["claimBoundary"],
    }


def _assert_execution_guards(
    cohort_pin: _PinnedDirectory,
    log_pin: _PinnedDirectory,
    tools_before: list[dict[str, Any]],
) -> None:
    cohort_pin.assert_current()
    log_pin.assert_current()
    if _tool_records() != tools_before:
        raise DraftCohortError("cohort tool provenance drifted during execution")


def _case(plan: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    run_suffix = manifest["brief"]["sha256"][:12]
    return {
        "schema_version": 1,
        "case_id": plan["cohort_id"],
        "run_id": f"draft-{plan['cohort_id']}-{run_suffix}",
        "partition": plan["partition"],
        "brief": manifest["brief"],
        "capture_plan": {
            "locale": plan["locale"],
            "state": "default",
            "pages": "all_html_outputs",
            "wait_condition": "load+fonts+two-raf+300ms+two-raf",
            "profiles": CAPTURE_STANDARD["profiles"],
        },
        "craft": {
            "rubric_version": "wow-core-craft-v1",
            "required_dimensions": sorted(CORE_CRAFT),
            "feedback_policy": "aggregate-failure-families-only",
        },
    }


def run(
    plan_path: Path,
    brief_path: Path,
    cohort_root: Path,
    log_dir: Path,
    *,
    model: str = current_build.CURRENT_DEFAULT_MODEL,
    reasoning_effort: str = current_build.CURRENT_DEFAULT_REASONING_EFFORT,
    hard_seconds: int = 1800,
    inactivity_seconds: int | None = None,
    max_repair_rounds: int = 1,
    browser_contract: Path | None = None,
) -> dict[str, Any]:
    if type(max_repair_rounds) is not int or not 0 <= max_repair_rounds <= 1:
        raise DraftCohortError("draft max repair rounds must be within 0..1")
    plan_path, _ = _regular_absolute_file(plan_path, "plan", PLAN_LIMIT)
    brief_path, brief_raw = _regular_absolute_file(brief_path, "brief", BRIEF_LIMIT)
    plan, plan_record = load_plan(plan_path)
    outputs = direction_outputs(plan)
    browser_contract_path: Path | None = None
    browser_contract_data: dict[str, Any] | None = None
    browser_contract_record: dict[str, Any] | None = None
    browser_contract_identity: tuple[int, int] | None = None
    if browser_contract is not None:
        try:
            (
                browser_contract_path,
                browser_contract_data,
                browser_contract_record,
            ) = current_build._load_browser_contract(browser_contract, outputs)
        except (OSError, current_build.RunnerError) as error:
            raise DraftCohortError("draft browser contract is invalid") from error
        _outside_authoring_repository(
            browser_contract_path, "draft browser contract"
        )
        browser_contract_identity = _browser_contract_identity(
            browser_contract_path, browser_contract_record
        )
    _validate_interaction_witnesses(plan, browser_contract_data)
    try:
        brief_text = brief_raw.decode("utf-8")
    except UnicodeError as error:
        raise DraftCohortError("brief must be strict UTF-8") from error
    if "\x00" in brief_text:
        raise DraftCohortError("brief must not contain NUL")
    cohort_root = _real_empty_directory(cohort_root, "cohort root")
    log_dir = _real_empty_directory(log_dir, "log directory")
    for path, label in ((plan_path, "plan"), (brief_path, "brief"), (cohort_root, "cohort root"), (log_dir, "log directory")):
        _outside_authoring_repository(path, label)
    _separate(cohort_root, log_dir, "cohort root and log directory")
    _separate(plan_path, cohort_root, "plan and cohort root")
    _separate(brief_path, cohort_root, "brief and cohort root")
    if browser_contract_path is not None:
        for boundary, label in (
            (plan_path, "plan"),
            (brief_path, "brief"),
            (cohort_root, "cohort root"),
            (log_dir, "log directory"),
        ):
            _separate(
                browser_contract_path,
                boundary,
                f"draft browser contract and {label}",
            )

    with _PinnedDirectory(cohort_root, "cohort root") as cohort_pin:
        with _PinnedDirectory(log_dir, "log directory") as log_pin:
            return _run_pinned(
                plan_path,
                brief_path,
                brief_raw,
                plan,
                plan_record,
                cohort_root,
                log_dir,
                cohort_pin,
                log_pin,
                model=model,
                reasoning_effort=reasoning_effort,
                hard_seconds=hard_seconds,
                inactivity_seconds=inactivity_seconds,
                max_repair_rounds=max_repair_rounds,
                browser_contract_path=browser_contract_path,
                browser_contract_record=browser_contract_record,
                browser_contract_identity=browser_contract_identity,
            )


def _run_pinned(
    plan_path: Path,
    brief_path: Path,
    brief_raw: bytes,
    plan: dict[str, Any],
    plan_record: dict[str, Any],
    cohort_root: Path,
    log_dir: Path,
    cohort_pin: _PinnedDirectory,
    log_pin: _PinnedDirectory,
    *,
    model: str,
    reasoning_effort: str,
    hard_seconds: int,
    inactivity_seconds: int | None,
    max_repair_rounds: int,
    browser_contract_path: Path | None,
    browser_contract_record: dict[str, Any] | None,
    browser_contract_identity: tuple[int, int] | None,
) -> dict[str, Any]:

    tools_before = _tool_records()
    outputs = direction_outputs(plan)

    def assert_current() -> None:
        _assert_execution_guards(cohort_pin, log_pin, tools_before)
        try:
            current_build._browser_contract_unchanged(
                browser_contract_path, browser_contract_record
            )
        except (OSError, current_build.RunnerError) as error:
            raise DraftCohortError(
                "draft browser contract drifted during execution"
            ) from error
        if (
            browser_contract_path is not None
            and browser_contract_record is not None
            and _browser_contract_identity(
                browser_contract_path, browser_contract_record
            )
            != browser_contract_identity
        ):
            raise DraftCohortError(
                "draft browser contract drifted during execution"
            )

    effective_text = effective_brief(brief_raw.decode("utf-8"), plan)
    effective_raw = effective_text.encode("utf-8")
    if len(effective_raw) > BRIEF_LIMIT:
        raise DraftCohortError("effective brief exceeds the current build limit")
    effective_path, effective_record = log_pin.write_exclusive(
        "draft-cohort-effective-brief.md", effective_raw
    )
    workspace = cohort_pin.mkdir("workspace")
    inactivity = inactivity_seconds if inactivity_seconds is not None else min(600, hard_seconds)
    assert_current()
    try:
        manifest = current_build.run(
            effective_path,
            workspace,
            model=model,
            reasoning_effort=reasoning_effort,
            hard_seconds=hard_seconds,
            inactivity_seconds=inactivity,
            outputs=outputs,
            log_dir=log_dir,
            max_repair_rounds=max_repair_rounds,
            case_mode="greenfield",
            browser_contract=browser_contract_path,
            skill_reference="references/design-exploration.md",
        )
    except (OSError, current_build.RunnerError) as error:
        assert_current()
        raise DraftCohortError("draft cohort build failed; inspect the bounded current-build receipt") from error
    assert_current()
    if manifest.get("browser_contract") != browser_contract_record:
        raise DraftCohortError("draft browser contract provenance is invalid")

    case_raw = (json.dumps(_case(plan, manifest), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    case_path, case_record = log_pin.write_exclusive("draft-cohort-case.json", case_raw)
    convergence_raw = (json.dumps({
        "schema_version": 1,
        "cohort_id": plan["cohort_id"],
        "surface": plan["surface"],
        "variants": [
            {"id": variant["id"], "page": f"directions/{variant['id']}.html"}
            for variant in plan["variants"]
        ],
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    convergence_path, convergence_config_record = log_pin.write_exclusive(
        "draft-cohort-convergence.json", convergence_raw
    )
    evidence = cohort_root / "evidence"
    assert_current()
    try:
        run_capture(workspace, case_path, evidence, convergence_path)
    except DraftCohortError:
        assert_current()
        raise
    assert_current()
    capture_receipt = evidence / "capture-receipt.json"
    try:
        validated_capture = validate_current_capture_evidence(
            workspace,
            case_path,
            capture_receipt,
            workspace / "run-manifest.json",
        )
    except CurrentCraftError as error:
        assert_current()
        raise DraftCohortError("fresh capture provenance validation failed") from error
    try:
        convergence = _convergence_summary(plan, evidence)
    except DraftCohortError:
        assert_current()
        raise

    _, plan_after = _regular_absolute_file(plan_path, "plan", PLAN_LIMIT)
    _, brief_after = _regular_absolute_file(brief_path, "brief", BRIEF_LIMIT)
    _, convergence_after = _regular_absolute_file(
        convergence_path, "draft convergence contract", PLAN_LIMIT
    )
    if (
        _digest_bytes(plan_after) != plan_record["sha256"]
        or _digest_bytes(brief_after) != _digest_bytes(brief_raw)
        or _digest_bytes(convergence_after) != convergence_config_record["sha256"]
    ):
        raise DraftCohortError("plan, brief, or convergence provenance drifted during the cohort run")
    assert_current()

    validated = {
        "capture_count": validated_capture["capture_count"],
        "capture_set_sha256": validated_capture["capture_set_sha256"],
        "capture_standard": validated_capture["capture_standard"],
    }

    manifest_path = workspace / "run-manifest.json"
    try:
        manifest_record_before = _record(manifest_path)
        capture_record_before = _record(capture_receipt)
        validated_again = validate_current_capture_evidence(
            workspace,
            case_path,
            capture_receipt,
            manifest_path,
        )
        convergence_again = _convergence_summary(plan, evidence)
        manifest_record = _record(manifest_path)
        capture_record = _record(capture_receipt)
    except (OSError, CurrentCraftError, DraftCohortError) as error:
        assert_current()
        raise DraftCohortError("draft cohort final provenance validation failed") from error
    validated_again_projection = {
        "capture_count": validated_again["capture_count"],
        "capture_set_sha256": validated_again["capture_set_sha256"],
        "capture_standard": validated_again["capture_standard"],
    }
    if (
        manifest_record_before != manifest_record
        or capture_record_before != capture_record
        or validated_again_projection != validated
        or convergence_again != convergence
    ):
        raise DraftCohortError("draft cohort final provenance drifted")
    assert_current()
    receipt = {
        "schema_version": 1,
        "status": "captured",
        "classification": "draft_cohort_captured",
        "claim_boundary": CLAIM_BOUNDARY,
        "cohort": {
            "cohort_id": plan["cohort_id"],
            "partition": plan["partition"],
            "locale": plan["locale"],
            "surface": plan["surface"],
            "decision_question": plan["decision_question"],
            "held_constant_axes": plan["held_constant_axes"],
            "selection_criteria": plan["selection_criteria"],
            "variant_count": len(plan["variants"]),
            "variants": plan["variants"],
        },
        "source": {
            "plan": plan_record,
            "base_brief": {"bytes": len(brief_raw), "sha256": _digest_bytes(brief_raw)},
            "effective_brief": effective_record,
            "case": case_record,
            "convergence_config": convergence_config_record,
            "run_manifest": {"path": "workspace/run-manifest.json", **manifest_record},
            "capture_receipt": {"path": "evidence/capture-receipt.json", **capture_record},
            "skill_tree_sha256": manifest["skill_snapshot"]["tree_sha256"],
            "outputs": manifest["outputs"],
        },
        "configuration": {
            "model": model,
            "reasoning_effort": reasoning_effort,
            "max_repair_rounds": max_repair_rounds,
            "browser_contract": browser_contract_record,
            "skill_reference": "references/design-exploration.md",
            "capture_standard": CAPTURE_STANDARD,
        },
        "evidence": {**validated, "convergence": convergence},
        "tools": tools_before,
    }
    try:
        encoded = (json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        assert_current()
        cohort_pin.write_exclusive("draft-cohort-receipt.json", encoded)
    except (OSError, TypeError, ValueError, DraftCohortError) as error:
        assert_current()
        raise DraftCohortError("draft cohort final receipt could not be created") from error
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--brief", required=True, type=Path)
    parser.add_argument("--cohort-root", required=True, type=Path)
    parser.add_argument("--log-dir", required=True, type=Path)
    parser.add_argument("--model", default=current_build.CURRENT_DEFAULT_MODEL)
    parser.add_argument(
        "--reasoning-effort",
        choices=("low", "medium", "high", "xhigh"),
        default=current_build.CURRENT_DEFAULT_REASONING_EFFORT,
    )
    parser.add_argument("--hard-seconds", type=int, default=1800)
    parser.add_argument("--inactivity-seconds", type=int)
    parser.add_argument("--browser-contract", type=Path)
    parser.add_argument("--max-repair-rounds", type=int, default=1)
    args = parser.parse_args(argv)
    try:
        run(
            args.plan,
            args.brief,
            args.cohort_root,
            args.log_dir,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            hard_seconds=args.hard_seconds,
            inactivity_seconds=args.inactivity_seconds,
            max_repair_rounds=args.max_repair_rounds,
            browser_contract=args.browser_contract,
        )
    except (OSError, DraftCohortError) as error:
        print(f"current draft cohort failed: {error}", file=sys.stderr)
        return 1
    print("current draft cohort captured")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
