#!/usr/bin/env python3
"""Run the pinned official DESIGN.md linter over completed matrix outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "evals" / "product-flow-v4-generation-results.json"
DEFAULT_RETRY_LEDGER = ROOT / "evals" / "product-flow-v4-infrastructure-retry.json"
DEFAULT_OUTPUT = ROOT / "evals" / "product-flow-v4-design-md-results.json"


def locked_package_record() -> dict[str, str]:
    payload = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    package = payload.get("packages", {}).get("node_modules/@google/design.md", {})
    record = {field: package.get(field) for field in ("version", "resolved", "integrity")}
    if any(
        not isinstance(value, str) or not value or any(character.isspace() for character in value)
        for value in record.values()
    ):
        raise ValueError("package-lock.json has no exact integrity-bound @google/design.md record")
    return record  # type: ignore[return-value]


def safe_tool_root(path: Path) -> Path:
    absolute = Path(os.path.abspath(path.expanduser()))
    trusted_platform_links = {Path("/etc"), Path("/tmp"), Path("/var")} if sys.platform == "darwin" else set()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if current.is_symlink() and current not in trusted_platform_links:
            raise ValueError(f"DESIGN.md tool root crosses a symbolic link: {current}")
    return absolute


def locked_linter_command(tool_root: Path, timeout_seconds: int) -> tuple[list[str], dict[str, str]]:
    tool_root = safe_tool_root(tool_root)
    if tool_root.exists() and (tool_root.is_symlink() or not tool_root.is_dir()):
        raise ValueError(f"DESIGN.md tool root is unsafe: {tool_root}")
    tool_root.mkdir(parents=True, exist_ok=True)
    for name in ("package.json", "package-lock.json"):
        source = ROOT / name
        destination = tool_root / name
        if source.is_symlink() or not source.is_file() or destination.is_symlink():
            raise ValueError(f"locked install input is missing or unsafe: {source}")
        shutil.copyfile(source, destination)
        os.chmod(destination, 0o600)
    npm = shutil.which("npm")
    node = shutil.which("node")
    if npm is None or node is None:
        raise ValueError("npm and Node.js are required for the locked DESIGN.md linter")
    completed = subprocess.run(
        [
            npm,
            "ci",
            "--ignore-scripts",
            "--no-audit",
            "--no-fund",
        ],
        cwd=tool_root,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    if completed.returncode != 0:
        diagnostic = " ".join((completed.stderr or completed.stdout or "npm ci failed").split())[:500]
        raise ValueError(f"locked DESIGN.md linter install failed: {diagnostic}")
    package_record = locked_package_record()
    installed_package = tool_root / "node_modules" / "@google" / "design.md" / "package.json"
    entrypoint = tool_root / "node_modules" / "@google" / "design.md" / "dist" / "index.js"
    if (
        installed_package.is_symlink()
        or not installed_package.is_file()
        or entrypoint.is_symlink()
        or not entrypoint.is_file()
    ):
        raise ValueError("locked DESIGN.md linter install is missing or unsafe")
    installed = json.loads(installed_package.read_text(encoding="utf-8"))
    if installed.get("version") != package_record["version"]:
        raise ValueError("locked DESIGN.md linter version disagrees after install")
    return [node, str(entrypoint), "lint"], package_record


def locked_package_version() -> str:
    return locked_package_record()["version"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    supplemental = parser.add_mutually_exclusive_group()
    supplemental.add_argument("--supplemental-retry", type=Path, default=DEFAULT_RETRY_LEDGER)
    supplemental.add_argument(
        "--no-supplemental-retry",
        action="store_const",
        const=None,
        default=argparse.SUPPRESS,
        dest="supplemental_retry",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--tool-root", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true", help="atomically replace an existing report")
    parser.add_argument("--timeout-seconds", type=int, default=60)
    args = parser.parse_args()
    if not 5 <= args.timeout_seconds <= 300:
        parser.error("--timeout-seconds must be within 5..300")
    return args


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def safe_target(value: str, artifact_root: Path) -> Path:
    candidate = Path(value)
    unresolved = candidate if candidate.is_absolute() else ROOT / candidate
    try:
        relative = unresolved.relative_to(ROOT)
    except ValueError as error:
        raise ValueError(f"target escapes repository root: {value}") from error
    if ".." in relative.parts:
        raise ValueError(f"target path is unsafe: {value}")
    cursor = ROOT
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError(f"target contains a symlink component: {value}")
    target = unresolved.resolve()
    if target.parent != artifact_root:
        raise ValueError(f"target escapes artifact root: {value}")
    if target.is_symlink() or not target.is_dir():
        raise ValueError(f"target is missing or unsafe: {value}")
    return target


def artifact_root_from_contract(configured_root: object) -> Path:
    candidate = Path(configured_root) if isinstance(configured_root, str) else ROOT / "evals"
    unresolved = candidate if candidate.is_absolute() else ROOT / candidate
    try:
        relative = unresolved.relative_to(ROOT / "evals")
    except ValueError as error:
        raise ValueError("generation artifact root must stay inside repository evals") from error
    if ".." in relative.parts:
        raise ValueError("generation artifact root path is unsafe")
    cursor = ROOT / "evals"
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError("generation artifact root contains a symlink component")
    artifact_root = unresolved.resolve()
    try:
        artifact_root.relative_to((ROOT / "evals").resolve())
    except ValueError as error:
        raise ValueError("generation artifact root escapes repository evals") from error
    if not artifact_root.is_dir() or artifact_root.is_symlink():
        raise ValueError("generation artifact root is missing or unsafe")
    return artifact_root


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(serialized)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def main() -> int:
    args = parse_args()
    tool_root = args.tool_root
    try:
        command_prefix, package_record = locked_linter_command(tool_root, args.timeout_seconds)
    except (OSError, UnicodeError, json.JSONDecodeError, subprocess.TimeoutExpired, ValueError) as error:
        raise SystemExit(str(error)) from error
    package_version = package_record["version"]
    ledger_path = args.ledger.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if output.exists() and not args.overwrite:
        raise SystemExit(f"refusing to overwrite existing report: {output}")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    results = ledger.get("results")
    if not isinstance(results, list):
        raise SystemExit("generation ledger has no results list")

    contract = ledger.get("contract")
    configured_root = contract.get("artifact_root") if isinstance(contract, dict) else None
    try:
        artifact_root = artifact_root_from_contract(configured_root)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    supplemental_path = args.supplemental_retry.expanduser().resolve() if args.supplemental_retry else None
    supplemental: dict[str, object] | None = None
    if supplemental_path is not None and supplemental_path.is_file():
        supplemental_ledger = json.loads(supplemental_path.read_text(encoding="utf-8"))
        candidate = supplemental_ledger.get("retry")
        if isinstance(candidate, dict) and candidate.get("visual_evaluation_eligible") is True:
            supplemental = candidate

    report: dict[str, object] = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "generation_ledger": {"path": display_path(ledger_path), "sha256": digest(ledger_path)},
        "supplemental_retry_ledger": (
            {"path": display_path(supplemental_path), "sha256": digest(supplemental_path)}
            if supplemental is not None and supplemental_path is not None
            else None
        ),
        "linter": {"package": "@google/design.md", "version": package_version},
        "results": [],
    }
    clean = 0
    dirty = 0
    infrastructure_failures = 0
    candidates = [(item, "formal_matrix") for item in results]
    if supplemental is not None:
        candidates.append((supplemental, "infrastructure_retry"))
    for item, evidence_source in candidates:
        if not isinstance(item, dict) or item.get("status") not in {"completed", "existing_completed"}:
            continue
        target = safe_target(str(item.get("target", "")), artifact_root)
        design = target / "DESIGN.md"
        record: dict[str, object] = {
            "provider": item.get("provider"),
            "model": item.get("model"),
            "case_id": item.get("case_id"),
            "path": display_path(design),
            "evidence_source": evidence_source,
        }
        if design.is_symlink() or not design.is_file():
            record.update(status="infrastructure_failure", error="DESIGN.md missing or unsafe")
            infrastructure_failures += 1
            report["results"].append(record)  # type: ignore[union-attr]
            continue
        record["sha256"] = digest(design)
        try:
            completed = subprocess.run(
                [*command_prefix, str(design)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=args.timeout_seconds,
                check=False,
            )
            if completed.returncode != 0:
                raise ValueError(f"official linter exited with {completed.returncode}: {completed.stderr[:300]}")
            parsed = json.loads(completed.stdout)
            if not isinstance(parsed, dict) or not isinstance(parsed.get("summary"), dict):
                raise ValueError("official linter returned no summary")
            summary = parsed["summary"]
            values = tuple(summary.get(field) for field in ("errors", "warnings", "infos"))
            if any(type(value) is not int or value < 0 for value in values):
                raise ValueError("official linter returned a malformed summary")
            if not isinstance(parsed.get("findings"), list):
                raise ValueError("official linter returned no findings list")
            errors, warnings, infos = values
            status = "clean" if errors == 0 and warnings == 0 else "findings"
            record.update(
                status=status,
                exit_code=completed.returncode,
                summary={"errors": errors, "warnings": warnings, "infos": infos},
                findings=parsed.get("findings", []),
            )
            if status == "clean":
                clean += 1
            else:
                dirty += 1
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError, TypeError, ValueError) as error:
            record.update(status="infrastructure_failure", error=str(error)[:500])
            infrastructure_failures += 1
        report["results"].append(record)  # type: ignore[union-attr]

    report["summary"] = {
        "checked": clean + dirty + infrastructure_failures,
        "clean": clean,
        "with_findings": dirty,
        "infrastructure_failures": infrastructure_failures,
    }
    write_report(output, report)
    return 1 if infrastructure_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
