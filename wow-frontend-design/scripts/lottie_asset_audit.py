#!/usr/bin/env python3
"""Dependency-free static risk audit for Lottie JSON and dotLottie archives."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


IGNORED_DIRS = {".git", ".next", ".nuxt", ".output", "build", "dist", "node_modules", "out", "vendor"}
MAX_FILES = 2_000
MAX_ASSET_BYTES = 5_000_000
MAX_ARCHIVE_ENTRIES = 500
MAX_DECOMPRESSED_BYTES = 20_000_000
MAX_COMPRESSION_RATIO = 100
MAX_LAYERS = 250
MAX_TREE_NODES = 50_000
SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3}


@dataclass(frozen=True)
class Finding:
    severity: str
    rule: str
    path: str
    message: str


class AuditError(ValueError):
    """Raised when the audit target itself is unsafe or invalid."""


def is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def reject_non_finite_constant(value: str) -> None:
    raise ValueError(f"non-finite numeric constant is not valid JSON: {value}")


def relative(path: Path, root: Path) -> str:
    base = root if root.is_dir() else root.parent
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def iter_assets(root: Path) -> Iterable[Path]:
    if root.is_symlink():
        raise AuditError(f"refusing symlink root: {root}")
    if root.is_file():
        if root.suffix.lower() in {".json", ".lottie"}:
            yield root
        return
    if not root.is_dir():
        raise AuditError(f"path is not a file or directory: {root}")
    count = 0
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(
            name for name in dirs if name not in IGNORED_DIRS and not (Path(current) / name).is_symlink()
        )
        for name in sorted(names):
            path = Path(current) / name
            if path.is_symlink() or path.suffix.lower() not in {".json", ".lottie"}:
                continue
            count += 1
            if count > MAX_FILES:
                raise AuditError(f"file limit exceeded: {MAX_FILES}")
            yield path


def is_lottie(value: Any) -> bool:
    return isinstance(value, dict) and {"v", "fr", "ip", "op", "layers"}.issubset(value)


def walk(value: Any) -> Iterable[tuple[str | None, Any]]:
    stack: list[tuple[str | None, Any]] = [(None, value)]
    seen = 0
    while stack:
        key, item = stack.pop()
        seen += 1
        if seen > MAX_TREE_NODES:
            raise AuditError(f"parsed tree exceeds {MAX_TREE_NODES} nodes")
        yield key, item
        if isinstance(item, dict):
            stack.extend(reversed(list(item.items())))
        elif isinstance(item, list):
            stack.extend((None, child) for child in reversed(item))


def audit_document(value: dict[str, Any], name: str) -> list[Finding]:
    findings: list[Finding] = []

    def add(severity: str, rule: str, message: str) -> None:
        findings.append(Finding(severity, rule, name, message))

    fr, ip, op = value.get("fr"), value.get("ip"), value.get("op")
    width, height = value.get("w"), value.get("h")
    if not all(is_finite_number(item) for item in (fr, ip, op)):
        add("high", "LOTTIE001", "Frame rate/in/out points must be finite numeric values.")
    elif fr <= 0 or fr > 240 or op <= ip or (op - ip) / fr > 3_600:
        add("high", "LOTTIE002", "Frame rate/range is impossible or exceeds the one-hour audit limit.")
    if not all(is_finite_number(item) and 0 < item <= 16_384 for item in (width, height)):
        add("high", "LOTTIE003", "Canvas width/height is missing, non-positive, or above 16384px.")

    layers = value.get("layers")
    if not isinstance(layers, list):
        add("high", "LOTTIE004", "Top-level layers must be an array.")
    elif len(layers) > MAX_LAYERS:
        add("medium", "LOTTIE005", f"Top-level layer count {len(layers)} exceeds the {MAX_LAYERS} review threshold.")

    assets = value.get("assets", [])
    if isinstance(assets, list):
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            location = f"{asset.get('u', '')}{asset.get('p', '')}".strip()
            lowered = location.lower()
            if lowered.startswith(("http://", "https://", "//", "file://")):
                add("high", "LOTTIE006", f"External asset URL requires an explicit fetch/SSRF policy: {location[:120]}")
            elif lowered.startswith("data:"):
                add("medium", "LOTTIE007", "Embedded data asset needs decoded-byte, MIME, and image-dimension limits.")

    has_expression = False
    has_text = False
    try:
        for key, item in walk(value):
            if key == "x" and isinstance(item, str) and item.strip():
                has_expression = True
            if key == "t" and isinstance(item, dict) and ("d" in item or "a" in item):
                has_text = True
    except AuditError as error:
        add("high", "LOTTIE008", str(error))
    if has_expression:
        add("medium", "LOTTIE009", "Expression-like content found; confirm the exact player rejects or safely supports it.")
    if has_text or value.get("fonts"):
        add("medium", "LOTTIE010", "Text/font content needs license, glyph, shaping, CJK/RTL, fallback, and DOM-equivalent review.")
    return findings


def parse_json_bytes(data: bytes, name: str) -> tuple[dict[str, Any] | None, list[Finding]]:
    try:
        value = json.loads(data.decode("utf-8"), parse_constant=reject_non_finite_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        return None, [Finding("high", "LOTTIE011", name, f"Invalid UTF-8 or strict JSON: {error}")]
    return (value if is_lottie(value) else None), []


def audit_json(path: Path, root: Path) -> tuple[bool, list[Finding]]:
    name = relative(path, root)
    try:
        size = path.stat().st_size
        if size > MAX_ASSET_BYTES:
            return True, [Finding("high", "LOTTIE012", name, f"Asset exceeds {MAX_ASSET_BYTES} bytes.")]
        value, findings = parse_json_bytes(path.read_bytes(), name)
    except OSError as error:
        return True, [Finding("high", "LOTTIE013", name, f"Asset could not be read: {error}")]
    if value is None:
        return bool(findings), findings
    return True, findings + audit_document(value, name)


def audit_archive(path: Path, root: Path) -> list[Finding]:
    name = relative(path, root)
    findings: list[Finding] = []
    try:
        if path.stat().st_size > MAX_ASSET_BYTES:
            return [Finding("high", "LOTTIE012", name, f"Archive exceeds {MAX_ASSET_BYTES} bytes.")]
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ARCHIVE_ENTRIES:
                findings.append(Finding("high", "LOTTIE014", name, f"Archive exceeds {MAX_ARCHIVE_ENTRIES} entries."))
                return findings
            total = 0
            found_manifest = False
            found_animation = False
            for info in infos:
                member = PurePosixPath(info.filename)
                if member.is_absolute() or ".." in member.parts or "\x00" in info.filename:
                    findings.append(Finding("high", "LOTTIE015", name, f"Unsafe archive path: {info.filename!r}"))
                    continue
                if info.flag_bits & 0x1:
                    findings.append(Finding("high", "LOTTIE016", name, f"Encrypted archive member is unsupported: {info.filename}"))
                    continue
                total += info.file_size
                if total > MAX_DECOMPRESSED_BYTES:
                    findings.append(Finding("high", "LOTTIE017", name, f"Archive exceeds {MAX_DECOMPRESSED_BYTES} decompressed bytes."))
                    break
                ratio = info.file_size / max(info.compress_size, 1)
                if ratio > MAX_COMPRESSION_RATIO:
                    findings.append(Finding("high", "LOTTIE018", name, f"Suspicious compression ratio for {info.filename}: {ratio:.1f}x"))
                if info.filename == "manifest.json":
                    found_manifest = True
                if info.filename.startswith("animations/") and info.filename.endswith(".json"):
                    found_animation = True
                    animation_name = f"{name}!/{info.filename}"
                    if info.file_size > MAX_ASSET_BYTES:
                        findings.append(
                            Finding(
                                "high",
                                "LOTTIE012",
                                animation_name,
                                f"Animation document exceeds {MAX_ASSET_BYTES} bytes and was not audited.",
                            )
                        )
                        continue
                    value, parse_findings = parse_json_bytes(archive.read(info), animation_name)
                    findings.extend(parse_findings)
                    if value is not None:
                        findings.extend(audit_document(value, animation_name))
            if not found_manifest or not found_animation:
                findings.append(Finding("high", "LOTTIE019", name, "dotLottie archive needs manifest.json and an animations/*.json document."))
    except (OSError, zipfile.BadZipFile, RuntimeError) as error:
        findings.append(Finding("high", "LOTTIE020", name, f"Invalid or unreadable dotLottie archive: {error}"))
    return findings


def audit(root: Path) -> tuple[list[Finding], int]:
    expanded = root.expanduser()
    if expanded.is_symlink():
        raise AuditError(f"refusing symlink root: {expanded}")
    resolved = expanded.resolve(strict=False)
    findings: list[Finding] = []
    audited = 0
    for path in iter_assets(resolved):
        if path.suffix.lower() == ".lottie":
            audited += 1
            findings.extend(audit_archive(path, resolved))
        else:
            recognized, json_findings = audit_json(path, resolved)
            if recognized:
                audited += 1
                findings.extend(json_findings)
    findings.sort(key=lambda item: (-SEVERITY_RANK[item.severity], item.path, item.rule))
    return findings, audited


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--fail-on", choices=("low", "medium", "high"))
    args = parser.parse_args()
    try:
        findings, audited = audit(args.root)
    except AuditError as error:
        print(f"audit error: {error}", file=sys.stderr)
        return 2
    if args.as_json:
        print(json.dumps({"audited_assets": audited, "findings": [asdict(item) for item in findings]}, indent=2))
    else:
        print(f"audited Lottie assets: {audited}; findings: {len(findings)}")
        for item in findings:
            print(f"{item.severity.upper()} {item.rule} {item.path}: {item.message}")
    if args.fail_on and any(SEVERITY_RANK[item.severity] >= SEVERITY_RANK[args.fail_on] for item in findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
