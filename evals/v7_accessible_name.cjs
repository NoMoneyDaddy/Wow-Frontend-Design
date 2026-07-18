"use strict";

const ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const MAX_TARGETS = 8;
const OPERATION_TIMEOUT_MS = 5000;
const ALLOWED_ROLES = new Set([
  "combobox", "listbox", "searchbox", "spinbutton", "textbox",
]);
const CLAIM_BOUNDARY = "two fresh evaluator-controlled accessibility-name observations of declared form controls";

function publicUnavailableReason(reason) {
  if (reason === "external_request_blocked") return reason;
  if (["focus_target_count_invalid", "focus_target_not_visible"].includes(reason)) return "control_not_rendered";
  if ([
    "excluded_input_type", "expected_role_incompatible", "role_name_not_unique",
    "unsupported_input_type", "unsupported_native_control",
  ].includes(reason)) return "accessibility_tree_unavailable";
  if (["native_control_drift", "unstable_fresh_replay"].includes(reason)) return "replay_unstable";
  return "runtime_unavailable";
}

function fail(message) {
  throw new TypeError(message);
}

function validateAccessibleNameTargets(targets, focusTargets) {
  if (!Array.isArray(targets) || targets.length < 1 || targets.length > MAX_TARGETS) {
    fail("accessibleNameTargets must contain 1..8 entries");
  }
  if (!Array.isArray(focusTargets)) fail("focusTargets must be an array");
  const focusById = new Map(focusTargets.map((target) => [target.id, target]));
  const ids = new Set();
  const focusIds = new Set();
  for (const [index, target] of targets.entries()) {
    if (!target || typeof target !== "object" || Array.isArray(target)
        || Object.keys(target).sort().join("|") !== "expectedName|expectedRole|focusTargetId|id") {
      fail(`accessibleNameTargets[${index}] contract is invalid`);
    }
    if (typeof target.id !== "string" || !ID.test(target.id) || ids.has(target.id)) {
      fail("accessibleNameTarget ids must be unique lowercase kebab-case");
    }
    ids.add(target.id);
    if (typeof target.focusTargetId !== "string" || !ID.test(target.focusTargetId) || focusIds.has(target.focusTargetId)) {
      fail("accessibleNameTarget focusTargetIds must be unique lowercase kebab-case");
    }
    focusIds.add(target.focusTargetId);
    const focusTarget = focusById.get(target.focusTargetId);
    if (!focusTarget || focusTarget.role !== "form-control") {
      fail(`accessibleNameTargets[${index}] must reference a form-control focusTarget`);
    }
    if (!ALLOWED_ROLES.has(target.expectedRole)) fail(`accessibleNameTargets[${index}].expectedRole is invalid`);
    if (typeof target.expectedName !== "string" || target.expectedName.length < 1
        || target.expectedName.length > 120 || target.expectedName.trim() !== target.expectedName) {
      fail(`accessibleNameTargets[${index}].expectedName is invalid`);
    }
  }
  if (focusIds.size !== focusTargets.length || focusTargets.some((target) => !focusIds.has(target.id))) {
    fail("accessibleNameTargets must exactly cover focusTargets");
  }
  return targets;
}

function aggregateAccessibleNameResults(targets, replayResults) {
  return targets.map((target) => {
    const replays = replayResults.get(target.id) || [];
    const fixed = { id: target.id, role: target.expectedRole, replays: replays.length };
    if (replays.length !== 2 || replays.some((item) => !item
        || !["match", "miss", "unavailable"].includes(item.status))) {
      return { ...fixed, status: "unavailable", reason: "runtime_unavailable" };
    }
    if (replays.some((item) => item.status === "unavailable")) {
      return {
        ...fixed,
        status: "unavailable",
        reason: publicUnavailableReason(replays.find((item) => item.status === "unavailable").reason),
      };
    }
    if (replays[0].signature !== replays[1].signature) {
      return { ...fixed, status: "unavailable", reason: "replay_unstable" };
    }
    if (replays[0].status !== replays[1].status) {
      return { ...fixed, status: "unavailable", reason: "replay_unstable" };
    }
    const matched = replays[0].status === "match";
    return { ...fixed, status: matched ? "clear" : "confirmed" };
  });
}

async function applyPrecedingSteps(page, steps, stopId) {
  for (const step of steps) {
    if (step.id === stopId) return true;
    const locator = page.locator(step.selector);
    if (await locator.count() !== 1) return false;
    if (step.action === "click") await locator.click({ timeout: OPERATION_TIMEOUT_MS });
    else if (step.action === "fill") await locator.fill(step.value, { timeout: OPERATION_TIMEOUT_MS });
    else if (step.action === "select") await locator.selectOption(step.value, { timeout: OPERATION_TIMEOUT_MS });
    else if (step.action === "press") await locator.press(step.value, { timeout: OPERATION_TIMEOUT_MS });
    else return false;
  }
  return false;
}

async function nativeDescriptor(locator) {
  return locator.evaluate((node) => {
    const tag = node.tagName.toLowerCase();
    if (tag === "textarea") return { supported: true, role: "textbox", signature: "textarea:textbox" };
    if (tag === "select") {
      const listbox = node.multiple || node.size > 1;
      return { supported: true, role: listbox ? "listbox" : "combobox", signature: `select:${listbox ? "listbox" : "combobox"}` };
    }
    if (tag !== "input") return { supported: false, reason: "unsupported_native_control" };
    const type = (node.getAttribute("type") || "text").toLowerCase();
    const roles = {
      button: "button",
      checkbox: "checkbox",
      email: "textbox",
      number: "spinbutton",
      radio: "radio",
      range: "slider",
      reset: "button",
      search: "searchbox",
      submit: "button",
      tel: "textbox",
      text: "textbox",
      url: "textbox",
    };
    const role = roles[type];
    return role
      ? { supported: true, role, signature: `input:${type}:${role}` }
      : { supported: false, reason: ["hidden", "password"].includes(type) ? "excluded_input_type" : "unsupported_input_type" };
  });
}

async function replayAccessibleNameTarget(browser, url, contextOptions, target, focusTarget, steps) {
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
    if (blockedExternalRequests) return { status: "unavailable", reason: "external_request_blocked" };
    let fontTimer;
    const fontsReady = await Promise.race([
      page.evaluate(() => document.fonts.ready.then(() => true)),
      new Promise((resolve) => { fontTimer = setTimeout(() => resolve(false), 10_000); }),
    ]).finally(() => clearTimeout(fontTimer));
    if (!fontsReady) return { status: "unavailable", reason: "font_loading_unavailable" };
    if (!(await applyPrecedingSteps(page, steps, focusTarget.stepId))) {
      return { status: "unavailable", reason: "preceding_step_unavailable" };
    }
    const step = steps.find((item) => item.id === focusTarget.stepId);
    if (!step) return { status: "unavailable", reason: "focus_step_missing" };
    const locator = page.locator(step.selector);
    if (await locator.count() !== 1) return { status: "unavailable", reason: "focus_target_count_invalid" };
    if (!(await locator.isVisible())) return { status: "unavailable", reason: "focus_target_not_visible" };
    const descriptor = await nativeDescriptor(locator);
    if (!descriptor.supported) return { status: "unavailable", reason: descriptor.reason };
    if (descriptor.role !== target.expectedRole) return { status: "unavailable", reason: "expected_role_incompatible" };

    const targetHandle = await locator.elementHandle();
    if (!targetHandle) return { status: "unavailable", reason: "focus_target_count_invalid" };
    const roleOnlyLocator = page.getByRole(target.expectedRole);
    const roleOnlyCount = await roleOnlyLocator.count();
    if (roleOnlyCount > 64) {
      await targetHandle.dispose();
      return { status: "unavailable", reason: "expected_role_incompatible" };
    }
    const roleOnlyHandles = await roleOnlyLocator.elementHandles();
    let roleMatched = false;
    for (const roleHandle of roleOnlyHandles) {
      roleMatched ||= await page.evaluate(([left, right]) => left === right, [targetHandle, roleHandle]);
      await roleHandle.dispose();
    }
    if (!roleMatched) {
      await targetHandle.dispose();
      return { status: "unavailable", reason: "expected_role_incompatible" };
    }

    const roleLocator = page.getByRole(target.expectedRole, { name: target.expectedName, exact: true });
    const roleCount = await roleLocator.count();
    if (roleCount > 1) {
      await targetHandle.dispose();
      return { status: "unavailable", reason: "role_name_not_unique" };
    }
    let matched = false;
    if (roleCount === 1) {
      const roleHandle = await roleLocator.elementHandle();
      matched = Boolean(roleHandle
        && await page.evaluate(([left, right]) => left === right, [targetHandle, roleHandle]));
      await roleHandle?.dispose();
    }
    await targetHandle.dispose();
    await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    if (blockedExternalRequests) return { status: "unavailable", reason: "external_request_blocked" };
    return { status: matched ? "match" : "miss", signature: descriptor.signature };
  } catch {
    return { status: "unavailable", reason: "accessible_name_replay_failed" };
  } finally {
    await context?.close().catch(() => {});
  }
}

async function auditAccessibleNames(browser, url, contextOptions, spec, replayRunner = replayAccessibleNameTarget) {
  validateAccessibleNameTargets(spec.accessibleNameTargets, spec.focusTargets);
  const focusById = new Map(spec.focusTargets.map((target) => [target.id, target]));
  const replayResults = new Map();
  for (const target of spec.accessibleNameTargets) {
    const focusTarget = focusById.get(target.focusTargetId);
    const results = [];
    for (let replay = 0; replay < 2; replay += 1) {
      results.push(await replayRunner(browser, url, contextOptions, target, focusTarget, spec.steps));
    }
    replayResults.set(target.id, results);
  }
  const accessibleNameControls = aggregateAccessibleNameResults(spec.accessibleNameTargets, replayResults);
  const unavailable = accessibleNameControls.some((item) => item.status === "unavailable");
  return {
    accessibleNameCoverage: {
      status: unavailable ? "unavailable" : "complete",
      reason: unavailable ? "one_or_more_targets_unavailable" : null,
      declaredTargets: spec.accessibleNameTargets.length,
      completedTargets: accessibleNameControls.filter((item) => item.status !== "unavailable").length,
      freshReplays: spec.accessibleNameTargets.length * 2,
      claimBoundary: CLAIM_BOUNDARY,
    },
    accessibleNameControls,
  };
}

module.exports = {
  aggregateAccessibleNameResults,
  auditAccessibleNames,
  replayAccessibleNameTarget,
  validateAccessibleNameTargets,
};
