"use strict";

const CLAIM_BOUNDARY = "two fresh evaluator-controlled disclosure state replays";
const ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const MAX_TARGETS = 8;
const OPERATION_TIMEOUT_MS = 5000;

function fail(message) {
  throw new TypeError(message);
}

function validateDisclosureTargets(targets, steps) {
  if (!Array.isArray(targets) || targets.length < 1 || targets.length > MAX_TARGETS) {
    fail("disclosureTargets must contain 1..8 entries");
  }
  if (!Array.isArray(steps) || steps.length < 1 || steps.length > 20) fail("steps must contain 1..20 entries");
  const stepById = new Map(steps.map((step) => [step.id, step]));
  if (stepById.size !== steps.length) fail("step ids must be unique");
  const ids = new Set();
  const actionStepIds = new Set();
  for (const [index, target] of targets.entries()) {
    if (!target || typeof target !== "object" || Array.isArray(target)
        || Object.keys(target).sort().join("|") !== "actionStepId|id|panelSelector|settling") {
      fail(`disclosureTargets[${index}] contract is invalid`);
    }
    if (typeof target.id !== "string" || !ID.test(target.id) || ids.has(target.id)) {
      fail("disclosure target ids must be unique lowercase kebab-case");
    }
    ids.add(target.id);
    if (typeof target.actionStepId !== "string" || !ID.test(target.actionStepId)
        || actionStepIds.has(target.actionStepId)) fail("actionStepIds must be unique lowercase kebab-case");
    actionStepIds.add(target.actionStepId);
    if (target.settling !== "reduced-motion-static") {
      fail(`disclosureTargets[${index}].settling is invalid`);
    }
    if (typeof target.panelSelector !== "string" || target.panelSelector.length < 1
        || target.panelSelector.length > 300 || target.panelSelector.trim() !== target.panelSelector) {
      fail(`disclosureTargets[${index}].panelSelector is invalid`);
    }
    const step = stepById.get(target.actionStepId);
    if (!step || !["click", "press"].includes(step.action)) fail("disclosure action must use click or press");
    if (step.action === "press" && !["Enter", "Space"].includes(step.value)) {
      fail("disclosure press action must use Enter or Space");
    }
  }
  return targets;
}

function aggregateDisclosureResults(targets, replayResults) {
  const records = targets.map((target) => {
    const replays = replayResults.get(target.id) || [];
    const base = { id: target.id, replays: replays.length };
    if (replays.length !== 2 || replays.some((item) => !item
        || !["match", "mismatch", "unavailable"].includes(item.status))) {
      return { ...base, status: "unavailable", reason: "runtime_unavailable" };
    }
    if (replays.some((item) => item.status === "unavailable")) {
      if (replays[0].status !== replays[1].status || replays[0].reason !== replays[1].reason) {
        return { ...base, status: "unavailable", reason: "replay_unstable" };
      }
      const reason = replays[0].reason;
      const allowed = new Set([
        "action_outcome_unavailable", "disclosure_contract_unavailable", "external_request_blocked",
        "fonts_not_ready", "initial_state_unavailable", "replay_unstable", "runtime_unavailable",
        "state_settling_unavailable",
      ]);
      return { ...base, status: "unavailable", reason: allowed.has(reason) ? reason : "runtime_unavailable" };
    }
    if (replays[0].status !== replays[1].status || replays[0].signature !== replays[1].signature
        || replays[0].expanded !== replays[1].expanded || replays[0].panelVisible !== replays[1].panelVisible) {
      return { ...base, status: "unavailable", reason: "replay_unstable" };
    }
    const matched = replays[0].status === "match";
    return {
      ...base,
      status: matched ? "clear" : "confirmed",
      expanded: replays[0].expanded,
      panelVisible: replays[0].panelVisible,
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

async function inspectDisclosureState(page, buttonSelector, panelSelector) {
  return page.evaluate(({ controlSelector, contentSelector }) => {
    const presentationBlocked = (element) => {
      for (let node = element; node instanceof Element; node = node.parentElement) {
        const style = getComputedStyle(node);
        if (node.getAttribute("aria-hidden")?.toLowerCase() === "true" || node.hasAttribute("inert")
            || style.contentVisibility === "hidden" || Number(style.opacity) === 0) return true;
      }
      return false;
    };
    const hasComplexPaint = (element) => {
      for (let node = element; node instanceof Element; node = node.parentElement) {
        const style = getComputedStyle(node);
        if (style.filter !== "none" || style.clipPath !== "none"
            || style.maskImage !== "none" || style.mixBlendMode !== "normal") return true;
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
    const perceivable = (element) => {
      if (presentationBlocked(element)) return false;
      return [element, ...element.querySelectorAll("*")].some((candidate) => visibleBox(candidate));
    };
    try {
      const controls = document.querySelectorAll(controlSelector);
      const contents = document.querySelectorAll(contentSelector);
      if (controls.length !== 1 || contents.length !== 1) {
        return { selectorValid: true, unique: false };
      }
      const control = controls[0];
      const content = contents[0];
      const nativeButton = control instanceof HTMLButtonElement;
      return {
        selectorValid: true,
        unique: true,
        nativeButton,
        buttonVisible: nativeButton && visibleBox(control),
        expanded: nativeButton && control.getAttribute("aria-expanded") === "true",
        collapsed: nativeButton && control.getAttribute("aria-expanded") === "false",
        complexPaint: hasComplexPaint(content),
        panelVisible: perceivable(content),
        signature: nativeButton
          ? `button:${control.type}:panel:${content.tagName.toLowerCase()}:${content.id}`
          : null,
      };
    } catch {
      return { selectorValid: false, unique: false };
    }
  }, { controlSelector: buttonSelector, contentSelector: panelSelector });
}

async function inspectControlSemantics(page, buttonSelector) {
  let controlHandle;
  let control;
  let roleButtons = [];
  try {
    controlHandle = await page.evaluateHandle((selector) => document.querySelector(selector), buttonSelector);
    control = controlHandle.asElement();
    if (!control) return { buttonRole: false, enabled: false, ariaDisabled: true, inert: true, visible: false };
    roleButtons = await page.getByRole("button", { includeHidden: true }).elementHandles();
    let buttonRole = false;
    for (const candidate of roleButtons) {
      if (await candidate.evaluate((node, selected) => node === selected, control)) buttonRole = true;
    }
    const state = await control.evaluate((node) => ({
      ariaDisabled: [...document.querySelectorAll("[aria-disabled]")].some((candidate) =>
        candidate.getAttribute("aria-disabled")?.toLowerCase() === "true" && candidate.contains(node)),
      inert: node.closest("[inert]") !== null,
    }));
    return {
      ...state,
      buttonRole,
      enabled: await control.isEnabled(),
      visible: await control.isVisible(),
    };
  } catch {
    return { buttonRole: false, enabled: false, ariaDisabled: true, inert: true, visible: false };
  } finally {
    await Promise.all(roleButtons.map((handle) => handle.dispose().catch(() => {})));
    await controlHandle?.dispose().catch(() => {});
  }
}

async function panelHasActiveMotion(page, panelSelector) {
  return page.evaluate((selector) => {
    try {
      const panels = document.querySelectorAll(selector);
      if (panels.length !== 1) return null;
      const active = (animation) => animation.pending || animation.playState === "running"
        || animation.constructor?.name === "CSSTransition";
      if (panels[0].getAnimations({ subtree: true }).some(active)) return true;
      for (let ancestor = panels[0].parentElement; ancestor; ancestor = ancestor.parentElement) {
        if (ancestor.getAnimations({ subtree: false }).some(active)) return true;
      }
      return false;
    } catch {
      return null;
    }
  }, panelSelector);
}

async function applyDisclosureAction(page, step) {
  let handle;
  try {
    handle = await page.evaluateHandle((selector) => document.querySelector(selector), step.selector);
    const element = handle.asElement();
    if (!element) return false;
    if (step.action === "click") await element.click({ timeout: OPERATION_TIMEOUT_MS });
    else if (step.action === "press") await element.press(step.value, { timeout: OPERATION_TIMEOUT_MS });
    else return false;
    return true;
  } catch {
    return false;
  } finally {
    await handle?.dispose().catch(() => {});
  }
}

async function replayDisclosureTarget(browser, url, contextOptions, target, steps) {
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

    const actionIndex = steps.findIndex((step) => step.id === target.actionStepId);
    if (actionIndex < 0) return { status: "unavailable", reason: "disclosure_contract_unavailable" };
    for (let index = 0; index < actionIndex; index += 1) {
      if (!(await applyStep(page, steps[index]))) {
        return { status: "unavailable", reason: "disclosure_contract_unavailable" };
      }
    }
    const actionStep = steps[actionIndex];
    const initial = await inspectDisclosureState(page, actionStep.selector, target.panelSelector);
    const initialControl = await inspectControlSemantics(page, actionStep.selector);
    if (!initial.selectorValid) return { status: "unavailable", reason: "disclosure_contract_unavailable" };
    if (initial.complexPaint) return { status: "unavailable", reason: "disclosure_contract_unavailable" };
    if (!initial.unique || !initial.nativeButton || !initial.buttonVisible
        || !initialControl.visible || !initialControl.buttonRole || !initialControl.enabled
        || initialControl.ariaDisabled || initialControl.inert || !initial.collapsed || initial.panelVisible) {
      return { status: "unavailable", reason: "initial_state_unavailable" };
    }
    if (!(await applyDisclosureAction(page, actionStep))) {
      return { status: "unavailable", reason: "disclosure_contract_unavailable" };
    }
    await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    if (blockedExternalRequests) return { status: "unavailable", reason: "external_request_blocked" };
    const finalState = await inspectDisclosureState(page, actionStep.selector, target.panelSelector);
    const finalControl = await inspectControlSemantics(page, actionStep.selector);
    if (finalState.complexPaint) return { status: "unavailable", reason: "disclosure_contract_unavailable" };
    if (!finalState.selectorValid || !finalState.unique || !finalState.nativeButton
        || !finalState.buttonVisible || !finalControl.visible || !finalControl.buttonRole || !finalControl.enabled
        || finalControl.ariaDisabled || finalControl.inert || finalState.signature !== initial.signature) {
      return { status: "unavailable", reason: "disclosure_contract_unavailable" };
    }
    const activeMotion = await panelHasActiveMotion(page, target.panelSelector);
    if (activeMotion === null) return { status: "unavailable", reason: "disclosure_contract_unavailable" };
    if (activeMotion) return { status: "unavailable", reason: "state_settling_unavailable" };
    const matched = finalState.expanded && finalState.panelVisible;
    if (!finalState.expanded && !finalState.panelVisible) {
      return { status: "unavailable", reason: "action_outcome_unavailable" };
    }
    return {
      status: matched ? "match" : "mismatch",
      expanded: finalState.expanded,
      panelVisible: finalState.panelVisible,
      signature: finalState.signature,
    };
  } catch {
    return { status: "unavailable", reason: "runtime_unavailable" };
  } finally {
    await context?.close().catch(() => {});
  }
}

async function auditDisclosureTargets(browser, url, contextOptions, spec, replayRunner = replayDisclosureTarget) {
  validateDisclosureTargets(spec.disclosureTargets, spec.steps);
  const replayResults = new Map();
  for (const target of spec.disclosureTargets) {
    const results = [];
    for (let replay = 0; replay < 2; replay += 1) {
      results.push(await replayRunner(browser, url, contextOptions, target, spec.steps));
    }
    replayResults.set(target.id, results);
  }
  return aggregateDisclosureResults(spec.disclosureTargets, replayResults);
}

module.exports = {
  CLAIM_BOUNDARY,
  aggregateDisclosureResults,
  auditDisclosureTargets,
  replayDisclosureTarget,
  validateDisclosureTargets,
};
