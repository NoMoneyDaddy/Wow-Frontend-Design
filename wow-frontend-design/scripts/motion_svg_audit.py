#!/usr/bin/env python3
"""Dependency-free static risk audit for frontend motion and SVG usage."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


TEXT_EXTENSIONS = {
    ".astro",
    ".cshtml",
    ".css",
    ".ejs",
    ".erb",
    ".haml",
    ".hbs",
    ".htm",
    ".html",
    ".js",
    ".jsx",
    ".liquid",
    ".mjs",
    ".mustache",
    ".njk",
    ".php",
    ".pug",
    ".razor",
    ".scss",
    ".slim",
    ".svelte",
    ".svg",
    ".ts",
    ".tsx",
    ".twig",
    ".vue",
}
IGNORED_DIRS = {
    ".git",
    ".next",
    ".nuxt",
    ".output",
    ".turbo",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "vendor",
}
MAX_FILE_BYTES = 1_500_000
MAX_FILES = 4_000
MAX_TOTAL_BYTES = 64 * 1024 * 1024
SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3}

MOTION_PATTERN = re.compile(
    r"\b(?:animation(?:-[a-z-]+)?|transition(?:-[a-z-]+)?|requestAnimationFrame|"
    r"startViewTransition|ScrollTrigger|useReducedMotion|lottie|rive)\b|"
    r"\.animate\s*\(|\bgsap\s*\.\s*(?:to|from|fromTo|set|timeline|quickTo|quickSetter)\s*\(",
    re.IGNORECASE,
)
JS_RUNTIME_MOTION_PATTERN = re.compile(
    r"\b(?:ScrollTrigger|startViewTransition|lottie|rive)\b|\.animate\s*\(|"
    r"\bgsap\s*\.\s*(?:to|from|fromTo|set|timeline|quickTo|quickSetter)\s*\(|"
    r"requestAnimationFrame\s*\(\s*[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*\b",
    re.IGNORECASE,
)
GSAP_CALL_PATTERN = re.compile(
    r"\bgsap\s*\.\s*(?:to|from|fromTo|set|timeline|quickTo|quickSetter)\s*\(|"
    r"\bScrollTrigger\s*\.\s*(?:create|batch)\s*\(",
    re.IGNORECASE,
)
GSAP_CLEANUP_PATTERN = re.compile(
    r"\buseGSAP\s*\(|\b[A-Za-z_$][\w$]*\s*(?:\?\.|\.)\s*(?:revert|kill)\s*\(|"
    r"\bScrollTrigger\s*\.\s*killAll\s*\(",
    re.IGNORECASE,
)
REDUCED_MOTION_BLOCK_PATTERN = re.compile(
    r"@media\s*\([^)]*prefers-reduced-motion\s*:\s*reduce[^)]*\)\s*\{(?P<body>.*?)\}",
    re.IGNORECASE | re.DOTALL,
)
CSS_DECLARATION_PATTERN = re.compile(
    r"(?:^|[;{])\s*--?[A-Za-z_][\w-]*\s*:|(?:^|[;{])\s*[A-Za-z_][\w-]*\s*:"
)
SVG_BLOCK_PATTERN = re.compile(r"<svg\b(?P<attrs>[^>]*)>(?P<body>.*?)</svg\s*>", re.IGNORECASE | re.DOTALL)
OPEN_SVG_PATTERN = re.compile(r"<svg\b(?P<attrs>[^>]*)>", re.IGNORECASE | re.DOTALL)
TAG_PATTERN = re.compile(r"<(?:img|object|embed|iframe)\b[^>]*>", re.IGNORECASE | re.DOTALL)
ID_PATTERN = re.compile(r"(?<![\w:-])id\s*=\s*([\"'])(?P<id>[^\"']+)\1", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    severity: str
    rule: str
    path: str
    line: int
    message: str


class AuditError(Exception):
    """Raised for invalid or unreadable audit inputs."""


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def iter_source_files(root: Path) -> Iterable[Path]:
    if root.is_symlink():
        raise AuditError(f"refusing symlink root: {root}")
    if root.is_file():
        if root.suffix.lower() in TEXT_EXTENSIONS:
            yield root
        return
    if not root.is_dir():
        raise AuditError(f"path is not a file or directory: {root}")

    count = 0
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(
            name
            for name in dirs
            if name not in IGNORED_DIRS and not (Path(current) / name).is_symlink()
        )
        for name in sorted(names):
            path = Path(current) / name
            if path.is_symlink() or path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            count += 1
            if count > MAX_FILES:
                raise AuditError(f"file limit exceeded: {MAX_FILES}")
            yield path


def read_sources(root: Path) -> tuple[dict[Path, str], list[tuple[Path, str]]]:
    sources: dict[Path, str] = {}
    skipped: list[tuple[Path, str]] = []
    total_bytes = 0
    for path in iter_source_files(root):
        try:
            flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(path, flags)
            try:
                metadata = os.fstat(descriptor)
                if not stat.S_ISREG(metadata.st_mode):
                    skipped.append((path, "path is not a regular file"))
                    continue
                if metadata.st_size > MAX_FILE_BYTES:
                    skipped.append((path, f"file exceeds {MAX_FILE_BYTES} byte audit limit"))
                    continue
                chunks: list[bytes] = []
                remaining = MAX_FILE_BYTES + 1
                while remaining > 0:
                    chunk = os.read(descriptor, min(65_536, remaining))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
                raw = b"".join(chunks)
                if len(raw) > MAX_FILE_BYTES:
                    skipped.append((path, f"file exceeds {MAX_FILE_BYTES} byte audit limit"))
                    continue
            finally:
                os.close(descriptor)
            total_bytes += len(raw)
            if total_bytes > MAX_TOTAL_BYTES:
                raise AuditError(f"aggregate source limit exceeded: {MAX_TOTAL_BYTES}")
            sources[path] = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError) as error:
            skipped.append((path, f"file could not be decoded/read: {error}"))
    return sources, skipped


def blank_comments(text: str, *, strip_line_comments: bool = True) -> str:
    """Remove common comments while preserving offsets and line numbers."""

    def blank(match: re.Match[str]) -> str:
        return "".join("\n" if char == "\n" else " " for char in match.group(0))

    without_blocks = re.sub(r"/\*.*?\*/|<!--.*?-->", blank, text, flags=re.DOTALL)
    if not strip_line_comments:
        return without_blocks
    return re.sub(r"(?m)(?<!:)//[^\r\n]*$", blank, without_blocks)


def has_runtime_reduced_motion_path(text: str) -> bool:
    if re.search(r"useReducedMotion|matchMedia\s*\([^)]*prefers-reduced-motion", text, re.IGNORECASE):
        return True
    return (
        re.search(r"\bgsap\s*\.\s*matchMedia\s*\(", text, re.IGNORECASE) is not None
        and re.search(r"prefers-reduced-motion\s*:\s*reduce", text, re.IGNORECASE) is not None
    )


def has_reduced_motion_path(text: str) -> bool:
    if has_runtime_reduced_motion_path(text):
        return True
    return any(CSS_DECLARATION_PATTERN.search(match.group("body")) for match in REDUCED_MOTION_BLOCK_PATTERN.finditer(text))


def relative_path(path: Path, root: Path) -> str:
    base = root if root.is_dir() else root.parent
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def add(
    findings: list[Finding],
    severity: str,
    rule: str,
    path: Path,
    root: Path,
    text: str,
    offset: int,
    message: str,
) -> None:
    findings.append(
        Finding(
            severity=severity,
            rule=rule,
            path=relative_path(path, root),
            line=line_number(text, offset),
            message=message,
        )
    )


def audit_motion(root: Path, sources: dict[Path, str], findings: list[Finding]) -> None:
    motion_locations: list[tuple[Path, str, re.Match[str]]] = []
    analyzed = {path: blank_comments(text) for path, text in sources.items()}
    combined = "\n".join(analyzed.values())
    has_reduced_motion = has_reduced_motion_path(combined)
    has_runtime_reduced_motion = has_runtime_reduced_motion_path(combined)
    has_smooth_scroll = re.search(r"scroll-behavior\s*:\s*smooth", combined, re.IGNORECASE) is not None
    has_static_scroll_fallback = re.search(r"scroll-behavior\s*:\s*auto", combined, re.IGNORECASE) is not None

    runtime_location: tuple[Path, str, re.Match[str]] | None = None
    for path, original in sources.items():
        text = analyzed[path]
        match = MOTION_PATTERN.search(text)
        if match:
            motion_locations.append((path, text, match))

        runtime_match = JS_RUNTIME_MOTION_PATTERN.search(text)
        if runtime_match and runtime_location is None:
            runtime_location = (path, text, runtime_match)

        gsap_match = GSAP_CALL_PATTERN.search(text)
        if gsap_match and path.suffix.lower() in {".astro", ".jsx", ".svelte", ".tsx", ".vue"}:
            if GSAP_CLEANUP_PATTERN.search(text) is None:
                add(
                    findings,
                    "medium",
                    "MOTION008",
                    path,
                    root,
                    text,
                    gsap_match.start(),
                    "Component-scoped GSAP motion has no scanned useGSAP/context revert/kill lifecycle; unmounts may leak animations or stale inline state.",
                )

        for item in re.finditer(r"\bmarkers\s*:\s*true\b", text, re.IGNORECASE):
            add(
                findings,
                "medium",
                "MOTION009",
                path,
                root,
                text,
                item.start(),
                "ScrollTrigger development markers must be disabled before shipping.",
            )

        for item in re.finditer(
            r"\bonMounted\s*\(\s*\(\s*\)\s*=>\s*\{\s*(?:[A-Za-z_$][\w$]*\s*&&\s*)?"
            r"[A-Za-z_$][\w$]*\s*(?:\?\.|\.)\s*revert\s*\(",
            text,
            re.IGNORECASE,
        ):
            add(
                findings,
                "high",
                "MOTION010",
                path,
                root,
                text,
                item.start(),
                "GSAP cleanup is registered during mount; move revert/kill to the framework unmount or disposal lifecycle.",
            )

        for item in re.finditer(r"transition(?:-property)?\s*:\s*all\b", text, re.IGNORECASE):
            add(
                findings,
                "medium",
                "MOTION002",
                path,
                root,
                text,
                item.start(),
                "List transition properties; `all` can animate unintended layout or state changes.",
            )

        for item in re.finditer(r"animation(?:-iteration-count)?\s*:[^;{}]*\binfinite\b", text, re.IGNORECASE):
            add(
                findings,
                "medium",
                "MOTION003",
                path,
                root,
                text,
                item.start(),
                "Infinite animation needs reduced-motion, off-screen/background pause, and lifecycle cleanup evidence.",
            )

        for item in re.finditer(r"will-change\s*:", text, re.IGNORECASE):
            add(
                findings,
                "low",
                "MOTION005",
                path,
                root,
                text,
                item.start(),
                "Confirm `will-change` is temporary and removed after the proven animation.",
            )

        for item in re.finditer(r"(?:animation|transition)-duration\s*:\s*0?\.0+1ms", text, re.IGNORECASE):
            add(
                findings,
                "medium",
                "MOTION006",
                path,
                root,
                text,
                item.start(),
                "A near-zero duration is not a complete reduced-motion result; verify static state and stop runtime loops.",
            )

    if motion_locations and not has_reduced_motion:
        path, text, match = motion_locations[0]
        add(
            findings,
            "high",
            "MOTION001",
            path,
            root,
            text,
            match.start(),
            "Motion exists but no `prefers-reduced-motion: reduce` path was found in scanned source.",
        )

    if runtime_location and not has_runtime_reduced_motion:
        path, text, match = runtime_location
        add(
            findings,
            "high",
            "MOTION007",
            path,
            root,
            text,
            match.start(),
            "JavaScript/runtime motion exists but no scanned runtime reduced-motion preference check was found; a CSS query alone cannot stop it.",
        )

    if has_smooth_scroll and not has_static_scroll_fallback:
        for path, text in sources.items():
            item = re.search(r"scroll-behavior\s*:\s*smooth", text, re.IGNORECASE)
            if item:
                add(
                    findings,
                    "medium",
                    "MOTION004",
                    path,
                    root,
                    text,
                    item.start(),
                    "Smooth scrolling has no scanned `scroll-behavior: auto` fallback for reduced motion.",
                )
                break


def audit_svg_block(root: Path, path: Path, text: str, match: re.Match[str], findings: list[Finding]) -> None:
    attrs = match.group("attrs")
    body = match.group("body")
    block = match.group(0)
    start = match.start()

    if re.search(r"\bviewBox\s*=", attrs, re.IGNORECASE) is None:
        add(findings, "medium", "SVG001", path, root, text, start, "Inline SVG has no `viewBox`; responsive scaling may fail.")

    role_img = re.search(r"\brole\s*=\s*([\"'])img\1", attrs, re.IGNORECASE) is not None
    has_aria_name = re.search(r"\baria-(?:label|labelledby)\s*=\s*([\"'])\s*[^\s\"'][^\"']*\1", attrs, re.IGNORECASE) is not None
    has_title = re.search(r"<title\b[^>]*>\s*[^<\s][^<]*</title\s*>", body, re.IGNORECASE) is not None
    aria_hidden = re.search(r"\baria-hidden\s*=\s*([\"'])true\1", attrs, re.IGNORECASE) is not None

    if role_img and not (has_aria_name or has_title):
        add(findings, "high", "SVG002", path, root, text, start, "SVG with `role=img` has no non-empty accessible name.")
    if role_img and aria_hidden:
        add(findings, "medium", "SVG003", path, root, text, start, "SVG declares both `role=img` and `aria-hidden=true`; choose one semantic intent.")

    unsafe_patterns = (
        (r"<script\b", "script element"),
        (r"<foreignObject\b", "foreignObject"),
        (r"\son[a-z]+\s*=", "inline event handler"),
        (r"javascript\s*:", "javascript URL"),
        (r"@import\b", "CSS import"),
        (r"(?:href|xlink:href)\s*=\s*([\"'])(?:https?:|//|data:)", "external or data href"),
        (r"url\(\s*([\"']?)(?:https?:|//|data:)", "external or data CSS URL"),
    )
    for pattern, label in unsafe_patterns:
        item = re.search(pattern, block, re.IGNORECASE)
        if item:
            add(
                findings,
                "high",
                "SVG004",
                path,
                root,
                text,
                start + item.start(),
                f"SVG contains {label}; treat as active content and review the trust/sanitization boundary.",
            )

    item = re.search(r"\bpreserveAspectRatio\s*=\s*([\"'])none\1", attrs, re.IGNORECASE)
    if item:
        add(
            findings,
            "medium",
            "SVG007",
            path,
            root,
            text,
            start + item.start(),
            "`preserveAspectRatio=none` distorts geometry; verify that deformation is intentional.",
        )


def audit_svg(root: Path, sources: dict[Path, str], findings: list[Finding]) -> None:
    for path, original in sources.items():
        # Preserve `//host/path` in markup so protocol-relative SVG URLs remain auditable.
        text = blank_comments(original, strip_line_comments=False)
        block_matches = list(SVG_BLOCK_PATTERN.finditer(text))
        for match in block_matches:
            audit_svg_block(root, path, text, match, findings)

        # Catch malformed/unclosed SVG starts without duplicating complete blocks.
        if not block_matches:
            for match in OPEN_SVG_PATTERN.finditer(text):
                attrs = match.group("attrs")
                if re.search(r"\bviewBox\s*=", attrs, re.IGNORECASE) is None:
                    add(findings, "medium", "SVG001", path, root, text, match.start(), "SVG has no `viewBox`; responsive scaling may fail.")

        ids = [(match.group("id"), match.start()) for match in ID_PATTERN.finditer(text)]
        counts = Counter(value for value, _ in ids)
        for value in sorted(key for key, count in counts.items() if count > 1):
            duplicate_offset = next(offset for key, offset in ids if key == value)
            add(
                findings,
                "high",
                "SVG005",
                path,
                root,
                text,
                duplicate_offset,
                f"Duplicate ID `{value}` can break SVG references, ARIA, or repeated component instances.",
            )

        for tag in TAG_PATTERN.finditer(text):
            value = tag.group(0)
            if re.match(r"<img\b", value, re.IGNORECASE) and re.search(
                r"\bsrc\s*=\s*([\"'])[^\"']+\.svg(?:[?#][^\"']*)?\1", value, re.IGNORECASE
            ):
                if re.search(r"\balt\s*=", value, re.IGNORECASE) is None:
                    add(findings, "high", "SVG006", path, root, text, tag.start(), "SVG `<img>` has no `alt` attribute.")
            elif re.match(r"<(?:object|embed|iframe)\b", value, re.IGNORECASE) and re.search(
                r"\b(?:data|src)\s*=\s*([\"'])[^\"']+\.svg(?:[?#][^\"']*)?\1", value, re.IGNORECASE
            ):
                add(
                    findings,
                    "high",
                    "SVG008",
                    path,
                    root,
                    text,
                    tag.start(),
                    "SVG is loaded as an active document; verify trust, sandbox, CSP, navigation, and accessible fallback.",
                )


def audit(root: Path) -> tuple[list[Finding], int]:
    expanded = root.expanduser()
    if expanded.is_symlink():
        raise AuditError(f"refusing symlink root: {expanded}")
    resolved = expanded.resolve(strict=False)
    sources, skipped = read_sources(resolved)
    findings: list[Finding] = []
    for path, reason in skipped:
        findings.append(
            Finding(
                severity="medium",
                rule="AUDIT001",
                path=relative_path(path, resolved),
                line=1,
                message=f"Static audit coverage is incomplete: {reason}.",
            )
        )
    audit_motion(resolved, sources, findings)
    audit_svg(resolved, sources, findings)
    findings.sort(key=lambda item: (-SEVERITY_RANK[item.severity], item.path, item.line, item.rule))
    return findings, len(sources)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Statically audit frontend motion and SVG risks.")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--fail-on", choices=("none", "high", "medium", "low"), default="none")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        findings, file_count = audit(Path(args.path))
    except AuditError as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False) if args.json else f"ERROR: {error}")
        return 2

    counts = Counter(item.severity for item in findings)
    report = {
        "ok": not findings,
        "acceptance": "advisory_only",
        "files_scanned": file_count,
        "finding_count": len(findings),
        "severity": {key: counts.get(key, 0) for key in ("high", "medium", "low")},
        "findings": [asdict(item) for item in findings],
        "limitations": "Static risk discovery only; not browser, accessibility, security, visual, or performance proof.",
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"Scanned {file_count} files; findings: {len(findings)} "
            f"(high={counts.get('high', 0)}, medium={counts.get('medium', 0)}, low={counts.get('low', 0)})"
        )
        for item in findings:
            print(f"[{item.severity.upper()}] {item.path}:{item.line} {item.rule} — {item.message}")
        print("LIMIT: static risk discovery only; rendered and runtime behavior still require dedicated checks.")

    if args.fail_on != "none":
        threshold = SEVERITY_RANK[args.fail_on]
        if any(SEVERITY_RANK[item.severity] >= threshold for item in findings):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
