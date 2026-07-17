#!/usr/bin/env python3
"""Validate the checked-in external research source lock without network access."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any


REVISION = re.compile(r"^[0-9a-f]{40}$")
LICENSES = {
    "MIT",
    "MIT AND CC-BY-SA-4.0",
    "Apache-2.0",
    "Apache-2.0-subdirectory",
    "NOASSERTION",
}
SOURCE_KEYS = {"repository", "revision", "license", "paths"}
MAX_LOCK_BYTES = 1_000_000
MAX_JSON_DEPTH = 128


class SourceLockError(ValueError):
    """Raised when the source lock cannot be trusted."""


def _validate_json_depth(raw: bytes) -> None:
    depth = 0
    in_string = False
    escaped = False
    for byte in raw:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
        elif byte == 0x22:
            in_string = True
        elif byte in {0x5B, 0x7B}:
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise SourceLockError(f"lock exceeds {MAX_JSON_DEPTH} levels of JSON nesting")
        elif byte in {0x5D, 0x7D} and depth:
            depth -= 1


def load(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise SourceLockError(f"refusing symlink lock: {path}")
    try:
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise SourceLockError(f"lock is not a regular file: {path}")
            if info.st_size > MAX_LOCK_BYTES:
                raise SourceLockError(f"lock exceeds {MAX_LOCK_BYTES} bytes")
            raw = stream.read(MAX_LOCK_BYTES + 1)
            if len(raw) > MAX_LOCK_BYTES:
                raise SourceLockError(f"lock exceeds {MAX_LOCK_BYTES} bytes")
        _validate_json_depth(raw)
        value = json.loads(raw.decode("utf-8"))
    except (OSError, RecursionError, UnicodeDecodeError, json.JSONDecodeError) as error:
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
