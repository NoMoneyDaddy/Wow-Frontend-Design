"use strict";

const ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const MAX_LIFECYCLES = 4;
const OPERATION_TIMEOUT_MS = 5000;
const CLAIM_BOUNDARY = "two fresh evaluator-controlled dialog open-close focus lifecycle replays";

function publicUnavailableReason(reason) {
  if (reason === "external_request_blocked") return reason;
  if (["lifecycle_signature_drift", "unstable_fresh_replay"].includes(reason)) return "replay_unstable";
  if ([
    "dialog_count_invalid", "dialog_modal_invalid", "dialog_not_closed", "dialog_not_visible",
    "dialog_role_invalid", "dialog_shadow_root_unsupported", "open_target_count_invalid",
    "open_target_not_descendant", "open_target_not_focusable", "open_target_not_visible",
    "open_target_shadow_root_unsupported", "return_target_count_invalid", "return_target_not_focusable",
    "return_target_not_visible", "return_target_shadow_root_unsupported",
  ].includes(reason)) return "dialog_contract_unavailable";
  return "runtime_unavailable";
}

function fail(message) {
  throw new TypeError(message);
}

function validateDialogFocusLifecycles(lifecycles, steps) {
  if (!Array.isArray(lifecycles) || lifecycles.length < 1 || lifecycles.length > MAX_LIFECYCLES) {
    fail("dialogFocusLifecycles must contain 1..4 entries");
  }
  if (!Array.isArray(steps) || steps.length < 2 || steps.length > 20) fail("steps must contain 2..20 entries");
  const stepById = new Map(steps.map((step, index) => [step.id, { step, index }]));
  if (stepById.size !== steps.length) fail("step ids must be unique");
  const ids = new Set();
  const openStepIds = new Set();
  const closeStepIds = new Set();
  const dialogSelectors = new Set();
  for (const [index, lifecycle] of lifecycles.entries()) {
    if (!lifecycle || typeof lifecycle !== "object" || Array.isArray(lifecycle)
        || Object.keys(lifecycle).sort().join("|")
          !== "closeStepId|dialogSelector|id|openFocusSelector|openStepId|returnFocusSelector") {
      fail(`dialogFocusLifecycles[${index}] contract is invalid`);
    }
    if (typeof lifecycle.id !== "string" || !ID.test(lifecycle.id) || ids.has(lifecycle.id)) {
      fail("dialog lifecycle ids must be unique lowercase kebab-case");
    }
    ids.add(lifecycle.id);
    for (const key of ["dialogSelector", "openFocusSelector", "returnFocusSelector"]) {
      const value = lifecycle[key];
      if (typeof value !== "string" || value.length < 1 || value.length > 300 || value.trim() !== value) {
        fail(`dialogFocusLifecycles[${index}].${key} is invalid`);
      }
    }
    for (const key of ["openStepId", "closeStepId"]) {
      if (typeof lifecycle[key] !== "string" || !ID.test(lifecycle[key])) {
        fail(`dialogFocusLifecycles[${index}].${key} is invalid`);
      }
    }
    const open = stepById.get(lifecycle.openStepId);
    const close = stepById.get(lifecycle.closeStepId);
    if (!open || !close || open.index >= close.index) fail(`dialogFocusLifecycles[${index}] step order is invalid`);
    if (!["click", "press"].includes(open.step.action) || !["click", "press"].includes(close.step.action)) {
      fail(`dialogFocusLifecycles[${index}] open/close steps must use click or press`);
    }
    if (openStepIds.has(lifecycle.openStepId) || closeStepIds.has(lifecycle.closeStepId)
        || dialogSelectors.has(lifecycle.dialogSelector)) {
      fail(`dialogFocusLifecycles[${index}] step or dialog binding is duplicated`);
    }
    openStepIds.add(lifecycle.openStepId);
    closeStepIds.add(lifecycle.closeStepId);
    dialogSelectors.add(lifecycle.dialogSelector);
  }
  return lifecycles;
}

function aggregateDialogFocusResults(lifecycles, replayResults) {
  const records = lifecycles.map((lifecycle) => {
    const replays = replayResults.get(lifecycle.id) || [];
    const base = { id: lifecycle.id, replays: replays.length };
    if (replays.length !== 2 || replays.some((item) => !item
        || !["match", "mismatch", "unavailable"].includes(item.status))) {
      return { ...base, status: "unavailable", reason: "runtime_unavailable" };
    }
    if (replays.some((item) => item.status === "unavailable")) {
      return {
        ...base,
        status: "unavailable",
        reason: publicUnavailableReason(replays.find((item) => item.status === "unavailable").reason),
      };
    }
    if (replays[0].status !== replays[1].status) {
      return { ...base, status: "unavailable", reason: "replay_unstable" };
    }
    if (replays[0].signature !== replays[1].signature) {
      return { ...base, status: "unavailable", reason: "replay_unstable" };
    }
    const matched = replays[0].status === "match";
    return {
      ...base,
      status: matched ? "clear" : "confirmed",
      openFocus: replays[0].openFocus,
      returnFocus: replays[0].returnFocus,
    };
  });
  const completed = records.filter((record) => record.status !== "unavailable").length;
  return {
    dialogFocusCoverage: {
      status: completed === lifecycles.length ? "complete" : "unavailable",
      reason: completed === lifecycles.length ? null : "one_or_more_lifecycles_unavailable",
      declaredLifecycles: lifecycles.length,
      completedLifecycles: completed,
      freshReplays: lifecycles.length * 2,
      claimBoundary: CLAIM_BOUNDARY,
    },
    dialogFocusLifecycles: records,
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

async function applyStepRange(page, steps, start, end) {
  for (let index = start; index < end; index += 1) {
    if (!(await applyStep(page, steps[index]))) return false;
  }
  return true;
}

async function twoFrames(page) {
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
}

async function sameNode(page, leftLocator, rightLocator) {
  const left = await leftLocator.elementHandle();
  const right = await rightLocator.elementHandle();
  try {
    return Boolean(left && right && await page.evaluate(([first, second]) => first === second, [left, right]));
  } finally {
    await left?.dispose();
    await right?.dispose();
  }
}

async function activeIs(page, locator) {
  const handle = await locator.elementHandle();
  try {
    return Boolean(handle && await page.evaluate((node) => document.activeElement === node, handle));
  } finally {
    await handle?.dispose();
  }
}

async function focusTargetEligibility(locator) {
  return locator.evaluate((node) => {
    if (node.getRootNode() !== node.ownerDocument) return "shadow_root_unsupported";
    const disabled = ("disabled" in node && node.disabled === true)
      || node.getAttribute("aria-disabled") === "true" || Boolean(node.closest("[inert]"));
    const rawTabIndex = node.getAttribute("tabindex");
    const explicitTabIndex = rawTabIndex !== null && /^[+-]?\d+$/.test(rawTabIndex.trim());
    const focusable = !disabled && (node.tabIndex >= 0 || explicitTabIndex || node.isContentEditable);
    return focusable ? "eligible" : "not_focusable";
  });
}

async function replayDialogFocusLifecycle(browser, url, contextOptions, lifecycle, steps) {
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

    const openIndex = steps.findIndex((step) => step.id === lifecycle.openStepId);
    const closeIndex = steps.findIndex((step) => step.id === lifecycle.closeStepId);
    if (openIndex < 0 || closeIndex <= openIndex) return { status: "unavailable", reason: "lifecycle_step_unavailable" };
    if (!(await applyStepRange(page, steps, 0, openIndex))) {
      return { status: "unavailable", reason: "preceding_step_unavailable" };
    }
    if (!(await applyStep(page, steps[openIndex]))) return { status: "unavailable", reason: "open_step_unavailable" };
    await twoFrames(page);
    if (blockedExternalRequests) return { status: "unavailable", reason: "external_request_blocked" };

    const dialog = page.locator(lifecycle.dialogSelector);
    if (await dialog.count() !== 1) return { status: "unavailable", reason: "dialog_count_invalid" };
    if (!(await dialog.isVisible())) return { status: "unavailable", reason: "dialog_not_visible" };
    if (!(await dialog.evaluate((node) => node.getRootNode() === node.ownerDocument))) {
      return { status: "unavailable", reason: "dialog_shadow_root_unsupported" };
    }
    const dialogsByRole = page.getByRole("dialog");
    const roleCount = await dialogsByRole.count();
    if (roleCount > 32) return { status: "unavailable", reason: "dialog_role_invalid" };
    let actualDialog = false;
    for (let index = 0; index < roleCount && !actualDialog; index += 1) {
      actualDialog = await sameNode(page, dialog, dialogsByRole.nth(index));
    }
    if (!actualDialog) return { status: "unavailable", reason: "dialog_role_invalid" };
    if (await dialog.getAttribute("aria-modal") !== "true") {
      return { status: "unavailable", reason: "dialog_modal_invalid" };
    }

    const openTarget = page.locator(lifecycle.openFocusSelector);
    if (await openTarget.count() !== 1) return { status: "unavailable", reason: "open_target_count_invalid" };
    if (!(await openTarget.isVisible())) return { status: "unavailable", reason: "open_target_not_visible" };
    const openEligibility = await focusTargetEligibility(openTarget);
    if (openEligibility === "shadow_root_unsupported") {
      return { status: "unavailable", reason: "open_target_shadow_root_unsupported" };
    }
    if (openEligibility !== "eligible") return { status: "unavailable", reason: "open_target_not_focusable" };
    const descendant = await openTarget.evaluate((node, selector) => {
      const owner = document.querySelector(selector);
      return Boolean(owner && owner.contains(node));
    }, lifecycle.dialogSelector);
    if (!descendant) return { status: "unavailable", reason: "open_target_not_descendant" };
    const openFocus = await activeIs(page, openTarget);

    if (!(await applyStepRange(page, steps, openIndex + 1, closeIndex))) {
      return { status: "unavailable", reason: "middle_step_unavailable" };
    }
    if (!(await applyStep(page, steps[closeIndex]))) return { status: "unavailable", reason: "close_step_unavailable" };
    await twoFrames(page);
    if (blockedExternalRequests) return { status: "unavailable", reason: "external_request_blocked" };
    const dialogCount = await dialog.count();
    if (dialogCount > 1 || (dialogCount === 1 && await dialog.isVisible())) {
      return { status: "unavailable", reason: "dialog_not_closed" };
    }
    const returnTarget = page.locator(lifecycle.returnFocusSelector);
    if (await returnTarget.count() !== 1) return { status: "unavailable", reason: "return_target_count_invalid" };
    if (!(await returnTarget.isVisible())) return { status: "unavailable", reason: "return_target_not_visible" };
    const returnEligibility = await focusTargetEligibility(returnTarget);
    if (returnEligibility === "shadow_root_unsupported") {
      return { status: "unavailable", reason: "return_target_shadow_root_unsupported" };
    }
    if (returnEligibility !== "eligible") return { status: "unavailable", reason: "return_target_not_focusable" };
    const returnFocus = await activeIs(page, returnTarget);
    const signature = `${openFocus ? "open-match" : "open-mismatch"}:${returnFocus ? "return-match" : "return-mismatch"}`;
    return {
      status: openFocus && returnFocus ? "match" : "mismatch",
      openFocus,
      returnFocus,
      signature,
    };
  } catch {
    return { status: "unavailable", reason: "dialog_focus_replay_failed" };
  } finally {
    await context?.close().catch(() => {});
  }
}

async function auditDialogFocusLifecycles(browser, url, contextOptions, spec, replayRunner = replayDialogFocusLifecycle) {
  validateDialogFocusLifecycles(spec.dialogFocusLifecycles, spec.steps);
  const replayResults = new Map();
  for (const lifecycle of spec.dialogFocusLifecycles) {
    const results = [];
    for (let replay = 0; replay < 2; replay += 1) {
      results.push(await replayRunner(browser, url, contextOptions, lifecycle, spec.steps));
    }
    replayResults.set(lifecycle.id, results);
  }
  return aggregateDialogFocusResults(spec.dialogFocusLifecycles, replayResults);
}

module.exports = {
  aggregateDialogFocusResults,
  auditDialogFocusLifecycles,
  replayDialogFocusLifecycle,
  validateDialogFocusLifecycles,
};
