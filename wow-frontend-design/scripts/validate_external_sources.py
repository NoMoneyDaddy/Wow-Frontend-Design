#!/usr/bin/env python3
"""Validate the checked-in external research source lock without network access."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


REVISION = re.compile(r"^[0-9a-f]{40}$")
LICENSES = {"MIT", "Apache-2.0", "Apache-2.0-subdirectory", "NOASSERTION"}
SOURCE_KEYS = {"repository", "revision", "license", "paths"}


class SourceLockError(ValueError):
    """Raised when the source lock cannot be trusted."""


def load(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise SourceLockError(f"refusing symlink lock: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SourceLockError(f"cannot read valid JSON lock: {error}") from error
    if not isinstance(value, dict):
        raise SourceLockError("lock root must be an object")
    return value


def validate(path: Path) -> int:
    data = load(path)
    if set(data) != {"schema_version", "retrieved_at", "policy", "sources"}:
        raise SourceLockError("lock root has missing or unexpected keys")
    if data["schema_version"] != 1:
        raise SourceLockError("schema_version must equal 1")
    if not isinstance(data["retrieved_at"], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data["retrieved_at"]):
        raise SourceLockError("retrieved_at must be YYYY-MM-DD")
    if not isinstance(data["policy"], str) or len(data["policy"].strip()) < 20:
        raise SourceLockError("policy must explain the research boundary")
    sources = data["sources"]
    if not isinstance(sources, list) or not sources:
        raise SourceLockError("sources must be a non-empty array")

    repositories: set[str] = set()
    for index, source in enumerate(sources):
        label = f"sources[{index}]"
        if not isinstance(source, dict) or set(source) != SOURCE_KEYS:
            raise SourceLockError(f"{label} must contain exactly {sorted(SOURCE_KEYS)}")
        repository = source["repository"]
        revision = source["revision"]
        license_id = source["license"]
        paths = source["paths"]
        if not isinstance(repository, str) or not re.fullmatch(r"[^/\s]+/[^/\s]+", repository):
            raise SourceLockError(f"{label}.repository must be owner/name")
        if repository.casefold() in repositories:
            raise SourceLockError(f"duplicate repository: {repository}")
        repositories.add(repository.casefold())
        if not isinstance(revision, str) or REVISION.fullmatch(revision) is None:
            raise SourceLockError(f"{label}.revision must be a full lowercase Git SHA-1")
        if license_id not in LICENSES:
            raise SourceLockError(f"{label}.license must be an allowed reviewed value")
        if not isinstance(paths, list) or not paths or len(paths) != len(set(paths)):
            raise SourceLockError(f"{label}.paths must be a unique non-empty array")
        for item in paths:
            if not isinstance(item, str) or not item:
                raise SourceLockError(f"{label}.paths contains a non-string or empty value")
            candidate = PurePosixPath(item)
            if candidate.is_absolute() or ".." in candidate.parts or "\x00" in item:
                raise SourceLockError(f"{label}.paths contains an unsafe path: {item!r}")
    return len(sources)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lock", type=Path)
    args = parser.parse_args()
    try:
        count = validate(args.lock.expanduser())
    except SourceLockError as error:
        print(f"source lock invalid: {error}", file=sys.stderr)
        return 1
    print(f"source lock valid: {count} repositories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
