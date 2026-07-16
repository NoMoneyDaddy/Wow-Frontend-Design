"use strict";

const HARD_MODES = new Set(["product"]);
const ALLOWED_MODES = new Set(["product", "editorial", "display"]);
const ALLOWED_ROLES = new Set(["heading", "prose"]);

function auditV7A1Typography(specs) {
  const hardModes = new Set(["product"]);
  const allowedRoles = new Set(["heading", "prose"]);
  const visible = (node) => {
    if (!(node instanceof Element)) return false;
    const style = getComputedStyle(node);
    const rect = node.getBoundingClientRect();
    return style.display !== "none"
      && style.visibility !== "hidden"
      && Number(style.opacity) > 0.01
      && rect.width > 0.5
      && rect.height > 0.5
      && !node.closest("[aria-hidden='true'], [inert]");
  };

  const query = (selector) => {
    try {
      return [...document.querySelectorAll(selector)];
    } catch {
      return [];
    }
  };

  const graphemes = (value, locale) => {
    const segmenter = new Intl.Segmenter(locale || "zh-Hant", { granularity: "grapheme" });
    return [...segmenter.segment(value)];
  };

  const lineFragments = (node) => {
    const fragments = [];
    const locale = node.lang || document.documentElement.lang || "zh-Hant";
    const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
    let order = 0;
    while (walker.nextNode()) {
      const textNode = walker.currentNode;
      const parent = textNode.parentElement;
      if (!parent || parent.closest("rt, rp, script, style, [aria-hidden='true'], [inert]")) continue;
      for (const item of graphemes(textNode.data, locale)) {
        const range = document.createRange();
        range.setStart(textNode, item.index);
        range.setEnd(textNode, item.index + item.segment.length);
        const rect = [...range.getClientRects()].find((candidate) => candidate.width > 0.1 && candidate.height > 0.1);
        if (!rect) continue;
        fragments.push({
          order: order += 1,
          text: item.segment,
          top: rect.top,
          bottom: rect.bottom,
          left: rect.left,
          right: rect.right,
          height: rect.height,
        });
      }
    }

    const lines = [];
    for (const fragment of fragments) {
      let best = null;
      let bestOverlap = 0;
      for (const line of lines) {
        const overlap = Math.max(0, Math.min(line.bottom, fragment.bottom) - Math.max(line.top, fragment.top));
        const ratio = overlap / Math.max(1, Math.min(line.height, fragment.height));
        if (ratio >= 0.35 && ratio > bestOverlap) {
          best = line;
          bestOverlap = ratio;
        }
      }
      if (!best) {
        best = {
          top: fragment.top,
          bottom: fragment.bottom,
          left: fragment.left,
          right: fragment.right,
          height: fragment.height,
          fragments: [],
        };
        lines.push(best);
      }
      best.top = Math.min(best.top, fragment.top);
      best.bottom = Math.max(best.bottom, fragment.bottom);
      best.left = Math.min(best.left, fragment.left);
      best.right = Math.max(best.right, fragment.right);
      best.height = Math.max(best.height, fragment.height);
      best.fragments.push(fragment);
    }
    return lines
      .sort((left, right) => left.top - right.top || left.left - right.left)
      .map((line) => ({
        text: line.fragments.sort((left, right) => left.order - right.order).map((fragment) => fragment.text).join("").trim(),
        top: line.top,
        left: line.left,
        right: line.right,
        width: line.right - line.left,
      }));
  };

  const meaningful = (value) => graphemes(value).filter((item) => /[\p{Letter}\p{Number}]/u.test(item.segment));
  const han = (value) => graphemes(value).filter((item) => /\p{Script=Han}/u.test(item.segment));
  const taskPeer = (spec, node, owner) => {
    if (!spec.peerSelector) return false;
    const nodeRect = node.getBoundingClientRect();
    const ownerRect = owner.getBoundingClientRect();
    return query(spec.peerSelector).filter(visible).some((peer) => {
      if (peer === node || node.contains(peer) || !owner.contains(peer)) return false;
      const peerRect = peer.getBoundingClientRect();
      const name = (peer.getAttribute("aria-label") || peer.textContent || "").trim();
      const semantic = peer.matches("button, input, select, textarea, nav, aside, [role='button'], [role='status'], [role='group']");
      return Boolean(name) && semantic && peerRect.width >= 80
        && peerRect.left >= nodeRect.right - 8
        && peerRect.right <= ownerRect.right + 2
        && peerRect.bottom > ownerRect.top && peerRect.top < ownerRect.bottom;
    });
  };

  const issues = [];
  const observations = [];
  const targets = [];
  for (const spec of specs) {
    const nodes = query(spec.selector);
    const owners = query(spec.ownerSelector);
    if (nodes.length !== 1 || owners.length !== 1) {
      issues.push({
        code: "a1_target_contract_unresolved",
        targetId: spec.id,
        nodeCount: nodes.length,
        ownerCount: owners.length,
      });
      continue;
    }
    const node = nodes[0];
    const owner = owners[0];
    const style = getComputedStyle(node);
    const writingMode = style.writingMode;
    const mode = spec.mode;
    const role = spec.role;
    const horizontal = writingMode.startsWith("horizontal");
    const language = node.closest("[lang]")?.lang || document.documentElement.lang;
    const traditionalChinese = /^zh-(?:hant|tw|hk|mo)(?:-|$)/i.test(language);
    const leftToRight = style.direction === "ltr";
    const interactive = Boolean(node.closest("button, input, select, textarea, [role='button'], [role='option'], [role='tab']"));
    const eligible = visible(node) && visible(owner) && owner.contains(node) && horizontal && traditionalChinese
      && leftToRight && !interactive
      && hardModes.has(mode) && allowedRoles.has(role);
    const lines = lineFragments(node);
    const rect = node.getBoundingClientRect();
    const ownerRect = owner.getBoundingClientRect();
    const trackRatio = rect.width / Math.max(ownerRect.width, 1);
    const inlineStartGap = style.direction === "rtl" ? ownerRect.right - rect.right : rect.left - ownerRect.left;
    const inlineEndGap = style.direction === "rtl" ? rect.left - ownerRect.left : ownerRect.right - rect.right;
    const lastLine = lines.at(-1)?.text || "";
    const previousLine = lines.at(-2)?.text || "";
    const orphan = lines.length >= 2
      && meaningful(lastLine).length === 1
      && han(lastLine).length === 1
      && meaningful(previousLine).length >= 2;
    const hasTaskPeer = taskPeer(spec, node, owner);
    const ownerMinimum = role === "heading" ? 760 : 560;
    const gapMinimum = role === "heading" ? 280 : 220;
    const startAligned = inlineStartGap >= -2 && inlineStartGap <= Math.max(32, ownerRect.width * 0.08);
    const underfilledTrack = ownerRect.width >= ownerMinimum
      && trackRatio < 0.6
      && inlineEndGap > gapMinimum
      && startAligned
      && !hasTaskPeer;
    const measurement = {
      id: spec.id,
      role,
      mode,
      eligible,
      visible: visible(node),
      horizontal,
      interactive,
      language,
      traditionalChinese,
      leftToRight,
      writingMode,
      lineCount: lines.length,
      lastLineText: lastLine,
      previousLineText: previousLine,
      trackRatio: Number(trackRatio.toFixed(4)),
      inlineStartGap: Number(inlineStartGap.toFixed(2)),
      inlineEndGap: Number(inlineEndGap.toFixed(2)),
      ownerWidth: Number(ownerRect.width.toFixed(2)),
      trackWidth: Number(rect.width.toFixed(2)),
      hasTaskPeer,
      computedFontFamily: style.fontFamily,
    };
    targets.push(measurement);

    const findings = [];
    if (orphan) findings.push(role === "heading" ? "a1_heading_han_orphan" : "a1_prose_han_orphan");
    if (underfilledTrack) findings.push(role === "heading" ? "a1_heading_track_void" : "a1_prose_track_void");
    if (eligible) {
      for (const code of findings) issues.push({ code, targetId: spec.id, measurement });
    } else if (findings.length || !horizontal || interactive || !hardModes.has(mode)) {
      observations.push({
        targetId: spec.id,
        codes: findings,
        reason: !horizontal ? "vertical-writing"
          : !traditionalChinese ? "non-traditional-chinese"
            : !leftToRight ? "non-ltr"
          : interactive ? "interactive-control"
            : !hardModes.has(mode) ? `${mode}-intent`
              : "ineligible-target",
        measurement,
      });
    }
  }
  return {
    schemaVersion: 1,
    issues,
    observations,
    targets,
    environment: {
      documentLang: document.documentElement.lang,
      viewport: { width: innerWidth, height: innerHeight, devicePixelRatio },
      userAgent: navigator.userAgent,
      fontsStatus: document.fonts.status,
    },
  };
}

function validateSpecs(specs) {
  if (!Array.isArray(specs) || specs.length < 1 || specs.length > 64) throw new TypeError("specs must contain 1..64 entries");
  const ids = new Set();
  for (const spec of specs) {
    if (!spec || typeof spec !== "object" || Array.isArray(spec)) throw new TypeError("each spec must be an object");
    const keys = Object.keys(spec).sort();
    const expected = ["id", "mode", "ownerSelector", "role", "selector"];
    if (spec.peerSelector !== undefined) expected.push("peerSelector");
    if (keys.join("|") !== expected.sort().join("|")) throw new TypeError(`invalid spec keys for ${spec.id || "unknown"}`);
    if (typeof spec.id !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(spec.id) || ids.has(spec.id)) {
      throw new TypeError("spec ids must be unique lowercase kebab-case");
    }
    ids.add(spec.id);
    if (!ALLOWED_ROLES.has(spec.role)) throw new TypeError(`invalid role for ${spec.id}`);
    if (!ALLOWED_MODES.has(spec.mode)) throw new TypeError(`invalid mode for ${spec.id}`);
    for (const key of ["selector", "ownerSelector", "peerSelector"]) {
      if (spec[key] !== undefined && (typeof spec[key] !== "string" || spec[key].length < 1 || spec[key].length > 300)) {
        throw new TypeError(`invalid ${key} for ${spec.id}`);
      }
    }
  }
  return specs;
}

module.exports = { auditV7A1Typography, validateSpecs };
