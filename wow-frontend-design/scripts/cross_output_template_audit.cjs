#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

const MAX_INPUT_BYTES = 1024 * 1024;
const CLAIM_BOUNDARY = "exact or categorical dominant rendered macro-template and low-resolution visual-grammar candidates only; product specificity, originality and design quality remain unverified";

function fail(message) {
  throw new Error(message);
}

function quantize(value, extent) {
  if (!Number.isFinite(value) || !Number.isFinite(extent) || extent <= 0) return null;
  return Number((Math.round((value / extent) * 20) / 20).toFixed(2));
}

function collectMacroFingerprint() {
  const visible = (node) => {
    if (typeof node.checkVisibility === "function" && !node.checkVisibility({
      opacityProperty: true,
      visibilityProperty: true,
      contentVisibilityAuto: true,
    })) return false;
    const rect = node.getBoundingClientRect();
    return rect.width > 1 && rect.height > 1;
  };
  const q = (value, extent) => {
    if (!Number.isFinite(value) || !Number.isFinite(extent) || extent <= 0) return null;
    return Number((Math.round((value / extent) * 20) / 20).toFixed(2));
  };
  const roleFor = (node) => {
    const explicit = node.getAttribute("role");
    if (["banner", "navigation", "main", "complementary", "contentinfo", "dialog"].includes(explicit)) return explicit;
    return ({ HEADER: "banner", NAV: "navigation", MAIN: "main", ASIDE: "complementary", FOOTER: "contentinfo", DIALOG: "dialog" })[node.tagName]
      || (["FORM", "TABLE", "UL", "OL", "FIGURE", "SECTION", "ARTICLE"].includes(node.tagName) ? node.tagName.toLowerCase() : "region");
  };
  const representationFor = (node) => {
    const hasVisible = (selector) => (node.matches(selector) && visible(node))
      || [...node.querySelectorAll(selector)].some(visible);
    if (hasVisible("form")) return "form";
    if (hasVisible("table")) return "table";
    if (hasVisible("ul, ol")) return "list";
    if (hasVisible("figure, img, video, canvas, svg")) return "media";
    return "region";
  };
  const radiusBucket = (node) => {
    const radius = effectiveRadius(node);
    if (!Number.isFinite(radius) || radius <= 1) return "none";
    if (radius <= 8) return "small";
    if (radius <= 16) return "medium";
    return "large";
  };
  const familyCategory = (value) => {
    const family = String(value || "").toLowerCase();
    if (family.includes("黑體")) return "sans";
    if (family.includes("明體") || family.includes("宋體")) return "serif";
    if (/\b(monospace|mono|courier|consolas|menlo)\b/u.test(family)) return "mono";
    if (/\b(sans|system-ui|arial|helvetica|avenir|segoe|jhenghei|pingfang)\b/u.test(family)) return "sans";
    if (/\b(serif|ming|song|georgia|baskerville|palatino|iowan)\b/u.test(family)) return "serif";
    return "other";
  };
  const densityBucket = (count) => (count === 0 ? "none" : count <= 3 ? "sparse" : "many");
  function effectiveRadii(node) {
    const rect = node.getBoundingClientRect();
    const raw = String(getComputedStyle(node).borderTopLeftRadius || "0").trim().split(/\s+/u);
    const toPixels = (token, extent) => token.endsWith("%")
      ? Number.parseFloat(token) * extent / 100 : Number.parseFloat(token);
    return { horizontal: toPixels(raw[0], rect.width), vertical: toPixels(raw[1] || raw[0], rect.height) };
  }
  function effectiveRadius(node) {
    const radius = effectiveRadii(node);
    return Math.min(radius.horizontal, radius.vertical);
  }
  const mode = (values) => {
    const counts = new Map();
    for (const value of values) counts.set(value, (counts.get(value) || 0) + 1);
    return [...counts.entries()].sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))[0]?.[0] || "none";
  };
  const rectSignature = (rect, owner) => [
    q(rect.left - owner.left, owner.width),
    q(rect.top - owner.top, Math.max(owner.height, innerHeight)),
    q(rect.width, owner.width),
    q(rect.height, Math.max(owner.height, innerHeight)),
  ];
  const viewport = { left: 0, top: 0, width: innerWidth, height: innerHeight };
  const landmarkSelector = "header, nav, main, aside, footer, dialog[open], [role='banner'], [role='navigation'], [role='main'], [role='complementary'], [role='contentinfo'], [role='dialog'][aria-modal='true']";
  const landmarkNodes = [...new Set(document.querySelectorAll(landmarkSelector))].filter(visible);
  const landmarks = landmarkNodes.map((node) => ({
    role: roleFor(node),
    depth: landmarkNodes.filter((other) => other !== node && other.contains(node)).length,
    box: rectSignature(node.getBoundingClientRect(), viewport),
  }));
  const main = [...document.querySelectorAll("main, [role='main']")].find(visible) || document.body;
  const mainRect = main.getBoundingClientRect();
  const mainStyle = getComputedStyle(main);
  const tracks = String(mainStyle.gridTemplateColumns || "none").match(/[+-]?(?:\d+\.?\d*|\.\d+)px/gu) || [];
  const regions = [...main.children].filter(visible).map((node) => {
    const style = getComputedStyle(node);
    return {
      role: roleFor(node),
      representation: representationFor(node),
      box: rectSignature(node.getBoundingClientRect(), mainRect),
      display: style.display,
      radius: radiusBucket(node),
    };
  });
  const representationHistogram = ["form", "table", "ul", "ol", "figure", "img", "video", "canvas", "svg"]
    .map((selector) => [selector, [...main.querySelectorAll(selector)].filter(visible).length]);
  const display = [...document.querySelectorAll("h1, [data-display-type]")].find(visible);
  const displayStyle = display ? getComputedStyle(display) : null;
  const displayRatio = displayStyle ? Number.parseFloat(displayStyle.fontSize) / innerWidth : 0;
  const displayScale = !displayStyle ? "none" : displayRatio < 0.03 ? "compact" : displayRatio < 0.075 ? "display" : "oversized";
  const candidates = [...main.querySelectorAll("section, article, aside, form, main > *")].filter((node) => {
    if (!visible(node)) return false;
    const rect = node.getBoundingClientRect();
    return rect.width >= Math.min(320, innerWidth * 0.5) && rect.height >= 80;
  });
  const pills = [...document.querySelectorAll("button, a, [role='button'], [role='status'], [class*='pill'], [class*='chip'], [class~='tag'], [class*='badge']")]
    .filter((node) => {
      if (!visible(node)) return false;
      const rect = node.getBoundingClientRect();
      const radius = effectiveRadii(node);
      return rect.height > 0 && rect.height <= 64 && rect.width >= rect.height * 1.25
        && radius.horizontal >= rect.height * 0.45 && radius.vertical >= rect.height * 0.45;
    });
  return {
    version: 2,
    landmarks,
    mainFlow: {
      display: mainStyle.display,
      flexDirection: mainStyle.flexDirection,
      gridTracks: tracks.map((value) => q(Number.parseFloat(value), mainRect.width)),
      gap: q(Number.parseFloat(mainStyle.gap), mainRect.width),
    },
    regions,
    representationHistogram,
    visualGrammar: {
      displayFamily: displayStyle ? familyCategory(displayStyle.fontFamily) : "none",
      displayScale,
      majorRadius: mode(candidates.map(radiusBucket)),
      pillDensity: densityBucket(pills.length),
    },
  };
}

function boundedToken(value, label) {
  if (typeof value !== "string" || value.length < 1 || value.length > 80 || value.trim() !== value) fail(`${label} is invalid`);
  return value;
}

function boundedEnum(value, allowed, label) {
  const token = boundedToken(value, label);
  if (!allowed.includes(token)) fail(`${label} is invalid`);
  return token;
}

function requireExactKeys(value, expected, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)
    || Object.keys(value).sort().join("|") !== [...expected].sort().join("|")) fail(`${label} fields are invalid`);
}

function boundedNumber(value, label) {
  if (value === null) return null;
  if (typeof value !== "number" || !Number.isFinite(value) || Math.abs(value) > 100) fail(`${label} is invalid`);
  return value;
}

function projectFingerprint(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) fail("macroFingerprint is invalid");
  const baseKeys = ["version", "landmarks", "mainFlow", "regions", "representationHistogram"];
  if (value.version === 1) requireExactKeys(value, baseKeys, "macroFingerprint");
  else if (value.version === 2) requireExactKeys(value, [...baseKeys, "visualGrammar"], "macroFingerprint");
  else fail("macroFingerprint is invalid");
  if (!Array.isArray(value.landmarks) || value.landmarks.length > 50
    || !Array.isArray(value.regions) || value.regions.length > 100
    || !Array.isArray(value.representationHistogram) || value.representationHistogram.length > 30
    || !value.mainFlow || typeof value.mainFlow !== "object" || Array.isArray(value.mainFlow)) fail("macroFingerprint shape is invalid");
  const box = (items, label) => {
    if (!Array.isArray(items) || items.length !== 4) fail(`${label} is invalid`);
    return items.map((item, index) => boundedNumber(item, `${label}[${index}]`));
  };
  const landmarks = value.landmarks.map((item, index) => {
    requireExactKeys(item, ["role", "depth", "box"], `landmarks[${index}]`);
    if (!Number.isSafeInteger(item.depth) || item.depth < 0 || item.depth > 20) fail(`landmarks[${index}].depth is invalid`);
    return { role: boundedToken(item.role, `landmarks[${index}].role`), depth: item.depth, box: box(item.box, `landmarks[${index}].box`) };
  });
  requireExactKeys(value.mainFlow, ["display", "flexDirection", "gridTracks", "gap"], "mainFlow");
  const gridTracks = value.mainFlow.gridTracks;
  if (!Array.isArray(gridTracks) || gridTracks.length > 20) fail("mainFlow.gridTracks is invalid");
  const mainFlow = {
    display: boundedToken(value.mainFlow.display, "mainFlow.display"),
    flexDirection: boundedToken(value.mainFlow.flexDirection, "mainFlow.flexDirection"),
    gridTracks: gridTracks.map((item, index) => boundedNumber(item, `mainFlow.gridTracks[${index}]`)),
    gap: boundedNumber(value.mainFlow.gap, "mainFlow.gap"),
  };
  const regions = value.regions.map((item, index) => {
    requireExactKeys(item, ["role", "representation", "box", "display", "radius"], `regions[${index}]`);
    return {
      role: boundedToken(item.role, `regions[${index}].role`),
      representation: boundedToken(item.representation, `regions[${index}].representation`),
      box: box(item.box, `regions[${index}].box`),
      display: boundedToken(item.display, `regions[${index}].display`),
      radius: boundedToken(item.radius, `regions[${index}].radius`),
    };
  });
  const representationHistogram = value.representationHistogram.map((item, index) => {
    if (!Array.isArray(item) || item.length !== 2 || !Number.isSafeInteger(item[1]) || item[1] < 0 || item[1] > 10000) {
      fail(`representationHistogram[${index}] is invalid`);
    }
    return [boundedToken(item[0], `representationHistogram[${index}][0]`), item[1]];
  });
  const projected = { version: value.version, landmarks, mainFlow, regions, representationHistogram };
  if (value.version === 2) {
    requireExactKeys(value.visualGrammar, ["displayFamily", "displayScale", "majorRadius", "pillDensity"], "visualGrammar");
    projected.visualGrammar = {
      displayFamily: boundedEnum(value.visualGrammar.displayFamily, ["none", "serif", "sans", "mono", "other"], "visualGrammar.displayFamily"),
      displayScale: boundedEnum(value.visualGrammar.displayScale, ["none", "compact", "display", "oversized"], "visualGrammar.displayScale"),
      majorRadius: boundedEnum(value.visualGrammar.majorRadius, ["none", "small", "medium", "large"], "visualGrammar.majorRadius"),
      pillDensity: boundedEnum(value.visualGrammar.pillDensity, ["none", "sparse", "many"], "visualGrammar.pillDensity"),
    };
  }
  return projected;
}

function dominantFingerprint(value) {
  const projected = projectFingerprint(value);
  const tracks = projected.mainFlow.gridTracks;
  const trackTotal = tracks.every((item) => typeof item === "number" && item > 0)
    ? tracks.reduce((total, item) => total + item, 0) : 0;
  const dominantShare = trackTotal > 0 ? Math.max(...tracks) / trackTotal : null;
  const trackBalance = tracks.length === 0 ? "none"
    : tracks.length === 1 ? "single"
      : dominantShare === null ? "unknown"
        : dominantShare <= 0.55 ? "balanced"
          : dominantShare <= 0.75 ? "moderate-asymmetric" : "dominant-asymmetric";
  const visualBand = (value) => typeof value === "number"
    ? Math.max(-4, Math.min(8, Math.floor(value * 4 + 0.001))) : "unknown";
  return {
    version: 1,
    landmarks: projected.landmarks.map(({ role, depth }) => ({ role, depth })),
    mainFlow: {
      display: projected.mainFlow.display,
      flexDirection: projected.mainFlow.flexDirection,
      gridTrackCount: projected.mainFlow.gridTracks.length,
      trackBalance,
    },
    regions: projected.regions.map(({ role, representation, display, box }) => ({
      role,
      representation,
      display,
      visualRow: visualBand(box[1]),
      visualColumn: visualBand(box[0]),
    })),
    representationHistogram: projected.representationHistogram,
  };
}

function visualGrammarFingerprint(value) {
  const projected = projectFingerprint(value);
  return projected.version === 2 ? { version: 1, ...projected.visualGrammar } : null;
}

function macroStructureFingerprint(value) {
  const projected = projectFingerprint(value);
  const { visualGrammar: _visualGrammar, ...macro } = projected;
  return { ...macro, version: 1 };
}

function fingerprintHash(value) {
  return crypto.createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

function compareReceipts(left, right) {
  return ["caseId", "route", "surface", "viewport", "state", "fingerprintSha256"]
    .map((key) => String(left[key]).localeCompare(String(right[key])))
    .find((order) => order !== 0) || 0;
}

function auditCrossOutputTemplates(input) {
  requireExactKeys(input, ["schemaVersion", "cohort", "observations"], "input");
  if (input.schemaVersion !== 1) fail("input schemaVersion must be 1");
  if (typeof input.cohort !== "string" || !/^[a-z0-9]+(?:[._-][a-z0-9]+)*$/.test(input.cohort)) fail("cohort is invalid");
  if (!Array.isArray(input.observations) || input.observations.length < 2 || input.observations.length > 200) fail("observations must contain 2..200 entries");
  const identities = new Set();
  const exactGroups = new Map();
  const dominantGroups = new Map();
  const visualGrammarGroups = new Map();
  const visualGrammarObservations = [];
  for (const [index, observation] of input.observations.entries()) {
    requireExactKeys(observation, ["caseId", "route", "surface", "viewport", "state", "macroFingerprint"], `observations[${index}]`);
    for (const field of ["caseId", "route", "surface", "viewport", "state"]) {
      boundedToken(observation[field], `observations[${index}].${field}`);
    }
    const identity = JSON.stringify([observation.caseId, observation.route, observation.surface, observation.viewport, observation.state]);
    if (identities.has(identity)) fail(`duplicate observation identity: ${identity}`);
    identities.add(identity);
    const projected = projectFingerprint(observation.macroFingerprint);
    const macro = macroStructureFingerprint(projected);
    const fingerprintSha256 = fingerprintHash(macro);
    const dominantFingerprintSha256 = fingerprintHash(dominantFingerprint(macro));
    const visualGrammar = visualGrammarFingerprint(projected);
    const visualGrammarSha256 = visualGrammar ? fingerprintHash(visualGrammar) : null;
    const groupKey = JSON.stringify([observation.surface, observation.viewport, observation.state, fingerprintSha256]);
    const dominantGroupKey = JSON.stringify([
      observation.surface, observation.viewport, observation.state, dominantFingerprintSha256,
    ]);
    const receipt = {
      caseId: observation.caseId,
      route: observation.route,
      surface: observation.surface,
      viewport: observation.viewport,
      state: observation.state,
      fingerprintSha256,
    };
    const exactGroup = exactGroups.get(groupKey) || { fingerprintSha256, observations: [] };
    exactGroup.observations.push(receipt);
    exactGroups.set(groupKey, exactGroup);
    const dominantGroup = dominantGroups.get(dominantGroupKey)
      || { dominantFingerprintSha256, observations: [] };
    dominantGroup.observations.push(receipt);
    dominantGroups.set(dominantGroupKey, dominantGroup);
    if (visualGrammarSha256) {
      const visualGrammarKey = JSON.stringify([observation.surface, observation.viewport, observation.state, visualGrammarSha256]);
      const visualGrammarGroup = visualGrammarGroups.get(visualGrammarKey)
        || { visualGrammarSha256, observations: [] };
      visualGrammarGroup.observations.push(receipt);
      visualGrammarGroups.set(visualGrammarKey, visualGrammarGroup);
      visualGrammarObservations.push({ receipt, visualGrammar, visualGrammarSha256 });
    }
  }
  const exactAdvisories = [...exactGroups.values()].flatMap((group) => {
    const caseIds = [...new Set(group.observations.map((item) => item.caseId))].sort();
    if (caseIds.length < 2) return [];
    const observations = [...group.observations].sort(compareReceipts)
      .map(({ fingerprintSha256: _fingerprintSha256, ...identity }) => identity);
    return [{
      code: "cross_output_template_candidate",
      caseIds,
      fingerprintSha256: group.fingerprintSha256,
      observations,
      confirmation: "review product evidence and paired blind renders; do not auto-fail",
    }];
  });
  const nearAdvisories = [...dominantGroups.values()].flatMap((group) => {
    const caseIds = [...new Set(group.observations.map((item) => item.caseId))].sort();
    const exactFingerprintCount = new Set(group.observations.map((item) => item.fingerprintSha256)).size;
    if (caseIds.length < 2 || exactFingerprintCount < 2) return [];
    const observations = [...group.observations].sort(compareReceipts);
    return [{
      code: "near_cross_output_template_candidate",
      caseIds,
      dominantFingerprintSha256: group.dominantFingerprintSha256,
      exactFingerprintCount,
      observations: observations.map(({ fingerprintSha256, ...identity }) => ({
        ...identity, fingerprintSha256,
      })),
      confirmation: "review product evidence and paired blind renders; categorical structural similarity is not a defect",
    }];
  });
  const visualGrammarAdvisories = [...visualGrammarGroups.values()].flatMap((group) => {
    const caseIds = [...new Set(group.observations.map((item) => item.caseId))].sort();
    if (caseIds.length < 2) return [];
    const observations = [...group.observations].sort(compareReceipts);
    return [{
      code: "cross_output_visual_grammar_candidate",
      caseIds,
      visualGrammarSha256: group.visualGrammarSha256,
      observations: observations.map(({ fingerprintSha256, ...identity }) => ({ ...identity, fingerprintSha256 })),
      confirmation: "review product evidence and paired blind renders; low-resolution type, radius, and pill similarity is not a defect",
    }];
  });
  const visualAxes = ["displayFamily", "displayScale", "majorRadius", "pillDensity"];
  const partialVisualGroups = new Map();
  for (let leftIndex = 0; leftIndex < visualGrammarObservations.length; leftIndex += 1) {
    const left = visualGrammarObservations[leftIndex];
    for (let rightIndex = leftIndex + 1; rightIndex < visualGrammarObservations.length; rightIndex += 1) {
      const right = visualGrammarObservations[rightIndex];
      if (left.receipt.caseId === right.receipt.caseId) continue;
      if (["surface", "viewport", "state"].some((field) => left.receipt[field] !== right.receipt[field])) continue;
      if (left.visualGrammarSha256 === right.visualGrammarSha256) continue;
      const sharedAxes = visualAxes.flatMap((name) => (
        left.visualGrammar[name] !== "none" && left.visualGrammar[name] === right.visualGrammar[name]
          ? [{ name, value: left.visualGrammar[name] }] : []
      ));
      if (sharedAxes.length < 2) continue;
      const caseIds = [left.receipt.caseId, right.receipt.caseId].sort();
      const groupKey = JSON.stringify([
        caseIds, left.receipt.surface, left.receipt.viewport, left.receipt.state, sharedAxes,
      ]);
      const group = partialVisualGroups.get(groupKey)
        || { caseIds, sharedAxes, observations: new Map() };
      for (const receipt of [left.receipt, right.receipt]) {
        const identity = JSON.stringify([
          receipt.caseId, receipt.route, receipt.surface, receipt.viewport, receipt.state,
        ]);
        group.observations.set(identity, receipt);
      }
      partialVisualGroups.set(groupKey, group);
    }
  }
  const partialVisualAdvisories = [...partialVisualGroups.values()].map((group) => ({
    code: "cross_output_partial_visual_grammar_candidate",
    caseIds: group.caseIds,
    sharedAxes: group.sharedAxes,
    observations: [...group.observations.values()].sort(compareReceipts),
    confirmation: "review product evidence and paired blind renders; sharing multiple low-resolution visual axes is not a defect",
  }));
  const advisories = [
    ...exactAdvisories, ...nearAdvisories, ...visualGrammarAdvisories, ...partialVisualAdvisories,
  ].sort((left, right) => (
    left.code.localeCompare(right.code)
      || left.caseIds.join("|").localeCompare(right.caseIds.join("|"))
      || (left.fingerprintSha256 || left.dominantFingerprintSha256 || left.visualGrammarSha256 || JSON.stringify(left.sharedAxes))
        .localeCompare(right.fingerprintSha256 || right.dominantFingerprintSha256 || right.visualGrammarSha256 || JSON.stringify(right.sharedAxes))
  ));
  return {
    schemaVersion: 1,
    cohort: input.cohort,
    status: advisories.length ? "advisories_present" : "no_exact_template_candidates",
    observationCount: input.observations.length,
    advisories,
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function regularInput(file) {
  const absolute = path.resolve(file);
  const stat = fs.lstatSync(absolute);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size > MAX_INPUT_BYTES) fail("input must be a bounded regular file");
  return absolute;
}

function main(argv) {
  if (argv.length !== 2) fail("usage: cross_output_template_audit.cjs INPUT.json OUTPUT.json");
  const inputPath = regularInput(argv[0]);
  const outputPath = path.resolve(argv[1]);
  if (fs.existsSync(outputPath)) fail("output already exists");
  const result = auditCrossOutputTemplates(JSON.parse(fs.readFileSync(inputPath, "utf8")));
  fs.writeFileSync(outputPath, `${JSON.stringify(result, null, 2)}\n`, { flag: "wx", mode: 0o600 });
  process.stdout.write(`${result.status}: ${result.advisories.length} advisory candidate(s)\n`);
}

module.exports = {
  CLAIM_BOUNDARY, auditCrossOutputTemplates, collectMacroFingerprint, dominantFingerprint,
  macroStructureFingerprint, projectFingerprint, quantize, visualGrammarFingerprint,
};

if (require.main === module) {
  try {
    main(process.argv.slice(2));
  } catch (error) {
    console.error(`cross-output template audit failed: ${error.message}`);
    process.exitCode = 1;
  }
}
