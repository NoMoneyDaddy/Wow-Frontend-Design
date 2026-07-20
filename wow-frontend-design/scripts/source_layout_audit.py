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
    ".astro", ".css", ".htm", ".html", ".jsx", ".less", ".mdx", ".sass", ".scss",
    ".svelte", ".tsx", ".vue",
}
STYLE_EXTENSIONS = {".css", ".less", ".sass", ".scss"}
PARTIAL_STYLE_SYNTAX_EXTENSIONS = {".less", ".sass", ".scss"}
UNSUPPORTED_RELEVANT_EXTENSIONS = {".pcss", ".styl", ".stylus"}
STYLE_BLOCK = re.compile(r"<style\b[^>]*>(.*?)</style\s*>", re.IGNORECASE | re.DOTALL)
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
CSS_BLOCK = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)
PROSE_WITH_BREAK = re.compile(r"<(p|li)\b([^>]*)>(.*?)</\1\s*>", re.IGNORECASE | re.DOTALL)
BR = re.compile(r"<br\s*/?>", re.IGNORECASE)
INTENTIONAL_BREAK_ROLE = re.compile(
    r"(?:class|data-layout-role)\s*=\s*['\"][^'\"]*(?:address|poem|verse|lyrics|display|editorial)[^'\"]*['\"]",
    re.IGNORECASE,
)
SCREEN_READER_SELECTOR = re.compile(r"(?:sr-only|visually-hidden|screen-reader)", re.IGNORECASE)
EXTERNAL_STYLESHEET = re.compile(
    r"<link\b(?=[^>]*\brel\s*=\s*['\"]?stylesheet)(?=[^>]*\bhref\s*=\s*['\"](?:https?:)?//)",
    re.IGNORECASE,
)
EXTERNAL_CSS_IMPORT = re.compile(r"@import\s+(?:url\()?\s*['\"]?(?:https?:)?//", re.IGNORECASE)
UNMODELED_SELECTOR = re.compile(r":(?:global|has|is|where)\s*\(|(?:^|,)\s*&", re.IGNORECASE)
GLOBAL_SELECTOR = re.compile(
    r"^(?:(?:html|body|:root)(?:[:.#\[].*)?|\*|(?:html|body|:root)\s+\*)$",
    re.IGNORECASE,
)


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


def _selector_subject(selector: str) -> str:
    depth = 0
    quote: str | None = None
    subject_start = 0
    for index, character in enumerate(selector):
        if quote is not None:
            if character == quote and (index == 0 or selector[index - 1] != "\\"):
                quote = None
            continue
        if character in {'"', "'"}:
            quote = character
        elif character in "([":
            depth += 1
        elif character in ")]" and depth > 0:
            depth -= 1
        elif depth == 0 and (character.isspace() or character in ">+~"):
            subject_start = index + 1
    return selector[subject_start:].strip()


def _selector_targets(selector: str, element_pattern: re.Pattern[str]) -> bool:
    if UNMODELED_SELECTOR.search(selector):
        return False
    return any(element_pattern.match(_selector_subject(group)) for group in selector.split(","))


def _selector_is_global(selector: str) -> bool:
    if UNMODELED_SELECTOR.search(selector):
        return False
    return any(GLOBAL_SELECTOR.fullmatch(group.strip()) for group in selector.split(","))


PROSE_SUBJECT = re.compile(r"^(?:p|li)(?=[:.#\[]|$)", re.IGNORECASE)
HEADING_SUBJECT = re.compile(r"^h[1-3](?=[:.#\[]|$)", re.IGNORECASE)
TEXT_SUBJECT = re.compile(r"^(?:p|li|h[1-6])(?=[:.#\[]|$)", re.IGNORECASE)


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
    if suffix in {".astro", ".htm", ".html", ".jsx", ".mdx", ".svelte", ".tsx", ".vue"}:
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

            global_selector = _selector_is_global(selector)
            if global_selector and (word_break == "break-all" or line_break == "anywhere"):
                findings.append(_finding(
                    "global_emergency_breaking",
                    "high",
                    relative_path,
                    line,
                    f"{selector} {{ word-break: {word_break}; line-break: {line_break}; }}",
                    "Remove the global rule; scope emergency breaking to verified unbroken data and render-test it.",
                ))

            if _selector_targets(selector, PROSE_SUBJECT) and not SCREEN_READER_SELECTOR.search(selector):
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
            if _selector_targets(selector, HEADING_SUBJECT) and heading_measure:
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
            if _selector_targets(selector, TEXT_SUBJECT) and not SCREEN_READER_SELECTOR.search(selector) and clipped and fixed_block:
                findings.append(_finding(
                    "fixed_text_clipping",
                    "high",
                    relative_path,
                    line,
                    f"{selector} {{ height: {fixed_block}; overflow: {overflow or overflow_y}; }}",
                    "Confirm scroll/client geometry with long Traditional Chinese, zoom, and fallback fonts.",
                ))
    return findings


def audit(
    root: Path,
    max_files: int = 2_500,
    *,
    authorized_root: Path | None = None,
) -> dict[str, Any]:
    boundary = authorized_root if authorized_root is not None else root
    with project_scan.open_project_tree(root, boundary) as tree:
        files, truncated = tree.collect_files(
            max_files,
            max_directories=project_scan.MAX_WALK_DIRECTORIES,
            max_directory_entries=project_scan.MAX_DIRECTORY_ENTRIES,
            ignored_directories=project_scan.IGNORED_DIRS,
            is_sensitive=project_scan._is_sensitive,
        )
        candidates = [path for path in files if path.suffix.lower() in SOURCE_EXTENSIONS]
        findings: list[dict[str, Any]] = []
        scanned = 0
        unresolved_external_stylesheets = False
        unmodeled_selector_count = 0
        for path in candidates:
            try:
                text = tree.read_text(path, max_bytes=project_scan.MAX_READ_BYTES)
            except project_scan.ProjectIoError:
                continue
            if not text:
                continue
            scanned += 1
            unresolved_external_stylesheets = unresolved_external_stylesheets or bool(
                EXTERNAL_STYLESHEET.search(text) or EXTERNAL_CSS_IMPORT.search(text)
            )
            for css_text, _ in _css_regions(text, path.suffix.lower()):
                clean = CSS_COMMENT.sub("", css_text)
                unmodeled_selector_count += sum(
                    1 for block in CSS_BLOCK.finditer(clean) if UNMODELED_SELECTOR.search(block.group(1))
                )
            findings.extend(
                audit_text(text, path.relative_to(tree.root).as_posix(), path.suffix.lower())
            )
        io_protection = tree.protection
        unsafe_entries_skipped = tree.skipped_unsafe_entries
        unsupported_relevant_extensions = sorted(
            {path.suffix.lower() for path in files if path.suffix.lower() in UNSUPPORTED_RELEVANT_EXTENSIONS}
        )
        partial_syntax_extensions = sorted(
            {path.suffix.lower() for path in candidates if path.suffix.lower() in PARTIAL_STYLE_SYNTAX_EXTENSIONS}
        )
    coverage_incomplete = bool(
        scanned == 0
        or truncated
        or unsafe_entries_skipped
        or unresolved_external_stylesheets
        or unmodeled_selector_count
        or unsupported_relevant_extensions
        or partial_syntax_extensions
    )
    findings.sort(key=lambda item: (item["path"], item["line"], item["code"]))
    return {
        "schema_version": 1,
        "status": (
            "risks_found"
            if findings
            else "coverage_incomplete"
            if coverage_incomplete
            else "no_source_risks_observed"
        ),
        "claim_boundary": "Source risks only; rendered layout requires browser and screenshot evidence.",
        "scanned_files": scanned,
        "scan_truncated": truncated,
        "io_protection": io_protection,
        "unsafe_entries_skipped": unsafe_entries_skipped,
        "coverage": {
            "status": "incomplete" if coverage_incomplete else "bounded_supported_syntax_scanned",
            "supported_extensions": sorted(SOURCE_EXTENSIONS),
            "supported_files_scanned": scanned,
            "unsupported_relevant_extensions": unsupported_relevant_extensions,
            "partial_syntax_extensions": partial_syntax_extensions,
            "unresolved_external_stylesheets": unresolved_external_stylesheets,
            "unmodeled_selector_count": unmodeled_selector_count,
        },
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
        report = audit(
            args.project_root,
            max_files=args.max_files,
            authorized_root=args.authorized_root,
        )
    except (OSError, project_scan.ProjectIoError) as error:
        print(f"source layout audit failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.fail_on == "high" and any(item["severity"] == "high" for item in report["findings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
