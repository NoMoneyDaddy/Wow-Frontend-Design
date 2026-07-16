#!/usr/bin/env python3
"""Monitor one isolated Codex process with bounded staging and log usage."""

from __future__ import annotations

import argparse
import os
import signal
import stat
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


MAX_ENTRIES = 32


class ResourceMonitorError(RuntimeError):
    """Raised when resource usage cannot be measured safely."""


def stage_usage_bytes(root: Path, limit: int) -> int:
    if limit < 1:
        raise ResourceMonitorError("stage limit must be positive")
    if root.is_symlink() or not root.is_dir():
        raise ResourceMonitorError("stage must be a real directory")
    logical = 0
    allocated = 0
    entries = 0
    pending = [root]
    while pending:
        current = pending.pop()
        try:
            iterator = os.scandir(current)
        except OSError as error:
            raise ResourceMonitorError(f"cannot scan stage: {error}") from error
        with iterator:
            for item in iterator:
                entries += 1
                if entries > MAX_ENTRIES:
                    raise ResourceMonitorError("stage entry quota exceeded")
                try:
                    info = item.stat(follow_symlinks=False)
                except OSError as error:
                    raise ResourceMonitorError(f"cannot stat stage entry: {error}") from error
                if stat.S_ISDIR(info.st_mode):
                    pending.append(Path(item.path))
                elif stat.S_ISREG(info.st_mode):
                    logical += info.st_size
                    allocated += getattr(info, "st_blocks", 0) * 512
                    usage = max(logical, allocated)
                    if usage > limit:
                        return usage
                else:
                    raise ResourceMonitorError("stage contains a non-regular entry")
    return max(logical, allocated)


def regular_file_size(path: Path) -> int:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return 0
    except OSError as error:
        raise ResourceMonitorError(f"cannot stat log: {error}") from error
    if not stat.S_ISREG(info.st_mode):
        raise ResourceMonitorError("log must be a regular non-symlink file")
    return info.st_size


def process_group_alive(pid: int) -> bool:
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # POSIX kill(..., 0) uses EPERM to signal that the group exists but is
        # not currently signalable. Treat it as alive so monitoring fails closed.
        return True
    return True


def terminate_process_group(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except OSError:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    for _ in range(10):
        if not process_group_alive(pid):
            return
        time.sleep(0.1)
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except OSError:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            return


def write_marker(path: Path, message: str) -> None:
    if path.is_symlink() or not path.parent.is_dir() or path.parent.is_symlink():
        raise ResourceMonitorError("quota marker path is unsafe")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(message)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as error:
        raise ResourceMonitorError(f"cannot write quota marker: {error}") from error


def monitor(
    pid: int,
    stage: Path,
    log: Path,
    marker: Path,
    stage_limit: int,
    log_limit: int,
    interval: float,
) -> int:
    if pid < 1 or stage_limit < 1 or log_limit < 1 or not 0.1 <= interval <= 10:
        raise ResourceMonitorError("invalid monitor bounds")
    last_size = -1
    while process_group_alive(pid):
        stage_size = stage_usage_bytes(stage, stage_limit)
        log_size = regular_file_size(log)
        if stage_size > stage_limit or log_size > log_limit:
            message = (
                f"quota exceeded: stage={stage_size}/{stage_limit} "
                f"log={log_size}/{log_limit}\n"
            )
            print(message, file=sys.stderr, end="", flush=True)
            terminate_process_group(pid)
            write_marker(marker, message)
            return 0
        if log_size > last_size:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            print(f"codex-progress bytes={log_size} at={timestamp}", flush=True)
            last_size = log_size
        time.sleep(interval)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    measure_parser = subparsers.add_parser("measure")
    measure_parser.add_argument("--stage", required=True, type=Path)
    measure_parser.add_argument("--stage-limit", required=True, type=int)
    monitor_parser = subparsers.add_parser("monitor")
    monitor_parser.add_argument("--pid", required=True, type=int)
    monitor_parser.add_argument("--stage", required=True, type=Path)
    monitor_parser.add_argument("--log", required=True, type=Path)
    monitor_parser.add_argument("--marker", required=True, type=Path)
    monitor_parser.add_argument("--stage-limit", required=True, type=int)
    monitor_parser.add_argument("--log-limit", required=True, type=int)
    monitor_parser.add_argument("--interval", type=float, default=0.5)
    args = parser.parse_args()
    try:
        if args.command == "measure":
            print(stage_usage_bytes(args.stage.expanduser(), args.stage_limit))
            return 0
        return monitor(
            args.pid,
            args.stage.expanduser(),
            args.log.expanduser(),
            args.marker.expanduser(),
            args.stage_limit,
            args.log_limit,
            args.interval,
        )
    except ResourceMonitorError as error:
        if args.command == "monitor":
            try:
                terminate_process_group(args.pid)
            except ResourceMonitorError:
                pass
        print(f"Codex resource monitor failed closed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
