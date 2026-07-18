#!/usr/bin/env python3
"""Regression tests for fail-closed browser evaluator network policies."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Iterator


ROOT = Path(__file__).resolve().parents[2]
VISUAL_AUDITORS = {
    "v4": ROOT / "evals" / "playwright_visual_v4_audit.cjs",
    "v5": ROOT / "evals" / "playwright_visual_v5_audit.cjs",
    "v6": ROOT / "evals" / "playwright_visual_v6_audit.cjs",
}
DASHBOARD_AUDITOR = ROOT / "evals" / "playwright_dashboard_audit.cjs"
CAPTURE_SHOWCASE = ROOT / "evals" / "capture_showcase.cjs"
CURRENT_SMOKE = ROOT / "evals" / "playwright_html_smoke.cjs"
BROWSER_RUNTIME = ROOT / "evals" / "playwright_browser_runtime.cjs"


@contextmanager
def serve_html(html: str) -> Iterator[str]:
    body = html.encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@contextmanager
def record_requests() -> Iterator[tuple[str, list[str]]]:
    requests: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            requests.append(self.path)
            self.send_response(204)
            self.end_headers()

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/blocked-popup", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def popup_page(blocked_url: str, body: str = "<main><h1>測試頁面</h1></main>") -> str:
    web_socket_url = blocked_url.replace("http://", "ws://", 1)
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><title>網路邊界測試</title></head>
<body>{body}<script>
fetch({json.dumps(f"{blocked_url}?fetch=1")}).catch(() => {{}});
new WebSocket({json.dumps(web_socket_url)});
window.open({json.dumps(blocked_url)}, "_blank");
</script></body></html>"""


class BrowserEgressControlTests(unittest.TestCase):
    maxDiff = None

    def run_visual_auditor(self, version: str, identity: str, site_url: str) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report_path = root / "report.json"
            screenshots = root / "screenshots"
            screenshots.mkdir()
            completed = subprocess.run(
                [
                    "node",
                    str(VISUAL_AUDITORS[version]),
                    "--output",
                    str(report_path),
                    "--artifact-dir",
                    str(screenshots),
                    "--target",
                    f"{identity}={site_url}",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=90,
            )
            if completed.returncode != 0:
                self.fail(completed.stderr)
            return json.loads(report_path.read_text(encoding="utf-8"))

    def assert_popup_blocked(self, report: dict[str, object], blocked_url: str, requests: list[str]) -> None:
        self.assertEqual([], requests, "cross-origin popup reached the blocked server")
        web_socket_url = blocked_url.replace("http://", "ws://", 1)
        results = report["results"]
        self.assertTrue(results)
        for result in results:
            self.assertIn(blocked_url, result["externalRequests"])
            self.assertIn(web_socket_url, result["externalRequests"])
            self.assertIn("external_requests_attempted", result["visualIssues"])

    def test_v4_popup_first_navigation_is_blocked_context_wide(self) -> None:
        with record_requests() as (blocked_url, requests):
            body = '<main><h1>冷鏈工作面</h1>' + "".join(
                f'<article data-eval="record" data-record-id="record-{index}">紀錄 {index}</article>'
                for index in range(8)
            ) + "</main>"
            with serve_html(popup_page(blocked_url, body)) as site_url:
                report = self.run_visual_auditor(
                    "v4", "harbor-cold-chain-v4:fixture", site_url
                )
        self.assert_popup_blocked(report, blocked_url, requests)

    def test_v5_popup_first_navigation_is_blocked_context_wide(self) -> None:
        with record_requests() as (blocked_url, requests):
            options = "".join(
                f'<label data-eval="alternative-option" data-option-id="route-{index}">'
                f'<input type="radio" name="route" value="{index}">方案 {index}</label>'
                for index in range(3)
            )
            body = f"""<main data-eval="rebooking-flow"><h1>列車改簽</h1>
<p data-eval="disruption-alert">請選擇替代方案。</p>
<section data-eval="recovery-step" data-state="choose">{options}</section>
<button data-eval="primary-action">下一步</button>
<section data-eval="confirmation-summary" hidden>確認摘要</section>
<button data-eval="back-action" hidden>返回</button></main>
<script>document.querySelector('[data-eval="primary-action"]').onclick=()=>{{
document.querySelector('[data-eval="recovery-step"]').dataset.state='confirm';
document.querySelector('[data-eval="confirmation-summary"]').hidden=false;
document.querySelector('[data-eval="back-action"]').hidden=false;
}};</script>"""
            with serve_html(popup_page(blocked_url, body)) as site_url:
                report = self.run_visual_auditor(
                    "v5", "rail-rebooking-v5:fixture", site_url
                )
        self.assert_popup_blocked(report, blocked_url, requests)

    def test_v6_popup_first_navigation_is_blocked_context_wide(self) -> None:
        with record_requests() as (blocked_url, requests):
            body = """<main data-eval="specimen-workspace"><h1>字體工作面</h1>
<button data-eval="writing-toggle" aria-pressed="false">切換</button>
<div data-eval="specimen">文字樣本</div><div data-eval="fallback-note">備註</div>
<button data-eval="outline-toggle">外框</button></main>
<script>document.querySelector('[data-eval="writing-toggle"]').onclick=(event)=>{
document.querySelector('[data-eval="specimen"]').style.writingMode='vertical-rl';
event.currentTarget.setAttribute('aria-pressed','true');
};</script>"""
            with serve_html(popup_page(blocked_url, body)) as site_url:
                report = self.run_visual_auditor(
                    "v6", "type-foundry-specimen-v6:fixture", site_url
                )
        self.assert_popup_blocked(report, blocked_url, requests)

    def test_dashboard_popup_is_blocked_and_reported(self) -> None:
        with record_requests() as (blocked_url, requests):
            body = """<input id="search-input"><input id="f-search">
<button id="clear-filters">清除</button><table><tbody id="workorder-body"></tbody></table>
<div id="work-list"></div><div id="detail-overlay" hidden></div><div id="detail"></div>
<div id="background"></div><script>
const table=document.querySelector('#workorder-body'), list=document.querySelector('#work-list');
function render(){
 table.innerHTML='<tr><td><button class="view-detail-btn" data-id="x">開啟</button></td></tr>';
 list.innerHTML='<button class="wo" data-id="x">工單</button>';
 document.querySelector('.view-detail-btn').onclick=(event)=>{
  document.querySelector('#detail-overlay').hidden=false; document.body.style.overflow='hidden';
  document.querySelector('#background').setAttribute('inert',''); window.lastOpener=event.currentTarget;
 };
 document.querySelector('.wo').onclick=(event)=>{
  document.querySelector('#detail').classList.add('is-open'); document.body.style.overflow='hidden';
  document.querySelector('#background').setAttribute('inert',''); window.lastOpener=event.currentTarget;
 };
}
render();
for(const id of ['search-input','f-search']) document.getElementById(id).oninput=()=>{table.innerHTML='';list.innerHTML='';};
document.querySelector('#clear-filters').onclick=render;
addEventListener('keydown',(event)=>{if(event.key==='Escape'){
 document.querySelector('#detail-overlay').hidden=true; document.querySelector('#detail').classList.remove('is-open');
 document.body.style.overflow=''; document.querySelector('#background').removeAttribute('inert'); window.lastOpener?.focus();
}});
</script>"""
            with serve_html(popup_page(blocked_url, body)) as site_url:
                completed = subprocess.run(
                    ["node", str(DASHBOARD_AUDITOR), site_url, site_url],
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                    timeout=90,
                )
        self.assertEqual([], requests, "dashboard popup reached the blocked server")
        report = json.loads(completed.stdout)
        web_socket_url = blocked_url.replace("http://", "ws://", 1)
        for target in report["results"]:
            for result in target["viewports"]:
                self.assertIn(blocked_url, result["externalRequests"])
                self.assertIn(web_socket_url, result["externalRequests"])
                self.assertIn("external_requests_attempted", result["acceptanceIssues"])

    def test_capture_showcase_popup_is_blocked_before_network(self) -> None:
        with record_requests() as (blocked_url, requests):
            body = """<main><h1>展示頁</h1></main><script>
document.documentElement.dataset.theme=localStorage.getItem('wow-theme');
</script>"""
            with serve_html(popup_page(blocked_url, body)) as site_url:
                with tempfile.TemporaryDirectory() as temporary:
                    sandbox = Path(temporary)
                    (sandbox / "evals").mkdir()
                    (sandbox / "assets").mkdir()
                    script = sandbox / "evals" / "capture_showcase.cjs"
                    shutil.copy2(CAPTURE_SHOWCASE, script)
                    environment = os.environ.copy()
                    environment["NODE_PATH"] = str(ROOT / "node_modules")
                    completed = subprocess.run(
                        ["node", str(script), site_url],
                        cwd=sandbox,
                        env=environment,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False,
                        timeout=90,
                    )
        self.assertEqual([], requests, "capture popup reached the blocked server")
        self.assertNotEqual(0, completed.returncode)
        self.assertIn("capture precondition failed", completed.stderr)
        self.assertIn(blocked_url, completed.stderr)
        self.assertIn(blocked_url.replace("http://", "ws://", 1), completed.stderr)

    def test_current_smoke_blocks_http_websocket_and_popup_egress(self) -> None:
        with record_requests() as (blocked_url, requests), tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            (stage / "index.html").write_text(popup_page(blocked_url), encoding="utf-8")
            completed = subprocess.run(
                ["node", str(CURRENT_SMOKE), str(stage), '["index.html"]', '["index.html"]'],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=30,
            )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual([], requests, "current smoke allowed cross-origin traffic")
        receipt = json.loads(completed.stdout)
        self.assertEqual("rejected", receipt["status"])
        for result in receipt["results"]:
            self.assertGreater(result["counters"]["blocked_external_requests"], 0)
            self.assertGreater(result["counters"]["blocked_websockets"], 0)

    def test_all_auditors_block_service_workers(self) -> None:
        for source in (*VISUAL_AUDITORS.values(), DASHBOARD_AUDITOR, CAPTURE_SHOWCASE, BROWSER_RUNTIME):
            with self.subTest(source=source.name):
                self.assertIn('serviceWorkers: "block"', source.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
