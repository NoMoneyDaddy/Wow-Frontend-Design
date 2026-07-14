#!/usr/bin/env python3
"""Advisory offline audit for search/discovery metadata in HTML artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


LANGUAGE_TAG = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
MAX_DEFAULT_FILES = 200
MAX_DEFAULT_BYTES = 2_000_000


@dataclass
class Page:
    path: Path
    lang: str = ""
    titles: list[str] = field(default_factory=list)
    descriptions: list[str] = field(default_factory=list)
    canonicals: list[str] = field(default_factory=list)
    alternates: list[tuple[str, str]] = field(default_factory=list)
    robots: list[str] = field(default_factory=list)
    jsonld: list[str] = field(default_factory=list)
    h1_count: int = 0
    anchors_without_href: int = 0
    javascript_links: int = 0


class SearchHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.page = Page(path=Path("."))
        self._title_depth = 0
        self._title_parts: list[str] = []
        self._jsonld_depth = 0
        self._jsonld_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.casefold(): (value or "") for key, value in attrs}
        name = tag.casefold()
        if name == "html" and not self.page.lang:
            self.page.lang = values.get("lang", "").strip()
        elif name == "title":
            self._title_depth += 1
            if self._title_depth == 1:
                self._title_parts = []
        elif name == "meta":
            key = values.get("name", "").casefold()
            content = values.get("content", "").strip()
            if key == "description":
                self.page.descriptions.append(content)
            elif key in {"robots", "googlebot", "bingbot"}:
                self.page.robots.append(content.casefold())
        elif name == "link":
            rels = {item.casefold() for item in values.get("rel", "").split()}
            href = values.get("href", "").strip()
            if "canonical" in rels:
                self.page.canonicals.append(href)
            if "alternate" in rels and values.get("hreflang", "").strip():
                self.page.alternates.append((values["hreflang"].strip(), href))
        elif name == "script" and values.get("type", "").casefold() == "application/ld+json":
            self._jsonld_depth += 1
            if self._jsonld_depth == 1:
                self._jsonld_parts = []
        elif name == "h1":
            self.page.h1_count += 1
        elif name == "a":
            href = values.get("href")
            if href is None or not href.strip():
                self.page.anchors_without_href += 1
            elif href.strip().casefold().startswith("javascript:"):
                self.page.javascript_links += 1

    def handle_endtag(self, tag: str) -> None:
        name = tag.casefold()
        if name == "title" and self._title_depth:
            self._title_depth -= 1
            if self._title_depth == 0:
                self.page.titles.append("".join(self._title_parts).strip())
        elif name == "script" and self._jsonld_depth:
            self._jsonld_depth -= 1
            if self._jsonld_depth == 0:
                self.page.jsonld.append("".join(self._jsonld_parts).strip())

    def handle_data(self, data: str) -> None:
        if self._title_depth:
            self._title_parts.append(data)
        if self._jsonld_depth:
            self._jsonld_parts.append(data)


def finding(severity: str, code: str, path: Path, message: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "file": str(path), "message": message}


def is_absolute_web_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and not parsed.fragment


def blocks_indexing(value: str) -> bool:
    """Return whether a robots value explicitly blocks indexing."""
    directives = {part.strip().casefold() for part in value.split(",") if part.strip()}
    return bool(directives & {"noindex", "none"})


def collect_files(target: Path, max_files: int) -> list[Path]:
    if target.is_symlink():
        raise ValueError(f"refusing symlink target: {target}")
    if target.is_file():
        if target.suffix.casefold() not in {".html", ".htm"}:
            raise ValueError("target file must be HTML")
        return [target]
    if not target.is_dir():
        raise ValueError(f"target does not exist: {target}")
    files: list[Path] = []
    for candidate in sorted(target.rglob("*")):
        if candidate.is_symlink():
            continue
        if candidate.is_file() and candidate.suffix.casefold() in {".html", ".htm"}:
            files.append(candidate)
            if len(files) > max_files:
                raise ValueError(f"HTML file limit exceeded: {max_files}")
    if not files:
        raise ValueError("no HTML files found")
    return files


def parse_page(path: Path, max_bytes: int) -> Page:
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"HTML byte limit exceeded for {path}: {size} > {max_bytes}")
    parser = SearchHTMLParser()
    parser.page.path = path
    try:
        parser.feed(path.read_text(encoding="utf-8"))
        parser.close()
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError(f"cannot read UTF-8 HTML {path}: {error}") from error
    return parser.page


def audit_page(page: Page, indexable: bool) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    if not page.lang:
        results.append(finding("error", "html-lang-missing", page.path, "document has no html[lang]"))
    elif LANGUAGE_TAG.fullmatch(page.lang) is None:
        results.append(finding("error", "html-lang-invalid", page.path, f"invalid language tag: {page.lang!r}"))

    if len(page.titles) != 1 or not page.titles[0]:
        results.append(finding("error", "title-invalid", page.path, "document needs exactly one non-empty title"))
    if len(page.descriptions) != 1 or not page.descriptions[0]:
        results.append(finding("warning", "description-invalid", page.path, "document should have exactly one useful meta description"))
    if page.h1_count == 0:
        results.append(finding("warning", "h1-missing", page.path, "document has no h1; confirm the visible heading structure is descriptive"))
    if page.anchors_without_href:
        results.append(finding("error", "anchor-without-href", page.path, f"{page.anchors_without_href} anchor(s) have no crawlable href"))
    if page.javascript_links:
        results.append(finding("error", "javascript-link", page.path, f"{page.javascript_links} anchor(s) use javascript: URLs"))

    if len(page.canonicals) > 1:
        results.append(finding("error", "canonical-multiple", page.path, "document has multiple canonical links"))
    if indexable and not page.canonicals:
        results.append(finding("error", "canonical-missing", page.path, "indexable audit requires a canonical URL"))
    for canonical in page.canonicals:
        if not is_absolute_web_url(canonical):
            results.append(finding("error", "canonical-invalid", page.path, f"canonical must be absolute HTTP(S): {canonical!r}"))

    if indexable and any(blocks_indexing(value) for value in page.robots):
        results.append(finding("error", "indexable-noindex", page.path, "indexable audit found a noindex or none directive"))

    seen_languages: set[str] = set()
    for language, href in page.alternates:
        normalized = language.casefold()
        if normalized != "x-default" and LANGUAGE_TAG.fullmatch(language) is None:
            results.append(finding("error", "hreflang-invalid", page.path, f"invalid hreflang: {language!r}"))
        if normalized in seen_languages:
            results.append(finding("error", "hreflang-duplicate", page.path, f"duplicate hreflang: {language!r}"))
        seen_languages.add(normalized)
        if not is_absolute_web_url(href):
            results.append(finding("error", "hreflang-url-invalid", page.path, f"alternate URL must be absolute HTTP(S): {href!r}"))

    for index, payload in enumerate(page.jsonld):
        try:
            value: Any = json.loads(payload)
        except json.JSONDecodeError as error:
            results.append(finding("error", "jsonld-invalid", page.path, f"JSON-LD block {index} is invalid JSON: {error.msg}"))
            continue
        if not isinstance(value, (dict, list)):
            results.append(finding("error", "jsonld-root", page.path, f"JSON-LD block {index} root must be object or array"))
    return results


def audit(target: Path, indexable: bool, max_files: int, max_bytes: int) -> tuple[list[Page], list[dict[str, str]]]:
    pages = [parse_page(path, max_bytes) for path in collect_files(target, max_files)]
    results = [item for page in pages for item in audit_page(page, indexable)]
    title_owners: dict[str, list[Path]] = {}
    canonical_owners: dict[str, list[Path]] = {}
    for page in pages:
        if len(page.titles) == 1 and page.titles[0]:
            title_owners.setdefault(page.titles[0].casefold(), []).append(page.path)
        if len(page.canonicals) == 1:
            canonical_owners.setdefault(page.canonicals[0], []).append(page.path)
    for owners in title_owners.values():
        if len(owners) > 1:
            for owner in owners:
                results.append(finding("warning", "title-duplicate", owner, "title is duplicated in the audited set"))
    for canonical, owners in canonical_owners.items():
        if len(owners) > 1:
            for owner in owners:
                results.append(finding("error", "canonical-duplicate", owner, f"canonical is shared by multiple pages: {canonical}"))
    return pages, results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--indexable", action="store_true", help="require canonical and reject noindex for intentionally indexable pages")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--max-files", type=int, default=MAX_DEFAULT_FILES)
    parser.add_argument("--max-bytes", type=int, default=MAX_DEFAULT_BYTES)
    args = parser.parse_args()
    if args.max_files < 1 or args.max_bytes < 1:
        parser.error("limits must be positive")
    try:
        pages, results = audit(args.target.expanduser(), args.indexable, args.max_files, args.max_bytes)
    except (OSError, ValueError) as error:
        print(f"search audit failed: {error}", file=sys.stderr)
        return 2
    errors = sum(item["severity"] == "error" for item in results)
    warnings = sum(item["severity"] == "warning" for item in results)
    if args.format == "json":
        print(json.dumps({"pages": len(pages), "errors": errors, "warnings": warnings, "findings": results}, ensure_ascii=False, indent=2))
    else:
        for item in results:
            print(f"{item['severity'].upper()} {item['file']} [{item['code']}] {item['message']}")
        print(f"search audit: {len(pages)} page(s), {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
