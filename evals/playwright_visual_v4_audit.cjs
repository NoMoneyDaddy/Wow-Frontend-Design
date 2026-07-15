#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { chromium } = require("playwright");

const CASE_PAGES = {
  "harbor-cold-chain-v4": ["index.html"],
  "island-sound-archive-v4": ["index.html"],
  "plant-swap-one-line-v4": ["index.html", "browse.html", "listing.html"],
};
const MOBILE_USER_AGENT = "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36";
const VIEWPORTS = [
  { name: "desktop", width: 1440, height: 1000, screenWidth: 1440, screenHeight: 1000, deviceScaleFactor: 1, isMobile: false, hasTouch: false, userAgent: null },
  { name: "mobile", width: 390, height: 844, screenWidth: 390, screenHeight: 844, deviceScaleFactor: 3, isMobile: true, hasTouch: true, userAgent: MOBILE_USER_AGENT },
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

function issueCodes(result) {
  const issues = [];
  if (result.lang.toLowerCase() !== "zh-hant") issues.push("document_lang_not_zh_hant");
  if (!result.hasMain) issues.push("main_landmark_missing");
  if (result.visibleMainCount > 1) issues.push("multiple_visible_main_landmarks");
  if (!result.hasHeading) issues.push("primary_heading_missing");
  if (result.horizontalOverflow) issues.push("page_horizontal_overflow");
  if (result.shortActionFailures.length) issues.push("short_action_label_wrapped_or_clipped");
  if (result.clippedText.length) issues.push("visible_text_clipped");
  if (result.criticalTextCollisions.length) issues.push("critical_text_collision");
  if (result.closedNavigationLeaks.length) issues.push("closed_mobile_navigation_exposed");
  if (result.fixedStickyObstructions.length) issues.push("fixed_or_sticky_content_obstruction");
  if (result.consoleErrors.length) issues.push("console_errors");
  if (result.externalRequests.length) issues.push("external_requests_attempted");
  if (result.badResponses.length) issues.push("http_error_responses");
  if (result.caseId !== "plant-swap-one-line-v4") {
    if (result.visibleRecordCount < 8) issues.push("fewer_than_eight_visible_records");
    if (result.hiddenRecordCopies) issues.push("hidden_responsive_record_copies");
    if (result.duplicateRecordIds.length) issues.push("duplicate_record_ids");
    if (result.semanticStyleDrift.length) issues.push("semantic_color_role_drift");
    if (result.viewport === "mobile" && result.firstRecordDisplay === "table-row") {
      issues.push("mobile_keeps_desktop_table_row");
    }
  }
  if (result.caseId === "island-sound-archive-v4" && result.page === "index.html") {
    if (!result.verticalType.passed) issues.push("vertical_type_contract_failed");
    if (result.verticalTextCollisions.length) issues.push("vertical_type_text_collision");
  }
  return unique(issues);
}

async function auditPage(browser, options, target, pageName, viewport) {
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
  const measured = await page.evaluate(({ caseId, viewportName }) => {
    const visible = (node) => {
      const style = getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" && Number(style.opacity) > 0.01
        && rect.width > 0.5 && rect.height > 0.5;
    };
    const viewportIntersection = (rect) => {
      const left = Math.max(0, rect.left);
      const top = Math.max(0, rect.top);
      const right = Math.min(innerWidth, rect.right);
      const bottom = Math.min(innerHeight, rect.bottom);
      return {
        left: Math.round(left),
        top: Math.round(top),
        width: Math.max(0, Math.round(right - left)),
        height: Math.max(0, Math.round(bottom - top)),
      };
    };
    const visibleInViewport = (node) => {
      if (!visible(node)) return false;
      const intersection = viewportIntersection(node.getBoundingClientRect());
      return intersection.width > 2 && intersection.height > 2;
    };
    const textLineCount = (node) => {
      const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
      const tops = [];
      while (walker.nextNode()) {
        if (!walker.currentNode.textContent.trim()) continue;
        const range = document.createRange();
        range.selectNodeContents(walker.currentNode);
        for (const rect of range.getClientRects()) {
          if (rect.width > 0 && rect.height > 0) tops.push(Math.round(rect.top));
        }
      }
      return new Set(tops).size;
    };
    const signature = (node, properties) => {
      if (!node) return null;
      const style = getComputedStyle(node);
      return properties.map((property) => style[property]).join("|");
    };

    const actionNodes = [...document.querySelectorAll("button, a, [role='button'], input[type='button'], input[type='submit']")]
      .filter(visible);
    const shortActionFailures = actionNodes.map((node) => {
      const text = (node.innerText || node.value || node.getAttribute("aria-label") || "").trim().replace(/\s+/g, " ");
      const clipped = node.scrollWidth > node.clientWidth + 1 || node.scrollHeight > node.clientHeight + 1;
      return { tag: node.tagName.toLowerCase(), text, lineCount: textLineCount(node), clipped };
    }).filter((item) => item.text && [...item.text].length <= 12 && (item.lineCount > 1 || item.clipped));

    const textNodes = [...document.querySelectorAll("h1, h2, h3, p, li, label, button, a, [data-eval]")]
      .filter(visible);
    const clippedText = textNodes.map((node) => {
      const style = getComputedStyle(node);
      const clipped = node.scrollWidth > node.clientWidth + 1 || node.scrollHeight > node.clientHeight + 1;
      const clipsOverflow = [style.overflow, style.overflowX, style.overflowY].some((value) => ["hidden", "clip"].includes(value));
      return {
        tag: node.tagName.toLowerCase(),
        hook: node.getAttribute("data-eval"),
        text: (node.textContent || "").trim().replace(/\s+/g, " ").slice(0, 80),
        overflow: `${style.overflow}/${style.overflowX}/${style.overflowY}`,
        clipped: clipped && clipsOverflow,
      };
    }).filter((item) => item.text && item.clipped).slice(0, 30);

    const criticalNodes = [...document.querySelectorAll('h1, h2, h3, button, [role="button"], [data-eval="global-action"], [data-eval="mobile-nav-toggle"], header a')]
      .filter(visible)
      .filter((node) => node.textContent.trim());
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
        if (overlapWidth <= 2 || overlapHeight <= 2) continue;
        criticalTextCollisions.push({
          left: left.textContent.trim().slice(0, 80),
          right: right.textContent.trim().slice(0, 80),
          overlap: `${Math.round(overlapWidth)}x${Math.round(overlapHeight)}`,
        });
        if (criticalTextCollisions.length >= 25) break;
      }
      if (criticalTextCollisions.length >= 25) break;
    }

    const mobileNavToggle = document.querySelector('[data-eval="mobile-nav-toggle"]');
    const controlledId = mobileNavToggle?.getAttribute("aria-controls") || "";
    const controlledNav = (controlledId && document.getElementById(controlledId))
      || document.querySelector('[data-eval="global-nav"]');
    const closedNavigationLeaks = [];
    if (viewportName === "mobile" && mobileNavToggle && visibleInViewport(mobileNavToggle)
      && mobileNavToggle.getAttribute("aria-expanded") === "false"
      && controlledNav && visibleInViewport(controlledNav)) {
      const rect = controlledNav.getBoundingClientRect();
      closedNavigationLeaks.push({
        toggleText: (mobileNavToggle.textContent || "").trim().replace(/\s+/g, " ").slice(0, 80),
        controlledId: controlledNav.id || null,
        navHook: controlledNav.getAttribute("data-eval"),
        rect: {
          left: Math.round(rect.left),
          top: Math.round(rect.top),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
        },
        viewportIntersection: viewportIntersection(rect),
      });
    }

    const obstructionTargets = [...document.querySelectorAll(
      "main h1, main h2, main h3, main p, main button, main a, main input, main select, main textarea, main [data-eval='record']",
    )].filter(visibleInViewport);
    const fixedStickyObstructions = [];
    const positionedCandidates = [...document.body.querySelectorAll("*")].filter((node) => {
      const style = getComputedStyle(node);
      return ["fixed", "sticky"].includes(style.position) && visibleInViewport(node)
        && style.pointerEvents !== "none";
    });
    for (const obstruction of positionedCandidates) {
      const obstructionRect = obstruction.getBoundingClientRect();
      const overlaps = [];
      for (const targetNode of obstructionTargets) {
        if (obstruction.contains(targetNode) || targetNode.contains(obstruction)) continue;
        const targetRect = targetNode.getBoundingClientRect();
        const left = Math.max(obstructionRect.left, targetRect.left, 0);
        const top = Math.max(obstructionRect.top, targetRect.top, 0);
        const right = Math.min(obstructionRect.right, targetRect.right, innerWidth);
        const bottom = Math.min(obstructionRect.bottom, targetRect.bottom, innerHeight);
        const overlapWidth = right - left;
        const overlapHeight = bottom - top;
        if (overlapWidth <= 4 || overlapHeight <= 4) continue;
        const sample = document.elementFromPoint((left + right) / 2, (top + bottom) / 2);
        if (!sample || (sample !== obstruction && !obstruction.contains(sample))) continue;
        overlaps.push({
          tag: targetNode.tagName.toLowerCase(),
          hook: targetNode.getAttribute("data-eval"),
          text: (targetNode.textContent || "").trim().replace(/\s+/g, " ").slice(0, 80),
          overlap: `${Math.round(overlapWidth)}x${Math.round(overlapHeight)}`,
        });
        if (overlaps.length >= 20) break;
      }
      if (!overlaps.length) continue;
      fixedStickyObstructions.push({
        tag: obstruction.tagName.toLowerCase(),
        hook: obstruction.getAttribute("data-eval"),
        position: getComputedStyle(obstruction).position,
        text: (obstruction.textContent || "").trim().replace(/\s+/g, " ").slice(0, 80),
        overlaps,
      });
      if (fixedStickyObstructions.length >= 20) break;
    }

    const outsideViewport = [...document.body.querySelectorAll("*")].filter(visible).map((node) => {
      const rect = node.getBoundingClientRect();
      return {
        tag: node.tagName.toLowerCase(),
        className: typeof node.className === "string" ? node.className.slice(0, 80) : "",
        left: Math.round(rect.left),
        right: Math.round(rect.right),
        width: Math.round(rect.width),
      };
    }).filter((item) => item.left < -2 || item.right > innerWidth + 2).slice(0, 30);

    const records = [...document.querySelectorAll('[data-eval="record"]')];
    const visibleRecords = records.filter(visible);
    const recordIds = records.map((node) => (node.getAttribute("data-record-id") || "").trim()).filter(Boolean);
    const duplicateRecordIds = recordIds.filter((value, index) => recordIds.indexOf(value) !== index);
    const semanticGroups = new Map();
    for (const node of document.querySelectorAll('[data-eval="record-priority"], [data-eval="record-status"], [data-eval="record-due"]')) {
      const key = `${node.getAttribute("data-eval")}::${node.textContent.trim()}`;
      const style = getComputedStyle(node);
      const value = [style.color, style.backgroundColor, style.borderColor, style.fontWeight].join("|");
      if (!semanticGroups.has(key)) semanticGroups.set(key, new Set());
      semanticGroups.get(key).add(value);
    }
    const semanticStyleDrift = [...semanticGroups.entries()]
      .filter(([, values]) => values.size > 1)
      .map(([key, values]) => ({ key, signatures: [...values] }));

    const verticalNode = document.querySelector('[data-eval="vertical-type"]');
    const verticalType = verticalNode && visible(verticalNode) ? (() => {
      const style = getComputedStyle(verticalNode);
      const clipped = verticalNode.scrollWidth > verticalNode.clientWidth + 1 || verticalNode.scrollHeight > verticalNode.clientHeight + 1;
      const expectedMode = viewportName === "desktop" ? /^vertical-/.test(style.writingMode) : style.writingMode === "horizontal-tb";
      return {
        present: true,
        writingMode: style.writingMode,
        transform: style.transform,
        clipped,
        passed: expectedMode && style.transform === "none" && !clipped,
      };
    })() : { present: false, writingMode: null, transform: null, clipped: null, passed: false };
    const verticalTextCollisions = verticalNode && visible(verticalNode)
      ? [...document.querySelectorAll("h1, h2, h3, p")].filter((node) => {
        if (!visible(node) || node === verticalNode || node.contains(verticalNode) || verticalNode.contains(node)) return false;
        const verticalRect = verticalNode.getBoundingClientRect();
        const candidateRect = node.getBoundingClientRect();
        const overlapWidth = Math.min(verticalRect.right, candidateRect.right) - Math.max(verticalRect.left, candidateRect.left);
        const overlapHeight = Math.min(verticalRect.bottom, candidateRect.bottom) - Math.max(verticalRect.top, candidateRect.top);
        return overlapWidth > 2 && overlapHeight > 2;
      }).map((node) => ({
        tag: node.tagName.toLowerCase(),
        text: (node.textContent || "").trim().replace(/\s+/g, " ").slice(0, 80),
      })).slice(0, 20)
      : [];

    const rootStyle = getComputedStyle(document.documentElement);
    const rootVariables = {};
    for (let index = 0; index < rootStyle.length; index += 1) {
      const name = rootStyle[index];
      if (name.startsWith("--")) rootVariables[name] = rootStyle.getPropertyValue(name).trim();
    }
    const header = document.querySelector("header") || document.querySelector('[data-eval="global-nav"]')?.parentElement;
    const nav = document.querySelector('[data-eval="global-nav"]') || document.querySelector("nav");
    const globalAction = document.querySelector('[data-eval="global-action"]');

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
      closedNavigationLeaks,
      fixedStickyObstructions,
      outsideViewport,
      recordCount: records.length,
      visibleRecordCount: visibleRecords.length,
      hiddenRecordCopies: Math.max(0, records.length - visibleRecords.length),
      duplicateRecordIds: [...new Set(duplicateRecordIds)],
      firstRecordDisplay: visibleRecords[0] ? getComputedStyle(visibleRecords[0]).display : null,
      semanticStyleDrift,
      verticalType,
      verticalTextCollisions,
      rootVariables,
      shellSignature: {
        body: signature(document.body, ["color", "backgroundColor", "fontFamily", "fontSize"]),
        header: signature(header, ["color", "backgroundColor", "borderBottomColor", "fontFamily"]),
        nav: signature(nav, ["color", "backgroundColor", "fontFamily", "fontWeight"]),
        action: signature(globalAction, ["color", "backgroundColor", "borderColor", "borderRadius", "fontFamily"]),
      },
      structuredCase: caseId !== "plant-swap-one-line-v4",
    };
  }, { caseId: target.caseId, viewportName: viewport.name });

  const pageSlug = pageName.replace(/\.html$/i, "");
  const screenshot = path.join(options.artifactDir, `${target.caseId}-${target.alias}-${pageSlug}-${viewport.name}.png`);
  if (fs.existsSync(screenshot)) throw new Error(`refusing to overwrite screenshot: ${screenshot}`);
  await page.screenshot({ path: screenshot, fullPage: false, animations: "disabled", caret: "hide" });
  const screenshotSha256 = crypto.createHash("sha256").update(fs.readFileSync(screenshot)).digest("hex");

  const result = {
    caseId: target.caseId,
    alias: target.alias,
    page: pageName,
    url: targetUrl,
    viewport: viewport.name,
    size: `${viewport.width}x${viewport.height}`,
    screenshot,
    screenshotSha256,
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
  const sharedNames = Object.keys(pages[0].rootVariables)
    .filter((name) => pages.every((page) => Object.hasOwn(page.rootVariables, name)));
  return sharedNames.filter((name) => new Set(pages.map((page) => page.rootVariables[name])).size > 1);
}

function compareMultiPageShell(results, target) {
  const comparisons = [];
  for (const viewport of VIEWPORTS) {
    const pages = results.filter((result) => result.caseId === target.caseId && result.alias === target.alias && result.viewport === viewport.name);
    const driftedSharedTokens = sharedRootTokenDrift(pages);
    const shellMaps = pages.map((result) => JSON.stringify(result.shellSignature));
    const issues = [];
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
          report.results.push(await auditPage(browser, options, target, pageName, viewport));
        }
      }
      if (target.caseId === "plant-swap-one-line-v4") {
        report.crossPageComparisons.push(...compareMultiPageShell(report.results, target));
      }
    }
  } finally {
    await browser.close();
  }

  const byTarget = {};
  for (const target of options.targets) {
    const key = `${target.caseId}:${target.alias}`;
    const viewIssues = report.results
      .filter((result) => result.caseId === target.caseId && result.alias === target.alias)
      .flatMap((result) => result.visualIssues);
    const crossIssues = report.crossPageComparisons
      .filter((result) => result.caseId === target.caseId && result.alias === target.alias)
      .flatMap((result) => result.visualIssues);
    byTarget[key] = unique([...viewIssues, ...crossIssues]);
  }
  report.summary = {
    checkedPages: report.results.length,
    targetsWithObservedIssues: Object.values(byTarget).filter((issues) => issues.length).length,
    issuesByTarget: byTarget,
    verdict: Object.values(byTarget).some((issues) => issues.length) ? "observed_issues" : "no_observed_issues",
  };
  fs.mkdirSync(path.dirname(options.output), { recursive: true });
  fs.writeFileSync(options.output, `${JSON.stringify(report, null, 2)}\n`, { encoding: "utf8", flag: "wx" });
}

module.exports = { compareMultiPageShell, sharedRootTokenDrift, VIEWPORTS };

if (require.main === module) {
  main().catch((error) => {
    console.error(error.stack || error.message || String(error));
    process.exitCode = 1;
  });
}
