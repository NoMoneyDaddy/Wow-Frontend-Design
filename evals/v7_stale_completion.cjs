"use strict";

const INTERNAL_PLAN = Symbol("v7StaleCompletionPlan");
const ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const MAX_BODY_BYTES = 16 * 1024;
const OPERATION_TIMEOUT_MS = 3000;
const QUIESCENCE_MS = 750;

function fail(message) {
  throw new TypeError(message);
}

function exactObject(value, keys, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)
      || Object.keys(value).sort().join("|") !== [...keys].sort().join("|")) fail(`${label} contract is invalid`);
}

function boundedString(value, label, maximum = 300) {
  if (typeof value !== "string" || value.length < 1 || value.length > maximum || value.trim() !== value) {
    fail(`${label} is invalid`);
  }
  return value;
}

function recordId(value, label) {
  if (typeof value !== "string" || !ID.test(value)) fail(`${label} is invalid`);
  return value;
}

function validatePredicate(predicate, label) {
  exactObject(predicate, ["text", "value"].includes(predicate?.type)
    ? ["id", "selector", "type", "value"] : ["id", "selector", "type"], label);
  recordId(predicate.id, `${label}.id`);
  boundedString(predicate.selector, `${label}.selector`);
  if (!["visible", "hidden", "text", "value"].includes(predicate.type)) fail(`${label}.type is invalid`);
  if (["text", "value"].includes(predicate.type)) boundedString(predicate.value, `${label}.value`, 500);
  return predicate;
}

function validateAsyncCompletion(declaration, steps) {
  exactObject(declaration, [
    "freshness", "id", "initiationStepId", "interruptionStepId", "pending", "request",
  ], "asyncCompletion");
  recordId(declaration.id, "asyncCompletion.id");
  if (!Array.isArray(steps) || steps.length !== 2) fail("stale-completion steps must contain exactly 2 entries");
  const stepIds = steps.map((step, index) => {
    if (!step || typeof step !== "object" || Array.isArray(step)) fail(`steps[${index}] is invalid`);
    return recordId(step.id, `steps[${index}].id`);
  });
  if (stepIds.length !== new Set(stepIds).size) fail("step ids must be unique");
  recordId(declaration.initiationStepId, "asyncCompletion.initiationStepId");
  recordId(declaration.interruptionStepId, "asyncCompletion.interruptionStepId");
  const initiationIndex = stepIds.indexOf(declaration.initiationStepId);
  const interruptionIndex = stepIds.indexOf(declaration.interruptionStepId);
  if (initiationIndex !== 0 || interruptionIndex !== 1) {
    fail("asyncCompletion steps must exist, be adjacent, and preserve initiation/interruption order");
  }

  exactObject(declaration.request, ["fulfill", "id", "method", "path"], "asyncCompletion.request");
  recordId(declaration.request.id, "asyncCompletion.request.id");
  if (!["GET", "POST"].includes(declaration.request.method)) fail("asyncCompletion.request.method is invalid");
  const requestPath = boundedString(declaration.request.path, "asyncCompletion.request.path", 500);
  if (!requestPath.startsWith("/") || requestPath.startsWith("//") || requestPath.includes("#")) {
    fail("asyncCompletion.request.path must be a same-origin absolute path");
  }
  const parsedPath = new URL(requestPath, "https://evaluator.invalid");
  if (parsedPath.origin !== "https://evaluator.invalid" || `${parsedPath.pathname}${parsedPath.search}` !== requestPath) {
    fail("asyncCompletion.request.path must be canonical");
  }
  exactObject(declaration.request.fulfill, ["body", "contentType", "status"], "asyncCompletion.request.fulfill");
  const fulfill = declaration.request.fulfill;
  if (!Number.isInteger(fulfill.status) || fulfill.status < 200 || fulfill.status > 599) {
    fail("asyncCompletion.request.fulfill.status is invalid");
  }
  boundedString(fulfill.contentType, "asyncCompletion.request.fulfill.contentType", 100);
  if (/\r|\n/.test(fulfill.contentType)) fail("asyncCompletion.request.fulfill.contentType is invalid");
  if (typeof fulfill.body !== "string" || Buffer.byteLength(fulfill.body, "utf8") > MAX_BODY_BYTES) {
    fail("asyncCompletion.request.fulfill.body is invalid");
  }

  const pending = validatePredicate(declaration.pending, "asyncCompletion.pending");
  exactObject(declaration.freshness, ["content", "identity", "success"], "asyncCompletion.freshness");
  const identity = validatePredicate(declaration.freshness.identity, "asyncCompletion.freshness.identity");
  const success = validatePredicate(declaration.freshness.success, "asyncCompletion.freshness.success");
  const content = validatePredicate(declaration.freshness.content, "asyncCompletion.freshness.content");
  if (!["text", "value"].includes(identity.type)) fail("freshness identity must use text or value");
  const predicateIds = [pending.id, identity.id, success.id, content.id];
  if (predicateIds.length !== new Set(predicateIds).size) fail("asyncCompletion predicate ids must be unique");

  Object.defineProperty(declaration, INTERNAL_PLAN, {
    configurable: true,
    enumerable: false,
    value: {
      initiationStep: steps[initiationIndex],
      interruptionStep: steps[interruptionIndex],
    },
  });
  return declaration;
}

function fixedResult(declaration) {
  const safe = (value) => typeof value === "string" && ID.test(value) ? value : null;
  const freshness = declaration?.freshness || {};
  return {
    declarationId: safe(declaration?.id),
    requestId: safe(declaration?.request?.id),
    initiationStepId: safe(declaration?.initiationStepId),
    pendingPredicateId: safe(declaration?.pending?.id),
    interruptionStepId: safe(declaration?.interruptionStepId),
    freshnessPredicateIds: [freshness.identity, freshness.success, freshness.content]
      .map((predicate) => safe(predicate?.id)).filter(Boolean),
    request: "unavailable",
    pending: "unavailable",
    interruption: "unavailable",
    release: "not_released",
    freshness: "unavailable",
    reason: "runtime_unavailable",
  };
}

async function withTimeout(promise, timeout = OPERATION_TIMEOUT_MS) {
  let timer;
  return Promise.race([
    promise,
    new Promise((resolve) => { timer = setTimeout(() => resolve(Symbol.for("timeout")), timeout); }),
  ]).finally(() => clearTimeout(timer));
}

async function applyStep(page, step) {
  const locator = page.locator(step.selector);
  if (await locator.count() !== 1) return false;
  if (step.action === "click") await locator.click({ timeout: OPERATION_TIMEOUT_MS });
  else if (step.action === "fill") await locator.fill(step.value, { timeout: OPERATION_TIMEOUT_MS });
  else if (step.action === "select") await locator.selectOption(step.value, { timeout: OPERATION_TIMEOUT_MS });
  else if (step.action === "press") await locator.press(step.value, { timeout: OPERATION_TIMEOUT_MS });
  else return false;
  return true;
}

async function predicateState(page, predicate) {
  try {
    const locator = page.locator(predicate.selector);
    const count = await locator.count();
    if (predicate.type === "hidden") {
      if (count === 0) return { available: true, matched: true, identity: null };
      if (count !== 1) return { available: false, matched: false, identity: null };
      return { available: true, matched: !(await locator.isVisible()), identity: null };
    }
    if (count !== 1) return { available: false, matched: false, identity: null };
    if (predicate.type === "visible") return { available: true, matched: await locator.isVisible(), identity: null };
    const identity = predicate.type === "value" ? await locator.inputValue() : (await locator.textContent() || "");
    return {
      available: true,
      matched: predicate.type === "value" ? identity === predicate.value : identity.includes(predicate.value),
      identity,
    };
  } catch {
    return { available: false, matched: false, identity: null };
  }
}

async function runStaleCompletionReplay(page, url, declaration) {
  const result = fixedResult(declaration);
  const plan = declaration?.[INTERNAL_PLAN];
  if (!plan) return { ...result, reason: "declaration_not_validated" };
  let target;
  let pageUrl;
  try {
    pageUrl = new URL(page.url());
    const base = new URL(url instanceof URL ? url.href : url);
    target = new URL(declaration.request.path, base.origin);
    if (base.origin === "null" || pageUrl.origin !== base.origin || target.origin !== base.origin) {
      return { ...result, reason: "request_origin_unavailable" };
    }
  } catch {
    return { ...result, reason: "request_origin_unavailable" };
  }

  let requestCount = 0;
  let methodMismatch = false;
  let heldRoute = null;
  let releaseMode = null;
  let resolveHeld;
  let resolveRelease;
  let resolveReleaseDone;
  const held = new Promise((resolve) => { resolveHeld = resolve; });
  const release = new Promise((resolve) => { resolveRelease = resolve; });
  const releaseDone = new Promise((resolve) => { resolveReleaseDone = resolve; });
  const handler = async (route) => {
    if (route.request().method() !== declaration.request.method) {
      methodMismatch = true;
      resolveHeld(false);
      await route.abort("blockedbyclient");
      return;
    }
    requestCount += 1;
    if (requestCount > 1) {
      await route.abort("blockedbyclient");
      return;
    }
    heldRoute = route;
    resolveHeld(true);
    await release;
    try {
      if (releaseMode === "fulfill") {
        await route.fulfill({
          status: declaration.request.fulfill.status,
          contentType: declaration.request.fulfill.contentType,
          body: declaration.request.fulfill.body,
        });
        resolveReleaseDone(true);
      } else {
        await route.abort("blockedbyclient");
        resolveReleaseDone(false);
      }
    } catch {
      resolveReleaseDone(false);
    }
  };

  const stopHeldRequest = async () => {
    if (!heldRoute || releaseMode !== null) return;
    releaseMode = "abort";
    resolveRelease();
    await withTimeout(releaseDone);
  };

  await page.route(target.href, handler);
  try {
    if (!(await applyStep(page, plan.initiationStep))) return { ...result, reason: "initiation_unavailable" };
    const observed = await withTimeout(held);
    if (observed === false || methodMismatch) {
      return { ...result, reason: "request_mismatch" };
    }
    if (observed === Symbol.for("timeout")) {
      return { ...result, request: methodMismatch ? "unavailable" : "not_observed", reason: methodMismatch ? "request_mismatch" : "request_not_observed" };
    }
    result.request = "held_once";
    if (requestCount > 1) return { ...result, request: "count_exceeded", reason: "request_count_exceeded" };

    const pending = await predicateState(page, declaration.pending);
    if (!pending.available) return { ...result, reason: "predicate_unavailable" };
    if (!pending.matched) return { ...result, pending: "not_matched", reason: "pending_not_observed" };
    result.pending = "matched";

    const identityBefore = await predicateState(page, declaration.freshness.identity);
    if (!identityBefore.available) return { ...result, reason: "predicate_unavailable" };
    if (!(await applyStep(page, plan.interruptionStep))) return { ...result, reason: "interruption_unavailable" };
    const identityAfter = await predicateState(page, declaration.freshness.identity);
    if (!identityAfter.available) return { ...result, reason: "predicate_unavailable" };
    if (!identityAfter.matched || identityBefore.identity === identityAfter.identity) {
      return { ...result, interruption: "not_changed", reason: "interruption_identity_unchanged" };
    }
    result.interruption = "identity_changed";

    const response = page.waitForResponse((item) => item.url() === target.href
      && item.request().method() === declaration.request.method, { timeout: OPERATION_TIMEOUT_MS }).catch(() => null);
    releaseMode = "fulfill";
    resolveRelease();
    const released = await withTimeout(releaseDone);
    const observedResponse = await response;
    if (released !== true || !observedResponse) return { ...result, release: "unavailable", reason: "release_unavailable" };
    const responseFailure = await observedResponse.finished().catch(() => true);
    if (responseFailure) return { ...result, release: "unavailable", reason: "release_unavailable" };
    result.release = "fulfilled_once";
    await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await page.waitForTimeout(QUIESCENCE_MS);
    if (methodMismatch) {
      return { ...result, request: "unavailable", freshness: "unavailable", reason: "request_mismatch" };
    }
    if (requestCount > 1) return { ...result, request: "count_exceeded", reason: "request_count_exceeded" };

    const states = [];
    for (const predicate of [
      declaration.freshness.identity,
      declaration.freshness.success,
      declaration.freshness.content,
    ]) states.push(await predicateState(page, predicate));
    if (states.some((state) => !state.available)) return { ...result, reason: "predicate_unavailable" };
    const fresh = states.every((state) => state.matched);
    return {
      ...result,
      freshness: fresh ? "fresh" : "stale",
      reason: fresh ? "fresh_completion_isolated" : "stale_completion_reassigned",
    };
  } catch {
    return result;
  } finally {
    await stopHeldRequest();
    await page.unroute(target.href, handler).catch(() => {});
  }
}

module.exports = { QUIESCENCE_MS, runStaleCompletionReplay, validateAsyncCompletion };
