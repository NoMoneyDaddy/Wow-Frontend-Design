#!/usr/bin/env python3
"""Run or resume the fixed six-model, three-theme visual-design cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "evals" / "product-flow-v3-generation-results.json"
BRIEFS = {
    "mountain-rescue-flow-v3": ROOT / "evals" / "briefs" / "mountain-rescue-flow-v3.md",
    "city-poetry-festival-v3": ROOT / "evals" / "briefs" / "city-poetry-festival-v3.md",
    "bookstore-one-line-v3": ROOT / "evals" / "briefs" / "bookstore-one-line-v3.md",
}
SKILL = ROOT / "wow-frontend-design" / "SKILL.md"
TRUSTED_CONTEXT = (
    SKILL,
    ROOT / "wow-frontend-design" / "references" / "creative-direction.md",
    ROOT / "wow-frontend-design" / "references" / "anti-ai-slop.md",
    ROOT / "wow-frontend-design" / "references" / "mobile-responsive.md",
    ROOT / "wow-frontend-design" / "references" / "localization.md",
    ROOT / "wow-frontend-design" / "references" / "typography-webfonts.md",
    ROOT / "wow-frontend-design" / "references" / "implementation.md",
    ROOT / "wow-frontend-design" / "references" / "component-composition.md",
    ROOT / "wow-frontend-design" / "references" / "quality-gates.md",
    ROOT / "wow-frontend-design" / "references" / "weak-model-playbook.md",
    ROOT / "wow-frontend-design" / "references" / "color-system-psychology.md",
    ROOT / "wow-frontend-design" / "references" / "design-md-contract.md",
    ROOT / "wow-frontend-design" / "assets" / "DESIGN.template.md",
)
PROVIDERS = {
    "claude": ("haiku", "sonnet", "opus"),
    "codex": ("gpt-5.4-mini", "gpt-5.4", "gpt-5.5"),
}
OUTPUTS_BY_CASE = {
    "mountain-rescue-flow-v3": ("DESIGN.md", "index.html"),
    "city-poetry-festival-v3": ("DESIGN.md", "index.html"),
    "bookstore-one-line-v3": ("DESIGN.md", "index.html", "catalog.html", "book.html"),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("all", *PROVIDERS), default="all")
    parser.add_argument("--theme", choices=("all", *BRIEFS), default="all")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--resume", action="store_true", help="replace an existing ledger and reuse valid completed targets")
    args = parser.parse_args()
    if args.timeout_seconds < 30 or args.timeout_seconds > 3600:
        parser.error("--timeout-seconds must be within 30..3600")
    return args


def selected_cases(provider: str, theme: str) -> list[tuple[str, str, str]]:
    providers = PROVIDERS if provider == "all" else {provider: PROVIDERS[provider]}
    themes = tuple(BRIEFS) if theme == "all" else (theme,)
    return [
        (provider_name, model, case_id)
        for case_id in themes
        for provider_name, models in providers.items()
        for model in models
    ]


def target_for(provider: str, model: str, case_id: str) -> Path:
    prefix = "claude" if provider == "claude" else "codex"
    return ROOT / "evals" / f"{prefix}-{model}-{case_id}"


def outputs_for(case_id: str) -> tuple[str, ...]:
    return OUTPUTS_BY_CASE[case_id]


def verified_existing(target: Path, case_id: str) -> dict[str, object] | None:
    outputs = outputs_for(case_id)
    manifest_path = target / "run-manifest.json"
    present = [target / name for name in (*outputs, "run-manifest.json") if (target / name).exists()]
    if not present:
        return None
    if len(present) != len(outputs) + 1 or any(path.is_symlink() or not path.is_file() for path in present):
        raise ValueError(f"partial or unsafe pre-existing output: {display_path(target)}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    declared = {item["path"]: item["sha256"] for item in manifest.get("outputs", [])}
    if set(declared) != set(outputs):
        raise ValueError(f"invalid manifest output set: {display_path(manifest_path)}")
    for name in outputs:
        if digest(target / name) != declared[name]:
            raise ValueError(f"manifest digest mismatch: {display_path(target / name)}")
    return manifest


def command_for(provider: str, model: str, case_id: str) -> list[str]:
    runner = ROOT / "evals" / ("run_claude_case.sh" if provider == "claude" else "run_codex_case.sh")
    return [str(runner), model, "--case", case_id]


def terminate_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.communicate(timeout=5)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    process.communicate()


def run_isolated(command: list[str], timeout_seconds: float) -> subprocess.CompletedProcess[str]:
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except BaseException:
        terminate_process_group(process)
        raise
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def short_error(completed: subprocess.CompletedProcess[str] | None, timeout: Exception | None = None) -> str:
    if timeout is not None:
        return f"timed out: {timeout}"[:500]
    assert completed is not None
    combined = "\n".join(part.strip() for part in (completed.stderr, completed.stdout) if part.strip())
    return " ".join(combined.split())[:500] or "runner exited without diagnostic output"


def classify_failure(exit_code: int | None, summary: str) -> str:
    lowered = summary.casefold()
    if exit_code == 2:
        return "infrastructure_failure"
    if "model" in lowered and any(word in lowered for word in ("unavailable", "unsupported", "not found", "does not exist")):
        return "model_resolution_failure"
    if "policy rejected" in lowered or "forbidden by this isolated evaluation" in lowered:
        return "output_policy_rejected"
    return "generation_failed"


def write_ledger(path: Path, ledger: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(ledger, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(serialized)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def main() -> int:
    args = parse_args()
    output = args.output.expanduser().resolve()
    if output.exists() and not args.resume:
        raise SystemExit(f"refusing to overwrite existing ledger: {output}")
    if any(not brief.is_file() or brief.is_symlink() for brief in BRIEFS.values()) or any(
        not path.is_file() or path.is_symlink() for path in TRUSTED_CONTEXT
    ):
        raise SystemExit("fixed briefs or Skill are missing/unsafe")

    cases = selected_cases(args.provider, args.theme)
    expected_contract = {
        "briefs": {
            case_id: {"path": str(path.relative_to(ROOT)), "sha256": digest(path)}
            for case_id, path in BRIEFS.items()
        },
        "skill": {"path": str(SKILL.relative_to(ROOT)), "sha256": digest(SKILL)},
        "trusted_context": [
            {"path": str(path.relative_to(ROOT)), "sha256": digest(path)} for path in TRUSTED_CONTEXT
        ],
        "outputs_by_case": {case_id: list(outputs) for case_id, outputs in OUTPUTS_BY_CASE.items()},
        "providers_are_separate_cohorts": True,
        "resolved_backend_snapshots_may_be_unreported": True,
        "generation_settings": {
            "effort": "model_default",
            "claude_extended_thinking": False,
            "codex_reasoning_summary": "none",
            "codex_internal_reasoning_disable_supported": False,
        },
    }
    expected_selection = {"provider": args.provider, "theme": args.theme, "count": len(cases)}
    if output.exists():
        ledger = json.loads(output.read_text(encoding="utf-8"))
        if ledger.get("schema_version") != 1 or ledger.get("contract") != expected_contract:
            raise SystemExit("resume ledger contract does not match the current fixed brief/Skill")
        if ledger.get("selection") != expected_selection or not isinstance(ledger.get("results"), list):
            raise SystemExit("resume ledger selection is incompatible")
        ledger["status"] = "running"
        ledger["finished_at"] = None
        ledger.pop("summary", None)
    else:
        ledger = {
            "schema_version": 1,
            "status": "running",
            "started_at": utc_now(),
            "finished_at": None,
            "contract": expected_contract,
            "selection": expected_selection,
            "results": [],
        }
    prior_by_key: dict[tuple[str, str, str], dict[str, object]] = {}
    for item in ledger["results"]:  # type: ignore[index]
        if not isinstance(item, dict):
            raise SystemExit("resume ledger contains a malformed result")
        key = (str(item.get("provider")), str(item.get("model")), str(item.get("case_id")))
        if key in prior_by_key or key not in cases:
            raise SystemExit("resume ledger contains a duplicate or out-of-selection result")
        prior_by_key[key] = item
    write_ledger(output, ledger)

    for provider, model, case_id in cases:
        target = target_for(provider, model, case_id)
        relative_target = str(target.relative_to(ROOT))
        previous = prior_by_key.get((provider, model, case_id))
        if previous is not None:
            if previous.get("status") in {"completed", "existing_completed"}:
                verified_existing(target, case_id)
            print(f"preserving {provider} / {model} / {case_id}: {previous.get('status')}", flush=True)
            continue
        print(f"starting {provider} / {model} / {case_id}", flush=True)
        record: dict[str, object] = {
            "provider": provider,
            "model": model,
            "case_id": case_id,
            "target": relative_target,
            "started_at": utc_now(),
        }
        started = time.monotonic()
        try:
            manifest = verified_existing(target, case_id)
            if manifest is not None:
                record.update(status="existing_completed", exit_code=None, manifest=f"{relative_target}/run-manifest.json")
            else:
                completed = run_isolated(command_for(provider, model, case_id), args.timeout_seconds)
                if completed.returncode == 0:
                    verified_existing(target, case_id)
                    record.update(status="completed", exit_code=0, manifest=f"{relative_target}/run-manifest.json")
                else:
                    summary = short_error(completed)
                    record.update(status=classify_failure(completed.returncode, summary), exit_code=completed.returncode, error_summary=summary)
        except subprocess.TimeoutExpired as error:
            summary = short_error(None, error)
            record.update(status="timeout", exit_code=None, error_summary=summary)
        except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError) as error:
            record.update(status="infrastructure_failure", exit_code=None, error_summary=str(error)[:500])
        record["finished_at"] = utc_now()
        record["duration_seconds"] = round(time.monotonic() - started, 3)
        ledger["results"].append(record)  # type: ignore[union-attr]
        write_ledger(output, ledger)
        print(f"finished {provider} / {model} / {case_id}: {record['status']}", flush=True)

    statuses = [str(item["status"]) for item in ledger["results"]]  # type: ignore[index]
    completed_count = sum(status in {"completed", "existing_completed"} for status in statuses)
    ledger["status"] = "completed" if completed_count == len(statuses) else "partial" if completed_count else "failed"
    ledger["finished_at"] = utc_now()
    ledger["summary"] = {
        "requested": len(statuses),
        "completed": completed_count,
        "failed": len(statuses) - completed_count,
        "statuses": {status: statuses.count(status) for status in sorted(set(statuses))},
    }
    write_ledger(output, ledger)
    return 0 if completed_count == len(statuses) else 1


if __name__ == "__main__":
    raise SystemExit(main())
