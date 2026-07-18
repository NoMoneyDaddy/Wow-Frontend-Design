#!/usr/bin/env python3
"""Regression tests for the current Playwright network boundary."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Iterator


ROOT = Path(__file__).resolve().parents[1]
CURRENT_SMOKE = ROOT / "evals" / "playwright_html_smoke.cjs"
BROWSER_RUNTIME = ROOT / "evals" / "playwright_browser_runtime.cjs"


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


def page_with_egress(blocked_url: str) -> str:
    websocket_url = blocked_url.replace("http://", "ws://", 1)
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><title>網路邊界測試</title></head>
<body><main><h1>測試頁面</h1></main><script>
fetch({json.dumps(f"{blocked_url}?fetch=1")}).catch(() => {{}});
new WebSocket({json.dumps(websocket_url)});
window.open({json.dumps(blocked_url)}, "_blank");
</script></body></html>"""


class BrowserEgressControlTests(unittest.TestCase):
    def test_current_smoke_blocks_http_websocket_and_popup_egress(self) -> None:
        with record_requests() as (blocked_url, requests), tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            (stage / "index.html").write_text(page_with_egress(blocked_url), encoding="utf-8")
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

    def test_current_runtime_blocks_service_workers(self) -> None:
        source = BROWSER_RUNTIME.read_text(encoding="utf-8")
        self.assertIn('serviceWorkers: "block"', source)


if __name__ == "__main__":
    unittest.main()
