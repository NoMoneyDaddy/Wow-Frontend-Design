#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const { chromium } = require("playwright");

function parseArguments(argv) {
  const options = { diagnostic: false, output: null, urls: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--diagnostic") {
      options.diagnostic = true;
    } else if (argument === "--output") {
      options.output = argv[index + 1] || null;
      index += 1;
      if (!options.output) throw new Error("--output requires a path");
    } else if (argument.startsWith("--")) {
      throw new Error(`unknown option: ${argument}`);
    } else {
      options.urls.push(argument);
    }
  }
  if (options.urls.length > 2) throw new Error("at most two target URLs are accepted");
  return options;
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

const options = parseArguments(process.argv.slice(2));

const targets = [
  {
    alias: "haiku",
    url: options.urls[0] || "http://127.0.0.1:4178/",
    row: "#workorder-body tr",
    search: "#search-input",
    clear: "#clear-filters",
    opener: ".view-detail-btn",
    detail: "#detail-overlay",
    mobileOverlayOnly: false,
    isOpen: (node) => !node.hasAttribute("hidden"),
  },
  {
    alias: "opus",
    url: options.urls[1] || "http://127.0.0.1:4179/",
    row: "#work-list .wo",
    search: "#f-search",
    clear: "#clear-filters",
    opener: "#work-list .wo",
    detail: "#detail",
    mobileOverlayOnly: true,
    isOpen: (node) => node.classList.contains("is-open"),
  },
];

const viewports = [
  { name: "desktop", width: 1440, height: 1000 },
  { name: "mobile", width: 390, height: 844 },
];

function activeSnapshot() {
  const active = document.activeElement;
  if (!active) return null;
  const style = getComputedStyle(active);
  return {
    tag: active.tagName.toLowerCase(),
    id: active.id || null,
    dataId: active.dataset ? active.dataset.id || null : null,
    text: (active.textContent || "").trim().slice(0, 80),
    connected: active.isConnected,
    rendered: style.display !== "none" && style.visibility !== "hidden" && active.getClientRects().length > 0,
  };
}

async function clickAndContinue(locator) {
  try {
    await locator.click({ timeout: 1500 });
    return { userClickSucceeded: true, error: null, continuationUsedDomClick: false };
  } catch (error) {
    const summary = String(error && error.message ? error.message : error).split("\n")[0];
    const result = { userClickSucceeded: false, error: summary, continuationUsedDomClick: false };
    if (options.diagnostic) {
      try {
        await locator.evaluate((node) => node.click());
        result.continuationUsedDomClick = true;
      } catch (fallbackError) {
        result.continuationError = String(
          fallbackError && fallbackError.message ? fallbackError.message : fallbackError
        ).split("\n")[0];
      }
    }
    return result;
  }
}

function acceptanceIssues(result) {
  const issues = [];
  if (result.initialRows < 1) issues.push("initial_rows_missing");
  if (result.zeroRows !== 0) issues.push("search_did_not_reach_empty_state");
  if (!result.clearAction.userClickSucceeded) issues.push("clear_control_not_user_clickable");
  if (result.restoredRows !== result.initialRows) issues.push("clear_did_not_restore_rows");
  if (!result.noPageOverflow) issues.push("page_overflow");
  if (result.reducedMotionRunningAnimationsAfter30ms !== 0) issues.push("reduced_motion_animation_running");
  if (result.consoleErrors.length) issues.push("console_errors");
  if (result.externalRequests.length) issues.push("external_requests_attempted");
  if (result.requestFailures.length) issues.push("request_failures");
  if (result.badResponses.length) issues.push("http_error_responses");
  if (!result.detail.openAction.userClickSucceeded) issues.push("detail_control_not_user_clickable");
  if (result.detail.overlayApplicable) {
    if (!result.detail.opened) issues.push("detail_overlay_did_not_open");
    if (!result.detail.closed) issues.push("detail_overlay_did_not_close_with_escape");
    if (!result.detail.focusReturned) issues.push("detail_focus_not_returned");
    if (result.detail.isolation.bodyOverflow === "visible") issues.push("modal_did_not_lock_page_scroll");
    if (result.detail.isolation.inertElements < 1 && result.detail.isolation.ariaHiddenElements < 1) {
      issues.push("modal_background_not_isolated");
    }
  }
  return issues;
}

async function auditTarget(browser, target, viewport) {
  const allowedOrigin = new URL(target.url).origin;
  const externalRequests = [];
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    reducedMotion: "reduce",
    locale: "zh-TW",
    serviceWorkers: "block",
  });
  await installExactOriginRoutes(context, allowedOrigin, externalRequests);
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

  await page.goto(target.url, { waitUntil: "networkidle" });
  await page.waitForTimeout(30);
  const initialRows = await page.locator(target.row).count();
  const layout = await page.evaluate(() => ({
    viewportWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
    runningAnimations: document.getAnimations().filter((item) => item.playState === "running").length,
  }));

  await page.locator(target.search).fill("不存在-Playwright-查核");
  await page.waitForTimeout(20);
  const zeroRows = await page.locator(target.row).count();
  const clearAction = await clickAndContinue(page.locator(target.clear));
  await page.waitForTimeout(20);
  const restoredRows = await page.locator(target.row).count();

  // A failed user click must remain a failed assertion. Reload only separates the
  // following detail test from the broken filter state; it does not repair it.
  let resetAfterClearFailure = false;
  if (!clearAction.userClickSucceeded && !clearAction.continuationUsedDomClick) {
    await page.reload({ waitUntil: "networkidle" });
    resetAfterClearFailure = true;
  }

  const opener = page.locator(target.opener).first();
  const openerId = await opener.getAttribute("data-id");
  const openAction = await clickAndContinue(opener);
  await page.waitForTimeout(20);
  const overlayApplicable = !target.mobileOverlayOnly || viewport.name === "mobile";
  const opened = overlayApplicable ? await page.locator(target.detail).evaluate(target.isOpen) : null;
  const openState = await page.evaluate(activeSnapshot);
  const isolation = await page.evaluate(() => ({
    bodyOverflow: getComputedStyle(document.body).overflow,
    inertElements: document.querySelectorAll("[inert]").length,
    ariaHiddenElements: document.querySelectorAll('[aria-hidden="true"]').length,
  }));

  let closed = null;
  let closeState = null;
  let focusReturned = null;
  if (overlayApplicable) {
    await page.keyboard.press("Escape");
    await page.waitForTimeout(20);
    closed = !(await page.locator(target.detail).evaluate(target.isOpen));
    closeState = await page.evaluate(activeSnapshot);
    focusReturned = Boolean(
      closeState && closeState.rendered && closeState.connected && openerId && closeState.dataId === openerId
    );
  }

  await context.close();
  const result = {
    viewport: viewport.name,
    size: `${viewport.width}x${viewport.height}`,
    initialRows,
    zeroRows,
    restoredRows,
    clearAction,
    resetAfterClearFailure,
    noPageOverflow: layout.scrollWidth <= layout.viewportWidth,
    reducedMotionRunningAnimationsAfter30ms: layout.runningAnimations,
    detail: { overlayApplicable, openAction, opened, openFocus: openState, isolation, closed, closeFocus: closeState, focusReturned },
    consoleErrors,
    externalRequests,
    requestFailures,
    badResponses,
  };
  result.acceptanceIssues = acceptanceIssues(result);
  result.acceptancePassed = result.acceptanceIssues.length === 0;
  return result;
}

(async () => {
  const launch = { headless: true };
  if (process.env.CHROME_EXECUTABLE_PATH) launch.executablePath = process.env.CHROME_EXECUTABLE_PATH;
  const browser = await chromium.launch(launch);
  const report = {
    schema_version: 2,
    generated_at: new Date().toISOString(),
    mode: options.diagnostic ? "diagnostic" : "acceptance",
    automation: `Playwright ${require("playwright/package.json").version}`,
    browser: await browser.version(),
    results: [],
  };
  try {
    for (const target of targets) {
      const run = { alias: target.alias, url: target.url, viewports: [] };
      for (const viewport of viewports) run.viewports.push(await auditTarget(browser, target, viewport));
      report.results.push(run);
    }
  } finally {
    await browser.close();
  }
  const failed = report.results.flatMap((target) => target.viewports).filter((result) => !result.acceptancePassed);
  report.summary = {
    checkedViewports: report.results.reduce((count, target) => count + target.viewports.length, 0),
    failedViewports: failed.length,
    verdict: options.diagnostic ? "diagnostic_only" : failed.length ? "failed" : "passed",
  };
  const serialized = `${JSON.stringify(report, null, 2)}\n`;
  if (options.output) fs.writeFileSync(options.output, serialized, { encoding: "utf8", flag: "wx" });
  process.stdout.write(serialized);
  if (!options.diagnostic && failed.length) process.exitCode = 1;
})().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exitCode = 1;
});
