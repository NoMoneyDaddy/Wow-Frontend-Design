#!/usr/bin/env python3
"""Run the product-flow generation matrix and require complete browser screenshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
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
VISUAL_AUDITOR = ROOT / "evals" / "playwright_visual_v7_audit.cjs"
CASE_PAGES = {
    "wind-maintenance-dispatch-v6": ("index.html",),
    "type-foundry-specimen-v6": ("index.html",),
    "repair-cafe-intake-v6": ("index.html",),
    "night-market-allergen-v6": ("index.html",),
    "royalty-statement-v6": ("index.html",),
    "packaging-configurator-v6": ("index.html", "materials.html", "summary.html"),
    "oral-history-archive-v6": ("index.html", "archive.html", "story.html"),
    "grant-review-board-v6": ("index.html",),
}
MOBILE_USER_AGENT = "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"
TABLET_USER_AGENT = "Mozilla/5.0 (Linux; Android 14; Pixel Tablet) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
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
    "tablet": {
        "width": 834,
        "height": 1112,
        "screenWidth": 834,
        "screenHeight": 1112,
        "deviceScaleFactor": 2,
        "isMobile": True,
        "hasTouch": True,
        "userAgent": TABLET_USER_AGENT,
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
    "compact-mobile": {
        "width": 360,
        "height": 800,
        "screenWidth": 360,
        "screenHeight": 800,
        "deviceScaleFactor": 3,
        "isMobile": True,
        "hasTouch": True,
        "userAgent": MOBILE_USER_AGENT,
    },
}
COMPLETED_STATUSES = {"completed", "existing_completed"}
FONT_EVIDENCE_CLASSIFICATIONS = {
    "failed_font_face",
    "fallback_rendered",
    "not_applicable",
    "platform_fonts_unavailable",
    "rendered",
    "unverified_alias",
}
GENERIC_FONT_FAMILIES = {
    "-apple-system", "blinkmacsystemfont", "cursive", "emoji", "fangsong", "fantasy",
    "math", "monospace", "sans-serif", "serif", "system-ui", "ui-monospace", "ui-rounded",
    "ui-sans-serif", "ui-serif",
}
FONT_ANGLE_EPSILON = 0.001


def _normalize_font_family(value: object) -> str:
    return " ".join(str(value or "").strip().split()).lower()


def _classify_font_evidence_role(role: dict[str, Any]) -> str:
    primary = _normalize_font_family(role.get("declaredPrimary"))
    is_generic = not role["declaredPrimaryQuoted"] and (
        primary in GENERIC_FONT_FAMILIES or primary.startswith("generic(")
    )
    if not primary or is_generic:
        return "not_applicable"
    if role["declaredFaceSelectionUnavailable"]:
        return "evidence_unavailable"
    if not role["probeHasRelevantGlyph"]:
        return "not_applicable"
    actual_families = {
        _normalize_font_family(value)
        for font in role["actualFonts"]
        if font["glyphCount"] > 0
        for value in (font["familyName"], font["postScriptName"])
        if _normalize_font_family(value)
    }
    matching_faces = [
        face for face in role["fontFaces"]
        if _normalize_font_family(face["family"]) == primary
    ]
    if role["declaredFaceSelectionFailed"]:
        return "failed_font_face"
    if not actual_families:
        return "platform_fonts_unavailable"
    if primary in actual_families:
        return "rendered"
    if any(face["status"] == "loaded" for face in matching_faces):
        return "unverified_alias"
    return "fallback_rendered"


def _numeric_descriptor_range(value: object, aliases: dict[str, float] | None = None) -> tuple[float, float] | None:
    normalized = str(value or "normal").strip().lower()
    if aliases and normalized in aliases:
        return aliases[normalized], aliases[normalized]
    numbers = [float(number) for number in re.findall(r"\d+(?:\.\d+)?", normalized)]
    if not numbers:
        return None
    return (numbers[0], numbers[0]) if len(numbers) == 1 else (numbers[0], numbers[1])


def _font_style_descriptor(value: object) -> tuple[str, tuple[float, float]]:
    normalized = str(value or "normal").strip().lower()
    if normalized.startswith("italic"):
        return "italic", (14.0, 14.0)
    if normalized.startswith("oblique"):
        angles = []
        for number, unit in re.findall(r"([+-]?(?:\d+(?:\.\d+)?|\.\d+))(deg|grad|rad|turn)\b", normalized):
            angle = float(number)
            angles.append({"deg": angle, "grad": angle * 0.9, "rad": angle * 180 / math.pi, "turn": angle * 360}[unit])
        return "oblique", (min(angles), max(angles)) if angles else (14.0, 14.0)
    return "normal", (0.0, 0.0)


def _select_boundary_faces(
    candidates: list[tuple[dict[str, Any], tuple[float, float]]],
    boundary_index: int,
    direction: str,
) -> list[dict[str, Any]]:
    if not candidates:
        return []
    values = [item[1][boundary_index] for item in candidates]
    boundary = min(values) if direction == "min" else max(values)
    return [face for face, value_range in candidates if value_range[boundary_index] == boundary]


def _select_style_faces(faces: list[dict[str, Any]], requested_value: object) -> list[dict[str, Any]]:
    requested_category, requested_range = _font_style_descriptor(requested_value)
    requested_angle = 0.0 if requested_category == "normal" else requested_range[0]
    candidates = []
    for face in faces:
        category, value_range = _font_style_descriptor(face["style"])
        candidates.append((face, (0.0, 0.0) if category == "normal" else ((14.0, 14.0) if category == "italic" else value_range)))
    oriented = [(face, (-value_range[1], -value_range[0])) for face, value_range in candidates] if requested_angle < 0 else candidates
    target = abs(requested_angle)
    same_direction = [(face, value_range) for face, value_range in oriented if value_range[1] >= -FONT_ANGLE_EPSILON]
    exact = [face for face, value_range in same_direction if value_range[0] - FONT_ANGLE_EPSILON <= target <= value_range[1] + FONT_ANGLE_EPSILON]
    if exact:
        return exact
    below = [(face, value_range) for face, value_range in same_direction if value_range[1] < target - FONT_ANGLE_EPSILON]
    above = [(face, value_range) for face, value_range in same_direction if value_range[0] > target + FONT_ANGLE_EPSILON]
    order = ((above, 0, "min"), (below, 1, "max")) if target >= 14 else ((below, 1, "max"), (above, 0, "min"))
    for pool, boundary_index, direction in order:
        selected = _select_boundary_faces(pool, boundary_index, direction)
        if selected:
            return selected
    return _select_boundary_faces([(face, value_range) for face, value_range in oriented if value_range[1] < 0], 1, "max")


def _unicode_range_covers(value: object, code_point: int) -> bool:
    ranges = []
    for part in str(value or "U+0-10FFFF").split(","):
        match = re.fullmatch(r"U\+([0-9A-F?]+)(?:-([0-9A-F]+))?", part.strip(), re.IGNORECASE)
        if not match:
            continue
        start = int(match.group(1).replace("?", "0"), 16)
        end = int((match.group(2) or match.group(1)).replace("?", "F"), 16)
        ranges.append((start, end))
    return not ranges or any(start <= code_point <= end for start, end in ranges)


def _select_stretch_faces(faces: list[dict[str, Any]], requested_stretch: object) -> list[dict[str, Any]]:
    aliases = {
        "ultra-condensed": 50, "extra-condensed": 62.5, "condensed": 75, "semi-condensed": 87.5,
        "normal": 100, "semi-expanded": 112.5, "expanded": 125, "extra-expanded": 150, "ultra-expanded": 200,
    }
    role_stretch_range = _numeric_descriptor_range(requested_stretch, aliases)
    selected = list(faces)
    if role_stretch_range is None or not selected:
        return selected
    role_stretch = role_stretch_range[0]
    candidates = [(face, _numeric_descriptor_range(face["stretch"], aliases) or (100.0, 100.0)) for face in selected]
    exact = [face for face, value_range in candidates if value_range[0] <= role_stretch <= value_range[1]]
    if exact:
        return exact
    if role_stretch <= 100:
        narrower = [(face, value_range) for face, value_range in candidates if value_range[1] < role_stretch]
        pool = narrower or [(face, value_range) for face, value_range in candidates if value_range[0] > role_stretch]
        boundary_index = 1 if narrower else 0
        direction = "max" if narrower else "min"
    else:
        wider = [(face, value_range) for face, value_range in candidates if value_range[0] > role_stretch]
        pool = wider or [(face, value_range) for face, value_range in candidates if value_range[1] < role_stretch]
        boundary_index = 0 if wider else 1
        direction = "min" if wider else "max"
    return _select_boundary_faces(pool, boundary_index, direction)


def _selected_font_faces(role: dict[str, Any], faces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    family = _normalize_font_family(role["declaredPrimary"])
    selected = [face for face in faces if _normalize_font_family(face["family"]) == family]
    selected = _select_stretch_faces(selected, role["fontStretch"])
    selected = _select_style_faces(selected, role["fontStyle"])
    role_weight_range = _numeric_descriptor_range(role["fontWeight"], {"normal": 400, "bold": 700})
    if role_weight_range is None:
        return selected
    role_weight = role_weight_range[0]
    candidates = [(face, _numeric_descriptor_range(face["weight"], {"normal": 400, "bold": 700}) or (400.0, 400.0)) for face in selected]
    matches = [face for face, value_range in candidates if value_range[0] <= role_weight <= value_range[1]]
    if matches or not candidates:
        return matches

    def preference(value_range: tuple[float, float]) -> tuple[int, float]:
        if role_weight < 400:
            return (0, role_weight - value_range[1]) if value_range[1] < role_weight else (1, value_range[0] - role_weight)
        if role_weight > 500:
            return (0, value_range[0] - role_weight) if value_range[0] > role_weight else (1, role_weight - value_range[1])
        if role_weight <= value_range[0] <= 500:
            return 0, value_range[0] - role_weight
        if value_range[1] < role_weight:
            return 1, role_weight - value_range[1]
        return 2, value_range[0] - 500

    ranked = [(face, preference(value_range)) for face, value_range in candidates]
    best = min(value for _, value in ranked)
    return [face for face, value in ranked if value == best]


def _font_face_selection_state(role: dict[str, Any], faces: list[dict[str, Any]]) -> str:
    if not role["probeCodePoints"]:
        return "resolved"
    selected = _selected_font_faces(role, faces)
    pending = False
    ambiguous = False
    for code_point in role["probeCodePoints"]:
        covering = [face for face in selected if _unicode_range_covers(face["unicodeRange"], code_point)]
        if covering and all(face["status"] == "error" for face in covering):
            return "failed"
        if any(face["status"] == "error" for face in covering) and any(face["status"] == "loaded" for face in covering):
            ambiguous = True
        if covering and not any(face["status"] == "loaded" for face in covering):
            pending = pending or any(face["status"] in {"loading", "unloaded"} for face in covering)
    return "unavailable" if pending or ambiguous else "resolved"


def _expected_font_face_selection_state(role: dict[str, Any]) -> str:
    state = "unavailable" if role["probeRelevantGlyphOverflow"] else (
        _font_face_selection_state(role, role["fontFaces"]) if role["probeHasRelevantGlyph"] else "resolved"
    )
    if not role["probeTextComplete"] and role["probeHasRelevantGlyph"]:
        state = "unavailable"
    has_relevant_failed_face = any(
        face["status"] == "error"
        and _normalize_font_family(face["family"]) == _normalize_font_family(role["declaredPrimary"])
        and any(_unicode_range_covers(face["unicodeRange"], code_point) for code_point in role["probeCodePoints"])
        for face in role["fontFaces"]
    )
    if (
        not role["fontProbeStable"]
        or not role["fontInventoryStable"]
        or not role["platformFontsStable"]
        or not role["fontPaintEvidenceReliable"]
        or role["browserGeneratedTextUnavailable"]
        or role["renderedTextMappingUnavailable"]
        or role["pseudoTextMappingUnavailable"]
    ):
        return "unavailable"
    if role["declaredFaceCheckReliable"] and role["declaredFaceCheck"] and state == "failed":
        return "unavailable"
    if (
        role["declaredFaceCheckReliable"]
        and not role["declaredFaceCheck"]
        and has_relevant_failed_face
        and role["probeHasRelevantGlyph"]
        and state == "resolved"
    ):
        return "unavailable"
    return state


def locked_package_record(package_name: str) -> dict[str, str]:
    payload = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    record = payload.get("packages", {}).get(f"node_modules/{package_name}", {})
    values = {field: record.get(field) for field in ("version", "resolved", "integrity")}
    if any(not isinstance(value, str) or not value or any(character.isspace() for character in value) for value in values.values()):
        raise ValueError(f"package-lock.json has no exact integrity-bound {package_name} record")
    return values  # type: ignore[return-value]


def locked_package_version(package_name: str) -> str:
    return locked_package_record(package_name)["version"]


PLAYWRIGHT_LOCK = locked_package_record("playwright")
PLAYWRIGHT_VERSION = PLAYWRIGHT_LOCK["version"]
DESIGN_MD_VERSION = locked_package_version("@google/design.md")


class EvaluationError(ValueError):
    """Raised when a generation or screenshot inventory is incomplete or unsafe."""


class DesignFindingsError(EvaluationError):
    """Raised when the official DESIGN.md linter completed with findings."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("all", "claude", "codex"), default="all")
    parser.add_argument("--model", choices=("all", *matrix.MODELS), default="all")
    parser.add_argument("--theme", choices=("all", *CASE_PAGES), default="all")
    parser.add_argument("--target-root", required=True, type=Path)
    parser.add_argument("--generation-output", required=True, type=Path)
    parser.add_argument("--design-output", required=True, type=Path)
    parser.add_argument("--visual-output", required=True, type=Path)
    parser.add_argument("--screenshot-dir", required=True, type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--retry-delay-seconds", type=float, default=5.0)
    parser.add_argument("--capture-max-attempts", type=int, default=3)
    parser.add_argument("--capture-timeout-seconds", type=int, default=300)
    parser.add_argument("--lint-max-attempts", type=int, default=3)
    parser.add_argument("--lint-timeout-seconds", type=int, default=180)
    parser.add_argument("--tool-install-max-attempts", type=int, default=3)
    parser.add_argument(
        "--visual-repair-max-rounds",
        type=int,
        default=2,
        help="fresh repair generations after a valid visual report still has blocking findings",
    )
    parser.add_argument("--visual-repair-round", type=int, default=0, help=argparse.SUPPRESS)
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
    if args.tool_install_max_attempts < 1 or args.tool_install_max_attempts > 3:
        parser.error("--tool-install-max-attempts must be within 1..3")
    if args.visual_repair_max_rounds < 0 or args.visual_repair_max_rounds > 3:
        parser.error("--visual-repair-max-rounds must be within 0..3")
    if args.visual_repair_round < 0 or args.visual_repair_round > args.visual_repair_max_rounds:
        parser.error("--visual-repair-round must be within 0..visual-repair-max-rounds")
    if args.provider != "all" and args.model != "all" and args.model not in matrix.PROVIDERS[args.provider]:
        parser.error(f"--model {args.model} does not belong to provider {args.provider}")
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
    recorded_root = Path(contract["artifact_root"])
    artifact_root = (recorded_root if recorded_root.is_absolute() else ROOT / recorded_root).resolve()
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
        receipt = result.get("receipt")
        if not isinstance(receipt, dict):
            raise EvaluationError(f"generation target has no evaluator receipt: {target}")
        try:
            manifest = matrix.verified_existing(target, provider, model, str(case_id), expected_receipt=receipt)
        except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError) as error:
            raise EvaluationError(f"generation target provenance is invalid: {target}: {error}") from error
        if manifest is None:
            raise EvaluationError(f"generation target has no completed manifest: {target}")
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


def _portable_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return str(resolved)


def _recorded_path(value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise EvaluationError("evidence record has no path")
    path = Path(value)
    return (path if path.is_absolute() else ROOT / path).resolve()


def _generation_input_record(generation_output: Path) -> dict[str, str]:
    generation_output = generation_output.resolve()
    if not generation_output.is_file() or generation_output.is_symlink():
        raise EvaluationError(f"generation ledger is missing or unsafe: {generation_output}")
    return {"path": _portable_path(generation_output), "sha256": _digest(generation_output)}


def _target_input_records(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for target in targets:
        case_id = str(target["case_id"])
        directory = Path(target["directory"]).resolve()
        if not directory.is_dir() or directory.is_symlink():
            raise EvaluationError(f"visual target is missing or unsafe: {directory}")
        artifacts = []
        for name in ("DESIGN.md", *CASE_PAGES[case_id]):
            path = directory / name
            if not path.is_file() or path.is_symlink():
                raise EvaluationError(f"target input is missing or unsafe: {path}")
            artifacts.append({"path": name, "bytes": path.stat().st_size, "sha256": _digest(path)})
        records.append(
            {
                "caseId": case_id,
                "alias": str(target["alias"]),
                "target": _portable_path(directory),
                "artifacts": artifacts,
            }
        )
    return records


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    parent = path.parent
    if not parent.is_dir() or parent.is_symlink():
        raise EvaluationError(f"evidence output parent is unsafe: {parent}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def bind_visual_report(visual_output: Path, generation_output: Path, targets: list[dict[str, Any]]) -> None:
    report = _load_json(visual_output, "visual report")
    report["generation_ledger"] = _generation_input_record(generation_output)
    report["target_inputs"] = _target_input_records(targets)
    _atomic_write_json(visual_output, report)


def _validate_input_bindings(
    report: dict[str, Any],
    generation_output: Path,
    targets: list[dict[str, Any]],
) -> None:
    generation_record = report.get("generation_ledger")
    expected_generation = _generation_input_record(generation_output)
    if not isinstance(generation_record, dict):
        raise EvaluationError("evidence report has no generation-ledger binding")
    if _recorded_path(generation_record.get("path")) != _recorded_path(expected_generation["path"]):
        raise EvaluationError("evidence report generation-ledger path disagrees")
    if generation_record.get("sha256") != expected_generation["sha256"]:
        raise EvaluationError("evidence report generation-ledger hash disagrees")
    actual_inputs = report.get("target_inputs")
    expected_inputs = _target_input_records(targets)
    if not isinstance(actual_inputs, list) or len(actual_inputs) != len(expected_inputs):
        raise EvaluationError("evidence report target-input hashes disagree")
    for actual, expected in zip(actual_inputs, expected_inputs):
        if not isinstance(actual, dict):
            raise EvaluationError("evidence report target-input hashes disagree")
        actual_without_path = {key: value for key, value in actual.items() if key != "target"}
        expected_without_path = {key: value for key, value in expected.items() if key != "target"}
        if (
            actual_without_path != expected_without_path
            or _recorded_path(actual.get("target")) != _recorded_path(expected.get("target"))
        ):
            raise EvaluationError("evidence report target-input hashes disagree")


def _png_size(path: Path) -> tuple[int, int]:
    try:
        media_type, width, height = png_metadata(path.read_bytes())
    except (OSError, LedgerError) as error:
        raise EvaluationError(f"screenshot failed full PNG decode: {path}: {error}") from error
    if media_type != "image/png":
        raise EvaluationError(f"screenshot is not a PNG: {path}")
    return width, height


def _validate_font_evidence(result: dict[str, Any], key: tuple[object, ...]) -> None:
    evidence = result.get("fontEvidence")
    if not isinstance(evidence, dict) or evidence.get("status") != "captured":
        raise EvaluationError(f"font evidence is missing or incomplete: {key}")
    roles = evidence.get("roles")
    mismatches = evidence.get("primaryMismatches")
    if not isinstance(roles, list) or not roles or not isinstance(mismatches, list):
        raise EvaluationError(f"font evidence roles are missing or malformed: {key}")
    resolved_platform_role = False
    expected_mismatches = []
    for role in roles:
        if not isinstance(role, dict):
            raise EvaluationError(f"font evidence role is malformed: {key}")
        if any(not isinstance(role.get(field), str) or not role.get(field) for field in (
            "role", "selector", "declaredPrimary", "classification", "fontStretch", "fontStyle", "fontWeight",
        )):
            raise EvaluationError(f"font evidence role identity is malformed: {key}")
        if (
            role.get("source") not in {"dom-text", "native-control", "pseudo"}
            or not isinstance(role.get("pseudoDescendant"), bool)
            or type(role.get("textRunIndex")) is not int
            or role["textRunIndex"] < 0
            or type(role.get("textNodeCount")) is not int
            or role["textNodeCount"] <= 0
        ):
            raise EvaluationError(f"font evidence text-run identity is malformed: {key}")
        if role.get("classification") not in FONT_EVIDENCE_CLASSIFICATIONS:
            raise EvaluationError(f"font evidence classification is invalid: {key}")
        if (
            not isinstance(role.get("probeSourceTextEmpty"), bool)
            or not isinstance(role.get("declaredPrimaryQuoted"), bool)
            or not isinstance(role.get("pseudoTextMappingUnavailable"), bool)
            or not isinstance(role.get("renderedTextMappingUnavailable"), bool)
            or not isinstance(role.get("probeTextComplete"), bool)
            or not isinstance(role.get("probeHasLetterOrNumber"), bool)
            or not isinstance(role.get("probeHasRelevantGlyph"), bool)
            or not isinstance(role.get("probeRelevantGlyphOverflow"), bool)
            or not isinstance(role.get("fontPaintVisible"), bool)
            or not isinstance(role.get("fontPaintEvidenceReliable"), bool)
            or not isinstance(role.get("fontProbeStable"), bool)
            or not isinstance(role.get("fontInventoryStable"), bool)
            or not isinstance(role.get("platformFontsStable"), bool)
            or not isinstance(role.get("browserGeneratedTextUnavailable"), bool)
            or not isinstance(role.get("declaredFaceCheck"), bool)
            or not isinstance(role.get("declaredFaceCheckReliable"), bool)
            or not isinstance(role.get("declaredFaceSelectionFailed"), bool)
            or not isinstance(role.get("declaredFaceSelectionUnavailable"), bool)
        ):
            raise EvaluationError(f"font evidence browser checks are malformed: {key}")
        if (
            not role["fontPaintVisible"]
            or not role["fontPaintEvidenceReliable"]
            or not role["fontProbeStable"]
            or not role["fontInventoryStable"]
            or not role["platformFontsStable"]
        ):
            raise EvaluationError(f"font evidence stability checks did not pass: {key}")
        mapping_unavailable = (
            role["browserGeneratedTextUnavailable"]
            or role["renderedTextMappingUnavailable"]
            or role["pseudoTextMappingUnavailable"]
        )
        if mapping_unavailable and role.get("classification") != "not_applicable":
            raise EvaluationError(f"font evidence rendered-text mapping did not resolve: {key}")
        if role.get("classification") in {"evidence_unavailable", "platform_fonts_unavailable"}:
            raise EvaluationError(f"font evidence role did not resolve: {key}")
        actual_fonts = role.get("actualFonts")
        font_faces = role.get("fontFaces")
        if not isinstance(actual_fonts, list) or not isinstance(font_faces, list):
            raise EvaluationError(f"font evidence font inventory is malformed: {key}")
        probe_code_points = role.get("probeCodePoints")
        if (
            not isinstance(probe_code_points, list)
            or len(probe_code_points) > 2048
            or any(type(code_point) is not int or not 0 <= code_point <= 0x10FFFF for code_point in probe_code_points)
            or len(probe_code_points) != len(set(probe_code_points))
            or bool(probe_code_points) != role["probeHasRelevantGlyph"]
        ):
            raise EvaluationError(f"font evidence probe code points are malformed: {key}")
        for font in actual_fonts:
            if (
                not isinstance(font, dict)
                or not isinstance(font.get("familyName"), str)
                or not font["familyName"]
                or not isinstance(font.get("postScriptName"), str)
                or type(font.get("glyphCount")) is not int
                or font["glyphCount"] < 0
            ):
                raise EvaluationError(f"font evidence platform usage is malformed: {key}")
            if font["glyphCount"] > 0:
                resolved_platform_role = True
        for face in font_faces:
            if (
                not isinstance(face, dict)
                or any(not isinstance(face.get(field), str) or not face[field] for field in ("family", "status", "stretch", "style", "unicodeRange", "weight"))
                or face["status"] not in {"unloaded", "loading", "loaded", "error"}
            ):
                raise EvaluationError(f"font evidence font-face inventory is malformed: {key}")
        expected_selection_state = _expected_font_face_selection_state(role)
        if (
            role["declaredFaceSelectionFailed"] != (expected_selection_state == "failed")
            or role["declaredFaceSelectionUnavailable"] != (expected_selection_state == "unavailable")
        ):
            raise EvaluationError(f"font evidence face-selection state disagrees with classification: {key}")
        if role["classification"] != _classify_font_evidence_role(role):
            raise EvaluationError(f"font evidence classification disagrees with its evidence: {key}")
        if role.get("classification") == "failed_font_face":
            expected_mismatches.append(role)
    if not resolved_platform_role:
        raise EvaluationError(f"font evidence has no resolved platform-font role: {key}")
    if mismatches != expected_mismatches:
        raise EvaluationError(f"font evidence mismatch inventory disagrees: {key}")
    visual_issues = result.get("visualIssues")
    if not isinstance(visual_issues, list) or any(not isinstance(issue, str) or not issue for issue in visual_issues):
        raise EvaluationError(f"font evidence visual-issue inventory is malformed: {key}")
    has_font_issue = "declared_primary_font_not_rendered" in visual_issues
    if has_font_issue != bool(mismatches):
        raise EvaluationError(f"font evidence mismatch and visual issue disagree: {key}")


def validate_visual_completion(
    visual_output: Path,
    screenshot_dir: Path,
    targets: list[dict[str, Any]],
    generation_output: Path,
) -> int:
    report = _load_json(visual_output, "visual report")
    _validate_input_bindings(report, generation_output, targets)
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
        (target["case_id"], target["alias"], page, "base", viewport)
        for target in targets
        for page in CASE_PAGES[target["case_id"]]
        for viewport in VIEWPORTS
    }
    expected.update(
        {
            (target["case_id"], target["alias"], CASE_PAGES[target["case_id"]][0], "interaction", viewport)
            for target in targets
            for viewport in ("desktop", "mobile")
        }
    )
    results = report.get("results")
    if not isinstance(results, list) or len(results) != len(expected):
        raise EvaluationError(f"visual result count must be {len(expected)}")
    root = screenshot_dir.resolve()
    seen: set[tuple[str, str, str, str, str]] = set()
    screenshot_paths: set[Path] = set()
    for result in results:
        if not isinstance(result, dict):
            raise EvaluationError("visual result is malformed")
        key = (
            result.get("caseId"),
            result.get("alias"),
            result.get("page"),
            result.get("state"),
            result.get("viewport"),
        )
        if key in seen or key not in expected:
            raise EvaluationError(f"visual result identity is invalid: {key}")
        seen.add(key)  # type: ignore[arg-type]
        _validate_font_evidence(result, key)
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
        profile = VIEWPORTS[str(key[4])]
        width = int(profile["width"])
        height = int(profile["height"])
        scale = int(profile["deviceScaleFactor"])
        if _png_size(screenshot) != (width * scale, height * scale) or result.get("size") != f"{width}x{height}":
            raise EvaluationError(f"screenshot dimensions disagree: {key}")
        if result.get("screenshotSha256") != _digest(screenshot):
            raise EvaluationError(f"screenshot hash disagrees: {key}")
        if screenshot in screenshot_paths:
            raise EvaluationError(f"visual results reuse one screenshot across identities: {screenshot}")
        screenshot_paths.add(screenshot)
    if seen != expected or len(screenshot_paths) != len(expected):
        raise EvaluationError("visual screenshot inventory is incomplete")
    actual_pngs = {path.resolve() for path in screenshot_dir.glob("*.png") if path.is_file() and not path.is_symlink()}
    if actual_pngs != screenshot_paths:
        raise EvaluationError("screenshot directory contains missing or extra PNG files")
    summary = report.get("summary")
    if not isinstance(summary, dict) or summary.get("checkedPages") != len(expected):
        raise EvaluationError("visual report summary is incomplete")
    return len(expected)


def validate_design_completion(
    design_output: Path,
    targets: list[dict[str, Any]],
    generation_output: Path,
) -> tuple[int, int]:
    report = _load_json(design_output, "DESIGN.md lint report")
    generation_record = report.get("generation_ledger")
    expected_generation = _generation_input_record(generation_output)
    if not isinstance(generation_record, dict):
        raise EvaluationError("DESIGN.md report has no generation-ledger binding")
    if _recorded_path(generation_record.get("path")) != _recorded_path(expected_generation["path"]):
        raise EvaluationError("DESIGN.md report generation-ledger path disagrees")
    if generation_record.get("sha256") != expected_generation["sha256"]:
        raise EvaluationError("DESIGN.md report generation-ledger hash disagrees")
    if report.get("linter") != {"package": "@google/design.md", "version": DESIGN_MD_VERSION}:
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
        target = next(
            target
            for target in targets
            if (target["alias"].split("-", 1)[0], target["alias"].split("-", 1)[1], target["case_id"]) == key
        )
        design = Path(target["directory"]).resolve() / "DESIGN.md"
        if not design.is_file() or design.is_symlink():
            raise EvaluationError(f"DESIGN.md input is missing or unsafe for {key}")
        if _recorded_path(result.get("path")) != design or result.get("sha256") != _digest(design):
            raise EvaluationError(f"DESIGN.md input hash disagrees for {key}")
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
        raise DesignFindingsError(f"DESIGN.md repair required for {findings} target(s)")
    return clean, findings


def blocking_visual_findings(visual_output: Path) -> dict[str, list[str]]:
    report = _load_json(visual_output, "visual report")
    by_target: dict[str, set[str]] = {}
    advisories_from_results: dict[str, list[dict[str, Any]]] = {}
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
            if collection_name == "results":
                layout_flow = result.get("layoutFlow")
                raw_advisories = layout_flow.get("unfilledColumnAdvisories", []) if isinstance(layout_flow, dict) else []
                if not isinstance(raw_advisories, list):
                    raise EvaluationError("visual report result advisory inventory is malformed")
                if raw_advisories:
                    key = f"{result.get('caseId')}:{result.get('alias')}"
                    enriched = []
                    for advisory in raw_advisories:
                        if not isinstance(advisory, dict):
                            raise EvaluationError("visual report result advisory evidence is malformed")
                        enriched.append({
                            **advisory,
                            "page": result.get("page"),
                            "state": result.get("state"),
                            "viewport": result.get("viewport"),
                            "screenshot": result.get("screenshot"),
                        })
                    advisories_from_results.setdefault(key, []).extend(enriched)
    normalized = {key: sorted(issues) for key, issues in sorted(by_target.items())}
    summary = report.get("summary")
    if not isinstance(summary, dict):
        raise EvaluationError("visual report summary is malformed")
    advisory_fields_present = any(field in summary for field in ("advisoryCount", "targetsWithAdvisories", "advisoriesByTarget"))
    advisory_count = summary.get("advisoryCount", 0)
    targets_with_advisories = summary.get("targetsWithAdvisories", 0)
    advisories_by_target = summary.get("advisoriesByTarget", {})
    if (
        type(advisory_count) is not int
        or advisory_count < 0
        or type(targets_with_advisories) is not int
        or targets_with_advisories < 0
        or not isinstance(advisories_by_target, dict)
    ):
        raise EvaluationError("visual report advisory summary is malformed")
    actual_advisory_count = 0
    for target, advisories in advisories_by_target.items():
        if not isinstance(target, str) or not isinstance(advisories, list):
            raise EvaluationError("visual report advisory inventory is malformed")
        for advisory in advisories:
            if not isinstance(advisory, dict) or any(
                not isinstance(advisory.get(field), str) or not advisory[field]
                for field in ("page", "state", "viewport", "screenshot", "confidence")
            ):
                raise EvaluationError("visual report advisory evidence is malformed")
        actual_advisory_count += len(advisories)
    if actual_advisory_count != advisory_count:
        raise EvaluationError("visual report advisory count disagrees")
    if advisories_from_results != advisories_by_target:
        raise EvaluationError("visual report advisory evidence disagrees with results")
    if len(advisories_from_results) != targets_with_advisories:
        raise EvaluationError("visual report advisory target count disagrees")
    if advisory_fields_present and not advisories_from_results and (advisory_count or targets_with_advisories or advisories_by_target):
        raise EvaluationError("visual report zero-advisory summary is malformed")
    expected_verdict = "observed_issues" if normalized else (
        "advisories_present" if advisory_count else "no_observed_issues"
    )
    if summary.get("verdict") != expected_verdict:
        raise EvaluationError("visual report verdict disagrees with blocking issues")
    return normalized


def repair_summary(findings: dict[str, list[str]]) -> str:
    return "; ".join(f"{target}={','.join(codes)}" for target, codes in findings.items())


def visual_advisory_count(visual_output: Path) -> int:
    blocking_visual_findings(visual_output)
    report = _load_json(visual_output, "visual report")
    summary = report.get("summary")
    count = summary.get("advisoryCount", 0) if isinstance(summary, dict) else None
    if type(count) is not int or count < 0:
        raise EvaluationError("visual report advisory count is malformed")
    return count


def _archive_failed_path(path: Path, attempt: int) -> Path:
    destination = path.with_name(f"{path.name}.failed-attempt-{attempt}")
    if destination.exists():
        raise EvaluationError(f"refusing to overwrite failed-attempt evidence: {destination}")
    path.rename(destination)
    return destination


def _archive_visual_repair_state(paths: list[Path], attempt: int) -> dict[Path, Path]:
    if not paths or len(set(paths)) != len(paths):
        raise EvaluationError("visual repair archive paths are empty or duplicated")
    plan = {path: path.with_name(f"{path.name}.failed-attempt-{attempt}") for path in paths}
    for source, destination in plan.items():
        if not source.exists() or source.is_symlink():
            raise EvaluationError(f"visual repair source is missing or unsafe: {source}")
        if destination.exists() or destination.is_symlink():
            raise EvaluationError(f"refusing to overwrite visual repair evidence: {destination}")
    moved: list[tuple[Path, Path]] = []
    try:
        for source, destination in plan.items():
            source.rename(destination)
            moved.append((source, destination))
    except OSError as error:
        rollback_errors: list[str] = []
        for source, destination in reversed(moved):
            try:
                destination.rename(source)
            except OSError as rollback_error:
                rollback_errors.append(f"{source}: {rollback_error}")
        if rollback_errors:
            raise EvaluationError(
                f"visual repair archive failed and rollback was incomplete: {'; '.join(rollback_errors)}"
            ) from error
        raise EvaluationError(f"visual repair archive failed and was rolled back: {error}") from error
    return plan


def _visual_repair_command(args: argparse.Namespace, next_round: int) -> list[str]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--provider",
        args.provider,
        "--model",
        args.model,
        "--theme",
        args.theme,
        "--target-root",
        str(args.target_root),
        "--generation-output",
        str(args.generation_output),
        "--design-output",
        str(args.design_output),
        "--visual-output",
        str(args.visual_output),
        "--screenshot-dir",
        str(args.screenshot_dir),
        "--timeout-seconds",
        str(args.timeout_seconds),
        "--max-attempts",
        str(args.max_attempts),
        "--retry-delay-seconds",
        str(args.retry_delay_seconds),
        "--capture-max-attempts",
        str(args.capture_max_attempts),
        "--capture-timeout-seconds",
        str(args.capture_timeout_seconds),
        "--lint-max-attempts",
        str(args.lint_max_attempts),
        "--lint-timeout-seconds",
        str(args.lint_timeout_seconds),
        "--tool-install-max-attempts",
        str(args.tool_install_max_attempts),
        "--visual-repair-max-rounds",
        str(args.visual_repair_max_rounds),
        "--visual-repair-round",
        str(next_round),
        "--resume",
    ]
    if args.chrome_executable is not None:
        command.extend(["--chrome-executable", str(args.chrome_executable)])
    return command


def _one_line(value: object, limit: int = 72) -> str:
    printable = "".join(character if character.isprintable() else " " for character in str(value))
    text = " ".join(printable.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _visual_issue_label(code: str) -> str:
    if code.startswith("interaction_exception:"):
        return "interaction_exception"
    return _one_line(code, 96)


def _visual_issue_detail(result: dict[str, Any], code: str) -> str:
    location = "/".join(
        _one_line(result.get(field, "?"), 32) for field in ("page", "viewport", "state")
    )
    if code.startswith("interaction_exception:"):
        diagnostic = code.split(":", 1)[1]
        return f"interaction_exception@{location} error={_one_line(diagnostic, 112)!r}"
    if code == "prose_track_underfilled":
        blocks = result.get("bodyFlow", {}).get("underfilledProseBlocks", [])
        if isinstance(blocks, list) and blocks and isinstance(blocks[0], dict):
            block = blocks[0]
            return (
                f"{code}@{location} text={_one_line(block.get('text', ''), 56)!r} "
                f"trackRatio={block.get('trackRatio')} unusedInline={block.get('unusedInline')}"
            )
    if code == "paragraph_measure_too_wide":
        items = result.get("readingRhythm", {}).get("tooWide", [])
        if isinstance(items, list) and items and isinstance(items[0], dict):
            item = items[0]
            return (
                f"{code}@{location} text={_one_line(item.get('text', ''), 56)!r} "
                f"script={item.get('script')} estimatedCharacters={item.get('estimatedCharacters')} "
                f"limit={item.get('limit')} Action: narrow only this text element's inline measure "
                f"to at most {item.get('limit')} estimated characters; do not shorten its copy or change unrelated prose."
            )
    if code == "readable_text_below_12px":
        items = result.get("textScale", {}).get("undersizedReadableText", [])
        if isinstance(items, list) and items and isinstance(items[0], dict):
            item = items[0]
            return (
                f"{code}@{location} text={_one_line(item.get('text', ''), 56)!r} "
                f"fontSize={item.get('fontSize')} hook={_one_line(item.get('hook', ''), 40)!r}"
            )
    if code in {"wide_heading_track_underfilled", "cjk_heading_overcompressed", "cjk_heading_orphan_line"}:
        key = {
            "wide_heading_track_underfilled": "underfilledWideHeadings",
            "cjk_heading_overcompressed": "compressedCjkHeadings",
            "cjk_heading_orphan_line": "orphanedCjkHeadingLines",
        }[code]
        headings = result.get("headingFlow", {}).get(key, [])
        if isinstance(headings, list) and headings and isinstance(headings[0], dict):
            heading = headings[0]
            metrics = " ".join(
                f"{field}={heading[field]}"
                for field in (
                    "lineCount",
                    "lastLineText",
                    "lastLineWidthInEms",
                    "longestLineRatio",
                    "widthInEms",
                    "parentSpareInEms",
                )
                if field in heading
            )
            return f"{code}@{location} text={_one_line(heading.get('text', ''), 56)!r} {metrics}".rstrip()
    if code == "fixed_or_sticky_content_obstruction":
        obstructions = result.get("fixedStickyObstructions", [])
        if isinstance(obstructions, list) and obstructions and isinstance(obstructions[0], dict):
            obstruction = obstructions[0]
            overlaps = obstruction.get("overlaps", [])
            overlap_text = ""
            if isinstance(overlaps, list) and overlaps and isinstance(overlaps[0], dict):
                overlap_text = _one_line(overlaps[0].get("text", ""), 56)
            return f"{code}@{location} position={obstruction.get('position')} overlaps={overlap_text!r}"
    if code == "layout_column_void":
        voids = result.get("layoutFlow", {}).get("unfilledColumnVoids", [])
        if isinstance(voids, list) and voids and isinstance(voids[0], dict):
            void = voids[0]
            return (
                f"{code}@{location} target={_one_line(void.get('target', ''), 56)!r} "
                f"voidHeight={void.get('voidHeight')} threshold={void.get('threshold')} "
                f"parentDisplay={void.get('parentDisplay')} parentWidth={void.get('parentWidth')}"
            )
    if code == "zh_hant_untranslated_interface_copy":
        copies = result.get("localeFlow", {}).get("untranslatedInterfaceCopy", [])
        if isinstance(copies, list) and copies and isinstance(copies[0], dict):
            return f"{code}@{location} text={_one_line(copies[0].get('text', ''), 72)!r}"
    if code == "declared_primary_font_not_rendered":
        mismatches = result.get("fontEvidence", {}).get("primaryMismatches", [])
        if isinstance(mismatches, list) and mismatches and isinstance(mismatches[0], dict):
            mismatch = mismatches[0]
            actual_fonts = mismatch.get("actualFonts", [])
            actual = []
            if isinstance(actual_fonts, list):
                for font in actual_fonts[:3]:
                    if isinstance(font, dict):
                        actual.append(
                            f"{_one_line(font.get('familyName', '?'), 28)}/{_one_line(font.get('postScriptName', '?'), 28)}"
                        )
            return (
                f"{code}@{location} role={_one_line(mismatch.get('role', ''), 24)!r} "
                f"selector={_one_line(mismatch.get('selector', ''), 40)!r} "
                f"text={_one_line(mismatch.get('text', ''), 36)!r} "
                f"declaredPrimary={_one_line(mismatch.get('declaredPrimary', ''), 32)!r} "
                f"actual={_one_line(','.join(actual), 64)!r} Action: fix this local @font-face source, "
                "or change only this role's primary token to the verified face; keep fallbacks and copy unchanged."
            )
    return f"{_visual_issue_label(code)}@{location}"


def visual_repair_feedback(findings: dict[str, list[str]], visual_output: Path | None = None) -> dict[str, str]:
    issues_by_case: dict[str, set[str]] = {}
    for target, codes in findings.items():
        case_id = target.split(":", 1)[0]
        issues_by_case.setdefault(case_id, set()).update(codes)
    details_by_case: dict[str, list[str]] = {case_id: [] for case_id in issues_by_case}
    if visual_output is not None:
        report = _load_json(visual_output, "visual report")
        for collection_name in ("results", "crossPageComparisons"):
            collection = report.get(collection_name, [])
            if not isinstance(collection, list):
                raise EvaluationError(f"visual report {collection_name} is malformed")
            for result in collection:
                if not isinstance(result, dict):
                    continue
                case_id = result.get("caseId")
                issues = result.get("visualIssues")
                if case_id not in issues_by_case or not isinstance(issues, list):
                    continue
                for code in sorted(issues_by_case[case_id].intersection(issue for issue in issues if isinstance(issue, str))):
                    detail = _visual_issue_detail(result, code)
                    if detail not in details_by_case[case_id]:
                        details_by_case[case_id].append(detail)

    feedback: dict[str, str] = {}
    suffix = " Preserve passed behavior/direction; do not edit or weaken the evaluator."
    for case_id, codes in sorted(issues_by_case.items()):
        labels = sorted({_visual_issue_label(code) for code in codes})
        message = "REPAIR REQUIRED: " + _one_line(",".join(labels), 192) + "."
        for index, detail in enumerate(details_by_case[case_id]):
            separator = " Evidence: " if index == 0 else "; "
            if len(message) + len(separator) + len(detail) + len(suffix) > 500:
                break
            message += separator + detail
        feedback[case_id] = message + suffix
    return feedback


def _prepare_selective_repair_state(
    archived_target_root: Path,
    archived_generation_output: Path,
    target_root: Path,
    generation_output: Path,
    findings: dict[str, list[str]],
) -> int:
    ledger = _load_json(archived_generation_output, "archived generation ledger")
    contract = ledger.get("contract")
    selection = ledger.get("selection")
    results = ledger.get("results")
    if (
        ledger.get("status") != "completed"
        or not isinstance(contract, dict)
        or not isinstance(selection, dict)
        or not isinstance(results, list)
        or selection.get("count") != len(results)
    ):
        raise EvaluationError("archived generation ledger is incomplete or malformed")
    recorded_root = contract.get("artifact_root")
    if not isinstance(recorded_root, str):
        raise EvaluationError("archived generation artifact root disagrees with repair target root")
    recorded_root_path = Path(recorded_root)
    resolved_recorded_root = (
        recorded_root_path if recorded_root_path.is_absolute() else ROOT / recorded_root_path
    ).resolve()
    if resolved_recorded_root != target_root.resolve():
        raise EvaluationError("archived generation artifact root disagrees with repair target root")
    if target_root.exists() or generation_output.exists():
        raise EvaluationError("selective repair outputs already exist")
    target_root.mkdir(parents=True, mode=0o755)
    preserved: list[dict[str, Any]] = []
    for raw_result in results:
        if not isinstance(raw_result, dict):
            raise EvaluationError("archived generation result is malformed")
        provider = raw_result.get("provider")
        model = raw_result.get("model")
        case_id = raw_result.get("case_id")
        if provider not in {"claude", "codex"} or not isinstance(model, str) or case_id not in CASE_PAGES:
            raise EvaluationError("archived generation result identity is malformed")
        key = f"{case_id}:{provider}-{model}"
        if key in findings:
            continue
        target_value = raw_result.get("target")
        receipt = raw_result.get("receipt")
        if not isinstance(target_value, str) or not isinstance(receipt, dict):
            raise EvaluationError("archived generation result has no target receipt")
        recorded_target = (Path(target_value) if Path(target_value).is_absolute() else ROOT / target_value).resolve()
        if recorded_target.parent != target_root.resolve():
            raise EvaluationError("archived generation target escapes repair target root")
        source = archived_target_root / recorded_target.name
        destination = target_root / recorded_target.name
        if not source.is_dir() or source.is_symlink() or any(path.is_symlink() for path in source.rglob("*")):
            raise EvaluationError(f"preserved repair target is missing or unsafe: {source}")
        shutil.copytree(source, destination, copy_function=shutil.copy2)
        try:
            manifest = matrix.verified_existing(
                destination,
                str(provider),
                model,
                str(case_id),
                expected_receipt=receipt,
            )
        except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError) as error:
            raise EvaluationError(f"preserved repair target provenance is invalid: {destination}: {error}") from error
        copied = dict(raw_result)
        copied["status"] = "existing_completed"
        copied["receipt"] = matrix._manifest_receipt(destination, manifest)
        preserved.append(copied)
    ledger["status"] = "partial"
    ledger["finished_at"] = None
    ledger["results"] = preserved
    ledger.pop("summary", None)
    _atomic_write_json(generation_output, ledger)
    return len(preserved)


def _run_visual_repair(
    args: argparse.Namespace,
    findings: dict[str, list[str]],
    generation_output: Path,
    design_output: Path,
    visual_output: Path,
    screenshot_dir: Path,
    target_root: Path,
) -> int:
    if args.visual_repair_round >= args.visual_repair_max_rounds:
        print(
            f"visual repair fuse reached after {args.visual_repair_round + 1} evaluated generation(s); "
            f"best artifacts and findings were preserved: {repair_summary(findings)}",
            file=sys.stderr,
        )
        return 1
    next_round = args.visual_repair_round + 1
    feedback_by_case = visual_repair_feedback(findings, visual_output)
    archived = _archive_visual_repair_state(
        [target_root, generation_output, design_output, visual_output, screenshot_dir],
        next_round,
    )
    source_root = archived[target_root]
    preserved_count = _prepare_selective_repair_state(
        source_root,
        archived[generation_output],
        target_root,
        generation_output,
        findings,
    )
    environment = os.environ.copy()
    environment["PRODUCT_FLOW_REPAIR_SOURCE_ROOT"] = str(source_root)
    environment.pop("PRODUCT_FLOW_RETRY_FEEDBACK", None)
    environment["PRODUCT_FLOW_RETRY_FEEDBACK_BY_CASE"] = json.dumps(
        feedback_by_case,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    environment["PRODUCT_FLOW_VISUAL_REPAIR_ROUND"] = str(next_round)
    command = _visual_repair_command(args, next_round)
    print(
        f"starting visual repair round {next_round}/{args.visual_repair_max_rounds}; "
        f"preserved {preserved_count} passing target(s); prior targets and evidence archived at {source_root}",
        flush=True,
    )
    process = subprocess.Popen(command, cwd=ROOT, env=environment, start_new_session=True)
    try:
        return process.wait()
    except BaseException:
        matrix.terminate_process_group(process)
        raise


def _run_generation(args: argparse.Namespace, output: Path) -> int:
    command = [
        sys.executable,
        str(MATRIX_RUNNER),
        "--provider",
        args.provider,
        "--model",
        args.model,
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


def _safe_tool_root(args: argparse.Namespace) -> Path:
    root = args.target_root.expanduser().resolve() / ".tools"
    if root.exists() and (root.is_symlink() or not root.is_dir()):
        raise EvaluationError(f"tool cache is unsafe: {root}")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_tool_record(root: Path, record: dict[str, Any]) -> None:
    _atomic_write_json(root / "tool-resolution.json", record)


def _probe_playwright(environment: dict[str, str], package_root: Path) -> dict[str, str]:
    module_root = package_root / "node_modules" / "playwright"
    package_json = module_root / "package.json"
    if module_root.is_symlink() or not module_root.is_dir() or package_json.is_symlink() or not package_json.is_file():
        raise EvaluationError("integrity-installed Playwright package is missing or unsafe")
    try:
        package_record = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EvaluationError(f"cannot read integrity-installed Playwright package: {error}") from error
    if package_record.get("version") != PLAYWRIGHT_VERSION:
        raise EvaluationError(
            f"Playwright version mismatch: expected {PLAYWRIGHT_VERSION}, got {package_record.get('version')}"
        )
    node = shutil.which("node", path=environment.get("PATH"))
    if node is None:
        raise EvaluationError("Node.js is unavailable for the pinned Playwright probe")
    completed = subprocess.run(
        [
            node,
            "-e",
            (
                "const root=process.argv[1];"
                "const p=require(root);"
                "const v=require(root + '/package.json').version;"
                "process.stdout.write(JSON.stringify({version:v,executable:p.chromium.executablePath()}));"
            ),
            str(module_root),
        ],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        diagnostic = " ".join((completed.stderr or completed.stdout or "Playwright probe failed").split())[:500]
        raise EvaluationError(diagnostic)
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise EvaluationError("Playwright probe returned invalid JSON") from error
    if value.get("version") != PLAYWRIGHT_VERSION or not isinstance(value.get("executable"), str):
        raise EvaluationError(
            f"Playwright version mismatch: expected {PLAYWRIGHT_VERSION}, got {value.get('version')}"
        )
    return {"version": value["version"], "executable": value["executable"]}


def _install_tool_with_retries(
    args: argparse.Namespace,
    command: list[str],
    environment: dict[str, str],
    label: str,
) -> list[dict[str, Any]]:
    attempts: list[dict[str, Any]] = []
    for attempt in range(1, args.tool_install_max_attempts + 1):
        try:
            completed = matrix.run_isolated(
                command,
                min(max(args.capture_timeout_seconds, 300), 900),
                hard_timeout_seconds=1800,
                environment=environment,
            )
            diagnostic = " ".join((completed.stderr or completed.stdout or "").split())[:500]
            attempts.append({"attempt": attempt, "exit_code": completed.returncode, "diagnostic": diagnostic})
            if completed.returncode == 0:
                return attempts
        except subprocess.TimeoutExpired as error:
            attempts.append({"attempt": attempt, "exit_code": None, "diagnostic": str(error)[:500]})
        if attempt < args.tool_install_max_attempts and args.retry_delay_seconds:
            time.sleep(args.retry_delay_seconds)
    raise EvaluationError(f"{label} installation failed after {len(attempts)} attempt(s): {attempts[-1]['diagnostic']}")


def resolve_visual_tools(args: argparse.Namespace) -> dict[str, str]:
    tool_root = _safe_tool_root(args)
    environment = os.environ.copy()
    browsers_root = tool_root / "browsers"
    if browsers_root.exists() and (browsers_root.is_symlink() or not browsers_root.is_dir()):
        raise EvaluationError(f"browser cache is unsafe: {browsers_root}")
    browsers_root.mkdir(exist_ok=True)
    environment["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_root)
    record: dict[str, Any] = {
        "schema_version": 1,
        "playwright": {
            "requested_version": PLAYWRIGHT_VERSION,
            "install_scope": "fresh_evaluator_cache",
            "lock": dict(PLAYWRIGHT_LOCK),
            "package_lock_sha256": _digest(ROOT / "package-lock.json"),
        },
    }
    npm = shutil.which("npm")
    if npm is None:
        raise EvaluationError("npm is unavailable for integrity-bound Playwright installation")
    package_cache = Path(tempfile.mkdtemp(prefix=f"playwright-{PLAYWRIGHT_VERSION}-", dir=tool_root))
    for name in ("package.json", "package-lock.json"):
        source = ROOT / name
        destination = package_cache / name
        if source.is_symlink() or not source.is_file():
            raise EvaluationError(f"locked install input is missing or unsafe: {source}")
        shutil.copyfile(source, destination)
        os.chmod(destination, 0o600)
    environment["NODE_PATH"] = str(package_cache / "node_modules")
    attempts = _install_tool_with_retries(
        args,
        [
            npm,
            "ci",
            "--prefix",
            str(package_cache),
            "--ignore-scripts",
            "--no-audit",
            "--no-fund",
        ],
        environment,
        "Playwright package",
    )
    probe = _probe_playwright(environment, package_cache)
    record["playwright"].update(
        {
            "source": "installed_from_repository_lock",
            "version": probe["version"],
            "attempts": attempts,
        }
    )

    if args.chrome_executable is not None:
        chrome = args.chrome_executable.expanduser().resolve()
        if not chrome.is_file() or chrome.is_symlink():
            raise EvaluationError(f"Chrome executable is missing or unsafe: {chrome}")
        record["browser"] = {"source": "provided", "executable": str(chrome)}
        _write_tool_record(tool_root, record)
        return environment

    executable = Path(probe["executable"])
    if not executable.is_file():
        probe = _probe_playwright(environment, package_cache)
        executable = Path(probe["executable"])
        cli = package_cache / "node_modules" / "playwright" / "cli.js"
        if not cli.is_file() or cli.is_symlink():
            raise EvaluationError("pinned Playwright CLI is missing or unsafe")
        node = shutil.which("node")
        if node is None:
            raise EvaluationError("Node.js is unavailable for the pinned Playwright CLI")
        attempts = _install_tool_with_retries(
            args,
            [node, str(cli), "install", "chromium"],
            environment,
            "Chromium",
        )
        probe = _probe_playwright(environment, package_cache)
        executable = Path(probe["executable"])
        record["browser"] = {"source": "installed", "executable": str(executable), "attempts": attempts}
    else:
        record["browser"] = {"source": "existing", "executable": str(executable)}
    if not executable.is_file() or executable.is_symlink():
        raise EvaluationError("resolved Chromium executable is missing or unsafe")
    _write_tool_record(tool_root, record)
    return environment


def _run_design_attempt(args: argparse.Namespace, generation_output: Path, design_output: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["npm_config_cache"] = str(_safe_tool_root(args) / "npm-cache")
    environment["npm_config_ignore_scripts"] = "true"
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
        environment=environment,
    )


def _run_visual_attempt(
    args: argparse.Namespace,
    targets: list[dict[str, Any]],
    bases: list[str],
    visual_output: Path,
    screenshot_dir: Path,
    tool_environment: dict[str, str] | None = None,
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
    environment = dict(tool_environment or os.environ)
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
        print(
            "product-flow generation incomplete after retries; completed artifacts and attempt history were preserved, "
            "then rerun with --resume after resolving the recorded diagnostic",
            file=sys.stderr,
        )
        return 1
    try:
        targets = completed_targets(generation_output)
        design_complete = False
        if design_output.exists():
            if not args.resume:
                raise EvaluationError(f"refusing to overwrite DESIGN.md report: {design_output}")
            try:
                clean, findings = validate_design_completion(design_output, targets, generation_output)
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
                        clean, findings = validate_design_completion(design_output, targets, generation_output)
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
            count = validate_visual_completion(visual_output, screenshot_dir, targets, generation_output)
            blockers = blocking_visual_findings(visual_output)
            if blockers:
                print(
                    f"product-flow benchmark complete: {len(targets)} targets and {count} screenshots retained; "
                    f"repair required for {len(blockers)} target(s): {repair_summary(blockers)}",
                    file=sys.stderr,
                )
                return _run_visual_repair(
                    args,
                    blockers,
                    generation_output,
                    design_output,
                    visual_output,
                    screenshot_dir,
                    target_root,
                )
            advisory_count = visual_advisory_count(visual_output)
            if advisory_count:
                print(
                    f"product-flow execution complete with {advisory_count} advisory finding(s): "
                    f"{len(targets)} targets and {count} screenshots retained; no clean acceptance claim",
                    file=sys.stderr,
                )
            else:
                print(f"product-flow execution complete and acceptance passed: {len(targets)} targets and {count} screenshots retained")
            return 0
        tool_environment = resolve_visual_tools(args)
        with serve_targets(targets) as bases:
            for attempt in range(1, args.capture_max_attempts + 1):
                try:
                    completed = _run_visual_attempt(
                        args,
                        targets,
                        bases,
                        visual_output,
                        screenshot_dir,
                        tool_environment,
                    )
                except subprocess.TimeoutExpired as error:
                    completed = subprocess.CompletedProcess([], 124, "", f"timed out: {error}")
                if completed.returncode == 0:
                    try:
                        bind_visual_report(visual_output, generation_output, targets)
                        count = validate_visual_completion(visual_output, screenshot_dir, targets, generation_output)
                    except EvaluationError as error:
                        completed = subprocess.CompletedProcess(completed.args, 1, completed.stdout, str(error))
                    else:
                        blockers = blocking_visual_findings(visual_output)
                        if blockers:
                            print(
                                f"product-flow benchmark complete: {len(targets)} targets and {count} screenshots captured; "
                                f"repair required for {len(blockers)} target(s): {repair_summary(blockers)}",
                                file=sys.stderr,
                            )
                            return _run_visual_repair(
                                args,
                                blockers,
                                generation_output,
                                design_output,
                                visual_output,
                                screenshot_dir,
                                target_root,
                            )
                        advisory_count = visual_advisory_count(visual_output)
                        if advisory_count:
                            print(
                                f"product-flow execution complete with {advisory_count} advisory finding(s): "
                                f"{len(targets)} targets and {count} screenshots captured; no clean acceptance claim",
                                file=sys.stderr,
                            )
                        else:
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
