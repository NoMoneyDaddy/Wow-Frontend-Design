#!/usr/bin/env python3
"""Run the product-flow generation matrix and require complete browser screenshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from typing import Any, Iterator
from urllib.parse import unquote, urlsplit

import run_product_flow_matrix as matrix


ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / "wow-frontend-design" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))
from evidence_ledger import LedgerError, png_metadata  # noqa: E402

MATRIX_RUNNER = ROOT / "evals" / "run_product_flow_matrix.py"
DESIGN_LINTER = ROOT / "evals" / "lint_design_md_matrix.py"
VISUAL_AUDITOR = ROOT / "evals" / "playwright_visual_v4_audit.cjs"
CASE_PAGES = {
    "harbor-cold-chain-v4": ("index.html",),
    "island-sound-archive-v4": ("index.html",),
    "plant-swap-one-line-v4": ("index.html", "browse.html", "listing.html"),
}
MOBILE_USER_AGENT = "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"
VIEWPORTS = {
    "desktop": {
        "width": 1440,
        "height": 1000,
        "screenWidth": 1440,
        "screenHeight": 1000,
        "deviceScaleFactor": 1,
        "isMobile": False,
        "hasTouch": False,
        "userAgent": None,
    },
    "mobile": {
        "width": 390,
        "height": 844,
        "screenWidth": 390,
        "screenHeight": 844,
        "deviceScaleFactor": 3,
        "isMobile": True,
        "hasTouch": True,
        "userAgent": MOBILE_USER_AGENT,
    },
}
COMPLETED_STATUSES = {"completed", "existing_completed"}


class EvaluationError(ValueError):
    """Raised when a generation or screenshot inventory is incomplete or unsafe."""


class DesignFindingsError(EvaluationError):
    """Raised when the official DESIGN.md linter completed with findings."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("all", "claude", "codex"), default="all")
    parser.add_argument("--theme", choices=("all", *CASE_PAGES), default="all")
    parser.add_argument("--target-root", required=True, type=Path)
    parser.add_argument("--generation-output", required=True, type=Path)
    parser.add_argument("--design-output", required=True, type=Path)
    parser.add_argument("--visual-output", required=True, type=Path)
    parser.add_argument("--screenshot-dir", required=True, type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--retry-delay-seconds", type=float, default=5.0)
    parser.add_argument("--capture-max-attempts", type=int, default=3)
    parser.add_argument("--capture-timeout-seconds", type=int, default=300)
    parser.add_argument("--lint-max-attempts", type=int, default=3)
    parser.add_argument("--lint-timeout-seconds", type=int, default=180)
    parser.add_argument("--chrome-executable", type=Path)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.capture_max_attempts < 1 or args.capture_max_attempts > 10:
        parser.error("--capture-max-attempts must be within 1..10")
    if args.capture_timeout_seconds < 30 or args.capture_timeout_seconds > 1800:
        parser.error("--capture-timeout-seconds must be within 30..1800")
    if args.lint_max_attempts < 1 or args.lint_max_attempts > 10:
        parser.error("--lint-max-attempts must be within 1..10")
    if args.lint_timeout_seconds < 30 or args.lint_timeout_seconds > 600:
        parser.error("--lint-timeout-seconds must be within 30..600")
    return args


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise EvaluationError(f"{label} is missing or unsafe: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EvaluationError(f"cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise EvaluationError(f"{label} must be a JSON object")
    return value


def _safe_target(value: Any, artifact_root: Path) -> Path:
    if not isinstance(value, str) or not value:
        raise EvaluationError("generation target path is invalid")
    candidate = PurePosixPath(value)
    if "\x00" in value or (not candidate.is_absolute() and ".." in candidate.parts):
        raise EvaluationError(f"generation target path is unsafe: {value}")
    target = (Path(value) if candidate.is_absolute() else ROOT / candidate).resolve()
    if target.parent != artifact_root:
        raise EvaluationError(f"generation target escapes the artifact root: {value}")
    if not target.is_dir() or target.is_symlink():
        raise EvaluationError(f"generation target is missing or unsafe: {value}")
    return target


def completed_targets(generation_output: Path) -> list[dict[str, Any]]:
    ledger = _load_json(generation_output, "generation ledger")
    if ledger.get("status") != "completed":
        raise EvaluationError("generation matrix is incomplete")
    selection = ledger.get("selection")
    contract = ledger.get("contract")
    results = ledger.get("results")
    if not isinstance(contract, dict) or not isinstance(contract.get("artifact_root"), str):
        raise EvaluationError("generation ledger has no artifact root")
    artifact_root = Path(contract["artifact_root"]).resolve()
    if not artifact_root.is_dir() or artifact_root.is_symlink():
        raise EvaluationError("generation artifact root is missing or unsafe")
    if not isinstance(selection, dict) or not isinstance(results, list) or selection.get("count") != len(results):
        raise EvaluationError("generation ledger selection/result count disagrees")
    targets: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for result in results:
        if not isinstance(result, dict) or result.get("status") not in COMPLETED_STATUSES:
            raise EvaluationError("generation ledger contains an incomplete result")
        provider = result.get("provider")
        model = result.get("model")
        case_id = result.get("case_id")
        if provider not in {"claude", "codex"} or not isinstance(model, str) or case_id not in CASE_PAGES:
            raise EvaluationError("generation ledger contains an unknown target")
        alias = f"{provider}-{model}"
        key = (str(case_id), alias)
        if key in seen:
            raise EvaluationError("generation ledger contains a duplicate visual target")
        seen.add(key)
        target = _safe_target(result.get("target"), artifact_root)
        expected_name = f"{alias}-{case_id}"
        if target.name != expected_name:
            raise EvaluationError(f"generation target name disagrees with model/case: {target.name}")
        for page in CASE_PAGES[str(case_id)]:
            artifact = target / page
            if not artifact.is_file() or artifact.is_symlink():
                raise EvaluationError(f"generated page is missing or unsafe: {artifact}")
        targets.append({"case_id": str(case_id), "alias": alias, "directory": target})
    return targets


def _handler_for(routes: dict[str, Path]) -> type[BaseHTTPRequestHandler]:
    class AllowlistHandler(BaseHTTPRequestHandler):
        def _serve(self, include_body: bool) -> None:
            parsed = urlsplit(self.path)
            request_path = unquote(parsed.path)
            if parsed.query or parsed.fragment or request_path not in routes:
                self.send_error(404)
                return
            artifact = routes[request_path]
            if not artifact.is_file() or artifact.is_symlink():
                self.send_error(404)
                return
            body = artifact.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if include_body:
                self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            self._serve(True)

        def do_HEAD(self) -> None:  # noqa: N802
            self._serve(False)

        def log_message(self, _format: str, *_args: object) -> None:
            return

    return AllowlistHandler


@contextmanager
def serve_targets(targets: list[dict[str, Any]]) -> Iterator[list[str]]:
    routes: dict[str, Path] = {}
    bases: list[str] = []
    for index, target in enumerate(targets):
        prefix = f"/target-{index}/"
        for page in CASE_PAGES[target["case_id"]]:
            routes[f"{prefix}{page}"] = target["directory"] / page
        bases.append(prefix)
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler_for(routes))
    thread = threading.Thread(target=server.serve_forever, name="product-flow-visual-server", daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        yield [f"http://127.0.0.1:{port}{base}" for base in bases]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _png_size(path: Path) -> tuple[int, int]:
    try:
        media_type, width, height = png_metadata(path.read_bytes())
    except (OSError, LedgerError) as error:
        raise EvaluationError(f"screenshot failed full PNG decode: {path}: {error}") from error
    if media_type != "image/png":
        raise EvaluationError(f"screenshot is not a PNG: {path}")
    return width, height


def validate_visual_completion(
    visual_output: Path,
    screenshot_dir: Path,
    targets: list[dict[str, Any]],
) -> int:
    report = _load_json(visual_output, "visual report")
    auditor = report.get("auditor")
    if not isinstance(auditor, dict) or auditor.get("sha256") != _digest(VISUAL_AUDITOR):
        raise EvaluationError("visual report auditor provenance disagrees")
    reported_viewports = report.get("viewports")
    if reported_viewports != [{"name": name, **profile} for name, profile in VIEWPORTS.items()]:
        raise EvaluationError("visual report viewport contract disagrees")
    reported_targets = report.get("targets")
    expected_targets = {(target["case_id"], target["alias"]) for target in targets}
    actual_targets = {
        (target.get("caseId"), target.get("alias"))
        for target in reported_targets
        if isinstance(target, dict)
    } if isinstance(reported_targets, list) else set()
    if not isinstance(reported_targets, list) or len(reported_targets) != len(expected_targets) or actual_targets != expected_targets:
        raise EvaluationError("visual report target inventory disagrees")
    expected = {
        (target["case_id"], target["alias"], page, viewport)
        for target in targets
        for page in CASE_PAGES[target["case_id"]]
        for viewport in VIEWPORTS
    }
    results = report.get("results")
    if not isinstance(results, list) or len(results) != len(expected):
        raise EvaluationError(f"visual result count must be {len(expected)}")
    root = screenshot_dir.resolve()
    seen: set[tuple[str, str, str, str]] = set()
    screenshot_paths: set[Path] = set()
    for result in results:
        if not isinstance(result, dict):
            raise EvaluationError("visual result is malformed")
        key = (result.get("caseId"), result.get("alias"), result.get("page"), result.get("viewport"))
        if key in seen or key not in expected:
            raise EvaluationError(f"visual result identity is invalid: {key}")
        seen.add(key)  # type: ignore[arg-type]
        screenshot_value = result.get("screenshot")
        if not isinstance(screenshot_value, str) or not screenshot_value:
            raise EvaluationError(f"visual result has no screenshot: {key}")
        screenshot = Path(screenshot_value)
        if not screenshot.is_absolute():
            screenshot = ROOT / screenshot
        screenshot = screenshot.resolve()
        try:
            screenshot.relative_to(root)
        except ValueError as error:
            raise EvaluationError(f"screenshot escapes the requested directory: {screenshot}") from error
        if not screenshot.is_file() or screenshot.is_symlink():
            raise EvaluationError(f"screenshot is missing or unsafe: {screenshot}")
        profile = VIEWPORTS[str(key[3])]
        width = int(profile["width"])
        height = int(profile["height"])
        scale = int(profile["deviceScaleFactor"])
        if _png_size(screenshot) != (width * scale, height * scale) or result.get("size") != f"{width}x{height}":
            raise EvaluationError(f"screenshot dimensions disagree: {key}")
        if result.get("screenshotSha256") != _digest(screenshot):
            raise EvaluationError(f"screenshot hash disagrees: {key}")
        screenshot_paths.add(screenshot)
    if seen != expected:
        raise EvaluationError("visual screenshot inventory is incomplete")
    actual_pngs = {path.resolve() for path in screenshot_dir.glob("*.png") if path.is_file() and not path.is_symlink()}
    if actual_pngs != screenshot_paths:
        raise EvaluationError("screenshot directory contains missing or extra PNG files")
    summary = report.get("summary")
    if not isinstance(summary, dict) or summary.get("checkedPages") != len(expected):
        raise EvaluationError("visual report summary is incomplete")
    return len(expected)


def validate_design_completion(design_output: Path, targets: list[dict[str, Any]]) -> tuple[int, int]:
    report = _load_json(design_output, "DESIGN.md lint report")
    if report.get("linter") != {"package": "@google/design.md", "version": "0.2.0"}:
        raise EvaluationError("DESIGN.md report did not use the pinned official linter")
    results = report.get("results")
    expected = {(target["alias"].split("-", 1)[0], target["alias"].split("-", 1)[1], target["case_id"]) for target in targets}
    if not isinstance(results, list) or len(results) != len(expected):
        raise EvaluationError(f"DESIGN.md result count must be {len(expected)}")
    seen: set[tuple[str, str, str]] = set()
    clean = findings = 0
    for result in results:
        if not isinstance(result, dict):
            raise EvaluationError("DESIGN.md result is malformed")
        key = (result.get("provider"), result.get("model"), result.get("case_id"))
        if key in seen or key not in expected:
            raise EvaluationError(f"DESIGN.md result identity is invalid: {key}")
        seen.add(key)  # type: ignore[arg-type]
        status = result.get("status")
        if status == "clean":
            clean += 1
        elif status == "findings":
            findings += 1
        else:
            raise EvaluationError(f"DESIGN.md lint did not complete for {key}")
        summary = result.get("summary")
        if not isinstance(summary, dict) or any(not isinstance(summary.get(field), int) for field in ("errors", "warnings", "infos")):
            raise EvaluationError(f"DESIGN.md summary is malformed for {key}")
    summary = report.get("summary")
    if summary != {
        "checked": len(expected),
        "clean": clean,
        "with_findings": findings,
        "infrastructure_failures": 0,
    }:
        raise EvaluationError("DESIGN.md aggregate summary is incomplete")
    if findings:
        raise DesignFindingsError(f"DESIGN.md clean gate rejected {findings} target(s) with findings")
    return clean, findings


def blocking_visual_findings(visual_output: Path) -> dict[str, list[str]]:
    report = _load_json(visual_output, "visual report")
    by_target: dict[str, set[str]] = {}
    for collection_name in ("results", "crossPageComparisons"):
        collection = report.get(collection_name)
        if not isinstance(collection, list):
            raise EvaluationError(f"visual report {collection_name} is malformed")
        for result in collection:
            if not isinstance(result, dict):
                raise EvaluationError(f"visual report {collection_name} entry is malformed")
            issues = result.get("visualIssues")
            if not isinstance(issues, list) or any(not isinstance(issue, str) or not issue for issue in issues):
                raise EvaluationError(f"visual report {collection_name} issues are malformed")
            if issues:
                key = f"{result.get('caseId')}:{result.get('alias')}"
                by_target.setdefault(key, set()).update(issues)
    normalized = {key: sorted(issues) for key, issues in sorted(by_target.items())}
    summary = report.get("summary")
    if not isinstance(summary, dict):
        raise EvaluationError("visual report summary is malformed")
    expected_verdict = "observed_issues" if normalized else "no_observed_issues"
    if summary.get("verdict") != expected_verdict:
        raise EvaluationError("visual report verdict disagrees with blocking issues")
    return normalized


def _archive_failed_path(path: Path, attempt: int) -> Path:
    destination = path.with_name(f"{path.name}.failed-attempt-{attempt}")
    if destination.exists():
        raise EvaluationError(f"refusing to overwrite failed-attempt evidence: {destination}")
    path.rename(destination)
    return destination


def _run_generation(args: argparse.Namespace, output: Path) -> int:
    command = [
        sys.executable,
        str(MATRIX_RUNNER),
        "--provider",
        args.provider,
        "--theme",
        args.theme,
        "--output",
        str(output),
        "--target-root",
        str(args.target_root.expanduser().resolve()),
        "--timeout-seconds",
        str(args.timeout_seconds),
        "--max-attempts",
        str(args.max_attempts),
        "--retry-delay-seconds",
        str(args.retry_delay_seconds),
    ]
    if args.resume:
        command.append("--resume")
    process = subprocess.Popen(command, cwd=ROOT, start_new_session=True)
    try:
        return process.wait()
    except BaseException:
        matrix.terminate_process_group(process)
        raise


def _run_design_attempt(args: argparse.Namespace, generation_output: Path, design_output: Path) -> subprocess.CompletedProcess[str]:
    return matrix.run_isolated(
        [
            sys.executable,
            str(DESIGN_LINTER),
            "--ledger",
            str(generation_output),
            "--no-supplemental-retry",
            "--output",
            str(design_output),
            "--timeout-seconds",
            str(min(args.lint_timeout_seconds, 300)),
        ],
        args.lint_timeout_seconds,
    )


def _run_visual_attempt(
    args: argparse.Namespace,
    targets: list[dict[str, Any]],
    bases: list[str],
    visual_output: Path,
    screenshot_dir: Path,
) -> subprocess.CompletedProcess[str]:
    command = [
        "node",
        str(VISUAL_AUDITOR),
        "--output",
        os.path.relpath(visual_output, ROOT),
        "--artifact-dir",
        os.path.relpath(screenshot_dir, ROOT),
    ]
    if len(targets) != len(bases):
        raise EvaluationError("visual target/base counts disagree")
    for target, base in zip(targets, bases):
        command.extend(["--target", f"{target['case_id']}:{target['alias']}={base}"])
    environment = os.environ.copy()
    if args.chrome_executable is not None:
        chrome = args.chrome_executable.expanduser().resolve()
        if not chrome.is_file() or chrome.is_symlink():
            raise EvaluationError(f"Chrome executable is missing or unsafe: {chrome}")
        environment["CHROME_EXECUTABLE_PATH"] = str(chrome)
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=args.capture_timeout_seconds)
    except BaseException:
        matrix.terminate_process_group(process)
        raise
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def _prepare_capture_paths(visual_output: Path, screenshot_dir: Path, resume: bool) -> bool:
    if visual_output.exists():
        if resume:
            return False
        raise EvaluationError(f"refusing to overwrite visual report: {visual_output}")
    if screenshot_dir.exists():
        if screenshot_dir.is_symlink() or not screenshot_dir.is_dir():
            raise EvaluationError(f"screenshot directory is unsafe: {screenshot_dir}")
        if any(screenshot_dir.iterdir()):
            if not resume:
                raise EvaluationError(f"refusing non-empty screenshot directory: {screenshot_dir}")
            _archive_failed_path(screenshot_dir, 0)
            screenshot_dir.mkdir()
    else:
        screenshot_dir.mkdir(parents=True)
    visual_output.parent.mkdir(parents=True, exist_ok=True)
    return True


def main() -> int:
    args = parse_args()
    generation_output = args.generation_output.expanduser().resolve()
    design_output = args.design_output.expanduser().resolve()
    visual_output = args.visual_output.expanduser().resolve()
    screenshot_dir = args.screenshot_dir.expanduser().resolve()
    target_root_input = args.target_root.expanduser()
    if target_root_input.is_symlink():
        print("product-flow evaluation incomplete: target root is unsafe", file=sys.stderr)
        return 1
    target_root = target_root_input.resolve()
    if len({generation_output, design_output, visual_output}) != 3:
        print("product-flow evaluation incomplete: generation, design, and visual outputs must differ", file=sys.stderr)
        return 1
    if target_root == (ROOT / "evals").resolve():
        print("product-flow evaluation incomplete: --target-root must isolate a new evaluation run", file=sys.stderr)
        return 1
    if target_root.exists():
        if not target_root.is_dir() or target_root.is_symlink():
            print("product-flow evaluation incomplete: target root is unsafe", file=sys.stderr)
            return 1
        if any(target_root.iterdir()) and not args.resume:
            print("product-flow evaluation incomplete: target root is not empty; use a new root or --resume", file=sys.stderr)
            return 1
    else:
        target_root.mkdir(parents=True, mode=0o755)
    if _run_generation(args, generation_output) != 0:
        print("product-flow evaluation incomplete: generation matrix failed after retries", file=sys.stderr)
        return 1
    try:
        targets = completed_targets(generation_output)
        design_complete = False
        if design_output.exists():
            if not args.resume:
                raise EvaluationError(f"refusing to overwrite DESIGN.md report: {design_output}")
            try:
                clean, findings = validate_design_completion(design_output, targets)
            except DesignFindingsError:
                raise
            except EvaluationError:
                _archive_failed_path(design_output, 0)
            else:
                design_complete = True
                print(f"DESIGN.md lint retained: {clean} clean, {findings} with findings")
        if not design_complete:
            design_output.parent.mkdir(parents=True, exist_ok=True)
            for attempt in range(1, args.lint_max_attempts + 1):
                try:
                    completed = _run_design_attempt(args, generation_output, design_output)
                except subprocess.TimeoutExpired as error:
                    completed = subprocess.CompletedProcess([], 124, "", f"timed out: {error}")
                if completed.returncode == 0:
                    try:
                        clean, findings = validate_design_completion(design_output, targets)
                    except DesignFindingsError:
                        raise
                    except EvaluationError as error:
                        completed = subprocess.CompletedProcess(completed.args, 1, completed.stdout, str(error))
                    else:
                        design_complete = True
                        print(f"DESIGN.md lint complete: {clean} clean, {findings} with findings")
                        break
                diagnostic = " ".join((completed.stderr or completed.stdout or "lint failed").split())[:500]
                print(
                    f"DESIGN.md lint attempt {attempt}/{args.lint_max_attempts} failed: {diagnostic}",
                    file=sys.stderr,
                    flush=True,
                )
                if design_output.exists():
                    _archive_failed_path(design_output, attempt)
                if attempt < args.lint_max_attempts and args.retry_delay_seconds:
                    time.sleep(args.retry_delay_seconds)
            if not design_complete:
                raise EvaluationError("DESIGN.md lint failed after retries")
        should_capture = _prepare_capture_paths(visual_output, screenshot_dir, args.resume)
        if not should_capture:
            count = validate_visual_completion(visual_output, screenshot_dir, targets)
            blockers = blocking_visual_findings(visual_output)
            if blockers:
                print(
                    f"product-flow execution complete: {len(targets)} targets and {count} screenshots retained; "
                    f"acceptance failed for {len(blockers)} target(s)",
                    file=sys.stderr,
                )
                return 1
            print(f"product-flow execution complete and acceptance passed: {len(targets)} targets and {count} screenshots retained")
            return 0
        with serve_targets(targets) as bases:
            for attempt in range(1, args.capture_max_attempts + 1):
                try:
                    completed = _run_visual_attempt(args, targets, bases, visual_output, screenshot_dir)
                except subprocess.TimeoutExpired as error:
                    completed = subprocess.CompletedProcess([], 124, "", f"timed out: {error}")
                if completed.returncode == 0:
                    try:
                        count = validate_visual_completion(visual_output, screenshot_dir, targets)
                    except EvaluationError as error:
                        completed = subprocess.CompletedProcess(completed.args, 1, completed.stdout, str(error))
                    else:
                        blockers = blocking_visual_findings(visual_output)
                        if blockers:
                            print(
                                f"product-flow execution complete: {len(targets)} targets and {count} screenshots captured; "
                                f"acceptance failed for {len(blockers)} target(s)",
                                file=sys.stderr,
                            )
                            return 1
                        print(
                            f"product-flow execution complete and acceptance passed: "
                            f"{len(targets)} targets and {count} screenshots captured"
                        )
                        return 0
                diagnostic = " ".join((completed.stderr or completed.stdout or "capture failed").split())[:500]
                print(
                    f"visual capture attempt {attempt}/{args.capture_max_attempts} failed: {diagnostic}",
                    file=sys.stderr,
                    flush=True,
                )
                if visual_output.exists():
                    _archive_failed_path(visual_output, attempt)
                if screenshot_dir.exists():
                    _archive_failed_path(screenshot_dir, attempt)
                if attempt < args.capture_max_attempts:
                    screenshot_dir.mkdir()
                    if args.retry_delay_seconds:
                        time.sleep(args.retry_delay_seconds)
    except (EvaluationError, OSError) as error:
        print(f"product-flow evaluation incomplete: {error}", file=sys.stderr)
        return 1
    print("product-flow evaluation incomplete: screenshots failed after retries", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
