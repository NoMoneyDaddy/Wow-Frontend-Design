#!/usr/bin/env python3
"""Regression tests for the v5 interaction-aware visual auditor."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread


ROOT = Path(__file__).resolve().parents[2]
AUDITOR = ROOT / "evals" / "playwright_visual_v5_audit.cjs"


class PlaywrightVisualV5AuditTests(unittest.TestCase):
    def run_node(self, source: str) -> object:
        completed = subprocess.run(
            ["node", "-e", source],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            self.fail(completed.stderr)
        return json.loads(completed.stdout)

    def test_mobile_profile_is_a_touch_device_with_dpr_three(self) -> None:
        source = f"""
const {{ VIEWPORTS }} = require({json.dumps(str(AUDITOR))});
process.stdout.write(JSON.stringify(VIEWPORTS.find((item) => item.name === 'mobile')));
"""
        mobile = self.run_node(source)
        self.assertEqual((390, 844, 3), (mobile["width"], mobile["height"], mobile["deviceScaleFactor"]))
        self.assertTrue(mobile["isMobile"])
        self.assertTrue(mobile["hasTouch"])
        self.assertIn("Android", mobile["userAgent"])

    def test_cross_page_comparison_detects_shared_token_drift(self) -> None:
        source = f"""
const {{ sharedRootTokenDrift }} = require({json.dumps(str(AUDITOR))});
const pages = [
  {{ rootVariables: {{ '--ink': '#111', '--page-only': 'a' }} }},
  {{ rootVariables: {{ '--ink': '#222' }} }},
  {{ rootVariables: {{ '--ink': '#111', '--other': 'b' }} }},
];
process.stdout.write(JSON.stringify(sharedRootTokenDrift(pages)));
"""
        self.assertEqual(["--ink"], self.run_node(source))

    def test_language_contract_accepts_specific_traditional_chinese_for_open_brief(self) -> None:
        source = f"""
const {{ issueCodes }} = require({json.dumps(str(AUDITOR))});
const base = {{
  interaction: {{ failures: [] }}, contractIssues: [], hasMain: true, visibleMainCount: 1,
  hasHeading: true, horizontalOverflow: false, outsideViewport: [], shortActionFailures: [],
  clippedText: [], criticalTextCollisions: [], fixedStickyObstructions: [], viewport: 'mobile',
  smallTouchTargets: [], readingRhythm: {{ tooTight: [], tooWide: [] }}, narrowTextColumns: [],
  reducedMotionAnimations: [], consoleErrors: [], externalRequests: [], badResponses: [],
}};
process.stdout.write(JSON.stringify({{
  openBrief: issueCodes({{ ...base, caseId: 'ceramics-festival-one-line-v5', lang: 'zh-Hant-TW' }}),
  exactBrief: issueCodes({{ ...base, caseId: 'rail-rebooking-v5', lang: 'zh-Hant-TW' }}),
}}));
"""
        result = self.run_node(source)
        self.assertNotIn("document_lang_not_zh_hant", result["openBrief"])
        self.assertIn("document_lang_not_zh_hant", result["exactBrief"])

    def test_rail_interaction_reaches_confirmation_on_both_profiles(self) -> None:
        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, _format: str, *_args: object) -> None:
                return

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target"
            screenshots = root / "screenshots"
            report_path = root / "visual.json"
            target.mkdir()
            screenshots.mkdir()
            options = "".join(
                f'<label data-eval="alternative-option" data-option-id="route-{index}">'
                f'<input type="radio" name="route" value="{index}">方案 {index}</label>'
                for index in range(1, 4)
            )
            (target / "index.html").write_text(
                f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>改簽測試</title><style>
*{{box-sizing:border-box}} body{{margin:0;font:16px/1.55 sans-serif}} main{{max-width:48rem;margin:auto;padding:2rem 1rem}}
label,button{{display:block;min-width:44px;min-height:44px;padding:.75rem;margin:.75rem 0}} [hidden]{{display:none!important}}
.sr-only{{position:absolute;inline-size:1px;block-size:1px;margin:-1px;overflow:hidden;clip-path:inset(50%)}}
</style></head><body><main data-eval="rebooking-flow"><h1>選擇替代方案</h1>
<p data-eval="disruption-alert">原列車停駛，請選擇安全的替代方案。</p>
<h3 class="sr-only">只供輔助科技使用的說明</h3>
<section data-eval="recovery-step" data-state="choose">{options}</section>
<button data-eval="primary-action">下一步</button>
<section data-eval="confirmation-summary" hidden><h2>確認改簽</h2><p>兩位成人與一位孩童，費用差額 NT$0。</p></section>
<button data-eval="back-action" hidden>返回修改</button></main>
<script>document.querySelector('[data-eval="primary-action"]').addEventListener('click',()=>{{
 const selected=document.querySelector('input:checked'); if(!selected)return;
 document.querySelector('[data-eval="recovery-step"]').dataset.state='confirm';
 document.querySelector('[data-eval="confirmation-summary"]').hidden=false;
 document.querySelector('[data-eval="back-action"]').hidden=false;
}});</script></body></html>""",
                encoding="utf-8",
            )
            handler = partial(QuietHandler, directory=str(target))
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                completed = subprocess.run(
                    [
                        "node",
                        str(AUDITOR),
                        "--output",
                        str(report_path),
                        "--artifact-dir",
                        str(screenshots),
                        "--target",
                        f"rail-rebooking-v5:fixture=http://127.0.0.1:{server.server_port}/",
                    ],
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                    timeout=60,
                )
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
            if completed.returncode != 0:
                self.fail(completed.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(2, report["summary"]["checkedPages"])
            for result in report["results"]:
                self.assertEqual("confirm", result["interaction"]["finalState"])
                self.assertTrue(result["interaction"]["summaryVisible"])
                self.assertEqual([], result["interaction"]["failures"])
                self.assertEqual([], result["clippedText"])


if __name__ == "__main__":
    unittest.main()
