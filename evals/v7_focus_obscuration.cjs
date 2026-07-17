#!/usr/bin/env node
"use strict";

const MAX_DOM_ELEMENTS = 2000;
const MAX_OCCLUDERS = 12;
const MAX_PARTITION_CELLS = 128;
const CLAIM_BOUNDARY = "Programmatic focus of evaluator-declared task controls against simple opaque author-created fixed/sticky DOM rectangles in the named browser/profile/state; no keyboard, virtual-keyboard, assistive-technology, or WCAG conformance claim.";

function aggregateFocusResults(focusTargets, replayResults) {
  const focusedControls = [];
  let completedTargets = 0;
  for (const target of focusTargets) {
    const replays = replayResults.get(target.id) || [];
    if (replays.length !== 2 || replays.some((item) => !item || !["clear", "obscured", "unavailable"].includes(item.status))) {
      focusedControls.push({
        id: target.id,
        role: target.role,
        status: "unavailable",
        fullyObscured: false,
        replays: replays.length,
        reason: "fresh_replay_incomplete",
      });
      continue;
    }
    if (replays.some((item) => item.status === "unavailable")) {
      const reason = replays.find((item) => item.status === "unavailable").reason;
      focusedControls.push({
        id: target.id,
        role: target.role,
        status: "unavailable",
        fullyObscured: false,
        replays: 2,
        reason,
      });
      continue;
    }
    if (replays[0].status !== replays[1].status) {
      focusedControls.push({
        id: target.id,
        role: target.role,
        status: "unavailable",
        fullyObscured: false,
        replays: 2,
        reason: "unstable_fresh_replay",
      });
      continue;
    }
    const geometryStable = Math.abs(replays[0].targetArea - replays[1].targetArea) <= 1
      && (replays[0].status !== "obscured" || (
        replays[0].occluderCount === replays[1].occluderCount
        && Math.abs(replays[0].coveredArea - replays[1].coveredArea) <= 1
      ));
    if (!geometryStable) {
      focusedControls.push({
        id: target.id,
        role: target.role,
        status: "unavailable",
        fullyObscured: false,
        replays: 2,
        reason: "unstable_fresh_replay_geometry",
      });
      continue;
    }
    completedTargets += 1;
    const obscured = replays[0].status === "obscured";
    focusedControls.push({
      id: target.id,
      role: target.role,
      status: obscured ? "confirmed" : "clear",
      fullyObscured: obscured,
      replays: 2,
      occluderCount: replays[0].occluderCount,
      targetArea: replays[0].targetArea,
      coveredArea: replays[0].coveredArea,
    });
  }
  const unavailable = focusedControls.some((item) => item.status === "unavailable");
  return {
    focusCoverage: {
      status: unavailable ? "unavailable" : focusTargets.length ? "complete" : "not_applicable",
      reason: unavailable ? "one_or_more_targets_unavailable" : null,
      declaredTargets: focusTargets.length,
      completedTargets,
      freshReplays: [...replayResults.values()].reduce((total, items) => total + items.length, 0),
      claimBoundary: CLAIM_BOUNDARY,
    },
    focusedControls,
  };
}

async function inspectFocusedControl(page, selector) {
  return page.evaluate(({ selector, limits }) => {
    const rectArea = (rect) => Math.max(0, rect.right - rect.left) * Math.max(0, rect.bottom - rect.top);
    const rectIntersect = (left, right) => {
      const result = {
        left: Math.max(left.left, right.left),
        top: Math.max(left.top, right.top),
        right: Math.min(left.right, right.right),
        bottom: Math.min(left.bottom, right.bottom),
      };
      return result.right > result.left && result.bottom > result.top ? result : null;
    };
    const target = document.querySelector(selector);
    if (!(target instanceof Element)) return { status: "unavailable", reason: "focus_target_missing" };
    const active = document.activeElement;
    if (!(active === target || target.contains(active))) return { status: "unavailable", reason: "programmatic_focus_failed" };
    const targetStyle = getComputedStyle(target);
    if (targetStyle.display === "none" || targetStyle.visibility !== "visible" || Number(targetStyle.opacity) < 0.999) {
      return { status: "unavailable", reason: "focus_target_not_visually_stable" };
    }
    const targetRect = target.getBoundingClientRect();
    if (targetRect.width <= 0 || targetRect.height <= 0) return { status: "unavailable", reason: "focus_target_not_rendered" };
    const viewport = window.visualViewport
      ? {
          left: window.visualViewport.offsetLeft,
          top: window.visualViewport.offsetTop,
          right: window.visualViewport.offsetLeft + window.visualViewport.width,
          bottom: window.visualViewport.offsetTop + window.visualViewport.height,
        }
      : { left: 0, top: 0, right: window.innerWidth, bottom: window.innerHeight };
    const tolerance = 1;
    if (targetRect.left < viewport.left - tolerance || targetRect.top < viewport.top - tolerance
        || targetRect.right > viewport.right + tolerance || targetRect.bottom > viewport.bottom + tolerance) {
      return { status: "unavailable", reason: "target_not_fully_in_viewport" };
    }
    const nodes = [...document.querySelectorAll("*")];
    if (nodes.length > limits.maxDomElements) return { status: "unavailable", reason: "dom_budget_exceeded" };

    const targetBox = { left: targetRect.left, top: targetRect.top, right: targetRect.right, bottom: targetRect.bottom };
    const candidates = [];
    const complex = [];
    const alpha = (color) => {
      const match = color.match(/^rgba?\((?:[^,]+,){3}\s*([\d.]+)\s*\)$/i);
      if (match) return Number(match[1]);
      return /^rgb\(/i.test(color) ? 1 : null;
    };
    const zeroRadius = (style) => [
      style.borderTopLeftRadius,
      style.borderTopRightRadius,
      style.borderBottomRightRadius,
      style.borderBottomLeftRadius,
    ].every((value) => value === "0px");
    const hasComplexPaintAncestor = (node) => {
      for (let ancestor = node.parentElement; ancestor; ancestor = ancestor.parentElement) {
        const style = getComputedStyle(ancestor);
        const containment = new Set(style.contain.split(/\s+/));
        if (Number(style.opacity) < 0.999 || style.transform !== "none"
            || (style.translate || "none") !== "none" || (style.rotate || "none") !== "none"
            || (style.scale || "none") !== "none" || (style.offsetPath || "none") !== "none"
            || style.perspective !== "none"
            || (style.clip || "auto") !== "auto" || (style.clipPath || "none") !== "none"
            || (style.maskImage || "none") !== "none" || (style.filter || "none") !== "none"
            || (style.mixBlendMode || "normal") !== "normal"
            || style.overflowX !== "visible" || style.overflowY !== "visible"
            || containment.has("paint") || containment.has("content") || containment.has("strict")) {
          return true;
        }
      }
      return false;
    };
    for (const node of nodes) {
      if (node === target || target.contains(node) || node.contains(target)) continue;
      const style = getComputedStyle(node);
      if (!["fixed", "sticky"].includes(style.position) || style.display === "none"
          || style.visibility === "hidden" || Number(style.opacity) <= 0.01) continue;
      const raw = node.getBoundingClientRect();
      const rect = rectIntersect(targetBox, raw);
      if (!rect) continue;
      const cx = (rect.left + rect.right) / 2;
      const cy = (rect.top + rect.bottom) / 2;
      const stack = document.elementsFromPoint(cx, cy);
      const targetIndex = stack.findIndex((item) => item === target || target.contains(item));
      const nodeIndex = stack.indexOf(node);
      if (nodeIndex >= 0 && targetIndex >= 0 && nodeIndex > targetIndex) continue;
      if (nodeIndex < 0 || targetIndex < 0) {
        complex.push(node);
        continue;
      }
      const backgroundAlpha = alpha(style.backgroundColor);
      const simple = Number(style.opacity) >= 0.999 && backgroundAlpha !== null && backgroundAlpha >= 0.999
        && style.backgroundClip.split(",").every((value) => value.trim() === "border-box")
        && style.transform === "none" && (style.translate || "none") === "none"
        && (style.rotate || "none") === "none" && (style.scale || "none") === "none"
        && (style.offsetPath || "none") === "none" && (style.clip || "auto") === "auto"
        && (style.clipPath || "none") === "none" && (style.maskImage || "none") === "none"
        && (style.filter || "none") === "none" && (style.mixBlendMode || "normal") === "normal"
        && zeroRadius(style) && !hasComplexPaintAncestor(node);
      if (!simple) complex.push(node);
      else candidates.push({ node, rect });
    }
    if (complex.length) return { status: "unavailable", reason: "complex_occluder_geometry" };
    if (candidates.length > limits.maxOccluders) return { status: "unavailable", reason: "occluder_budget_exceeded" };
    if (!candidates.length) return { status: "clear", occluderCount: 0, targetArea: rectArea(targetBox), coveredArea: 0 };

    const xs = [...new Set([targetBox.left, targetBox.right, ...candidates.flatMap(({ rect }) => [rect.left, rect.right])])].sort((a, b) => a - b);
    const ys = [...new Set([targetBox.top, targetBox.bottom, ...candidates.flatMap(({ rect }) => [rect.top, rect.bottom])])].sort((a, b) => a - b);
    if ((xs.length - 1) * (ys.length - 1) > limits.maxPartitionCells) {
      return { status: "unavailable", reason: "partition_budget_exceeded" };
    }
    let coveredArea = 0;
    for (let x = 0; x < xs.length - 1; x += 1) {
      for (let y = 0; y < ys.length - 1; y += 1) {
        const cell = { left: xs[x], right: xs[x + 1], top: ys[y], bottom: ys[y + 1] };
        if (rectArea(cell) <= 0) continue;
        const cx = (cell.left + cell.right) / 2;
        const cy = (cell.top + cell.bottom) / 2;
        const stack = document.elementsFromPoint(cx, cy);
        const targetIndex = stack.findIndex((item) => item === target || target.contains(item));
        const covering = candidates.find(({ node, rect }) => rect.left <= cx && rect.right >= cx
          && rect.top <= cy && rect.bottom >= cy && stack.indexOf(node) >= 0
          && (targetIndex < 0 || stack.indexOf(node) < targetIndex));
        if (!covering) return { status: "clear", occluderCount: candidates.length, targetArea: rectArea(targetBox), coveredArea };
        coveredArea += rectArea(cell);
      }
    }
    return {
      status: "obscured",
      occluderCount: candidates.length,
      targetArea: rectArea(targetBox),
      coveredArea,
    };
  }, {
    selector,
    limits: {
      maxDomElements: MAX_DOM_ELEMENTS,
      maxOccluders: MAX_OCCLUDERS,
      maxPartitionCells: MAX_PARTITION_CELLS,
    },
  });
}

async function applyPrecedingSteps(page, steps, stopId) {
  for (const step of steps) {
    if (step.id === stopId) return;
    const locator = page.locator(step.selector);
    if (await locator.count() !== 1) throw new Error("preceding_step_unavailable");
    if (step.action === "click") await locator.click();
    else if (step.action === "fill") await locator.fill(step.value);
    else if (step.action === "select") await locator.selectOption(step.value);
    else await locator.press(step.value);
  }
  throw new Error("focus_step_missing");
}

async function replayFocusTarget(browser, url, contextOptions, target, steps) {
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
    await applyPrecedingSteps(page, steps, target.stepId);
    const step = steps.find((item) => item.id === target.stepId);
    const locator = page.locator(step.selector);
    if (await locator.count() !== 1) return { status: "unavailable", reason: "focus_target_count_invalid" };
    await locator.scrollIntoViewIfNeeded();
    await locator.focus();
    await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    if (blockedExternalRequests) return { status: "unavailable", reason: "external_request_blocked" };
    return await inspectFocusedControl(page, step.selector);
  } catch (error) {
    const allowed = new Set(["preceding_step_unavailable", "focus_step_missing"]);
    return { status: "unavailable", reason: allowed.has(error.message) ? error.message : "focus_replay_failed" };
  } finally {
    await context?.close().catch(() => {});
  }
}

async function auditFocusedControls(browser, url, contextOptions, spec, replayRunner = replayFocusTarget) {
  if (spec.schemaVersion !== 2) {
    return {
      focusCoverage: {
        status: "unavailable",
        reason: "focus_targets_not_declared",
        declaredTargets: 0,
        completedTargets: 0,
        freshReplays: 0,
        claimBoundary: CLAIM_BOUNDARY,
      },
      focusedControls: [],
    };
  }
  const replayResults = new Map();
  for (const target of spec.focusTargets) {
    const results = [];
    for (let replay = 0; replay < 2; replay += 1) {
      results.push(await replayRunner(browser, url, contextOptions, target, spec.steps));
    }
    replayResults.set(target.id, results);
  }
  return aggregateFocusResults(spec.focusTargets, replayResults);
}

module.exports = {
  CLAIM_BOUNDARY,
  aggregateFocusResults,
  auditFocusedControls,
  inspectFocusedControl,
  replayFocusTarget,
};
