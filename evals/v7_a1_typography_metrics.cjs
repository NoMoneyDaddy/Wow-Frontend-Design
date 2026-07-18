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

  const textPaintedThrough = (parent) => {
    if (["hidden", "collapse"].includes(getComputedStyle(parent).visibility)) return false;
    let effectiveOpacity = 1;
    for (let current = parent; current; current = current.parentElement) {
      const style = getComputedStyle(current);
      effectiveOpacity *= Number(style.opacity);
      if (
        style.display === "none"
        || effectiveOpacity <= 0.01
        || style.contentVisibility === "hidden"
      ) return false;
    }
    return true;
  };

  const lineFragments = (node) => {
    const fragments = [];
    const locale = node.lang || document.documentElement.lang || "zh-Hant";
    const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
    let order = 0;
    while (walker.nextNode()) {
      const textNode = walker.currentNode;
      const parent = textNode.parentElement;
      if (
        !parent
        || parent.closest("rt, rp, script, style, [aria-hidden='true'], [inert]")
        || !textPaintedThrough(parent)
      ) continue;
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

  const textCompleteness = (node, facts) => {
    const style = getComputedStyle(node);
    const base = {
      status: "complete",
      reason: null,
      mechanism: null,
      tolerance: null,
      inlineDelta: 0,
      blockDelta: 0,
      graphemeCount: 0,
      outsideRectCount: 0,
    };
    const notApplicable = (reason) => ({ ...base, status: "not_applicable", reason });
    const unavailable = (reason, values = {}) => ({ ...base, ...values, status: "unavailable", reason });
    if (facts.mode !== "product") return notApplicable(`${facts.mode}_intent`);
    if (!facts.horizontal) return notApplicable("vertical_writing");
    if (!facts.leftToRight) return notApplicable("right_to_left");
    if (facts.interactive) return notApplicable("interactive_control");
    if (!facts.eligible) return notApplicable("ineligible_target");

    const normalized = (value) => value || "none";
    const individualTransform = [style.translate, style.rotate, style.scale]
      .some((value) => value && value !== "none");
    if (style.transform !== "none" || individualTransform || normalized(style.offsetPath) !== "none") {
      return unavailable("transformed_target");
    }
    if ((style.clip || "auto") !== "auto") return unavailable("complex_clip_or_filter");
    const zoom = !style.zoom || style.zoom === "normal" ? 1 : Number(style.zoom);
    if (!Number.isFinite(zoom) || zoom !== 1) return unavailable("non_unit_zoom");
    if (normalized(style.clipPath) !== "none" || normalized(style.maskImage) !== "none"
        || normalized(style.filter) !== "none") return unavailable("complex_clip_or_filter");
    const pseudoContent = ["::before", "::after"].some((pseudo) => {
      const content = getComputedStyle(node, pseudo).content;
      return Boolean(content && !["none", "normal", "\"\"", "''"].includes(content));
    });
    if (pseudoContent) return unavailable("pseudo_content_present");
    if (node.clientWidth <= 0 || node.clientHeight <= 0) return unavailable("direct_client_box_unavailable");

    const inlineDelta = Math.max(0, node.scrollWidth - node.clientWidth);
    const blockDelta = Math.max(0, node.scrollHeight - node.clientHeight);
    const finiteLineHeight = Number.parseFloat(style.lineHeight);
    const lineHeightIsFinite = Number.isFinite(finiteLineHeight) && finiteLineHeight > 0;
    const finiteTolerance = lineHeightIsFinite ? Math.max(2, finiteLineHeight * 0.25) : null;
    const overflowX = style.overflowX;
    const overflowY = style.overflowY;
    const nonScrollX = ["hidden", "clip"].includes(overflowX);
    const nonScrollY = ["hidden", "clip"].includes(overflowY);
    const clamp = Number.parseInt(style.webkitLineClamp, 10);
    const ellipsisOrClampTolerance = finiteTolerance ?? 2;
    let mechanism = null;
    if (Number.isFinite(clamp) && clamp > 0 && nonScrollY && blockDelta > ellipsisOrClampTolerance) {
      mechanism = "line_clamp";
    } else if (style.textOverflow === "ellipsis" && nonScrollX && inlineDelta > ellipsisOrClampTolerance) {
      mechanism = "inline_ellipsis";
    } else if (nonScrollX && inlineDelta > (finiteTolerance ?? 2)) {
      mechanism = "inline_clip";
    } else if (nonScrollY && blockDelta > (finiteTolerance ?? 2)) {
      mechanism = "block_clip";
    }

    const tolerance = finiteTolerance ?? (["inline_ellipsis", "line_clamp"].includes(mechanism) ? 2 : null);
    const comparisonTolerance = tolerance ?? 2;
    const scrollAxis = !mechanism && (
      (["auto", "scroll"].includes(overflowX) && inlineDelta > comparisonTolerance && "inline")
      || (["auto", "scroll"].includes(overflowY) && blockDelta > comparisonTolerance && "block")
      || null
    );
    const values = {
      mechanism: scrollAxis ? "scroll_region" : mechanism,
      tolerance: tolerance === null ? null : Number(tolerance.toFixed(2)),
      inlineDelta: Number(Math.min(inlineDelta, 1_000_000).toFixed(2)),
      blockDelta: Number(Math.min(blockDelta, 1_000_000).toFixed(2)),
    };
    if (nonScrollX && inlineDelta > (finiteTolerance ?? 2) && !["clip", "ellipsis"].includes(style.textOverflow)) {
      return unavailable("unsupported_text_overflow", values);
    }
    const relevantDelta = scrollAxis
      ? scrollAxis === "inline" ? inlineDelta : blockDelta
      : ["inline_ellipsis", "inline_clip"].includes(mechanism) ? inlineDelta : blockDelta;
    if ((!scrollAxis && !mechanism) || relevantDelta <= comparisonTolerance) return { ...base, ...values };
    if (!scrollAxis && tolerance === null) return unavailable("line_height_unavailable", values);

    const clientLeft = node.getBoundingClientRect().left + node.clientLeft;
    const clientTop = node.getBoundingClientRect().top + node.clientTop;
    const clipBox = {
      left: clientLeft,
      top: clientTop,
      right: clientLeft + node.clientWidth,
      bottom: clientTop + node.clientHeight,
    };
    const locale = node.lang || document.documentElement.lang || "zh-Hant";
    const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
    const fragments = [];
    let graphemeCount = 0;
    while (walker.nextNode()) {
      const textNode = walker.currentNode;
      const parent = textNode.parentElement;
      if (
        !parent
        || parent.closest("rt, rp, script, style, [aria-hidden='true'], [inert]")
        || !textPaintedThrough(parent)
      ) continue;
      for (const item of graphemes(textNode.data, locale)) {
        graphemeCount += 1;
        if (graphemeCount > 4096) return unavailable("grapheme_budget_exceeded", {
          ...values,
          graphemeCount: 4096,
        });
        const range = document.createRange();
        range.setStart(textNode, item.index);
        range.setEnd(textNode, item.index + item.segment.length);
        for (const rect of range.getClientRects()) {
          if (rect.width > 0.1 && rect.height > 0.1) fragments.push(rect);
        }
      }
    }
    const inlineMechanism = ["inline_ellipsis", "inline_clip"].includes(mechanism);
    const outside = fragments.filter((rect) => scrollAxis
      ? scrollAxis === "inline"
        ? rect.left < clipBox.left - comparisonTolerance || rect.right > clipBox.right + comparisonTolerance
        : rect.top < clipBox.top - comparisonTolerance || rect.bottom > clipBox.bottom + comparisonTolerance
      : inlineMechanism
        ? rect.left < clipBox.left - comparisonTolerance || rect.right > clipBox.right + comparisonTolerance
        : rect.top < clipBox.top - comparisonTolerance || rect.bottom > clipBox.bottom + comparisonTolerance);
    const measured = {
      ...base,
      ...values,
      graphemeCount,
      outsideRectCount: Math.min(outside.length, 4096),
    };
    if (!outside.length) return { ...measured, status: "advisory", reason: "direct_text_overflow_not_confirmed" };
    if (scrollAxis) {
      const labelledBy = (node.getAttribute("aria-labelledby") || "").trim().split(/\s+/).filter(Boolean);
      const labelledName = labelledBy.some((id) => Boolean(document.getElementById(id)?.textContent?.trim()));
      const named = Boolean(node.getAttribute("aria-label")?.trim() || labelledName);
      const accessible = node.getAttribute("role") === "region" && node.tabIndex >= 0 && named;
      return {
        ...measured,
        status: accessible ? "accessible_scroll" : "advisory",
        reason: accessible ? "named_focusable_scroll_region" : "scroll_region_not_accessibly_exposed",
      };
    }
    return { ...measured, status: "clipped", reason: "direct_text_outside_client_box" };
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
  const flaggedVoidOwners = new Set();
  const columnVoid = (owner) => {
    const parent = owner.parentElement;
    if (!parent || parent === document.body || !visible(parent)) return null;
    const parentStyle = getComputedStyle(parent);
    if (!["grid", "inline-grid", "flex", "inline-flex"].includes(parentStyle.display)) return null;
    const ownerRect = owner.getBoundingClientRect();
    const parentRect = parent.getBoundingClientRect();
    if (ownerRect.width >= parentRect.width * 0.8 || ownerRect.height < 120) return null;
    const siblings = [...parent.children].filter((item) => item !== owner && visible(item));
    const sidePeers = siblings.map((item) => ({ item, rect: item.getBoundingClientRect() })).filter(({ rect }) => {
      const horizontalOverlap = Math.max(0, Math.min(ownerRect.right, rect.right) - Math.max(ownerRect.left, rect.left));
      return horizontalOverlap <= Math.min(ownerRect.width, rect.width) * 0.2
        && rect.top <= ownerRect.bottom + 64
        && rect.bottom > ownerRect.bottom;
    });
    if (!sidePeers.length) return null;
    const peerBottom = Math.max(...sidePeers.map(({ rect }) => rect.bottom));
    const voidHeight = peerBottom - ownerRect.bottom;
    const filler = siblings.some((item) => {
      if (sidePeers.some((peer) => peer.item === item)) return false;
      const rect = item.getBoundingClientRect();
      const horizontalOverlap = Math.max(0, Math.min(ownerRect.right, rect.right) - Math.max(ownerRect.left, rect.left));
      return horizontalOverlap >= Math.min(ownerRect.width, rect.width) * 0.45
        && rect.top < peerBottom - 24
        && rect.bottom > ownerRect.bottom + 24;
    });
    const threshold = Math.max(240, innerHeight * 0.3);
    if (filler || voidHeight <= threshold) return null;
    return {
      voidHeight: Number(voidHeight.toFixed(2)),
      threshold: Number(threshold.toFixed(2)),
      ownerHeight: Number(ownerRect.height.toFixed(2)),
      peerHeight: Number(Math.max(...sidePeers.map(({ rect }) => rect.height)).toFixed(2)),
      parentDisplay: parentStyle.display,
      parentWidth: Number(parentRect.width.toFixed(2)),
    };
  };
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
    const ownerColumnVoid = columnVoid(owner);
    const targetColumnVoid = ownerColumnVoid ? null : columnVoid(node);
    const columnVoidMeasurement = ownerColumnVoid
      ? { source: "owner", ...ownerColumnVoid }
      : targetColumnVoid ? { source: "target", ...targetColumnVoid } : null;
    const columnVoidKey = ownerColumnVoid ? owner : node.parentElement;
    const ownerMinimum = role === "heading" ? 760 : 560;
    const gapMinimum = role === "heading" ? 280 : 220;
    const startAligned = inlineStartGap >= -2 && inlineStartGap <= Math.max(32, ownerRect.width * 0.08);
    const underfilledTrack = ownerRect.width >= ownerMinimum
      && trackRatio < 0.6
      && inlineEndGap > gapMinimum
      && startAligned
      && !hasTaskPeer;
    const completeness = textCompleteness(node, {
      eligible,
      horizontal,
      interactive,
      leftToRight,
      mode,
    });
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
      columnVoid: columnVoidMeasurement,
      computedFontFamily: style.fontFamily,
      textCompleteness: completeness,
    };
    targets.push(measurement);

    const findings = [];
    if (columnVoidMeasurement && columnVoidKey && !flaggedVoidOwners.has(columnVoidKey)) {
      flaggedVoidOwners.add(columnVoidKey);
      issues.push({ code: "a1_layout_column_void", targetId: spec.id, measurement });
    }
    if (orphan) findings.push(role === "heading" ? "a1_heading_han_orphan" : "a1_prose_han_orphan");
    if (underfilledTrack) findings.push(role === "heading" ? "a1_heading_track_void" : "a1_prose_track_void");
    if (completeness.status === "clipped") findings.push("a1_required_text_clipped");
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
