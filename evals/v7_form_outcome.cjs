"use strict";

const { createHash } = require("node:crypto");

const CLAIM_BOUNDARY = "two fresh evaluator-controlled mutually-exclusive visual form outcome replays";
const ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const VALID_VALUE = /^eval-outcome-valid-[a-z0-9]+(?:-[a-z0-9]+)*$/;
const INVALID_VALUE = /^eval-outcome-invalid-[a-z0-9]+(?:-[a-z0-9]+)*$/;
const MAX_TARGETS = 4;
const MAX_VALUE_SUFFIX_LENGTH = 40;
const OPERATION_TIMEOUT_MS = 5000;

function fail(message) {
  throw new TypeError(message);
}

function validBoundedValue(value, prefix, pattern) {
  return typeof value === "string" && value.slice(prefix.length).length <= MAX_VALUE_SUFFIX_LENGTH
    && pattern.test(value);
}

function privateMessageFingerprint(value) {
  return createHash("sha256").update(value, "utf8").digest("hex");
}

function validateFormOutcomeTargets(targets, steps) {
  if (!Array.isArray(targets) || targets.length < 1 || targets.length > MAX_TARGETS) {
    fail("formOutcomeTargets must contain 1..4 entries");
  }
  if (!Array.isArray(steps) || steps.length < 4 || steps.length > 20) fail("steps must contain 4..20 entries");
  const stepById = new Map(steps.map((step, index) => [step?.id, { step, index }]));
  if (stepById.size !== steps.length || stepById.has(undefined)) fail("step ids must exist and be unique");
  const targetIds = new Set();
  const referencedStepIds = new Set();
  for (const [index, target] of targets.entries()) {
    const exactKeys = "errorSelector|id|invalidControlStepId|invalidationStepId|normalization"
      + "|outcomeSemantics|settling|successSelector|successStepId|validControlStepId|validationMode";
    if (!target || typeof target !== "object" || Array.isArray(target)
        || Object.keys(target).sort().join("|") !== exactKeys) {
      fail(`formOutcomeTargets[${index}] contract is invalid`);
    }
    if (typeof target.id !== "string" || !ID.test(target.id) || targetIds.has(target.id)) {
      fail("form outcome target ids must be unique lowercase kebab-case");
    }
    targetIds.add(target.id);
    if (target.outcomeSemantics !== "mutually-exclusive" || target.normalization !== "none"
        || target.settling !== "reduced-motion-static"
        || !["custom-aria", "native-constraint"].includes(target.validationMode)) {
      fail(`formOutcomeTargets[${index}] fixed semantics are invalid`);
    }
    if (typeof target.successSelector !== "string" || target.successSelector.length < 1
        || target.successSelector.length > 300 || target.successSelector.trim() !== target.successSelector) {
      fail(`formOutcomeTargets[${index}] selector is invalid`);
    }
    if (target.validationMode === "custom-aria") {
      if (typeof target.errorSelector !== "string" || target.errorSelector.length < 1
          || target.errorSelector.length > 300 || target.errorSelector.trim() !== target.errorSelector
          || target.successSelector === target.errorSelector) {
        fail("custom-aria requires distinct bounded success and error selectors");
      }
    } else if (target.errorSelector !== null) fail("native-constraint requires errorSelector=null");
    const stepKeys = ["validControlStepId", "successStepId", "invalidControlStepId", "invalidationStepId"];
    const declarations = stepKeys.map((key) => {
      if (typeof target[key] !== "string" || !ID.test(target[key]) || referencedStepIds.has(target[key])) {
        fail(`formOutcomeTargets[${index}] step reference is invalid`);
      }
      referencedStepIds.add(target[key]);
      return stepById.get(target[key]);
    });
    if (declarations.some((item) => !item)
        || !declarations.every((item, position) => item.index === declarations[0].index + position)) {
      fail(`formOutcomeTargets[${index}] steps must be consecutive and ordered`);
    }
    const [validControl, success, invalidControl, invalidation] = declarations.map((item) => item.step);
    if (!["fill", "select"].includes(validControl.action)
        || invalidControl.action !== validControl.action
        || invalidControl.selector !== validControl.selector) {
      fail("valid and invalid control steps must use the same fill or select control");
    }
    if (!validBoundedValue(validControl.value, "eval-outcome-valid-", VALID_VALUE)
        || !validBoundedValue(invalidControl.value, "eval-outcome-invalid-", INVALID_VALUE)) {
      fail("control values must be bounded evaluator-owned outcome tokens");
    }
    for (const actionStep of [success, invalidation]) {
      if (!["click", "press"].includes(actionStep.action)
          || (actionStep.action === "press" && !["Enter", "Space"].includes(actionStep.value))) {
        fail("outcome actions must use click or bounded press");
      }
    }
  }
  return targets;
}

function aggregateFormOutcomeResults(targets, replayResults) {
  const allowedReasons = new Set([
    "external_request_blocked", "fonts_not_ready", "form_outcome_contract_unavailable",
    "initial_state_unavailable", "invalid_checkpoint_unavailable", "replay_unstable",
    "runtime_unavailable", "state_settling_unavailable", "success_checkpoint_unavailable",
  ]);
  const records = targets.map((target) => {
    const replays = replayResults.get(target.id) || [];
    const base = { id: target.id, replays: replays.length };
    if (replays.length !== 2 || replays.some((item) => !item
        || !["clean", "stale", "unavailable"].includes(item.status))) {
      return { ...base, status: "unavailable", reason: "runtime_unavailable" };
    }
    if (replays.some((item) => item.status === "unavailable")) {
      if (replays[0].status !== replays[1].status || replays[0].reason !== replays[1].reason) {
        return { ...base, status: "unavailable", reason: "replay_unstable" };
      }
      return {
        ...base,
        status: "unavailable",
        reason: allowedReasons.has(replays[0].reason) ? replays[0].reason : "runtime_unavailable",
      };
    }
    if (replays[0].status !== replays[1].status || replays[0].signature !== replays[1].signature
        || replays[0].staleSuccess !== replays[1].staleSuccess) {
      return { ...base, status: "unavailable", reason: "replay_unstable" };
    }
    const staleSuccess = replays[0].status === "stale";
    return {
      ...base,
      status: staleSuccess ? "confirmed" : "clear",
      staleSuccess,
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
    if (await locator.count() !== 1 || !(await locator.isVisible())) return false;
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

async function applyLightDomStep(page, step) {
  let handle;
  try {
    handle = await page.evaluateHandle((selector) => {
      const matches = document.querySelectorAll(selector);
      return matches.length === 1 ? matches[0] : null;
    }, step.selector);
    const element = handle.asElement();
    if (!element || !(await element.isVisible()) || !(await element.isEnabled())) return false;
    if (step.action === "click") await element.click({ timeout: OPERATION_TIMEOUT_MS });
    else if (step.action === "fill") await element.fill(step.value, { timeout: OPERATION_TIMEOUT_MS });
    else if (step.action === "select") await element.selectOption(step.value, { timeout: OPERATION_TIMEOUT_MS });
    else if (step.action === "press") await element.press(step.value, { timeout: OPERATION_TIMEOUT_MS });
    else return false;
    return true;
  } catch {
    return false;
  } finally {
    await handle?.dispose().catch(() => {});
  }
}

async function inspectControl(page, selector, action) {
  let handle;
  try {
    const state = await page.evaluate(({ controlSelector, controlAction }) => {
      try {
        const matches = document.querySelectorAll(controlSelector);
        if (matches.length !== 1) return { selectorValid: true, unique: false };
        const node = matches[0];
        let nativeKind = null;
        if (controlAction === "fill" && node instanceof HTMLTextAreaElement) nativeKind = "textarea";
        else if (controlAction === "fill" && node instanceof HTMLInputElement) {
          const type = (node.getAttribute("type") || "text").toLowerCase();
          if (["text", "search", "email", "tel", "url"].includes(type)) nativeKind = `input-${type}`;
        } else if (controlAction === "select" && node instanceof HTMLSelectElement
            && !node.multiple && node.size <= 1) nativeKind = "select-one";
        return {
          ariaDisabled: [...document.querySelectorAll("[aria-disabled]")].some((candidate) =>
            candidate.getAttribute("aria-disabled")?.toLowerCase() === "true" && candidate.contains(node)),
          ariaInvalid: node.getAttribute("aria-invalid")?.toLowerCase() === "true",
          inert: node.closest("[inert]") !== null,
          nativeKind,
          selectorValid: true,
          signature: nativeKind ? `${nativeKind}:${node.id}` : null,
          unique: true,
          validityValid: nativeKind ? node.validity.valid : null,
          willValidate: nativeKind ? node.willValidate === true : false,
        };
      } catch {
        return { selectorValid: false, unique: false };
      }
    }, { controlSelector: selector, controlAction: action });
    if (!state?.selectorValid || !state.unique) return state;
    handle = await page.evaluateHandle((controlSelector) => document.querySelector(controlSelector), selector);
    const node = handle.asElement();
    const result = {
      ...state,
      enabled: node ? await node.isEnabled() : false,
      visible: node ? await node.isVisible() : false,
    };
    return result;
  } catch {
    return null;
  } finally {
    await handle?.dispose().catch(() => {});
  }
}

async function inspectOutcomes(page, successSelector, errorSelector) {
  return page.evaluate(({ successQuery, errorQuery }) => {
    const presentationBlocked = (element) => {
      for (let node = element; node instanceof Element; node = node.parentElement) {
        const style = getComputedStyle(node);
        if (node.getAttribute("aria-hidden")?.toLowerCase() === "true" || node.hasAttribute("inert")
            || style.contentVisibility === "hidden" || Number(style.opacity) === 0) return true;
      }
      return false;
    };
    const complexPaint = (element) => {
      const nonDefaultPaint = (node) => {
        const style = getComputedStyle(node);
        const property = (name, fallback) => style.getPropertyValue(name).trim() || fallback;
        return property("filter", "none") !== "none" || property("clip-path", "none") !== "none"
          || property("mask-image", "none") !== "none"
          || property("mix-blend-mode", "normal") !== "normal";
      };
      if ([element, ...element.querySelectorAll("*")].some((node) => nonDefaultPaint(node))) return true;
      for (let node = element.parentElement; node instanceof Element; node = node.parentElement) {
        if (nonDefaultPaint(node)) return true;
      }
      return false;
    };
    const visibleBox = (element) => {
      if (presentationBlocked(element)) return false;
      const style = getComputedStyle(element);
      const bounds = element.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" && style.visibility !== "collapse"
        && bounds.width > 0 && bounds.height > 0;
    };
    const perceivable = (element) => !presentationBlocked(element)
      && [element, ...element.querySelectorAll("*")].some((candidate) => visibleBox(candidate));
    const normalized = (value) => (value || "").replace(/\s+/g, " ").trim();
    const messageContent = (element) => {
      const text = normalized(element instanceof HTMLElement ? element.innerText : element.textContent);
      if (text.length > 4096) return { available: false, value: "" };
      if (text.length > 0) return { available: true, value: text };
      return { available: true, value: "" };
    };
    try {
      const successes = document.querySelectorAll(successQuery);
      const errors = errorQuery === null ? [] : document.querySelectorAll(errorQuery);
      if (successes.length !== 1 || (errorQuery !== null && errors.length !== 1)
          || (errorQuery !== null && successes[0] === errors[0])) {
        return { selectorValid: true, unique: false };
      }
      const success = successes[0];
      const error = errorQuery === null ? null : errors[0];
      const successMessage = messageContent(success);
      const errorMessage = error === null ? { available: true, value: "" } : messageContent(error);
      return {
        selectorValid: true,
        unique: true,
        complexPaint: complexPaint(success) || (error !== null && complexPaint(error)),
        contentAvailable: successMessage.available && errorMessage.available,
        errorContent: errorMessage.value.length > 0,
        errorMessage: errorMessage.value,
        successVisible: perceivable(success),
        successContent: successMessage.value.length > 0,
        successMessage: successMessage.value,
        errorVisible: error !== null && perceivable(error),
        signature: error === null ? `${success.tagName.toLowerCase()}:${success.id}|native`
          : `${success.tagName.toLowerCase()}:${success.id}|${error.tagName.toLowerCase()}:${error.id}`,
      };
    } catch {
      return { selectorValid: false, unique: false };
    }
  }, { successQuery: successSelector, errorQuery: errorSelector });
}

async function outcomeHasActiveMotion(page, selector) {
  return page.evaluate((query) => {
    try {
      const matches = document.querySelectorAll(query);
      if (matches.length !== 1) return null;
      const active = (animation) => animation.pending || animation.playState === "running"
        || animation.constructor?.name === "CSSTransition";
      if (matches[0].getAnimations({ subtree: true }).some(active)) return true;
      for (let ancestor = matches[0].parentElement; ancestor; ancestor = ancestor.parentElement) {
        if (ancestor.getAnimations({ subtree: false }).some(active)) return true;
      }
      return false;
    } catch {
      return null;
    }
  }, selector);
}

async function outcomesHaveActiveMotion(page, target) {
  const selectors = [target.successSelector];
  if (target.errorSelector !== null) selectors.push(target.errorSelector);
  const states = await Promise.all(selectors.map((selector) => outcomeHasActiveMotion(page, selector)));
  if (states.includes(null)) return null;
  return states.some(Boolean);
}

async function settle(page) {
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
}

async function readControlValue(page, selector) {
  return page.evaluate((controlSelector) => {
    try {
      const matches = document.querySelectorAll(controlSelector);
      const node = matches.length === 1 ? matches[0] : null;
      if (!(node instanceof HTMLInputElement) && !(node instanceof HTMLTextAreaElement)
          && !(node instanceof HTMLSelectElement)) return { available: false, value: null };
      return { available: true, value: node.value };
    } catch {
      return { available: false, value: null };
    }
  }, selector);
}

async function replayFormOutcomeTarget(browser, url, contextOptions, target, steps) {
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
    if (!fontsReady) return { status: "unavailable", reason: "fonts_not_ready" };
    if (blockedExternalRequests) return { status: "unavailable", reason: "external_request_blocked" };

    const validIndex = steps.findIndex((step) => step.id === target.validControlStepId);
    if (validIndex < 0) return { status: "unavailable", reason: "form_outcome_contract_unavailable" };
    for (let index = 0; index < validIndex; index += 1) {
      if (!(await applyStep(page, steps[index]))) {
        return { status: "unavailable", reason: "form_outcome_contract_unavailable" };
      }
    }
    const sequence = steps.slice(validIndex, validIndex + 4);
    const customAria = target.validationMode === "custom-aria";
    const initialControl = await inspectControl(page, sequence[0].selector, sequence[0].action);
    const initialOutcomes = await inspectOutcomes(page, target.successSelector, target.errorSelector);
    if (!initialControl?.selectorValid || !initialOutcomes.selectorValid || initialOutcomes.complexPaint) {
      return { status: "unavailable", reason: "form_outcome_contract_unavailable" };
    }
    if (!initialOutcomes.unique || !initialControl.unique || !initialControl.nativeKind
        || !initialControl.visible || !initialControl.enabled
        || initialControl.ariaDisabled || initialControl.inert
        || (customAria ? initialControl.ariaInvalid : !initialControl.willValidate)
        || initialOutcomes.successVisible || initialOutcomes.errorVisible) {
      return { status: "unavailable", reason: "initial_state_unavailable" };
    }
    const initialMotion = await outcomesHaveActiveMotion(page, target);
    if (initialMotion === null) return { status: "unavailable", reason: "form_outcome_contract_unavailable" };
    if (initialMotion) return { status: "unavailable", reason: "state_settling_unavailable" };

    if (!(await applyLightDomStep(page, sequence[0])) || !(await applyLightDomStep(page, sequence[1]))) {
      return { status: "unavailable", reason: "form_outcome_contract_unavailable" };
    }
    await settle(page);
    if (blockedExternalRequests) return { status: "unavailable", reason: "external_request_blocked" };
    const validControl = await inspectControl(page, sequence[0].selector, sequence[0].action);
    const validOutcomes = await inspectOutcomes(page, target.successSelector, target.errorSelector);
    if (!validControl?.selectorValid || !validOutcomes.selectorValid || !validOutcomes.unique
        || !validControl.unique || validOutcomes.complexPaint || validControl.signature !== initialControl.signature) {
      return { status: "unavailable", reason: "form_outcome_contract_unavailable" };
    }
    const validMotion = await outcomesHaveActiveMotion(page, target);
    if (validMotion === null) return { status: "unavailable", reason: "form_outcome_contract_unavailable" };
    if (validMotion) return { status: "unavailable", reason: "state_settling_unavailable" };
    if (!validControl.visible || !validControl.enabled || validControl.ariaDisabled || validControl.inert
        || !validOutcomes.contentAvailable || !validOutcomes.successVisible || !validOutcomes.successContent
        || (customAria ? validControl.ariaInvalid || validOutcomes.errorVisible
          : !validControl.willValidate || validControl.validityValid !== true)) {
      return { status: "unavailable", reason: "success_checkpoint_unavailable" };
    }
    const validSuccessFingerprint = privateMessageFingerprint(validOutcomes.successMessage);

    if (!(await applyLightDomStep(page, sequence[2]))) {
      return { status: "unavailable", reason: "form_outcome_contract_unavailable" };
    }
    const invalidBaseline = await readControlValue(page, sequence[2].selector);
    if (!invalidBaseline.available) return { status: "unavailable", reason: "invalid_checkpoint_unavailable" };
    if (!(await applyLightDomStep(page, sequence[3]))) {
      return { status: "unavailable", reason: "form_outcome_contract_unavailable" };
    }
    await settle(page);
    if (blockedExternalRequests) return { status: "unavailable", reason: "external_request_blocked" };
    const invalidControl = await inspectControl(page, sequence[2].selector, sequence[2].action);
    const invalidOutcomes = await inspectOutcomes(page, target.successSelector, target.errorSelector);
    if (!invalidControl?.selectorValid || !invalidOutcomes.selectorValid || !invalidOutcomes.unique
        || !invalidControl.unique || invalidOutcomes.complexPaint
        || invalidControl.signature !== initialControl.signature) {
      return { status: "unavailable", reason: "form_outcome_contract_unavailable" };
    }
    const invalidMotion = await outcomesHaveActiveMotion(page, target);
    if (invalidMotion === null) return { status: "unavailable", reason: "form_outcome_contract_unavailable" };
    if (invalidMotion) return { status: "unavailable", reason: "state_settling_unavailable" };
    const invalidValue = await readControlValue(page, sequence[2].selector);
    if (!invalidValue.available || invalidValue.value !== invalidBaseline.value) {
      return { status: "unavailable", reason: "invalid_checkpoint_unavailable" };
    }
    if (!invalidOutcomes.contentAvailable || !invalidControl.visible || !invalidControl.enabled
        || invalidControl.ariaDisabled || invalidControl.inert
        || (customAria ? !invalidControl.ariaInvalid || !invalidOutcomes.errorVisible || !invalidOutcomes.errorContent
          : !invalidControl.willValidate || invalidControl.validityValid !== false)) {
      return { status: "unavailable", reason: "invalid_checkpoint_unavailable" };
    }
    const sameSuccessMessage = invalidOutcomes.successContent
      && privateMessageFingerprint(invalidOutcomes.successMessage) === validSuccessFingerprint;
    const staleSuccess = sameSuccessMessage && invalidOutcomes.successVisible;
    return {
      status: staleSuccess ? "stale" : "clean",
      staleSuccess,
      signature: `${invalidControl.signature}:${invalidOutcomes.signature}`,
    };
  } catch {
    return { status: "unavailable", reason: "runtime_unavailable" };
  } finally {
    await context?.close().catch(() => {});
  }
}

async function auditFormOutcomeTargets(browser, url, contextOptions, spec, replayRunner = replayFormOutcomeTarget) {
  validateFormOutcomeTargets(spec.formOutcomeTargets, spec.steps);
  const replayResults = new Map();
  for (const target of spec.formOutcomeTargets) {
    const results = [];
    for (let replay = 0; replay < 2; replay += 1) {
      results.push(await replayRunner(browser, url, contextOptions, target, spec.steps));
    }
    replayResults.set(target.id, results);
  }
  return aggregateFormOutcomeResults(spec.formOutcomeTargets, replayResults);
}

module.exports = {
  CLAIM_BOUNDARY,
  aggregateFormOutcomeResults,
  auditFormOutcomeTargets,
  replayFormOutcomeTarget,
  validateFormOutcomeTargets,
};
