#!/usr/bin/env python3
"""Regression tests for the evaluator-owned semantic HTML release gate."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from evals.html_semantic_gate import run_html_semantic_gate


class HtmlSemanticGateTests(unittest.TestCase):
    def test_rejects_invalid_interactive_html_with_bounded_findings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                "<!doctype html><html lang='en'><head><title>Example</title></head>"
                "<body><main><button><div>Bad child</div></button></main></body></html>",
                encoding="utf-8",
            )

            receipt = run_html_semantic_gate(stage, ("index.html",), 30)

        self.assertEqual(1, receipt["schema_version"])
        self.assertEqual("rejected", receipt["status"])
        self.assertEqual("semantic-html", receipt["claim_boundary"])
        self.assertEqual("vnu-jar", receipt["tool"]["package"])
        self.assertEqual(1, receipt["finding_count"])
        finding = receipt["outputs"][0]["findings"][0]
        self.assertEqual("index.html", finding["path"])
        self.assertIn("button", finding["message"])
        self.assertNotIn(str(stage), str(receipt))

    def test_accepts_semantically_valid_html(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text(
                "<!doctype html><html lang='en'><head><title>Example</title></head>"
                "<body><main><button><span>Good child</span></button></main></body></html>",
                encoding="utf-8",
            )

            receipt = run_html_semantic_gate(stage, ("index.html",), 30)

        self.assertEqual("passed", receipt["status"])
        self.assertEqual(0, receipt["finding_count"])
        self.assertEqual([], receipt["outputs"][0]["findings"])

    def test_rejects_non_html_scope_before_running_validator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "DESIGN.md").write_text("# Design\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "HTML outputs only"):
                run_html_semantic_gate(stage, ("DESIGN.md",), 30)


if __name__ == "__main__":
    unittest.main()
