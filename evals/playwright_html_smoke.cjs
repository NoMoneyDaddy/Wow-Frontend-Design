#!/usr/bin/env node
"use strict";

const { AxeBuilder } = require("@axe-core/playwright");
const { runLocalPageMatrix } = require("./playwright_browser_runtime.cjs");

const VIEWPORTS = [
  { name: "desktop", viewport: { width: 1440, height: 1000 }, reducedMotion: "no-preference" },
  { name: "mobile", viewport: { width: 390, height: 844 }, reducedMotion: "reduce" },
];

function fail(message) {
  process.stderr.write(`html smoke infrastructure failure: ${message}\n`);
  process.exitCode = 2;
}

async function main() {
  if (process.argv.length !== 5) {
    fail("expected stage, JSON page list and JSON output list");
    return;
  }
  const stage = process.argv[2];
  const pages = JSON.parse(process.argv[3]);
  const allowedFiles = JSON.parse(process.argv[4]);
  if (!Array.isArray(pages) || pages.length === 0 || pages.some((item) => typeof item !== "string")
    || !Array.isArray(allowedFiles) || allowedFiles.some((item) => typeof item !== "string")) {
    fail("invalid page list");
    return;
  }
  const { browserVersion, results } = await runLocalPageMatrix({
    stage,
    pages,
    allowedFiles,
    profiles: VIEWPORTS,
    inspectPage: async (page) => {
      const analysis = await new AxeBuilder({ page }).analyze();
      return {
        axe_violation_count: analysis.violations.length,
        axe_rule_ids: analysis.violations.map((violation) => violation.id).sort(),
      };
    },
  });
  for (const result of results) {
    const passed = result.navigation === "passed"
      && result.visible_main
      && result.visible_text
      && result.visible_primary_content
      && !result.root_horizontal_overflow
      && Object.values(result.counters).every((count) => count === 0)
      && result.inspection.axe_violation_count === 0;
    result.status = passed ? "passed" : "rejected";
  }

  const status = results.every((result) => result.status === "passed") ? "passed" : "rejected";
  process.stdout.write(`${JSON.stringify({
    schema_version: 1,
    status,
    tool: {
      package: "playwright",
      version: require("playwright/package.json").version,
      browser: "chromium",
      browser_version: browserVersion,
    },
    settle_ms: 300,
    profiles: VIEWPORTS.map(({ name, viewport, reducedMotion }) => ({ name, viewport, reduced_motion: reducedMotion })),
    results,
  })}\n`);
}

main().catch((error) => fail(error && error.name ? error.name : "unknown"));
