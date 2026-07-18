#!/usr/bin/env python3
"""Tests for the isolated static-site capability boundary."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "evals" / "validate_isolated_web_output.py"
SPEC = importlib.util.spec_from_file_location("validate_isolated_web_output", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class IsolatedWebOutputTests(unittest.TestCase):
    def validate(self, html: str, js: str = "void 0;") -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = [root / "index.html", root / "styles.css", root / "app.js"]
            files[0].write_text(html, encoding="utf-8")
            files[1].write_text("body { color: #111; }", encoding="utf-8")
            files[2].write_text(js, encoding="utf-8")
            return validator.validate(files)

    def validate_with_css(self, css: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = [root / "index.html", root / "styles.css", root / "app.js"]
            files[0].write_text("<!doctype html><main></main>", encoding="utf-8")
            files[1].write_text(css, encoding="utf-8")
            files[2].write_text("void 0;", encoding="utf-8")
            return validator.validate(files)

    def test_same_document_navigation_is_allowed(self) -> None:
        html = '<!doctype html><form action="#results"><button>查詢</button></form><a href="#results">結果</a>'
        self.assertEqual([], self.validate(html, 'location.hash = "#results";'))

    def test_relative_or_external_form_action_is_rejected(self) -> None:
        issues = self.validate('<!doctype html><form action="/submit"><button>送出</button></form>')
        self.assertTrue(any("action may only" in issue for issue in issues))
        external = self.validate('<!doctype html><form action="https://example.invalid"><button>送出</button></form>')
        self.assertTrue(any("action may only" in issue for issue in external))

    def test_inert_uri_text_is_allowed_but_css_resource_loading_is_rejected(self) -> None:
        self.assertEqual([], self.validate_with_css("/* file: styles.css; https://example.invalid */ body { color: #111; }"))
        issues = self.validate_with_css("body { background: url(https://example.invalid/a.png); }")
        self.assertTrue(any("CSS url()" in issue for issue in issues))

    def test_network_api_remains_rejected(self) -> None:
        issues = self.validate("<!doctype html><main></main>", 'fetch("/api");')
        self.assertTrue(any("fetch call" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
