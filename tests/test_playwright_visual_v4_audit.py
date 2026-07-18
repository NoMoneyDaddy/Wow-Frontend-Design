#!/usr/bin/env python3
"""Unit tests for product-flow visual audit comparison helpers."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread


ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / "evals" / "playwright_visual_v4_audit.cjs"


class PlaywrightVisualAuditTests(unittest.TestCase):
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

    def test_cross_page_comparison_ignores_page_only_root_variables(self) -> None:
        source = f"""
const {{ sharedRootTokenDrift }} = require({json.dumps(str(AUDITOR))});
const pages = [
  {{ rootVariables: {{ '--ink': '#111', '--measure': '42em' }} }},
  {{ rootVariables: {{ '--ink': '#111' }} }},
  {{ rootVariables: {{ '--ink': '#111', '--success': '#070' }} }},
];
process.stdout.write(JSON.stringify(sharedRootTokenDrift(pages)));
"""
        self.assertEqual([], self.run_node(source))

    def test_cross_page_comparison_retains_shared_token_value_drift(self) -> None:
        source = f"""
const {{ sharedRootTokenDrift }} = require({json.dumps(str(AUDITOR))});
const pages = [
  {{ rootVariables: {{ '--ink': '#111', '--surface': '#fff' }} }},
  {{ rootVariables: {{ '--ink': '#222', '--surface': '#fff' }} }},
  {{ rootVariables: {{ '--ink': '#111', '--surface': '#fff' }} }},
];
process.stdout.write(JSON.stringify(sharedRootTokenDrift(pages)));
"""
        self.assertEqual(["--ink"], self.run_node(source))

    def test_mobile_profile_emulates_touch_device_not_only_viewport(self) -> None:
        source = f"""
const {{ VIEWPORTS }} = require({json.dumps(str(AUDITOR))});
process.stdout.write(JSON.stringify(VIEWPORTS.find((item) => item.name === 'mobile')));
"""
        mobile = self.run_node(source)
        self.assertEqual(390, mobile["width"])
        self.assertEqual(844, mobile["height"])
        self.assertTrue(mobile["isMobile"])
        self.assertTrue(mobile["hasTouch"])
        self.assertEqual(3, mobile["deviceScaleFactor"])
        self.assertIn("Android", mobile["userAgent"])

    def test_mobile_closed_nav_and_fixed_obstruction_are_blocking(self) -> None:
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
            records = "".join(
                f'<article data-eval="record" data-record-id="record-{index}">批次 {index}</article>'
                for index in range(8)
            )
            (target / "index.html").write_text(
                f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>視覺遮擋 fixture</title>
<style>
* {{ box-sizing: border-box; }}
body {{ margin: 0; font: 16px sans-serif; }}
[data-eval="mobile-nav-toggle"] {{ display: none; }}
[data-eval="global-nav"] {{ display: flex; gap: 1rem; }}
main {{ position: relative; min-height: 1100px; padding: 1rem; }}
.fixed-action {{ position: static; }}
@media (max-width: 600px) {{
  [data-eval="mobile-nav-toggle"] {{ display: block; min-height: 44px; }}
  [data-eval="global-nav"] {{
    position: fixed; inset: 72px 8px auto; z-index: 20;
    min-height: 180px; padding: 1rem; background: white;
  }}
  .covered-copy {{ position: absolute; top: 770px; margin: 0; }}
  .fixed-action {{
    position: fixed; inset: auto 8px 0; z-index: 30;
    min-height: 90px; background: white;
  }}
}}
</style>
</head>
<body>
<header>
  <button data-eval="mobile-nav-toggle" aria-expanded="false" aria-controls="fixture-nav">導覽</button>
  <nav id="fixture-nav" data-eval="global-nav"><a href="#main">首頁</a><a href="#records">紀錄</a></nav>
</header>
<main id="main"><h1>工作面</h1><section id="records">{records}</section><p class="covered-copy">不得被固定控制列遮住</p></main>
<button class="fixed-action" data-eval="global-action">主要動作</button>
</body>
</html>
""",
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
                        f"harbor-cold-chain-v4:fixture=http://127.0.0.1:{server.server_port}/",
                    ],
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
            if completed.returncode != 0:
                self.fail(completed.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            issues = report["summary"]["issuesByTarget"]["harbor-cold-chain-v4:fixture"]
            diagnostics = json.dumps(report["results"], ensure_ascii=False, indent=2)
            self.assertIn("closed_mobile_navigation_exposed", issues, diagnostics)
            self.assertIn("fixed_or_sticky_content_obstruction", issues, diagnostics)


if __name__ == "__main__":
    unittest.main()
