#!/usr/bin/env node
/**
 * Optional Pretext typography preflight.
 * It never installs dependencies and degrades to an explicit unavailable result.
 */

const PACKAGE_NAME = "@chenglou/pretext";
const CLAIM_BOUNDARY = "diagnostic preflight only; rendered layout remains unverified";
const LIMITATIONS = [
  "horizontal-text-only",
  "overflow-wrap-break-word-only",
  "not-rendered-layout-evidence",
];

function finiteNumericInput(value) {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function printableValue(value) {
  if (typeof value === "string") return value.slice(0, 80);
  if (value === undefined) return "undefined";
  try {
    return JSON.stringify(value).slice(0, 80);
  } catch {
    return String(value).slice(0, 80);
  }
}

function unsupportedTextBehavior(input) {
  const unsupported = [];
  const allowed = {
    whiteSpace: new Set(["normal", "pre-wrap"]),
    wordBreak: new Set(["normal", "keep-all"]),
    overflowWrap: new Set(["break-word"]),
    writingMode: new Set(["horizontal-tb"]),
  };
  for (const [property, values] of Object.entries(allowed)) {
    if (input[property] !== undefined && !values.has(input[property])) {
      unsupported.push({ property, value: printableValue(input[property]) });
    }
  }
  return unsupported;
}

export async function loadPretext() {
  try {
    const module = await import(PACKAGE_NAME);
    return { status: "available", module };
  } catch (error) {
    return {
      status: "unavailable",
      package: PACKAGE_NAME,
      reason: String(error?.message || error).slice(0, 240),
    };
  }
}

export async function measureTypographyCandidate(input) {
  if (!input || typeof input !== "object") {
    return { status: "invalid", reason: "input must be an object" };
  }
  const text = typeof input.text === "string" ? input.text : null;
  const font = typeof input.font === "string" ? input.font : null;
  const maxWidth = finiteNumericInput(input.maxWidth);
  const lineHeight = finiteNumericInput(input.lineHeight);
  if (text === null || font === null || font.trim() === "" || maxWidth === null || maxWidth <= 0 || lineHeight === null || lineHeight <= 0) {
    return { status: "invalid", reason: "text, font, maxWidth, and lineHeight are required" };
  }
  if (input.letterSpacing !== undefined && (typeof input.letterSpacing !== "number" || !Number.isFinite(input.letterSpacing))) {
    return { status: "invalid", reason: "letterSpacing must be a finite pixel value" };
  }
  const unsupported = unsupportedTextBehavior(input);
  if (unsupported.length > 0) {
    return {
      status: "invalid",
      reason: "CSS text behavior is not supported by the pinned Pretext adapter",
      reasonCode: "unsupported_css_text_behavior",
      unsupported,
      claimBoundary: CLAIM_BOUNDARY,
    };
  }
  const capability = await loadPretext();
  if (capability.status !== "available") return capability;
  const options = {};
  if (input.whiteSpace === "pre-wrap") options.whiteSpace = "pre-wrap";
  if (input.wordBreak === "keep-all") options.wordBreak = "keep-all";
  if (input.letterSpacing !== undefined) options.letterSpacing = input.letterSpacing;
  try {
    const prepared = capability.module.prepareWithSegments(text, font, options);
    const stats = capability.module.measureLineStats(prepared, maxWidth);
    const layout = capability.module.layout(prepared, maxWidth, lineHeight);
    return {
      status: "measured",
      lineCount: layout.lineCount,
      height: layout.height,
      maxLineWidth: stats.maxLineWidth,
      measuredLineCount: stats.lineCount,
      maxWidth,
      lineHeight,
      textLength: [...text].length,
      appliedOptions: {
        whiteSpace: input.whiteSpace ?? "normal",
        wordBreak: input.wordBreak ?? "normal",
        overflowWrap: "break-word",
        writingMode: "horizontal-tb",
        letterSpacing: options.letterSpacing ?? 0,
      },
      limitations: [...LIMITATIONS],
      claimBoundary: CLAIM_BOUNDARY,
    };
  } catch (error) {
    return {
      status: "unavailable",
      package: PACKAGE_NAME,
      reason: String(error?.message || error).slice(0, 240),
    };
  }
}
