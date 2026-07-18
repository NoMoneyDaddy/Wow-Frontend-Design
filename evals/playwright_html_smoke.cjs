#!/usr/bin/env node
"use strict";

const { AxeBuilder } = require("@axe-core/playwright");
const { runLocalPageMatrix } = require("./playwright_browser_runtime.cjs");

const VIEWPORTS = [
  { name: "desktop", viewport: { width: 1440, height: 1000 }, reducedMotion: "no-preference" },
  { name: "mobile", viewport: { width: 390, height: 844 }, reducedMotion: "reduce" },
];

function fail(message) {
  process.stderr.write(`html smoke infrastructure failure: ${message}\n`);
  process.exitCode = 2;
}

async function main() {
  if (process.argv.length !== 5) {
    fail("expected stage, JSON page list and JSON output list");
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
  const { browserVersion, results } = await runLocalPageMatrix({
    stage,
    pages,
    allowedFiles,
    profiles: VIEWPORTS,
    inspectPage: async (page) => {
      const analysis = await new AxeBuilder({ page }).analyze();
      const layoutHazards = await page.evaluate(() => {
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
              || (box.width >= innerWidth * 0.7 && box.height >= 96));
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
        };
      });
      return {
        axe_violation_count: analysis.violations.length,
        axe_rule_ids: analysis.violations.map((violation) => violation.id).sort(),
        layout_hazards: layoutHazards,
      };
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
      && result.inspection.layout_hazards.fixed_content_obstruction_count === 0;
    result.status = passed ? "passed" : "rejected";
  }

  const status = results.every((result) => result.status === "passed") ? "passed" : "rejected";
  process.stdout.write(`${JSON.stringify({
    schema_version: 1,
    status,
    tool: {
      package: "playwright",
      version: require("playwright/package.json").version,
      browser: "chromium",
      browser_version: browserVersion,
    },
    settle_ms: 300,
    profiles: VIEWPORTS.map(({ name, viewport, reducedMotion }) => ({ name, viewport, reduced_motion: reducedMotion })),
    results,
  })}\n`);
}

main().catch((error) => fail(error && error.name ? error.name : "unknown"));
