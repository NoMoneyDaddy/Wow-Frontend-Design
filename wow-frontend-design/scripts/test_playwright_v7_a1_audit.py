#!/usr/bin/env python3
"""Integration tests for the isolated v7-A1 browser auditor."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDITOR = ROOT / "evals" / "playwright_v7_a1_audit.cjs"
FIXTURE = ROOT / "evals" / "fixtures" / "v7-a1-typography.html"


class PlaywrightV7A1AuditTests(unittest.TestCase):
    def test_profile_inventory_contains_six_distinct_compositions(self) -> None:
        source = f"""
const {{ PROFILES }} = require({json.dumps(str(AUDITOR))});
process.stdout.write(JSON.stringify(PROFILES));
"""
        completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True, check=True)
        profiles = json.loads(completed.stdout)
        self.assertEqual(
            {"desktop", "standard-desktop", "short-desktop", "tablet", "mobile", "compact-mobile"},
            set(profiles),
        )
        self.assertTrue(profiles["mobile"]["isMobile"])
        self.assertTrue(profiles["mobile"]["hasTouch"])
        self.assertEqual(3, profiles["mobile"]["deviceScaleFactor"])

    def test_fixture_produces_hashed_png_and_findings_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = {
                "schemaVersion": 1,
                "caseId": "fixture-case",
                "state": "base",
                "steps": [],
                "assertions": [{"id": "heading-visible", "type": "visible", "selector": "#heading-orphan"}],
                "targets": [{
                    "id": "orphan",
                    "selector": "#heading-orphan",
                    "ownerSelector": "#owner-orphan",
                    "role": "heading",
                    "mode": "product",
                }],
            }
            spec_path = root / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            screenshot = root / "fixture.png"
            output = root / "result.json"
            command = [
                "node", str(AUDITOR),
                "--url", FIXTURE.as_uri(),
                "--variant", "accepted",
                "--case-id", "fixture-case",
                "--state", "base",
                "--profile", "mobile",
                "--engine", "chromium",
                "--spec", str(spec_path),
                "--screenshot", str(screenshot),
                "--output", str(output),
            ]
            completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(2, completed.returncode, completed.stderr)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("findings", result["verdict"])
            self.assertEqual("accepted", result["identity"]["variant"])
            self.assertIn("page_horizontal_overflow", result["runtime"]["issues"])
            self.assertTrue(all("url" not in item for item in result["runtime"]["externalRequests"]))
            self.assertEqual("a1_heading_han_orphan", result["typography"]["issues"][0]["code"])
            self.assertNotIn("selector", json.dumps(result["runtime"]))
            self.assertNotIn("#heading-orphan", json.dumps(result["runtime"]))
            self.assertTrue(result["browser"]["profile"]["fullMobileEmulation"])
            self.assertEqual(3, result["browser"]["profile"]["deviceScaleFactor"])
            self.assertEqual(64, len(result["screenshot"]["sha256"]))
            self.assertGreater(result["screenshot"]["bytes"], 100)
            self.assertEqual(
                result["runtime"]["pageBounds"]["width"] * 3,
                result["screenshot"]["width"],
            )

    def test_non_loopback_network_target_is_rejected(self) -> None:
        source = f"""
const {{ targetUrl }} = require({json.dumps(str(AUDITOR))});
try {{ targetUrl('https://example.com/'); }}
catch (error) {{ process.stdout.write(error.message); process.exit(0); }}
process.exit(1);
"""
        completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, completed.returncode)
        self.assertIn("loopback", completed.stdout)

    def test_interaction_spec_requires_steps_and_assertions(self) -> None:
        contracts = (
            ("steps", [], [{"id": "dialog-visible", "type": "visible", "selector": "#dialog"}]),
            ("assertions", [{"id": "open-dialog", "action": "click", "selector": "#open"}], []),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for label, steps, assertions in contracts:
                with self.subTest(label=label):
                    spec = {
                        "schemaVersion": 1,
                        "caseId": "fixture-case",
                        "state": "interaction",
                        "steps": steps,
                        "assertions": assertions,
                        "targets": [],
                    }
                    spec_path = root / f"{label}.json"
                    spec_path.write_text(json.dumps(spec), encoding="utf-8")
                    source = f"""
const {{ loadSpec }} = require({json.dumps(str(AUDITOR))});
try {{ loadSpec({json.dumps(str(spec_path))}, 'fixture-case', 'interaction'); }}
catch (error) {{ process.stdout.write(error.message); process.exit(0); }}
process.exit(1);
"""
                    completed = subprocess.run(["node", "-e", source], cwd=ROOT, text=True, capture_output=True)
                    self.assertEqual(0, completed.returncode)
                    self.assertIn(f"spec {label} must contain 1..20 entries", completed.stdout)


if __name__ == "__main__":
    unittest.main()
