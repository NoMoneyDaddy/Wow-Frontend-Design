#!/usr/bin/env node
/**
 * Optional Pretext typography preflight.
 * It never installs dependencies and degrades to an explicit unavailable result.
 */

const PACKAGE_NAME = "@chenglou/pretext";

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
  const maxWidth = Number(input.maxWidth);
  const lineHeight = Number(input.lineHeight);
  if (text === null || font === null || !Number.isFinite(maxWidth) || maxWidth <= 0 || !Number.isFinite(lineHeight) || lineHeight <= 0) {
    return { status: "invalid", reason: "text, font, maxWidth, and lineHeight are required" };
  }
  const capability = await loadPretext();
  if (capability.status !== "available") return capability;
  const options = {};
  if (input.whiteSpace === "pre-wrap") options.whiteSpace = "pre-wrap";
  if (input.wordBreak === "keep-all") options.wordBreak = "keep-all";
  if (Number.isFinite(Number(input.letterSpacing))) options.letterSpacing = Number(input.letterSpacing);
  const prepared = capability.module.prepare(text, font, options);
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
  };
}
