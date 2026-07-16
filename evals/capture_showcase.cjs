#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const url = process.argv[2] || "http://127.0.0.1:4175/";
const sourcePaths = [
  "evals/weak-model-showcase/index.html",
  "evals/weak-model-showcase/styles.css",
  "evals/weak-model-showcase/app.js",
  "evals/weak-model-showcase/theme-init.js",
];
const captures = [
  { name: "showcase-desktop.png", viewport: { width: 1440, height: 1000 }, theme: "light" },
  { name: "showcase-desktop-dark.png", viewport: { width: 1440, height: 1000 }, theme: "dark" },
  { name: "showcase-mobile.png", viewport: { width: 390, height: 844 }, theme: "light" },
  { name: "showcase-mobile-dark.png", viewport: { width: 390, height: 844 }, theme: "dark" },
];

function sha256(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function pngSize(file) {
  const header = fs.readFileSync(file).subarray(0, 24);
  if (header.toString("hex", 0, 8) !== "89504e470d0a1a0a") throw new Error(`not a PNG: ${file}`);
  return `${header.readUInt32BE(16)}x${header.readUInt32BE(20)}`;
}

function matchesAllowedNetworkOrigin(value, allowedOrigin) {
  try {
    const parsed = new URL(value);
    if (["data:", "about:"].includes(parsed.protocol)) return true;
    if (parsed.protocol === "ws:") parsed.protocol = "http:";
    if (parsed.protocol === "wss:") parsed.protocol = "https:";
    return parsed.origin === allowedOrigin;
  } catch {
    return false;
  }
}

async function installExactOriginRoutes(context, allowedOrigin, externalRequests) {
  await context.route("**/*", async (route) => {
    const requestUrl = route.request().url();
    if (!matchesAllowedNetworkOrigin(requestUrl, allowedOrigin)) {
      externalRequests.push(requestUrl);
      return route.abort("blockedbyclient");
    }
    return route.continue();
  });
  await context.routeWebSocket("**/*", async (webSocket) => {
    const requestUrl = webSocket.url();
    if (!matchesAllowedNetworkOrigin(requestUrl, allowedOrigin)) {
      externalRequests.push(requestUrl);
      await webSocket.close({ code: 1008, reason: "Blocked by evaluator origin policy" });
      return;
    }
    webSocket.connectToServer();
  });
}

(async () => {
  const launch = { headless: true };
  if (process.env.CHROME_EXECUTABLE_PATH) launch.executablePath = process.env.CHROME_EXECUTABLE_PATH;
  const browser = await chromium.launch(launch);
  const browserVersion = await browser.version();
  const browserProduct = process.env.CHROME_EXECUTABLE_PATH ? "Google Chrome" : "Playwright-managed Chromium";
  const results = [];
  try {
    for (const capture of captures) {
      const targetOrigin = new URL(url).origin;
      const externalRequests = [];
      const context = await browser.newContext({
        viewport: capture.viewport,
        deviceScaleFactor: 1,
        locale: "zh-TW",
        timezoneId: "Asia/Taipei",
        colorScheme: capture.theme,
        reducedMotion: "reduce",
        serviceWorkers: "block",
      });
      await installExactOriginRoutes(context, targetOrigin, externalRequests);
      await context.addInitScript((theme) => localStorage.setItem("wow-theme", theme), capture.theme);
      const page = await context.newPage();
      const consoleErrors = [];
      const requestFailures = [];
      const badResponses = [];
      page.on("console", (message) => {
        if (message.type() === "error") consoleErrors.push(message.text());
      });
      page.on("requestfailed", (request) => requestFailures.push(request.url()));
      page.on("response", (response) => {
        if (response.status() >= 400) badResponses.push({ status: response.status(), url: response.url() });
      });

      await page.goto(url, { waitUntil: "networkidle" });
      await page.evaluate(() => document.fonts.ready);
      await page.waitForFunction(
        (theme) => document.readyState === "complete" && document.documentElement.dataset.theme === theme,
        capture.theme
      );
      await page.evaluate(() => scrollTo(0, 0));
      const output = path.join(root, "assets", capture.name);
      await page.screenshot({ path: output, fullPage: true, animations: "disabled", type: "png" });
      const documentState = await page.evaluate(() => ({
        language: document.documentElement.lang,
        theme: document.documentElement.dataset.theme,
        activeElement: document.activeElement ? document.activeElement.tagName.toLowerCase() : null,
        scrollX: window.scrollX,
        scrollY: window.scrollY,
        readyState: document.readyState,
        fonts: document.fonts.status,
      }));
      if (consoleErrors.length || requestFailures.length || badResponses.length || externalRequests.length) {
        throw new Error(
          `${capture.name} capture precondition failed: ${JSON.stringify({ consoleErrors, requestFailures, badResponses, externalRequests })}`
        );
      }
      results.push({
        path: path.posix.join("assets", capture.name),
        viewport: `${capture.viewport.width}x${capture.viewport.height}`,
        device_scale_factor: 1,
        decoded_size: pngSize(output),
        theme: capture.theme,
        state: "default_top_of_page",
        document: documentState,
        sha256: sha256(output),
      });
      await context.close();
    }
  } finally {
    await browser.close();
  }

  const manifest = {
    schema_version: 2,
    status: "observed_release_showcase_not_regression_baseline",
    captured_at: new Date().toISOString(),
    case_id: "weak-model-showcase-release-capture",
    route: url,
    repository_commit: null,
    source_binding:
      "commit-independent pre-release capture: integrity is bound to the exact source, capture-script, dependency-lock and image hashes below; repository_commit remains null by design to avoid a self-referential release cycle",
    environment: {
      os: `${os.platform()} ${os.release()} ${os.arch()}`,
      browser: `${browserProduct} ${browserVersion}`,
      automation: `Playwright ${require("playwright/package.json").version}`,
      headless: true,
      browser_executable: process.env.CHROME_EXECUTABLE_PATH || "Playwright-managed Chromium",
      locale: "zh-TW",
      timezone: "Asia/Taipei",
      color_profile: "not explicitly controlled",
      reduced_motion: "reduce",
      network: "local static server; console errors, failed requests, HTTP >=400 and external requests asserted empty",
      wait_condition: "networkidle + document.readyState=complete + document.fonts.ready/status=loaded + explicit theme applied",
      screenshot_options: { full_page: true, animations: "disabled", type: "png" },
    },
    capture_command: "CHROME_EXECUTABLE_PATH=/absolute/path/to/chrome node evals/capture_showcase.cjs http://127.0.0.1:4175/",
    capture_script: { path: "evals/capture_showcase.cjs", sha256: sha256(__filename) },
    dependency_lock: { path: "package-lock.json", sha256: sha256(path.join(root, "package-lock.json")) },
    source_files: sourcePaths.map((relative) => ({ path: relative, sha256: sha256(path.join(root, relative)) })),
    captures: results,
    claim_boundary:
      "Captures support rendered visual observation only. They do not prove design quality, WCAG conformance, cross-browser compatibility, interaction, performance, or future regression equivalence.",
  };
  fs.writeFileSync(path.join(root, "assets", "screenshots.json"), `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
})().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exitCode = 1;
});
