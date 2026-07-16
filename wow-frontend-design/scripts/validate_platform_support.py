#!/usr/bin/env python3
"""Validate the frozen platform/source snapshot without upgrading its claims."""

from __future__ import annotations

import argparse
import json
import re
import stat
import sys
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit


MAX_BYTES = 1_048_576
MAX_DEPTH = 32
SOURCE_ROOT_KEYS = {"schema_version", "retrieved_at", "policy", "sources"}
SOURCE_KEYS = {"id", "publisher", "url", "retrieved_at", "mutable", "claims"}
MATRIX_ROOT_KEYS = {"schema_version", "snapshot_at", "semantics", "source_snapshot", "targets"}
TARGET_KEYS = {
    "id",
    "category",
    "official_status",
    "repository_status",
    "checks",
    "source_ids",
    "artifacts",
    "boundary",
}
CHECK_KEYS = {"install", "discovery", "invocation", "implementation", "browser", "visual"}
APPROVED_SOURCE_HOSTS = {
    "agentskills.io",
    "cli.github.com",
    "developers.openai.com",
    "docs.anthropic.com",
    "docs.github.com",
    "geminicli.com",
    "platform.claude.com",
    "playwright.dev",
}
CATEGORIES = {"host", "operating_system", "browser", "device", "environment", "model"}
PREFIXES = {
    "host": "host-",
    "operating_system": "os-",
    "browser": "browser-",
    "device": "device-",
    "environment": "environment-",
    "model": "model-",
}
OFFICIAL_STATUSES = {
    "supported",
    "preview",
    "best_effort",
    "model_variable",
    "not_documented",
    "not_applicable",
}
REPOSITORY_STATUSES = {
    "browser_observed",
    "tested_in_ci",
    "partially_tested",
    "observed_failed",
    "historic_only",
    "documented_not_tested",
    "not_tested",
}
CHECK_STATUSES = {"passed", "failed", "partial", "historic_only", "not_run", "not_applicable"}
REQUIRED_TARGET_IDS = {
    "browser-chrome-edge-channels",
    "browser-chromium",
    "browser-firefox",
    "browser-webkit",
    "device-physical-android-chrome",
    "device-physical-ios-safari",
    "environment-claude-code-remote",
    "environment-github-actions-ubuntu",
    "environment-local-workspace",
    "environment-no-network-sandbox",
    "environment-read-only-home",
    "host-claude-ai",
    "host-claude-api",
    "host-claude-code",
    "host-codex-chatgpt-desktop",
    "host-codex-cli",
    "host-codex-ide-extension",
    "host-custom-agent-wrapper",
    "host-gemini-cli",
    "host-github-copilot-cli",
    "host-github-copilot-jetbrains",
    "host-github-copilot-vscode",
    "model-claude-haiku-opus",
    "model-gemini-offerings",
    "model-github-copilot-offerings",
    "model-gpt-5-4-mini",
    "model-local-runtime",
    "model-other-codex-models",
    "os-linux-native",
    "os-macos-native",
    "os-windows-native",
    "os-windows-wsl",
}
ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class PlatformSupportError(ValueError):
    """Raised when support coordinates, evidence stages or paths drift."""


def _reject_scheduled_recheck(value: Any, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise PlatformSupportError("JSON nesting exceeds the bounded depth")
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).casefold().replace("-", "_")
            scheduled = (
                normalized.startswith("next_review")
                or normalized.startswith("next_check")
                or normalized.startswith("next_recheck")
                or normalized.startswith("recheck_at")
                or normalized.startswith("review_due")
            )
            if scheduled:
                raise PlatformSupportError(f"scheduled recheck field is forbidden: {key!r}")
            _reject_scheduled_recheck(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _reject_scheduled_recheck(child, depth + 1)


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        mode = path.lstat().st_mode
    except OSError as error:
        raise PlatformSupportError(f"cannot stat {label}: {error}") from error
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise PlatformSupportError(f"{label} must be a regular non-symlink file")
    if path.stat().st_size > MAX_BYTES:
        raise PlatformSupportError(f"{label} exceeds {MAX_BYTES} bytes")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PlatformSupportError(f"cannot read valid {label}: {error}") from error
    if not isinstance(data, dict):
        raise PlatformSupportError(f"{label} root must be an object")
    _reject_scheduled_recheck(data)
    return data


def _date(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise PlatformSupportError(f"{label} must be YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise PlatformSupportError(f"{label} must be YYYY-MM-DD") from error
    if parsed.isoformat() != value:
        raise PlatformSupportError(f"{label} must be canonical YYYY-MM-DD")
    return value


def _safe_repo_file(raw: Any, root: Path, label: str) -> Path:
    if not isinstance(raw, str) or not raw or "\x00" in raw or "\\" in raw:
        raise PlatformSupportError(f"{label} must be a non-empty POSIX path")
    relative = PurePosixPath(raw)
    if not relative.parts or relative == PurePosixPath(".") or relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
        raise PlatformSupportError(f"{label} is unsafe: {raw!r}")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise PlatformSupportError(f"{label} traverses a symlink: {raw!r}")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as error:
        raise PlatformSupportError(f"{label} is missing or escapes the repository: {raw!r}") from error
    if not (resolved.is_file() or resolved.is_dir()):
        raise PlatformSupportError(f"{label} is not a regular artifact: {raw!r}")
    return resolved


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        raise PlatformSupportError(f"{label} must be a non-empty string array")
    if len(value) != len(set(value)):
        raise PlatformSupportError(f"{label} must contain unique values")
    return value


def _validate_sources(data: dict[str, Any]) -> set[str]:
    if set(data) != SOURCE_ROOT_KEYS or data.get("schema_version") != 1:
        raise PlatformSupportError("source snapshot root or schema_version is invalid")
    snapshot_date = _date(data["retrieved_at"], "source snapshot retrieved_at")
    if not isinstance(data["policy"], str) or len(data["policy"].strip()) < 60:
        raise PlatformSupportError("source snapshot policy must state its evidence boundary")
    sources = data["sources"]
    if not isinstance(sources, list) or not sources:
        raise PlatformSupportError("sources must be a non-empty array")
    ids: set[str] = set()
    urls: set[str] = set()
    for index, source in enumerate(sources):
        label = f"sources[{index}]"
        if not isinstance(source, dict) or set(source) != SOURCE_KEYS:
            raise PlatformSupportError(f"{label} must contain exactly {sorted(SOURCE_KEYS)}")
        source_id = source["id"]
        if not isinstance(source_id, str) or ID_PATTERN.fullmatch(source_id) is None or source_id in ids:
            raise PlatformSupportError(f"{label}.id must be unique lowercase kebab-case")
        ids.add(source_id)
        if not isinstance(source["publisher"], str) or not source["publisher"].strip():
            raise PlatformSupportError(f"{label}.publisher is invalid")
        url = source["url"] if isinstance(source["url"], str) else ""
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in APPROVED_SOURCE_HOSTS
            or parsed.port not in {None, 443}
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
            or url in urls
        ):
            raise PlatformSupportError(f"{label}.url is not a unique approved official HTTPS coordinate")
        urls.add(url)
        if _date(source["retrieved_at"], f"{label}.retrieved_at") != snapshot_date:
            raise PlatformSupportError(f"{label}.retrieved_at must equal the snapshot date")
        if source["mutable"] is not True:
            raise PlatformSupportError(f"{label}.mutable must acknowledge upstream mutability")
        _string_list(source["claims"], f"{label}.claims")
    return ids


def _validate_target_consistency(target: dict[str, Any], label: str) -> None:
    status = target["repository_status"]
    values = target["checks"]
    if status == "browser_observed" and not (values["browser"] == "passed" and values["visual"] == "passed"):
        raise PlatformSupportError(f"{label} browser_observed requires passed browser and visual checks")
    if status == "observed_failed" and "failed" not in values.values():
        raise PlatformSupportError(f"{label} observed_failed requires at least one failed check")
    if status == "historic_only" and not all(
        value in {"historic_only", "not_applicable"} for value in values.values()
    ):
        raise PlatformSupportError(f"{label} historic_only cannot contain current evidence")
    if status in {"documented_not_tested", "not_tested"} and any(
        value in {"passed", "failed", "partial", "historic_only"} for value in values.values()
    ):
        raise PlatformSupportError(f"{label} untested status cannot contain observed evidence")


def validate(matrix_path: Path, repository_root: Path) -> tuple[int, int]:
    root = repository_root.resolve(strict=True)
    matrix = _load_json(matrix_path, "platform matrix")
    if set(matrix) != MATRIX_ROOT_KEYS or matrix.get("schema_version") != 1:
        raise PlatformSupportError("platform matrix root or schema_version is invalid")
    _date(matrix["snapshot_at"], "platform matrix snapshot_at")
    if not isinstance(matrix["semantics"], str) or len(matrix["semantics"].strip()) < 80:
        raise PlatformSupportError("platform matrix semantics must state its evidence boundary")

    source_path = _safe_repo_file(matrix["source_snapshot"], root, "source_snapshot")
    source_data = _load_json(source_path, "source snapshot")
    source_ids = _validate_sources(source_data)
    if source_data["retrieved_at"] != matrix["snapshot_at"]:
        raise PlatformSupportError("matrix and source snapshot dates must match")

    targets = matrix["targets"]
    if not isinstance(targets, list) or not targets:
        raise PlatformSupportError("targets must be a non-empty array")
    ids: set[str] = set()
    used_source_ids: set[str] = set()
    for index, target in enumerate(targets):
        label = f"targets[{index}]"
        if not isinstance(target, dict) or set(target) != TARGET_KEYS:
            raise PlatformSupportError(f"{label} must contain exactly {sorted(TARGET_KEYS)}")
        target_id = target["id"]
        category = target["category"]
        if (
            not isinstance(target_id, str)
            or ID_PATTERN.fullmatch(target_id) is None
            or target_id in ids
            or not isinstance(category, str)
            or category not in CATEGORIES
            or not target_id.startswith(PREFIXES[category])
        ):
            raise PlatformSupportError(f"{label} id/category is invalid or duplicated")
        ids.add(target_id)
        if not isinstance(target["official_status"], str) or target["official_status"] not in OFFICIAL_STATUSES:
            raise PlatformSupportError(f"{label}.official_status is invalid")
        if not isinstance(target["repository_status"], str) or target["repository_status"] not in REPOSITORY_STATUSES:
            raise PlatformSupportError(f"{label}.repository_status is invalid")
        checks = target["checks"]
        if not isinstance(checks, dict) or set(checks) != CHECK_KEYS:
            raise PlatformSupportError(f"{label}.checks must contain exactly {sorted(CHECK_KEYS)}")
        if any(not isinstance(value, str) or value not in CHECK_STATUSES for value in checks.values()):
            raise PlatformSupportError(f"{label}.checks contains an invalid status")
        references = _string_list(target["source_ids"], f"{label}.source_ids")
        unknown_sources = sorted(set(references) - source_ids)
        if unknown_sources:
            raise PlatformSupportError(f"{label}.source_ids contains unknown ids: {unknown_sources}")
        used_source_ids.update(references)
        artifacts = _string_list(target["artifacts"], f"{label}.artifacts")
        for artifact in artifacts:
            _safe_repo_file(artifact, root, f"{label}.artifacts")
        if not isinstance(target["boundary"], str) or len(target["boundary"].strip()) < 60:
            raise PlatformSupportError(f"{label}.boundary must constrain the claim")
        _validate_target_consistency(target, label)

    if ids != REQUIRED_TARGET_IDS:
        missing = sorted(REQUIRED_TARGET_IDS - ids)
        unexpected = sorted(ids - REQUIRED_TARGET_IDS)
        raise PlatformSupportError(f"platform inventory drift; missing={missing}, unexpected={unexpected}")
    if used_source_ids != source_ids:
        raise PlatformSupportError(f"unused official source ids: {sorted(source_ids - used_source_ids)}")
    return len(targets), len(source_ids)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--repository-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        target_count, source_count = validate(args.matrix.expanduser(), args.repository_root.expanduser())
    except (PlatformSupportError, OSError) as error:
        print(f"platform support invalid: {error}", file=sys.stderr)
        return 1
    print(f"platform support valid: {target_count} targets, {source_count} official source coordinates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
