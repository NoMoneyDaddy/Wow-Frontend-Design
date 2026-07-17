#!/usr/bin/env python3
"""Regression tests for advisory-only cross-output template telemetry."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDITOR = ROOT / "wow-frontend-design" / "scripts" / "cross_output_template_audit.cjs"


class CrossOutputTemplateAuditTests(unittest.TestCase):
    def run_node(self, source: str) -> object:
        completed = subprocess.run(
            ["node", "-e", source],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)

    def test_text_and_accent_swap_produces_exact_cross_product_advisory(self) -> None:
        source = """
const { chromium } = require('playwright');
const { auditCrossOutputTemplates, collectMacroFingerprint } = require(__AUDITOR__);
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1200, height: 800 } });
  const render = async (title, accent, layout = 'same', hiddenMarkup = '') => {
    const regions = layout === 'same'
      ? `<section><form></form>${hiddenMarkup}</section><aside><ul><li></li></ul></aside>`
      : '<section><table><tr><td></td></tr></table></section><section><figure></figure></section>';
    await page.setContent(`<style>:root{--accent:${accent}}body{margin:0}header{height:80px}main{display:grid;grid-template-columns:${layout === 'same' ? '2fr 1fr' : '1fr'};gap:24px;height:500px}main>*{border-radius:12px}</style><header>${title}</header><main>${regions}</main><footer></footer>`);
    return page.evaluate(collectMacroFingerprint);
  };
  const a = await render('修繕派工', '#d9485f');
  const b = await render('版稅報表', '#3267d6', 'same', '<table style="display:none"><tr><td>hidden</td></tr></table>');
  const c = await render('館藏目錄', '#3c7a57', 'different');
  await browser.close();
  const row = (caseId, route, macroFingerprint) => ({ caseId, route, surface: 'primary', viewport: 'desktop', state: 'base', macroFingerprint });
  const result = auditCrossOutputTemplates({ schemaVersion: 1, cohort: 'model-run-1', observations: [row('repair', '/', a), row('royalty', '/', b), row('catalogue', '/', c)] });
  process.stdout.write(JSON.stringify({ same: JSON.stringify(a) === JSON.stringify(b), different: JSON.stringify(a) !== JSON.stringify(c), result }));
})().catch((error) => { console.error(error); process.exitCode = 1; });
""".replace("__AUDITOR__", json.dumps(str(AUDITOR)))
        observed = self.run_node(source)
        self.assertTrue(observed["same"])
        self.assertTrue(observed["different"])
        self.assertEqual("advisories_present", observed["result"]["status"])
        self.assertEqual(["repair", "royalty"], observed["result"]["advisories"][0]["caseIds"])
        self.assertNotIn("visualIssues", observed["result"])
        self.assertIn("unverified", observed["result"]["claimBoundary"])

    def test_same_product_routes_do_not_create_cross_output_advisory(self) -> None:
        fingerprint = {"version": 1, "landmarks": [], "mainFlow": {"display": "block", "flexDirection": "row", "gridTracks": [], "gap": 0}, "regions": [], "representationHistogram": []}
        source = f"""
const {{ auditCrossOutputTemplates }} = require({json.dumps(str(AUDITOR))});
const fingerprint = {json.dumps(fingerprint)};
const observations = ['/','/detail'].map((route) => ({{caseId:'same-product',route,surface:'primary',viewport:'desktop',state:'base',macroFingerprint:fingerprint}}));
process.stdout.write(JSON.stringify(auditCrossOutputTemplates({{schemaVersion:1,cohort:'run-2',observations}})));
"""
        result = self.run_node(source)
        self.assertEqual("no_exact_template_candidates", result["status"])
        self.assertEqual([], result["advisories"])

    def test_shared_primitive_with_different_region_graph_does_not_warn(self) -> None:
        first = {"version": 1, "landmarks": [{"role": "main", "depth": 0, "box": [0, 0, 1, 1]}], "mainFlow": {"display": "grid", "flexDirection": "row", "gridTracks": [1], "gap": 0}, "regions": [{"role": "table", "representation": "table", "box": [0, 0, 1, 1], "display": "block", "radius": "none"}], "representationHistogram": [["table", 1]]}
        second = {"version": 1, "landmarks": [{"role": "main", "depth": 0, "box": [0, 0, 1, 1]}], "mainFlow": {"display": "block", "flexDirection": "row", "gridTracks": [], "gap": 0}, "regions": [{"role": "form", "representation": "form", "box": [0, 0, 1, 0.5], "display": "block", "radius": "none"}, {"role": "table", "representation": "table", "box": [0, 0.5, 1, 0.5], "display": "block", "radius": "none"}], "representationHistogram": [["table", 1]]}
        source = f"""
const {{ auditCrossOutputTemplates }} = require({json.dumps(str(AUDITOR))});
const row = (caseId, macroFingerprint) => ({{caseId,route:'/',surface:'primary',viewport:'desktop',state:'base',macroFingerprint}});
process.stdout.write(JSON.stringify(auditCrossOutputTemplates({{schemaVersion:1,cohort:'run-3',observations:[row('a',{json.dumps(first)}),row('b',{json.dumps(second)})]}})));
"""
        result = self.run_node(source)
        self.assertEqual([], result["advisories"])

    def test_spacing_radius_and_track_ratio_tweaks_cannot_hide_dominant_template(self) -> None:
        first = {
            "version": 1,
            "landmarks": [{"role": "main", "depth": 0, "box": [0, 0, 1, 1]}],
            "mainFlow": {"display": "grid", "flexDirection": "row", "gridTracks": [0.65, 0.35], "gap": 0.02},
            "regions": [
                {"role": "region", "representation": "form", "box": [0, 0, 0.65, 1], "display": "block", "radius": "small"},
                {"role": "complementary", "representation": "list", "box": [0.67, 0, 0.33, 1], "display": "block", "radius": "small"},
            ],
            "representationHistogram": [["form", 1], ["ul", 1]],
        }
        second = {
            "version": 1,
            "landmarks": [{"role": "main", "depth": 0, "box": [0, 0, 1, 0.95]}],
            "mainFlow": {"display": "grid", "flexDirection": "row", "gridTracks": [0.6, 0.4], "gap": 0.05},
            "regions": [
                {"role": "region", "representation": "form", "box": [0, 0.05, 0.6, 0.9], "display": "block", "radius": "large"},
                {"role": "complementary", "representation": "list", "box": [0.65, 0.05, 0.35, 0.9], "display": "block", "radius": "none"},
            ],
            "representationHistogram": [["form", 1], ["ul", 1]],
        }
        source = f"""
const {{ auditCrossOutputTemplates }} = require({json.dumps(str(AUDITOR))});
const row = (caseId, macroFingerprint) => ({{caseId,route:'/',surface:'primary',viewport:'desktop',state:'base',macroFingerprint}});
process.stdout.write(JSON.stringify(auditCrossOutputTemplates({{schemaVersion:1,cohort:'near-1',observations:[row('repair',{json.dumps(first)}),row('royalty',{json.dumps(second)})]}})));
"""
        result = self.run_node(source)
        self.assertEqual("advisories_present", result["status"])
        self.assertEqual(1, len(result["advisories"]))
        advisory = result["advisories"][0]
        self.assertEqual("near_cross_output_template_candidate", advisory["code"])
        self.assertEqual(["repair", "royalty"], advisory["caseIds"])
        self.assertEqual(2, advisory["exactFingerprintCount"])
        self.assertRegex(advisory["dominantFingerprintSha256"], r"^[a-f0-9]{64}$")
        self.assertIn("not a defect", advisory["confirmation"])
        self.assertIn("unverified", result["claimBoundary"])

    def test_different_dominant_region_order_does_not_create_near_advisory(self) -> None:
        base = {"version": 1, "landmarks": [], "mainFlow": {"display": "grid", "flexDirection": "row", "gridTracks": [0.5, 0.5], "gap": 0.02}, "representationHistogram": [["form", 1], ["table", 1]]}
        first = {**base, "regions": [{"role": "region", "representation": "form", "box": [0, 0, 0.5, 1], "display": "block", "radius": "small"}, {"role": "region", "representation": "table", "box": [0.5, 0, 0.5, 1], "display": "block", "radius": "small"}]}
        second = {**base, "regions": list(reversed(first["regions"]))}
        source = f"""
const {{ auditCrossOutputTemplates }} = require({json.dumps(str(AUDITOR))});
const row = (caseId, macroFingerprint) => ({{caseId,route:'/',surface:'primary',viewport:'desktop',state:'base',macroFingerprint}});
process.stdout.write(JSON.stringify(auditCrossOutputTemplates({{schemaVersion:1,cohort:'near-2',observations:[row('a',{json.dumps(first)}),row('b',{json.dumps(second)})]}})));
"""
        result = self.run_node(source)
        self.assertEqual([], result["advisories"])

    def test_css_visual_position_swap_and_major_track_reweight_do_not_warn(self) -> None:
        region = lambda representation, box: {"role": "region", "representation": representation, "box": box, "display": "block", "radius": "small"}
        base = {"version": 1, "landmarks": [], "representationHistogram": [["form", 1], ["table", 1]]}
        first = {**base, "mainFlow": {"display": "grid", "flexDirection": "row", "gridTracks": [0.6, 0.4], "gap": 0.02}, "regions": [region("form", [0, 0, 0.6, 1]), region("table", [0.6, 0, 0.4, 1])]}
        swapped = {**base, "mainFlow": {"display": "grid", "flexDirection": "row", "gridTracks": [0.6, 0.4], "gap": 0.02}, "regions": [region("form", [0.6, 0, 0.4, 1]), region("table", [0, 0, 0.6, 1])]}
        reweighted = {**base, "mainFlow": {"display": "grid", "flexDirection": "row", "gridTracks": [0.9, 0.1], "gap": 0.02}, "regions": [region("form", [0, 0, 0.9, 1]), region("table", [0.9, 0, 0.1, 1])]}
        source = f"""
const {{ auditCrossOutputTemplates }} = require({json.dumps(str(AUDITOR))});
const row=(caseId,macroFingerprint)=>( {{caseId,route:'/',surface:'primary',viewport:'desktop',state:'base',macroFingerprint}} );
const audit=(observations)=>auditCrossOutputTemplates({{schemaVersion:1,cohort:'near-3',observations}}).advisories;
process.stdout.write(JSON.stringify({{swapped:audit([row('a',{json.dumps(first)}),row('b',{json.dumps(swapped)})]),reweighted:audit([row('a',{json.dumps(first)}),row('b',{json.dumps(reweighted)})])}}));
"""
        result = self.run_node(source)
        self.assertEqual([], result["swapped"])
        self.assertEqual([], result["reweighted"])

    def test_receipt_is_stable_when_observation_input_order_changes(self) -> None:
        fingerprint = {"version": 1, "landmarks": [], "mainFlow": {"display": "block", "flexDirection": "row", "gridTracks": [], "gap": 0}, "regions": [], "representationHistogram": []}
        source = f"""
const {{ auditCrossOutputTemplates }} = require({json.dumps(str(AUDITOR))});
const row=(caseId,route)=>( {{caseId,route,surface:'primary',viewport:'desktop',state:'base',macroFingerprint:{json.dumps(fingerprint)}}} );
const input=[row('zeta','/b'),row('alpha','/a'),row('middle','/c')];
const audit=(observations)=>auditCrossOutputTemplates({{schemaVersion:1,cohort:'stable-1',observations}});
process.stdout.write(JSON.stringify({{forward:audit(input),reverse:audit([...input].reverse())}}));
"""
        result = self.run_node(source)
        self.assertEqual(result["forward"], result["reverse"])

    def test_key_order_does_not_change_hash(self) -> None:
        source = f"""
const {{ auditCrossOutputTemplates }} = require({json.dumps(str(AUDITOR))});
const a = {{version:1,landmarks:[],mainFlow:{{display:'block',flexDirection:'row',gridTracks:[],gap:0}},regions:[],representationHistogram:[]}};
const b = {{representationHistogram:[],regions:[],mainFlow:{{gap:0,gridTracks:[],flexDirection:'row',display:'block'}},landmarks:[],version:1}};
const row = (caseId, macroFingerprint) => ({{caseId,route:'/',surface:'primary',viewport:'desktop',state:'base',macroFingerprint}});
process.stdout.write(JSON.stringify(auditCrossOutputTemplates({{schemaVersion:1,cohort:'run-4',observations:[row('a',a),row('b',b)]}})));
"""
        result = self.run_node(source)
        self.assertEqual("advisories_present", result["status"])
        self.assertEqual(["a", "b"], result["advisories"][0]["caseIds"])

    def test_forbidden_fingerprint_fields_and_tuple_collisions_fail_closed(self) -> None:
        source = f"""
const {{ auditCrossOutputTemplates }} = require({json.dumps(str(AUDITOR))});
const fingerprint = {{version:1,landmarks:[],mainFlow:{{display:'block',flexDirection:'row',gridTracks:[],gap:0}},regions:[],representationHistogram:[]}};
const row = (caseId, surface, viewport, state, macroFingerprint = fingerprint) => ({{caseId,route:'/',surface,viewport,state,macroFingerprint}});
let forbidden;
try {{ auditCrossOutputTemplates({{schemaVersion:1,cohort:'run-5',observations:[row('a','x','y','z',{{...fingerprint,copy:'forbidden'}}),row('b','x','y','z')]}}); }}
catch (error) {{ forbidden = error.message; }}
const collision = auditCrossOutputTemplates({{schemaVersion:1,cohort:'run-5',observations:[row('a','x|y','z','q'),row('b','x','y|z','q')]}});
process.stdout.write(JSON.stringify({{forbidden,collision}}));
"""
        result = self.run_node(source)
        self.assertIn("fields", result["forbidden"])
        self.assertEqual([], result["collision"]["advisories"])

    def test_nested_landmark_changes_rendered_fingerprint(self) -> None:
        source = f"""
const {{ chromium }} = require('playwright');
const {{ collectMacroFingerprint }} = require({json.dumps(str(AUDITOR))});
(async () => {{
  const browser = await chromium.launch({{headless:true}});
  const page = await browser.newPage({{viewport:{{width:800,height:600}}}});
  await page.setContent('<style>header{{height:80px}}nav{{height:30px}}main{{height:400px}}</style><header></header><main></main>');
  const plain = await page.evaluate(collectMacroFingerprint);
  await page.setContent('<style>header{{height:80px}}nav{{height:30px}}main{{height:400px}}</style><header><nav></nav></header><main></main>');
  const nested = await page.evaluate(collectMacroFingerprint);
  await browser.close();
  process.stdout.write(JSON.stringify({{plain,nested}}));
}})().catch((error) => {{console.error(error);process.exitCode=1}});
"""
        result = self.run_node(source)
        self.assertNotEqual(result["plain"], result["nested"])
        self.assertEqual(1, result["nested"]["landmarks"][1]["depth"])

    def test_cli_rejects_symlink_oversize_and_existing_output(self) -> None:
        fingerprint = {"version": 1, "landmarks": [], "mainFlow": {"display": "block", "flexDirection": "row", "gridTracks": [], "gap": 0}, "regions": [], "representationHistogram": []}
        row = lambda case_id: {"caseId": case_id, "route": "/", "surface": "primary", "viewport": "desktop", "state": "base", "macroFingerprint": fingerprint}
        payload = {"schemaVersion": 1, "cohort": "cli-run", "observations": [row("a"), row("b")]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.json"
            source.write_text(json.dumps(payload), encoding="utf-8")
            output = root / "output.json"
            first = subprocess.run(["node", str(AUDITOR), str(source), str(output)], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, first.returncode, first.stderr)
            second = subprocess.run(["node", str(AUDITOR), str(source), str(output)], cwd=ROOT, text=True, capture_output=True)
            self.assertNotEqual(0, second.returncode)
            self.assertIn("already exists", second.stderr)

            linked = root / "linked.json"
            linked.symlink_to(source)
            linked_result = subprocess.run(["node", str(AUDITOR), str(linked), str(root / "linked-output.json")], cwd=ROOT, text=True, capture_output=True)
            self.assertNotEqual(0, linked_result.returncode)
            self.assertIn("regular file", linked_result.stderr)

            oversized = root / "oversized.json"
            oversized.write_text(" " * (1024 * 1024 + 1), encoding="utf-8")
            oversized_result = subprocess.run(["node", str(AUDITOR), str(oversized), str(root / "oversized-output.json")], cwd=ROOT, text=True, capture_output=True)
            self.assertNotEqual(0, oversized_result.returncode)
            self.assertIn("bounded regular file", oversized_result.stderr)


if __name__ == "__main__":
    unittest.main()
