#!/usr/bin/env python3
"""Regression tests for the optional, fail-soft Pretext adapter."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "wow-frontend-design" / "scripts" / "pretext_typography_adapter.mjs"


class PretextTypographyAdapterTests(unittest.TestCase):
    def run_node(self, expression: str) -> dict:
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", expression],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)

    def test_missing_package_is_explicitly_unavailable(self) -> None:
        result = self.run_node(
            f"import {{ measureTypographyCandidate }} from {json.dumps(ADAPTER.as_uri())};"
            "console.log(JSON.stringify(await measureTypographyCandidate({text:'繁中段落',font:'16px Arial',maxWidth:240,lineHeight:24})));"
        )
        self.assertIn(result["status"], {"unavailable", "measured"})
        if result["status"] == "unavailable":
            self.assertEqual("@chenglou/pretext", result["package"])

    def test_canvas_capability_failure_is_fail_soft(self) -> None:
        result = self.run_node(
            f"import {{ measureTypographyCandidate }} from {json.dumps(ADAPTER.as_uri())};"
            "console.log(JSON.stringify(await measureTypographyCandidate({text:'繁中段落',font:'16px Arial',maxWidth:240,lineHeight:24})));"
        )
        if result["status"] == "unavailable":
            self.assertEqual("@chenglou/pretext", result["package"])
            self.assertIn("canvas", result["reason"].lower())

    def test_measurement_with_canvas_capability(self) -> None:
        result = self.run_node(
            "globalThis.OffscreenCanvas=class{getContext(){return {font:'',measureText(value){return {width:[...value].length*8}}}}};"
            f"const {{ measureTypographyCandidate }}=await import({json.dumps(ADAPTER.as_uri())});"
            "console.log(JSON.stringify(await measureTypographyCandidate({text:'alpha beta gamma',font:'16px Arial',maxWidth:64,lineHeight:24})));"
        )
        self.assertEqual("measured", result["status"])
        self.assertGreaterEqual(result["lineCount"], 2)
        self.assertEqual(result["lineCount"], result["measuredLineCount"])
        self.assertEqual(result["lineCount"] * 24, result["height"])
        self.assertEqual(
            {
                "whiteSpace": "normal",
                "wordBreak": "normal",
                "overflowWrap": "break-word",
                "writingMode": "horizontal-tb",
                "letterSpacing": 0,
            },
            result["appliedOptions"],
        )
        self.assertIn("not-rendered-layout-evidence", result["limitations"])
        self.assertIn("unverified", result["claimBoundary"])

    def test_unsupported_css_text_behaviors_fail_before_capability_lookup(self) -> None:
        for property_name, value in (
            ("whiteSpace", "nowrap"),
            ("wordBreak", "break-all"),
            ("overflowWrap", "normal"),
            ("overflowWrap", "anywhere"),
            ("writingMode", "vertical-rl"),
        ):
            with self.subTest(property_name=property_name, value=value):
                candidate = {
                    "text": "long-content-identifier",
                    "font": "16px Arial",
                    "maxWidth": 64,
                    "lineHeight": 24,
                    property_name: value,
                }
                result = self.run_node(
                    f"import {{ measureTypographyCandidate }} from {json.dumps(ADAPTER.as_uri())};"
                    f"console.log(JSON.stringify(await measureTypographyCandidate({json.dumps(candidate)})));"
                )
                self.assertEqual("invalid", result["status"])
                self.assertEqual("unsupported_css_text_behavior", result["reasonCode"])
                self.assertEqual(property_name, result["unsupported"][0]["property"])

    def test_invalid_letter_spacing_fails_before_capability_lookup(self) -> None:
        for value in ("normal", "1", None):
            with self.subTest(value=value):
                candidate = {
                    "text": "copy",
                    "font": "16px Arial",
                    "maxWidth": 64,
                    "lineHeight": 24,
                    "letterSpacing": value,
                }
                result = self.run_node(
                    f"import {{ measureTypographyCandidate }} from {json.dumps(ADAPTER.as_uri())};"
                    f"console.log(JSON.stringify(await measureTypographyCandidate({json.dumps(candidate)})));"
                )
                self.assertEqual("invalid", result["status"])
                self.assertIn("letterSpacing", result["reason"])

    def test_non_scalar_dimensions_and_empty_font_are_invalid(self) -> None:
        for overrides in (
            {"font": ""},
            {"font": "   "},
            {"maxWidth": True},
            {"maxWidth": [240]},
            {"lineHeight": False},
            {"lineHeight": [24]},
        ):
            with self.subTest(overrides=overrides):
                candidate = {
                    "text": "copy",
                    "font": "16px Arial",
                    "maxWidth": 240,
                    "lineHeight": 24,
                    **overrides,
                }
                result = self.run_node(
                    f"import {{ measureTypographyCandidate }} from {json.dumps(ADAPTER.as_uri())};"
                    f"console.log(JSON.stringify(await measureTypographyCandidate({json.dumps(candidate)})));"
                )
                self.assertEqual("invalid", result["status"])

    def test_explicit_supported_css_options_are_recorded(self) -> None:
        candidate = {
            "text": "alpha beta gamma",
            "font": "16px Arial",
            "maxWidth": "64",
            "lineHeight": "24",
            "whiteSpace": "pre-wrap",
            "wordBreak": "keep-all",
            "overflowWrap": "break-word",
            "writingMode": "horizontal-tb",
            "letterSpacing": 1,
        }
        result = self.run_node(
            "globalThis.OffscreenCanvas=class{getContext(){return {font:'',measureText(value){return {width:[...value].length*8}}}}};"
            f"const {{ measureTypographyCandidate }}=await import({json.dumps(ADAPTER.as_uri())});"
            f"console.log(JSON.stringify(await measureTypographyCandidate({json.dumps(candidate)})));"
        )
        self.assertEqual("measured", result["status"])
        self.assertEqual(
            {
                "whiteSpace": "pre-wrap",
                "wordBreak": "keep-all",
                "overflowWrap": "break-word",
                "writingMode": "horizontal-tb",
                "letterSpacing": 1,
            },
            result["appliedOptions"],
        )

    def test_result_limitations_cannot_pollute_later_measurements(self) -> None:
        result = self.run_node(
            "globalThis.OffscreenCanvas=class{getContext(){return {font:'',measureText(value){return {width:[...value].length*8}}}}};"
            f"const {{ measureTypographyCandidate }}=await import({json.dumps(ADAPTER.as_uri())});"
            "const candidate={text:'copy',font:'16px Arial',maxWidth:64,lineHeight:24};"
            "const first=await measureTypographyCandidate(candidate);"
            "first.limitations.length=0;"
            "const second=await measureTypographyCandidate(candidate);"
            "console.log(JSON.stringify(second));"
        )
        self.assertEqual("measured", result["status"])
        self.assertIn("not-rendered-layout-evidence", result["limitations"])

    def test_invalid_candidate_fails_before_capability_lookup(self) -> None:
        result = self.run_node(
            f"import {{ measureTypographyCandidate }} from {json.dumps(ADAPTER.as_uri())};"
            "console.log(JSON.stringify(await measureTypographyCandidate({text:'',font:'',maxWidth:0,lineHeight:0})));"
        )
        self.assertEqual("invalid", result["status"])


if __name__ == "__main__":
    unittest.main()
