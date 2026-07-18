#!/usr/bin/env python3
"""Tests for the bounded search/discovery HTML audit."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wow-frontend-design" / "scripts"))

import search_discovery_audit


VALID = """<!doctype html>
<html lang="zh-Hant"><head><title>測試頁</title>
<meta name="description" content="清楚描述">
<link rel="canonical" href="https://example.test/zh-hant/page">
</head><body><h1>測試頁</h1><a href="/next">下一頁</a></body></html>"""


class SearchDiscoveryAuditTests(unittest.TestCase):
    def write(self, root: Path, name: str, content: str) -> Path:
        target = root / name
        target.write_text(content, encoding="utf-8")
        return target

    def test_valid_indexable_page_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            page = self.write(Path(temp), "index.html", VALID)
            pages, findings = search_discovery_audit.audit(page, True, 10, 100_000)
            self.assertEqual(1, len(pages))
            self.assertEqual([], findings)

    def test_indexable_page_requires_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            page = self.write(Path(temp), "index.html", VALID.replace('<link rel="canonical" href="https://example.test/zh-hant/page">', ""))
            _, findings = search_discovery_audit.audit(page, True, 10, 100_000)
            self.assertTrue(any(item["code"] == "canonical-missing" for item in findings))

    def test_noindex_indexable_page_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            html = VALID.replace("</head>", '<meta name="robots" content="noindex, follow"></head>')
            page = self.write(Path(temp), "index.html", html)
            _, findings = search_discovery_audit.audit(page, True, 10, 100_000)
            self.assertTrue(any(item["code"] == "indexable-noindex" for item in findings))

    def test_none_indexable_page_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            html = VALID.replace("</head>", '<meta name="robots" content="none"></head>')
            page = self.write(Path(temp), "index.html", html)
            _, findings = search_discovery_audit.audit(page, True, 10, 100_000)
            self.assertTrue(any(item["code"] == "indexable-noindex" for item in findings))

    def test_none_non_indexable_page_is_not_a_conflicting_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            html = VALID.replace("</head>", '<meta name="robots" content="none"></head>')
            page = self.write(Path(temp), "index.html", html)
            _, findings = search_discovery_audit.audit(page, False, 10, 100_000)
            self.assertFalse(any(item["code"] == "indexable-noindex" for item in findings))

    def test_description_and_h1_are_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            html = VALID.replace('<meta name="description" content="清楚描述">', "").replace("<h1>測試頁</h1>", "")
            page = self.write(Path(temp), "index.html", html)
            _, findings = search_discovery_audit.audit(page, False, 10, 100_000)
            self.assertEqual({"description-invalid", "h1-missing"}, {item["code"] for item in findings})
            self.assertTrue(all(item["severity"] == "warning" for item in findings))

    def test_invalid_jsonld_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            html = VALID.replace("</head>", '<script type="application/ld+json">{bad}</script></head>')
            page = self.write(Path(temp), "index.html", html)
            _, findings = search_discovery_audit.audit(page, False, 10, 100_000)
            self.assertTrue(any(item["code"] == "jsonld-invalid" for item in findings))

    def test_javascript_anchor_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            page = self.write(Path(temp), "index.html", VALID.replace("/next", "javascript:void(0)"))
            _, findings = search_discovery_audit.audit(page, False, 10, 100_000)
            self.assertTrue(any(item["code"] == "javascript-link" for item in findings))

    def test_symlink_root_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            page = self.write(root, "index.html", VALID)
            link = root / "linked.html"
            link.symlink_to(page)
            with self.assertRaises(ValueError):
                search_discovery_audit.collect_files(link, 10)

    def test_duplicate_canonical_fails_set(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write(root, "one.html", VALID)
            self.write(root, "two.html", VALID.replace("測試頁", "第二頁"))
            _, findings = search_discovery_audit.audit(root, True, 10, 100_000)
            self.assertEqual(2, sum(item["code"] == "canonical-duplicate" for item in findings))


if __name__ == "__main__":
    unittest.main()
