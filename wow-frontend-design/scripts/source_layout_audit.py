#!/usr/bin/env python3
"""Bounded source-level layout risk audit for frontend projects.

Rendered browser evidence remains authoritative. This scanner finds a small set
of high-signal source patterns early and reports precise repair pointers.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import project_scan


SOURCE_EXTENSIONS = {
    ".astro", ".css", ".htm", ".html", ".jsx", ".less", ".sass", ".scss",
    ".svelte", ".tsx", ".vue",
}
STYLE_EXTENSIONS = {".css", ".less", ".sass", ".scss"}
STYLE_BLOCK = re.compile(r"<style\b[^>]*>(.*?)</style\s*>", re.IGNORECASE | re.DOTALL)
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
CSS_BLOCK = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)
PROSE_WITH_BREAK = re.compile(r"<(p|li)\b([^>]*)>(.*?)</\1\s*>", re.IGNORECASE | re.DOTALL)
BR = re.compile(r"<br\s*/?>", re.IGNORECASE)
INTENTIONAL_BREAK_ROLE = re.compile(
    r"(?:class|data-layout-role)\s*=\s*['\"][^'\"]*(?:address|poem|verse|lyrics|display|editorial)[^'\"]*['\"]",
    re.IGNORECASE,
)
PROSE_SELECTOR = re.compile(r"(?:^|[\s>,+~])p(?=[:.#\[\s>,+~]|$)", re.IGNORECASE)
HEADING_SELECTOR = re.compile(r"(?:^|[\s>,+~])h[1-3](?=[:.#\[\s>,+~]|$)", re.IGNORECASE)
TEXT_SELECTOR = re.compile(r"(?:^|[\s>,+~])(?:p|li|h[1-6])(?=[:.#\[\s>,+~]|$)", re.IGNORECASE)
SCREEN_READER_SELECTOR = re.compile(r"(?:sr-only|visually-hidden|screen-reader)", re.IGNORECASE)


class SourceLayoutAuditError(ValueError):
    """Raised when the source audit cannot safely inspect its target."""


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, max(0, offset)) + 1


def _declaration_value(declarations: str, property_name: str) -> str | None:
    match = re.search(
        rf"(?:^|;)\s*{re.escape(property_name)}\s*:\s*([^;!}}]+)",
        declarations,
        re.IGNORECASE,
    )
    return " ".join(match.group(1).split()).lower() if match else None


def _css_regions(text: str, suffix: str) -> Iterable[tuple[str, int]]:
    if suffix in STYLE_EXTENSIONS:
        yield text, 0
        return
    for match in STYLE_BLOCK.finditer(text):
        yield match.group(1), match.start(1)


def _finding(
    code: str,
    severity: str,
    relative_path: str,
    line: int,
    evidence: str,
    confirmation: str,
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "path": relative_path,
        "line": line,
        "evidence": " ".join(evidence.split())[:180],
        "confirmation": confirmation,
    }


def audit_text(text: str, relative_path: str, suffix: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if suffix in {".astro", ".htm", ".html", ".jsx", ".svelte", ".tsx", ".vue"}:
        for match in PROSE_WITH_BREAK.finditer(text):
            if BR.search(match.group(3)) and not INTENTIONAL_BREAK_ROLE.search(match.group(2)):
                findings.append(_finding(
                    "forced_body_break",
                    "medium",
                    relative_path,
                    _line_number(text, match.start()),
                    match.group(0),
                    "Confirm the rendered prose role; ordinary body copy should wrap naturally.",
                ))

    for css_text, base_offset in _css_regions(text, suffix):
        clean = CSS_COMMENT.sub(lambda match: "\n" * match.group(0).count("\n"), css_text)
        for block in CSS_BLOCK.finditer(clean):
            selector = " ".join(block.group(1).split())
            declarations = block.group(2)
            line = _line_number(text, base_offset + block.start())
            word_break = _declaration_value(declarations, "word-break")
            line_break = _declaration_value(declarations, "line-break")
            white_space = _declaration_value(declarations, "white-space")
            overflow = _declaration_value(declarations, "overflow")
            overflow_y = _declaration_value(declarations, "overflow-y")
            height = _declaration_value(declarations, "height")
            max_height = _declaration_value(declarations, "max-height")
            max_width = _declaration_value(declarations, "max-width")
            max_inline = _declaration_value(declarations, "max-inline-size")
            width = _declaration_value(declarations, "width")

            global_selector = any(
                re.search(pattern, selector, re.IGNORECASE)
                for pattern in (r"(?:^|,)\s*(?:html|body|:root)(?:\s|,|$)", r"(?:^|,)\s*\*(?:\s|,|$)")
            )
            if global_selector and (word_break == "break-all" or line_break == "anywhere"):
                findings.append(_finding(
                    "global_emergency_breaking",
                    "high",
                    relative_path,
                    line,
                    f"{selector} {{ word-break: {word_break}; line-break: {line_break}; }}",
                    "Remove the global rule; scope emergency breaking to verified unbroken data and render-test it.",
                ))

            if PROSE_SELECTOR.search(selector) and not SCREEN_READER_SELECTOR.search(selector):
                if white_space in {"nowrap", "pre"}:
                    findings.append(_finding(
                        "prose_wrap_disabled",
                        "high",
                        relative_path,
                        line,
                        f"{selector} {{ white-space: {white_space}; }}",
                        "Confirm computed style and overflow at mobile, zoom, and expanded locale widths.",
                    ))

            heading_measure = next(
                (value for value in (max_width, max_inline, width) if value and re.search(r"\b\d+(?:\.\d+)?ch\b", value)),
                None,
            )
            if HEADING_SELECTOR.search(selector) and heading_measure:
                findings.append(_finding(
                    "heading_latin_ch_measure",
                    "medium",
                    relative_path,
                    line,
                    f"{selector} {{ measure: {heading_measure}; }}",
                    "Measure CJK line fragments in the browser; Latin ch is only a risk signal, not a failure by itself.",
                ))

            clipped = (overflow in {"hidden", "clip"} or overflow_y in {"hidden", "clip"})
            fixed_block = next((value for value in (height, max_height) if value and value not in {"auto", "none"}), None)
            if TEXT_SELECTOR.search(selector) and not SCREEN_READER_SELECTOR.search(selector) and clipped and fixed_block:
                findings.append(_finding(
                    "fixed_text_clipping",
                    "high",
                    relative_path,
                    line,
                    f"{selector} {{ height: {fixed_block}; overflow: {overflow or overflow_y}; }}",
                    "Confirm scroll/client geometry with long Traditional Chinese, zoom, and fallback fonts.",
                ))
    return findings


def audit(root: Path, max_files: int = 2_500) -> dict[str, Any]:
    files, truncated = project_scan.collect_files(root, max_files=max_files)
    candidates = [path for path in files if path.suffix.lower() in SOURCE_EXTENSIONS]
    findings: list[dict[str, Any]] = []
    scanned = 0
    for path in candidates:
        text = project_scan.read_text(path)
        if not text:
            continue
        scanned += 1
        findings.extend(audit_text(text, path.relative_to(root).as_posix(), path.suffix.lower()))
    findings.sort(key=lambda item: (item["path"], item["line"], item["code"]))
    return {
        "schema_version": 1,
        "status": "risks_found" if findings else "no_source_risks_observed",
        "claim_boundary": "Source risks only; rendered layout requires browser and screenshot evidence.",
        "scanned_files": scanned,
        "scan_truncated": truncated,
        "finding_count": len(findings),
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--authorized-root", required=True, type=Path)
    parser.add_argument("--max-files", type=int, default=2_500)
    parser.add_argument("--fail-on", choices=("none", "high"), default="none")
    args = parser.parse_args(argv)
    if args.max_files < 1 or args.max_files > 50_000:
        parser.error("--max-files must be between 1 and 50000")
    try:
        root = project_scan.resolve_project_root(args.project_root, args.authorized_root)
        report = audit(root, max_files=args.max_files)
    except (OSError, project_scan.ProjectRootError) as error:
        print(f"source layout audit failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.fail_on == "high" and any(item["severity"] == "high" for item in report["findings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
