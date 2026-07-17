#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { chromium, firefox, webkit } = require("playwright");
const { auditV7A1Typography, validateSpecs } = require("./v7_a1_typography_metrics.cjs");
const { auditFocusedControls } = require("./v7_focus_obscuration.cjs");

const MAX_JSON_BYTES = 1024 * 1024;
const MAX_PAGE_WIDTH = 10_000;
const MAX_PAGE_HEIGHT = 30_000;
const MAX_SCREENSHOT_PIXELS = 100_000_000;
const MAX_RUNTIME_EVENTS = 50;
const ENGINES = { chromium, firefox, webkit };
const PROFILES = Object.freeze({
  desktop: { width: 1440, height: 1000, deviceScaleFactor: 1, hasTouch: false, isMobile: false },
  "standard-desktop": { width: 1280, height: 720, deviceScaleFactor: 1, hasTouch: false, isMobile: false },
  "short-desktop": { width: 1024, height: 600, deviceScaleFactor: 1, hasTouch: false, isMobile: false },
  tablet: { width: 768, height: 1024, deviceScaleFactor: 2, hasTouch: true, isMobile: false },
  mobile: { width: 390, height: 844, deviceScaleFactor: 3, hasTouch: true, isMobile: true },
  "compact-mobile": { width: 360, height: 800, deviceScaleFactor: 3, hasTouch: true, isMobile: true },
});
const MOBILE_UA = Object.freeze({
  chromium: "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0 Mobile Safari/537.36",
  firefox: "Mozilla/5.0 (Android 15; Mobile; rv:148.0) Gecko/148.0 Firefox/148.0",
  webkit: "Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 Mobile/15E148 Safari/604.1",
});

function fail(message) {
  throw new Error(message);
}

function parseArguments(argv) {
  const allowed = new Set(["url", "variant", "case-id", "state", "profile", "engine", "spec", "screenshot", "output"]);
  const result = {};
  for (let index = 0; index < argv.length; index += 2) {
    const raw = argv[index];
    if (!raw?.startsWith("--") || index + 1 >= argv.length) fail("arguments must be --key value pairs");
    const key = raw.slice(2);
    if (!allowed.has(key) || Object.hasOwn(result, key)) fail(`unknown or duplicate argument: ${raw}`);
    result[key] = argv[index + 1];
  }
  for (const key of allowed) if (!result[key]) fail(`missing --${key}`);
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(result["case-id"])) fail("case-id must be lowercase kebab-case");
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(result.state)) fail("state must be lowercase kebab-case");
  if (!["accepted", "candidate"].includes(result.variant)) fail("variant must be accepted or candidate");
  if (!Object.hasOwn(PROFILES, result.profile)) fail("unknown profile");
  if (!Object.hasOwn(ENGINES, result.engine)) fail("unknown engine");
  return result;
}

function regularInput(file, label) {
  const absolute = path.resolve(file);
  const stat = fs.lstatSync(absolute);
  if (!stat.isFile() || stat.isSymbolicLink()) fail(`${label} must be a regular non-symlink file`);
  if (stat.size > MAX_JSON_BYTES) fail(`${label} is too large`);
  return absolute;
}

function freshOutput(file, label) {
  const absolute = path.resolve(file);
  if (fs.existsSync(absolute)) fail(`${label} already exists`);
  const parent = path.dirname(absolute);
  const stat = fs.lstatSync(parent);
  if (!stat.isDirectory() || stat.isSymbolicLink()) fail(`${label} parent must be a regular directory`);
  return absolute;
}

function boundedString(value, label, maximum = 500) {
  if (typeof value !== "string" || value.length < 1 || value.length > maximum || value.trim() !== value) fail(`${label} is invalid`);
  return value;
}

function validateStep(step, index) {
  if (!step || typeof step !== "object" || Array.isArray(step)) fail(`steps[${index}] must be an object`);
  const action = step.action;
  const schemas = {
    click: ["action", "id", "selector"],
    fill: ["action", "id", "selector", "value"],
    select: ["action", "id", "selector", "value"],
    press: ["action", "id", "selector", "value"],
  };
  if (!Object.hasOwn(schemas, action) || Object.keys(step).sort().join("|") !== schemas[action].sort().join("|")) {
    fail(`steps[${index}] has an invalid action contract`);
  }
  if (typeof step.id !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(step.id)) fail(`steps[${index}].id is invalid`);
  boundedString(step.selector, `steps[${index}].selector`, 300);
  if (step.value !== undefined) boundedString(step.value, `steps[${index}].value`, 300);
  return step;
}

function validateAssertion(assertion, index) {
  if (!assertion || typeof assertion !== "object" || Array.isArray(assertion)) fail(`assertions[${index}] must be an object`);
  const schemas = {
    visible: ["id", "selector", "type"],
    hidden: ["id", "selector", "type"],
    text: ["id", "selector", "type", "value"],
  };
  if (!Object.hasOwn(schemas, assertion.type)
      || Object.keys(assertion).sort().join("|") !== schemas[assertion.type].sort().join("|")) {
    fail(`assertions[${index}] has an invalid contract`);
  }
  if (typeof assertion.id !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(assertion.id)) fail(`assertions[${index}].id is invalid`);
  boundedString(assertion.selector, `assertions[${index}].selector`, 300);
  if (assertion.value !== undefined) boundedString(assertion.value, `assertions[${index}].value`, 300);
  return assertion;
}

function validateFocusTargets(focusTargets, steps) {
  if (!Array.isArray(focusTargets) || focusTargets.length < 1 || focusTargets.length > 8) {
    fail("spec focusTargets must contain 1..8 entries");
  }
  const stepById = new Map(steps.map((step) => [step.id, step]));
  const allowedActions = {
    "form-control": new Set(["fill", "select"]),
    "primary-action": new Set(["click", "press"]),
  };
  const targets = focusTargets.map((target, index) => {
    if (!target || typeof target !== "object" || Array.isArray(target)
        || Object.keys(target).sort().join("|") !== "id|role|stepId") {
      fail(`focusTargets[${index}] has an invalid contract`);
    }
    if (typeof target.id !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(target.id)) {
      fail(`focusTargets[${index}].id is invalid`);
    }
    if (typeof target.stepId !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(target.stepId)) {
      fail(`focusTargets[${index}].stepId is invalid`);
    }
    if (!Object.hasOwn(allowedActions, target.role)) fail(`focusTargets[${index}].role is invalid`);
    const step = stepById.get(target.stepId);
    if (!step) fail(`focusTargets[${index}].stepId does not identify a step`);
    if (!allowedActions[target.role].has(step.action)) fail(`focusTargets[${index}] role does not match its step action`);
    return target;
  });
  for (const key of ["id", "stepId"]) {
    const values = targets.map((target) => target[key]);
    if (values.length !== new Set(values).size) fail(`focusTargets ${key}s must be unique`);
  }
  return targets;
}

function loadSpec(file, expectedCase, expectedState) {
  const absolute = regularInput(file, "spec");
  let data;
  try {
    data = JSON.parse(fs.readFileSync(absolute, "utf8"));
  } catch (error) {
    fail(`spec is not valid JSON: ${error.message}`);
  }
  const rootKeys = {
    1: ["assertions", "caseId", "schemaVersion", "state", "steps", "targets"],
    2: ["assertions", "caseId", "focusTargets", "schemaVersion", "state", "steps", "targets"],
  };
  const expectedKeys = data && typeof data === "object" && !Array.isArray(data) ? rootKeys[data.schemaVersion] : null;
  if (!expectedKeys || Object.keys(data).sort().join("|") !== expectedKeys.sort().join("|")) {
    fail("spec root contract is invalid");
  }
  if (data.caseId !== expectedCase || data.state !== expectedState) fail("spec identity does not match CLI identity");
  const minimumEntries = data.state === "interaction" ? 1 : 0;
  if (!Array.isArray(data.steps) || data.steps.length < minimumEntries || data.steps.length > 20) {
    fail(`spec steps must contain ${minimumEntries}..20 entries`);
  }
  if (!Array.isArray(data.assertions) || data.assertions.length < minimumEntries || data.assertions.length > 20) {
    fail(`spec assertions must contain ${minimumEntries}..20 entries`);
  }
  data.targets = validateSpecs(data.targets);
  data.steps = data.steps.map(validateStep);
  data.assertions = data.assertions.map(validateAssertion);
  for (const [label, entries] of [["steps", data.steps], ["assertions", data.assertions]]) {
    const ids = entries.map((entry) => entry.id);
    if (ids.length !== new Set(ids).size) fail(`${label} ids must be unique`);
  }
  if (data.schemaVersion === 2) data.focusTargets = validateFocusTargets(data.focusTargets, data.steps);
  return { absolute, data };
}

function targetUrl(raw) {
  let parsed;
  try {
    parsed = new URL(raw);
  } catch {
    fail("url is invalid");
  }
  if (parsed.protocol === "file:") return parsed;
  const loopback = new Set(["127.0.0.1", "localhost", "[::1]"]);
  if (!["http:", "https:"].includes(parsed.protocol) || !loopback.has(parsed.hostname)) {
    fail("url must use file: or loopback HTTP(S)");
  }
  return parsed;
}

function sha256(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function pngDimensions(file) {
  const body = fs.readFileSync(file);
  const signature = "89504e470d0a1a0a";
  if (body.length < 24 || body.subarray(0, 8).toString("hex") !== signature || body.subarray(12, 16).toString("ascii") !== "IHDR") {
    fail("screenshot is not a complete PNG");
  }
  return { width: body.readUInt32BE(16), height: body.readUInt32BE(20), bytes: body.length, sha256: sha256(file) };
}

async function applySteps(page, steps, blockedStepId = null) {
  const attempts = [];
  let priorStepNotCompleted = false;
  for (const step of steps) {
    if (priorStepNotCompleted) {
      attempts.push({ id: step.id, action: step.action, completed: false, reason: "prior_step_not_completed" });
      continue;
    }
    if (step.id === blockedStepId) {
      attempts.push({ id: step.id, action: step.action, completed: false, reason: "focused_control_obscured" });
      priorStepNotCompleted = true;
      continue;
    }
    const locator = page.locator(step.selector);
    if (await locator.count() !== 1) fail(`interaction selector must resolve exactly once: ${step.selector}`);
    if (step.action === "click") await locator.click();
    else if (step.action === "fill") await locator.fill(step.value);
    else if (step.action === "select") await locator.selectOption(step.value);
    else await locator.press(step.value);
    attempts.push({ id: step.id, action: step.action, completed: true });
  }
  return attempts;
}

async function runAssertions(page, assertions) {
  const results = [];
  for (const assertion of assertions) {
    const locator = page.locator(assertion.selector);
    const count = await locator.count();
    let passed = false;
    if (assertion.type === "visible") passed = count === 1 && await locator.isVisible();
    else if (assertion.type === "hidden") passed = count === 0 || (count === 1 && !(await locator.isVisible()));
    else passed = count === 1 && (await locator.textContent() || "").includes(assertion.value);
    results.push({ id: assertion.id, type: assertion.type, count, passed });
  }
  return results;
}

function unavailableAssertions(assertions) {
  return assertions.map((assertion) => ({
    id: assertion.id,
    type: assertion.type,
    evaluated: false,
    reason: "interaction_state_unavailable",
  }));
}

async function main() {
  const args = parseArguments(process.argv.slice(2));
  const spec = loadSpec(args.spec, args["case-id"], args.state);
  const url = targetUrl(args.url);
  const screenshot = freshOutput(args.screenshot, "screenshot");
  const output = freshOutput(args.output, "output");
  const profile = PROFILES[args.profile];
  const browserType = ENGINES[args.engine];
  let browser;
  let context;
  try {
    browser = await browserType.launch({ headless: true });
    const mobileRequested = profile.isMobile;
    const fullMobileEmulation = mobileRequested && args.engine !== "firefox";
    const contextOptions = {
      viewport: { width: profile.width, height: profile.height },
      screen: { width: profile.width, height: profile.height },
      deviceScaleFactor: profile.deviceScaleFactor,
      hasTouch: profile.hasTouch,
      isMobile: fullMobileEmulation,
      userAgent: mobileRequested ? MOBILE_UA[args.engine] : undefined,
      serviceWorkers: "block",
      locale: "zh-TW",
      timezoneId: "Asia/Taipei",
    };
    context = await browser.newContext(contextOptions);
    const externalRequests = [];
  let externalRequestCount = 0;
  const allowedOrigin = url.protocol === "file:" ? null : url.origin;
  await context.route("**/*", async (route) => {
    const requestUrl = new URL(route.request().url());
    const allowed = ["data:", "blob:"].includes(requestUrl.protocol)
      || (url.protocol === "file:" && requestUrl.href === url.href)
      || (allowedOrigin !== null && requestUrl.origin === allowedOrigin);
    if (allowed) await route.continue();
    else {
      externalRequestCount += 1;
      if (externalRequests.length < MAX_RUNTIME_EVENTS) externalRequests.push({
        method: route.request().method().slice(0, 20),
        resourceType: route.request().resourceType(),
        destination: requestUrl.protocol === "file:" ? "blocked-local-file" : "blocked-network",
      });
      await route.abort("blockedbyclient");
    }
  });
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  let consoleErrorCount = 0;
  let pageErrorCount = 0;
  page.on("console", (message) => {
    if (message.type() !== "error") return;
    consoleErrorCount += 1;
    if (consoleErrors.length < MAX_RUNTIME_EVENTS) consoleErrors.push(message.text().slice(0, 500));
  });
  page.on("pageerror", (error) => {
    pageErrorCount += 1;
    if (pageErrors.length < MAX_RUNTIME_EVENTS) pageErrors.push(error.message.slice(0, 500));
  });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto(url.href, { waitUntil: "domcontentloaded", timeout: 30_000 });
  await page.addStyleTag({ content: "*,*::before,*::after{animation-duration:0.001ms!important;animation-delay:0ms!important;transition-duration:0.001ms!important;transition-delay:0ms!important}" });
  let fontTimer;
  const fontsReady = await Promise.race([
    page.evaluate(() => document.fonts.ready.then(() => true)),
    new Promise((resolve) => { fontTimer = setTimeout(() => resolve(false), 10_000); }),
  ]).finally(() => clearTimeout(fontTimer));
  const focusEvidence = await auditFocusedControls(browser, url, contextOptions, spec.data);
  const focusById = new Map(focusEvidence.focusedControls.map((control) => [control.id, control]));
  const confirmedClickStepIds = spec.data.schemaVersion === 2 && focusEvidence.focusCoverage.status === "complete"
    ? new Set(spec.data.focusTargets.filter((target) => {
        const step = spec.data.steps.find((item) => item.id === target.stepId);
        const control = focusById.get(target.id);
        return step?.action === "click" && control?.status === "confirmed" && control.fullyObscured === true;
      }).map((target) => target.stepId))
    : new Set();
  const blockedStepId = spec.data.steps.find((step) => confirmedClickStepIds.has(step.id))?.id || null;
  const resultSchemaVersion = blockedStepId === null ? spec.data.schemaVersion : 3;
  const resultFocusEvidence = resultSchemaVersion === 3 ? {
    focusCoverage: focusEvidence.focusCoverage,
    focusedControls: focusEvidence.focusedControls.map((control) => ({
      ...control,
      stepId: spec.data.focusTargets.find((target) => target.id === control.id).stepId,
    })),
  } : focusEvidence;
  const interactions = await applySteps(page, spec.data.steps, blockedStepId);
  await page.waitForTimeout(150);
  const assertions = blockedStepId === null
    ? await runAssertions(page, spec.data.assertions)
    : unavailableAssertions(spec.data.assertions);
  const typography = await page.evaluate(auditV7A1Typography, spec.data.targets);
  const pageBounds = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight }));
  const horizontalOverflow = pageBounds.width > profile.width + 2;
  const devicePixelArea = pageBounds.width * pageBounds.height * profile.deviceScaleFactor ** 2;
  const fullPage = pageBounds.width <= MAX_PAGE_WIDTH && pageBounds.height <= MAX_PAGE_HEIGHT
    && devicePixelArea <= MAX_SCREENSHOT_PIXELS;
  const eventOverflow = consoleErrorCount > MAX_RUNTIME_EVENTS
    || pageErrorCount > MAX_RUNTIME_EVENTS || externalRequestCount > MAX_RUNTIME_EVENTS;
  const focusedControlObscured = focusEvidence.focusedControls.some(
    (control) => control.status === "confirmed" && control.fullyObscured === true,
  );
  const focusVerificationUnavailable = spec.data.schemaVersion === 2
    && focusEvidence.focusCoverage.status === "unavailable";
  await page.screenshot({ path: screenshot, fullPage, animations: "disabled" });
  const evidence = {
    schemaVersion: resultSchemaVersion,
    identity: { variant: args.variant, caseId: args["case-id"], state: args.state, profile: args.profile, engine: args.engine },
    input: { scheme: url.protocol.slice(0, -1), route: url.pathname.split("/").pop() || "/", specSha256: sha256(spec.absolute) },
    browser: {
      playwright: require("playwright/package.json").version,
      engineVersion: browser.version(),
      profile: { ...profile, fullMobileEmulation, userAgent: await page.evaluate(() => navigator.userAgent) },
    },
    runtime: {
      fontsReady,
      interactions,
      assertions,
      consoleErrors,
      pageErrors,
      externalRequests,
      pageBounds,
      devicePixelArea,
      horizontalOverflow,
      eventOverflow,
      ...(spec.data.schemaVersion === 2 ? {
        focusCoverage: resultFocusEvidence.focusCoverage,
        focusedControls: resultFocusEvidence.focusedControls,
      } : {}),
      eventCounts: { consoleErrors: consoleErrorCount, pageErrors: pageErrorCount, externalRequests: externalRequestCount },
      issues: [
        ...(horizontalOverflow ? ["page_horizontal_overflow"] : []),
        ...(!fullPage ? ["page_capture_area_exceeded"] : []),
        ...(eventOverflow ? ["runtime_event_limit_exceeded"] : []),
        ...(focusedControlObscured ? ["focused_control_obscured"] : []),
        ...(focusVerificationUnavailable ? ["focus_obscuration_verification_unavailable"] : []),
      ],
    },
    typography,
    verdict: fontsReady && fullPage && !horizontalOverflow && !eventOverflow && !focusedControlObscured
      && !focusVerificationUnavailable
      && assertions.every((item) => item.passed)
      && consoleErrors.length === 0 && pageErrors.length === 0 && externalRequests.length === 0
      && typography.issues.length === 0 ? "clean" : "findings",
    screenshot: { path: path.basename(screenshot), fullPage, ...pngDimensions(screenshot) },
  };
  fs.writeFileSync(output, `${JSON.stringify(evidence, null, 2)}\n`, { encoding: "utf8", flag: "wx", mode: 0o600 });
    process.stdout.write(`${JSON.stringify({ verdict: evidence.verdict, output, screenshot })}\n`);
    process.exitCode = evidence.verdict === "clean" ? 0 : 2;
  } finally {
    await context?.close().catch(() => {});
    await browser?.close().catch(() => {});
  }
}

if (require.main === module) {
  main().catch((error) => {
    console.error(`v7 A1 audit failed: ${error.message}`);
    process.exitCode = 1;
  });
}

module.exports = { PROFILES, loadSpec, parseArguments, pngDimensions, targetUrl, validateFocusTargets };
