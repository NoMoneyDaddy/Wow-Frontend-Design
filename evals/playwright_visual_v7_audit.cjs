#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { chromium } = require("playwright");

const PRODUCT_TEXT_ROOT_SELECTOR = "main, dialog[open], [role='dialog'][aria-modal='true']";
const FONT_ROLE_SELECTORS = [
  { role: "page-heading", selector: "h1" },
  { role: "lead-prose", selector: "main p" },
  { role: "specimen", selector: "[data-eval='specimen'] h1, [data-eval='specimen'] h2, [data-eval='specimen'] h3, [data-eval='specimen'] p, [data-eval='specimen'] li, [data-eval='specimen'] dt, [data-eval='specimen'] dd, [data-eval='specimen'] label, [data-eval='specimen'] button" },
  { role: "interface-control", selector: "main button, main a, main input, main select, main textarea" },
  { role: "interface-control-option", selector: "main select option" },
  { role: "interface-control-optgroup", selector: "main select optgroup" },
];
const GENERIC_FONT_FAMILIES = new Set([
  "-apple-system", "blinkmacsystemfont", "cursive", "emoji", "fangsong", "fantasy",
  "math", "monospace", "sans-serif", "serif", "system-ui", "ui-monospace", "ui-rounded",
  "ui-sans-serif", "ui-serif",
]);
const FONT_ANGLE_EPSILON = 0.001;
const FONT_PROBE_UNIQUE_LIMIT = 2048;
const EVIDENCE_ONLY_ISSUES = new Set(["font_evidence_unavailable"]);

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
const LOCALE_RULES = {
  explainedTerm: String.raw`[（(][^）)]*[A-Za-z][^）)]*[）)]`,
  identifier: String.raw`\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b`,
  namedCurrencyValue: String.raw`^[A-Za-z][A-Za-z0-9 .&'’/-]*\s+(?:NT\$|TWD|USD|EUR)\s*[\d,]+(?:\.\d+)?$`,
};
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

function parseFirstDeclaredFontFamily(value) {
  const source = String(value || "").trim();
  let quote = null;
  let wasQuoted = false;
  let escaped = false;
  let result = "";
  for (const character of source) {
    if (escaped) {
      result += character;
      escaped = false;
      continue;
    }
    if (character === "\\") {
      result += character;
      escaped = true;
      continue;
    }
    if (quote) {
      result += character;
      if (character === quote) quote = null;
      continue;
    }
    if (character === "\"" || character === "'") {
      quote = character;
      if (!result.trim()) wasQuoted = true;
      result += character;
      continue;
    }
    if (character === ",") break;
    result += character;
  }
  return {
    family: result.trim().replace(/^(?:"([\s\S]*)"|'([\s\S]*)')$/, (_, doubleQuoted, singleQuoted) => doubleQuoted ?? singleQuoted),
    quoted: wasQuoted,
  };
}

function firstDeclaredFontFamily(value) {
  return parseFirstDeclaredFontFamily(value).family;
}

function normalizeFontFamily(value) {
  return String(value || "").trim().replace(/\s+/g, " ").toLocaleLowerCase("en-US");
}

function hasMixedHanAndLatin(value) {
  const text = String(value || "");
  return /\p{Script=Han}/u.test(text) && /[A-Za-z0-9]/u.test(text);
}

function hasLetterOrNumber(value) {
  return /[\p{Letter}\p{Number}]/u.test(String(value || ""));
}

function numericDescriptorRange(value, aliases = {}) {
  const normalized = String(value || "normal").trim().toLowerCase();
  if (Object.hasOwn(aliases, normalized)) return [aliases[normalized], aliases[normalized]];
  const numbers = normalized.match(/\d+(?:\.\d+)?/g)?.map(Number) || [];
  if (!numbers.length) return null;
  return numbers.length === 1 ? [numbers[0], numbers[0]] : [numbers[0], numbers[1]];
}

function fontStyleDescriptor(value) {
  const normalized = String(value || "normal").trim().toLowerCase();
  if (normalized.startsWith("italic")) return { category: "italic", range: [14, 14] };
  if (normalized.startsWith("oblique")) {
    const angles = [...normalized.matchAll(/([+-]?(?:\d+(?:\.\d+)?|\.\d+))(deg|grad|rad|turn)\b/g)].map((match) => {
      const value = Number(match[1]);
      return { deg: value, grad: value * 0.9, rad: value * 180 / Math.PI, turn: value * 360 }[match[2]];
    });
    const range = angles.length ? [Math.min(...angles), Math.max(...angles)] : [14, 14];
    return { category: "oblique", range };
  }
  return { category: "normal", range: [0, 0] };
}

function selectBoundaryFaces(candidates, boundaryIndex, direction) {
  if (!candidates.length) return [];
  const boundary = direction === "min"
    ? Math.min(...candidates.map(({ range }) => range[boundaryIndex]))
    : Math.max(...candidates.map(({ range }) => range[boundaryIndex]));
  return candidates.filter(({ range }) => range[boundaryIndex] === boundary).map(({ face }) => face);
}

function selectStyleFaces(faces, requestedValue) {
  const requested = fontStyleDescriptor(requestedValue);
  const requestedAngle = requested.category === "normal" ? 0 : requested.range[0];
  const candidates = faces.map((face) => {
    const descriptor = fontStyleDescriptor(face.style);
    const range = descriptor.category === "normal"
      ? [0, 0]
      : descriptor.category === "italic" ? [14, 14] : descriptor.range;
    return { face, range };
  });
  const oriented = requestedAngle < 0
    ? candidates.map(({ face, range }) => ({ face, range: [-range[1], -range[0]] }))
    : candidates;
  const target = Math.abs(requestedAngle);
  const sameDirection = oriented.filter(({ range }) => range[1] >= -FONT_ANGLE_EPSILON);
  const exact = sameDirection.filter(({ range }) => (
    target >= range[0] - FONT_ANGLE_EPSILON
    && target <= range[1] + FONT_ANGLE_EPSILON
  ));
  if (exact.length) return exact.map(({ face }) => face);
  const below = sameDirection.filter(({ range }) => range[1] < target - FONT_ANGLE_EPSILON);
  const above = sameDirection.filter(({ range }) => range[0] > target + FONT_ANGLE_EPSILON);
  const order = target >= 14
    ? [[above, 0, "min"], [below, 1, "max"]]
    : [[below, 1, "max"], [above, 0, "min"]];
  for (const [pool, boundaryIndex, direction] of order) {
    const selected = selectBoundaryFaces(pool, boundaryIndex, direction);
    if (selected.length) return selected;
  }
  return selectBoundaryFaces(oriented.filter(({ range }) => range[1] < 0), 1, "max");
}

function unicodeRangeCovers(value, codePoint) {
  const ranges = String(value || "U+0-10FFFF").split(",").flatMap((part) => {
    const match = part.trim().match(/^U\+([0-9A-F?]+)(?:-([0-9A-F]+))?$/i);
    if (!match) return [];
    const start = Number.parseInt(match[1].replace(/\?/g, "0"), 16);
    const end = Number.parseInt((match[2] || match[1]).replace(/\?/g, "F"), 16);
    return Number.isFinite(start) && Number.isFinite(end) ? [[start, end]] : [];
  });
  if (!ranges.length) return true;
  return ranges.some(([start, end]) => codePoint >= start && codePoint <= end);
}

function selectStretchFaces(faces, requestedStretch) {
  let selected = [...faces];
  const stretchAliases = {
    "ultra-condensed": 50, "extra-condensed": 62.5, condensed: 75, "semi-condensed": 87.5,
    normal: 100, "semi-expanded": 112.5, expanded: 125, "extra-expanded": 150, "ultra-expanded": 200,
  };
  const roleStretch = numericDescriptorRange(requestedStretch, stretchAliases)?.[0];
  if (roleStretch !== undefined && selected.length) {
    const candidates = selected.map((face) => ({ face, range: numericDescriptorRange(face.stretch, stretchAliases) || [100, 100] }));
    const exact = candidates.filter(({ range }) => roleStretch >= range[0] && roleStretch <= range[1]);
    if (exact.length) {
      selected = exact.map(({ face }) => face);
    } else if (roleStretch <= 100) {
      const narrower = candidates.filter(({ range }) => range[1] < roleStretch);
      const pool = narrower.length ? narrower : candidates.filter(({ range }) => range[0] > roleStretch);
      const boundary = narrower.length
        ? Math.max(...pool.map(({ range }) => range[1]))
        : Math.min(...pool.map(({ range }) => range[0]));
      selected = pool.filter(({ range }) => (narrower.length ? range[1] : range[0]) === boundary).map(({ face }) => face);
    } else {
      const wider = candidates.filter(({ range }) => range[0] > roleStretch);
      const pool = wider.length ? wider : candidates.filter(({ range }) => range[1] < roleStretch);
      const boundary = wider.length
        ? Math.min(...pool.map(({ range }) => range[0]))
        : Math.max(...pool.map(({ range }) => range[1]));
      selected = pool.filter(({ range }) => (wider.length ? range[0] : range[1]) === boundary).map(({ face }) => face);
    }
  }
  return selected;
}

function selectedFontFaces(role, faces) {
  const family = normalizeFontFamily(role.declaredPrimary);
  let selected = (faces || []).filter((face) => normalizeFontFamily(face.family) === family);
  selected = selectStretchFaces(selected, role.fontStretch);
  selected = selectStyleFaces(selected, role.fontStyle);
  const roleWeight = numericDescriptorRange(role.fontWeight, { normal: 400, bold: 700 })?.[0];
  if (roleWeight !== undefined) {
    const candidates = selected.map((face) => ({
      face,
      range: numericDescriptorRange(face.weight, { normal: 400, bold: 700 }) || [400, 400],
    }));
    const weightMatches = candidates.filter(({ range }) => roleWeight >= range[0] && roleWeight <= range[1]);
    if (weightMatches.length) {
      selected = weightMatches.map(({ face }) => face);
    } else if (candidates.length) {
      const preference = ({ range }) => {
        if (roleWeight < 400) {
          return range[1] < roleWeight ? [0, roleWeight - range[1]] : [1, range[0] - roleWeight];
        }
        if (roleWeight > 500) {
          return range[0] > roleWeight ? [0, range[0] - roleWeight] : [1, roleWeight - range[1]];
        }
        if (range[0] >= roleWeight && range[0] <= 500) return [0, range[0] - roleWeight];
        if (range[1] < roleWeight) return [1, roleWeight - range[1]];
        return [2, range[0] - 500];
      };
      const ranked = candidates.map((candidate) => ({ ...candidate, preference: preference(candidate) }));
      ranked.sort((left, right) => left.preference[0] - right.preference[0] || left.preference[1] - right.preference[1]);
      const best = ranked[0].preference;
      selected = ranked
        .filter(({ preference: value }) => value[0] === best[0] && value[1] === best[1])
        .map(({ face }) => face);
    }
  }
  return selected;
}

function fontFaceSelectionState(role, faces) {
  if (!Array.isArray(role.probeCodePoints) || !role.probeCodePoints.length) return "resolved";
  const selected = selectedFontFaces(role, faces);
  let pending = false;
  let ambiguous = false;
  for (const codePoint of role.probeCodePoints) {
    const coveringFaces = selected.filter((face) => unicodeRangeCovers(face.unicodeRange, codePoint));
    if (coveringFaces.length && coveringFaces.every((face) => face.status === "error")) return "failed";
    if (coveringFaces.some((face) => face.status === "error") && coveringFaces.some((face) => face.status === "loaded")) {
      ambiguous = true;
    }
    if (coveringFaces.length && !coveringFaces.some((face) => face.status === "loaded")) {
      pending ||= coveringFaces.some((face) => ["loading", "unloaded"].includes(face.status));
    }
  }
  return pending || ambiguous ? "unavailable" : "resolved";
}

function classifyPrimaryFontUsage(role) {
  const primary = normalizeFontFamily(role.declaredPrimary);
  const isGeneric = !role.declaredPrimaryQuoted
    && (GENERIC_FONT_FAMILIES.has(primary) || primary.startsWith("generic("));
  const textHasRelevantGlyph = role.probeHasRelevantGlyph ?? role.probeHasLetterOrNumber ?? hasLetterOrNumber(role.text);
  if (!primary || isGeneric) return "not_applicable";
  if (role.declaredFaceSelectionUnavailable) return "evidence_unavailable";
  if (!textHasRelevantGlyph) return "not_applicable";
  const actualFamilies = (role.actualFonts || [])
    .filter((font) => Number(font.glyphCount) > 0)
    .flatMap((font) => [font.familyName, font.postScriptName])
    .map(normalizeFontFamily)
    .filter(Boolean);
  const matchingFaces = (role.fontFaces || []).filter((face) => normalizeFontFamily(face.family) === primary);
  if (role.declaredFaceSelectionFailed) return "failed_font_face";
  if (!actualFamilies.length) return "platform_fonts_unavailable";
  if (actualFamilies.includes(primary)) return "rendered";
  if (matchingFaces.some((face) => face.status === "loaded")) return "unverified_alias";
  return "fallback_rendered";
}

function primaryFontMismatch(role) {
  return classifyPrimaryFontUsage(role) === "failed_font_face";
}

function captureFontProbeInIsolatedWorld(maxUniqueGlyphs, sourceTextOverride) {
  const sourceNode = this;
  const sourceIsTextNode = sourceNode?.nodeType === Node.TEXT_NODE;
  const node = sourceIsTextNode ? sourceNode.parentElement : sourceNode;
  if (!node) throw new Error("font probe source has no element context");
  const style = getComputedStyle(node);
  const declaredFamily = String(style.fontFamily);
  const fontStretch = String(style.fontStretch);
  const fontStyle = String(style.fontStyle);
  const fontWeight = String(style.fontWeight);
  const rectangle = sourceIsTextNode
    ? (() => {
      const range = document.createRange();
      range.selectNodeContents(sourceNode);
      const bounds = range.getBoundingClientRect();
      range.detach();
      return bounds;
    })()
    : node.getBoundingClientRect();
  const pseudoBeforeStyle = getComputedStyle(node, "::before");
  const pseudoAfterStyle = getComputedStyle(node, "::after");
  const pseudoBeforeContent = String(pseudoBeforeStyle.content || "none");
  const pseudoAfterContent = String(pseudoAfterStyle.content || "none");
  const colorHasVisibleAlpha = (value) => {
    const normalized = String(value || "").trim().toLowerCase();
    if (!normalized || normalized === "transparent") return false;
    const alphaMatch = normalized.match(/\/\s*([+-]?(?:\d+\.?\d*|\.\d+)%?)\s*\)$/u)
      || (normalized.startsWith("rgba(") ? normalized.match(/,\s*([+-]?(?:\d+\.?\d*|\.\d+))\s*\)$/u) : null);
    if (!alphaMatch) return true;
    const alpha = Number.parseFloat(alphaMatch[1]);
    return Number.isFinite(alpha) && alpha > 0;
  };
  const computedColorTokens = (value) => {
    const source = String(value || "");
    const tokens = [...source.matchAll(/(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color)\([^()]*\)|\btransparent\b/giu)]
      .map((match) => match[0]);
    return tokens;
  };
  const paintValueHasVisibleColor = (value) => {
    const normalized = String(value || "").trim().toLowerCase();
    if (!normalized || normalized === "none") return false;
    const colors = computedColorTokens(normalized);
    return colors.length ? colors.some(colorHasVisibleAlpha) : true;
  };
  const imagePaintVisible = (value) => {
    const normalized = String(value || "").trim().toLowerCase();
    if (!normalized || normalized === "none") return false;
    const colors = computedColorTokens(normalized);
    const externalImage = /(?:cross-fade|element|image-set|paint|src|url)\(/iu.test(normalized);
    if (colors.length && colors.every((color) => !colorHasVisibleAlpha(color)) && !externalImage) return false;
    return true;
  };
  const imagePaintReliable = (value) => {
    const normalized = String(value || "").trim().toLowerCase();
    if (!normalized || normalized === "none") return true;
    if (/(?:cross-fade|element|image-set|paint|src|url)\(/iu.test(normalized)) return false;
    return computedColorTokens(normalized).length > 0;
  };
  const colorHasVisibleLuminance = (value) => {
    if (!colorHasVisibleAlpha(value)) return false;
    const normalized = String(value || "").trim().toLowerCase();
    if (!normalized.startsWith("rgb")) return null;
    const components = normalized.match(/[+-]?(?:\d+\.?\d*|\.\d+)%?/gu) || [];
    if (components.length < 3) return null;
    return components.slice(0, 3).some((component) => Number.parseFloat(component) > 0);
  };
  const filterRemovesPaint = (value) => [...String(value || "").matchAll(/opacity\(([^)]+)\)/giu)]
    .some((match) => Number.parseFloat(match[1]) === 0);
  const transformRemovesPaint = (transform, scale) => {
    const scaleComponents = String(scale || "none").trim().split(/[\t\n\f\r ]+/u);
    if (scaleComponents[0] !== "none" && scaleComponents.some((value) => Number.parseFloat(value) === 0)) return true;
    if (!transform || transform === "none" || typeof DOMMatrix !== "function") return false;
    try {
      return Array.from(new DOMMatrix(transform).inverse().toFloat64Array()).some((value) => !Number.isFinite(value));
    }
    catch {
      return false;
    }
  };
  const lengthToPixels = (value, extent) => {
    const token = String(value || "").trim().toLowerCase();
    if (token.endsWith("%")) return (Number.parseFloat(token) / 100) * extent;
    if (token.endsWith("px") || /^[-+]?\d*\.?\d+$/u.test(token)) return Number.parseFloat(token);
    return Number.NaN;
  };
  const clipPathRemovesPaint = (computedStyle, box) => {
    const clipPath = String(computedStyle.clipPath || "none").trim().toLowerCase();
    const inset = clipPath.match(/^inset\((.*?)(?:\s+round\s+.*)?\)$/u);
    if (inset) {
      const values = inset[1].trim().split(/[\t\n\f\r ]+/u);
      const [top, right = top, bottom = top, left = right] = values.length === 3
        ? [values[0], values[1], values[2], values[1]]
        : values.length === 4
          ? values
          : [values[0], values[1] || values[0], values[2] || values[0], values[3] || values[1] || values[0]];
      const vertical = lengthToPixels(top, box.height) + lengthToPixels(bottom, box.height);
      const horizontal = lengthToPixels(left, box.width) + lengthToPixels(right, box.width);
      if ((Number.isFinite(vertical) && vertical >= box.height) || (Number.isFinite(horizontal) && horizontal >= box.width)) return true;
    }
    const polygon = clipPath.match(/^polygon\((.*)\)$/u);
    if (polygon) {
      const pointTokens = polygon[1].split(",").map((point) => point.trim());
      if (/^(?:evenodd|nonzero)$/u.test(pointTokens[0])) pointTokens.shift();
      const points = pointTokens.map((point) => {
        const [x, y] = point.split(/[\t\n\f\r ]+/u);
        return [lengthToPixels(x, box.width), lengthToPixels(y, box.height)];
      });
      if (points.length >= 3 && points.every((point) => point.every(Number.isFinite))) {
        const origin = points[0];
        const directionPoint = points.find((point) => point[0] !== origin[0] || point[1] !== origin[1]);
        if (!directionPoint) return true;
        const dx = directionPoint[0] - origin[0];
        const dy = directionPoint[1] - origin[1];
        const allCollinear = points.every((point) => Math.abs(dx * (point[1] - origin[1]) - dy * (point[0] - origin[0])) <= Number.EPSILON);
        if (allCollinear) return true;
      }
    }
    const circle = clipPath.match(/^circle\(([^\t\n\f\r )]+)/u);
    if (circle && Number.parseFloat(circle[1]) === 0) return true;
    const ellipse = clipPath.match(/^ellipse\(([^\t\n\f\r )]+)[\t\n\f\r ]+([^\t\n\f\r )]+)/u);
    return Boolean(ellipse && [ellipse[1], ellipse[2]].some((radius) => Number.parseFloat(radius) === 0));
  };
  const clipPathPaintReliable = (computedStyle) => {
    const clipPath = String(computedStyle.clipPath || "none").trim().toLowerCase();
    return clipPath === "none";
  };
  const legacyClipRemovesPaint = (computedStyle) => {
    const clip = String(computedStyle.clip || "auto").trim().toLowerCase();
    const rectangle = clip.match(/^rect\((.*)\)$/u);
    if (!rectangle) return false;
    const values = rectangle[1].trim().split(/\s*,\s*|[\t\n\f\r ]+/u).filter(Boolean);
    if (values.length !== 4) return false;
    const [top, right, bottom, left] = values.map((value) => lengthToPixels(value, 0));
    return [top, right, bottom, left].every(Number.isFinite) && (right <= left || bottom <= top);
  };
  const legacyClipPaintReliable = (computedStyle) => String(computedStyle.clip || "auto").trim().toLowerCase() === "auto";
  const paintBoxLayersReliable = (value, expected) => String(value || expected)
    .split(",")
    .map((layer) => layer.trim().toLowerCase())
    .every((layer) => layer === expected);
  const simplePaintGeometryReliable = (size, position, repeat) => {
    const sizes = String(size || "auto").split(",").map((value) => value.trim().toLowerCase());
    const positions = String(position || "0% 0%").split(",").map((value) => value.trim().toLowerCase());
    const repeats = String(repeat || "repeat").split(",").map((value) => value.trim().toLowerCase());
    const allowedSizes = new Set(["auto", "auto auto", "100% 100%", "cover"]);
    const allowedPositions = new Set(["0% 0%", "0px 0px", "50% 50%", "center", "center center"]);
    const allowedRepeats = new Set(["no-repeat", "repeat", "repeat repeat"]);
    return sizes.every((value) => allowedSizes.has(value))
      && positions.every((value) => allowedPositions.has(value))
      && repeats.every((value) => allowedRepeats.has(value));
  };
  const maskPaintState = (computedStyle) => {
    const maskImages = [...new Set([computedStyle.maskImage, computedStyle.webkitMaskImage]
      .map((value) => String(value || "none").trim())
      .filter((value) => value !== "none"))];
    if (!maskImages.length) return { reliable: true, removesPaint: false };
    if (
      !paintBoxLayersReliable(computedStyle.maskOrigin || computedStyle.webkitMaskOrigin, "border-box")
      || !paintBoxLayersReliable(computedStyle.maskClip || computedStyle.webkitMaskClip, "border-box")
    ) {
      return { reliable: false, removesPaint: false };
    }
    if (!simplePaintGeometryReliable(
      computedStyle.maskSize || computedStyle.webkitMaskSize,
      computedStyle.maskPosition || computedStyle.webkitMaskPosition,
      computedStyle.maskRepeat || computedStyle.webkitMaskRepeat,
    )) {
      return { reliable: false, removesPaint: false };
    }
    const composites = String(computedStyle.maskComposite || computedStyle.webkitMaskComposite || "add")
      .split(",").map((value) => value.trim().toLowerCase());
    if (composites.some((value) => !["add", "source-over"].includes(value))) {
      return { reliable: false, removesPaint: false };
    }
    if (maskImages.some((value) => !imagePaintReliable(value))) return { reliable: false, removesPaint: false };
    const modes = String(computedStyle.maskMode || "match-source").split(",").map((value) => value.trim().toLowerCase());
    let anyVisibleLayer = false;
    for (let index = 0; index < maskImages.length; index += 1) {
      const colors = computedColorTokens(maskImages[index]);
      if (!colors.length) return { reliable: false, removesPaint: false };
      const mode = modes[index] || modes[modes.length - 1] || "match-source";
      if (mode === "luminance") {
        const luminance = colors.map(colorHasVisibleLuminance);
        if (luminance.some((value) => value === null)) return { reliable: false, removesPaint: false };
        anyVisibleLayer ||= luminance.some(Boolean);
      }
      else {
        anyVisibleLayer ||= colors.some(colorHasVisibleAlpha);
      }
    }
    return { reliable: true, removesPaint: !anyVisibleLayer };
  };
  let ancestorPaintVisible = true;
  let fontPaintEvidenceReliable = true;
  let fixedContainingBlockIsViewport = true;
  let clippedRectangle = rectangle;
  for (let current = node; current; current = current.parentElement) {
    const currentStyle = getComputedStyle(current);
    if (current !== node && (
      String(currentStyle.transform) !== "none"
      || String(currentStyle.perspective) !== "none"
      || String(currentStyle.filter) !== "none"
      || String(currentStyle.backdropFilter || currentStyle.webkitBackdropFilter || "none") !== "none"
      || /(?:^|\s)(?:content|layout|paint|strict)(?:\s|$)/u.test(String(currentStyle.contain))
      || /(?:^|,\s*)(?:filter|perspective|transform)(?:\s*,|$)/u.test(String(currentStyle.willChange))
      || currentStyle.contentVisibility === "auto"
    )) {
      fixedContainingBlockIsViewport = false;
    }
    const maskState = maskPaintState(currentStyle);
    if (
      !clipPathPaintReliable(currentStyle)
      || !legacyClipPaintReliable(currentStyle)
      || !maskState.reliable
      || /url\(/iu.test(String(currentStyle.filter))
    ) {
      fontPaintEvidenceReliable = false;
    }
    if (
      currentStyle.display === "none"
      || currentStyle.contentVisibility === "hidden"
      || Number.parseFloat(currentStyle.opacity) <= 0
      || filterRemovesPaint(currentStyle.filter)
      || transformRemovesPaint(currentStyle.transform, currentStyle.scale)
      || clipPathRemovesPaint(currentStyle, current.getBoundingClientRect())
      || legacyClipRemovesPaint(currentStyle)
      || maskState.removesPaint
    ) {
      ancestorPaintVisible = false;
      break;
    }
    if (currentStyle.display !== "contents" && (sourceIsTextNode || current !== node) && (
      ["clip", "hidden"].includes(currentStyle.overflowX)
      || ["clip", "hidden"].includes(currentStyle.overflowY)
    )) {
      const ancestorRectangle = current.getBoundingClientRect();
      const previousClippedRectangle = clippedRectangle;
      clippedRectangle = {
        left: ["clip", "hidden"].includes(currentStyle.overflowX)
          ? Math.max(clippedRectangle.left, ancestorRectangle.left)
          : clippedRectangle.left,
        right: ["clip", "hidden"].includes(currentStyle.overflowX)
          ? Math.min(clippedRectangle.right, ancestorRectangle.right)
          : clippedRectangle.right,
        top: ["clip", "hidden"].includes(currentStyle.overflowY)
          ? Math.max(clippedRectangle.top, ancestorRectangle.top)
          : clippedRectangle.top,
        bottom: ["clip", "hidden"].includes(currentStyle.overflowY)
          ? Math.min(clippedRectangle.bottom, ancestorRectangle.bottom)
          : clippedRectangle.bottom,
      };
      if (["left", "right", "top", "bottom"].some(
        (edge) => Math.abs(clippedRectangle[edge] - previousClippedRectangle[edge]) > Number.EPSILON,
      )) {
        fontPaintEvidenceReliable = false;
      }
      if (clippedRectangle.right <= clippedRectangle.left || clippedRectangle.bottom <= clippedRectangle.top) {
        ancestorPaintVisible = false;
        break;
      }
    }
  }
  const visibleTextShadow = paintValueHasVisibleColor(style.textShadow);
  const visibleTextStroke = Number.parseFloat(style.webkitTextStrokeWidth) > 0
    && colorHasVisibleAlpha(style.webkitTextStrokeColor);
  const textUsesBackgroundPaint = String(style.backgroundClip).includes("text");
  const visibleTextBackground = String(style.backgroundClip).includes("text")
    && (colorHasVisibleAlpha(style.backgroundColor) || imagePaintVisible(style.backgroundImage));
  if (
    textUsesBackgroundPaint
    && !colorHasVisibleAlpha(style.backgroundColor)
    && (
      !imagePaintReliable(style.backgroundImage)
      || !simplePaintGeometryReliable(style.backgroundSize, style.backgroundPosition, style.backgroundRepeat)
      || !paintBoxLayersReliable(style.backgroundOrigin, "padding-box")
    )
  ) {
    fontPaintEvidenceReliable = false;
  }
  const fillPaintVisible = colorHasVisibleAlpha(style.webkitTextFillColor || style.color)
    || visibleTextShadow
    || visibleTextStroke
    || visibleTextBackground;
  const zeroClippedContentBox = Number.parseFloat(style.width) <= 0
    && Number.parseFloat(style.height) <= 0
    && [style.paddingTop, style.paddingRight, style.paddingBottom, style.paddingLeft].every((value) => Number.parseFloat(value) <= 0)
    && style.overflowX !== "visible"
    && style.overflowY !== "visible";
  const visibilityCheckNode = sourceIsTextNode
    ? (() => {
      let current = node;
      while (current && getComputedStyle(current).display === "contents") current = current.parentElement;
      return current;
    })()
    : node;
  const documentLeft = -window.scrollX;
  const documentTop = -window.scrollY;
  const intersectsDocumentCanvas = rectangle.right > documentLeft
    && rectangle.left < documentLeft + document.documentElement.scrollWidth
    && rectangle.bottom > documentTop
    && rectangle.top < documentTop + document.documentElement.scrollHeight;
  const intersectsViewport = rectangle.right > 0
    && rectangle.left < window.innerWidth
    && rectangle.bottom > 0
    && rectangle.top < window.innerHeight;
  const fixedUsesViewport = style.position === "fixed" && fixedContainingBlockIsViewport;
  const fontPaintVisible = ancestorPaintVisible
    && fillPaintVisible
    && !zeroClippedContentBox
    && (fixedUsesViewport ? intersectsViewport : intersectsDocumentCanvas)
    && Number.parseFloat(style.fontSize) > 0
    && (
      !visibilityCheckNode
      || typeof visibilityCheckNode.checkVisibility !== "function"
      || visibilityCheckNode.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })
    );
  const imageContentToken = /^(?:-webkit-cross-fade|-webkit-gradient|-webkit-image-set|conic-gradient|cross-fade|element|image|image-set|linear-gradient|paint|radial-gradient|repeating-conic-gradient|repeating-linear-gradient|repeating-radial-gradient|src|url)\(/i;
  const tokenizeComputedContent = (value) => {
    const source = String(value || "").trim();
    const tokens = [];
    let token = "";
    let quote = null;
    let escaped = false;
    let depth = 0;
    for (const character of source) {
      if (escaped) {
        token += character;
        escaped = false;
        continue;
      }
      if (character === "\\") {
        token += character;
        escaped = true;
        continue;
      }
      if (quote) {
        token += character;
        if (character === quote) quote = null;
        continue;
      }
      if (character === "\"" || character === "'") {
        quote = character;
        token += character;
        continue;
      }
      if (character === "(") depth += 1;
      if (character === ")" && depth > 0) depth -= 1;
      if (character === "/" && depth === 0) break;
      if (/[\t\n\f\r ]/u.test(character) && depth === 0) {
        if (token) tokens.push(token);
        token = "";
        continue;
      }
      token += character;
    }
    if (token) tokens.push(token);
    return tokens;
  };
  const decodeCssStringToken = (token) => {
    const quote = token[0];
    if ((quote !== "\"" && quote !== "'") || token.at(-1) !== quote) return null;
    let result = "";
    for (let index = 1; index < token.length - 1; index += 1) {
      const character = token[index];
      if (character !== "\\") {
        result += character;
        continue;
      }
      const next = token[index + 1];
      if (next === "\n" || next === "\r" || next === "\f") {
        if (next === "\r" && token[index + 2] === "\n") index += 1;
        index += 1;
        continue;
      }
      let hexadecimal = "";
      while (index + 1 < token.length - 1 && hexadecimal.length < 6 && /[0-9a-f]/i.test(token[index + 1])) {
        hexadecimal += token[++index];
      }
      if (hexadecimal) {
        const codePoint = Number.parseInt(hexadecimal, 16);
        result += String.fromCodePoint(codePoint === 0 || codePoint > 0x10FFFF ? 0xFFFD : codePoint);
        if (/[\t\n\f\r ]/u.test(token[index + 1] || "")) index += 1;
      } else if (index + 1 < token.length - 1) {
        result += token[++index];
      }
    }
    return result;
  };
  const pseudoTextMappingUnavailable = false;
  let visible = style.display !== "none"
    && style.visibility !== "hidden"
    && Number(rectangle.width) > 0
    && Number(rectangle.height) > 0;
  let probeText = sourceTextOverride === undefined
    ? (sourceIsTextNode ? sourceNode.nodeValue || "" : node.textContent || "")
    : String(sourceTextOverride);
  let diagnosticText = probeText;
  let probeTextComplete = true;
  let fontProbeEligible = true;
  const unsupportedTypographicPseudo = sourceIsTextNode && ["::first-letter", "::first-line"].some((pseudo) => {
    const pseudoStyle = getComputedStyle(node, pseudo);
    return ["fontFamily", "fontStretch", "fontStyle", "fontWeight"].some(
      (property) => String(pseudoStyle[property]) !== String(style[property]),
    );
  });
  let renderedTextMappingUnavailable = unsupportedTypographicPseudo
    || String(style.webkitTextSecurity || "none") !== "none";
  if (!sourceIsTextNode && node instanceof HTMLInputElement) {
    const value = node.value || "";
    const placeholder = node.placeholder || "";
    const placeholderStyle = getComputedStyle(node, "::placeholder");
    const placeholderTypographyDiffers = !value && Boolean(placeholder) && [
      "fontFamily", "fontStretch", "fontStyle", "fontWeight", "textTransform",
    ].some((property) => String(placeholderStyle[property]) !== String(style[property]));
    const nativeNonTextTypes = new Set(["checkbox", "color", "radio", "range"]);
    const nativeMappedTextTypes = new Set(["date", "datetime-local", "file", "month", "password", "time", "week"]);
    if (node.scrollWidth > node.clientWidth || node.scrollHeight > node.clientHeight) {
      fontPaintEvidenceReliable = false;
    }
    if (nativeNonTextTypes.has(node.type)) {
      probeText = "";
      diagnosticText = "";
    } else {
      probeText = value || placeholder;
      diagnosticText = ["button", "submit", "reset"].includes(node.type)
        ? probeText
        : (placeholder || (value ? "[input value present]" : ""));
      renderedTextMappingUnavailable ||= Boolean(value && nativeMappedTextTypes.has(node.type))
        || placeholderTypographyDiffers;
    }
  } else if (!sourceIsTextNode && node instanceof HTMLTextAreaElement) {
    const value = node.value || "";
    const placeholder = node.placeholder || "";
    const placeholderStyle = getComputedStyle(node, "::placeholder");
    probeText = value || placeholder;
    diagnosticText = placeholder || (value ? "[textarea value present]" : "");
    const horizontallyScrollable = ["auto", "scroll"].includes(String(style.overflowX));
    const verticallyScrollable = ["auto", "scroll"].includes(String(style.overflowY));
    if (
      (node.scrollWidth > node.clientWidth && !horizontallyScrollable)
      || (node.scrollHeight > node.clientHeight && !verticallyScrollable)
    ) {
      fontPaintEvidenceReliable = false;
    }
    renderedTextMappingUnavailable ||= !value && Boolean(placeholder) && [
      "fontFamily", "fontStretch", "fontStyle", "fontWeight", "textTransform",
    ].some((property) => String(placeholderStyle[property]) !== String(style[property]));
  } else if (!sourceIsTextNode && node instanceof HTMLSelectElement) {
    const isListBox = node.multiple || node.size > 1;
    fontProbeEligible = !isListBox;
    probeText = isListBox ? "" : [...node.selectedOptions].slice(0, 1).map((option) => option.label || "").join(" ");
    diagnosticText = probeText;
  } else if (!sourceIsTextNode && (node instanceof HTMLOptionElement || node instanceof HTMLOptGroupElement)) {
    probeText = node.label || "";
    diagnosticText = probeText;
  } else if (!sourceIsTextNode && String(node.tagName || "").startsWith("::")) {
    const contentTokens = tokenizeComputedContent(style.content);
    probeText = contentTokens.map(decodeCssStringToken).filter((value) => value !== null).join("");
    probeTextComplete = contentTokens.every((token) => (
      decodeCssStringToken(token) !== null
      || imageContentToken.test(token)
      || /^no-(?:open|close)-quote$/i.test(token)
    ));
    diagnosticText = "[generated content]";
  }
  const textTransform = String(style.textTransform || "none").trim().toLowerCase();
  if (textTransform !== "none") {
    try {
      const language = node.closest("[lang]")?.lang || document.documentElement.lang || undefined;
      if (textTransform === "uppercase") {
        renderedTextMappingUnavailable ||= probeText.toLocaleUpperCase(language) !== probeText;
      } else if (textTransform === "lowercase") {
        renderedTextMappingUnavailable ||= probeText.toLocaleLowerCase(language) !== probeText;
      } else {
        renderedTextMappingUnavailable = true;
      }
    } catch {
      renderedTextMappingUnavailable = true;
    }
  }
  const allRelevantProbeCharacters = [...new Intl.Segmenter("und", { granularity: "grapheme" }).segment(probeText)]
    .flatMap(({ segment }) => {
      const characters = [...segment];
      const forcedText = characters.includes("\uFE0E");
      const forcedEmoji = characters.some((character, index) => (
        characters[index + 1] === "\uFE0F"
        && /\p{Emoji}/u.test(character)
        && !/\p{Emoji_Modifier}/u.test(character)
      ));
      const defaultEmoji = !forcedText && (
        characters.some((character) => /\p{Extended_Pictographic}/u.test(character) && /\p{Emoji_Presentation}/u.test(character))
        || characters.some((character) => /\p{Regional_Indicator}/u.test(character))
      );
      if (forcedEmoji || defaultEmoji) return [];
      return characters.filter((character) => /[\p{Letter}\p{Mark}\p{Number}\p{Punctuation}\p{Symbol}]/u.test(character) && !/[\uFE0E\uFE0F]/u.test(character));
    });
  const uniqueRelevantProbeCharacters = [...new Set(allRelevantProbeCharacters)];
  const relevantProbeCharacters = uniqueRelevantProbeCharacters.slice(0, maxUniqueGlyphs);
  const relevantProbeText = relevantProbeCharacters.join("");
  let quote = null;
  let escapedCharacter = false;
  let primaryFamily = "";
  for (const character of declaredFamily) {
    if (escapedCharacter) {
      primaryFamily += character;
      escapedCharacter = false;
      continue;
    }
    if (character === "\\") {
      primaryFamily += character;
      escapedCharacter = true;
      continue;
    }
    if (quote) {
      primaryFamily += character;
      if (character === quote) quote = null;
      continue;
    }
    if (character === "\"" || character === "'") {
      quote = character;
      primaryFamily += character;
      continue;
    }
    if (character === ",") break;
    primaryFamily += character;
  }
  primaryFamily = primaryFamily.trim().replace(/^(?:"([\s\S]*)"|'([\s\S]*)')$/, (_, doubleQuoted, singleQuoted) => doubleQuoted ?? singleQuoted);
  const escapedFamily = primaryFamily.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
  const stretchKeywords = {
    "50%": "ultra-condensed", "62.5%": "extra-condensed", "75%": "condensed", "87.5%": "semi-condensed",
    "100%": "normal", "112.5%": "semi-expanded", "125%": "expanded", "150%": "extra-expanded", "200%": "ultra-expanded",
  };
  const queryStretch = stretchKeywords[fontStretch] || fontStretch;
  const descriptors = [fontStyle, fontWeight];
  if (queryStretch && queryStretch !== "normal" && !queryStretch.endsWith("%")) descriptors.push(queryStretch);
  const query = `${descriptors.join(" ")} 16px "${escapedFamily}"`;
  return {
    visible,
    fontPaintVisible,
    fontPaintEvidenceReliable,
    fontProbeEligible,
    declaredFamily,
    declaredFaceCheck: {
      check: document.fonts.check(query, relevantProbeText),
      omittedArbitraryStretch: Boolean(queryStretch && queryStretch.endsWith("%") && queryStretch !== "100%"),
    },
    fontStretch,
    fontStyle,
    fontWeight,
    pseudoBeforeContent,
    pseudoAfterContent,
    pseudoTextMappingUnavailable,
    renderedTextMappingUnavailable,
    probeTextComplete,
    probeSourceTextEmpty: probeText.length === 0,
    probeHasLetterOrNumber: /[\p{Letter}\p{Number}]/u.test(probeText),
    probeHasRelevantGlyph: relevantProbeCharacters.length > 0,
    probeRelevantGlyphOverflow: uniqueRelevantProbeCharacters.length > maxUniqueGlyphs,
    probeCodePoints: relevantProbeCharacters.map((character) => character.codePointAt(0)),
    text: diagnosticText.trim().replace(/\s+/g, " ").slice(0, 240),
  };
}

function captureFontFacesInIsolatedWorld() {
  globalThis.__wowFontEvidenceFaceState ||= { ids: new WeakMap(), nextId: 1 };
  return [...document.fonts].map((face) => ({
    evidenceIdentity: (() => {
      if (!globalThis.__wowFontEvidenceFaceState.ids.has(face)) {
        globalThis.__wowFontEvidenceFaceState.ids.set(face, globalThis.__wowFontEvidenceFaceState.nextId++);
      }
      return globalThis.__wowFontEvidenceFaceState.ids.get(face);
    })(),
    family: face.family.replace(/^(?:"([\s\S]*)"|'([\s\S]*)')$/, (_, doubleQuoted, singleQuoted) => doubleQuoted ?? singleQuoted),
    status: face.status,
    stretch: face.stretch,
    style: face.style,
    unicodeRange: face.unicodeRange,
    weight: face.weight,
  }));
}

function captureFontSelectorSnapshotInIsolatedWorld(selector) {
  return [...document.querySelectorAll(selector)].map((node) => {
    const style = getComputedStyle(node);
    const rectangle = node.getBoundingClientRect();
    const transformIsSingular = (value) => {
      const match = String(value || "").trim().match(/^matrix\(([^)]+)\)$/u);
      if (!match) return false;
      const values = match[1].split(",").map((part) => Number.parseFloat(part.trim()));
      return values.length === 6
        && values.every(Number.isFinite)
        && Math.abs(values[0] * values[3] - values[1] * values[2]) <= Number.EPSILON;
    };
    const nodePaintSuppressed = (() => {
      for (let current = node; current; current = current.parentElement) {
        const currentStyle = getComputedStyle(current);
        if (
          currentStyle.display === "none"
          || currentStyle.contentVisibility === "hidden"
          || Number(currentStyle.opacity) <= 0
          || /opacity\(\s*(?:0|0%)\s*\)/iu.test(String(currentStyle.filter))
          || /^inset\(\s*50%(?:\s+50%){0,3}\s*\)$/iu.test(String(currentStyle.clipPath).trim())
          || String(currentStyle.scale).trim().split(/[\t\n\f\r ]+/u).some((value) => Number.parseFloat(value) === 0)
          || transformIsSingular(currentStyle.transform)
        ) return true;
      }
      return false;
    })();
    const descendantTextRuns = [];
    const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
    for (let textNode = nodePaintSuppressed ? null : walker.nextNode(); textNode; textNode = walker.nextNode()) {
      const owner = textNode.parentElement;
      if (!owner) continue;
      const ownerStyle = getComputedStyle(owner);
      if (["hidden", "collapse"].includes(ownerStyle.visibility)) continue;
      let textRendered = true;
      for (let current = owner; current; current = current.parentElement) {
        const currentStyle = getComputedStyle(current);
        if (
          current.getAttribute("aria-hidden") === "true"
          || currentStyle.display === "none"
          || currentStyle.contentVisibility === "hidden"
          || Number(currentStyle.opacity) <= 0
        ) {
          textRendered = false;
          break;
        }
        if (current === node) break;
      }
      if (!textRendered) continue;
      descendantTextRuns.push([
        textNode.nodeValue || "",
        ownerStyle.fontFamily,
        ownerStyle.fontStretch,
        ownerStyle.fontStyle,
        ownerStyle.fontWeight,
        ownerStyle.fontSize,
        ownerStyle.textTransform,
        ownerStyle.webkitTextSecurity,
        ownerStyle.display,
        ownerStyle.visibility,
        ownerStyle.opacity,
        ownerStyle.color,
        ownerStyle.webkitTextFillColor,
        ownerStyle.textShadow,
        ownerStyle.webkitTextStrokeWidth,
        ownerStyle.webkitTextStrokeColor,
        ownerStyle.filter,
        ownerStyle.transform,
        ownerStyle.scale,
        ownerStyle.clipPath,
        ownerStyle.clip,
        ownerStyle.maskImage || ownerStyle.webkitMaskImage,
        ownerStyle.maskSize || ownerStyle.webkitMaskSize,
        ownerStyle.maskPosition || ownerStyle.webkitMaskPosition,
        ownerStyle.maskRepeat || ownerStyle.webkitMaskRepeat,
        ownerStyle.maskOrigin || ownerStyle.webkitMaskOrigin,
        ownerStyle.maskClip || ownerStyle.webkitMaskClip,
        ownerStyle.backgroundImage,
        ownerStyle.backgroundSize,
        ownerStyle.backgroundPosition,
        ownerStyle.backgroundRepeat,
        ownerStyle.backgroundOrigin,
        ownerStyle.backgroundClip,
        ["::first-letter", "::first-line"].map((pseudo) => {
          const pseudoStyle = getComputedStyle(owner, pseudo);
          return [pseudoStyle.fontFamily, pseudoStyle.fontStretch, pseudoStyle.fontStyle, pseudoStyle.fontWeight];
        }),
      ]);
    }
    let sourceText = descendantTextRuns;
    if (node instanceof HTMLInputElement || node instanceof HTMLTextAreaElement) {
      sourceText = node.value || node.placeholder || "";
    } else if (node instanceof HTMLSelectElement) {
      const isListBox = node.multiple || node.size > 1;
      const renderedOptionEntries = isListBox
        ? [...node.querySelectorAll("optgroup, option")].filter((item) => {
          for (let current = item; current && current !== node; current = current.parentElement) {
            const itemStyle = getComputedStyle(current);
            if (current.hidden || itemStyle.display === "none" || ["collapse", "hidden"].includes(itemStyle.visibility)) return false;
          }
          return true;
        })
        : [...node.selectedOptions].slice(0, 1);
      sourceText = renderedOptionEntries.map((item) => [item.tagName, item.label || ""]);
    } else if (node instanceof HTMLOptionElement || node instanceof HTMLOptGroupElement) {
      sourceText = node.label || "";
    }
    const pseudoBeforeStyle = getComputedStyle(node, "::before");
    const pseudoAfterStyle = getComputedStyle(node, "::after");
    const placeholderStyle = getComputedStyle(node, "::placeholder");
    return [
      node.tagName,
      style.display !== "none" && style.visibility !== "hidden" && rectangle.width > 0 && rectangle.height > 0,
      style.fontFamily,
      style.fontStretch,
      style.fontStyle,
      style.fontWeight,
      style.textTransform,
      style.webkitTextSecurity,
      [pseudoBeforeStyle.content, pseudoBeforeStyle.display, pseudoBeforeStyle.visibility, pseudoBeforeStyle.fontFamily, pseudoBeforeStyle.fontSize, pseudoBeforeStyle.fontStretch, pseudoBeforeStyle.fontStyle, pseudoBeforeStyle.fontWeight, pseudoBeforeStyle.opacity, pseudoBeforeStyle.overflowX, pseudoBeforeStyle.overflowY, pseudoBeforeStyle.width, pseudoBeforeStyle.height, pseudoBeforeStyle.padding, pseudoBeforeStyle.borderWidth, pseudoBeforeStyle.quotes],
      [pseudoAfterStyle.content, pseudoAfterStyle.display, pseudoAfterStyle.visibility, pseudoAfterStyle.fontFamily, pseudoAfterStyle.fontSize, pseudoAfterStyle.fontStretch, pseudoAfterStyle.fontStyle, pseudoAfterStyle.fontWeight, pseudoAfterStyle.opacity, pseudoAfterStyle.overflowX, pseudoAfterStyle.overflowY, pseudoAfterStyle.width, pseudoAfterStyle.height, pseudoAfterStyle.padding, pseudoAfterStyle.borderWidth, pseudoAfterStyle.quotes],
      [placeholderStyle.fontFamily, placeholderStyle.fontSize, placeholderStyle.fontStretch, placeholderStyle.fontStyle, placeholderStyle.fontWeight, placeholderStyle.textTransform, placeholderStyle.opacity, placeholderStyle.visibility],
      sourceText,
    ];
  });
}

function captureActiveFontAnimationsInIsolatedWorld(specifications) {
  const roots = [document];
  for (let rootIndex = 0; rootIndex < roots.length; rootIndex += 1) {
    for (const element of roots[rootIndex].querySelectorAll("*")) {
      if (element.shadowRoot && !roots.includes(element.shadowRoot)) roots.push(element.shadowRoot);
    }
  }
  const animations = [...new Set(roots.flatMap((root) => (
    root instanceof Document
      ? Document.prototype.getAnimations.call(root)
      : ShadowRoot.prototype.getAnimations.call(root)
  )))];
  const composedParent = (node) => {
    if (node?.assignedSlot) return node.assignedSlot;
    const parent = node?.parentNode;
    return parent instanceof ShadowRoot ? parent.host : parent;
  };
  const composedMatches = (node, selector) => selector.split(",").some((clause) => {
    const tokens = clause.trim().split(/\s+/);
    if (!tokens.length || !node.matches(tokens.at(-1))) return false;
    let ancestor = composedParent(node);
    for (let index = tokens.length - 2; index >= 0; index -= 1) {
      while (ancestor instanceof Element && !ancestor.matches(tokens[index])) {
        ancestor = composedParent(ancestor);
      }
      if (!(ancestor instanceof Element)) return false;
      ancestor = composedParent(ancestor);
    }
    return true;
  });
  const pseudoHasRenderedText = (node, pseudoElement) => {
    const style = getComputedStyle(node, pseudoElement);
    const visualContent = String(style.content || "").replace(/\s+\/\s+[\s\S]*$/, "").trim().toLowerCase();
    const quoteTokensOnly = /^(?:(?:open-quote|close-quote|no-open-quote|no-close-quote)\s*)+$/.test(visualContent);
    const hasText = !["", "none", "normal", "\"\"", "''", "no-open-quote", "no-close-quote"].includes(visualContent)
      && !/^(?:url\([^)]*\)\s*)+$/.test(visualContent)
      && !(quoteTokensOnly && style.quotes === "none")
      && !/^(?:(?:no-open-quote|no-close-quote)\s*)+$/.test(visualContent);
    return hasText && style.display !== "none" && !["hidden", "collapse"].includes(style.visibility)
      && Number(style.opacity) > 0;
  };
  const transformIsSingular = (value) => {
    const match = String(value || "").trim().match(/^matrix\(([^)]+)\)$/u);
    if (!match) return false;
    const values = match[1].split(",").map((part) => Number.parseFloat(part.trim()));
    return values.length === 6
      && values.every(Number.isFinite)
      && Math.abs(values[0] * values[3] - values[1] * values[2]) <= Number.EPSILON;
  };
  const paintSuppressed = (node) => {
    for (let current = node; current instanceof Element; current = composedParent(current)) {
      const style = getComputedStyle(current);
      if (/opacity\(\s*(?:0|0%)\s*\)/iu.test(String(style.filter))) return true;
      if (/^inset\(\s*50%(?:\s+50%){0,3}\s*\)$/iu.test(String(style.clipPath).trim())) return true;
      if (String(style.scale).trim().split(/[\t\n\f\r ]+/u).some((value) => Number.parseFloat(value) === 0)) return true;
      if (transformIsSingular(style.transform)) return true;
    }
    return false;
  };
  const isRenderedRole = (node) => {
    if (paintSuppressed(node)) return false;
    for (let current = node; current instanceof Element; current = composedParent(current)) {
      if (current.getAttribute("aria-hidden") === "true") return false;
      const style = getComputedStyle(current);
      if (style.display === "none" || style.contentVisibility === "hidden" || Number(style.opacity) <= 0) return false;
    }
    const style = getComputedStyle(node);
    const hasOwnBox = !["hidden", "collapse"].includes(style.visibility)
      && [...node.getClientRects()].some((rectangle) => rectangle.width > 0 && rectangle.height > 0);
    return hasOwnBox || pseudoHasRenderedText(node, "::before") || pseudoHasRenderedText(node, "::after");
  };
  const roleNodes = roots.flatMap((root) => [...root.querySelectorAll("*")]).filter((node) => (
    isRenderedRole(node) && specifications.some(({ selector }) => composedMatches(node, selector))
  ));
  const composedContains = (ancestor, node) => {
    for (let current = node; current; current = composedParent(current)) {
      if (current === ancestor) return true;
    }
    return false;
  };
  const hasRenderedText = (node) => {
    if (!(node instanceof Element) && !(node instanceof ShadowRoot)) return false;
    if (node instanceof Element && node.getAttribute("aria-hidden") === "true") return false;
    let directTextVisible = true;
    if (node instanceof Element) {
      const style = getComputedStyle(node);
      if (
        style.display === "none"
        || style.contentVisibility === "hidden"
        || Number(style.opacity) <= 0
        || /opacity\(\s*(?:0|0%)\s*\)/iu.test(String(style.filter))
        || /^inset\(\s*50%(?:\s+50%){0,3}\s*\)$/iu.test(String(style.clipPath).trim())
        || String(style.scale).trim().split(/[\t\n\f\r ]+/u).some((value) => Number.parseFloat(value) === 0)
        || transformIsSingular(style.transform)
      ) return false;
      directTextVisible = !["hidden", "collapse"].includes(style.visibility);
    }
    const children = [
      ...node.childNodes,
      ...(node instanceof HTMLSlotElement ? node.assignedNodes({ flatten: true }) : []),
      ...(node.shadowRoot ? [node.shadowRoot] : []),
    ];
    return children.some((child) => (
      child.nodeType === Node.TEXT_NODE
        ? directTextVisible && /[\p{Letter}\p{Number}]/u.test(child.nodeValue || "")
        : (child instanceof Element || child instanceof ShadowRoot) && hasRenderedText(child)
    ));
  };
  const affectsLayout = (property) => (
    /^(?:blockSize|bottom|column|contain|contentVisibility|display|flex|float|gap|grid|height|inlineSize|inset|left|margin|maxHeight|maxWidth|minHeight|minWidth|order|padding|position|right|rowGap|top|verticalAlign|width|writingMode)/.test(property)
  );
  return animations.flatMap((animation, animationIndex) => {
    if (!["pending", "running"].includes(animation.playState)) return [];
    const effect = animation.effect;
    const target = effect?.target;
    if (!(target instanceof Element)) return [];
    const intersectsRole = roleNodes.some((roleNode) => (
      composedContains(roleNode, target) || composedContains(target, roleNode)
    ));
    if (!intersectsRole) return [];
    let keyframes;
    try {
      keyframes = KeyframeEffect.prototype.getKeyframes.call(effect);
    } catch {
      return [{ animationIndex, keyframes: "unavailable" }];
    }
    const metadata = new Set(["composite", "computedOffset", "easing", "offset"]);
    const properties = [...new Set(keyframes.flatMap((keyframe) => (
      Object.keys(keyframe).filter((property) => !metadata.has(property))
    )))];
    const changesStyle = properties.some((property) => (
      new Set(keyframes.map((keyframe) => JSON.stringify(keyframe[property] ?? null))).size > 1
    ));
    const pseudoElement = typeof effect.pseudoElement === "string" ? effect.pseudoElement : "";
    const pseudoStyle = pseudoElement ? getComputedStyle(target, pseudoElement) : null;
    const pseudoContent = String(pseudoStyle?.content || "").trim();
    const visualPseudoContent = pseudoContent.replace(/\s+\/\s+[\s\S]*$/, "").trim().toLowerCase();
    const quoteTokensOnly = /^(?:(?:open-quote|close-quote|no-open-quote|no-close-quote)\s*)+$/.test(visualPseudoContent);
    const pseudoContentHasText = !["", "none", "normal", "\"\"", "''", "no-open-quote", "no-close-quote"].includes(visualPseudoContent)
      && !/^(?:url\([^)]*\)\s*)+$/.test(visualPseudoContent)
      && !(quoteTokensOnly && pseudoStyle?.quotes === "none")
      && !/^(?:(?:no-open-quote|no-close-quote)\s*)+$/.test(visualPseudoContent);
    const pseudoHasRenderedText = Boolean(
      pseudoElement
      && pseudoStyle
      && pseudoContentHasText
      && pseudoStyle.display !== "none"
      && pseudoStyle.visibility !== "hidden"
      && Number(pseudoStyle.opacity) > 0
    );
    const targetContainsRole = roleNodes.some((roleNode) => composedContains(target, roleNode));
    const descendantAffectsText = pseudoHasRenderedText || hasRenderedText(target)
      || (getComputedStyle(target).position !== "absolute"
        && getComputedStyle(target).position !== "fixed"
        && properties.some(affectsLayout));
    return changesStyle && (targetContainsRole || descendantAffectsText) ? [{ animationIndex }] : [];
  });
}

async function callIsolatedFontProbe(session, executionContextId, nodeId, sourceTextOverride) {
  const { object } = await session.send("DOM.resolveNode", { nodeId, executionContextId });
  if (!object?.objectId) throw new Error(`could not resolve font probe node ${nodeId}`);
  try {
    const { result, exceptionDetails } = await session.send("Runtime.callFunctionOn", {
      objectId: object.objectId,
      functionDeclaration: captureFontProbeInIsolatedWorld.toString(),
      arguments: [
        { value: FONT_PROBE_UNIQUE_LIMIT },
        ...(sourceTextOverride === undefined ? [] : [{ value: sourceTextOverride }]),
      ],
      returnByValue: true,
      awaitPromise: true,
      silent: true,
    });
    if (exceptionDetails || !result || !("value" in result)) {
      const detail = exceptionDetails?.exception?.description || exceptionDetails?.text || "no value";
      throw new Error(`isolated font probe failed for node ${nodeId}: ${detail}`);
    }
    return result.value;
  } finally {
    await session.send("Runtime.releaseObject", { objectId: object.objectId }).catch(() => {});
  }
}

async function captureIsolatedFontFaces(session, executionContextId) {
  const { result, exceptionDetails } = await session.send("Runtime.evaluate", {
    contextId: executionContextId,
    expression: `(${captureFontFacesInIsolatedWorld.toString()})()`,
    returnByValue: true,
    awaitPromise: true,
    silent: true,
  });
  if (exceptionDetails || !Array.isArray(result?.value)) {
    throw new Error(`isolated font face inventory failed: ${exceptionDetails?.text || "no value"}`);
  }
  return result.value;
}

async function captureIsolatedActiveFontAnimations(session, executionContextId, specifications) {
  const { result, exceptionDetails } = await session.send("Runtime.evaluate", {
    contextId: executionContextId,
    expression: `(${captureActiveFontAnimationsInIsolatedWorld.toString()})(${JSON.stringify(specifications)})`,
    returnByValue: true,
    awaitPromise: true,
    silent: true,
  });
  if (exceptionDetails || !Array.isArray(result?.value)) {
    throw new Error(`isolated font animation inventory failed: ${exceptionDetails?.text || "no value"}`);
  }
  return result.value;
}

async function captureIsolatedFontSelectorSnapshot(session, executionContextId, selector) {
  const { result, exceptionDetails } = await session.send("Runtime.evaluate", {
    contextId: executionContextId,
    expression: `(${captureFontSelectorSnapshotInIsolatedWorld.toString()})(${JSON.stringify(selector)})`,
    returnByValue: true,
    awaitPromise: true,
    silent: true,
  });
  if (exceptionDetails || !Array.isArray(result?.value)) {
    throw new Error(`isolated font selector snapshot failed: ${exceptionDetails?.text || "no value"}`);
  }
  return crypto.createHash("sha256").update(JSON.stringify(result.value)).digest("hex");
}

function stableFontProbeSignature(probe) {
  return JSON.stringify([
    probe.visible,
    probe.fontPaintVisible,
    probe.fontPaintEvidenceReliable,
    probe.fontProbeEligible,
    probe.declaredFamily,
    probe.fontStretch,
    probe.fontStyle,
    probe.fontWeight,
    probe.pseudoBeforeContent,
    probe.pseudoAfterContent,
    probe.pseudoTextMappingUnavailable,
    probe.renderedTextMappingUnavailable,
    probe.probeTextComplete,
    probe.probeSourceTextEmpty,
    probe.probeHasLetterOrNumber,
    probe.probeHasRelevantGlyph,
    probe.probeRelevantGlyphOverflow,
    probe.probeCodePoints,
    probe.declaredFaceCheck,
  ]);
}

function stableFontFaceInventorySignature(fontFaces) {
  return JSON.stringify((fontFaces || []).map((face) => [
    face.evidenceIdentity,
    face.family,
    face.status,
    face.stretch,
    face.style,
    face.unicodeRange,
    face.weight,
  ]).sort((left, right) => JSON.stringify(left).localeCompare(JSON.stringify(right), "en-US")));
}

function stablePlatformFontSignature(fonts) {
  return JSON.stringify((fonts || []).map((font) => [
    font.familyName,
    font.postScriptName,
    Number(font.glyphCount),
  ]).sort((left, right) => JSON.stringify(left).localeCompare(JSON.stringify(right), "en-US")));
}

function aggregatePlatformFonts(fontGroups) {
  const aggregated = new Map();
  for (const fonts of fontGroups || []) {
    for (const font of fonts || []) {
      const key = JSON.stringify([font.familyName, font.postScriptName, Boolean(font.isCustomFont)]);
      const current = aggregated.get(key);
      if (current) current.glyphCount += Number(font.glyphCount);
      else aggregated.set(key, { ...font, glyphCount: Number(font.glyphCount) });
    }
  }
  return [...aggregated.values()];
}

function descendantTextNodeRecords(node, output = []) {
  for (const [childIndex, child] of [...(node?.children || [])].entries()) {
    if (child.nodeType === 3) {
      output.push({
        nodeId: child.nodeId,
        parentNodeId: node.nodeId,
        childIndex,
        text: String(child.nodeValue || ""),
      });
    }
    else descendantTextNodeRecords(child, output);
  }
  for (const shadowRoot of node?.shadowRoots || []) descendantTextNodeRecords(shadowRoot, output);
  if (node?.contentDocument) descendantTextNodeRecords(node.contentDocument, output);
  return output;
}

function descendantPseudoNodeRecords(node, rootNodeId, output = []) {
  for (const pseudoNode of node?.pseudoElements || []) {
    output.push({
      pseudoNode,
      descendant: node.nodeId !== rootNodeId,
    });
  }
  for (const child of node?.children || []) {
    if (child.nodeType !== 3) descendantPseudoNodeRecords(child, rootNodeId, output);
  }
  for (const shadowRoot of node?.shadowRoots || []) descendantPseudoNodeRecords(shadowRoot, rootNodeId, output);
  if (node?.contentDocument) descendantPseudoNodeRecords(node.contentDocument, rootNodeId, output);
  return output;
}

function cdpFontSubtreeFingerprint(node) {
  const serialize = (current) => current ? [
    current.nodeType,
    current.nodeName,
    current.localName,
    current.nodeValue,
    current.pseudoType || null,
    current.pseudoIdentifier || null,
    current.shadowRootType || null,
    current.attributes || [],
    (current.children || []).map(serialize),
    (current.shadowRoots || []).map(serialize),
    (current.pseudoElements || []).map(serialize),
    serialize(current.contentDocument),
  ] : null;
  return crypto.createHash("sha256").update(JSON.stringify(serialize(node))).digest("hex");
}

function cdpBackendParentMap(node, parentBackendNodeId = null, output = new Map()) {
  if (!node || typeof node !== "object") return output;
  if (node.backendNodeId) output.set(node.backendNodeId, parentBackendNodeId);
  const children = [
    ...(node.children || []),
    ...(node.shadowRoots || []),
    ...(node.pseudoElements || []),
    ...[node.contentDocument, node.importedDocument, node.templateContent].filter(Boolean),
    ...(node.distributedNodes || []),
  ];
  for (const child of children) cdpBackendParentMap(child, node.backendNodeId || parentBackendNodeId, output);
  return output;
}

function cdpBackendNodeMap(node, output = new Map()) {
  if (!node || typeof node !== "object") return output;
  if (node.backendNodeId && !output.has(node.backendNodeId)) output.set(node.backendNodeId, node);
  const children = [
    ...(node.children || []),
    ...(node.shadowRoots || []),
    ...(node.pseudoElements || []),
    ...[node.contentDocument, node.importedDocument, node.templateContent].filter(Boolean),
    ...(node.distributedNodes || []),
  ];
  for (const child of children) cdpBackendNodeMap(child, output);
  return output;
}

function cdpNodeAttribute(node, name) {
  for (let index = 0; index < (node?.attributes || []).length; index += 2) {
    if (node.attributes[index] === name) return node.attributes[index + 1];
  }
  return null;
}

function cdpNodeHasAncestor(node, parentMap, nodeMap, predicate) {
  for (let backendNodeId = parentMap.get(node.backendNodeId); backendNodeId; backendNodeId = parentMap.get(backendNodeId)) {
    const ancestor = nodeMap.get(backendNodeId);
    if (ancestor && predicate(ancestor)) return true;
  }
  return false;
}

function cdpNodeMatchesFontRole(node, specification, parentMap, nodeMap) {
  if (node?.nodeType !== 1 || !node.backendNodeId || !node.nodeId) return false;
  const localName = String(node.localName || "").toLowerCase();
  const ancestorNamed = (name) => cdpNodeHasAncestor(
    node,
    parentMap,
    nodeMap,
    (ancestor) => String(ancestor.localName || "").toLowerCase() === name,
  );
  if (specification.role === "page-heading") return localName === "h1";
  if (specification.role === "lead-prose") return localName === "p" && ancestorNamed("main");
  if (specification.role === "specimen") {
    return ["h1", "h2", "h3", "p", "li", "dt", "dd", "label", "button"].includes(localName)
      && cdpNodeHasAncestor(
        node,
        parentMap,
        nodeMap,
        (ancestor) => cdpNodeAttribute(ancestor, "data-eval") === "specimen",
      );
  }
  if (specification.role === "interface-control") {
    return ["button", "a", "input", "select", "textarea"].includes(localName) && ancestorNamed("main");
  }
  if (specification.role === "interface-control-option") {
    return localName === "option" && ancestorNamed("select") && ancestorNamed("main");
  }
  if (specification.role === "interface-control-optgroup") {
    return localName === "optgroup" && ancestorNamed("select") && ancestorNamed("main");
  }
  return false;
}

function cdpFontRoleNodes(specification, parentMap, nodeMap) {
  return [...nodeMap.values()].filter((node) => (
    cdpNodeMatchesFontRole(node, specification, parentMap, nodeMap)
  ));
}

function cdpNodeHasRenderedText(node) {
  if (!node || typeof node !== "object") return false;
  const attributes = new Map();
  for (let index = 0; index < (node.attributes || []).length; index += 2) {
    attributes.set(node.attributes[index], node.attributes[index + 1]);
  }
  if (attributes.get("aria-hidden") === "true") return false;
  if (node.nodeType === 3 && /[\p{Letter}\p{Number}]/u.test(node.nodeValue || "")) return true;
  const children = [
    ...(node.children || []),
    ...(node.shadowRoots || []),
    ...(node.pseudoElements || []),
    ...[node.contentDocument, node.importedDocument, node.templateContent].filter(Boolean),
    ...(node.distributedNodes || []),
  ];
  return children.some(cdpNodeHasRenderedText);
}

function animationPropertyAffectsLayout(property) {
  return /^(?:blockSize|bottom|column|contain|contentVisibility|display|flex|float|gap|grid|height|inlineSize|inset|left|margin|maxHeight|maxWidth|minHeight|minWidth|order|padding|position|right|rowGap|top|verticalAlign|width|writingMode)/.test(property);
}

function captureAnimationTargetTextInIsolatedWorld(pseudoElement) {
  const transformIsSingular = (value) => {
    const match = String(value || "").trim().match(/^matrix\(([^)]+)\)$/u);
    if (!match) return false;
    const values = match[1].split(",").map((part) => Number.parseFloat(part.trim()));
    return values.length === 6
      && values.every(Number.isFinite)
      && Math.abs(values[0] * values[3] - values[1] * values[2]) <= Number.EPSILON;
  };
  const hasRenderedText = (node) => {
    if (!(node instanceof Element) && !(node instanceof ShadowRoot)) return false;
    let directTextVisible = true;
    if (node instanceof Element) {
      if (node.getAttribute("aria-hidden") === "true") return false;
      const style = getComputedStyle(node);
      if (
        style.display === "none"
        || style.contentVisibility === "hidden"
        || Number(style.opacity) <= 0
        || /opacity\(\s*(?:0|0%)\s*\)/iu.test(String(style.filter))
        || /^inset\(\s*50%(?:\s+50%){0,3}\s*\)$/iu.test(String(style.clipPath).trim())
        || String(style.scale).trim().split(/[\t\n\f\r ]+/u).some((value) => Number.parseFloat(value) === 0)
        || transformIsSingular(style.transform)
      ) return false;
      directTextVisible = !["hidden", "collapse"].includes(style.visibility);
    }
    const children = [
      ...node.childNodes,
      ...(node instanceof HTMLSlotElement ? node.assignedNodes({ flatten: true }) : []),
      ...(node.shadowRoot ? [node.shadowRoot] : []),
    ];
    return children.some((child) => (
      child.nodeType === Node.TEXT_NODE
        ? directTextVisible && /[\p{Letter}\p{Number}]/u.test(child.nodeValue || "")
        : (child instanceof Element || child instanceof ShadowRoot) && hasRenderedText(child)
    ));
  };
  const pseudoStyle = pseudoElement ? getComputedStyle(this, pseudoElement) : null;
  const pseudoContent = String(pseudoStyle?.content || "").trim();
  const visualPseudoContent = pseudoContent.replace(/\s+\/\s+[\s\S]*$/, "").trim().toLowerCase();
  const quoteTokensOnly = /^(?:(?:open-quote|close-quote|no-open-quote|no-close-quote)\s*)+$/.test(visualPseudoContent);
  const pseudoContentHasText = !["", "none", "normal", "\"\"", "''", "no-open-quote", "no-close-quote"].includes(visualPseudoContent)
    && !/^(?:url\([^)]*\)\s*)+$/.test(visualPseudoContent)
    && !(quoteTokensOnly && pseudoStyle?.quotes === "none")
    && !/^(?:(?:no-open-quote|no-close-quote)\s*)+$/.test(visualPseudoContent);
  return {
    targetHasRenderedText: hasRenderedText(this),
    pseudoHasRenderedText: Boolean(
      pseudoElement
      && pseudoStyle
      && pseudoContentHasText
      && pseudoStyle.display !== "none"
      && pseudoStyle.visibility !== "hidden"
      && Number(pseudoStyle.opacity) > 0
    ),
  };
}

function captureNodeRenderedInIsolatedWorld() {
  const transformIsSingular = (value) => {
    const match = String(value || "").trim().match(/^matrix\(([^)]+)\)$/u);
    if (!match) return false;
    const values = match[1].split(",").map((part) => Number.parseFloat(part.trim()));
    return values.length === 6
      && values.every(Number.isFinite)
      && Math.abs(values[0] * values[3] - values[1] * values[2]) <= Number.EPSILON;
  };
  const composedParent = (node) => {
    if (node?.assignedSlot) return node.assignedSlot;
    const parent = node?.parentNode;
    return parent instanceof ShadowRoot ? parent.host : parent;
  };
  for (let current = this; current instanceof Element; current = composedParent(current)) {
    if (current.getAttribute("aria-hidden") === "true") return false;
    const style = getComputedStyle(current);
    if (style.display === "none" || style.contentVisibility === "hidden" || Number(style.opacity) <= 0) return false;
  }
  const style = getComputedStyle(this);
  for (let current = this; current instanceof Element; current = composedParent(current)) {
    const currentStyle = getComputedStyle(current);
    if (/opacity\(\s*(?:0|0%)\s*\)/iu.test(String(currentStyle.filter))) return false;
    if (/^inset\(\s*50%(?:\s+50%){0,3}\s*\)$/iu.test(String(currentStyle.clipPath).trim())) return false;
    if (String(currentStyle.scale).trim().split(/[\t\n\f\r ]+/u).some((value) => Number.parseFloat(value) === 0)) return false;
    if (transformIsSingular(currentStyle.transform)) return false;
  }
  const pseudoHasRenderedText = (pseudoElement) => {
    const pseudoStyle = getComputedStyle(this, pseudoElement);
    const visualContent = String(pseudoStyle.content || "").replace(/\s+\/\s+[\s\S]*$/, "").trim().toLowerCase();
    const quoteTokensOnly = /^(?:(?:open-quote|close-quote|no-open-quote|no-close-quote)\s*)+$/.test(visualContent);
    const hasText = !["", "none", "normal", "\"\"", "''", "no-open-quote", "no-close-quote"].includes(visualContent)
      && !/^(?:url\([^)]*\)\s*)+$/.test(visualContent)
      && !(quoteTokensOnly && pseudoStyle.quotes === "none")
      && !/^(?:(?:no-open-quote|no-close-quote)\s*)+$/.test(visualContent);
    return hasText && pseudoStyle.display !== "none" && !["hidden", "collapse"].includes(pseudoStyle.visibility)
      && Number(pseudoStyle.opacity) > 0;
  };
  const hasOwnBox = !["hidden", "collapse"].includes(style.visibility)
    && [...this.getClientRects()].some((rectangle) => rectangle.width > 0 && rectangle.height > 0);
  return hasOwnBox || pseudoHasRenderedText("::before") || pseudoHasRenderedText("::after");
}

async function captureIsolatedNodeRendered(session, executionContextId, node) {
  let objectId;
  try {
    const { object } = await session.send("DOM.resolveNode", {
      backendNodeId: node.backendNodeId,
      executionContextId,
    });
    objectId = object?.objectId;
    if (!objectId) return false;
    const { result, exceptionDetails } = await session.send("Runtime.callFunctionOn", {
      objectId,
      functionDeclaration: captureNodeRenderedInIsolatedWorld.toString(),
      returnByValue: true,
      silent: true,
    });
    return !exceptionDetails && result?.value === true;
  } finally {
    if (objectId) await session.send("Runtime.releaseObject", { objectId }).catch(() => {});
  }
}

async function renderedCdpFontRoleNodes(session, executionContextId, specification, parentMap, nodeMap) {
  const nodes = cdpFontRoleNodes(specification, parentMap, nodeMap);
  const shadowNodes = nodes.filter((node) => cdpNodeHasAncestor(
    node,
    parentMap,
    nodeMap,
    (ancestor) => ancestor.nodeType === 11,
  ));
  const rendered = await Promise.all(shadowNodes.map(
    (node) => captureIsolatedNodeRendered(session, executionContextId, node),
  ));
  const renderedShadowNodes = shadowNodes.filter((_, index) => rendered[index]);
  return nodes.filter((node) => !shadowNodes.includes(node)).concat(renderedShadowNodes);
}

async function captureIsolatedAnimationTargetText(
  session,
  executionContextId,
  backendNodeId,
  pseudoElement,
) {
  let objectId;
  try {
    const { object } = await session.send("DOM.resolveNode", { backendNodeId, executionContextId });
    objectId = object?.objectId;
    if (!objectId) throw new Error("animation target unavailable");
    const { result, exceptionDetails } = await session.send("Runtime.callFunctionOn", {
      objectId,
      functionDeclaration: captureAnimationTargetTextInIsolatedWorld.toString(),
      arguments: [{ value: pseudoElement }],
      returnByValue: true,
      silent: true,
    });
    const value = result?.value;
    if (
      exceptionDetails
      || typeof value?.targetHasRenderedText !== "boolean"
      || typeof value?.pseudoHasRenderedText !== "boolean"
    ) throw new Error("animation target text inventory unavailable");
    return value;
  } finally {
    if (objectId) await session.send("Runtime.releaseObject", { objectId }).catch(() => {});
  }
}

function cdpBackendContains(parentMap, ancestorBackendNodeId, nodeBackendNodeId) {
  for (let current = nodeBackendNodeId; current; current = parentMap.get(current)) {
    if (current === ancestorBackendNodeId) return true;
  }
  return false;
}

async function cdpAnimationStyleChange(session, animationId) {
  let objectId;
  try {
    const { remoteObject } = await session.send("Animation.resolveAnimation", { animationId });
    objectId = remoteObject?.objectId;
    if (!objectId) return { changesStyle: true, properties: [] };
    const { result, exceptionDetails } = await session.send("Runtime.callFunctionOn", {
      objectId,
      functionDeclaration: `function () {
        const keyframes = this.effect?.getKeyframes?.();
        if (!Array.isArray(keyframes)) return null;
        const metadata = new Set(["composite", "computedOffset", "easing", "offset"]);
        const properties = [...new Set(keyframes.flatMap((keyframe) => (
          Object.keys(keyframe).filter((property) => !metadata.has(property))
        )))];
        return {
          changesStyle: properties.some((property) => (
            new Set(keyframes.map((keyframe) => JSON.stringify(keyframe[property] ?? null))).size > 1
          )),
          properties,
          pseudoElement: typeof this.effect?.pseudoElement === "string"
            ? this.effect.pseudoElement
            : null,
        };
      }`,
      returnByValue: true,
      silent: true,
    });
    const value = result?.value;
    if (
      exceptionDetails
      || typeof value?.changesStyle !== "boolean"
      || !Array.isArray(value.properties)
      || !(value.pseudoElement === null || typeof value.pseudoElement === "string")
    ) {
      return { changesStyle: true, properties: [] };
    }
    return value;
  } catch {
    return { changesStyle: true, properties: [] };
  } finally {
    if (objectId) await session.send("Runtime.releaseObject", { objectId }).catch(() => {});
  }
}

async function activeIntersectingCdpAnimations(
  session,
  executionContextId,
  animations,
  parentMap,
  nodeMap,
  roleBackendNodeIds,
) {
  const findings = [];
  for (const animation of animations.values()) {
    if (!["pending", "running"].includes(animation.playState) || animation.pausedState) continue;
    const targetBackendNodeId = animation.source?.backendNodeId;
    if (!targetBackendNodeId) continue;
    const styleChange = await cdpAnimationStyleChange(session, animation.id);
    const targetNode = nodeMap.get(targetBackendNodeId);
    const isolatedText = await captureIsolatedAnimationTargetText(
      session,
      executionContextId,
      targetBackendNodeId,
      styleChange.pseudoElement,
    ).catch(() => ({
      targetHasRenderedText: cdpNodeHasRenderedText(targetNode),
      pseudoHasRenderedText: Boolean(styleChange.pseudoElement),
    }));
    const targetRendered = await captureIsolatedNodeRendered(
      session,
      executionContextId,
      targetNode || { backendNodeId: targetBackendNodeId },
    ).catch(() => true);
    if (!targetRendered && !isolatedText.targetHasRenderedText && !isolatedText.pseudoHasRenderedText) continue;
    const targetContainsRole = [...roleBackendNodeIds].some((roleBackendNodeId) => (
      cdpBackendContains(parentMap, targetBackendNodeId, roleBackendNodeId)
    ));
    const roleContainsTarget = [...roleBackendNodeIds].some((roleBackendNodeId) => (
      cdpBackendContains(parentMap, roleBackendNodeId, targetBackendNodeId)
    ));
    if (!targetContainsRole && !roleContainsTarget) continue;
    const position = targetNode
      ? await session.send("CSS.getComputedStyleForNode", { nodeId: targetNode.nodeId }).catch(() => null)
      : null;
    const positionValue = position?.computedStyle?.find(({ name }) => name === "position")?.value;
    const descendantAffectsText = isolatedText.targetHasRenderedText || isolatedText.pseudoHasRenderedText
      || (!["absolute", "fixed"].includes(positionValue)
        && styleChange.properties.some(animationPropertyAffectsLayout));
    if (styleChange.changesStyle && (targetContainsRole || descendantAffectsText)) {
      findings.push({ id: animation.id, targetBackendNodeId });
    }
  }
  return findings;
}

function userAgentShadowTextNodeRecords(node) {
  return (node?.shadowRoots || [])
    .filter((shadowRoot) => shadowRoot.shadowRootType === "user-agent")
    .flatMap((shadowRoot) => descendantTextNodeRecords(shadowRoot))
    .filter(({ text }) => text.length > 0);
}

async function captureNativeHostPlatformFonts(session, nodeId, describedNode, rendered) {
  const { fonts } = await session.send("CSS.getPlatformFontsForNode", { nodeId });
  if (
    fonts.some((font) => Number(font.glyphCount) > 0)
    || rendered.renderedTextMappingUnavailable
    || rendered.probeSourceTextEmpty
    || !["input", "textarea"].includes(String(describedNode?.localName || "").toLowerCase())
  ) {
    return { fonts, source: "host" };
  }
  const shadowRecords = userAgentShadowTextNodeRecords(describedNode);
  const shadowCodePoints = new Set(
    shadowRecords.flatMap(({ text }) => [...text].map((character) => character.codePointAt(0))),
  );
  if (
    !rendered.probeCodePoints.length
    || rendered.probeCodePoints.some((codePoint) => !shadowCodePoints.has(codePoint))
  ) {
    return { fonts, source: "host" };
  }
  const shadowFonts = await captureTextRecordPlatformFonts(session, shadowRecords);
  return shadowFonts.some((font) => Number(font.glyphCount) > 0)
    ? { fonts: shadowFonts, source: "user-agent-shadow" }
    : { fonts, source: "host" };
}

async function captureTextRecordPlatformFonts(session, records) {
  return aggregatePlatformFonts(await Promise.all(records.map(async ({ nodeId }) => {
    const { fonts } = await session.send("CSS.getPlatformFontsForNode", { nodeId });
    return fonts;
  })));
}

function stableFontTextRunGroupSignature(probe) {
  return JSON.stringify([
    probe.visible,
    probe.fontPaintVisible,
    probe.fontPaintEvidenceReliable,
    probe.fontProbeEligible,
    probe.declaredFamily,
    probe.fontStretch,
    probe.fontStyle,
    probe.fontWeight,
    probe.pseudoTextMappingUnavailable,
    probe.renderedTextMappingUnavailable,
    probe.probeTextComplete,
  ]);
}

function subtractPlatformFonts(fonts, excludedFonts) {
  const excludedCounts = new Map();
  for (const font of excludedFonts || []) {
    const key = JSON.stringify([font.familyName, font.postScriptName]);
    excludedCounts.set(key, (excludedCounts.get(key) || 0) + Number(font.glyphCount));
  }
  return (fonts || []).flatMap((font) => {
    const key = JSON.stringify([font.familyName, font.postScriptName]);
    const excluded = Math.min(Number(font.glyphCount), excludedCounts.get(key) || 0);
    excludedCounts.set(key, Math.max(0, (excludedCounts.get(key) || 0) - excluded));
    const glyphCount = Number(font.glyphCount) - excluded;
    return glyphCount > 0 ? [{ ...font, glyphCount }] : [];
  });
}

function finalizeFontCandidate(index, rendered, fonts, fontFaces, pseudoType = null, metadata = {}) {
  const primary = firstDeclaredFontFamily(rendered.declaredFamily);
  const familyFaces = fontFaces.filter(
    (face) => normalizeFontFamily(face.family) === normalizeFontFamily(primary),
  );
  const stretchSelectedFaces = selectStretchFaces(familyFaces, rendered.fontStretch);
  rendered.declaredFaceCheckReliable = rendered.probeTextComplete
    && !rendered.probeRelevantGlyphOverflow
    && (!rendered.declaredFaceCheck.omittedArbitraryStretch || stretchSelectedFaces.length === familyFaces.length);
  rendered.declaredFaceCheck = rendered.declaredFaceCheck.check;
  let selectionState = rendered.probeRelevantGlyphOverflow
    ? "unavailable"
    : rendered.probeHasRelevantGlyph
      ? fontFaceSelectionState({ declaredPrimary: primary, ...rendered }, fontFaces)
      : "resolved";
  if (!rendered.probeTextComplete && rendered.probeHasRelevantGlyph) selectionState = "unavailable";
  const hasRelevantFailedFace = fontFaces.some((face) => (
    face.status === "error"
    && normalizeFontFamily(face.family) === normalizeFontFamily(primary)
    && rendered.probeCodePoints.some((codePoint) => unicodeRangeCovers(face.unicodeRange, codePoint))
  ));
  if (
    !rendered.fontProbeStable
    || !rendered.fontInventoryStable
    || !rendered.platformFontsStable
    || !rendered.fontPaintEvidenceReliable
    || rendered.browserGeneratedTextUnavailable
    || rendered.renderedTextMappingUnavailable
    || rendered.pseudoTextMappingUnavailable
  ) {
    selectionState = "unavailable";
  }
  else if (rendered.declaredFaceCheckReliable && rendered.declaredFaceCheck && selectionState === "failed") {
    selectionState = "unavailable";
  }
  else if (
    rendered.declaredFaceCheckReliable
    && !rendered.declaredFaceCheck
    && hasRelevantFailedFace
    && rendered.probeHasRelevantGlyph
    && selectionState === "resolved"
  ) {
    selectionState = "unavailable";
  }
  rendered.declaredFaceSelectionFailed = selectionState === "failed";
  rendered.declaredFaceSelectionUnavailable = selectionState === "unavailable";
  const candidate = { index, pseudoType, ...metadata, rendered, fonts, fontFaces };
  const hasFailedFace = fontFaces.some(
    (face) => face.status === "error" && normalizeFontFamily(face.family) === normalizeFontFamily(primary),
  );
  if (rendered.declaredFaceSelectionUnavailable) return { candidate, priority: "unavailable" };
  if (hasFailedFace && rendered.declaredFaceSelectionFailed && rendered.probeHasRelevantGlyph) return { candidate, priority: "failed" };
  if (hasMixedHanAndLatin(rendered.text)) return { candidate, priority: "mixed" };
  return { candidate, priority: rendered.text ? "other" : "ignore" };
}

async function captureRepresentativeFontNodes(
  specification,
  session,
  executionContextId,
  rootNodeId,
  limit = 3,
  flattenedNodeIds = [],
) {
  const initialSelectorSnapshot = await captureIsolatedFontSelectorSnapshot(session, executionContextId, specification.selector);
  const { nodeIds: documentNodeIds } = await session.send("DOM.querySelectorAll", { nodeId: rootNodeId, selector: specification.selector });
  const nodeIds = [...new Set(flattenedNodeIds)];
  const unavailable = [];
  const failed = [];
  const mixed = [];
  const other = [];
  const initialCdpSubtreeFingerprints = new Map();
  const recordCandidate = ({ candidate, priority }) => {
    if (priority === "unavailable") unavailable.push(candidate);
    else if (priority === "failed") failed.push(candidate);
    else if (priority === "mixed") mixed.push(candidate);
    else if (priority === "other") other.push(candidate);
  };
  for (let index = 0; index < nodeIds.length; index += 1) {
    const nodeId = nodeIds[index];
    const renderedHost = await callIsolatedFontProbe(session, executionContextId, nodeId);
    const { node: describedNode } = await session.send("DOM.describeNode", { nodeId, depth: -1, pierce: true });
    initialCdpSubtreeFingerprints.set(nodeId, cdpFontSubtreeFingerprint(describedNode));
    const nativeTextHost = new Set(["input", "option", "optgroup", "select", "textarea"])
      .has(String(describedNode.localName || "").toLowerCase());
    const shouldProbeNativeHost = nativeTextHost
      && renderedHost.visible
      && renderedHost.fontPaintVisible
      && renderedHost.fontProbeEligible;
    const nativeFontFaces = shouldProbeNativeHost
      ? await captureIsolatedFontFaces(session, executionContextId)
      : [];
    const initialNativeCapture = shouldProbeNativeHost
      ? await captureNativeHostPlatformFonts(session, nodeId, describedNode, renderedHost)
      : { fonts: [], source: "host" };
    const pseudoFontsForHost = [];
    const confirmedPseudoFontsForHost = [];
    let pseudoRunIndex = 0;
    for (const pseudoRecord of descendantPseudoNodeRecords(describedNode, describedNode.nodeId)) {
      const { pseudoNode } = pseudoRecord;
      if (!["after", "before"].includes(pseudoNode.pseudoType)) continue;
      const pseudoFontFaces = await captureIsolatedFontFaces(session, executionContextId);
      let pseudoRendered = await callIsolatedFontProbe(session, executionContextId, pseudoNode.nodeId);
      const { fonts: pseudoFonts } = await session.send("CSS.getPlatformFontsForNode", { nodeId: pseudoNode.nodeId });
      const confirmedPseudo = await callIsolatedFontProbe(session, executionContextId, pseudoNode.nodeId);
      const { fonts: confirmedPseudoFonts } = await session.send("CSS.getPlatformFontsForNode", { nodeId: pseudoNode.nodeId });
      const confirmedPseudoFontFaces = await captureIsolatedFontFaces(session, executionContextId);
      if (!pseudoRecord.descendant) {
        pseudoFontsForHost.push(...pseudoFonts);
        confirmedPseudoFontsForHost.push(...confirmedPseudoFonts);
      }
      if (!pseudoRendered.visible || !pseudoRendered.fontPaintVisible) continue;
      if (!pseudoFonts.some((font) => Number(font.glyphCount) > 0)) continue;
      if (pseudoRendered.probeTextComplete && !pseudoRendered.probeHasRelevantGlyph) continue;
      pseudoRendered.fontProbeStable = stableFontProbeSignature(pseudoRendered) === stableFontProbeSignature(confirmedPseudo);
      pseudoRendered.fontInventoryStable = stableFontFaceInventorySignature(pseudoFontFaces) === stableFontFaceInventorySignature(confirmedPseudoFontFaces);
      pseudoRendered.platformFontsStable = stablePlatformFontSignature(pseudoFonts) === stablePlatformFontSignature(confirmedPseudoFonts);
      pseudoRendered.browserGeneratedTextUnavailable = false;
      pseudoRendered.pseudoTextMappingUnavailable = false;
      pseudoRendered.probeSourceTextEmpty = false;
      pseudoRendered.probeHasRelevantGlyph = true;
      pseudoRendered.text = "[generated content]";
      delete pseudoRendered.fontProbeEligible;
      delete pseudoRendered.pseudoBeforeContent;
      delete pseudoRendered.pseudoAfterContent;
      delete pseudoRendered.visible;
      recordCandidate(finalizeFontCandidate(
        index,
        pseudoRendered,
        pseudoFonts,
        pseudoFontFaces,
        pseudoNode.pseudoType,
        { source: "pseudo", textRunIndex: pseudoRunIndex, textNodeCount: 1, pseudoDescendant: pseudoRecord.descendant },
      ));
      pseudoRunIndex += 1;
    }
    if (shouldProbeNativeHost) {
      let rendered = renderedHost;
      const confirmed = await callIsolatedFontProbe(session, executionContextId, nodeId);
      const confirmedNativeCapture = await captureNativeHostPlatformFonts(
        session,
        nodeId,
        describedNode,
        confirmed,
      );
      const confirmedFontFaces = await captureIsolatedFontFaces(session, executionContextId);
      const fonts = subtractPlatformFonts(initialNativeCapture.fonts, pseudoFontsForHost);
      const confirmedFonts = subtractPlatformFonts(confirmedNativeCapture.fonts, confirmedPseudoFontsForHost);
      const browserGeneratedTextUnavailable = rendered.probeSourceTextEmpty
        && fonts.some((font) => Number(font.glyphCount) > 0);
      rendered.fontProbeStable = stableFontProbeSignature(rendered) === stableFontProbeSignature(confirmed);
      rendered.fontInventoryStable = stableFontFaceInventorySignature(nativeFontFaces) === stableFontFaceInventorySignature(confirmedFontFaces);
      rendered.platformFontsStable = initialNativeCapture.source === confirmedNativeCapture.source
        && stablePlatformFontSignature(fonts) === stablePlatformFontSignature(confirmedFonts);
      rendered.browserGeneratedTextUnavailable = browserGeneratedTextUnavailable;
      rendered.pseudoTextMappingUnavailable = false;
      if (browserGeneratedTextUnavailable) rendered.text = "[browser-generated control label unavailable]";
      delete rendered.fontProbeEligible;
      delete rendered.pseudoBeforeContent;
      delete rendered.pseudoAfterContent;
      delete rendered.visible;
      recordCandidate(finalizeFontCandidate(
        index,
        rendered,
        fonts,
        nativeFontFaces,
        null,
        { source: "native-control", textRunIndex: 0, textNodeCount: 1 },
      ));
    }
    if (!nativeTextHost) {
      const textGroups = [];
      let activeTextGroup = null;
      for (const record of descendantTextNodeRecords(describedNode)) {
        const probe = await callIsolatedFontProbe(session, executionContextId, record.nodeId);
        if (!probe.visible || !probe.fontPaintVisible || !probe.fontProbeEligible || probe.probeSourceTextEmpty) {
          activeTextGroup = null;
          continue;
        }
        const signature = stableFontTextRunGroupSignature(probe);
        const previousRecord = activeTextGroup?.records.at(-1);
        if (
          activeTextGroup?.signature === signature
          && previousRecord?.parentNodeId === record.parentNodeId
          && record.childIndex === previousRecord.childIndex + 1
        ) {
          activeTextGroup.records.push({ ...record, probe });
        }
        else {
          activeTextGroup = { signature, records: [{ ...record, probe }] };
          textGroups.push(activeTextGroup);
        }
      }
      let textRunIndex = 0;
      for (const { signature: groupSignature, records } of textGroups) {
        const sourceText = records.map((record) => record.text).join("");
        const fontFaces = await captureIsolatedFontFaces(session, executionContextId);
        const initialMemberProbes = await Promise.all(records.map(
          (record) => callIsolatedFontProbe(session, executionContextId, record.nodeId),
        ));
        let rendered = await callIsolatedFontProbe(session, executionContextId, records[0].nodeId, sourceText);
        const fonts = await captureTextRecordPlatformFonts(session, records);
        const confirmedMemberProbes = await Promise.all(records.map(
          (record) => callIsolatedFontProbe(session, executionContextId, record.nodeId),
        ));
        const confirmed = await callIsolatedFontProbe(session, executionContextId, records[0].nodeId, sourceText);
        const confirmedFonts = await captureTextRecordPlatformFonts(session, records);
        const confirmedFontFaces = await captureIsolatedFontFaces(session, executionContextId);
        rendered.fontProbeStable = stableFontTextRunGroupSignature(rendered) === groupSignature
          && stableFontProbeSignature(rendered) === stableFontProbeSignature(confirmed)
          && initialMemberProbes.every((probe, memberIndex) => (
            stableFontTextRunGroupSignature(probe) === groupSignature
            && stableFontProbeSignature(probe) === stableFontProbeSignature(confirmedMemberProbes[memberIndex])
          ));
        rendered.fontInventoryStable = stableFontFaceInventorySignature(fontFaces) === stableFontFaceInventorySignature(confirmedFontFaces);
        rendered.platformFontsStable = stablePlatformFontSignature(fonts) === stablePlatformFontSignature(confirmedFonts);
        rendered.browserGeneratedTextUnavailable = false;
        rendered.pseudoTextMappingUnavailable = false;
        delete rendered.fontProbeEligible;
        delete rendered.pseudoBeforeContent;
        delete rendered.pseudoAfterContent;
        delete rendered.visible;
        recordCandidate(finalizeFontCandidate(
          index,
          rendered,
          fonts,
          fontFaces,
          null,
          { source: "dom-text", textRunIndex, textNodeCount: records.length },
        ));
        textRunIndex += 1;
      }
    }
  }
  const finalSelectorSnapshot = await captureIsolatedFontSelectorSnapshot(session, executionContextId, specification.selector);
  const { nodeIds: confirmedNodeIds } = await session.send("DOM.querySelectorAll", { nodeId: rootNodeId, selector: specification.selector });
  const cdpSubtreeStable = await Promise.all(nodeIds.map(async (nodeId) => {
    const { node } = await session.send("DOM.describeNode", { nodeId, depth: -1, pierce: true });
    return initialCdpSubtreeFingerprints.get(nodeId) === cdpFontSubtreeFingerprint(node);
  }));
  if (
    initialSelectorSnapshot !== finalSelectorSnapshot
    || documentNodeIds.length !== confirmedNodeIds.length
    || documentNodeIds.some((nodeId, index) => nodeId !== confirmedNodeIds[index])
    || cdpSubtreeStable.some((stable) => !stable)
  ) {
    throw new Error(`font selector state changed during capture: ${specification.role}`);
  }
  return [...unavailable.slice(0, 1), ...failed, ...mixed, ...other].slice(0, limit);
}

function stableRepresentativeFontNodesSignature(candidates) {
  const normalized = (candidates || []).map((candidate) => ({
    ...candidate,
    fonts: [...(candidate.fonts || [])].sort((left, right) => (
      JSON.stringify(left).localeCompare(JSON.stringify(right), "en-US")
    )),
    fontFaces: [...(candidate.fontFaces || [])].sort((left, right) => (
      JSON.stringify(left).localeCompare(JSON.stringify(right), "en-US")
    )),
  }));
  return crypto.createHash("sha256").update(JSON.stringify(normalized)).digest("hex");
}

async function representativeFontNodes(
  specification,
  session,
  executionContextId,
  rootNodeId,
  limit = 3,
  flattenedNodeIds = [],
) {
  const initial = await captureRepresentativeFontNodes(
    specification,
    session,
    executionContextId,
    rootNodeId,
    limit,
    flattenedNodeIds,
  );
  const confirmed = await captureRepresentativeFontNodes(
    specification,
    session,
    executionContextId,
    rootNodeId,
    limit,
    flattenedNodeIds,
  );
  if (stableRepresentativeFontNodesSignature(initial) !== stableRepresentativeFontNodesSignature(confirmed)) {
    throw new Error(`font role evidence changed during collection: ${specification.role}`);
  }
  return confirmed;
}

async function collectFontEvidence(context, page) {
  let session;
  let roles = [];
  try {
    session = await context.newCDPSession(page);
    await session.send("Page.enable");
    await session.send("Runtime.enable");
    await session.send("DOM.enable");
    await session.send("CSS.enable");
    const cdpAnimations = new Map();
    session.on("Animation.animationStarted", ({ animation }) => cdpAnimations.set(animation.id, animation));
    session.on("Animation.animationUpdated", ({ animation }) => cdpAnimations.set(animation.id, animation));
    session.on("Animation.animationCanceled", ({ id }) => cdpAnimations.delete(id));
    await session.send("Animation.enable");
    const { frameTree } = await session.send("Page.getFrameTree");
    const { executionContextId } = await session.send("Page.createIsolatedWorld", {
      frameId: frameTree.frame.id,
      worldName: "wow-font-evidence",
      grantUniversalAccess: false,
    });
    const { root } = await session.send("DOM.getDocument", { depth: -1, pierce: true });
    let backendParentMap = cdpBackendParentMap(root);
    let backendNodeMap = cdpBackendNodeMap(root);
    const frontendBackendMap = new Map(
      [...backendNodeMap.values()].filter(({ nodeId }) => nodeId).map(({ nodeId, backendNodeId }) => [nodeId, backendNodeId]),
    );
    const initialActiveFontAnimations = await captureIsolatedActiveFontAnimations(
      session,
      executionContextId,
      FONT_ROLE_SELECTORS,
    );
    if (initialActiveFontAnimations.length) {
      throw new Error("active rendered-text animation prevented stable evidence");
    }
    const initialFontInventorySignature = stableFontFaceInventorySignature(
      await captureIsolatedFontFaces(session, executionContextId),
    );
    const initialRoleStates = new Map();
    let roleBackendNodeIds = new Set();
    const flattenedRoleNodeIds = new Map();
    for (const specification of FONT_ROLE_SELECTORS) {
      const snapshot = await captureIsolatedFontSelectorSnapshot(session, executionContextId, specification.selector);
      const { nodeIds } = await session.send("DOM.querySelectorAll", { nodeId: root.nodeId, selector: specification.selector });
      const flattenedNodes = await renderedCdpFontRoleNodes(
        session,
        executionContextId,
        specification,
        backendParentMap,
        backendNodeMap,
      );
      const backendNodeIds = flattenedNodes.map(({ backendNodeId }) => backendNodeId).sort((left, right) => left - right);
      const documentBackendNodeIds = nodeIds.map((nodeId) => frontendBackendMap.get(nodeId)).filter(Boolean);
      flattenedRoleNodeIds.set(specification.role, flattenedNodes.map(({ nodeId }) => nodeId));
      for (const backendNodeId of backendNodeIds) roleBackendNodeIds.add(backendNodeId);
      initialRoleStates.set(specification.role, { snapshot, documentBackendNodeIds, backendNodeIds });
    }
    if ((await activeIntersectingCdpAnimations(
      session,
      executionContextId,
      cdpAnimations,
      backendParentMap,
      backendNodeMap,
      roleBackendNodeIds,
    )).length) {
      throw new Error("active rendered-text animation prevented stable evidence");
    }
    for (const specification of FONT_ROLE_SELECTORS) {
      for (const candidate of await representativeFontNodes(
        specification,
        session,
        executionContextId,
        root.nodeId,
        3,
        flattenedRoleNodeIds.get(specification.role),
      )) {
        const parsedPrimary = parseFirstDeclaredFontFamily(candidate.rendered.declaredFamily);
        const matchingFaces = candidate.fontFaces.filter(
          (face) => normalizeFontFamily(face.family) === normalizeFontFamily(parsedPrimary.family),
        );
        const renderedEvidence = candidate.rendered;
        const pseudoSelector = candidate.pseudoType
          ? specification.selector.split(",").map((selector) => (
            `${selector.trim()}${candidate.pseudoDescendant ? " " : ""}::${candidate.pseudoType}`
          )).join(", ")
          : specification.selector;
        const role = {
          ...specification,
          role: candidate.pseudoType ? `${specification.role}-pseudo` : specification.role,
          selector: pseudoSelector,
          sampleIndex: candidate.index,
          pseudoType: candidate.pseudoType,
          pseudoDescendant: Boolean(candidate.pseudoDescendant),
          source: candidate.source,
          textRunIndex: candidate.textRunIndex,
          textNodeCount: candidate.textNodeCount,
          ...renderedEvidence,
          declaredPrimary: parsedPrimary.family,
          declaredPrimaryQuoted: parsedPrimary.quoted,
          fontFaces: matchingFaces.map(({ evidenceIdentity, ...face }) => face),
          actualFonts: candidate.fonts,
        };
        roles.push({ ...role, classification: classifyPrimaryFontUsage(role) });
      }
    }
    const { root: confirmedRoot } = await session.send("DOM.getDocument", { depth: -1, pierce: true });
    const confirmedBackendParentMap = cdpBackendParentMap(confirmedRoot);
    const confirmedBackendNodeMap = cdpBackendNodeMap(confirmedRoot);
    const confirmedFrontendBackendMap = new Map(
      [...confirmedBackendNodeMap.values()].filter(({ nodeId }) => nodeId).map(({ nodeId, backendNodeId }) => [nodeId, backendNodeId]),
    );
    const confirmedRoleBackendNodeIds = new Set();
    for (const specification of FONT_ROLE_SELECTORS) {
      const initial = initialRoleStates.get(specification.role);
      const snapshot = await captureIsolatedFontSelectorSnapshot(session, executionContextId, specification.selector);
      const { nodeIds } = await session.send("DOM.querySelectorAll", { nodeId: confirmedRoot.nodeId, selector: specification.selector });
      const documentBackendNodeIds = nodeIds.map(
        (nodeId) => confirmedFrontendBackendMap.get(nodeId),
      ).filter(Boolean);
      const backendNodeIds = (await renderedCdpFontRoleNodes(
        session,
        executionContextId,
        specification,
        confirmedBackendParentMap,
        confirmedBackendNodeMap,
      )).map(({ backendNodeId }) => backendNodeId).sort((left, right) => left - right);
      for (const backendNodeId of backendNodeIds) confirmedRoleBackendNodeIds.add(backendNodeId);
      if (
        !initial
        || initial.snapshot !== snapshot
        || initial.documentBackendNodeIds.length !== documentBackendNodeIds.length
        || initial.documentBackendNodeIds.some(
          (backendNodeId, index) => backendNodeId !== documentBackendNodeIds[index],
        )
        || initial.backendNodeIds.length !== backendNodeIds.length
        || initial.backendNodeIds.some((backendNodeId, index) => backendNodeId !== backendNodeIds[index])
      ) {
        throw new Error(`font role state changed during collection: ${specification.role}`);
      }
    }
    backendParentMap = confirmedBackendParentMap;
    backendNodeMap = confirmedBackendNodeMap;
    roleBackendNodeIds = confirmedRoleBackendNodeIds;
    const finalActiveFontAnimations = await captureIsolatedActiveFontAnimations(
      session,
      executionContextId,
      FONT_ROLE_SELECTORS,
    );
    if (finalActiveFontAnimations.length) {
      throw new Error("active rendered-text animation prevented stable evidence");
    }
    if ((await activeIntersectingCdpAnimations(
      session,
      executionContextId,
      cdpAnimations,
      backendParentMap,
      backendNodeMap,
      roleBackendNodeIds,
    )).length) {
      throw new Error("active rendered-text animation prevented stable evidence");
    }
    const finalFontInventorySignature = stableFontFaceInventorySignature(
      await captureIsolatedFontFaces(session, executionContextId),
    );
    if (initialFontInventorySignature !== finalFontInventorySignature) {
      throw new Error("font face inventory changed during collection");
    }
    const resolvedPlatformRole = roles.some((role) => (role.actualFonts || []).some((font) => Number(font.glyphCount) > 0));
    if (
      !roles.length
      || !resolvedPlatformRole
      || roles.some((role) => ["evidence_unavailable", "platform_fonts_unavailable"].includes(role.classification))
    ) {
      throw new Error("font evidence did not resolve a rendered text role");
    }
    return {
      status: "captured",
      roles,
      primaryMismatches: roles.filter(primaryFontMismatch),
    };
  } catch (error) {
    return {
      status: "unavailable",
      error: String(error.message || error).slice(0, 240),
      roles,
      primaryMismatches: roles.filter(primaryFontMismatch),
    };
  } finally {
    if (session) await session.detach().catch(() => {});
  }
}

function assertFontEvidenceComplete(evidence, identity = "unknown") {
  if (evidence?.status !== "captured" || !Array.isArray(evidence.roles) || !evidence.roles.length) {
    const unresolved = (evidence?.roles || [])
      .filter((role) => ["evidence_unavailable", "platform_fonts_unavailable"].includes(role.classification))
      .slice(0, 3)
      .map((role) => `${role.role}:${role.declaredPrimary}:${role.fontWeight}`)
      .join(",");
    throw new Error(
      `font evidence unavailable at ${identity}: ${String(evidence?.error || "no rendered roles")}${unresolved ? ` (${unresolved})` : ""}`,
    );
  }
}

async function captureFontEvidenceForAudit(context, page, identity) {
  let evidence;
  try {
    evidence = await collectFontEvidence(context, page);
    assertFontEvidenceComplete(evidence, identity);
    return evidence;
  } catch (error) {
    return {
      ...(evidence || {}),
      status: "unavailable",
      error: String(error.message || error).slice(0, 240),
      roles: Array.isArray(evidence?.roles) ? evidence.roles : [],
      primaryMismatches: [],
    };
  }
}

function matchesAllowedNetworkOrigin(value, allowedOrigin) {
  try {
    const parsed = new URL(value);
    if (["data:", "about:"].includes(parsed.protocol)) return true;
    if (parsed.protocol === "ws:") parsed.protocol = "http:";
    if (parsed.protocol === "wss:") parsed.protocol = "https:";
    return parsed.origin === allowedOrigin;
  } catch {
    return false;
  }
}

async function installExactOriginRoutes(context, allowedOrigin, externalRequests) {
  await context.route("**/*", async (route) => {
    const requestUrl = route.request().url();
    if (!matchesAllowedNetworkOrigin(requestUrl, allowedOrigin)) {
      externalRequests.push(requestUrl);
      return route.abort("blockedbyclient");
    }
    const parsed = new URL(requestUrl);
    if (parsed.pathname.endsWith("/favicon.ico")) return route.fulfill({ status: 204, body: "" });
    return route.continue();
  });
  await context.routeWebSocket("**/*", async (webSocket) => {
    const requestUrl = webSocket.url();
    if (!matchesAllowedNetworkOrigin(requestUrl, allowedOrigin)) {
      externalRequests.push(requestUrl);
      await webSocket.close({ code: 1008, reason: "Blocked by evaluator origin policy" });
      return;
    }
    webSocket.connectToServer();
  });
}

function hasUnexplainedEnglish(text) {
  const normalized = String(text || "").trim().replace(/\s+/g, " ");
  if (!normalized || new RegExp(LOCALE_RULES.namedCurrencyValue, "u").test(normalized)) return false;
  const stripped = normalized
    .replace(new RegExp(LOCALE_RULES.explainedTerm, "gu"), "")
    .replace(new RegExp(LOCALE_RULES.identifier, "gu"), "");
  return /[A-Za-z]{3,}/.test(stripped);
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

async function settleRenderedStateInIsolatedWorld(frameDurationMs) {
  await new Promise((resolve) => requestAnimationFrame(resolve));
  const shortAnimations = Document.prototype.getAnimations.call(document).filter((animation) => {
      const timing = animation.effect?.getComputedTiming();
      const currentTime = Number(animation.currentTime);
      const endTime = Number(timing?.endTime);
      const remainingTime = endTime - Math.max(0, currentTime);
      const playbackRate = Number(animation.playbackRate);
      const totalWallTime = endTime / playbackRate;
      const remainingWallTime = remainingTime / playbackRate;
      return animation.playState === "running"
        && Number.isFinite(playbackRate)
        && playbackRate > 0
        && Number.isFinite(endTime)
        && Number.isFinite(remainingTime)
        && Number.isFinite(totalWallTime)
        && Number.isFinite(remainingWallTime)
        && endTime <= frameDurationMs
        && remainingTime <= frameDurationMs
        && totalWallTime <= frameDurationMs
        && remainingWallTime <= frameDurationMs;
  });
  const finishedGetter = Object.getOwnPropertyDescriptor(Animation.prototype, "finished")?.get;
  if (typeof finishedGetter !== "function") throw new Error("native animation.finished unavailable");
  await Promise.allSettled(shortAnimations.map((animation) => finishedGetter.call(animation)));
  await new Promise((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(resolve));
  });
}

async function waitForRenderedStateToSettle(page) {
  const singleFrameDurationMs = 1000 / 60;
  const session = await page.context().newCDPSession(page);
  await session.send("Page.enable");
  await session.send("Runtime.enable");
  const { frameTree } = await session.send("Page.getFrameTree");
  const { executionContextId } = await session.send("Page.createIsolatedWorld", {
    frameId: frameTree.frame.id,
    worldName: "wow-render-settle",
    grantUniversalAccess: false,
  });
  const settleAttempt = session.send("Runtime.evaluate", {
    contextId: executionContextId,
    expression: `(${settleRenderedStateInIsolatedWorld.toString()})(${JSON.stringify(singleFrameDurationMs)})`,
    returnByValue: true,
    awaitPromise: true,
    silent: true,
  });
  let deadline;
  try {
    const { exceptionDetails } = await Promise.race([
      settleAttempt,
      new Promise((_, reject) => {
        deadline = setTimeout(() => {
          reject(new Error("rendered state did not settle within eight frame budgets"));
        }, singleFrameDurationMs * 8);
      }),
    ]);
    if (exceptionDetails) {
      throw new Error(`isolated rendered-state settle failed: ${exceptionDetails.text || "unknown error"}`);
    }
  } finally {
    clearTimeout(deadline);
    await session.detach().catch(() => {});
  }
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
      const step = await firstVisible(page, '[data-eval="booking-step"]');
      const beforeStep = (await step.innerText()).trim();
      await (await firstVisible(page, '[data-eval="continue-action"]')).click();
      await page.waitForTimeout(100);
      evidence.errorVisible = await page.locator('[data-eval="form-error"]').isVisible();
      await page.locator('[data-eval="item-name"]').fill("二十年以上的手提收音機，旋鈕鬆脫且偶爾沒有聲音");
      await (await firstVisible(page, '[data-eval="continue-action"]')).click();
      await page.waitForTimeout(100);
      const afterStep = await firstVisible(page, '[data-eval="booking-step"]');
      evidence.step = await afterStep.getAttribute("data-step");
      evidence.stepChanged = beforeStep !== (await afterStep.innerText()).trim();
      evidence.confirmationVisible = await page.locator('[data-eval="confirmation-summary"]').isVisible();
      const transitioned = evidence.stepChanged || evidence.confirmationVisible || ["2", "3"].includes(evidence.step);
      if (!evidence.errorVisible || !transitioned) evidence.failures.push("repair_intake_validation_or_transition_failed");
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
      const workspace = page.locator('[data-eval="royalty-workspace"]');
      const previous = page.locator('[data-period-value="previous"]');
      const beforePeriod = await workspace.getAttribute("data-period");
      const beforeText = (await workspace.innerText()).trim();
      const beforePressed = await previous.getAttribute("aria-pressed");
      await previous.click();
      await page.waitForTimeout(100);
      evidence.afterPeriod = await workspace.getAttribute("data-period");
      evidence.periodContentChanged = beforeText !== (await workspace.innerText()).trim();
      evidence.periodControlChanged = beforePressed !== await previous.getAttribute("aria-pressed");
      await (await firstVisible(page, '[data-eval="chart-mark"]')).click();
      await page.waitForTimeout(100);
      evidence.tooltipVisible = await page.locator('[data-eval="chart-tooltip"]').isVisible();
      if (beforePeriod === evidence.afterPeriod && !evidence.periodContentChanged && !evidence.periodControlChanged) {
        evidence.failures.push("royalty_period_switch_failed");
      }
      if (!evidence.tooltipVisible) evidence.failures.push("royalty_tooltip_failed");
    } else if (caseId === "packaging-configurator-v6") {
      const inputs = page.locator('[data-eval="size-option"] input[type="radio"]:enabled');
      const inputCount = await inputs.count();
      if (!inputCount) throw new Error("no enabled size radio inside data-eval=size-option");
      let input = inputs.first();
      for (let index = 0; index < inputCount; index += 1) {
        if (!(await inputs.nth(index).isChecked())) {
          input = inputs.nth(index);
          break;
        }
      }
      const label = input.locator("xpath=ancestor::label[1]");
      if ((await label.count()) && await label.isVisible()) await label.click();
      else await input.check();
      evidence.sizeSelected = await input.isChecked();
      evidence.summaryVisible = await page.locator('[data-eval="config-summary"]').isVisible();
      if (!evidence.sizeSelected || !evidence.summaryVisible) evidence.failures.push("packaging_summary_failed");
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
      await firstRow.locator('[data-eval="compare-a-action"]').click();
      if (plan.usesCaseNavigation) {
        await page.locator('[data-eval="next-proposal"]').click();
        await page.waitForTimeout(100);
      }
      await secondRow.locator('[data-eval="shortlist-action"]').click();
      await secondRow.locator('[data-eval="compare-b-action"]').click();
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
  if ((result.textScale?.undersizedReadableText || []).length) issues.push("readable_text_below_12px");
  if ((result.narrowTextColumns || []).length) issues.push("content_column_too_narrow");
  if ((result.bodyFlow?.forcedLineBreaks || []).length) issues.push("forced_body_line_break");
  if ((result.bodyFlow?.nonWrappingProse || []).length) issues.push("body_copy_normal_wrap_disabled");
  if ((result.bodyFlow?.underfilledProseBlocks || []).length) issues.push("prose_track_underfilled");
  if ((result.headingFlow?.compressedCjkHeadings || []).length) issues.push("cjk_heading_overcompressed");
  if ((result.headingFlow?.orphanedCjkHeadingLines || []).length) issues.push("cjk_heading_orphan_line");
  if ((result.headingFlow?.underfilledWideHeadings || []).length) issues.push("wide_heading_track_underfilled");
  if ((result.layoutFlow?.domOrderReversals || []).length) issues.push("visual_order_reverses_dom_flow");
  if ((result.layoutFlow?.displacedIntroCopy || []).length) issues.push("intro_copy_displaced_to_right_track");
  if ((result.layoutFlow?.unfilledColumnVoids || []).length) issues.push("layout_column_void");
  if ((result.localeFlow?.untranslatedInterfaceCopy || []).length) issues.push("zh_hant_untranslated_interface_copy");
  if (!result.fontEvidence || result.fontEvidence.status !== "captured") issues.push("font_evidence_unavailable");
  if (result.fontEvidence?.status === "captured" && (result.fontEvidence.primaryMismatches || []).length) {
    issues.push("declared_primary_font_not_rendered");
  }
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
    serviceWorkers: "block",
  };
  if (viewport.userAgent) contextOptions.userAgent = viewport.userAgent;
  const targetUrl = new URL(pageName, target.url).href;
  const origin = new URL(target.url).origin;
  const consoleErrors = [];
  const externalRequests = [];
  const badResponses = [];
  const context = await browser.newContext(contextOptions);
  await installExactOriginRoutes(context, origin, externalRequests);
  const page = await context.newPage();

  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("response", (response) => {
    if (response.status() >= 400 && !response.url().endsWith("/favicon.ico")) {
      badResponses.push({ status: response.status(), url: response.url() });
    }
  });
  await page.goto(targetUrl, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(250);
  await page.evaluate(() => document.fonts.ready);
  const interaction = state === "interaction"
    ? await runCaseInteraction(page, target.caseId, viewport)
    : { attempted: false, failures: [] };
  await page.evaluate(() => document.fonts.ready);
  if (state === "interaction") await waitForRenderedStateToSettle(page);

  const measured = await page.evaluate(({ caseId, viewportName, requiredPages, localeRules, productTextRootSelector }) => {
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
    const textLineRects = (node) => {
      const range = document.createRange();
      range.selectNodeContents(node);
      const lines = new Map();
      for (const rect of [...range.getClientRects()].filter((item) => item.width > 0.5 && item.height > 0.5)) {
        const key = Math.round(rect.top);
        const current = lines.get(key) || { left: rect.left, right: rect.right };
        current.left = Math.min(current.left, rect.left);
        current.right = Math.max(current.right, rect.right);
        lines.set(key, current);
      }
      return [...lines.values()].map((line) => ({ ...line, width: line.right - line.left }));
    };
    const textLineFragments = (node) => {
      const lines = new Map();
      const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        const textNode = walker.currentNode;
        let offset = 0;
        for (const character of textNode.data) {
          const end = offset + character.length;
          const range = document.createRange();
          range.setStart(textNode, offset);
          range.setEnd(textNode, end);
          const rect = [...range.getClientRects()].find((item) => item.width > 0.1 && item.height > 0.1);
          if (rect) {
            const key = Math.round(rect.top);
            const current = lines.get(key) || { top: rect.top, left: rect.left, right: rect.right, text: "" };
            current.left = Math.min(current.left, rect.left);
            current.right = Math.max(current.right, rect.right);
            current.text += character;
            lines.set(key, current);
          }
          offset = end;
        }
      }
      return [...lines.values()]
        .sort((a, b) => a.top - b.top)
        .map((line) => ({ ...line, text: line.text.trim(), width: line.right - line.left }));
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
    const activeModal = document.querySelector('dialog[open], [role="dialog"][aria-modal="true"]');
    const isolatedBehindModal = (node) => Boolean(
      activeModal
      && !activeModal.contains(node)
      && node.closest('[inert], [aria-hidden="true"]')
    );
    const productTextNodes = (selector) => [...new Set(
      [...document.querySelectorAll(productTextRootSelector)]
        .filter((root) => visible(root) && !isolatedBehindModal(root))
        .flatMap((root) => [...root.querySelectorAll(selector)]),
    )].filter((node) => visible(node) && !isolatedBehindModal(node));
    const flowContainer = (node) => node.parentElement
      || node.closest("header, .masthead, .hero, .banner, .panel, section, article");
    const hasTaskBearingRightPeer = (node, container) => {
      if (!container) return false;
      const rect = node.getBoundingClientRect();
      return [...container.querySelectorAll("nav, aside, button, input, select, textarea, [role='button'], [role='group'], [data-status], [data-eval]")]
        .filter((peer) => peer !== node && !node.contains(peer) && visible(peer))
        .some((peer) => {
          const peerRect = peer.getBoundingClientRect();
          const verticallyRelevant = peerRect.bottom > rect.top - 24 && peerRect.top < rect.bottom + 24;
          return verticallyRelevant && peerRect.left > rect.left + rect.width * 0.72 && peerRect.width >= 96;
        });
    };

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

    const criticalNodes = [...document.querySelectorAll("h1, h2, h3, button, [role='button']")]
      .filter(visibleInViewport)
      .filter((node) => node.textContent.trim() && !isolatedBehindModal(node));
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

    const readableNodes = productTextNodes("p, li")
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
      const measureLimit = cjkDominant ? 48 : 90;
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
    const undersizedReadableText = readableNodes
      .map((node) => ({
        text: node.textContent.trim().replace(/\s+/g, " ").slice(0, 80),
        fontSize: Number(Number.parseFloat(getComputedStyle(node).fontSize).toFixed(2)),
        hook: node.getAttribute("data-eval"),
      }))
      .filter((item) => Number.isFinite(item.fontSize) && item.fontSize < 12)
      .slice(0, 20);
    const textScale = { undersizedReadableText };

    const narrowTextColumns = productTextNodes("p, li")
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

    const bodyFlowNodes = productTextNodes("p, li")
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
    const underfilledProseBlocks = [...new Set([
      ...document.querySelectorAll("header p"),
      ...productTextNodes("p"),
    ])]
      .filter(visible)
      .filter((node) => node.textContent.trim().length >= 40)
      .map((node) => {
        const container = flowContainer(node);
        const rect = node.getBoundingClientRect();
        const containerRect = container?.getBoundingClientRect() || rect;
        const text = node.textContent.trim().replace(/\s+/g, " ");
        const characters = [...text];
        const hanCount = characters.filter((character) => /\p{Script=Han}/u.test(character)).length;
        return {
          text: text.slice(0, 80),
          cjkDominant: hanCount / Math.max(characters.length, 1) >= 0.35,
          trackRatio: Number((rect.width / Math.max(containerRect.width, 1)).toFixed(2)),
          unusedInline: Math.round(containerRect.width - rect.width),
          containerWidth: Math.round(containerRect.width),
          hasTaskPeer: hasTaskBearingRightPeer(node, container),
        };
      })
      .filter((item) => item.cjkDominant && item.containerWidth >= 560 && item.trackRatio < 0.6
        && item.unusedInline > 220 && !item.hasTaskPeer)
      .slice(0, 20);
    const bodyFlow = { forcedLineBreaks, nonWrappingProse, underfilledProseBlocks };

    const compressedCjkHeadings = [...document.querySelectorAll("h1")]
      .filter(visible)
      .map((node) => {
        const style = getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        const parentRect = node.parentElement?.getBoundingClientRect() || rect;
        const fontSize = Number.parseFloat(style.fontSize);
        const text = node.textContent.trim().replace(/\s+/g, " ");
        const characters = [...text];
        const hanCount = characters.filter((character) => /\p{Script=Han}/u.test(character)).length;
        return {
          text: text.slice(0, 80),
          lineCount: textLineCount(node),
          cjkDominant: hanCount / Math.max(characters.length, 1) >= 0.5,
          widthInEms: Number((rect.width / fontSize).toFixed(2)),
          parentSpareInEms: Number(((parentRect.width - rect.width) / fontSize).toFixed(2)),
        };
      })
      .filter((item) => item.cjkDominant && item.lineCount >= 4 && item.widthInEms < 8
        && (item.parentSpareInEms > 1 || item.lineCount >= 5))
      .slice(0, 20);
    const orphanedCjkHeadingLines = [...document.querySelectorAll("h1, h2, h3")]
      .filter(visible)
      .map((node) => {
        const style = getComputedStyle(node);
        const fontSize = Number.parseFloat(style.fontSize);
        const text = node.textContent.trim().replace(/\s+/g, " ");
        const characters = [...text];
        const hanCount = characters.filter((character) => /\p{Script=Han}/u.test(character)).length;
        const lines = textLineFragments(node);
        const meaningfulCount = (value) => [...value].filter((character) => /[\p{Letter}\p{Number}]/u.test(character)).length;
        const lastLine = lines.at(-1) || { text: "", width: 0 };
        const previousLine = lines.at(-2) || { text: "", width: 0 };
        return {
          text: text.slice(0, 80),
          cjkDominant: hanCount / Math.max(characters.length, 1) >= 0.5,
          horizontal: style.writingMode.startsWith("horizontal"),
          characterCount: characters.length,
          lineCount: lines.length,
          lastLineText: lastLine.text.slice(0, 24),
          lastLineMeaningfulCount: meaningfulCount(lastLine.text),
          previousLineMeaningfulCount: meaningfulCount(previousLine.text),
          lastLineWidthInEms: Number((lastLine.width / Math.max(fontSize, 1)).toFixed(2)),
        };
      })
      .filter((item) => item.horizontal && item.cjkDominant && item.characterCount >= 4
        && item.lineCount >= 2 && item.lastLineMeaningfulCount <= 1
        && item.previousLineMeaningfulCount >= 2 && item.lastLineWidthInEms <= 1.8)
      .slice(0, 20);
    const underfilledWideHeadings = [...document.querySelectorAll("h1")]
      .filter(visible)
      .map((node) => {
        const container = flowContainer(node);
        const peerContainer = node.closest("header, .masthead, .hero, .banner, .panel, section, article") || container;
        const containerRect = container?.getBoundingClientRect() || node.getBoundingClientRect();
        const lines = textLineRects(node);
        const text = node.textContent.trim().replace(/\s+/g, " ");
        const characters = [...text];
        const hanCount = characters.filter((character) => /\p{Script=Han}/u.test(character)).length;
        const longestLine = Math.max(0, ...lines.map((line) => line.width));
        return {
          text: text.slice(0, 80),
          cjkDominant: hanCount / Math.max(characters.length, 1) >= 0.5,
          characterCount: characters.length,
          lineCount: lines.length,
          longestLineRatio: Number((longestLine / Math.max(containerRect.width, 1)).toFixed(2)),
          unusedInline: Math.round(containerRect.width - longestLine),
          containerWidth: Math.round(containerRect.width),
          hasTaskPeer: hasTaskBearingRightPeer(node, peerContainer),
        };
      })
      .filter((item) => item.cjkDominant && item.containerWidth >= 760
        && item.characterCount >= 14 && item.lineCount >= 2
        && item.longestLineRatio < 0.6 && item.unusedInline > 280 && !item.hasTaskPeer)
      .slice(0, 20);
    const headingFlow = { compressedCjkHeadings, orphanedCjkHeadingLines, underfilledWideHeadings };

    const domOrderReversals = [];
    for (const root of [...document.querySelectorAll("header")].filter(visible)) {
      const children = [...root.children]
        .filter(visible)
        .filter((node) => !["absolute", "fixed"].includes(getComputedStyle(node).position));
      for (let index = 1; index < children.length; index += 1) {
        const previous = children[index - 1];
        const current = children[index];
        const previousRect = previous.getBoundingClientRect();
        const currentRect = current.getBoundingClientRect();
        const tolerance = Math.max(12, Number.parseFloat(getComputedStyle(current).fontSize) * 0.35);
        if (currentRect.top + tolerance < previousRect.top) {
          domOrderReversals.push({
            header: nameFor(root).slice(0, 60),
            previous: nameFor(previous).slice(0, 60),
            current: nameFor(current).slice(0, 60),
            upwardShift: Math.round(previousRect.top - currentRect.top),
          });
        }
        if (domOrderReversals.length >= 20) break;
      }
      if (domOrderReversals.length >= 20) break;
    }
    const displacedIntroCopy = [...document.querySelectorAll("header p.lede, header p.summary, .masthead p.lede, .masthead p.summary")]
      .filter(visible)
      .map((node) => {
        const container = flowContainer(node);
        const rect = node.getBoundingClientRect();
        const containerRect = container?.getBoundingClientRect() || rect;
        return {
          text: node.textContent.trim().replace(/\s+/g, " ").slice(0, 80),
          startRatio: Number(((rect.left - containerRect.left) / Math.max(containerRect.width, 1)).toFixed(2)),
          containerWidth: Math.round(containerRect.width),
        };
      })
      .filter((item) => item.containerWidth >= 760 && item.startRatio > 0.35)
      .slice(0, 20);
    const unfilledColumnVoids = [];
    const unfilledColumnAdvisories = [];
    const measuredLayoutContainers = new Set();
    const horizontalOverlapRatio = (first, second) => {
      const overlap = Math.max(0, Math.min(first.right, second.right) - Math.max(first.left, second.left));
      return overlap / Math.max(1, Math.min(first.width, second.width));
    };
    const layoutSubjects = [...document.querySelectorAll([
      "main > *", "main section", "main article", "main aside", "main form", "main [data-eval]",
    ].join(", "))]
      .filter(visible)
      .filter((node) => !["absolute", "fixed"].includes(getComputedStyle(node).position));
    for (const subject of layoutSubjects) {
      const parent = subject.parentElement;
      if (!parent || measuredLayoutContainers.has(parent)) continue;
      const parentStyle = getComputedStyle(parent);
      if (!["grid", "inline-grid", "flex", "inline-flex"].includes(parentStyle.display)) continue;
      const parentRect = parent.getBoundingClientRect();
      const subjectRect = subject.getBoundingClientRect();
      if (parentRect.width < 760 || subjectRect.height < 120 || subjectRect.width >= parentRect.width * 0.8) continue;
      const siblings = [...parent.children]
        .filter((node) => node !== subject && visible(node))
        .filter((node) => !["absolute", "fixed"].includes(getComputedStyle(node).position));
      const sidePeers = siblings.filter((node) => {
        const rect = node.getBoundingClientRect();
        return horizontalOverlapRatio(subjectRect, rect) <= 0.2
          && rect.top <= subjectRect.bottom + 64
          && rect.bottom > subjectRect.bottom;
      });
      if (!sidePeers.length) continue;
      const peerRect = sidePeers
        .map((node) => node.getBoundingClientRect())
        .sort((first, second) => second.bottom - first.bottom)[0];
      const hasLowerFiller = siblings.some((node) => {
        const rect = node.getBoundingClientRect();
        return horizontalOverlapRatio(subjectRect, rect) >= 0.45
          && rect.top >= subjectRect.bottom - 24
          && rect.bottom >= peerRect.bottom - 24;
      });
      const voidHeight = peerRect.bottom - subjectRect.bottom;
      const threshold = Math.max(240, window.innerHeight * 0.3);
      if (hasLowerFiller || voidHeight <= threshold) continue;
      const contentNodes = [...subject.querySelectorAll(
        "h1, h2, h3, h4, h5, h6, p, li, table, form, figure, img, [data-eval]",
      )].filter(visible);
      const interactiveNodes = [...subject.querySelectorAll(
        "button, a, input, select, textarea, summary, [role='button']",
      )].filter(visible);
      const subjectText = (subject.innerText || subject.textContent || "").trim().replace(/\s+/g, " ");
      // A tall neighbour is not enough to prove a broken composition: dashboards,
      // reading layouts, and detail panes often have intentionally independent
      // heights. Escalate only when the shorter column is genuinely sparse; keep
      // dense independent columns as visual observations instead of repair blockers.
      const sparseContent = contentNodes.length <= 2
        && interactiveNodes.length <= 2
        && [...subjectText].length <= 160;
      if (!sparseContent) {
        unfilledColumnAdvisories.push({
          target: nameFor(subject).slice(0, 80),
          voidHeight: Math.round(voidHeight),
          threshold: Math.round(threshold),
          subjectHeight: Math.round(subjectRect.height),
          peerHeight: Math.round(peerRect.height),
          parentDisplay: parentStyle.display,
          parentWidth: Math.round(parentRect.width),
          confidence: "dense-independent-column",
          contentNodes: contentNodes.length,
          interactiveNodes: interactiveNodes.length,
          textLength: [...subjectText].length,
        });
        if (unfilledColumnAdvisories.length >= 20) break;
        continue;
      }
      measuredLayoutContainers.add(parent);
      unfilledColumnVoids.push({
        target: nameFor(subject).slice(0, 80),
        voidHeight: Math.round(voidHeight),
        threshold: Math.round(threshold),
        subjectHeight: Math.round(subjectRect.height),
        peerHeight: Math.round(peerRect.height),
        parentDisplay: parentStyle.display,
        parentWidth: Math.round(parentRect.width),
        confidence: "sparse-column",
        contentNodes: contentNodes.length,
        interactiveNodes: interactiveNodes.length,
        textLength: [...subjectText].length,
      });
      if (unfilledColumnVoids.length >= 20) break;
    }
    const layoutFlow = {
      domOrderReversals,
      displacedIntroCopy,
      unfilledColumnVoids,
      unfilledColumnAdvisories,
    };

    const localeCandidates = [...document.querySelectorAll([
      "button", "label", "summary", "nav a", "[role='button']",
      ".eyebrow", ".kicker", ".pill", ".flag", ".chip", ".status-chip",
      ".section__eyebrow", ".brand__eyebrow", ".media-fallback__label",
      ".lede", ".summary", ".subhead", ".summary-note", ".fallback-note p",
    ].join(", "))].filter(visible);
    const untranslatedInterfaceCopy = localeCandidates
      .map((node) => {
        const text = (node.innerText || node.textContent || node.getAttribute("aria-label") || "").trim().replace(/\s+/g, " ");
        const namedCurrencyValue = new RegExp(localeRules.namedCurrencyValue, "u").test(text);
        const withoutAllowedTerms = text
          .replace(new RegExp(localeRules.explainedTerm, "gu"), "")
          .replace(new RegExp(localeRules.identifier, "gu"), "");
        return {
          tag: node.tagName.toLowerCase(),
          text: text.slice(0, 80),
          unexplainedEnglish: !namedCurrencyValue && /[A-Za-z]{3,}/.test(withoutAllowedTerms),
        };
      })
      .filter((item) => item.text && item.unexplainedEnglish)
      .filter((item, index, values) => values.findIndex((candidate) => candidate.text === item.text) === index)
      .slice(0, 20);
    const localeFlow = { untranslatedInterfaceCopy };

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
      for (const hook of ["shortlist-action", "compare-a-action", "compare-b-action", "compare-panel", "decision-action", "decision-modal", "retry-action"]) {
        if (!document.querySelector(`[data-eval="${hook}"]`)) contractIssues.push(`grant_${hook}_missing`);
      }
      if (["mobile", "compact-mobile"].includes(viewportName) && !document.querySelector('[data-eval="next-proposal"]')) {
        contractIssues.push("grant_next-proposal_missing");
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
      textScale,
      narrowTextColumns,
      bodyFlow,
      headingFlow,
      layoutFlow,
      localeFlow,
      reducedMotionAnimations,
      contractIssues,
      rootVariables,
      shellSignature: {
        typography: signature(document.body, ["fontFamily", "fontSize"]),
        header: signature(header, ["color", "backgroundColor", "borderBottomColor", "fontFamily"]),
        nav: signature(nav, ["color", "backgroundColor", "fontFamily", "fontWeight"]),
      },
    };
  }, {
    caseId: target.caseId,
    viewportName: viewport.name,
    requiredPages: CASE_PAGES[target.caseId],
    localeRules: LOCALE_RULES,
    productTextRootSelector: PRODUCT_TEXT_ROOT_SELECTOR,
  });
  const fontEvidence = await captureFontEvidenceForAudit(
    context,
    page,
    `${target.caseId}/${pageName}/${viewport.name}/${state}`,
  );

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
    fontEvidence,
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
  const evidenceGapsByTarget = {};
  const advisoriesByTarget = {};
  for (const target of options.targets) {
    const key = `${target.caseId}:${target.alias}`;
    const targetResults = report.results.filter((result) => result.caseId === target.caseId && result.alias === target.alias);
    const viewIssues = targetResults.flatMap((result) => result.visualIssues);
    const crossIssues = report.crossPageComparisons.filter((result) => result.caseId === target.caseId && result.alias === target.alias).flatMap((result) => result.visualIssues);
    const allIssues = unique([...viewIssues, ...crossIssues]);
    byTarget[key] = allIssues.filter((issue) => !EVIDENCE_ONLY_ISSUES.has(issue));
    const evidenceGaps = targetResults.flatMap((result) => {
      if (!result.visualIssues.includes("font_evidence_unavailable")) return [];
      return [{
        page: result.page,
        state: result.state,
        viewport: result.viewport,
        screenshot: result.screenshot,
        error: result.fontEvidence?.error || "font evidence unavailable",
      }];
    });
    if (evidenceGaps.length) evidenceGapsByTarget[key] = evidenceGaps;
    const advisories = targetResults.flatMap((result) => (result.layoutFlow?.unfilledColumnAdvisories || []).map((advisory) => ({
      ...advisory,
      page: result.page,
      state: result.state,
      viewport: result.viewport,
      screenshot: result.screenshot,
    })));
    if (advisories.length) advisoriesByTarget[key] = advisories;
  }
  const advisoryCount = Object.values(advisoriesByTarget).reduce((count, advisories) => count + advisories.length, 0);
  const evidenceGapCount = Object.values(evidenceGapsByTarget).reduce((count, gaps) => count + gaps.length, 0);
  const observedIssueCount = Object.values(byTarget).reduce((count, issues) => count + issues.length, 0);
  report.summary = {
    checkedPages: report.results.length,
    minimumExpectedScreenshots: 60,
    targetsWithObservedIssues: Object.values(byTarget).filter((issues) => issues.length).length,
    issuesByTarget: byTarget,
    advisoryCount,
    targetsWithAdvisories: Object.keys(advisoriesByTarget).length,
    advisoriesByTarget,
    evidenceGapCount,
    targetsWithEvidenceGaps: Object.keys(evidenceGapsByTarget).length,
    evidenceGapsByTarget,
    verdict: observedIssueCount
      ? "observed_issues"
      : evidenceGapCount
        ? "evidence_unavailable"
        : advisoryCount
          ? "advisories_present"
          : "no_observed_issues",
  };
  fs.mkdirSync(path.dirname(options.output), { recursive: true });
  fs.writeFileSync(options.output, `${JSON.stringify(report, null, 2)}\n`, { encoding: "utf8", flag: "wx" });
}

module.exports = {
  CASE_PAGES,
  FONT_ROLE_SELECTORS,
  PRODUCT_TEXT_ROOT_SELECTOR,
  VIEWPORTS,
  assertFontEvidenceComplete,
  captureFontEvidenceForAudit,
  classifyPrimaryFontUsage,
  collectFontEvidence,
  compareMultiPageShell,
  firstDeclaredFontFamily,
  grantInteractionPlan,
  hasUnexplainedEnglish,
  issueCodes,
  normalizeFontFamily,
  parseArguments,
  primaryFontMismatch,
  sharedRootTokenDrift,
  waitForRenderedStateToSettle,
};

if (require.main === module) {
  main().catch((error) => {
    console.error(error.stack || error.message || String(error));
    process.exitCode = 1;
  });
}
