#!/usr/bin/env node
/**
 * Optional Pretext typography preflight.
 * It never installs dependencies and degrades to an explicit unavailable result.
 */

import { readFileSync, realpathSync } from "node:fs";
import { createRequire } from "node:module";
import { isAbsolute, join, relative, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const PACKAGE_NAME = "@chenglou/pretext";
const SUPPORTED_PACKAGE_VERSION = "0.0.8";
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
    if ((property === "overflowWrap" || input[property] !== undefined) && !values.has(input[property])) {
      unsupported.push({ property, value: printableValue(input[property]) });
    }
  }
  return unsupported;
}

function isWithin(root, target) {
  const candidate = relative(root, target);
  return candidate === "" || (!candidate.startsWith("..") && !isAbsolute(candidate));
}

function unavailable(reason, reasonCode, packageResolution) {
  return {
    status: "unavailable",
    package: PACKAGE_NAME,
    reason: String(reason).slice(0, 240),
    ...(reasonCode ? { reasonCode } : {}),
    ...(packageResolution ? { packageResolution } : {}),
  };
}

export async function loadPretext(options = {}) {
  try {
    if (options.projectRoot === undefined) {
      const module = await import(PACKAGE_NAME);
      return { status: "available", module, packageResolution: "adapter-ancestor" };
    }
    if (typeof options.projectRoot !== "string" || !isAbsolute(options.projectRoot)) {
      return unavailable(
        "projectRoot must be an absolute caller-authorized directory",
        "invalid_project_root",
        "project-local",
      );
    }
    const projectRoot = realpathSync(resolve(options.projectRoot));
    const packageManifest = realpathSync(
      join(projectRoot, "node_modules", "@chenglou", "pretext", "package.json"),
    );
    if (!isWithin(projectRoot, packageManifest)) {
      return unavailable(
        "project-local Pretext package resolves outside projectRoot",
        "package_outside_project",
        "project-local",
      );
    }
    const metadata = JSON.parse(readFileSync(packageManifest, "utf8"));
    if (metadata.version !== SUPPORTED_PACKAGE_VERSION) {
      return unavailable(
        `project-local Pretext version must equal ${SUPPORTED_PACKAGE_VERSION}`,
        "unsupported_package_version",
        "project-local",
      );
    }
    const requireFromProject = createRequire(pathToFileURL(join(projectRoot, "package.json")));
    const resolvedModule = realpathSync(requireFromProject.resolve(PACKAGE_NAME));
    if (!isWithin(projectRoot, resolvedModule)) {
      return unavailable(
        "resolved Pretext module is outside projectRoot",
        "package_outside_project",
        "project-local",
      );
    }
    const module = await import(pathToFileURL(resolvedModule).href);
    return { status: "available", module, packageResolution: "project-local" };
  } catch (error) {
    return unavailable(error?.message || error, "package_unavailable", options.projectRoot === undefined ? "adapter-ancestor" : "project-local");
  }
}

export async function measureTypographyCandidate(input, options = {}) {
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
  const capability = await loadPretext(options);
  if (capability.status !== "available") return capability;
  const pretextOptions = {};
  if (input.whiteSpace === "pre-wrap") pretextOptions.whiteSpace = "pre-wrap";
  if (input.wordBreak === "keep-all") pretextOptions.wordBreak = "keep-all";
  if (input.letterSpacing !== undefined) pretextOptions.letterSpacing = input.letterSpacing;
  try {
    const prepared = capability.module.prepareWithSegments(text, font, pretextOptions);
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
      packageResolution: capability.packageResolution,
      appliedOptions: {
        whiteSpace: input.whiteSpace ?? "normal",
        wordBreak: input.wordBreak ?? "normal",
        overflowWrap: "break-word",
        writingMode: "horizontal-tb",
        letterSpacing: pretextOptions.letterSpacing ?? 0,
      },
      limitations: [...LIMITATIONS],
      claimBoundary: CLAIM_BOUNDARY,
    };
  } catch (error) {
    return unavailable(error?.message || error, "measurement_unavailable", capability.packageResolution);
  }
}
