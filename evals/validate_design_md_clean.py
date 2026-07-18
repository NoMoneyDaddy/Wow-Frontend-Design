#!/usr/bin/env python3
"""Require DESIGN.md to pass the pinned official linter without findings."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any


PACKAGE = "@google/design.md"
ROOT = Path(__file__).resolve().parents[1]
LOCKFILE = ROOT / "package-lock.json"
SYSTEM_PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"


class DesignMdInfrastructureError(ValueError):
    """Raised when the pinned local official linter cannot be trusted or run."""


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _safe_regular(path: Path, label: str, *, executable: bool = False) -> Path:
    try:
        info = path.lstat()
        canonical = path.resolve(strict=True)
        canonical_info = canonical.lstat()
    except OSError as error:
        raise DesignMdInfrastructureError(f"missing or unsafe {label}") from error
    if (
        path.is_symlink()
        or not stat.S_ISREG(info.st_mode)
        or not stat.S_ISREG(canonical_info.st_mode)
        or (executable and not os.access(canonical, os.X_OK))
    ):
        raise DesignMdInfrastructureError(f"missing or unsafe {label}")
    return canonical


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise DesignMdInfrastructureError(f"malformed {label}") from error
    if not isinstance(payload, dict):
        raise DesignMdInfrastructureError(f"malformed {label}")
    return payload


def locked_package_version(lockfile: Path = LOCKFILE) -> str:
    payload = _load_object(lockfile, "package-lock.json")
    package = payload.get("packages", {}).get("node_modules/@google/design.md", {})
    version = package.get("version")
    if not isinstance(version, str) or not version or any(character.isspace() for character in version):
        raise ValueError("package-lock.json has no exact @google/design.md version")
    return version


def _local_tool(repository_root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Path]]:
    lockfile = _safe_regular(repository_root / "package-lock.json", "package-lock.json")
    package_json = _safe_regular(
        repository_root / "node_modules" / "@google" / "design.md" / "package.json",
        "installed @google/design.md package.json",
    )
    entry = _safe_regular(
        repository_root / "node_modules" / "@google" / "design.md" / "dist" / "index.js",
        "installed @google/design.md CLI",
    )
    lock = _load_object(lockfile, "package-lock.json")
    locked = lock.get("packages", {}).get("node_modules/@google/design.md", {})
    if not isinstance(locked, dict):
        raise DesignMdInfrastructureError("package-lock.json has no pinned @google/design.md package")
    version = locked.get("version")
    integrity = locked.get("integrity")
    if (
        not isinstance(version, str)
        or not re.fullmatch(r"[0-9A-Za-z.+_-]{1,100}", version)
        or not isinstance(integrity, str)
        or not re.fullmatch(r"sha512-[A-Za-z0-9+/=]{20,200}", integrity)
    ):
        raise DesignMdInfrastructureError("package-lock.json has invalid @google/design.md provenance")
    installed = _load_object(package_json, "installed @google/design.md package.json")
    bins = installed.get("bin")
    if (
        installed.get("name") != PACKAGE
        or installed.get("version") != version
        or installed.get("main") != "./dist/index.js"
        or not isinstance(bins, dict)
        or bins.get("design.md") != "./dist/index.js"
        or bins.get("designmd") != "./dist/index.js"
    ):
        raise DesignMdInfrastructureError("installed @google/design.md disagrees with pinned metadata")
    node_raw = shutil.which("node", path=SYSTEM_PATH)
    if not node_raw:
        raise DesignMdInfrastructureError("canonical Node.js executable is unavailable")
    node = Path(node_raw).resolve(strict=True)
    if not node.is_file() or not os.access(node, os.X_OK):
        raise DesignMdInfrastructureError("canonical Node.js executable is unsafe")
    try:
        node_version_result = subprocess.run(
            [str(node), "--version"],
            env={"PATH": SYSTEM_PATH, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise DesignMdInfrastructureError("canonical Node.js version probe failed") from error
    node_version = node_version_result.stdout.strip()
    if node_version_result.returncode != 0 or re.fullmatch(r"v[0-9]+(?:\.[0-9]+){2}(?:[-+][0-9A-Za-z.-]+)?", node_version) is None:
        raise DesignMdInfrastructureError("canonical Node.js version probe failed")
    provenance = {
        "package": PACKAGE,
        "version": version,
        "lock_integrity": integrity,
        "lockfile_sha256": _digest(lockfile),
        "lockfile_mode": f"{stat.S_IMODE(lockfile.stat().st_mode):04o}",
        "package_json_sha256": _digest(package_json),
        "package_json_mode": f"{stat.S_IMODE(package_json.stat().st_mode):04o}",
        "cli_entry_sha256": _digest(entry),
        "cli_entry_bytes": entry.stat().st_size,
        "cli_entry_mode": f"{stat.S_IMODE(entry.stat().st_mode):04o}",
        "node_version": node_version,
        "node_sha256": _digest(node),
        "node_bytes": node.stat().st_size,
        "node_mode": f"{stat.S_IMODE(node.stat().st_mode):04o}",
    }
    return provenance, {"lockfile": lockfile, "package_json": package_json, "entry": entry, "node": node}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("design", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--local-only", action="store_true", help="require the pinned repo-local official CLI")
    parser.add_argument("--json", action="store_true", help="print the validation receipt as JSON")
    args = parser.parse_args()
    if not 5 <= args.timeout_seconds <= 300:
        parser.error("--timeout-seconds must be within 5..300")
    return args


def clean_summary(payload: Any) -> tuple[int, int, int]:
    if not isinstance(payload, dict) or not isinstance(payload.get("summary"), dict):
        raise ValueError("official linter returned no summary")
    summary = payload["summary"]
    values = tuple(summary.get(name) for name in ("errors", "warnings", "infos"))
    if any(type(value) is not int or value < 0 for value in values):
        raise ValueError("official linter returned a malformed summary")
    return values  # type: ignore[return-value]


def validate_local(
    design: Path,
    *,
    timeout_seconds: int = 180,
    repository_root: Path = ROOT,
) -> dict[str, Any]:
    if not 5 <= timeout_seconds <= 300:
        raise DesignMdInfrastructureError("timeout must be within 5..300 seconds")
    design = _safe_regular(design, "DESIGN.md")
    try:
        design_bytes = design.read_bytes()
        design_bytes.decode("utf-8")
    except (OSError, UnicodeError) as error:
        raise DesignMdInfrastructureError("DESIGN.md is not strict UTF-8") from error
    design_info = design.stat()
    if not 1 <= len(design_bytes) <= 1_048_576 or b"\x00" in design_bytes:
        raise DesignMdInfrastructureError("DESIGN.md is empty, oversized or contains NUL")
    before, paths = _local_tool(repository_root)
    try:
        completed = subprocess.run(
            [str(paths["node"]), str(paths["entry"]), "lint", str(design)],
            cwd=design.parent,
            env={
                "HOME": str(design.parent),
                "PATH": SYSTEM_PATH,
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
            },
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        payload = json.loads(completed.stdout)
        errors, warnings, infos = clean_summary(payload)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError) as error:
        raise DesignMdInfrastructureError(f"official local linter failed: {error}") from error
    if completed.returncode not in (0, 1):
        raise DesignMdInfrastructureError("official local linter returned an invalid exit code")
    findings = payload.get("findings")
    if not isinstance(findings, list) or any(not isinstance(finding, dict) for finding in findings):
        raise DesignMdInfrastructureError("official local linter returned malformed findings")
    try:
        encoded_findings = json.dumps(findings, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise DesignMdInfrastructureError("official local linter returned malformed findings") from error
    if len(encoded_findings) > 1_048_576:
        raise DesignMdInfrastructureError("official local linter findings exceeded the receipt quota")
    after, _ = _local_tool(repository_root)
    if before != after:
        raise DesignMdInfrastructureError("official local linter provenance drifted during validation")
    final_info = design.lstat()
    if (
        design.is_symlink()
        or not stat.S_ISREG(final_info.st_mode)
        or design.read_bytes() != design_bytes
        or stat.S_IMODE(final_info.st_mode) != stat.S_IMODE(design_info.st_mode)
    ):
        raise DesignMdInfrastructureError("DESIGN.md drifted during validation")
    summary = {"errors": errors, "warnings": warnings, "infos": infos}
    return {
        "status": "passed" if not errors and not warnings else "rejected",
        "required_result": "zero-errors-zero-warnings",
        "summary": summary,
        "findings": findings,
        "input": {
            "bytes": len(design_bytes),
            "mode": f"{stat.S_IMODE(design_info.st_mode):04o}",
            "sha256": hashlib.sha256(design_bytes).hexdigest(),
        },
        "tool": before,
    }


def _validate_legacy_npx(design: Path, timeout_seconds: int) -> dict[str, Any]:
    """Compatibility path for legacy callers; new controlled runners must use validate_local."""

    version = locked_package_version()
    try:
        completed = subprocess.run(
            ["npx", "--yes", f"{PACKAGE}@{version}", "lint", str(design)],
            cwd=design.parent,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        payload = json.loads(completed.stdout)
        errors, warnings, infos = clean_summary(payload)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError) as error:
        raise DesignMdInfrastructureError(f"legacy official linter failed: {error}") from error
    if completed.returncode not in (0, 1):
        raise DesignMdInfrastructureError("legacy official linter returned an invalid exit code")
    return {
        "status": "passed" if not errors and not warnings else "rejected",
        "required_result": "zero-errors-zero-warnings",
        "summary": {"errors": errors, "warnings": warnings, "infos": infos},
        "tool": {"package": PACKAGE, "version": version, "mode": "legacy-npx-fallback"},
    }


def main() -> int:
    args = parse_args()
    raw_design = args.design.expanduser()
    if raw_design.is_symlink():
        print(f"DESIGN.md clean gate infrastructure failure: unsafe file: {raw_design}", file=sys.stderr)
        return 2
    design = raw_design.resolve()
    if not design.is_file():
        print(f"DESIGN.md clean gate infrastructure failure: missing file: {design}", file=sys.stderr)
        return 2
    try:
        try:
            receipt = validate_local(design, timeout_seconds=args.timeout_seconds)
        except DesignMdInfrastructureError:
            if args.local_only:
                raise
            receipt = _validate_legacy_npx(design, args.timeout_seconds)
        errors, warnings, infos = (receipt["summary"][name] for name in ("errors", "warnings", "infos"))
    except (OSError, DesignMdInfrastructureError) as error:
        print(f"DESIGN.md clean gate infrastructure failure: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    if errors or warnings:
        print(
            f"DESIGN.md clean gate rejected findings: errors={errors}, warnings={warnings}, infos={infos}",
            file=sys.stderr,
        )
        return 1
    if not args.json:
        print(f"DESIGN.md clean gate passed: errors=0, warnings=0, infos={infos}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
