#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { chromium } = require("playwright");

const CASE_PAGES = {
  "wind-maintenance-dispatch-v6": ["index.html"],
  "type-foundry-specimen-v6": ["index.html"],
  "repair-cafe-intake-v6": ["index.html"],
  "night-market-allergen-v6": ["index.html"],
  "royalty-statement-v6": ["index.html"],
  "packaging-configurator-v6": ["index.html", "materials.html", "summary.html"],
  "oral-history-archive-v6": ["index.html", "archive.html", "story.html"],
  "grant-review-board-v6": ["index.html"],
};
const MOBILE_USER_AGENT = "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36";
const TABLET_USER_AGENT = "Mozilla/5.0 (Linux; Android 14; Pixel Tablet) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36";
const VIEWPORTS = [
  { name: "desktop", width: 1440, height: 1000, screenWidth: 1440, screenHeight: 1000, deviceScaleFactor: 1, isMobile: false, hasTouch: false, userAgent: null },
  { name: "tablet", width: 834, height: 1112, screenWidth: 834, screenHeight: 1112, deviceScaleFactor: 2, isMobile: true, hasTouch: true, userAgent: TABLET_USER_AGENT },
  { name: "mobile", width: 390, height: 844, screenWidth: 390, screenHeight: 844, deviceScaleFactor: 3, isMobile: true, hasTouch: true, userAgent: MOBILE_USER_AGENT },
  { name: "compact-mobile", width: 360, height: 800, screenWidth: 360, screenHeight: 800, deviceScaleFactor: 3, isMobile: true, hasTouch: true, userAgent: MOBILE_USER_AGENT },
];

function parseArguments(argv) {
  const options = { output: null, artifactDir: null, targets: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--output" || value === "--artifact-dir") {
      const key = value === "--output" ? "output" : "artifactDir";
      options[key] = argv[++index] || null;
      if (!options[key]) throw new Error(`${value} requires a path`);
      continue;
    }
    if (value === "--target") {
      const specification = argv[++index] || "";
      const separator = specification.indexOf("=");
      const identity = specification.slice(0, separator);
      const split = identity.indexOf(":");
      if (separator < 1 || split < 1) throw new Error("--target requires <case-id>:<label>=<localhost-url>");
      const caseId = identity.slice(0, split);
      const alias = identity.slice(split + 1);
      if (!CASE_PAGES[caseId] || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(alias)) {
        throw new Error(`invalid target identity: ${identity}`);
      }
      const parsed = new URL(specification.slice(separator + 1));
      if (parsed.protocol !== "http:" || !["127.0.0.1", "localhost", "[::1]"].includes(parsed.hostname)) {
        throw new Error(`target ${identity} must use HTTP on localhost`);
      }
      if (parsed.username || parsed.password || parsed.search || parsed.hash || !parsed.pathname.endsWith("/")) {
        throw new Error(`target ${identity} must be an uncredentialed directory URL`);
      }
      options.targets.push({ caseId, alias, url: parsed.href });
      continue;
    }
    throw new Error(`unknown argument: ${value}`);
  }
  if (!options.output || !options.artifactDir || !options.targets.length) {
    throw new Error("--output, --artifact-dir, and at least one --target are required");
  }
  if (fs.existsSync(options.output)) throw new Error(`refusing to overwrite report: ${options.output}`);
  const artifactStat = fs.lstatSync(options.artifactDir);
  if (!artifactStat.isDirectory() || artifactStat.isSymbolicLink()) throw new Error("artifact directory must be real");
  const identities = options.targets.map(({ caseId, alias }) => `${caseId}:${alias}`);
  if (new Set(identities).size !== identities.length) throw new Error("target identities must be unique");
  return options;
}

function unique(values) {
  return [...new Set(values)];
}

async function visibleCount(page, selector) {
  return page.locator(selector).evaluateAll((nodes) => nodes.filter((node) => {
    const style = getComputedStyle(node);
    const rect = node.getBoundingClientRect();
    return style.display !== "none" && style.visibility !== "hidden" && Number(style.opacity) > 0.01
      && rect.width > 0.5 && rect.height > 0.5;
  }).length);
}

async function firstVisible(page, selector) {
  const candidates = page.locator(selector);
  const count = await candidates.count();
  for (let index = 0; index < count; index += 1) {
    const candidate = candidates.nth(index);
    if (await candidate.isVisible()) return candidate;
  }
  throw new Error(`no visible element matched ${selector}`);
}

function grantInteractionPlan(viewportName) {
  const usesCaseNavigation = viewportName === "mobile" || viewportName === "compact-mobile";
  return {
    usesCaseNavigation,
    expectedVisibleRecords: usesCaseNavigation ? 1 : 6,
  };
}

async function runCaseInteraction(page, caseId, viewport) {
  const evidence = { attempted: true, failures: [] };
  try {
    if (caseId === "wind-maintenance-dispatch-v6") {
      evidence.initialRecords = await visibleCount(page, '[data-eval="dispatch-row"]');
      await page.locator('button[data-filter-value="urgent"]').click();
      await page.waitForTimeout(100);
      evidence.filteredRecords = await visibleCount(page, '[data-eval="dispatch-row"]');
      await (await firstVisible(page, '[data-eval="open-dispatch"]')).click();
      await page.locator('[data-eval="reassign-action"]').click();
      await page.waitForTimeout(100);
      evidence.statusVisible = await page.locator('[data-eval="status-message"]').isVisible();
      if (evidence.initialRecords !== 8 || evidence.filteredRecords !== 3) {
        evidence.failures.push("wind_filter_count_failed");
      }
      if (!evidence.statusVisible) evidence.failures.push("wind_reassignment_feedback_missing");
    } else if (caseId === "type-foundry-specimen-v6") {
      const toggle = page.locator('[data-eval="writing-toggle"]');
      evidence.initialWritingMode = await page.locator('[data-eval="specimen"]').evaluate((node) => getComputedStyle(node).writingMode);
      await toggle.click();
      await page.waitForTimeout(100);
      evidence.finalWritingMode = await page.locator('[data-eval="specimen"]').evaluate((node) => getComputedStyle(node).writingMode);
      evidence.togglePressed = await toggle.getAttribute("aria-pressed");
      if (evidence.initialWritingMode === evidence.finalWritingMode || evidence.togglePressed !== "true") {
        evidence.failures.push("type_writing_mode_toggle_failed");
      }
    } else if (caseId === "repair-cafe-intake-v6") {
      await (await firstVisible(page, '[data-eval="continue-action"]')).click();
      await page.waitForTimeout(100);
      evidence.errorVisible = await page.locator('[data-eval="form-error"]').isVisible();
      await page.locator('[data-eval="item-name"]').fill("二十年以上的手提收音機，旋鈕鬆脫且偶爾沒有聲音");
      await (await firstVisible(page, '[data-eval="continue-action"]')).click();
      await page.waitForTimeout(100);
      evidence.step = await (await firstVisible(page, '[data-eval="booking-step"]')).getAttribute("data-step");
      if (!evidence.errorVisible || !["2", "3"].includes(evidence.step)) evidence.failures.push("repair_intake_validation_or_transition_failed");
    } else if (caseId === "night-market-allergen-v6") {
      evidence.initialRecords = await visibleCount(page, '[data-eval="stall-record"]');
      await page.locator('button[data-filter-value="peanut-free"]').click();
      await page.waitForTimeout(100);
      evidence.filteredRecords = await visibleCount(page, '[data-eval="stall-record"]');
      await (await firstVisible(page, '[data-eval="open-stall"]')).click();
      evidence.detailVisible = await visibleCount(page, '[data-eval="stall-detail"]') > 0;
      if (evidence.initialRecords !== 8 || evidence.filteredRecords !== 4) evidence.failures.push("allergen_filter_count_failed");
      if (!evidence.detailVisible) evidence.failures.push("allergen_detail_failed");
    } else if (caseId === "royalty-statement-v6") {
      const before = await page.locator('[data-eval="royalty-workspace"]').getAttribute("data-period");
      await page.locator('[data-period-value="previous"]').click();
      await (await firstVisible(page, '[data-eval="chart-mark"]')).click();
      await page.waitForTimeout(100);
      evidence.afterPeriod = await page.locator('[data-eval="royalty-workspace"]').getAttribute("data-period");
      evidence.tooltipVisible = await page.locator('[data-eval="chart-tooltip"]').isVisible();
      if (before === evidence.afterPeriod) evidence.failures.push("royalty_period_switch_failed");
      if (!evidence.tooltipVisible) evidence.failures.push("royalty_tooltip_failed");
    } else if (caseId === "packaging-configurator-v6") {
      const option = await firstVisible(page, '[data-eval="size-option"]:has(input[value="s"])');
      if (!(await option.isEnabled())) throw new Error("S size option is disabled");
      await option.click();
      evidence.summaryVisible = await page.locator('[data-eval="config-summary"]').isVisible();
      if (!evidence.summaryVisible) evidence.failures.push("packaging_summary_failed");
    } else if (caseId === "oral-history-archive-v6") {
      evidence.shellVisible = await page.locator('[data-eval="archive-shell"]').isVisible();
      if (!evidence.shellVisible) evidence.failures.push("oral_history_shell_missing");
    } else if (caseId === "grant-review-board-v6") {
      const plan = grantInteractionPlan(viewport.name);
      evidence.initialRecords = await visibleCount(page, '[data-eval="proposal-row"]');
      const rows = page.locator('[data-eval="proposal-row"]');
      const rowCount = await rows.count();
      if (rowCount < 2) throw new Error("grant comparison requires at least two proposals");
      const firstRow = rows.nth(0);
      const secondRow = rows.nth(1);
      await firstRow.locator('[data-eval="shortlist-action"]').click();
      await firstRow.locator('[data-action="compare"][data-slot="a"]').click();
      if (plan.usesCaseNavigation) {
        await page.locator('#nextCase').click();
        await page.waitForTimeout(100);
      }
      await secondRow.locator('[data-eval="shortlist-action"]').click();
      await secondRow.locator('[data-action="compare"][data-slot="b"]').click();
      await page.locator('[data-eval="decision-action"]').click();
      await page.waitForTimeout(100);
      evidence.modalVisible = await page.locator('[data-eval="decision-modal"]').isVisible();
      evidence.backgroundInert = await page.locator('[data-eval="grant-board"]').evaluate((node) => {
        const inertAncestor = node.closest("[inert]");
        return Boolean(inertAncestor) || node.closest('[aria-hidden="true"]') !== null;
      });
      if (evidence.initialRecords !== plan.expectedVisibleRecords || !evidence.modalVisible) evidence.failures.push("grant_decision_flow_failed");
      if (!evidence.backgroundInert) evidence.failures.push("grant_modal_background_not_inert");
    }
  } catch (error) {
    evidence.failures.push(`interaction_exception:${String(error.message || error).slice(0, 160)}`);
  }
  return evidence;
}

function issueCodes(result) {
  const issues = [...result.contractIssues, ...result.interaction.failures];
  const normalizedLang = result.lang.toLowerCase();
  const langMatches = /^zh-hant(?:-|$)/.test(normalizedLang);
  if (!langMatches) issues.push("document_lang_not_zh_hant");
  if (!result.hasMain) issues.push("main_landmark_missing");
  if (result.visibleMainCount !== 1) issues.push("visible_main_landmark_count_invalid");
  if (!result.hasHeading) issues.push("primary_heading_missing");
  if (result.horizontalOverflow || result.outsideViewport.length) issues.push("page_horizontal_overflow");
  if (result.shortActionFailures.length) issues.push("short_action_label_wrapped_or_clipped");
  if (result.clippedText.length) issues.push("visible_text_clipped");
  if (result.criticalTextCollisions.length) issues.push("critical_text_collision");
  if (result.fixedStickyObstructions.length) issues.push("fixed_or_sticky_content_obstruction");
  if (result.viewport !== "desktop" && result.smallTouchTargets.length) issues.push("touch_target_below_24px");
  if (result.readingRhythm.tooTight.length) issues.push("paragraph_line_height_too_tight");
  if (result.readingRhythm.tooWide.length) issues.push("paragraph_measure_too_wide");
  if ((result.narrowTextColumns || []).length) issues.push("content_column_too_narrow");
  if ((result.bodyFlow?.forcedLineBreaks || []).length) issues.push("forced_body_line_break");
  if ((result.bodyFlow?.nonWrappingProse || []).length) issues.push("body_copy_normal_wrap_disabled");
  if (result.reducedMotionAnimations.length) issues.push("reduced_motion_animation_active");
  if (result.consoleErrors.length) issues.push("console_errors");
  if (result.externalRequests.length) issues.push("external_requests_attempted");
  if (result.badResponses.length) issues.push("http_error_responses");
  return unique(issues);
}

async function auditPage(browser, options, target, pageName, viewport, state = "base") {
  const contextOptions = {
    viewport: { width: viewport.width, height: viewport.height },
    screen: { width: viewport.screenWidth, height: viewport.screenHeight },
    deviceScaleFactor: viewport.deviceScaleFactor,
    isMobile: viewport.isMobile,
    hasTouch: viewport.hasTouch,
    locale: "zh-TW",
    reducedMotion: "reduce",
  };
  if (viewport.userAgent) contextOptions.userAgent = viewport.userAgent;
  const context = await browser.newContext(contextOptions);
  const page = await context.newPage();
  const targetUrl = new URL(pageName, target.url).href;
  const origin = new URL(target.url).origin;
  const consoleErrors = [];
  const externalRequests = [];
  const badResponses = [];

  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("response", (response) => {
    if (response.status() >= 400 && !response.url().endsWith("/favicon.ico")) {
      badResponses.push({ status: response.status(), url: response.url() });
    }
  });
  await page.route("**/*", async (route) => {
    const requestUrl = new URL(route.request().url());
    if (["data:", "blob:"].includes(requestUrl.protocol)) return route.continue();
    if (requestUrl.origin !== origin) {
      externalRequests.push(route.request().url());
      return route.abort("blockedbyclient");
    }
    if (requestUrl.pathname.endsWith("/favicon.ico")) return route.fulfill({ status: 204, body: "" });
    return route.continue();
  });

  await page.goto(targetUrl, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(250);
  const interaction = state === "interaction"
    ? await runCaseInteraction(page, target.caseId, viewport)
    : { attempted: false, failures: [] };

  const measured = await page.evaluate(({ caseId, viewportName, requiredPages }) => {
    const visible = (node) => {
      const style = getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      const clippedAssistiveText = style.position === "absolute"
        && rect.width <= 2 && rect.height <= 2
        && ([style.overflow, style.overflowX, style.overflowY].some((value) => ["hidden", "clip"].includes(value))
          || style.clipPath !== "none" || style.clip !== "auto");
      return style.display !== "none" && style.visibility !== "hidden" && Number(style.opacity) > 0.01
        && rect.width > 0.5 && rect.height > 0.5 && !clippedAssistiveText;
    };
    const visibleInViewport = (node) => {
      if (!visible(node)) return false;
      const rect = node.getBoundingClientRect();
      return rect.right > 2 && rect.bottom > 2 && rect.left < innerWidth - 2 && rect.top < innerHeight - 2;
    };
    const textLineCount = (node) => {
      const range = document.createRange();
      range.selectNodeContents(node);
      return new Set([...range.getClientRects()].filter((rect) => rect.width > 0 && rect.height > 0).map((rect) => Math.round(rect.top))).size;
    };
    const signature = (node, properties) => {
      if (!node) return null;
      const style = getComputedStyle(node);
      return properties.map((property) => style[property]).join("|");
    };
    const nameFor = (node) => {
      const labelledBy = node.getAttribute("aria-labelledby");
      return (node.getAttribute("aria-label")
        || (labelledBy && document.getElementById(labelledBy)?.textContent)
        || node.textContent || "").trim().replace(/\s+/g, " ");
    };
    const duplicateValues = (nodes, attribute) => {
      const values = nodes.map((node) => (node.getAttribute(attribute) || "").trim()).filter(Boolean);
      return uniqueInPage(values.filter((value, index) => values.indexOf(value) !== index));
    };
    const uniqueInPage = (values) => [...new Set(values)];

    const actionNodes = [...document.querySelectorAll("button, [role='button'], input[type='button'], input[type='submit']")].filter(visible);
    const shortActionFailures = actionNodes.map((node) => {
      const text = (node.innerText || node.value || node.getAttribute("aria-label") || "").trim().replace(/\s+/g, " ");
      const clipped = node.scrollWidth > node.clientWidth + 1 || node.scrollHeight > node.clientHeight + 1;
      return { text, lineCount: textLineCount(node), clipped };
    }).filter((item) => item.text && [...item.text].length <= 12 && (item.lineCount > 1 || item.clipped));

    const textNodes = [...document.querySelectorAll("h1, h2, h3, p, li, label, button, a, td, th, [data-eval]")].filter(visible);
    const clippedText = textNodes.map((node) => {
      const style = getComputedStyle(node);
      const clipped = node.scrollWidth > node.clientWidth + 1 || node.scrollHeight > node.clientHeight + 1;
      const clipsOverflow = [style.overflow, style.overflowX, style.overflowY].some((value) => ["hidden", "clip"].includes(value));
      return { tag: node.tagName.toLowerCase(), hook: node.getAttribute("data-eval"), text: (node.textContent || "").trim().replace(/\s+/g, " ").slice(0, 80), clipped: clipped && clipsOverflow };
    }).filter((item) => item.text && item.clipped).slice(0, 30);

    const criticalNodes = [...document.querySelectorAll("h1, h2, h3, button, [role='button']")].filter(visibleInViewport).filter((node) => node.textContent.trim());
    const criticalTextCollisions = [];
    for (let leftIndex = 0; leftIndex < criticalNodes.length; leftIndex += 1) {
      for (let rightIndex = leftIndex + 1; rightIndex < criticalNodes.length; rightIndex += 1) {
        const left = criticalNodes[leftIndex];
        const right = criticalNodes[rightIndex];
        if (left.contains(right) || right.contains(left)) continue;
        const a = left.getBoundingClientRect();
        const b = right.getBoundingClientRect();
        const overlapWidth = Math.min(a.right, b.right) - Math.max(a.left, b.left);
        const overlapHeight = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        if (overlapWidth > 2 && overlapHeight > 2) {
          criticalTextCollisions.push({ left: left.textContent.trim().slice(0, 60), right: right.textContent.trim().slice(0, 60), overlap: `${Math.round(overlapWidth)}x${Math.round(overlapHeight)}` });
        }
        if (criticalTextCollisions.length >= 20) break;
      }
      if (criticalTextCollisions.length >= 20) break;
    }

    const obstructionTargets = [...document.querySelectorAll("main h1, main h2, main h3, main p, main button, main input, main select, main [data-eval]")].filter(visibleInViewport);
    const fixedStickyObstructions = [];
    for (const obstruction of [...document.body.querySelectorAll("*")].filter((node) => {
      const style = getComputedStyle(node);
      const intentionalModal = node.matches('dialog[open], [role="dialog"][aria-modal="true"]')
        || node.closest('dialog[open], [role="dialog"][aria-modal="true"]');
      return !intentionalModal && ["fixed", "sticky"].includes(style.position)
        && visibleInViewport(node) && style.pointerEvents !== "none";
    })) {
      const obstructionRect = obstruction.getBoundingClientRect();
      const overlaps = obstructionTargets.filter((targetNode) => {
        if (obstruction.contains(targetNode) || targetNode.contains(obstruction)) return false;
        const rect = targetNode.getBoundingClientRect();
        const left = Math.max(obstructionRect.left, rect.left, 0);
        const top = Math.max(obstructionRect.top, rect.top, 0);
        const right = Math.min(obstructionRect.right, rect.right, innerWidth);
        const bottom = Math.min(obstructionRect.bottom, rect.bottom, innerHeight);
        if (right - left <= 4 || bottom - top <= 4) return false;
        const sample = document.elementFromPoint((left + right) / 2, (top + bottom) / 2);
        return sample === obstruction || obstruction.contains(sample);
      }).slice(0, 10).map((node) => ({ hook: node.getAttribute("data-eval"), text: node.textContent.trim().replace(/\s+/g, " ").slice(0, 60) }));
      if (overlaps.length) fixedStickyObstructions.push({ hook: obstruction.getAttribute("data-eval"), position: getComputedStyle(obstruction).position, overlaps });
      if (fixedStickyObstructions.length >= 10) break;
    }

    const outsideViewport = [...document.body.querySelectorAll("*")].filter(visible).map((node) => {
      const rect = node.getBoundingClientRect();
      return { tag: node.tagName.toLowerCase(), hook: node.getAttribute("data-eval"), left: Math.round(rect.left), right: Math.round(rect.right), width: Math.round(rect.width) };
    }).filter((item) => item.left < -2 || item.right > innerWidth + 2).slice(0, 30);

    const smallTouchTargets = viewportName === "desktop" ? [] : actionNodes.map((node) => {
      const rect = node.getBoundingClientRect();
      return { text: nameFor(node).slice(0, 60), width: Math.round(rect.width), height: Math.round(rect.height) };
    }).filter((item) => item.width < 24 || item.height < 24).slice(0, 30);

    const readableNodes = [...document.querySelectorAll("main p, main li")]
      .filter(visible)
      .filter((node) => node.tagName !== "LI" || !node.querySelector("p, div, section, article, ul, ol"))
      .filter((node) => node.textContent.trim().length >= 40);
    const readingRhythm = { tooTight: [], tooWide: [] };
    for (const node of readableNodes) {
      const style = getComputedStyle(node);
      const fontSize = Number.parseFloat(style.fontSize);
      const lineHeight = style.lineHeight === "normal" ? fontSize * 1.2 : Number.parseFloat(style.lineHeight);
      const ratio = lineHeight / fontSize;
      const rect = node.getBoundingClientRect();
      const text = node.textContent.trim().replace(/\s+/g, " ");
      const characters = [...text];
      const hanCount = characters.filter((character) => /\p{Script=Han}/u.test(character)).length;
      const cjkDominant = hanCount / Math.max(characters.length, 1) >= 0.35;
      const weightedFullWidthLength = characters.reduce((total, character) => {
        if (/\p{Script=Han}/u.test(character)) return total + 1;
        if (/\s/u.test(character)) return total + 0.33;
        return total + 0.55;
      }, 0);
      const capacity = cjkDominant ? rect.width / fontSize : rect.width / (fontSize * 0.55);
      const estimatedCharacters = Math.min(cjkDominant ? weightedFullWidthLength : characters.length, capacity);
      const measureLimit = cjkDominant ? 40 : 90;
      if (Number.isFinite(ratio) && ratio < 1.35) readingRhythm.tooTight.push({ text: node.textContent.trim().slice(0, 60), ratio: Number(ratio.toFixed(2)) });
      if (estimatedCharacters > measureLimit) readingRhythm.tooWide.push({
        text: node.textContent.trim().slice(0, 60),
        script: cjkDominant ? "cjk" : "latin",
        estimatedCharacters: Math.round(estimatedCharacters),
        limit: measureLimit,
      });
    }
    readingRhythm.tooTight = readingRhythm.tooTight.slice(0, 20);
    readingRhythm.tooWide = readingRhythm.tooWide.slice(0, 20);

    const narrowTextColumns = [...document.querySelectorAll("main p, main li")]
      .filter(visible)
      .map((node) => {
        const style = getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        const text = node.textContent.trim().replace(/\s+/g, " ");
        const fontSize = Number.parseFloat(style.fontSize);
        return {
          tag: node.tagName.toLowerCase(),
          text: text.slice(0, 60),
          writingMode: style.writingMode,
          widthInEms: Number((rect.width / fontSize).toFixed(2)),
          characterCount: [...text].length,
        };
      })
      .filter((item) => item.writingMode.startsWith("horizontal") && item.characterCount >= 12 && item.widthInEms < 6)
      .slice(0, 20);

    const bodyFlowNodes = [...document.querySelectorAll("main p, main li")]
      .filter(visible)
      .filter((node) => node.tagName !== "LI" || !node.querySelector("p, div, section, article, ul, ol"))
      .filter((node) => node.textContent.trim().length >= 40);
    const forcedLineBreaks = bodyFlowNodes
      .filter((node) => node.querySelector("br") && !node.closest("blockquote, [data-display-copy], [data-intentional-break='true']"))
      .map((node) => ({
        tag: node.tagName.toLowerCase(),
        text: node.textContent.trim().replace(/\s+/g, " ").slice(0, 80),
        breakCount: node.querySelectorAll("br").length,
      }))
      .slice(0, 20);
    const nonWrappingProse = bodyFlowNodes
      .map((node) => {
        const style = getComputedStyle(node);
        const text = node.textContent.trim().replace(/\s+/g, " ");
        const characters = [...text];
        const hanCount = characters.filter((character) => /\p{Script=Han}/u.test(character)).length;
        const cjkDominant = hanCount / Math.max(characters.length, 1) >= 0.35;
        return {
          tag: node.tagName.toLowerCase(),
          text: text.slice(0, 80),
          whiteSpace: style.whiteSpace,
          wordBreak: style.wordBreak,
          cjkDominant,
        };
      })
      .filter((item) => ["nowrap", "pre"].includes(item.whiteSpace) || (item.cjkDominant && item.wordBreak === "keep-all"))
      .slice(0, 20);
    const bodyFlow = { forcedLineBreaks, nonWrappingProse };

    const reducedMotionAnimations = [...document.body.querySelectorAll("*")].filter(visible).map((node) => {
      const style = getComputedStyle(node);
      const durations = style.animationDuration.split(",").map((value) => Number.parseFloat(value) || 0);
      return { tag: node.tagName.toLowerCase(), name: style.animationName, duration: Math.max(...durations) };
    }).filter((item) => item.name !== "none" && item.duration > 0.01).slice(0, 20);

    const rootStyle = getComputedStyle(document.documentElement);
    const rootVariables = {};
    for (let index = 0; index < rootStyle.length; index += 1) {
      const name = rootStyle[index];
      if (name.startsWith("--")) rootVariables[name] = rootStyle.getPropertyValue(name).trim();
    }
    const header = document.querySelector("header");
    const nav = document.querySelector("nav");
    const contractIssues = [];

    const currentPage = location.pathname.split("/").pop() || "index.html";
    if (caseId === "wind-maintenance-dispatch-v6") {
      const records = [...document.querySelectorAll('[data-eval="dispatch-row"]')];
      if (!document.querySelector('[data-eval="dispatch-workspace"]')) contractIssues.push("wind_workspace_missing");
      if (records.length !== 8 || duplicateValues(records, "data-record-id").length) contractIssues.push("wind_record_inventory_invalid");
      for (const hook of ["open-dispatch", "reassign-action", "status-message"]) {
        if (!document.querySelector(`[data-eval="${hook}"]`)) contractIssues.push(`wind_${hook}_missing`);
      }
    } else if (caseId === "type-foundry-specimen-v6") {
      for (const hook of ["specimen-workspace", "writing-toggle", "specimen", "fallback-note", "outline-toggle"]) {
        if (!document.querySelector(`[data-eval="${hook}"]`)) contractIssues.push(`type_${hook}_missing`);
      }
    } else if (caseId === "repair-cafe-intake-v6") {
      for (const hook of ["intake-form", "item-name", "continue-action", "form-error", "booking-step", "edit-action", "confirmation-summary"]) {
        if (!document.querySelector(`[data-eval="${hook}"]`)) contractIssues.push(`repair_${hook}_missing`);
      }
    } else if (caseId === "night-market-allergen-v6") {
      const records = [...document.querySelectorAll('[data-eval="stall-record"]')];
      if (!document.querySelector('[data-eval="allergen-guide"]')) contractIssues.push("allergen_guide_missing");
      if (records.length !== 8 || duplicateValues(records, "data-record-id").length) contractIssues.push("allergen_record_inventory_invalid");
      for (const hook of ["stall-search", "open-stall", "stall-detail", "offline-note"]) {
        if (!document.querySelector(`[data-eval="${hook}"]`)) contractIssues.push(`allergen_${hook}_missing`);
      }
    } else if (caseId === "royalty-statement-v6") {
      const records = [...document.querySelectorAll('[data-eval="royalty-row"]')];
      const marks = [...document.querySelectorAll('[data-eval="chart-mark"]')];
      if (!document.querySelector('[data-eval="royalty-workspace"]')) contractIssues.push("royalty_workspace_missing");
      if (records.length !== 6 || duplicateValues(records, "data-record-id").length) contractIssues.push("royalty_record_inventory_invalid");
      if (marks.length < 6 || marks.some((mark) => !nameFor(mark))) contractIssues.push("royalty_chart_mark_accessibility_failed");
      for (const hook of ["royalty-chart", "anomaly", "chart-tooltip"]) {
        if (!document.querySelector(`[data-eval="${hook}"]`)) contractIssues.push(`royalty_${hook}_missing`);
      }
    } else if (caseId === "packaging-configurator-v6") {
      const linkedPages = [...document.querySelectorAll("a[href]")].map((node) => {
        try { return new URL(node.getAttribute("href"), location.href).pathname.split("/").pop() || "index.html"; } catch { return ""; }
      });
      const missing = requiredPages.filter((required) => !linkedPages.includes(required));
      if (missing.length || !document.querySelector('[data-eval="configurator-shell"]')) contractIssues.push("packaging_cross_page_contract_failed");
      const hooks = currentPage === "index.html" ? ["size-option", "use-option", "config-summary"]
        : currentPage === "materials.html" ? ["material-option", "conflict-message"]
          : ["price-summary", "reset-action"];
      for (const hook of hooks) if (!document.querySelector(`[data-eval="${hook}"]`)) contractIssues.push(`packaging_${hook}_missing`);
    } else if (caseId === "oral-history-archive-v6") {
      const linkedPages = [...document.querySelectorAll("a[href]")].map((node) => {
        try { return new URL(node.getAttribute("href"), location.href).pathname.split("/").pop() || "index.html"; } catch { return ""; }
      });
      if (requiredPages.some((required) => !linkedPages.includes(required)) || !document.querySelector('[data-eval="archive-shell"]')) contractIssues.push("oral_history_cross_page_contract_failed");
      if (currentPage === "archive.html" && document.querySelectorAll('[data-eval="story-record"]').length < 6) contractIssues.push("oral_history_story_inventory_invalid");
      if (currentPage === "story.html") {
        if (document.querySelectorAll("main p").length < 5) contractIssues.push("oral_history_longform_too_short");
        for (const hook of ["footnote", "media-fallback"]) if (!document.querySelector(`[data-eval="${hook}"]`)) contractIssues.push(`oral_history_${hook}_missing`);
      }
    } else if (caseId === "grant-review-board-v6") {
      const records = [...document.querySelectorAll('[data-eval="proposal-row"]')];
      if (!document.querySelector('[data-eval="grant-board"]')) contractIssues.push("grant_board_missing");
      if (records.length !== 6 || duplicateValues(records, "data-record-id").length) contractIssues.push("grant_record_inventory_invalid");
      for (const hook of ["shortlist-action", "compare-panel", "decision-action", "decision-modal", "retry-action"]) {
        if (!document.querySelector(`[data-eval="${hook}"]`)) contractIssues.push(`grant_${hook}_missing`);
      }
    }

    return {
      lang: document.documentElement.lang || "",
      title: document.title,
      hasMain: Boolean(document.querySelector("main")),
      visibleMainCount: [...document.querySelectorAll("main")].filter(visible).length,
      hasHeading: Boolean(document.querySelector("h1")),
      horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
      shortActionFailures,
      clippedText,
      criticalTextCollisions,
      fixedStickyObstructions,
      outsideViewport,
      smallTouchTargets,
      readingRhythm,
      narrowTextColumns,
      bodyFlow,
      reducedMotionAnimations,
      contractIssues,
      rootVariables,
      shellSignature: {
        typography: signature(document.body, ["fontFamily", "fontSize"]),
        header: signature(header, ["color", "backgroundColor", "borderBottomColor", "fontFamily"]),
        nav: signature(nav, ["color", "backgroundColor", "fontFamily", "fontWeight"]),
      },
    };
  }, { caseId: target.caseId, viewportName: viewport.name, requiredPages: CASE_PAGES[target.caseId] });

  const pageSlug = pageName.replace(/\.html$/i, "");
  const screenshot = path.join(options.artifactDir, `${target.caseId}-${target.alias}-${pageSlug}-${state}-${viewport.name}.png`);
  if (fs.existsSync(screenshot)) throw new Error(`refusing to overwrite screenshot: ${screenshot}`);
  await page.screenshot({ path: screenshot, fullPage: false, animations: "disabled", caret: "hide" });
  const screenshotSha256 = crypto.createHash("sha256").update(fs.readFileSync(screenshot)).digest("hex");

  const result = {
    caseId: target.caseId,
    alias: target.alias,
    page: pageName,
    state,
    url: targetUrl,
    viewport: viewport.name,
    size: `${viewport.width}x${viewport.height}`,
    screenshot,
    screenshotSha256,
    interaction,
    ...measured,
    consoleErrors: unique(consoleErrors),
    externalRequests: unique(externalRequests),
    badResponses,
  };
  result.visualIssues = issueCodes(result);
  await context.close();
  return result;
}

function sharedRootTokenDrift(pages) {
  if (!pages.length) return [];
  const sharedNames = Object.keys(pages[0].rootVariables).filter((name) => pages.every((page) => Object.hasOwn(page.rootVariables, name)));
  return sharedNames.filter((name) => new Set(pages.map((page) => page.rootVariables[name])).size > 1);
}

function compareMultiPageShell(results, target) {
  const comparisons = [];
  for (const viewport of VIEWPORTS) {
    const pages = results.filter((result) => result.caseId === target.caseId && result.alias === target.alias && result.viewport === viewport.name && result.state === "base");
    const driftedSharedTokens = sharedRootTokenDrift(pages);
    const shellMaps = pages.map((result) => JSON.stringify(result.shellSignature));
    const issues = [];
    if (pages.length !== CASE_PAGES[target.caseId].length) issues.push("cross_page_inventory_incomplete");
    if (driftedSharedTokens.length) issues.push("cross_page_design_token_drift");
    if (new Set(shellMaps).size > 1) issues.push("cross_page_shell_style_drift");
    comparisons.push({
      caseId: target.caseId,
      alias: target.alias,
      viewport: viewport.name,
      pages: pages.map((result) => result.page),
      driftedSharedTokens,
      visualIssues: issues,
    });
  }
  return comparisons;
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  const launchOptions = { headless: true };
  if (process.env.CHROME_EXECUTABLE_PATH) launchOptions.executablePath = process.env.CHROME_EXECUTABLE_PATH;
  const browser = await chromium.launch(launchOptions);
  const report = {
    schema_version: 1,
    generated_at: new Date().toISOString(),
    evaluator: `Playwright ${require("playwright/package.json").version}`,
    auditor: {
      path: path.relative(process.cwd(), __filename),
      sha256: crypto.createHash("sha256").update(fs.readFileSync(__filename)).digest("hex"),
    },
    browser: await browser.version(),
    viewports: VIEWPORTS,
    targets: options.targets,
    results: [],
    crossPageComparisons: [],
  };
  try {
    for (const target of options.targets) {
      for (const pageName of CASE_PAGES[target.caseId]) {
        for (const viewport of VIEWPORTS) {
          report.results.push(await auditPage(browser, options, target, pageName, viewport, "base"));
        }
      }
      for (const viewport of VIEWPORTS.filter(({ name }) => ["desktop", "mobile"].includes(name))) {
        report.results.push(await auditPage(browser, options, target, CASE_PAGES[target.caseId][0], viewport, "interaction"));
      }
      if (CASE_PAGES[target.caseId].length > 1) {
        report.crossPageComparisons.push(...compareMultiPageShell(report.results, target));
      }
    }
  } finally {
    await browser.close();
  }

  const byTarget = {};
  for (const target of options.targets) {
    const key = `${target.caseId}:${target.alias}`;
    const viewIssues = report.results.filter((result) => result.caseId === target.caseId && result.alias === target.alias).flatMap((result) => result.visualIssues);
    const crossIssues = report.crossPageComparisons.filter((result) => result.caseId === target.caseId && result.alias === target.alias).flatMap((result) => result.visualIssues);
    byTarget[key] = unique([...viewIssues, ...crossIssues]);
  }
  report.summary = {
    checkedPages: report.results.length,
    minimumExpectedScreenshots: 60,
    targetsWithObservedIssues: Object.values(byTarget).filter((issues) => issues.length).length,
    issuesByTarget: byTarget,
    verdict: Object.values(byTarget).some((issues) => issues.length) ? "observed_issues" : "no_observed_issues",
  };
  fs.mkdirSync(path.dirname(options.output), { recursive: true });
  fs.writeFileSync(options.output, `${JSON.stringify(report, null, 2)}\n`, { encoding: "utf8", flag: "wx" });
}

module.exports = { CASE_PAGES, VIEWPORTS, compareMultiPageShell, grantInteractionPlan, issueCodes, parseArguments, sharedRootTokenDrift };

if (require.main === module) {
  main().catch((error) => {
    console.error(error.stack || error.message || String(error));
    process.exitCode = 1;
  });
}
