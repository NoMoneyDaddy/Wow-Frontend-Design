#!/usr/bin/env python3
"""Reject network, navigation, import, and local-resource capabilities in eval output."""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path


CSS_URL = re.compile(r"(?is)\burl\s*\(\s*([^)]*?)\s*\)")
CSS_IMPORT = re.compile(r"(?i)@\s*import\b")
PROTOCOL_RELATIVE = re.compile(r'''(?s)["'`]\s*//[^/\s]''')
JS_SINKS = (
    (re.compile(r"(?i)\bfetch\s*\("), "fetch call"),
    (re.compile(r"(?i)\bnew\s+(?:XMLHttpRequest|WebSocket|EventSource|Worker|SharedWorker|Image)\b"), "network-capable constructor"),
    (re.compile(r"(?i)\b(?:XMLHttpRequest|WebSocket|EventSource|importScripts)\s*\("), "network-capable API"),
    (re.compile(r"(?i)\bnavigator\s*\.\s*sendBeacon\s*\("), "sendBeacon call"),
    (re.compile(r"(?i)\b(?:window|document)\s*\.\s*open\s*\("), "window/document open"),
    (re.compile(r'''(?i)\bcreateElement\s*\(\s*["'](?:img|script|link|iframe|object|embed|source|video|audio)["']'''), "dynamic resource element"),
    (re.compile(r"(?i)\.\s*(?:src|srcset|href|action|formAction|poster)\s*="), "dynamic resource assignment"),
    (re.compile(r'''(?i)\[\s*["'](?:src|srcset|href|action|formaction|poster)["']\s*\]\s*='''), "dynamic resource bracket assignment"),
    (re.compile(r'''(?i)\bsetAttribute\s*\(\s*["'](?:src|srcset|href|action|formaction|poster)["']'''), "dynamic resource attribute"),
    (re.compile(r"(?i)\b(?:serviceWorker\s*\.\s*register|document\s*\.\s*write|insertAdjacentHTML)\s*\("), "dynamic document/resource API"),
    (re.compile(r"(?i)\bimport\s*\("), "dynamic import"),
    (re.compile(r'''(?im)^\s*(?:import|export)\b[^\n;]*\bfrom\s*["']'''), "module import"),
)


def css_unescape(value: str) -> str:
    def replace_hex(match: re.Match[str]) -> str:
        try:
            point = int(match.group(1), 16)
            return chr(point) if point <= 0x10FFFF else "�"
        except ValueError:
            return "�"

    value = re.sub(r"\\([0-9A-Fa-f]{1,6})(?:\r\n|[\t\n\f\r ])?", replace_hex, value)
    return re.sub(r"\\([^\r\n0-9A-Fa-f])", r"\1", value)


def normalized(value: str) -> str:
    return re.sub(r"[\x00-\x20\x7f]+", "", value).casefold()


def scan_css(value: str, source: str, issues: list[str]) -> None:
    decoded = css_unescape(value)
    active_css = re.sub(r"/\*.*?\*/", "", decoded, flags=re.DOTALL)
    if CSS_IMPORT.search(active_css):
        issues.append(f"{source}: CSS @import is forbidden")
    for match in CSS_URL.finditer(active_css):
        target = match.group(1).strip().strip('"\'')
        if not normalized(target).startswith("#"):
            issues.append(f"{source}: CSS url() may only reference an in-document fragment")


def scan_js(value: str, source: str, issues: list[str]) -> None:
    if PROTOCOL_RELATIVE.search(value):
        issues.append(f"{source}: protocol-relative string is forbidden")
    scan_css(value, source, issues)
    for pattern, label in JS_SINKS:
        if pattern.search(value):
            issues.append(f"{source}: {label} is forbidden")


class OutputParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.issues: list[str] = []
        self.script_depth = 0
        self.style_depth = 0
        self.script_parts: list[str] = []
        self.style_parts: list[str] = []

    def add(self, message: str) -> None:
        line, column = self.getpos()
        self.issues.append(f"index.html:{line}:{column + 1}: {message}")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        name = tag.casefold()
        lowered = [(key.casefold(), value or "") for key, value in attrs]
        values = {key: value for key, value in lowered}
        if len(values) != len(lowered):
            self.add(f"duplicate attributes on <{name}> are forbidden")
        if name in {"base", "iframe", "object", "embed", "portal"}:
            self.add(f"resource-capable <{name}> is forbidden")
        if name == "meta" and values.get("http-equiv", "").strip().casefold() == "refresh":
            self.add("meta refresh is forbidden")
        if name == "script":
            self.script_depth += 1
            if self.script_depth == 1:
                self.script_parts = []
        if name == "style":
            self.style_depth += 1
            if self.style_depth == 1:
                self.style_parts = []
        rels = {item.casefold() for item in values.get("rel", "").split()}
        for attribute, raw in lowered:
            value = raw.strip()
            if attribute in {"action", "formaction"}:
                if value and not normalized(value).startswith("#"):
                    self.add(f"{attribute} may only be empty or an in-document fragment")
            elif attribute == "srcdoc":
                self.add("srcdoc is forbidden")
            elif attribute == "style":
                scan_css(value, "index.html style attribute", self.issues)
            elif attribute.startswith("on"):
                scan_js(value, f"index.html {attribute} handler", self.issues)
            elif attribute in {"src", "srcset", "imagesrcset", "poster", "data", "background", "ping", "manifest", "xlink:href"}:
                if not (name == "script" and attribute == "src" and normalized(value) in {"app.js", "./app.js"}):
                    self.add(f"<{name}> {attribute} resource is forbidden: {value!r}")
            elif attribute == "href":
                stylesheet = name == "link" and "stylesheet" in rels and normalized(value) in {"styles.css", "./styles.css"}
                fragment = name in {"a", "use", "textpath"} and normalized(value).startswith("#")
                if not (stylesheet or fragment):
                    self.add(f"<{name}> href is not an allowed stylesheet or fragment: {value!r}")

    def handle_endtag(self, tag: str) -> None:
        name = tag.casefold()
        if name == "script" and self.script_depth:
            self.script_depth -= 1
            if self.script_depth == 0:
                scan_js("".join(self.script_parts), "index.html inline script", self.issues)
        elif name == "style" and self.style_depth:
            self.style_depth -= 1
            if self.style_depth == 0:
                scan_css("".join(self.style_parts), "index.html style block", self.issues)

    def handle_data(self, data: str) -> None:
        if self.script_depth:
            self.script_parts.append(data)
        if self.style_depth:
            self.style_parts.append(data)


def validate(paths: list[Path]) -> list[str]:
    if [path.name for path in paths] != ["index.html", "styles.css", "app.js"]:
        return ["paths must be index.html, styles.css, and app.js in that order"]
    texts: list[str] = []
    issues: list[str] = []
    for path in paths:
        if path.is_symlink() or not path.is_file():
            issues.append(f"{path.name}: missing, non-file, or symlink")
            texts.append("")
            continue
        size = path.stat().st_size
        if not 1 <= size <= 1_048_576:
            issues.append(f"{path.name}: size outside 1..1048576 bytes")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            issues.append(f"{path.name}: invalid strict UTF-8: {error}")
            text = ""
        texts.append(text)
        if "\x00" in text:
            issues.append(f"{path.name}: NUL byte is forbidden")
    html, css, js = texts
    parser = OutputParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception as error:
        issues.append(f"index.html: parser rejected output: {error}")
    if parser.script_depth or parser.style_depth:
        issues.append("index.html: unclosed script/style block is forbidden")
    issues.extend(parser.issues)
    scan_css(css, "styles.css", issues)
    scan_js(js, "app.js", issues)
    return list(dict.fromkeys(issues))


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: validate_isolated_web_output.py index.html styles.css app.js", file=sys.stderr)
        return 2
    issues = validate([Path(value) for value in sys.argv[1:]])
    for issue in issues:
        print(issue, file=sys.stderr)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
