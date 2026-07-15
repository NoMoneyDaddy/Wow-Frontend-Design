#!/usr/bin/env python3
"""Run the pinned official DESIGN.md linter over completed matrix outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "evals" / "product-flow-v4-generation-results.json"
DEFAULT_RETRY_LEDGER = ROOT / "evals" / "product-flow-v4-infrastructure-retry.json"
DEFAULT_OUTPUT = ROOT / "evals" / "product-flow-v4-design-md-results.json"
PACKAGE_VERSION = "0.2.0"


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
    target = (candidate if candidate.is_absolute() else ROOT / candidate).resolve()
    if target.parent != artifact_root:
        raise ValueError(f"target escapes artifact root: {value}")
    if target.is_symlink() or not target.is_dir():
        raise ValueError(f"target is missing or unsafe: {value}")
    return target


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
    ledger_path = args.ledger.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing report: {output}")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    results = ledger.get("results")
    if not isinstance(results, list):
        raise SystemExit("generation ledger has no results list")

    contract = ledger.get("contract")
    configured_root = contract.get("artifact_root") if isinstance(contract, dict) else None
    artifact_root = Path(configured_root).resolve() if isinstance(configured_root, str) else (ROOT / "evals").resolve()
    if not artifact_root.is_dir() or artifact_root.is_symlink():
        raise SystemExit("generation artifact root is missing or unsafe")

    supplemental_path = args.supplemental_retry.expanduser().resolve() if args.supplemental_retry else None
    supplemental: dict[str, object] | None = None
    if supplemental_path is not None and supplemental_path.is_file():
        supplemental_ledger = json.loads(supplemental_path.read_text(encoding="utf-8"))
        candidate = supplemental_ledger.get("retry")
        if isinstance(candidate, dict) and candidate.get("visual_evaluation_eligible") is True:
            supplemental = candidate

    command_prefix = ["npx", "--yes", f"@google/design.md@{PACKAGE_VERSION}", "lint"]
    report: dict[str, object] = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "generation_ledger": {"path": display_path(ledger_path), "sha256": digest(ledger_path)},
        "supplemental_retry_ledger": (
            {"path": display_path(supplemental_path), "sha256": digest(supplemental_path)}
            if supplemental is not None and supplemental_path is not None
            else None
        ),
        "linter": {"package": "@google/design.md", "version": PACKAGE_VERSION},
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
            parsed = json.loads(completed.stdout)
            summary = parsed.get("summary", {})
            errors = int(summary.get("errors", 0))
            warnings = int(summary.get("warnings", 0))
            infos = int(summary.get("infos", 0))
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
