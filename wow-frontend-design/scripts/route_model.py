#!/usr/bin/env python3
"""Route a caller-owned model profile without trusting model self-assessment."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


TASKS = {"AUDIT", "BUILD", "RETROFIT", "POLISH", "REPAIR"}
RISKS = {"low": 0, "medium": 1, "high": 2, "critical": 3}
LANES = {"CONSTRAINED", "STANDARD", "EXPLORATORY"}
MUTATING_TASKS = {"BUILD", "RETROFIT", "POLISH", "REPAIR"}
MIN_INDEPENDENT_RUNS = 3
MAX_PROFILE_BYTES = 1_000_000


class ProfileError(ValueError):
    """Raised when an evaluator-owned profile is malformed."""


def load_profile(path: Path) -> tuple[dict[str, Any], str]:
    if path.is_symlink():
        raise ProfileError("refusing symlink capability profile")
    if not path.is_file():
        raise ProfileError("capability profile must be a regular file")
    if path.stat().st_size > MAX_PROFILE_BYTES:
        raise ProfileError("capability profile exceeds size limit")
    raw = path.read_bytes()
    try:
        profile = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProfileError(f"invalid profile JSON: {exc}") from exc
    if not isinstance(profile, dict):
        raise ProfileError("profile must be a JSON object")
    return profile, hashlib.sha256(raw).hexdigest()


def require_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ProfileError(f"{key} must be a non-empty string")
    return value


def parse_iso_date(value: str, key: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ProfileError(f"{key} must use YYYY-MM-DD") from exc


def validate_profile(profile: dict[str, Any]) -> None:
    if profile.get("schema_version") != 1:
        raise ProfileError("schema_version must be 1")
    for key in (
        "profile_id", "owner", "provider", "model", "model_version",
        "evaluated_at", "valid_until", "skill_revision",
    ):
        require_string(profile, key)
    evaluated_at = parse_iso_date(profile["evaluated_at"], "evaluated_at")
    valid_until = parse_iso_date(profile["valid_until"], "valid_until")
    if valid_until < evaluated_at:
        raise ProfileError("valid_until cannot precede evaluated_at")
    cells = profile.get("cells")
    if not isinstance(cells, list) or not cells:
        raise ProfileError("cells must be a non-empty array")
    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            raise ProfileError(f"cells[{index}] must be an object")
        if cell.get("task") not in TASKS | {"*"}:
            raise ProfileError(f"cells[{index}].task is invalid")
        if not isinstance(cell.get("locale"), str) or not cell["locale"]:
            raise ProfileError(f"cells[{index}].locale must be a string")
        if cell.get("max_risk") not in RISKS:
            raise ProfileError(f"cells[{index}].max_risk is invalid")
        capabilities = cell.get("required_capabilities")
        if not isinstance(capabilities, list) or any(
            not isinstance(value, str) or not value for value in capabilities
        ):
            raise ProfileError(
                f"cells[{index}].required_capabilities must be a string array"
            )
        for key in (
            "runs", "contract_passes", "invariant_passes",
            "unsupported_claim_failures",
        ):
            value = cell.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ProfileError(f"cells[{index}].{key} must be a non-negative integer")
        if not isinstance(cell.get("independent_evaluation"), bool):
            raise ProfileError(f"cells[{index}].independent_evaluation must be boolean")
        if cell.get("recommended_lane") not in LANES:
            raise ProfileError(f"cells[{index}].recommended_lane is invalid")


def choose_cell(
    cells: list[dict[str, Any]], task: str, locale: str, risk: str
) -> dict[str, Any] | None:
    candidates = [
        cell for cell in cells
        if cell["task"] in {task, "*"}
        and cell["locale"] in {locale, "*"}
        and RISKS[risk] <= RISKS[cell["max_risk"]]
    ]
    if not candidates:
        return None
    candidates.sort(
        key=lambda cell: (
            cell["task"] == task,
            cell["locale"] == locale,
            -RISKS[cell["max_risk"]],
        ),
        reverse=True,
    )
    return candidates[0]


def route(
    profile: dict[str, Any], *, task: str, locale: str, risk: str,
    capabilities: set[str], as_of: date, allow_exploratory: bool,
) -> tuple[str, list[str], dict[str, Any] | None]:
    if task in MUTATING_TASKS and "write" not in capabilities:
        return "ADVISORY", ["mutating task has no write capability"], None
    if task == "AUDIT" and "read" not in capabilities:
        return "ADVISORY", ["audit has no read capability"], None
    if as_of > parse_iso_date(profile["valid_until"], "valid_until"):
        return "CONSTRAINED", ["capability profile is stale"], None
    if risk in {"high", "critical"}:
        return "CONSTRAINED", ["high-risk work requires specialist or human review"], None

    cell = choose_cell(profile["cells"], task, locale, risk)
    if cell is None:
        return "CONSTRAINED", ["no matching independent benchmark cell"], None

    reasons: list[str] = []
    missing = sorted(set(cell["required_capabilities"]) - capabilities)
    if missing:
        reasons.append("missing capabilities: " + ", ".join(missing))
    runs = cell["runs"]
    if runs < MIN_INDEPENDENT_RUNS:
        reasons.append(f"fewer than {MIN_INDEPENDENT_RUNS} independent runs")
    if not cell["independent_evaluation"]:
        reasons.append("evaluation was not independent")
    if cell["contract_passes"] != runs:
        reasons.append("not every run passed the output contract")
    if cell["invariant_passes"] != runs:
        reasons.append("not every run preserved required invariants")
    if cell["unsupported_claim_failures"] != 0:
        reasons.append("unsupported verification claims were observed")
    if reasons:
        return "CONSTRAINED", reasons, cell

    recommended = cell["recommended_lane"]
    if recommended == "EXPLORATORY" and not allow_exploratory:
        return "STANDARD", ["exploratory routing was not explicitly enabled"], cell
    return recommended, ["matched fresh evaluator-owned benchmark evidence"], cell


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--task", required=True, choices=sorted(TASKS))
    parser.add_argument("--locale", required=True)
    parser.add_argument("--risk", required=True, choices=sorted(RISKS))
    parser.add_argument("--capability", action="append", default=[])
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--allow-exploratory", action="store_true")
    parser.add_argument("--expected-profile-sha256")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        profile, digest = load_profile(args.profile)
        validate_profile(profile)
        as_of = parse_iso_date(args.as_of, "as_of")
        if args.expected_profile_sha256 and digest != args.expected_profile_sha256:
            raise ProfileError("profile SHA-256 does not match evaluator-frozen value")
        lane, reasons, cell = route(
            profile, task=args.task, locale=args.locale, risk=args.risk,
            capabilities=set(args.capability), as_of=as_of,
            allow_exploratory=args.allow_exploratory,
        )
    except (OSError, ProfileError) as exc:
        print(json.dumps({"lane": "CONSTRAINED", "error": str(exc)}))
        return 2

    print(json.dumps({
        "lane": lane,
        "reasons": reasons,
        "profile_id": profile["profile_id"],
        "profile_sha256": digest,
        "provider": profile["provider"],
        "model": profile["model"],
        "model_version": profile["model_version"],
        "task": args.task,
        "locale": args.locale,
        "risk": args.risk,
        "matched_cell": cell,
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
