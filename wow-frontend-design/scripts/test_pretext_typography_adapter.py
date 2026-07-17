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

    def test_invalid_candidate_fails_before_capability_lookup(self) -> None:
        result = self.run_node(
            f"import {{ measureTypographyCandidate }} from {json.dumps(ADAPTER.as_uri())};"
            "console.log(JSON.stringify(await measureTypographyCandidate({text:'',font:'',maxWidth:0,lineHeight:0})));"
        )
        self.assertEqual("invalid", result["status"])


if __name__ == "__main__":
    unittest.main()
