#!/usr/bin/env python3
"""Browser-backed tests for the bounded stale-completion replay module."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "evals" / "v7_stale_completion.cjs"
FIXTURE = ROOT / "evals" / "fixtures" / "v7-stale-completion.html"


STEPS = [
    {"id": "start-load", "action": "click", "selector": "#initiate"},
    {"id": "switch-identity", "action": "click", "selector": "#interrupt"},
]
DECLARATION = {
    "id": "old-item-completion",
    "request": {
        "id": "old-item-request",
        "method": "GET",
        "path": "/api/old?item=alpha",
        "fulfill": {
            "status": 200,
            "contentType": "application/json",
            "body": json.dumps({"content": "OLD-SECRET-COPY"}),
        },
    },
    "initiationStepId": "start-load",
    "pending": {"id": "load-pending", "type": "visible", "selector": "#pending"},
    "interruptionStepId": "switch-identity",
    "freshness": {
        "identity": {"id": "new-identity", "type": "text", "selector": "#identity", "value": "beta"},
        "success": {"id": "old-success-hidden", "type": "hidden", "selector": "#success"},
        "content": {"id": "new-content", "type": "text", "selector": "#content", "value": "beta-ready"},
    },
}


class V7StaleCompletionTests(unittest.TestCase):
    def test_exact_declaration_validation_fails_closed(self) -> None:
        cases = {
            "extra-key": {**DECLARATION, "selector": "#forbidden"},
            "non-adjacent": {**DECLARATION, "interruptionStepId": "later-step"},
            "external-path": {**DECLARATION, "request": {**DECLARATION["request"], "path": "https://example.com/api"}},
            "duplicate-predicate": {
                **DECLARATION,
                "freshness": {
                    **DECLARATION["freshness"],
                    "success": {"id": "load-pending", "type": "hidden", "selector": "#success"},
                },
            },
            "missing-value": {
                **DECLARATION,
                "freshness": {
                    **DECLARATION["freshness"],
                    "content": {"id": "new-content", "type": "text", "selector": "#content"},
                },
            },
        }
        source = f"""
const {{ validateAsyncCompletion }} = require({json.dumps(str(MODULE))});
const steps = JSON.parse(process.argv[1]);
const declaration = JSON.parse(process.argv[2]);
try {{ validateAsyncCompletion(declaration, steps); process.exit(1); }}
catch (error) {{ process.stdout.write(error.message); }}
"""
        steps = [*STEPS, {"id": "later-step", "action": "click", "selector": "#later"}]
        for label, declaration in cases.items():
            with self.subTest(label=label):
                completed = subprocess.run(
                    ["node", "-e", source, json.dumps(steps), json.dumps(declaration)],
                    cwd=ROOT, text=True, capture_output=True,
                )
                self.assertEqual(0, completed.returncode)
                self.assertTrue(completed.stdout)

    def test_replay_classifies_fresh_stale_and_unavailable_without_raw_data(self) -> None:
        source = f"""
const fs = require('node:fs');
const http = require('node:http');
const {{ chromium }} = require('playwright');
const {{ runStaleCompletionReplay, validateAsyncCompletion }} = require({json.dumps(str(MODULE))});
const fixture = fs.readFileSync({json.dumps(str(FIXTURE))});
const declarationSource = JSON.parse(process.argv[1]);
const steps = JSON.parse(process.argv[2]);
(async () => {{
  let apiRequests = 0;
  const server = http.createServer((request, response) => {{
    if (request.url.startsWith('/api/')) apiRequests += 1;
    response.writeHead(200, {{ 'content-type': 'text/html; charset=utf-8' }});
    response.end(fixture);
  }});
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${{server.address().port}}`;
  const browser = await chromium.launch({{ headless: true }});
  const results = {{}};
  for (const mode of ['correct', 'stale', 'duplicate', 'delayed-duplicate', 'method-mismatch', 'delayed-method-mismatch', 'no-pending', 'no-identity-change', 'no-request']) {{
    const context = await browser.newContext();
    await context.route('**/*', async (route) => {{
      const parsed = new URL(route.request().url());
      if (parsed.origin === origin) await route.continue();
      else await route.abort('blockedbyclient');
    }});
    const page = await context.newPage();
    await page.goto(`${{origin}}/?mode=${{mode}}`, {{ waitUntil: 'domcontentloaded' }});
    const declaration = validateAsyncCompletion(JSON.parse(JSON.stringify(declarationSource)), steps);
    results[mode] = await runStaleCompletionReplay(page, new URL(origin), declaration);
    await context.close();
  }}
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
  process.stdout.write(JSON.stringify({{ results, apiRequests }}));
}})().catch((error) => {{ console.error('fixed-test-failure'); process.exit(1); }});
"""
        completed = subprocess.run(
            ["node", "-e", source, json.dumps(DECLARATION), json.dumps(STEPS)],
            cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        results = payload["results"]
        self.assertEqual(0, payload["apiRequests"])
        self.assertEqual({
            "declarationId", "requestId", "initiationStepId", "pendingPredicateId",
            "interruptionStepId", "freshnessPredicateIds", "request", "pending",
            "interruption", "release", "freshness", "reason",
        }, set(results["correct"]))
        self.assertEqual("fresh", results["correct"]["freshness"])
        self.assertEqual("fresh_completion_isolated", results["correct"]["reason"])
        self.assertEqual("held_once", results["correct"]["request"])
        self.assertEqual("matched", results["correct"]["pending"])
        self.assertEqual("identity_changed", results["correct"]["interruption"])
        self.assertEqual("fulfilled_once", results["correct"]["release"])
        self.assertEqual("stale", results["stale"]["freshness"])
        self.assertEqual("stale_completion_reassigned", results["stale"]["reason"])
        self.assertEqual("request_count_exceeded", results["duplicate"]["reason"])
        self.assertEqual("request_count_exceeded", results["delayed-duplicate"]["reason"])
        self.assertEqual("request_mismatch", results["method-mismatch"]["reason"])
        self.assertEqual("request_mismatch", results["delayed-method-mismatch"]["reason"])
        self.assertEqual("unavailable", results["delayed-method-mismatch"]["freshness"])
        self.assertEqual("pending_not_observed", results["no-pending"]["reason"])
        self.assertEqual("interruption_identity_unchanged", results["no-identity-change"]["reason"])
        self.assertEqual("request_not_observed", results["no-request"]["reason"])
        serialized = json.dumps(results)
        for secret in ("#initiate", "/api/old", "beta-ready", "OLD-SECRET-COPY"):
            self.assertNotIn(secret, serialized)
            self.assertNotIn(secret, completed.stderr)
        self.assertNotIn("screenshot", MODULE.read_text(encoding="utf-8"))
        self.assertEqual([], list(ROOT.rglob("*stale-completion*.png")))


if __name__ == "__main__":
    unittest.main()
