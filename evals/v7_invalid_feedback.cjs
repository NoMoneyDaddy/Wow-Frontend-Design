"use strict";

const CLAIM_BOUNDARY = "two fresh evaluator-controlled invalid-feedback linkage replays";
const ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const MAX_TARGETS = 8;
const OPERATION_TIMEOUT_MS = 5000;

function fail(message) {
  throw new TypeError(message);
}

function validateInvalidFeedbackTargets(targets, steps) {
  if (!Array.isArray(targets) || targets.length < 1 || targets.length > MAX_TARGETS) {
    fail("invalidFeedbackTargets must contain 1..8 entries");
  }
  if (!Array.isArray(steps) || steps.length < 1 || steps.length > 20) fail("steps must contain 1..20 entries");
  const stepById = new Map(steps.map((step, index) => [step.id, { step, index }]));
  if (stepById.size !== steps.length) fail("step ids must be unique");
  const ids = new Set();
  const controlStepIds = new Set();
  const errorSelectors = new Set();
  for (const [index, target] of targets.entries()) {
    if (!target || typeof target !== "object" || Array.isArray(target)
        || Object.keys(target).sort().join("|") !== "controlStepId|errorSelector|id|invalidationStepId") {
      fail(`invalidFeedbackTargets[${index}] contract is invalid`);
    }
    if (typeof target.id !== "string" || !ID.test(target.id) || ids.has(target.id)) {
      fail("invalid feedback target ids must be unique lowercase kebab-case");
    }
    ids.add(target.id);
    if (typeof target.controlStepId !== "string" || !ID.test(target.controlStepId)
        || controlStepIds.has(target.controlStepId)) fail("controlStepIds must be unique lowercase kebab-case");
    controlStepIds.add(target.controlStepId);
    if (typeof target.invalidationStepId !== "string" || !ID.test(target.invalidationStepId)) {
      fail(`invalidFeedbackTargets[${index}].invalidationStepId is invalid`);
    }
    if (typeof target.errorSelector !== "string" || target.errorSelector.length < 1
        || target.errorSelector.length > 300 || target.errorSelector.trim() !== target.errorSelector
        || errorSelectors.has(target.errorSelector)) fail("error selectors must be unique bounded strings");
    errorSelectors.add(target.errorSelector);
    const control = stepById.get(target.controlStepId);
    const invalidation = stepById.get(target.invalidationStepId);
    if (!control || !invalidation || control.index >= invalidation.index) {
      fail(`invalidFeedbackTargets[${index}] step order is invalid`);
    }
    if (!["fill", "select"].includes(control.step.action)) fail("control step must use fill or select");
    if (!["click", "press"].includes(invalidation.step.action)) fail("invalidation step must use click or press");
  }
  return targets;
}

function aggregateInvalidFeedbackResults(targets, replayResults) {
  const records = targets.map((target) => {
    const replays = replayResults.get(target.id) || [];
    const base = { id: target.id, replays: replays.length };
    if (replays.length !== 2 || replays.some((item) => !item
        || !["linked", "missing", "unavailable"].includes(item.status))) {
      return { ...base, status: "unavailable", reason: "runtime_unavailable" };
    }
    if (replays.some((item) => item.status === "unavailable")) {
      const reason = replays.find((item) => item.status === "unavailable").reason;
      return {
        ...base,
        status: "unavailable",
        reason: ["feedback_contract_unavailable", "external_request_blocked", "runtime_unavailable"].includes(reason)
          ? reason : "runtime_unavailable",
      };
    }
    if (replays[0].status !== replays[1].status
        || replays[0].relation !== replays[1].relation
        || replays[0].signature !== replays[1].signature) {
      return { ...base, status: "unavailable", reason: "replay_unstable" };
    }
    const linked = replays[0].status === "linked";
    return {
      ...base,
      status: linked ? "clear" : "confirmed",
      relation: linked ? replays[0].relation : "missing",
    };
  });
  const completedTargets = records.filter((record) => record.status !== "unavailable").length;
  return {
    invalidFeedbackCoverage: {
      status: completedTargets === targets.length ? "complete" : "unavailable",
      reason: completedTargets === targets.length ? null : "one_or_more_targets_unavailable",
      declaredTargets: targets.length,
      completedTargets,
      freshReplays: targets.length * 2,
      claimBoundary: CLAIM_BOUNDARY,
    },
    invalidFeedbackTargets: records,
  };
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

async function replayInvalidFeedbackTarget(browser, url, contextOptions, target, steps) {
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
    if (invalidationIndex < 0) return { status: "unavailable", reason: "feedback_contract_unavailable" };
    for (let index = 0; index <= invalidationIndex; index += 1) {
      if (!(await applyStep(page, steps[index]))) {
        return { status: "unavailable", reason: "feedback_contract_unavailable" };
      }
    }
    await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    if (blockedExternalRequests) return { status: "unavailable", reason: "external_request_blocked" };

    const controlStep = steps.find((step) => step.id === target.controlStepId);
    if (!controlStep) return { status: "unavailable", reason: "feedback_contract_unavailable" };
    const control = page.locator(controlStep.selector);
    const error = page.locator(target.errorSelector);
    if (await control.count() !== 1 || await error.count() !== 1
        || !(await control.isVisible()) || !(await error.isVisible())) {
      return { status: "unavailable", reason: "feedback_contract_unavailable" };
    }
    const controlHandle = await control.elementHandle();
    const errorHandle = await error.elementHandle();
    const inspected = await page.evaluate(([controlNode, errorNode]) => {
      if (!(controlNode instanceof Element) || !(errorNode instanceof Element)
          || controlNode.getRootNode() !== document || errorNode.getRootNode() !== document) return null;
      const tag = controlNode.tagName.toLowerCase();
      let nativeSignature = null;
      if (tag === "textarea") nativeSignature = "textarea";
      else if (tag === "select") nativeSignature = controlNode.multiple || controlNode.size > 1 ? "select-listbox" : "select-combobox";
      else if (tag === "input") {
        const type = (controlNode.getAttribute("type") || "text").toLowerCase();
        if (["text", "search", "email", "tel", "url", "number"].includes(type)) nativeSignature = `input-${type}`;
      }
      if (!nativeSignature || controlNode.getAttribute("aria-invalid") !== "true") return null;
      const errorId = errorNode.id;
      const errorText = errorNode.textContent.trim();
      const idNodes = [...document.querySelectorAll("[id]")];
      const isAccessibilityHidden = (node) => {
        for (let current = node; current instanceof Element; current = current.parentElement) {
          if (current.hasAttribute("inert")
              || (current.getAttribute("aria-hidden") || "").trim().toLowerCase() === "true") return true;
        }
        return false;
      };
      if (!errorId || errorId.trim() !== errorId || /\s/.test(errorId)
          || !errorText || errorText.length > 4096 || idNodes.length > 5000
          || idNodes.filter((node) => node.id === errorId).length !== 1
          || isAccessibilityHidden(controlNode) || isAccessibilityHidden(errorNode)) return null;
      const tokens = (attribute) => (controlNode.getAttribute(attribute) || "").trim().split(/\s+/).filter(Boolean);
      const describedby = tokens("aria-describedby").includes(errorId);
      const errorMessageReference = (controlNode.getAttribute("aria-errormessage") || "").trim();
      if (/\s/.test(errorMessageReference)) return null;
      const errormessage = errorMessageReference === errorId;
      const relation = describedby && errormessage ? "both"
        : describedby ? "describedby" : errormessage ? "errormessage" : "missing";
      return { nativeSignature, errorId, relation };
    }, [controlHandle, errorHandle]).finally(async () => {
      await controlHandle?.dispose();
      await errorHandle?.dispose();
    });
    if (!inspected) return { status: "unavailable", reason: "feedback_contract_unavailable" };
    return {
      status: inspected.relation === "missing" ? "missing" : "linked",
      relation: inspected.relation,
      signature: `${inspected.nativeSignature}:${inspected.errorId}`,
    };
  } catch {
    return { status: "unavailable", reason: "runtime_unavailable" };
  } finally {
    await context?.close().catch(() => {});
  }
}

async function auditInvalidFeedbackTargets(browser, url, contextOptions, spec, replayRunner = replayInvalidFeedbackTarget) {
  validateInvalidFeedbackTargets(spec.invalidFeedbackTargets, spec.steps);
  const replayResults = new Map();
  for (const target of spec.invalidFeedbackTargets) {
    const results = [];
    for (let replay = 0; replay < 2; replay += 1) {
      results.push(await replayRunner(browser, url, contextOptions, target, spec.steps));
    }
    replayResults.set(target.id, results);
  }
  return aggregateInvalidFeedbackResults(spec.invalidFeedbackTargets, replayResults);
}

module.exports = {
  CLAIM_BOUNDARY,
  aggregateInvalidFeedbackResults,
  auditInvalidFeedbackTargets,
  replayInvalidFeedbackTarget,
  validateInvalidFeedbackTargets,
};
