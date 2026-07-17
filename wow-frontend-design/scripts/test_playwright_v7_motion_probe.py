#!/usr/bin/env python3
"""Browser tests for the bounded normal/reduce motion sidecar."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "evals" / "playwright_v7_motion_probe.cjs"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(root: Path, html: str) -> tuple[Path, Path, Path]:
    target = root / "target"
    target.mkdir()
    design = target / "DESIGN.md"
    route = target / "index.html"
    manifest = target / "run-manifest.json"
    spec = root / "客戶名稱-不可外洩文案.json"
    design.write_text("# Design\n", encoding="utf-8")
    route.write_text(html, encoding="utf-8")
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "completed",
                "outputs": [
                    {"path": item.name, "bytes": item.stat().st_size, "sha256": _sha(item)}
                    for item in (design, route)
                ],
            }
        ),
        encoding="utf-8",
    )
    spec.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "caseId": "case-one",
                "state": "base",
                "steps": [],
                "assertions": [
                    {"id": "required-status", "selector": ".secret-required", "type": "visible"}
                ],
                "targets": [
                    {
                        "id": "motion-title",
                        "selector": ".secret-title",
                        "ownerSelector": "main",
                        "role": "heading",
                        "mode": "product",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return route, manifest, spec


def _run(route: Path, manifest: Path, spec: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
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


class V7MotionProbeTests(unittest.TestCase):
    def test_normal_reduce_regression_requires_two_fresh_replays_without_source_leak(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            route, manifest, spec = _fixture(
                root,
                """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><style>
@keyframes drift{from{transform:translateX(0)}to{transform:translateX(20px)}}
.secret-title{animation:drift 5s linear infinite}.secret-required{display:block}
@media (prefers-reduced-motion:reduce){.secret-title{animation:none}.secret-required{display:none}}
</style></head><body><main><h1 class="secret-title">不可外洩產品文字</h1>
<p class="secret-required">必要狀態</p></main></body></html>""",
            )
            output = root / "motion.json"
            completed = _run(route, manifest, spec, output)
            self.assertEqual(0, completed.returncode, completed.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("complete", report["motion"]["status"])
            self.assertEqual(8, report["coverage"]["sample_count"])
            self.assertEqual(
                [390, 1024],
                [item["width"] for item in report["findings"] if item["code"] == "reduced_motion_task_regression"],
            )
            self.assertTrue(all(item["replays"] == 2 for item in report["findings"]))
            serialized = output.read_text(encoding="utf-8")
            self.assertNotIn(".secret-title", serialized)
            self.assertNotIn(".secret-required", serialized)
            self.assertNotIn("不可外洩產品文字", serialized)
            self.assertNotIn(spec.name, serialized)
            self.assertEqual("hidden-spec", report["subject"]["spec"])
            self.assertFalse(any(path.suffix in {".png", ".zip", ".webm"} for path in root.rglob("*")))
            schema_check = subprocess.run(
                [
                    "node", "-e",
                    """const fs=require('node:fs');const p=require(process.argv[1]);
const report=JSON.parse(fs.readFileSync(process.argv[2]));const contract=p.loadContract().value;
p.validateMotionReport(report,contract);const rejects=(mutate)=>{const copy=structuredClone(report);mutate(copy);
try{p.validateMotionReport(copy,contract);return false}catch{return true}};
if(!rejects(r=>{r.debug='forbidden'})||!rejects(r=>{r.coverage.sample_count+=1})
||!rejects(r=>{r.motion.observations[1].width=r.motion.observations[0].width}))process.exitCode=2;""",
                    str(PROBE), str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=20,
            )
            self.assertEqual(0, schema_check.returncode, schema_check.stderr)

    def test_no_observed_motion_is_not_applicable_and_does_not_run_reduce_lane(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            route, manifest, spec = _fixture(
                root,
                """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"></head>
<body><main><h1 class="secret-title">靜態內容</h1><p class="secret-required">狀態</p></main></body></html>""",
            )
            output = root / "motion.json"
            completed = _run(route, manifest, spec, output)
            self.assertEqual(0, completed.returncode, completed.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("not_applicable", report["motion"]["status"])
            self.assertEqual(2, report["coverage"]["sample_count"])
            self.assertEqual([], report["findings"])
            self.assertTrue(all(item["reduce"] is None for item in report["motion"]["observations"]))

    def test_animation_budget_exhaustion_is_unavailable_not_clean(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nodes = "".join(f'<i class="moving">{index}</i>' for index in range(65))
            route, manifest, spec = _fixture(
                root,
                f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><style>
@keyframes drift{{from{{opacity:.8}}to{{opacity:1}}}}.moving{{animation:drift 5s infinite}}
</style></head><body><main><h1 class="secret-title">標題</h1><p class="secret-required">狀態</p>{nodes}</main></body></html>""",
            )
            output = root / "motion.json"
            completed = _run(route, manifest, spec, output)
            self.assertEqual(2, completed.returncode, completed.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("unavailable", report["status"])
            self.assertEqual("animation_budget_exhausted", report["coverage"]["reason_code"])
            self.assertEqual([], report["findings"])

    def test_noncanonical_manifest_filename_is_rejected_without_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            route, manifest, spec = _fixture(
                root,
                """<!doctype html><html lang="zh-Hant"><body><main>
<h1 class="secret-title">標題</h1><p class="secret-required">狀態</p></main></body></html>""",
            )
            renamed = manifest.with_name("客戶名稱-不可外洩文案.json")
            manifest.rename(renamed)
            output = root / "motion.json"
            completed = _run(route, renamed, spec, output)
            self.assertNotEqual(0, completed.returncode)
            self.assertFalse(output.exists())

    def test_overflow_replay_without_normal_motion_cannot_confirm_finding(self) -> None:
        script = """const assert=require('node:assert/strict');const p=require(process.argv[1]);
const normal={assertions_passed:true,horizontal_overflow:false,motion:{total:1}};
const reduce={assertions_passed:true,horizontal_overflow:true,motion:{total:0}};
const normalReplay={assertions_passed:true,horizontal_overflow:false,motion:{total:0}};
const reduceReplay={assertions_passed:true,horizontal_overflow:true,motion:{total:0}};
assert.deepEqual(p.confirmedRegressionCodes(normal,reduce,normalReplay,reduceReplay),[]);"""
        completed = subprocess.run(
            ["node", "-e", script, str(PROBE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=20,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)


if __name__ == "__main__":
    unittest.main()
