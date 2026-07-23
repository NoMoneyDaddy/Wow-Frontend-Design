#!/usr/bin/env node
"use strict";

const { createHash } = require("node:crypto");
const { AxeBuilder } = require("@axe-core/playwright");
const { runLocalPageMatrix } = require("./playwright_browser_runtime.cjs");

const VIEWPORTS = [
  { name: "desktop", viewport: { width: 1440, height: 1000 }, reducedMotion: "no-preference" },
  { name: "mobile", viewport: { width: 390, height: 844 }, reducedMotion: "reduce" },
  { name: "narrow", viewport: { width: 320, height: 800 }, reducedMotion: "reduce" },
];
const MOBILE_MOTION_VIEWPORT = {
  name: "mobile-motion", viewport: { width: 390, height: 844 }, reducedMotion: "no-preference",
};
const LOCATOR_ROLES = new Set([
  "button", "checkbox", "combobox", "dialog", "form", "group", "heading", "link",
  "listbox", "menuitem", "navigation", "option", "radio", "region", "searchbox",
  "slider", "spinbutton", "switch", "tab", "table", "textbox", "treeitem",
]);
const MAX_AXE_TARGET_DESCRIPTORS = 32;

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function normalizedHexColor(value) {
  if (typeof value !== "string") return null;
  const match = value.trim().toLowerCase().match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/);
  if (!match) return null;
  const hex = match[1];
  return hex.length === 3
    ? `#${[...hex].map((character) => character.repeat(2)).join("")}`
    : `#${hex}`;
}

function ratioX100(value) {
  const numeric = typeof value === "number"
    ? value
    : Number.parseFloat(typeof value === "string" ? value : "");
  return Number.isFinite(numeric) && numeric >= 0 && numeric <= 21
    ? Math.round(numeric * 100)
    : null;
}

function contrastDescriptor(node) {
  for (const check of [...(node.any || []), ...(node.all || []), ...(node.none || [])]) {
    const data = check && typeof check === "object" ? check.data : null;
    if (!data || typeof data !== "object") continue;
    const foreground = normalizedHexColor(data.fgColor);
    const background = normalizedHexColor(data.bgColor);
    const actualRatio = ratioX100(data.contrastRatio);
    const requiredRatio = ratioX100(data.expectedContrastRatio);
    if (foreground && background && actualRatio !== null && requiredRatio !== null) {
      return {
        foreground,
        background,
        actual_ratio_x100: actualRatio,
        required_ratio_x100: requiredRatio,
      };
    }
  }
  return null;
}

async function structuralTargetPath(page, target) {
  if (!Array.isArray(target) || target.length !== 1 || typeof target[0] !== "string") return null;
  try {
    return await page.evaluate((selector) => globalThis.__wowEvaluatorRead?.structuralPath(selector) || null, target[0]);
  } catch {
    return null;
  }
}

async function summarizeAxeTargets(page, violations) {
  const identities = new Map();
  for (const violation of violations) {
    if (!violation || !/^[a-z0-9][a-z0-9-]{0,63}$/.test(violation.id)
      || !Array.isArray(violation.nodes)) continue;
    for (const node of violation.nodes) {
      const path = await structuralTargetPath(page, node?.target);
      const fingerprintSource = path
        ? JSON.stringify(path)
        : JSON.stringify(Array.isArray(node?.target) ? node.target : []);
      const targetSha256 = sha256(fingerprintSource);
      const identity = `${violation.id}\0${targetSha256}`;
      if (identities.has(identity)) continue;
      let descriptor = null;
      if (path) {
        descriptor = { rule_id: violation.id, target_sha256: targetSha256, path };
        const contrast = violation.id === "color-contrast" ? contrastDescriptor(node) : null;
        if (contrast) descriptor.contrast = contrast;
      }
      identities.set(identity, descriptor);
    }
  }
  const orderedIdentities = [...identities.keys()].sort();
  const descriptors = orderedIdentities
    .map((identity) => identities.get(identity))
    .filter(Boolean)
    .slice(0, MAX_AXE_TARGET_DESCRIPTORS);
  const identityPairs = orderedIdentities.map((identity) => identity.split("\0"));
  return {
    axe_target_count: orderedIdentities.length,
    axe_target_set_sha256: sha256(JSON.stringify(identityPairs)),
    axe_targets_truncated: descriptors.length !== orderedIdentities.length,
    axe_target_descriptors: descriptors,
  };
}

function fail(message) {
  process.stderr.write(`html smoke infrastructure failure: ${message}\n`);
  process.exitCode = 2;
}

function exactKeys(value, expected) {
  const keys = Object.keys(value).sort();
  return keys.length === expected.length && keys.every((key, index) => key === [...expected].sort()[index]);
}

function boundedContractText(value, maximum, allowEmpty = false) {
  return typeof value === "string"
    && (allowEmpty || value.length > 0)
    && Buffer.byteLength(value) <= maximum
    && !/[\u0000-\u001f\u007f]/u.test(value);
}

function validateBrowserContract(value, pages) {
  if (!value || typeof value !== "object" || Array.isArray(value)
    || !exactKeys(value, ["cases", "schema_version"])
    || ![1, 2].includes(value.schema_version) || !Array.isArray(value.cases)
    || value.cases.length < 1 || value.cases.length > 4) throw new Error("invalid browser contract");
  const assertions = value.schema_version === 1
    ? ["attribute-equals", "count-equals", "fully-visible-in-viewport", "text-includes", "visible"]
    : [
      "active-animation-count-between", "animations-inactive-for", "animations-settled", "attribute-equals", "count-equals",
      "font-face-loaded", "fully-visible-in-viewport",
      "inline-size-ratio-between", "inline-start-aligned-with", "last-line-graphemes-at-least", "line-count-between", "no-content-overflow",
      "rendered-text-excludes", "rendered-text-includes", "text-includes", "text-segment-on-one-line", "visible",
    ];
  const ids = new Set();
  const routes = new Set();
  for (const contractCase of value.cases) {
    if (!contractCase || typeof contractCase !== "object" || Array.isArray(contractCase)
      || !exactKeys(contractCase, ["id", "page", "profile", "steps"])
      || !/^[a-z][a-z0-9-]{0,47}$/.test(contractCase.id)
      || ids.has(contractCase.id) || !pages.includes(contractCase.page)
      || !(value.schema_version === 1
        ? ["desktop", "mobile"]
        : ["desktop", "mobile", "narrow", "mobile-motion"]).includes(contractCase.profile)
      || !Array.isArray(contractCase.steps) || contractCase.steps.length < 1 || contractCase.steps.length > 24) {
      throw new Error("invalid browser contract case");
    }
    const route = `${contractCase.page}\0${contractCase.profile}`;
    if (routes.has(route)) throw new Error("duplicate browser contract route");
    ids.add(contractCase.id);
    routes.add(route);
    const stepIds = new Set();
    let actionObserved = false;
    let inactivityAssertionSeen = false;
    for (const step of contractCase.steps) {
      const usesSelector = Object.hasOwn(step || {}, "selector");
      const usesRole = Object.hasOwn(step || {}, "role") || Object.hasOwn(step || {}, "name");
      if (usesSelector === usesRole || (usesRole && value.schema_version !== 2)) {
        throw new Error("invalid browser contract step locator");
      }
      const expectedKeys = usesSelector ? ["action", "id", "selector"] : ["action", "id", "name", "role"];
      if (["fill", "select"].includes(step?.action)) expectedKeys.push("value");
      if (step?.action === "press") expectedKeys.push("key");
      if (step?.action === "assert") {
        expectedKeys.push("expect");
        if (["attribute-equals", "rendered-text-excludes", "rendered-text-includes", "text-includes"].includes(step.expect)) expectedKeys.push("value");
        if (step.expect === "attribute-equals") expectedKeys.push("attribute");
        if (step.expect === "count-equals") expectedKeys.push("count");
        if (step.expect === "font-face-loaded") expectedKeys.push("family");
        if (step.expect === "inline-size-ratio-between") expectedKeys.push("reference_selector", "min_ratio", "max_ratio");
        if (step.expect === "inline-start-aligned-with") expectedKeys.push("reference_selector");
        if (step.expect === "last-line-graphemes-at-least") expectedKeys.push("count");
        if (step.expect === "line-count-between") expectedKeys.push("min_lines", "max_lines");
        if (step.expect === "text-segment-on-one-line") expectedKeys.push("segment");
        if (step.expect === "active-animation-count-between") expectedKeys.push("min_animations", "max_animations");
        if (step.expect === "animations-inactive-for") expectedKeys.push("duration_ms");
      }
      if (!step || typeof step !== "object" || Array.isArray(step)
        || !exactKeys(step, expectedKeys)
        || !/^[a-z][a-z0-9-]{0,47}$/.test(step.id) || stepIds.has(step.id)
        || !["assert", "click", "fill", "press", "select"].includes(step.action)
        || (usesSelector && !boundedContractText(step.selector, 256))
        || (usesRole && (!LOCATOR_ROLES.has(step.role) || !boundedContractText(step.name, 256)))) {
        throw new Error("invalid browser contract step");
      }
      if (["fill", "select"].includes(step.action)
        && !boundedContractText(step.value, 256)) {
        throw new Error("invalid browser contract value");
      }
      if (step.action === "press"
        && !["ArrowDown", "ArrowLeft", "ArrowRight", "ArrowUp", "End", "Enter", "Escape", "Home", "Space", "Tab"].includes(step.key)) {
        throw new Error("invalid browser contract key");
      }
      if (step.action === "assert") {
        if (!assertions.includes(step.expect)) {
          throw new Error("invalid browser contract assertion");
        }
        if (step.expect === "fully-visible-in-viewport" && actionObserved) {
          throw new Error("first viewport assertion must precede actions");
        }
        if (step.expect === "attribute-equals"
          && (typeof step.attribute !== "string" || !/^[A-Za-z_:][A-Za-z0-9_.:-]{0,63}$/.test(step.attribute)
            || typeof step.value !== "string" || Buffer.byteLength(step.value) > 256)) {
          throw new Error("invalid browser contract attribute assertion");
        }
        if (["rendered-text-excludes", "rendered-text-includes", "text-includes"].includes(step.expect)
          && !boundedContractText(step.value, 256)) {
          throw new Error("invalid browser contract text assertion");
        }
        if (step.expect === "count-equals"
          && (!Number.isInteger(step.count) || step.count < 0 || step.count > 1000)) {
          throw new Error("invalid browser contract count assertion");
        }
        if (step.expect === "font-face-loaded"
          && !boundedContractText(step.family, 128)) {
          throw new Error("invalid browser contract font assertion");
        }
        if (step.expect === "inline-start-aligned-with"
          && !boundedContractText(step.reference_selector, 256)) {
          throw new Error("invalid browser contract alignment assertion");
        }
        if (step.expect === "inline-size-ratio-between"
          && (!boundedContractText(step.reference_selector, 256)
            || typeof step.min_ratio !== "number" || !Number.isFinite(step.min_ratio)
            || typeof step.max_ratio !== "number" || !Number.isFinite(step.max_ratio)
            || !(step.min_ratio > 0 && step.min_ratio <= step.max_ratio && step.max_ratio <= 4))) {
          throw new Error("invalid browser contract inline size ratio assertion");
        }
        if (step.expect === "last-line-graphemes-at-least"
          && (!Number.isInteger(step.count) || step.count < 1 || step.count > 128)) {
          throw new Error("invalid browser contract grapheme assertion");
        }
        if (step.expect === "line-count-between"
          && (!Number.isInteger(step.min_lines) || !Number.isInteger(step.max_lines)
            || step.min_lines < 1 || step.min_lines > step.max_lines || step.max_lines > 128)) {
          throw new Error("invalid browser contract line assertion");
        }
        if (step.expect === "text-segment-on-one-line"
          && (!boundedContractText(step.segment, 128) || step.segment.trim() !== step.segment)) {
          throw new Error("invalid browser contract text segment assertion");
        }
        if (step.expect === "active-animation-count-between"
          && (!Number.isInteger(step.min_animations) || !Number.isInteger(step.max_animations)
            || step.min_animations < 0 || step.min_animations > step.max_animations || step.max_animations > 128)) {
          throw new Error("invalid browser contract animation assertion");
        }
        if (step.expect === "animations-inactive-for"
          && (inactivityAssertionSeen || !Number.isInteger(step.duration_ms)
            || step.duration_ms < 50 || step.duration_ms > 1000)) {
          throw new Error("invalid browser contract animation inactivity assertion");
        }
        if (step.expect === "animations-inactive-for") inactivityAssertionSeen = true;
      } else {
        actionObserved = true;
      }
      stepIds.add(step.id);
    }
  }
  return value;
}

function validateSourceLayoutRisks(value, pages) {
  if (!value || typeof value !== "object" || Array.isArray(value)
    || !exactKeys(value, ["heading_explicit_narrow_pages", "schema_version"])
    || value.schema_version !== 2
    || !Array.isArray(value.heading_explicit_narrow_pages)
    || value.heading_explicit_narrow_pages.length > pages.length
    || value.heading_explicit_narrow_pages.some((item) => typeof item !== "string" || !pages.includes(item))
    || value.heading_explicit_narrow_pages.join("\0")
      !== [...new Set(value.heading_explicit_narrow_pages)].sort().join("\0")) {
    throw new Error("invalid source layout risks");
  }
  return value;
}

async function settleStep(page) {
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  await page.waitForTimeout(20);
}

async function checkAssertion(page, locator, step) {
  const count = await locator.count();
  if (step.expect === "count-equals") return count === step.count;
  if (count !== 1) return false;
  if (step.expect === "visible") return locator.isVisible();
  if (step.expect === "attribute-equals") return await locator.getAttribute(step.attribute) === step.value;
  if (step.expect === "text-includes") return (await locator.textContent() || "").includes(step.value);
  if (step.expect === "inline-start-aligned-with") {
    const reference = page.locator(step.reference_selector);
    if (await reference.count() !== 1) return false;
    const snapshot = async () => {
      const [candidateHandle, anchorHandle] = await Promise.all([
        locator.elementHandle(), reference.elementHandle(),
      ]);
      if (!candidateHandle || !anchorHandle) return null;
      try {
        return await page.evaluate(({ candidate, anchor }) => {
          const trusted = globalThis.__wowEvaluatorRead;
          if (!trusted) return null;
          const probe = (element) => {
            let current = element;
            while (current) {
              const display = trusted.style(current, "display");
              const visibility = trusted.style(current, "visibility");
              if (display === "none" || visibility === "hidden"
                || visibility === "collapse" || trusted.zeroNumber(trusted.style(current, "opacity"))) return null;
              current = trusted.parent(current);
            }
            const box = trusted.rect(element);
            const direction = trusted.style(element, "direction");
            const writingMode = trusted.style(element, "writing-mode");
            if (!(box.width > 0 && box.height > 0) || !trusted.horizontalWritingMode(writingMode)
              || (direction !== "ltr" && direction !== "rtl")) return null;
            return { direction, inlineStart: direction === "rtl" ? box.right : box.left };
          };
          return { candidate: probe(candidate), anchor: probe(anchor) };
        }, { candidate: candidateHandle, anchor: anchorHandle });
      } finally {
        await candidateHandle.dispose();
        await anchorHandle.dispose();
      }
    };
    const aligned = (value) => value !== null && value.candidate !== null && value.anchor !== null
      && value.candidate.direction === value.anchor.direction
      && Math.abs(value.candidate.inlineStart - value.anchor.inlineStart) <= 1;
    const first = await snapshot();
    if (!aligned(first)) return false;
    await page.waitForTimeout(50);
    const second = await snapshot();
    return aligned(second)
      && Math.abs(first.candidate.inlineStart - second.candidate.inlineStart) <= 1
      && Math.abs(first.anchor.inlineStart - second.anchor.inlineStart) <= 1;
  }
  if (step.expect === "inline-size-ratio-between") {
    const reference = page.locator(step.reference_selector);
    if (await reference.count() !== 1) return false;
    const snapshot = async () => {
      const [candidateHandle, referenceHandle] = await Promise.all([
        locator.elementHandle(), reference.elementHandle(),
      ]);
      if (!candidateHandle || !referenceHandle) return null;
      try {
        return await page.evaluate(({ candidate, anchor }) => {
          const trusted = globalThis.__wowEvaluatorRead;
          if (!trusted) return null;
          const probe = (element) => {
            let current = element;
            while (current) {
              const display = trusted.style(current, "display");
              const visibility = trusted.style(current, "visibility");
              if (display === "none" || visibility === "hidden"
                || visibility === "collapse" || trusted.zeroNumber(trusted.style(current, "opacity"))) return null;
              current = trusted.parent(current);
            }
            const box = trusted.rect(element);
            const writingMode = trusted.style(element, "writing-mode");
            if (!(box.width > 0 && box.height > 0) || !trusted.horizontalWritingMode(writingMode)) return null;
            return box.width;
          };
          return { candidate: probe(candidate), reference: probe(anchor) };
        }, { candidate: candidateHandle, anchor: referenceHandle });
      } finally {
        await candidateHandle.dispose();
        await referenceHandle.dispose();
      }
    };
    const withinBounds = (value) => value !== null
      && value.candidate !== null && value.reference !== null && value.reference > 0
      && value.candidate / value.reference >= step.min_ratio
      && value.candidate / value.reference <= step.max_ratio;
    const first = await snapshot();
    if (!withinBounds(first)) return false;
    await page.waitForTimeout(50);
    const second = await snapshot();
    return withinBounds(second)
      && Math.abs(first.candidate - second.candidate) <= 1
      && Math.abs(first.reference - second.reference) <= 1;
  }
  if ([
    "active-animation-count-between", "animations-inactive-for", "animations-settled", "font-face-loaded",
    "last-line-graphemes-at-least", "line-count-between", "no-content-overflow",
    "rendered-text-excludes", "rendered-text-includes", "text-segment-on-one-line",
  ].includes(step.expect)) {
    return locator.evaluate((element, assertion) => {
      const trusted = globalThis.__wowEvaluatorRead;
      if (!trusted) return false;
      const styleVisible = (candidate) => {
        let current = candidate;
        while (current) {
          const display = trusted.style(current, "display");
          const visibility = trusted.style(current, "visibility");
          if (display === "none" || visibility === "hidden"
            || visibility === "collapse" || trusted.zeroNumber(trusted.style(current, "opacity"))) return false;
          current = trusted.parent(current);
        }
        return true;
      };
      const elementBox = trusted.rect(element);
      if (assertion.expect === "rendered-text-excludes") {
        if (!trusted.renderedTextIncludes(element, "")) return false;
        if (!styleVisible(element)) return true;
        return !trusted.renderedTextIncludes(element, assertion.value);
      }
      if (!styleVisible(element) || !(elementBox.width > 0 && elementBox.height > 0)) return false;
      const textNodes = () => {
        const nodes = [];
        const candidates = trusted.textNodes(element);
        for (let index = 0; index < candidates.length; index += 1) {
          const node = candidates[index];
          if (trusted.hasVisibleText(trusted.text(node) || "") && styleVisible(trusted.parent(node))) {
            nodes[nodes.length] = node;
          }
        }
        return nodes;
      };
      if (assertion.expect === "animations-inactive-for") {
        return trusted.animationsInactiveFor(element, assertion.duration_ms);
      }
      if (assertion.expect === "active-animation-count-between" || assertion.expect === "animations-settled") {
        const active = trusted.activeAnimationCount(element);
        if (assertion.expect === "animations-settled") return active === 0;
        return active >= assertion.min_animations && active <= assertion.max_animations;
      }
      if (assertion.expect === "font-face-loaded") {
        return trusted.fontFaceLoaded(element, assertion.family);
      }
      if (assertion.expect === "rendered-text-includes") {
        return trusted.renderedTextIncludes(element, assertion.value);
      }
      if (assertion.expect === "no-content-overflow") {
        const metrics = trusted.scrollMetrics(element);
        return metrics.clientWidth > 0 && metrics.clientHeight > 0
          && metrics.scrollWidth <= metrics.clientWidth + 1 && metrics.scrollHeight <= metrics.clientHeight + 1;
      }
      const profile = trusted.renderedLineProfile(element);
      if (!profile) return false;
      if (assertion.expect === "line-count-between") {
        return profile.lineCount >= assertion.min_lines && profile.lineCount <= assertion.max_lines;
      }
      let combined = "";
      const nodes = textNodes();
      for (let nodeIndex = 0; nodeIndex < nodes.length; nodeIndex += 1) {
        const node = nodes[nodeIndex];
        const value = trusted.text(node) || "";
        combined += value;
      }
      const literalRange = assertion.expect === "text-segment-on-one-line"
        ? trusted.uniqueLiteralRange(combined, assertion.segment)
        : null;
      if (assertion.expect === "text-segment-on-one-line" && !literalRange) return false;
      if (assertion.expect === "text-segment-on-one-line") {
        const matched = [];
        let expectedGraphemes = 0;
        const expectedSegments = trusted.segments(assertion.segment, trusted.locale() || undefined);
        for (let index = 0; index < expectedSegments.length; index += 1) {
          if (trusted.hasVisibleText(expectedSegments[index].value)) expectedGraphemes += 1;
        }
        for (let index = 0; index < profile.segments.length; index += 1) {
          const record = profile.segments[index];
          if (record.start >= literalRange.start && record.end <= literalRange.end) matched[matched.length] = record;
        }
        if (expectedGraphemes === 0 || matched.length !== expectedGraphemes) return false;
        for (let index = 1; index < matched.length; index += 1) {
          if (matched[index].line !== matched[0].line) return false;
        }
        return true;
      }
      return profile.lastLineGraphemes >= assertion.count;
    }, step);
  }
  if (step.expect !== "fully-visible-in-viewport") return false;
  return locator.evaluate(async (element) => {
    const box = element.getBoundingClientRect();
    let current = element;
    while (current instanceof Element) {
      const style = getComputedStyle(current);
      if (style.display === "none" || style.visibility === "hidden"
        || style.visibility === "collapse" || Number(style.opacity) === 0) return false;
      current = current.parentElement;
    }
    if (!(box.width > 0 && box.height > 0 && box.left >= 0 && box.top >= 0
      && box.right <= innerWidth && box.bottom <= innerHeight)) return false;
    return new Promise((resolve) => {
      const observer = new IntersectionObserver(([entry]) => {
        observer.disconnect();
        resolve(Boolean(entry?.isIntersecting && entry.intersectionRatio === 1));
      }, { threshold: [1] });
      observer.observe(element);
    });
  });
}

async function waitForAssertion(page, locator, step) {
  if (step.expect === "animations-inactive-for") return checkAssertion(page, locator, step);
  const deadline = Date.now() + 2_000;
  do {
    if (await checkAssertion(page, locator, step)) return true;
    await page.waitForTimeout(50);
  } while (Date.now() < deadline);
  return false;
}

async function runBrowserContract(page, contractCase) {
  const findingIds = [];
  const failures = [];
  let stepsExecuted = 0;
  let actionObserved = false;
  for (const step of contractCase.steps) {
    if (findingIds.length > 0 && (actionObserved || step.action !== "assert")) break;
    const finding = `contract-${contractCase.id}-${step.id}`;
    const locator = Object.hasOwn(step, "selector")
      ? page.locator(step.selector)
      : page.getByRole(step.role, { name: step.name, exact: true });
    let passed = false;
    try {
      if (step.action === "click") {
        await locator.click({ timeout: 2_000 });
        passed = true;
      } else if (step.action === "fill") {
        await locator.fill(step.value, { timeout: 2_000 });
        passed = true;
      } else if (step.action === "select") {
        await locator.selectOption(step.value, { timeout: 2_000 });
        passed = true;
      } else if (step.action === "press") {
        await locator.press(step.key, { timeout: 2_000 });
        passed = true;
      } else if (step.action === "assert") {
        passed = await waitForAssertion(page, locator, step);
      }
    } catch {
      passed = false;
    }
    stepsExecuted += 1;
    if (!passed) {
      findingIds.push(finding);
      let matches = null;
      try {
        matches = await locator.count();
      } catch {
        matches = null;
      }
      const reason = step.action === "assert" && step.expect === "count-equals"
        ? "assertion-not-satisfied"
        : matches === 0
          ? "locator-missing"
          : matches > 1
            ? "locator-ambiguous"
            : step.action === "assert" ? "assertion-not-satisfied" : "action-failed";
      failures.push({ finding_id: finding, reason });
      if (actionObserved || step.action !== "assert") break;
      continue;
    }
    if (step.action !== "assert") {
      actionObserved = true;
      await settleStep(page);
    }
  }
  await page.waitForTimeout(300);
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  return {
    case_id: contractCase.id,
    status: findingIds.length === 0 ? "passed" : "rejected",
    finding_ids: findingIds,
    failures,
    steps_executed: stepsExecuted,
  };
}

async function main() {
  if (![5, 6, 7].includes(process.argv.length)) {
    fail("expected stage, JSON page list, JSON output list, optional browser contract and optional source layout risks");
    return;
  }
  const stage = process.argv[2];
  const pages = JSON.parse(process.argv[3]);
  const allowedFiles = JSON.parse(process.argv[4]);
  if (!Array.isArray(pages) || pages.length === 0 || pages.some((item) => typeof item !== "string")
    || !Array.isArray(allowedFiles) || allowedFiles.some((item) => typeof item !== "string")) {
    fail("invalid page list");
    return;
  }
  const rawBrowserContract = process.argv.length >= 6 ? JSON.parse(process.argv[5]) : null;
  const browserContract = rawBrowserContract === null
    ? null
    : validateBrowserContract(rawBrowserContract, pages);
  const sourceLayoutRisks = process.argv.length === 7
    ? validateSourceLayoutRisks(JSON.parse(process.argv[6]), pages)
    : { schema_version: 2, heading_explicit_narrow_pages: [] };
  const profiles = browserContract?.cases.some((item) => item.profile === "mobile-motion")
    ? [...VIEWPORTS, MOBILE_MOTION_VIEWPORT]
    : VIEWPORTS;
  const { browserVersion, results } = await runLocalPageMatrix({
    stage,
    pages,
    allowedFiles,
    profiles,
    inspectPage: async (page, { relativePage, profile }) => {
      const analysis = await new AxeBuilder({ page })
        .options({ rules: { "label-content-name-mismatch": { enabled: true } } })
        .analyze();
      const axeTargets = await summarizeAxeTargets(page, analysis.violations);
      const headingExplicitNarrowRisk = sourceLayoutRisks.heading_explicit_narrow_pages.includes(relativePage);
      const layoutHazards = await page.evaluate(({ inspectCjkHeadingWidth }) => {
        const visible = (element) => {
          let current = element;
          while (current instanceof Element) {
            const currentStyle = getComputedStyle(current);
            if (currentStyle.display === "none" || currentStyle.visibility === "hidden"
              || currentStyle.visibility === "collapse" || Number(currentStyle.opacity) === 0) return false;
            current = current.parentElement;
          }
          const box = element.getBoundingClientRect();
          return box.width > 0 && box.height > 0;
        };
        const paintedColor = (value) => {
          if (!value || value === "transparent") return false;
          const slashAlpha = value.match(/\/\s*([\d.]+)%?\s*\)$/);
          if (slashAlpha) return Number(slashAlpha[1]) > 0;
          const legacyAlpha = value.match(/^(?:rgba|hsla)\((?:[^,]+,){3}\s*([\d.]+)\s*\)$/);
          return !legacyAlpha || Number(legacyAlpha[1]) > 0;
        };
        const paintRects = (element) => {
          const style = getComputedStyle(element);
          const box = element.getBoundingClientRect();
          const rects = [];
          if (paintedColor(style.backgroundColor) || style.backgroundImage !== "none"
            || element.matches("button,input,select,textarea,img,svg,canvas,video")) rects.push(box);
          for (const node of element.childNodes) {
            if (node.nodeType !== Node.TEXT_NODE || !(node.textContent || "").trim()) continue;
            const range = document.createRange();
            range.selectNodeContents(node);
            rects.push(...Array.from(range.getClientRects()));
          }
          for (const side of ["Top", "Right", "Bottom", "Left"]) {
            const width = Number.parseFloat(style[`border${side}Width`]);
            if (!(width > 0) || style[`border${side}Style`] === "none"
              || !paintedColor(style[`border${side}Color`])) continue;
            if (side === "Top") rects.push({ left: box.left, right: box.right, top: box.top, bottom: box.top + width, width: box.width, height: width });
            if (side === "Bottom") rects.push({ left: box.left, right: box.right, top: box.bottom - width, bottom: box.bottom, width: box.width, height: width });
            if (side === "Left") rects.push({ left: box.left, right: box.left + width, top: box.top, bottom: box.bottom, width, height: box.height });
            if (side === "Right") rects.push({ left: box.right - width, right: box.right, top: box.top, bottom: box.bottom, width, height: box.height });
          }
          return rects;
        };
        const intersects = (a, b) => a.left < b.right && a.right > b.left
          && a.top < b.bottom && a.bottom > b.top;
        const hiddenAttributeVisible = Array.from(document.querySelectorAll("[hidden]"))
          .filter(visible).length;
        const trusted = globalThis.__wowEvaluatorRead;
        let singleHanLastLineHeadingCount = 0;
        let cjkHeadingSplitWordCount = 0;
        let cjkHeadingExplicitNarrowCount = 0;
        let headingScanCount = 0;
        let headingScanTruncated = false;
        const displayHeadings = Array.from(document.querySelectorAll("h1,[role='heading'][aria-level='1']"));
        if (displayHeadings.length > 16) headingScanTruncated = true;
        for (let index = 0; index < displayHeadings.length && index < 16; index += 1) {
          const heading = displayHeadings[index];
          const text = trusted?.text(heading) || "";
          if (text.length > 512) {
            headingScanTruncated = true;
            continue;
          }
          const profile = trusted?.renderedLineProfile(heading);
          if (!profile) continue;
          headingScanCount += 1;
          cjkHeadingSplitWordCount += profile.splitHanWordCount;
          if (inspectCjkHeadingWidth && profile.lineCount >= 2 && profile.hanGraphemes > 0) {
            const headingBox = trusted?.rect(heading);
            const parentBox = heading.parentElement ? trusted?.rect(heading.parentElement) : null;
            if (headingBox?.width > 0 && parentBox?.width > 0
              && headingBox.width / parentBox.width < 0.8) {
              cjkHeadingExplicitNarrowCount += 1;
            }
          }
          if (profile.lineCount >= 2
            && profile.lastLineHanGraphemes === 1
            && profile.lastLineGraphemes === 1 + profile.lastLinePunctuationGraphemes) {
            singleHanLastLineHeadingCount += 1;
          }
        }
        const main = document.querySelector("main");
        let fixedContentObstructions = 0;
        if (main) {
          for (const fixed of Array.from(document.querySelectorAll("body *"))) {
            const style = getComputedStyle(fixed);
            if (style.position !== "fixed" || !visible(fixed)) continue;
            const numericZIndex = Number(style.zIndex);
            if (style.zIndex !== "auto" && Number.isFinite(numericZIndex) && numericZIndex < 0) continue;
            const viewportArea = innerWidth * innerHeight;
            const paintedElements = [fixed, ...Array.from(fixed.querySelectorAll("*")).filter(visible)];
            const paintedRects = paintedElements.flatMap(paintRects).filter((box) =>
              box.width * box.height >= viewportArea * 0.12
              || (box.width >= innerWidth * 0.7 && box.height >= 44));
            if (paintedRects.length === 0) continue;
            const contentRects = [];
            const walker = document.createTreeWalker(main, NodeFilter.SHOW_TEXT);
            for (let node = walker.nextNode(); node; node = walker.nextNode()) {
              if (fixed.contains(node.parentElement) || !visible(node.parentElement)
                || !(node.textContent || "").trim()) continue;
              const range = document.createRange();
              range.selectNodeContents(node);
              contentRects.push(...Array.from(range.getClientRects()));
            }
            for (const element of main.querySelectorAll("button,input,select,textarea,a,img,svg,canvas,video")) {
              if (!fixed.contains(element) && visible(element)) contentRects.push(element.getBoundingClientRect());
            }
            const coversMainContent = paintedRects.some((painted) => contentRects.some((content) => intersects(painted, content)));
            if (coversMainContent) fixedContentObstructions += 1;
          }
        }
        return {
          hidden_attribute_visible_count: hiddenAttributeVisible,
          fixed_content_obstruction_count: fixedContentObstructions,
          cjk_heading_explicit_narrow_count: cjkHeadingExplicitNarrowCount,
          cjk_heading_split_word_count: cjkHeadingSplitWordCount,
          heading_scan_count: headingScanCount,
          heading_scan_truncated: headingScanTruncated,
          single_han_last_line_heading_count: singleHanLastLineHeadingCount,
        };
      }, {
        inspectCjkHeadingWidth: headingExplicitNarrowRisk,
      });
      const matchingContract = browserContract?.cases.find((item) =>
        item.page === relativePage && item.profile === profile.name);
      const browserContractResult = matchingContract
        ? await runBrowserContract(page, matchingContract)
        : null;
      const inspection = {
        axe_violation_count: analysis.violations.length,
        axe_rule_ids: analysis.violations.map((violation) => violation.id).sort(),
        ...axeTargets,
        layout_hazards: {
          hidden_attribute_visible_count: layoutHazards.hidden_attribute_visible_count,
          fixed_content_obstruction_count: layoutHazards.fixed_content_obstruction_count,
          cjk_heading_explicit_narrow_count: layoutHazards.cjk_heading_explicit_narrow_count,
          cjk_heading_split_word_count: layoutHazards.cjk_heading_split_word_count,
        },
        typography_advisories: {
          heading_scan_count: layoutHazards.heading_scan_count,
          heading_scan_truncated: layoutHazards.heading_scan_truncated,
          single_han_last_line_heading_count: layoutHazards.single_han_last_line_heading_count,
        },
      };
      if (browserContractResult) inspection.browser_contract = browserContractResult;
      return inspection;
    },
  });
  for (const result of results) {
    const passed = result.navigation === "passed"
      && result.visible_main
      && result.visible_text
      && result.visible_primary_content
      && !result.root_horizontal_overflow
      && Object.values(result.counters).every((count) => count === 0)
      && result.inspection.axe_violation_count === 0
      && result.inspection.layout_hazards.hidden_attribute_visible_count === 0
      && result.inspection.layout_hazards.fixed_content_obstruction_count === 0
      && result.inspection.layout_hazards.cjk_heading_explicit_narrow_count === 0
      && result.inspection.layout_hazards.cjk_heading_split_word_count === 0
      && (!("browser_contract" in result.inspection) || result.inspection.browser_contract.status === "passed");
    result.status = passed ? "passed" : "rejected";
  }

  const status = results.every((result) => result.status === "passed") ? "passed" : "rejected";
  const receipt = {
    schema_version: 2,
    status,
    tool: {
      package: "playwright",
      version: require("playwright/package.json").version,
      browser: "chromium",
      browser_version: browserVersion,
    },
    settle_ms: 300,
    profiles: profiles.map(({ name, viewport, reducedMotion }) => ({ name, viewport, reduced_motion: reducedMotion })),
    source_layout_risks: sourceLayoutRisks,
    results,
  };
  if (browserContract) {
    receipt.browser_contract = {
      schema_version: browserContract.schema_version,
      case_count: browserContract.cases.length,
      case_ids: browserContract.cases.map((item) => item.id).sort(),
    };
  }
  process.stdout.write(`${JSON.stringify(receipt)}\n`);
}

main().catch((error) => fail(error && error.name ? error.name : "unknown"));
