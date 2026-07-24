#!/usr/bin/env python3
"""Prepare a current craft case from a completed run manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any

from validate_current_craft_acceptance import CORE_CRAFT, PROFILE_STANDARD


ROOT = Path(__file__).resolve().parents[1]
MAX_MANIFEST_BYTES = 2_000_000
MAX_OUTPUT_BYTES = 1_048_576
HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class CraftCaseError(ValueError):
    """Raised when a craft case cannot be prepared safely."""


def _required_flag(name: str) -> int:
    value = getattr(os, name, 0)
    if not isinstance(value, int) or value == 0:
        raise CraftCaseError(f"platform requires {name}")
    return value


def _identity(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _real_directory(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise CraftCaseError(f"{label} must be an absolute unaliased directory")
    try:
        info = path.lstat()
        canonical = path.resolve(strict=True)
    except OSError as error:
        raise CraftCaseError(f"{label} must be an absolute unaliased directory") from error
    if not stat.S_ISDIR(info.st_mode) or path.is_symlink() or canonical != path:
        raise CraftCaseError(f"{label} must be an absolute unaliased directory")
    return canonical


def _outside(path: Path, boundary: Path, label: str) -> None:
    if path == boundary or boundary in path.parents:
        raise CraftCaseError(f"{label} must remain outside the authoring repository")


def _read_manifest(path: Path) -> bytes:
    if not path.is_absolute():
        raise CraftCaseError("run manifest must be an absolute unaliased regular file")
    try:
        before = path.lstat()
        canonical = path.resolve(strict=True)
    except OSError as error:
        raise CraftCaseError("run manifest must be an absolute unaliased regular file") from error
    if (
        not stat.S_ISREG(before.st_mode)
        or path.is_symlink()
        or canonical != path
        or before.st_nlink != 1
        or not 1 <= before.st_size <= MAX_MANIFEST_BYTES
    ):
        raise CraftCaseError("run manifest must be a bounded unaliased regular file")

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | _required_flag("O_NOFOLLOW")
    descriptor = -1
    try:
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        if _identity(opened) != _identity(before) or not stat.S_ISREG(opened.st_mode):
            raise CraftCaseError("run manifest identity changed before it was read")
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise CraftCaseError("run manifest changed while it was read")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise CraftCaseError("run manifest changed while it was read")
        after = os.fstat(descriptor)
    except CraftCaseError:
        raise
    except OSError as error:
        raise CraftCaseError("run manifest could not be read safely") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)

    try:
        current = path.lstat()
    except OSError as error:
        raise CraftCaseError("run manifest changed while it was read") from error
    if _identity(before) != _identity(after) or _identity(before) != _identity(current):
        raise CraftCaseError("run manifest changed while it was read")
    return b"".join(chunks)


def _relative_path(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise CraftCaseError(f"{label} must be a normalized relative path")
    path = Path(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise CraftCaseError(f"{label} must be a normalized relative path")
    return value


def _manifest_payload(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise CraftCaseError("run manifest is not valid JSON") from error
    if not isinstance(value, dict):
        raise CraftCaseError("run manifest must be an object")
    if type(value.get("schema_version")) is not int or value["schema_version"] != 2:
        raise CraftCaseError("run manifest is not a completed current build")
    if value.get("status") != "completed":
        raise CraftCaseError("run manifest is not completed")

    brief = value.get("brief")
    if not isinstance(brief, dict) or set(brief) != {"bytes", "sha256"}:
        raise CraftCaseError("run manifest brief provenance is invalid")
    if (
        type(brief["bytes"]) is not int
        or brief["bytes"] < 1
        or not isinstance(brief["sha256"], str)
        or HASH_PATTERN.fullmatch(brief["sha256"]) is None
    ):
        raise CraftCaseError("run manifest brief provenance is invalid")

    outputs = value.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        raise CraftCaseError("run manifest must contain at least one HTML output")
    paths: set[str] = set()
    html_count = 0
    for index, raw_record in enumerate(outputs):
        if not isinstance(raw_record, dict) or set(raw_record) != {
            "path",
            "bytes",
            "mode",
            "sha256",
        }:
            raise CraftCaseError(f"run manifest outputs[{index}] is invalid")
        relative = _relative_path(raw_record["path"], f"run manifest outputs[{index}].path")
        if relative in paths:
            raise CraftCaseError("run manifest output paths must be unique")
        if (
            type(raw_record["bytes"]) is not int
            or raw_record["bytes"] < 1
            or not isinstance(raw_record["mode"], str)
            or re.fullmatch(r"0[0-7]{3}", raw_record["mode"]) is None
            or not isinstance(raw_record["sha256"], str)
            or HASH_PATTERN.fullmatch(raw_record["sha256"]) is None
        ):
            raise CraftCaseError(f"run manifest outputs[{index}] provenance is invalid")
        paths.add(relative)
        if relative.lower().endswith(".html"):
            html_count += 1
    if html_count < 1:
        raise CraftCaseError("run manifest must contain at least one HTML output")
    return value


def _validate_manifest_output(
    workspace: Path,
    record: dict[str, Any],
    index: int,
) -> None:
    label = f"run manifest outputs[{index}]"
    path = workspace / record["path"]
    try:
        before = path.lstat()
        canonical = path.resolve(strict=True)
    except OSError as error:
        raise CraftCaseError(f"{label} actual output is unavailable") from error
    if (
        canonical != path
        or path.is_symlink()
        or not stat.S_ISREG(before.st_mode)
        or before.st_nlink != 1
        or not 1 <= before.st_size <= MAX_OUTPUT_BYTES
        or before.st_size != record["bytes"]
        or f"{stat.S_IMODE(before.st_mode):04o}" != record["mode"]
    ):
        raise CraftCaseError(f"{label} actual output provenance is invalid")

    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | _required_flag("O_NOFOLLOW")
    )
    descriptor = -1
    try:
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        if _identity(opened) != _identity(before):
            raise CraftCaseError(f"{label} actual output identity changed")
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise CraftCaseError(f"{label} actual output changed")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise CraftCaseError(f"{label} actual output changed")
        after = os.fstat(descriptor)
    except CraftCaseError:
        raise
    except OSError as error:
        raise CraftCaseError(f"{label} actual output could not be read") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)

    try:
        current = path.lstat()
    except OSError as error:
        raise CraftCaseError(f"{label} actual output changed") from error
    raw = b"".join(chunks)
    if (
        _identity(before) != _identity(after)
        or _identity(before) != _identity(current)
        or hashlib.sha256(raw).hexdigest() != record["sha256"]
    ):
        raise CraftCaseError(f"{label} actual output provenance is invalid")


def _output_path(path: Path, workspace: Path) -> tuple[Path, Path]:
    if not path.is_absolute() or path.name in {"", ".", ".."}:
        raise CraftCaseError("output must be an absolute path")
    parent = _real_directory(path.parent, "output parent")
    output = parent / path.name
    if output != path:
        raise CraftCaseError("output must be an unaliased path")
    repository = ROOT.resolve(strict=True)
    if output == workspace or workspace in output.parents:
        raise CraftCaseError("output must remain outside the workspace")
    _outside(output, repository, "output")
    return output, parent


def _write_exclusive(path: Path, parent: Path, encoded: bytes) -> None:
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | _required_flag("O_DIRECTORY")
        | _required_flag("O_NOFOLLOW")
    )
    output_flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | _required_flag("O_NOFOLLOW")
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
            raise OSError("output parent identity changed")
        descriptor = os.open(
            path.name,
            output_flags,
            0o600,
            dir_fd=parent_descriptor,
        )
        created = True
        opened = os.fstat(descriptor)
        created_identity = (opened.st_dev, opened.st_ino)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise OSError("output is not a regular file")
        os.fchmod(descriptor, 0o600)
        written = 0
        while written < len(encoded):
            count = os.write(descriptor, encoded[written:])
            if count <= 0:
                raise OSError("short write")
            written += count
        os.fsync(descriptor)
        final = os.fstat(descriptor)
        current_parent = parent.lstat()
        current_output = os.stat(
            path.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        if (
            (current_parent.st_dev, current_parent.st_ino)
            != (pinned_parent.st_dev, pinned_parent.st_ino)
            or (current_output.st_dev, current_output.st_ino)
            != created_identity
            or current_output.st_nlink != 1
            or final.st_size != len(encoded)
            or stat.S_IMODE(final.st_mode) != 0o600
        ):
            raise OSError("output provenance is invalid")
    except OSError as error:
        if created and parent_descriptor >= 0 and created_identity is not None:
            try:
                current = os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
                if (current.st_dev, current.st_ino) == created_identity:
                    os.unlink(path.name, dir_fd=parent_descriptor)
            except OSError:
                pass
        raise CraftCaseError("craft case output could not be created exclusively") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if parent_descriptor >= 0:
            os.close(parent_descriptor)


def prepare_case(
    workspace_root: Path,
    output: Path,
    *,
    case_id: str = "current-production",
    partition: str = "validation",
    locale: str = "zh-Hant",
) -> dict[str, Any]:
    if not isinstance(case_id, str) or ID_PATTERN.fullmatch(case_id) is None:
        raise CraftCaseError("case_id is invalid")
    if partition not in {"validation", "test"}:
        raise CraftCaseError("partition must be validation or test")
    if locale not in {"zh-Hant", "en"}:
        raise CraftCaseError("locale must be zh-Hant or en")

    workspace = _real_directory(Path(workspace_root), "workspace root")
    repository = ROOT.resolve(strict=True)
    _outside(workspace, repository, "workspace root")
    manifest_path = workspace / "run-manifest.json"
    raw_manifest = _read_manifest(manifest_path)
    _outside(manifest_path.resolve(strict=True), repository, "run manifest")
    manifest = _manifest_payload(raw_manifest)
    for index, record in enumerate(manifest["outputs"]):
        _validate_manifest_output(workspace, record, index)
    output_path, parent = _output_path(Path(output), workspace)

    case = {
        "schema_version": 1,
        "case_id": case_id,
        "run_id": f"current-{hashlib.sha256(raw_manifest).hexdigest()}",
        "partition": partition,
        "brief": manifest["brief"],
        "capture_plan": {
            "locale": locale,
            "state": "default",
            "pages": "all_html_outputs",
            "wait_condition": "load+fonts+two-raf+300ms+two-raf",
            "profiles": PROFILE_STANDARD,
        },
        "craft": {
            "rubric_version": "wow-core-craft-v1",
            "required_dimensions": sorted(CORE_CRAFT),
            "feedback_policy": "aggregate-failure-families-only",
        },
    }
    encoded = (
        json.dumps(case, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    _write_exclusive(output_path, parent, encoded)
    return case


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare a current craft case from a completed run manifest."
    )
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--case-id", default="current-production")
    parser.add_argument(
        "--partition",
        choices=("validation", "test"),
        default="validation",
    )
    parser.add_argument("--locale", choices=("zh-Hant", "en"), default="zh-Hant")
    args = parser.parse_args(argv)
    try:
        prepare_case(
            args.workspace_root,
            args.output,
            case_id=args.case_id,
            partition=args.partition,
            locale=args.locale,
        )
    except CraftCaseError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
