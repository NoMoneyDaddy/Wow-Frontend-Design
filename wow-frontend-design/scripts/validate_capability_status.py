#!/usr/bin/env python3
"""Validate capability claims against checked-in artifact paths."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


STATUSES = {
    "tested_in_repo",
    "browser_observed",
    "observed_failed_acceptance",
    "rejected_before_publish",
    "definition_only",
    "documented_not_integration_tested",
    "partially_tested",
    "static_audit_only",
    "research_to_rule_only",
    "not_tested",
}
ROOT_KEYS = {"schema_version", "snapshot_at", "semantics", "capabilities"}
CAPABILITY_KEYS = {"id", "status", "claim", "artifacts", "boundary"}
REQUIRED_CAPABILITY_IDS = {
    "accessibility",
    "anti-ai-slop",
    "attention-behavioral-research",
    "award-quality",
    "claude-dashboard-pair",
    "cross-product-coverage",
    "deterministic-weak-model-guardrails",
    "framework-portability",
    "haiku-remediation-remake",
    "host-portability",
    "local-models",
    "locale-portability",
    "motion-svg-lottie",
    "search-aeo-geo",
    "skill-package",
    "structured-site-planning",
    "traditional-chinese-showcase",
    "webgl-advanced-media",
}


class CapabilityStatusError(ValueError):
    """Raised when the public capability ledger overstates or misframes evidence."""


def _load(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise CapabilityStatusError(f"refusing symlink status file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CapabilityStatusError(f"cannot read valid JSON: {error}") from error
    if not isinstance(data, dict):
        raise CapabilityStatusError("status root must be an object")
    return data


def validate(path: Path, repository_root: Path) -> int:
    data = _load(path)
    if set(data) != ROOT_KEYS:
        raise CapabilityStatusError("status root has missing or unexpected keys")
    if data["schema_version"] != 1:
        raise CapabilityStatusError("schema_version must equal 1")
    if not isinstance(data["snapshot_at"], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data["snapshot_at"]):
        raise CapabilityStatusError("snapshot_at must be YYYY-MM-DD")
    if not isinstance(data["semantics"], str) or len(data["semantics"].strip()) < 30:
        raise CapabilityStatusError("semantics must explain the evidence boundary")
    capabilities = data["capabilities"]
    if not isinstance(capabilities, list) or not capabilities:
        raise CapabilityStatusError("capabilities must be a non-empty array")

    root = repository_root.resolve()
    ids: set[str] = set()
    for index, item in enumerate(capabilities):
        label = f"capabilities[{index}]"
        if not isinstance(item, dict) or set(item) != CAPABILITY_KEYS:
            raise CapabilityStatusError(f"{label} must contain exactly {sorted(CAPABILITY_KEYS)}")
        capability_id = item["id"]
        if not isinstance(capability_id, str) or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", capability_id) is None:
            raise CapabilityStatusError(f"{label}.id must be lowercase kebab-case")
        if capability_id in ids:
            raise CapabilityStatusError(f"duplicate capability id: {capability_id}")
        ids.add(capability_id)
        if item["status"] not in STATUSES:
            raise CapabilityStatusError(f"{label}.status is not recognized")
        if not isinstance(item["claim"], str) or len(item["claim"].strip()) < 20:
            raise CapabilityStatusError(f"{label}.claim is too short")
        if not isinstance(item["boundary"], str) or len(item["boundary"].strip()) < 30:
            raise CapabilityStatusError(f"{label}.boundary must constrain the claim")
        artifacts = item["artifacts"]
        if not isinstance(artifacts, list) or not artifacts or len(artifacts) != len(set(artifacts)):
            raise CapabilityStatusError(f"{label}.artifacts must be unique and non-empty")
        for artifact in artifacts:
            if not isinstance(artifact, str) or not artifact:
                raise CapabilityStatusError(f"{label}.artifacts contains an invalid path")
            candidate = PurePosixPath(artifact)
            if candidate.is_absolute() or ".." in candidate.parts or "\x00" in artifact:
                raise CapabilityStatusError(f"{label}.artifacts contains an unsafe path: {artifact!r}")
            resolved = (root / candidate).resolve()
            try:
                resolved.relative_to(root)
            except ValueError as error:
                raise CapabilityStatusError(f"{label}.artifacts escapes repository root: {artifact!r}") from error
            if not resolved.exists() or resolved.is_symlink():
                raise CapabilityStatusError(f"{label}.artifacts is missing or a symlink: {artifact!r}")
    if ids != REQUIRED_CAPABILITY_IDS:
        missing = sorted(REQUIRED_CAPABILITY_IDS - ids)
        unexpected = sorted(ids - REQUIRED_CAPABILITY_IDS)
        raise CapabilityStatusError(f"capability inventory drift; missing={missing}, unexpected={unexpected}")
    return len(capabilities)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("status", type=Path)
    parser.add_argument("--repository-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        count = validate(args.status.expanduser(), args.repository_root.expanduser())
    except CapabilityStatusError as error:
        print(f"capability status invalid: {error}", file=sys.stderr)
        return 1
    print(f"capability status valid: {count} bounded claims")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
