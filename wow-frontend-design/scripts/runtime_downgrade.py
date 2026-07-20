#!/usr/bin/env python3
"""Apply evaluator-owned, one-way runtime lane downgrades."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


LANE_RANK = {
    "ADVISORY": 0,
    "CONSTRAINED": 1,
    "STANDARD": 2,
    "EXPLORATORY": 3,
}
EVENT_CODES = {
    "EVALUATOR_BOUNDARY_VIOLATION",
    "INACTIVITY_TIMEOUT",
    "MUTATION_CAPABILITY_MISSING",
    "OUTPUT_CONTRACT_FAILED",
    "PRESERVE_INVARIANT_FAILED",
    "REPAIR_FINDING",
    "SECURITY_PERMISSION_BLOCK",
    "TRANSIENT_TOOL_FAILURE",
    "UNSUPPORTED_CLAIM",
    "VERIFICATION_CAPABILITY_MISSING",
}
ROOT_KEYS = {
    "schema_version", "run_id", "initial_lane", "max_mutation_attempts", "events"
}
EVENT_KEYS = {
    "sequence", "code", "failure_key", "consecutive", "progress_observed",
    "mutation_attempts_used",
}
MUTATION_AUTHORIZING_ACTIONS = {
    "NARROW_AND_CONTINUE",
    "REMOVE_CLAIM_AND_RECHECK",
    "REPAIR_AND_RECHECK",
    "RESTART_ISOLATED",
    "RESTORE_AND_RECHECK",
}
CANONICAL_MAX_MUTATION_ATTEMPTS = 3
MAX_EVENTS = 100
MAX_INPUT_BYTES = 1_000_000


class RuntimeDowngradeError(ValueError):
    """Raised when a runtime event stream is malformed or unsafe."""


def _load(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise RuntimeDowngradeError("runtime event input must be a regular non-symlink file")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise RuntimeDowngradeError("runtime event input exceeds size limit")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeDowngradeError(f"cannot read valid runtime event JSON: {error}") from error
    if not isinstance(value, dict):
        raise RuntimeDowngradeError("runtime event input must be an object")
    return value


def validate(payload: dict[str, Any]) -> None:
    if set(payload) != ROOT_KEYS:
        raise RuntimeDowngradeError("runtime event input has missing or unexpected root keys")
    if type(payload["schema_version"]) is not int or payload["schema_version"] != 2:
        raise RuntimeDowngradeError("schema_version must equal 2")
    if not isinstance(payload["run_id"], str) or not payload["run_id"].strip():
        raise RuntimeDowngradeError("run_id must be a non-empty string")
    if not isinstance(payload["initial_lane"], str) or payload["initial_lane"] not in LANE_RANK:
        raise RuntimeDowngradeError("initial_lane is invalid")
    maximum = payload["max_mutation_attempts"]
    if (
        type(maximum) is not int
        or not 1 <= maximum <= CANONICAL_MAX_MUTATION_ATTEMPTS
    ):
        raise RuntimeDowngradeError(
            f"max_mutation_attempts must be within 1..{CANONICAL_MAX_MUTATION_ATTEMPTS}"
        )
    events = payload["events"]
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        raise RuntimeDowngradeError(f"events must be an array with at most {MAX_EVENTS} entries")

    previous_failure_key: str | None = None
    previous_consecutive = 0
    previous_mutation_attempts = 0
    for index, event in enumerate(events, start=1):
        label = f"events[{index - 1}]"
        if not isinstance(event, dict) or set(event) != EVENT_KEYS:
            raise RuntimeDowngradeError(f"{label} has missing or unexpected keys")
        if event["sequence"] != index:
            raise RuntimeDowngradeError(f"{label}.sequence must be contiguous and one-based")
        if not isinstance(event["code"], str) or event["code"] not in EVENT_CODES:
            raise RuntimeDowngradeError(f"{label}.code is invalid")
        if not isinstance(event["failure_key"], str) or re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", event["failure_key"]
        ) is None:
            raise RuntimeDowngradeError(f"{label}.failure_key is invalid")
        if not isinstance(event["consecutive"], int) or isinstance(event["consecutive"], bool) or event["consecutive"] < 1:
            raise RuntimeDowngradeError(f"{label}.consecutive must be a positive integer")
        if not isinstance(event["progress_observed"], bool):
            raise RuntimeDowngradeError(f"{label}.progress_observed must be boolean")
        attempts_used = event["mutation_attempts_used"]
        if (
            type(attempts_used) is not int
            or not previous_mutation_attempts <= attempts_used <= maximum
        ):
            raise RuntimeDowngradeError(
                f"{label}.mutation_attempts_used must be monotonic and within the run budget"
            )
        if event["progress_observed"]:
            expected = 1
        elif event["failure_key"] == previous_failure_key:
            expected = previous_consecutive + 1
        else:
            expected = 1
        if event["consecutive"] != expected:
            raise RuntimeDowngradeError(f"{label}.consecutive disagrees with the event stream")
        if event["progress_observed"] and event["code"] != "INACTIVITY_TIMEOUT":
            raise RuntimeDowngradeError(
                f"{label}.progress_observed is only valid for INACTIVITY_TIMEOUT"
            )
        if event["progress_observed"]:
            previous_failure_key = None
            previous_consecutive = 0
        else:
            previous_failure_key = event["failure_key"]
            previous_consecutive = event["consecutive"]
        previous_mutation_attempts = attempts_used


def cap_lane(current: str, maximum: str) -> str:
    """Return the lower lane; this function can never promote a run."""
    return current if LANE_RANK[current] <= LANE_RANK[maximum] else maximum


def transition(current: str, event: dict[str, Any]) -> tuple[str, str, str]:
    code = event["code"]
    consecutive = event["consecutive"]

    if code == "INACTIVITY_TIMEOUT":
        if event["progress_observed"]:
            return current, "EXTEND_TIMEOUT", "evaluator-owned progress is still advancing"
        if consecutive < 3:
            return current, "RETRY", "inactivity timeout is retryable before the fuse threshold"
        return cap_lane(current, "CONSTRAINED"), "HAND_OFF_BEST", "three consecutive inactive attempts reached the fuse"

    if code == "TRANSIENT_TOOL_FAILURE":
        if consecutive < 3:
            return current, "RETRY", "transient tool failure is retryable before the fuse threshold"
        return cap_lane(current, "CONSTRAINED"), "HAND_OFF_BEST", "three consecutive tool failures reached the fuse"

    if code == "REPAIR_FINDING":
        if consecutive < 3:
            return current, "REPAIR_AND_RECHECK", "repair finding remains an internal self-correction signal"
        return cap_lane(current, "CONSTRAINED"), "HAND_OFF_BEST", "the same repair finding survived three fixes"

    if code == "OUTPUT_CONTRACT_FAILED":
        return cap_lane(current, "CONSTRAINED"), "NARROW_AND_CONTINUE", "structured output contract failed"
    if code == "PRESERVE_INVARIANT_FAILED":
        return cap_lane(current, "CONSTRAINED"), "RESTORE_AND_RECHECK", "a caller-owned preserve invariant failed"
    if code == "UNSUPPORTED_CLAIM":
        return cap_lane(current, "CONSTRAINED"), "REMOVE_CLAIM_AND_RECHECK", "verification wording exceeded evidence"
    if code == "VERIFICATION_CAPABILITY_MISSING":
        return cap_lane(current, "CONSTRAINED"), "CONTINUE_WITH_UNVERIFIED_GATE", "a required verification capability is unavailable"
    if code == "EVALUATOR_BOUNDARY_VIOLATION":
        return cap_lane(current, "CONSTRAINED"), "RESTART_ISOLATED", "the implementation crossed the evaluator boundary"
    if code == "MUTATION_CAPABILITY_MISSING":
        return "ADVISORY", "STOP_MUTATION", "safe write capability is unavailable"
    if code == "SECURITY_PERMISSION_BLOCK":
        return "ADVISORY", "STOP_MUTATION", "security or permission policy blocks further mutation"
    raise RuntimeDowngradeError(f"unhandled event code: {code}")


def apply_events(payload: dict[str, Any]) -> dict[str, Any]:
    validate(payload)
    current = payload["initial_lane"]
    transitions: list[dict[str, Any]] = []
    for event in payload["events"]:
        before = current
        current, action, reason = transition(current, event)
        if (
            action in MUTATION_AUTHORIZING_ACTIONS
            and event["mutation_attempts_used"] >= payload["max_mutation_attempts"]
        ):
            current = cap_lane(current, "CONSTRAINED")
            action = "HAND_OFF_BEST"
            reason = "the evaluator-owned global mutation budget is exhausted"
        if LANE_RANK[current] > LANE_RANK[before]:
            raise RuntimeDowngradeError("internal error: runtime transition attempted an upgrade")
        transitions.append({
            **event,
            "before_lane": before,
            "after_lane": current,
            "action": action,
            "reason": reason,
        })
    return {
        "schema_version": 2,
        "run_id": payload["run_id"],
        "initial_lane": payload["initial_lane"],
        "max_mutation_attempts": payload["max_mutation_attempts"],
        "final_lane": current,
        "automatic_upgrade_permitted": False,
        "transitions": transitions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path)
    args = parser.parse_args()
    try:
        result = apply_events(_load(args.events.expanduser()))
    except RuntimeDowngradeError as error:
        print(json.dumps({"error": str(error), "automatic_upgrade_permitted": False}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
