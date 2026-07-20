#!/usr/bin/env python3
"""Descriptor-anchored, bounded reads inside an authorized project tree."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Callable, Iterable


DESCRIPTOR_ANCHORING_AVAILABLE = (
    os.name == "posix"
    and os.open in os.supports_dir_fd
    and hasattr(os, "O_DIRECTORY")
    and hasattr(os, "O_NOFOLLOW")
)
DEFAULT_MAX_READ_BYTES = 512_000
DEFAULT_MAX_DIRECTORIES = 20_000
DEFAULT_MAX_DIRECTORY_ENTRIES = 10_000


class ProjectIoError(ValueError):
    """Base error for unavailable or unsafe project I/O."""


class ProjectIoUnavailableError(ProjectIoError):
    """Raised when the platform cannot provide descriptor-anchored traversal."""


class ProjectRootError(ProjectIoError):
    """Raised when a requested project root crosses its authorized boundary."""


class UnsafeProjectFileError(ProjectIoError):
    """Raised when a project entry cannot be opened as a bounded regular file."""


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(Path(path).expanduser()))


def _validated_parts(path: Path) -> tuple[str, ...]:
    parts = tuple(part for part in path.parts if part not in {path.anchor, os.sep})
    for part in parts:
        if part in {"", ".", ".."} or os.sep in part or "\x00" in part:
            raise ProjectRootError(f"unsafe project path component: {part!r}")
    return parts


def _directory_flags() -> int:
    return (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )


def _file_flags() -> int:
    return (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_BINARY", 0)
    )


def _open_child_directory(parent_fd: int, name: str) -> int:
    descriptor = os.open(name, _directory_flags(), dir_fd=parent_fd)
    try:
        info = os.fstat(descriptor)
    except BaseException:
        os.close(descriptor)
        raise
    if not stat.S_ISDIR(info.st_mode):
        os.close(descriptor)
        raise ProjectRootError(f"project path component is not a directory: {name}")
    return descriptor


def _open_absolute_directory(path: Path) -> int:
    descriptor = os.open(path.anchor or os.sep, _directory_flags())
    try:
        for part in _validated_parts(path):
            child = _open_child_directory(descriptor, part)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


class ProjectTree:
    """An opened project root whose later traversal never re-resolves parent paths."""

    protection = "descriptor_anchored"

    def __init__(self, root: Path, root_fd: int) -> None:
        self.root = root
        self._root_fd = root_fd
        self.skipped_unsafe_entries = 0

    def __enter__(self) -> "ProjectTree":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._root_fd >= 0:
            os.close(self._root_fd)
            self._root_fd = -1

    def _require_open(self) -> None:
        if self._root_fd < 0:
            raise ProjectIoError("project tree is closed")

    def _relative_parts(self, path: Path) -> tuple[str, ...]:
        candidate = Path(path)
        if candidate.is_absolute():
            try:
                candidate = candidate.relative_to(self.root)
            except ValueError as error:
                raise UnsafeProjectFileError(f"project file escapes opened root: {path}") from error
        try:
            parts = _validated_parts(candidate)
        except ProjectRootError as error:
            raise UnsafeProjectFileError(str(error)) from error
        if not parts:
            raise UnsafeProjectFileError("project file path is empty")
        return parts

    def _open_directory(self, parts: Iterable[str]) -> int:
        self._require_open()
        descriptor = os.dup(self._root_fd)
        try:
            for part in parts:
                child = _open_child_directory(descriptor, part)
                os.close(descriptor)
                descriptor = child
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise

    def collect_files(
        self,
        max_files: int,
        *,
        max_directories: int = DEFAULT_MAX_DIRECTORIES,
        max_directory_entries: int = DEFAULT_MAX_DIRECTORY_ENTRIES,
        ignored_directories: set[str] | frozenset[str] = frozenset(),
        is_sensitive: Callable[[Path], bool] = lambda _: False,
    ) -> tuple[list[Path], bool]:
        files: list[Path] = []
        visited_directories = 0
        pending: list[tuple[str, ...]] = [()]

        while pending:
            relative_directory = pending.pop()
            visited_directories += 1
            if visited_directories > max_directories:
                return files, True
            directories: list[tuple[str, ...]] = []
            regular_files: list[Path] = []
            try:
                descriptor = self._open_directory(relative_directory)
                try:
                    with os.scandir(descriptor) as entries:
                        for entry_index, entry in enumerate(entries, start=1):
                            if entry_index > max_directory_entries:
                                return files, True
                            relative = Path(*relative_directory, entry.name)
                            if entry.is_symlink():
                                self.skipped_unsafe_entries += 1
                                continue
                            if entry.is_dir(follow_symlinks=False):
                                rel = relative.as_posix()
                                if entry.name in ignored_directories or rel in ignored_directories:
                                    continue
                                if entry.name.startswith(".") and entry.name not in {".github", ".storybook"}:
                                    continue
                                directories.append((*relative_directory, entry.name))
                            elif entry.is_file(follow_symlinks=False):
                                if not is_sensitive(relative):
                                    regular_files.append(self.root / relative)
                            else:
                                self.skipped_unsafe_entries += 1
                finally:
                    os.close(descriptor)
            except OSError:
                self.skipped_unsafe_entries += 1
                continue
            remaining_directory_budget = max_directories - visited_directories - len(pending)
            if len(directories) > remaining_directory_budget:
                return files, True
            pending.extend(sorted(directories, reverse=True))
            for path in sorted(regular_files):
                files.append(path)
                if len(files) >= max_files:
                    return files, True
        return files, False

    def read_bytes(self, path: Path, max_bytes: int = DEFAULT_MAX_READ_BYTES) -> bytes:
        parts = self._relative_parts(path)
        try:
            parent_fd = self._open_directory(parts[:-1])
            try:
                descriptor = os.open(parts[-1], _file_flags(), dir_fd=parent_fd)
            finally:
                os.close(parent_fd)
        except OSError as error:
            self.skipped_unsafe_entries += 1
            raise UnsafeProjectFileError(f"unsafe project file: {path}") from error
        with os.fdopen(descriptor, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise UnsafeProjectFileError(f"{path} is not a regular file")
            if info.st_size > max_bytes:
                raise UnsafeProjectFileError(f"{path} exceeds {max_bytes} bytes")
            raw = stream.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise UnsafeProjectFileError(f"{path} exceeds {max_bytes} bytes")
            return raw

    def read_text(self, path: Path, max_bytes: int = DEFAULT_MAX_READ_BYTES) -> str:
        return self.read_bytes(path, max_bytes).decode("utf-8", errors="ignore")


def open_project_tree(requested: Path, authorized: Path) -> ProjectTree:
    """Open requested below authorized without following any path component symlink."""
    if not DESCRIPTOR_ANCHORING_AVAILABLE:
        raise ProjectIoUnavailableError(
            "descriptor-anchored project I/O requires Unix dir_fd, O_DIRECTORY, and O_NOFOLLOW"
        )
    requested_absolute = _absolute(requested)
    authorized_absolute = _absolute(authorized)
    if authorized_absolute.is_symlink():
        raise ProjectRootError(f"authorized root must not be a symlink: {authorized_absolute}")
    try:
        relative_requested = requested_absolute.relative_to(authorized_absolute)
    except ValueError as error:
        raise ProjectRootError(
            f"project root escapes authorized root: {requested_absolute}"
        ) from error

    try:
        authorized_canonical = authorized_absolute.resolve(strict=True)
        descriptor = _open_absolute_directory(authorized_canonical)
        for part in _validated_parts(relative_requested):
            child = _open_child_directory(descriptor, part)
            os.close(descriptor)
            descriptor = child
    except OSError as error:
        try:
            os.close(descriptor)
        except (OSError, UnboundLocalError):
            pass
        raise ProjectRootError(
            f"project root is unavailable or contains a symlink component: {requested_absolute}"
        ) from error
    return ProjectTree(authorized_canonical / relative_requested, descriptor)
