#!/usr/bin/env python3
"""Contract and browser tests for the bounded v7 breakpoint probe."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "evals" / "playwright_v7_breakpoint_probe.cjs"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class V7BreakpointProbeTests(unittest.TestCase):
    def test_node_contract_and_bounded_transition_policy(self) -> None:
        script = r"""
const assert = require('node:assert');
const probe = require('./evals/playwright_v7_breakpoint_probe.cjs');
const contract = { ...probe.loadContract().value, max_samples: 48, max_depth: 11, max_transitions: 8 };
(async () => {
  const calls = [];
  const same = await probe.locateTransitions([320, 1440], async (width) => {
    calls.push(width); return { signature: 'same' };
  }, contract);
  assert.equal(same.status, 'complete');
  assert.deepEqual(calls, [320, 1440]);
  assert.deepEqual(same.transitions, []);

  const bounded = await probe.locateTransitions([320, 1440], async (width) => ({
    signature: width < 600 ? 'narrow' : 'wide'
  }), contract);
  assert.equal(bounded.status, 'complete');
  assert.deepEqual(bounded.transitions.map((item) => [item.lower_width, item.upper_width]), [[599, 600]]);

  const capped = await probe.locateTransitions([320, 1440], async (width) => ({
    signature: width < 600 ? 'narrow' : 'wide'
  }), { ...contract, max_samples: 2 });
  assert.equal(capped.status, 'unavailable');
  assert.equal(capped.reason_code, 'sample_budget_exhausted');
})();
"""
        completed = subprocess.run(
            ["node", "-e", script], cwd=ROOT, text=True, capture_output=True, timeout=20
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_browser_probe_finds_transition_without_screenshot_or_source_leak(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            design = target / "DESIGN.md"
            route = target / "index.html"
            manifest = target / "run-manifest.json"
            spec = Path(directory) / "hidden-spec.json"
            output = Path(directory) / "breakpoints.json"
            design.write_text("# Design\n", encoding="utf-8")
            route.write_text(
                """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<style>
*{box-sizing:border-box}body{margin:0}.layout{display:grid;gap:16px}.secret-selector{inline-size:auto}
@media (min-width:600px){.layout{grid-template-columns:1fr 1fr}}
@media (max-width:479px){.overflow-risk{inline-size:700px}}
</style></head><body><main class="layout"><h1 class="secret-selector">不可外洩產品文字</h1>
<section>甲</section><section>乙</section></main><div class="overflow-risk">風險</div></body></html>""",
                encoding="utf-8",
            )
            outputs = [
                {"path": item.name, "bytes": item.stat().st_size, "sha256": _sha(item)}
                for item in (design, route)
            ]
            manifest.write_text(
                json.dumps({"schema_version": 1, "status": "completed", "outputs": outputs}),
                encoding="utf-8",
            )
            spec.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "caseId": "case-one",
                        "state": "base",
                        "steps": [],
                        "assertions": [],
                        "targets": [
                            {
                                "id": "layout-title",
                                "selector": ".secret-selector",
                                "ownerSelector": ".layout",
                                "role": "heading",
                                "mode": "product",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    "node", str(PROBE),
                    "--variant", "candidate",
                    "--case-id", "case-one",
                    "--state", "base",
                    "--route", str(route),
                    "--target-manifest", str(manifest),
                    "--spec", str(spec),
                    "--output", str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=120,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("complete", report["status"])
            brackets = {(item["lower_width"], item["upper_width"]) for item in report["transitions"]}
            self.assertIn((599, 600), brackets)
            self.assertTrue(
                any(item["code"] == "breakpoint_horizontal_overflow" for item in report["findings"])
            )
            serialized = output.read_text(encoding="utf-8")
            self.assertNotIn(".secret-selector", serialized)
            self.assertNotIn("不可外洩產品文字", serialized)
            self.assertNotIn("screenshot", " ".join(str(path) for path in Path(directory).iterdir()).lower())
            self.assertFalse(any(path.suffix == ".png" for path in Path(directory).rglob("*")))

    def test_manifest_drift_fails_before_browser_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            route = root / "index.html"
            design = root / "DESIGN.md"
            manifest = root / "run-manifest.json"
            spec = root / "spec.json"
            output = root / "out.json"
            route.write_text("<main><h1>內容</h1></main>", encoding="utf-8")
            design.write_text("# Design\n", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "status": "completed",
                        "outputs": [
                            {"path": "DESIGN.md", "bytes": design.stat().st_size, "sha256": _sha(design)},
                            {"path": "index.html", "bytes": route.stat().st_size, "sha256": "0" * 64},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            spec.write_text("{}", encoding="utf-8")
            completed = subprocess.run(
                [
                    "node", str(PROBE), "--variant", "candidate", "--case-id", "case-one",
                    "--state", "base", "--route", str(route), "--target-manifest", str(manifest),
                    "--spec", str(spec), "--output", str(output),
                ],
                cwd=ROOT, text=True, capture_output=True, timeout=20,
            )
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("receipt drifted", completed.stderr)
            self.assertFalse(output.exists())

    def test_symlink_ancestor_is_rejected_and_stable_read_binds_one_byte_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real"
            real.mkdir()
            source = real / "spec.json"
            source.write_text('{"version":1}', encoding="utf-8")
            link = root / "linked"
            link.symlink_to(real, target_is_directory=True)
            script = r"""
const assert = require('node:assert');
const fs = require('node:fs');
const crypto = require('node:crypto');
const probe = require('./evals/playwright_v7_breakpoint_probe.cjs');
const [source, linked] = process.argv.slice(1);
const snapshot = probe.stableFile(source, 'fixture');
const parsed = JSON.parse(snapshot.bytes.toString('utf8'));
fs.writeFileSync(source, '{"version":2}');
assert.equal(parsed.version, 1);
assert.equal(snapshot.sha256, crypto.createHash('sha256').update(snapshot.bytes).digest('hex'));
assert.throws(() => probe.stableFile(linked, 'linked fixture'), /must not traverse a symlink/);
"""
            completed = subprocess.run(
                ["node", "-e", script, str(source), str(link / "spec.json")],
                cwd=ROOT, text=True, capture_output=True, timeout=20,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)


if __name__ == "__main__":
    unittest.main()
