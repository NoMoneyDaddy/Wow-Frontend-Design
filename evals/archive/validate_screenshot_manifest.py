#!/usr/bin/env python3
"""Validate release screenshot hashes, source binding, paths, and full PNG decode."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

SCRIPT_RUNTIME = Path(__file__).resolve().parents[2] / "wow-frontend-design" / "scripts"
sys.path.insert(0, str(SCRIPT_RUNTIME))

from evidence_ledger import LedgerError, png_metadata


SHA256 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_CAPTURES = {
    "assets/showcase-desktop.png",
    "assets/showcase-desktop-dark.png",
    "assets/showcase-mobile.png",
    "assets/showcase-mobile-dark.png",
}


class ScreenshotManifestError(ValueError):
    """Raised when release screenshot provenance is incomplete or stale."""


def _checked_path(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ScreenshotManifestError(f"{label}.path must be a non-empty string")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or ".." in candidate.parts or "\x00" in value:
        raise ScreenshotManifestError(f"{label}.path is unsafe")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ScreenshotManifestError(f"{label}.path escapes repository root") from error
    if not resolved.is_file() or resolved.is_symlink():
        raise ScreenshotManifestError(f"{label}.path is missing or a symlink")
    return resolved


def _verify_artifact(root: Path, item: Any, label: str) -> Path:
    if not isinstance(item, dict) or not isinstance(item.get("sha256"), str) or SHA256.fullmatch(item["sha256"]) is None:
        raise ScreenshotManifestError(f"{label} must contain path and lowercase SHA-256")
    resolved = _checked_path(root, item.get("path"), label)
    actual = hashlib.sha256(resolved.read_bytes()).hexdigest()
    if actual != item["sha256"]:
        raise ScreenshotManifestError(f"{label}.sha256 is stale")
    return resolved


def validate(manifest_path: Path, repository_root: Path) -> int:
    if manifest_path.is_symlink():
        raise ScreenshotManifestError("manifest must not be a symlink")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ScreenshotManifestError(f"cannot read valid manifest JSON: {error}") from error
    if not isinstance(data, dict) or data.get("schema_version") != 2:
        raise ScreenshotManifestError("manifest schema_version must equal 2")
    if data.get("repository_commit") is not None:
        commit = data["repository_commit"]
        if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
            raise ScreenshotManifestError("repository_commit must be null or a full commit SHA")
    for field in ("source_binding", "capture_command", "claim_boundary"):
        if not isinstance(data.get(field), str) or len(data[field].strip()) < 20:
            raise ScreenshotManifestError(f"{field} must state a usable evidence boundary")
    if data.get("repository_commit") is None:
        binding = data["source_binding"].casefold()
        required_terms = ("commit-independent", "source", "capture-script", "dependency-lock", "hash")
        if any(term not in binding for term in required_terms):
            raise ScreenshotManifestError(
                "a null repository_commit requires an explicit commit-independent hash boundary"
            )
    environment = data.get("environment")
    required_environment = {
        "os", "browser", "automation", "headless", "browser_executable", "locale", "timezone",
        "color_profile", "reduced_motion", "network", "wait_condition", "screenshot_options",
    }
    if not isinstance(environment, dict) or set(environment) != required_environment:
        raise ScreenshotManifestError("environment fields are incomplete or unexpected")

    root = repository_root.resolve()
    _verify_artifact(root, data.get("capture_script"), "capture_script")
    _verify_artifact(root, data.get("dependency_lock"), "dependency_lock")
    source_files = data.get("source_files")
    if not isinstance(source_files, list) or not source_files:
        raise ScreenshotManifestError("source_files must be non-empty")
    for index, source in enumerate(source_files):
        _verify_artifact(root, source, f"source_files[{index}]")

    captures = data.get("captures")
    if not isinstance(captures, list) or {item.get("path") for item in captures if isinstance(item, dict)} != EXPECTED_CAPTURES:
        raise ScreenshotManifestError("capture inventory must contain the four release images exactly")
    for index, capture in enumerate(captures):
        label = f"captures[{index}]"
        image = _verify_artifact(root, capture, label)
        try:
            media_type, width, height = png_metadata(image.read_bytes())
        except LedgerError as error:
            raise ScreenshotManifestError(f"{label} failed full PNG decode: {error}") from error
        if media_type != "image/png" or capture.get("decoded_size") != f"{width}x{height}":
            raise ScreenshotManifestError(f"{label}.decoded_size does not match decoded image")
        if capture.get("device_scale_factor") != 1 or capture.get("state") != "default_top_of_page":
            raise ScreenshotManifestError(f"{label} has an unexpected DPR or state")
        document = capture.get("document")
        if not isinstance(document, dict) or document.get("language") != "zh-Hant" or document.get("fonts") != "loaded":
            raise ScreenshotManifestError(f"{label} lacks zh-Hant/font-ready capture state")
    return len(captures)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--repository-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        count = validate(args.manifest.expanduser(), args.repository_root.expanduser())
    except ScreenshotManifestError as error:
        print(f"screenshot manifest invalid: {error}", file=sys.stderr)
        return 1
    print(f"screenshot manifest valid: {count} fully decoded captures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
