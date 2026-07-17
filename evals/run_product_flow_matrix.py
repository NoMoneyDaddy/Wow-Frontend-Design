#!/usr/bin/env python3
"""Run or resume the fixed eight-theme v6 design cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import selectors
import signal
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "evals" / "product-flow-v6-generation-results.json"
BRIEFS = {
    "wind-maintenance-dispatch-v6": ROOT / "evals" / "briefs" / "wind-maintenance-dispatch-v6.md",
    "type-foundry-specimen-v6": ROOT / "evals" / "briefs" / "type-foundry-specimen-v6.md",
    "repair-cafe-intake-v6": ROOT / "evals" / "briefs" / "repair-cafe-intake-v6.md",
    "night-market-allergen-v6": ROOT / "evals" / "briefs" / "night-market-allergen-v6.md",
    "royalty-statement-v6": ROOT / "evals" / "briefs" / "royalty-statement-v6.md",
    "packaging-configurator-v6": ROOT / "evals" / "briefs" / "packaging-configurator-v6.md",
    "oral-history-archive-v6": ROOT / "evals" / "briefs" / "oral-history-archive-v6.md",
    "grant-review-board-v6": ROOT / "evals" / "briefs" / "grant-review-board-v6.md",
}
SKILL = ROOT / "wow-frontend-design" / "SKILL.md"
TRUSTED_CONTEXT = (
    SKILL,
    ROOT / "wow-frontend-design" / "references" / "creative-direction.md",
    ROOT / "wow-frontend-design" / "references" / "anti-ai-slop.md",
    ROOT / "wow-frontend-design" / "references" / "mobile-responsive.md",
    ROOT / "wow-frontend-design" / "references" / "localization.md",
    ROOT / "wow-frontend-design" / "references" / "typography-webfonts.md",
    ROOT / "wow-frontend-design" / "references" / "typographic-layout.md",
    ROOT / "wow-frontend-design" / "references" / "implementation.md",
    ROOT / "wow-frontend-design" / "references" / "component-composition.md",
    ROOT / "wow-frontend-design" / "references" / "quality-gates.md",
    ROOT / "wow-frontend-design" / "references" / "weak-model-playbook.md",
    ROOT / "wow-frontend-design" / "references" / "color-system-psychology.md",
    ROOT / "wow-frontend-design" / "references" / "design-md-contract.md",
    ROOT / "wow-frontend-design" / "assets" / "DESIGN.template.md",
)
EVALUATOR_INPUTS = (
    ROOT / "evals" / "run_product_flow_evaluation.py",
    ROOT / "evals" / "run_product_flow_matrix.py",
    ROOT / "evals" / "lint_design_md_matrix.py",
    ROOT / "evals" / "playwright_visual_v6_audit.cjs",
    ROOT / "evals" / "run_claude_case.sh",
    ROOT / "evals" / "run_codex_case.sh",
    ROOT / "evals" / "monitor_codex_progress.py",
    ROOT / "evals" / "validate_visual_web_output.py",
    ROOT / "evals" / "validate_design_md_clean.py",
    ROOT / "evals" / "validate_codex_log_policy.py",
)
PROVIDERS = {"codex": ("gpt-5.4-mini",)}
MODELS = tuple(model for models in PROVIDERS.values() for model in models)
OUTPUTS_BY_CASE = {
    "wind-maintenance-dispatch-v6": ("DESIGN.md", "index.html"),
    "type-foundry-specimen-v6": ("DESIGN.md", "index.html"),
    "repair-cafe-intake-v6": ("DESIGN.md", "index.html"),
    "night-market-allergen-v6": ("DESIGN.md", "index.html"),
    "royalty-statement-v6": ("DESIGN.md", "index.html"),
    "packaging-configurator-v6": ("DESIGN.md", "index.html", "materials.html", "summary.html"),
    "oral-history-archive-v6": ("DESIGN.md", "index.html", "archive.html", "story.html"),
    "grant-review-board-v6": ("DESIGN.md", "index.html"),
}
DEFAULT_MAX_OUTPUT_BYTES = 16 * 1024 * 1024


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
    parser.add_argument("--model", choices=("all", *MODELS), default="all")
    parser.add_argument("--theme", choices=("all", *BRIEFS), default="all")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--target-root", type=Path, default=ROOT / "evals")
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=1800,
        help="inactivity timeout; advancing runner output resets this timer",
    )
    parser.add_argument("--hard-timeout-seconds", type=int, default=7200)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--retry-delay-seconds", type=float, default=5.0)
    parser.add_argument("--resume", action="store_true", help="replace an existing ledger and reuse valid completed targets")
    args = parser.parse_args()
    if args.timeout_seconds < 30 or args.timeout_seconds > 3600:
        parser.error("--timeout-seconds must be within 30..3600")
    if args.hard_timeout_seconds < args.timeout_seconds or args.hard_timeout_seconds > 14400:
        parser.error("--hard-timeout-seconds must be within timeout-seconds..14400")
    if args.max_attempts < 1 or args.max_attempts > 10:
        parser.error("--max-attempts must be within 1..10")
    if args.retry_delay_seconds < 0 or args.retry_delay_seconds > 300:
        parser.error("--retry-delay-seconds must be within 0..300")
    if args.provider != "all" and args.model != "all" and args.model not in PROVIDERS[args.provider]:
        parser.error(f"--model {args.model} does not belong to provider {args.provider}")
    return args


def selected_cases(provider: str, theme: str, model: str = "all") -> list[tuple[str, str, str]]:
    providers = PROVIDERS if provider == "all" else {provider: PROVIDERS[provider]}
    themes = tuple(BRIEFS) if theme == "all" else (theme,)
    return [
        (provider_name, model_name, case_id)
        for case_id in themes
        for provider_name, models in providers.items()
        for model_name in models
        if model == "all" or model_name == model
    ]


def target_for(provider: str, model: str, case_id: str, target_root: Path = ROOT / "evals") -> Path:
    prefix = "claude" if provider == "claude" else "codex"
    return target_root / f"{prefix}-{model}-{case_id}"


def outputs_for(case_id: str) -> tuple[str, ...]:
    return OUTPUTS_BY_CASE[case_id]


def _manifest_receipt(target: Path, manifest: dict[str, object]) -> dict[str, object]:
    outputs = manifest.get("outputs")
    assert isinstance(outputs, list)
    return {
        "manifest_sha256": digest(target / "run-manifest.json"),
        "outputs": {str(item["path"]): str(item["sha256"]) for item in outputs if isinstance(item, dict)},
    }


def verified_existing(
    target: Path,
    provider: str,
    model: str,
    case_id: str,
    *,
    expected_receipt: dict[str, object] | None = None,
    verify_current_tools: bool = True,
) -> dict[str, object] | None:
    outputs = outputs_for(case_id)
    if target.is_symlink() or (target.exists() and not target.is_dir()):
        raise ValueError(f"unsafe pre-existing target: {display_path(target)}")
    manifest_path = target / "run-manifest.json"
    present = [target / name for name in (*outputs, "run-manifest.json") if (target / name).exists()]
    if not present:
        return None
    if len(present) != len(outputs) + 1 or any(path.is_symlink() or not path.is_file() for path in present):
        raise ValueError(f"partial or unsafe pre-existing output: {display_path(target)}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or manifest.get("status") != "completed":
        raise ValueError(f"invalid manifest schema/status: {display_path(manifest_path)}")
    case_record = manifest.get("case")
    if not isinstance(case_record, dict) or case_record.get("id") != case_id:
        raise ValueError(f"manifest case provenance mismatch: {display_path(manifest_path)}")
    claimed_target = case_record.get("target")
    if not isinstance(claimed_target, str) or not claimed_target:
        raise ValueError(f"manifest target provenance is missing: {display_path(manifest_path)}")
    claimed_path = Path(claimed_target)
    claimed_path = (claimed_path if claimed_path.is_absolute() else ROOT / claimed_path).resolve()
    if claimed_path != target.resolve():
        raise ValueError(f"manifest target provenance mismatch: {display_path(manifest_path)}")
    model_record = manifest.get("model")
    model_field = "requested_alias" if provider == "claude" else "requested_identifier"
    if not isinstance(model_record, dict) or model_record.get(model_field) != model:
        raise ValueError(f"manifest model provenance mismatch: {display_path(manifest_path)}")
    if provider == "codex" and manifest.get("provider") != "openai-first-party-chatgpt-oauth":
        raise ValueError(f"manifest provider provenance mismatch: {display_path(manifest_path)}")
    if verify_current_tools:
        runner = ROOT / "evals" / ("run_claude_case.sh" if provider == "claude" else "run_codex_case.sh")
        validator = ROOT / "evals" / "validate_visual_web_output.py"
        for label, record, expected in (
            ("runner", manifest.get("runner"), runner),
            ("output validator", manifest.get("output_validator"), validator),
        ):
            if (
                not isinstance(record, dict)
                or record.get("path") != display_path(expected)
                or record.get("sha256") != digest(expected)
            ):
                raise ValueError(f"manifest {label} provenance mismatch: {display_path(manifest_path)}")
    manifest_outputs = manifest.get("outputs")
    if (
        not isinstance(manifest_outputs, list)
        or len(manifest_outputs) != len(outputs)
        or any(not isinstance(item, dict) for item in manifest_outputs)
    ):
        raise ValueError(f"invalid manifest outputs: {display_path(manifest_path)}")
    declared = {item.get("path"): item.get("sha256") for item in manifest_outputs}
    if set(declared) != set(outputs):
        raise ValueError(f"invalid manifest output set: {display_path(manifest_path)}")
    for name in outputs:
        artifact = target / name
        record = next(item for item in manifest_outputs if item.get("path") == name)
        if digest(artifact) != declared[name] or record.get("bytes") != artifact.stat().st_size:
            raise ValueError(f"manifest digest mismatch: {display_path(target / name)}")
    receipt = _manifest_receipt(target, manifest)
    if expected_receipt is not None and receipt != expected_receipt:
        raise ValueError(f"matrix receipt mismatch: {display_path(manifest_path)}")
    return manifest


def command_for(provider: str, model: str, case_id: str) -> list[str]:
    runner = ROOT / "evals" / ("run_claude_case.sh" if provider == "claude" else "run_codex_case.sh")
    return [str(runner), model, "--case", case_id]


def terminate_process_group(process: subprocess.Popen[str]) -> None:
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


class ProgressTimeoutExpired(subprocess.TimeoutExpired):
    def __init__(
        self,
        command: list[str],
        timeout: float,
        *,
        kind: str,
        output: str,
        stderr: str,
    ) -> None:
        super().__init__(command, timeout, output=output, stderr=stderr)
        self.kind = kind

    def __str__(self) -> str:
        return f"{self.kind} timeout after {self.timeout:g} seconds"


class OutputLimitExceeded(subprocess.TimeoutExpired):
    def __init__(self, command: list[str], limit_bytes: int, *, output: str, stderr: str) -> None:
        super().__init__(command, limit_bytes, output=output, stderr=stderr)
        self.limit_bytes = limit_bytes

    def __str__(self) -> str:
        return f"combined output exceeded {self.limit_bytes} bytes"


def run_isolated(
    command: list[str],
    timeout_seconds: float,
    *,
    hard_timeout_seconds: float | None = None,
    environment: dict[str, str] | None = None,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> subprocess.CompletedProcess[str]:
    if max_output_bytes < 1:
        raise ValueError("max_output_bytes must be positive")
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        env=environment,
    )
    assert process.stdout is not None and process.stderr is not None
    hard_limit = hard_timeout_seconds if hard_timeout_seconds is not None else timeout_seconds
    started = time.monotonic()
    last_activity = started
    chunks: dict[str, list[bytes]] = {"stdout": [], "stderr": []}
    captured_bytes = 0
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    timeout_kind: str | None = None
    try:
        while selector.get_map() or process.poll() is None:
            now = time.monotonic()
            idle_remaining = timeout_seconds - (now - last_activity)
            hard_remaining = hard_limit - (now - started)
            if idle_remaining <= 0:
                timeout_kind = "inactivity"
                break
            if hard_remaining <= 0:
                timeout_kind = "hard-runtime"
                break
            wait_seconds = min(1.0, idle_remaining, hard_remaining)
            if not selector.get_map():
                time.sleep(min(0.05, wait_seconds))
                continue
            events = selector.select(wait_seconds)
            for key, _ in events:
                data = os.read(key.fileobj.fileno(), 65536)
                if data:
                    remaining = max_output_bytes - captured_bytes
                    if len(data) > remaining:
                        if remaining:
                            chunks[str(key.data)].append(data[:remaining])
                            captured_bytes += remaining
                        timeout_kind = "output-limit"
                        break
                    chunks[str(key.data)].append(data)
                    captured_bytes += len(data)
                    last_activity = time.monotonic()
                else:
                    selector.unregister(key.fileobj)
            if timeout_kind is not None:
                break
        if timeout_kind is not None:
            terminate_process_group(process)  # type: ignore[arg-type]
            stdout = b"".join(chunks["stdout"]).decode("utf-8", errors="replace")
            stderr = b"".join(chunks["stderr"]).decode("utf-8", errors="replace")
            if timeout_kind == "output-limit":
                raise OutputLimitExceeded(command, max_output_bytes, output=stdout, stderr=stderr)
            limit = timeout_seconds if timeout_kind == "inactivity" else hard_limit
            raise ProgressTimeoutExpired(
                command,
                limit,
                kind=timeout_kind,
                output=stdout,
                stderr=stderr,
            )
        return_code = process.wait()
    except BaseException:
        terminate_process_group(process)  # type: ignore[arg-type]
        raise
    finally:
        selector.close()
        process.stdout.close()
        process.stderr.close()
    stdout = b"".join(chunks["stdout"]).decode("utf-8", errors="replace")
    stderr = b"".join(chunks["stderr"]).decode("utf-8", errors="replace")
    return subprocess.CompletedProcess(command, return_code, stdout, stderr)


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


COMPLETED_STATUSES = {"completed", "existing_completed"}
RETRYABLE_STATUSES = {"generation_failed"}
RETRYABLE_TIMEOUT_KINDS = {"inactivity"}


def should_retry(status: str, timeout_kind: str | None = None) -> bool:
    if status == "timeout":
        return timeout_kind in RETRYABLE_TIMEOUT_KINDS
    return status in RETRYABLE_STATUSES


def should_retry_attempt(attempt: dict[str, object]) -> bool:
    return should_retry(
        str(attempt.get("status", "")),
        str(attempt["timeout_kind"]) if attempt.get("timeout_kind") is not None else None,
    )


def apply_case_feedback(
    environment: dict[str, str],
    case_id: str,
    retry_feedback: str | None,
    *,
    provider: str | None = None,
    model: str | None = None,
) -> None:
    mapping_text = environment.pop("PRODUCT_FLOW_RETRY_FEEDBACK_BY_CASE", "")
    selected = retry_feedback
    if selected is None and mapping_text:
        try:
            mapping = json.loads(mapping_text)
        except json.JSONDecodeError as error:
            raise ValueError("PRODUCT_FLOW_RETRY_FEEDBACK_BY_CASE must be valid JSON") from error
        if not isinstance(mapping, dict) or any(not isinstance(key, str) or not isinstance(value, str) for key, value in mapping.items()):
            raise ValueError("PRODUCT_FLOW_RETRY_FEEDBACK_BY_CASE must map case ids to strings")
        target_key = f"{case_id}:{provider}-{model}" if provider and model else None
        selected = mapping.get(target_key) if target_key else None
        if selected is None:
            selected = mapping.get(case_id)
    environment.pop("PRODUCT_FLOW_RETRY_FEEDBACK", None)
    if selected is None:
        return
    if len(selected) > 500 or "\n" in selected or "\r" in selected:
        raise ValueError("case retry feedback must be one bounded line")
    environment["PRODUCT_FLOW_RETRY_FEEDBACK"] = selected


def attempt_from_record(record: dict[str, object]) -> dict[str, object]:
    fields = (
        "started_at",
        "finished_at",
        "duration_seconds",
        "status",
        "exit_code",
        "error_summary",
        "manifest",
        "timeout_kind",
        "receipt",
    )
    return {field: record[field] for field in fields if field in record}


def run_case_attempt(
    provider: str,
    model: str,
    case_id: str,
    target: Path,
    timeout_seconds: float,
    hard_timeout_seconds: float,
    retry_feedback: str | None,
) -> dict[str, object]:
    relative_target = display_path(target)
    attempt: dict[str, object] = {"started_at": utc_now()}
    started = time.monotonic()
    try:
        manifest = verified_existing(target, provider, model, case_id)
        if manifest is not None:
            raise ValueError(f"refusing unreceipted pre-existing output: {display_path(target)}")
        else:
            if target.exists():
                if not target.is_dir() or target.is_symlink():
                    raise ValueError(f"target is unsafe: {target}")
            else:
                target.mkdir(mode=0o755)
            environment = os.environ.copy()
            environment["PRODUCT_FLOW_TARGET_ROOT"] = str(target.parent)
            apply_case_feedback(
                environment,
                case_id,
                retry_feedback,
                provider=provider,
                model=model,
            )
            completed = run_isolated(
                command_for(provider, model, case_id),
                timeout_seconds,
                hard_timeout_seconds=hard_timeout_seconds,
                environment=environment,
            )
            if completed.returncode == 0:
                completed_manifest = verified_existing(target, provider, model, case_id)
                if completed_manifest is None:
                    raise ValueError(f"runner produced no completed manifest: {display_path(target)}")
                attempt.update(
                    status="completed",
                    exit_code=0,
                    manifest=f"{relative_target}/run-manifest.json",
                    receipt=_manifest_receipt(target, completed_manifest),
                )
            else:
                summary = short_error(completed)
                attempt.update(
                    status=classify_failure(completed.returncode, summary),
                    exit_code=completed.returncode,
                    error_summary=summary,
                )
    except subprocess.TimeoutExpired as error:
        attempt.update(status="timeout", exit_code=None, error_summary=short_error(None, error))
        if isinstance(error, OutputLimitExceeded):
            attempt["timeout_kind"] = "output-limit"
        elif isinstance(error, ProgressTimeoutExpired):
            attempt["timeout_kind"] = error.kind
    except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError) as error:
        attempt.update(status="infrastructure_failure", exit_code=None, error_summary=str(error)[:500])
    attempt["finished_at"] = utc_now()
    attempt["duration_seconds"] = round(time.monotonic() - started, 3)
    return attempt


def apply_attempts(record: dict[str, object], attempts: list[dict[str, object]]) -> None:
    if not attempts:
        raise ValueError("a result must contain at least one attempt")
    final = attempts[-1]
    for field in (
        "status",
        "exit_code",
        "error_summary",
        "manifest",
        "finished_at",
        "duration_seconds",
        "timeout_kind",
        "receipt",
    ):
        if field in final:
            record[field] = final[field]
        else:
            record.pop(field, None)
    record["started_at"] = attempts[0]["started_at"]
    record["attempt_count"] = len(attempts)
    record["attempts"] = attempts


def run_case_with_retries(
    provider: str,
    model: str,
    case_id: str,
    target: Path,
    *,
    initial_attempts: list[dict[str, object]],
    max_attempts: int,
    timeout_seconds: float,
    hard_timeout_seconds: float,
    retry_delay_seconds: float,
    before_attempt: Callable[[], None] | None = None,
    on_attempt: Callable[[list[dict[str, object]]], None] | None = None,
    attempt_runner: Callable[..., dict[str, object]] = run_case_attempt,
    sleeper: Callable[[float], None] = time.sleep,
) -> list[dict[str, object]]:
    attempts = [dict(attempt) for attempt in initial_attempts]
    while len(attempts) < max_attempts:
        if attempts and not should_retry_attempt(attempts[-1]):
            break
        if before_attempt is not None:
            before_attempt()
        attempt_number = len(attempts) + 1
        retry_feedback = str(attempts[-1].get("error_summary", "")) if attempts else None
        attempt = attempt_runner(
            provider,
            model,
            case_id,
            target,
            timeout_seconds,
            hard_timeout_seconds,
            retry_feedback,
        )
        attempt["attempt"] = attempt_number
        attempts.append(attempt)
        if on_attempt is not None:
            on_attempt(attempts)
        if str(attempt["status"]) in COMPLETED_STATUSES or not should_retry_attempt(attempt):
            break
        if len(attempts) < max_attempts and retry_delay_seconds:
            sleeper(retry_delay_seconds)
    return attempts


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


def verify_frozen_files(entries: list[dict[str, str]]) -> None:
    for entry in entries:
        path = ROOT / entry["path"]
        if not path.is_file() or path.is_symlink() or digest(path) != entry["sha256"]:
            raise SystemExit(f"frozen evaluation input changed during the run: {entry['path']}")


def main() -> int:
    args = parse_args()
    output = args.output.expanduser().resolve()
    target_root_input = args.target_root.expanduser()
    if target_root_input.is_symlink():
        raise SystemExit(f"target root is unsafe: {target_root_input}")
    target_root = target_root_input.resolve()
    if output.exists() and not args.resume:
        raise SystemExit(f"refusing to overwrite existing ledger: {output}")
    if target_root.exists():
        if not target_root.is_dir() or target_root.is_symlink():
            raise SystemExit(f"target root is unsafe: {target_root}")
    else:
        target_root.mkdir(parents=True, mode=0o755)
    if any(not brief.is_file() or brief.is_symlink() for brief in BRIEFS.values()) or any(
        not path.is_file() or path.is_symlink() for path in TRUSTED_CONTEXT
    ):
        raise SystemExit("fixed briefs or Skill are missing/unsafe")

    cases = selected_cases(args.provider, args.theme, args.model)
    expected_contract = {
        "briefs": {
            case_id: {"path": str(path.relative_to(ROOT)), "sha256": digest(path)}
            for case_id, path in BRIEFS.items()
        },
        "skill": {"path": str(SKILL.relative_to(ROOT)), "sha256": digest(SKILL)},
        "trusted_context": [
            {"path": str(path.relative_to(ROOT)), "sha256": digest(path)} for path in TRUSTED_CONTEXT
        ],
        "evaluator_inputs": [
            {"path": str(path.relative_to(ROOT)), "sha256": digest(path)} for path in EVALUATOR_INPUTS
        ],
        "outputs_by_case": {case_id: list(outputs) for case_id, outputs in OUTPUTS_BY_CASE.items()},
        "artifact_root": display_path(target_root),
        "providers_are_separate_cohorts": True,
        "resolved_backend_snapshots_may_be_unreported": True,
        "generation_settings": {
            "effort": "model_default",
            "claude_extended_thinking": False,
            "codex_reasoning_summary": "none",
            "codex_internal_reasoning_disable_supported": False,
        },
        "context_routing": "runner_selects_smallest_fixed_set_by_caller_model_and_case",
    }
    frozen_entries = [
        *expected_contract["briefs"].values(),  # type: ignore[union-attr]
        *expected_contract["trusted_context"],  # type: ignore[misc]
        *expected_contract["evaluator_inputs"],  # type: ignore[misc]
    ]
    expected_selection = {
        "provider": args.provider,
        "model": args.model,
        "theme": args.theme,
        "count": len(cases),
    }
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
    ledger["retry_policy"] = {
        "inactivity_timeout_seconds": args.timeout_seconds,
        "hard_timeout_seconds": args.hard_timeout_seconds,
        "active_output_extends_inactivity_deadline": True,
        "prior_diagnostic_is_forwarded_to_fresh_retry": True,
        "max_attempts_per_case": args.max_attempts,
        "retry_delay_seconds": args.retry_delay_seconds,
        "retryable_statuses": sorted(RETRYABLE_STATUSES),
        "retryable_timeout_kinds": sorted(RETRYABLE_TIMEOUT_KINDS),
        "non_retryable_timeout_kinds": ["hard-runtime", "output-limit"],
        "policy_rejection_requires_explicit_remediation": True,
        "incomplete_matrix_exit_code": 1,
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
        target = target_for(provider, model, case_id, target_root)
        relative_target = display_path(target)
        previous = prior_by_key.get((provider, model, case_id))
        if previous is not None and previous.get("status") in COMPLETED_STATUSES:
            receipt = previous.get("receipt")
            if not isinstance(receipt, dict):
                raise SystemExit(f"completed resume result has no evaluator receipt: {relative_target}")
            verified_existing(target, provider, model, case_id, expected_receipt=receipt)
            print(f"preserving {provider} / {model} / {case_id}: {previous.get('status')}", flush=True)
            continue
        if previous is None:
            record: dict[str, object] = {
                "provider": provider,
                "model": model,
                "case_id": case_id,
                "target": relative_target,
            }
            attempts: list[dict[str, object]] = []
            ledger["results"].append(record)  # type: ignore[union-attr]
            print(f"starting {provider} / {model} / {case_id}", flush=True)
        else:
            record = previous
            raw_attempts = previous.get("attempts")
            if raw_attempts is None:
                attempts = [attempt_from_record(previous)] if previous.get("status") else []
            elif isinstance(raw_attempts, list) and all(isinstance(item, dict) for item in raw_attempts):
                attempts = [dict(item) for item in raw_attempts]
            else:
                raise SystemExit("resume ledger contains malformed attempt history")
            for index, attempt in enumerate(attempts, start=1):
                attempt.setdefault("attempt", index)
            print(
                f"resuming {provider} / {model} / {case_id} after {len(attempts)} attempt(s): {previous.get('status')}",
                flush=True,
            )

        def persist_attempt(current_attempts: list[dict[str, object]]) -> None:
            apply_attempts(record, current_attempts)
            record["total_duration_seconds"] = round(
                sum(float(item.get("duration_seconds", 0.0)) for item in current_attempts), 3
            )
            write_ledger(output, ledger)
            current = current_attempts[-1]
            print(
                f"finished attempt {current['attempt']} {provider} / {model} / {case_id}: {current['status']}",
                flush=True,
            )

        if len(attempts) < args.max_attempts and (not attempts or should_retry_attempt(attempts[-1])):
            print(
                f"attempting up to {args.max_attempts} total {provider} / {model} / {case_id}",
                flush=True,
            )
        attempts = run_case_with_retries(
            provider,
            model,
            case_id,
            target,
            initial_attempts=attempts,
            max_attempts=args.max_attempts,
            timeout_seconds=args.timeout_seconds,
            hard_timeout_seconds=args.hard_timeout_seconds,
            retry_delay_seconds=args.retry_delay_seconds,
            before_attempt=lambda: verify_frozen_files(frozen_entries),
            on_attempt=persist_attempt,
        )

        if not attempts:
            raise SystemExit("result has no runnable or resumable attempt")
        apply_attempts(record, attempts)
        write_ledger(output, ledger)

    statuses = [str(item["status"]) for item in ledger["results"]]  # type: ignore[index]
    if len(statuses) != len(cases):
        raise SystemExit("matrix result count does not match the requested selection")
    completed_count = sum(status in COMPLETED_STATUSES for status in statuses)
    ledger["status"] = "completed" if completed_count == len(cases) else "partial" if completed_count else "failed"
    ledger["finished_at"] = utc_now()
    ledger["summary"] = {
        "requested": len(statuses),
        "completed": completed_count,
        "failed": len(statuses) - completed_count,
        "attempts": sum(int(item.get("attempt_count", 1)) for item in ledger["results"]),  # type: ignore[index]
        "retried_cases": sum(int(item.get("attempt_count", 1)) > 1 for item in ledger["results"]),  # type: ignore[index]
        "statuses": {status: statuses.count(status) for status in sorted(set(statuses))},
    }
    write_ledger(output, ledger)
    return 0 if completed_count == len(statuses) else 1


if __name__ == "__main__":
    raise SystemExit(main())
