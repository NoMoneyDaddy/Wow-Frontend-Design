#!/usr/bin/env python3
"""Regression tests for the generic public-Playwright fresh-output smoke gate."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "evals" / "playwright_html_smoke.cjs"


class PlaywrightHtmlSmokeTests(unittest.TestCase):
    def invoke(self, stage: Path, pages: list[str], outputs: list[str]) -> dict:
        completed = subprocess.run(
            ["node", str(SMOKE), str(stage), json.dumps(pages), json.dumps(outputs)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)

    def test_launch_failure_closes_server_and_exits_quickly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "index.html").write_text('<!doctype html><html lang="en"><head><title>X</title></head><body><main><h1>X</h1></main></body></html>', encoding="utf-8")
            environment = os.environ.copy()
            environment["PLAYWRIGHT_BROWSERS_PATH"] = str(stage / "missing-browsers")
            completed = subprocess.run(
                ["node", str(SMOKE), str(stage), '["index.html"]', '["index.html"]'],
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
                timeout=5,
                check=False,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("html smoke infrastructure failure", completed.stderr)

    def test_clean_multi_page_output_passes_both_fresh_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "app.js").write_text("document.querySelector('main').dataset.ready = 'true';\n", encoding="utf-8")
            html = '<!doctype html><html lang="en"><head><title>Ready</title></head><body><main><h1>Ready</h1></main><script src="app.js"></script></body></html>'
            (stage / "index.html").write_text(html, encoding="utf-8")
            (stage / "details.html").write_text(html.replace("Ready", "Details"), encoding="utf-8")
            outputs = ["index.html", "details.html", "app.js"]
            receipt = self.invoke(stage, ["index.html", "details.html"], outputs)
            self.assertEqual("passed", receipt["status"])
            self.assertEqual(
                {("index.html", "desktop"), ("index.html", "mobile"), ("details.html", "desktop"), ("details.html", "mobile")},
                {(item["page"], item["profile"]) for item in receipt["results"]},
            )
            self.assertTrue(all(item["status"] == "passed" for item in receipt["results"]))

    def test_runtime_accessibility_overflow_and_external_failures_are_observed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html><head><title>Broken</title></head><body>
<main><div style="width:2000px">Broken</div><img src="https://example.invalid/a.png"><script>throw new Error("boot")</script></main>
</body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("rejected", receipt["status"])
            for item in receipt["results"]:
                self.assertEqual("rejected", item["status"])
                self.assertTrue(item["root_horizontal_overflow"])
                self.assertGreater(item["counters"]["page_errors"], 0)
                self.assertGreater(item["counters"]["blocked_external_requests"], 0)
                self.assertGreater(item["inspection"]["axe_violation_count"], 0)
                self.assertNotIn("boot", json.dumps(item))

    def test_delayed_failures_and_transient_popup_are_observed_within_settle_window(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html lang="en"><head><title>Delayed</title></head><body>
<main><h1>Delayed</h1></main><script>
setTimeout(() => {
  document.querySelector('main').style.width = '2000px';
  fetch('https://example.invalid/delayed').catch(() => {});
  const popup = window.open('about:blank', '_blank');
  popup?.close();
  throw new Error('delayed boot');
}, 80);
</script></body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual(300, receipt["settle_ms"])
            self.assertEqual("rejected", receipt["status"])
            for item in receipt["results"]:
                self.assertGreater(item["counters"]["page_errors"], 0)
                self.assertGreater(item["counters"]["blocked_external_requests"], 0)
                self.assertGreater(item["counters"]["unexpected_pages"], 0)
                self.assertTrue(item["root_horizontal_overflow"])

    def test_clipped_body_content_does_not_impersonate_root_scroll_overflow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html lang="en"><head><title>Rail</title><style>
html, body { overflow-x: clip; }
.rail { max-width: 100%; overflow-x: auto; }
.track { width: 720px; }
</style></head><body><main><h1>Rail</h1><div class="rail"><div class="track">Scrollable child</div></div></main></body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("passed", receipt["status"])
            self.assertTrue(all(not item["root_horizontal_overflow"] for item in receipt["results"]))

    def test_text_outside_empty_main_does_not_satisfy_primary_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '<!doctype html><html lang="en"><head><title>Empty</title></head><body><main></main><footer><h1>Outside</h1></footer></body></html>'
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("rejected", receipt["status"])
            for item in receipt["results"]:
                self.assertTrue(item["visible_text"])
                self.assertFalse(item["visible_primary_content"])

    def test_noopener_popup_is_attributed_to_the_primary_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            html = '''<!doctype html><html lang="en"><head><title>Popup</title></head><body>
<main><h1>Popup</h1></main><script>
setTimeout(() => window.open('about:blank', '_blank', 'noopener'), 80);
</script></body></html>'''
            (stage / "index.html").write_text(html, encoding="utf-8")
            receipt = self.invoke(stage, ["index.html"], ["index.html"])
            self.assertEqual("rejected", receipt["status"])
            for item in receipt["results"]:
                self.assertGreater(item["counters"]["unexpected_pages"], 0)


if __name__ == "__main__":
    unittest.main()
