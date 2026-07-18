"use strict";

const CLAIM_BOUNDARY = "two fresh evaluator-controlled invalid-input preservation replays";
const ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const MAX_TARGETS = 8;
const OPERATION_TIMEOUT_MS = 5000;
const SAFE_EVALUATOR_VALUE = /^eval-preserve-[a-z0-9-]{1,40}$/;

function fail(message) {
  throw new TypeError(message);
}

function validateInvalidInputPreservationTargets(targets, steps) {
  if (!Array.isArray(targets) || targets.length < 1 || targets.length > MAX_TARGETS) {
    fail("invalidInputPreservationTargets must contain 1..8 entries");
  }
  if (!Array.isArray(steps) || steps.length < 2 || steps.length > 20) fail("steps must contain 2..20 entries");
  const stepById = new Map(steps.map((step, index) => [step.id, { step, index }]));
  if (stepById.size !== steps.length) fail("step ids must be unique");
  const ids = new Set();
  const controlStepIds = new Set();
  for (const [index, target] of targets.entries()) {
    if (!target || typeof target !== "object" || Array.isArray(target)
        || Object.keys(target).sort().join("|") !== "controlStepId|id|invalidationStepId|normalization") {
      fail(`invalidInputPreservationTargets[${index}] contract is invalid`);
    }
    if (typeof target.id !== "string" || !ID.test(target.id) || ids.has(target.id)) {
      fail("invalid-input preservation ids must be unique lowercase kebab-case");
    }
    ids.add(target.id);
    if (target.normalization !== "none") fail("invalid-input preservation requires normalization=none");
    if (typeof target.controlStepId !== "string" || !ID.test(target.controlStepId)
        || controlStepIds.has(target.controlStepId)) fail("controlStepIds must be unique lowercase kebab-case");
    controlStepIds.add(target.controlStepId);
    if (typeof target.invalidationStepId !== "string" || !ID.test(target.invalidationStepId)) {
      fail(`invalidInputPreservationTargets[${index}].invalidationStepId is invalid`);
    }
    const control = stepById.get(target.controlStepId);
    const invalidation = stepById.get(target.invalidationStepId);
    if (!control || !invalidation || invalidation.index !== control.index + 1) {
      fail(`invalidInputPreservationTargets[${index}] steps must be adjacent and ordered`);
    }
    if (!["fill", "select"].includes(control.step.action)) fail("control step must use fill or select");
    if (typeof control.step.value !== "string" || !SAFE_EVALUATOR_VALUE.test(control.step.value)) {
      fail("control step value must be a bounded evaluator-owned synthetic token");
    }
    if (!["click", "press"].includes(invalidation.step.action)) fail("invalidation step must use click or press");
  }
  return targets;
}

function aggregateInvalidInputPreservationResults(targets, replayResults) {
  const records = targets.map((target) => {
    const replays = replayResults.get(target.id) || [];
    const base = { id: target.id, replays: replays.length };
    if (replays.length !== 2 || replays.some((item) => !item
        || !["retained", "lost", "unavailable"].includes(item.status))) {
      return { ...base, status: "unavailable", reason: "runtime_unavailable" };
    }
    if (replays.some((item) => item.status === "unavailable")) {
      const reason = replays.find((item) => item.status === "unavailable").reason;
      return {
        ...base,
        status: "unavailable",
        reason: ["preservation_contract_unavailable", "external_request_blocked", "runtime_unavailable"].includes(reason)
          ? reason : "runtime_unavailable",
      };
    }
    if (replays[0].status !== replays[1].status || replays[0].nativeKind !== replays[1].nativeKind) {
      return { ...base, status: "unavailable", reason: "replay_unstable" };
    }
    const retained = replays[0].status === "retained";
    return {
      ...base,
      status: retained ? "clear" : "confirmed",
      nativeKind: replays[0].nativeKind,
      retained,
    };
  });
  const completedTargets = records.filter((record) => record.status !== "unavailable").length;
  return {
    coverage: {
      status: completedTargets === targets.length ? "complete" : "unavailable",
      reason: completedTargets === targets.length ? null : "one_or_more_targets_unavailable",
      declaredTargets: targets.length,
      completedTargets,
      freshReplays: [...replayResults.values()].reduce((total, items) => total + items.length, 0),
      claimBoundary: CLAIM_BOUNDARY,
    },
    records,
  };
}

async function applyStep(page, step) {
  try {
    const locator = page.locator(step.selector);
    if (await locator.count() !== 1) return false;
    if (!(await locator.isVisible())) return false;
    if (step.action === "click") await locator.click({ timeout: OPERATION_TIMEOUT_MS });
    else if (step.action === "fill") await locator.fill(step.value, { timeout: OPERATION_TIMEOUT_MS });
    else if (step.action === "select") await locator.selectOption(step.value, { timeout: OPERATION_TIMEOUT_MS });
    else if (step.action === "press") await locator.press(step.value, { timeout: OPERATION_TIMEOUT_MS });
    else return false;
    return true;
  } catch {
    return false;
  }
}

async function replayInvalidInputPreservationTarget(browser, url, contextOptions, target, steps) {
  let context;
  try {
    context = await browser.newContext(contextOptions);
    let blockedExternalRequests = 0;
    const allowedOrigin = url.protocol === "file:" ? null : url.origin;
    await context.route("**/*", async (route) => {
      const requestUrl = new URL(route.request().url());
      const allowed = ["data:", "blob:"].includes(requestUrl.protocol)
        || (url.protocol === "file:" && requestUrl.href === url.href)
        || (allowedOrigin !== null && requestUrl.origin === allowedOrigin);
      if (allowed) await route.continue();
      else {
        blockedExternalRequests += 1;
        await route.abort("blockedbyclient");
      }
    });
    const page = await context.newPage();
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto(url.href, { waitUntil: "domcontentloaded", timeout: 30_000 });
    let fontTimer;
    const fontsReady = await Promise.race([
      page.evaluate(() => document.fonts.ready.then(() => true)),
      new Promise((resolve) => { fontTimer = setTimeout(() => resolve(false), 10_000); }),
    ]).finally(() => clearTimeout(fontTimer));
    if (!fontsReady) return { status: "unavailable", reason: "runtime_unavailable" };
    if (blockedExternalRequests) return { status: "unavailable", reason: "external_request_blocked" };

    const invalidationIndex = steps.findIndex((step) => step.id === target.invalidationStepId);
    if (invalidationIndex < 0) return { status: "unavailable", reason: "preservation_contract_unavailable" };
    for (let index = 0; index < invalidationIndex; index += 1) {
      if (!(await applyStep(page, steps[index]))) {
        return { status: "unavailable", reason: "preservation_contract_unavailable" };
      }
    }
    const controlStep = steps.find((step) => step.id === target.controlStepId);
    if (!controlStep || typeof controlStep.value !== "string") {
      return { status: "unavailable", reason: "preservation_contract_unavailable" };
    }
    let control = page.locator(controlStep.selector);
    if (await control.count() !== 1 || !(await control.isVisible())) {
      return { status: "unavailable", reason: "preservation_contract_unavailable" };
    }
    const inspectNativeKind = (locator) => locator.evaluate((node) => {
      if (node.getRootNode() !== document) return null;
      const tag = node.tagName.toLowerCase();
      if (tag === "textarea") return "textarea";
      if (tag === "select") return !node.multiple && node.size <= 1 ? "select-one" : null;
      if (tag !== "input") return null;
      const type = (node.getAttribute("type") || "text").toLowerCase();
      return ["text", "search", "email", "tel", "url", "number"].includes(type) ? `input-${type}` : null;
    });
    const nativeKind = await inspectNativeKind(control);
    if (!nativeKind || await control.getAttribute("aria-invalid") === "true") {
      return { status: "unavailable", reason: "preservation_contract_unavailable" };
    }
    const valueBeforeInvalidation = await control.inputValue();
    if (!(await applyStep(page, steps[invalidationIndex]))) {
      return { status: "unavailable", reason: "preservation_contract_unavailable" };
    }
    await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    if (blockedExternalRequests) return { status: "unavailable", reason: "external_request_blocked" };
    control = page.locator(controlStep.selector);
    if (await control.count() !== 1 || !(await control.isVisible())
        || await inspectNativeKind(control) !== nativeKind
        || await control.getAttribute("aria-invalid") !== "true") {
      return { status: "unavailable", reason: "preservation_contract_unavailable" };
    }
    const retained = await control.inputValue() === valueBeforeInvalidation;
    return { status: retained ? "retained" : "lost", nativeKind };
  } catch {
    return { status: "unavailable", reason: "runtime_unavailable" };
  } finally {
    await context?.close().catch(() => {});
  }
}

async function auditInvalidInputPreservationTargets(browser, url, contextOptions, spec, replayRunner = replayInvalidInputPreservationTarget) {
  validateInvalidInputPreservationTargets(spec.invalidInputPreservationTargets, spec.steps);
  const replayResults = new Map();
  for (const target of spec.invalidInputPreservationTargets) {
    const results = [];
    for (let replay = 0; replay < 2; replay += 1) {
      results.push(await replayRunner(browser, url, contextOptions, target, spec.steps));
    }
    replayResults.set(target.id, results);
  }
  return aggregateInvalidInputPreservationResults(spec.invalidInputPreservationTargets, replayResults);
}

module.exports = {
  CLAIM_BOUNDARY,
  aggregateInvalidInputPreservationResults,
  auditInvalidInputPreservationTargets,
  replayInvalidInputPreservationTarget,
  validateInvalidInputPreservationTargets,
};
