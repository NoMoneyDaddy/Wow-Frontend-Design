---
version: alpha
name: Community Translation Workbench
description: A zh-Hant-first review desk for comparing Traditional Chinese, English, and Arabic segment variants before release.
colors:
  primary: "#1E4FD7"
  on-primary: "#FFFFFF"
  canvas: "#F4F7FB"
  surface: "#FFFFFF"
  ink: "#10243D"
  muted: "#5C6A84"
  success: "#1F7A4D"
  on-success: "#FFFFFF"
  danger: "#B42318"
  on-danger: "#FFFFFF"
typography:
  display:
    fontFamily: "\"Noto Sans TC\", \"PingFang TC\", \"Hiragino Sans\", \"Microsoft JhengHei\", system-ui, sans-serif"
    fontSize: 34px
    fontWeight: 750
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "\"Noto Sans TC\", \"PingFang TC\", \"Hiragino Sans\", \"Microsoft JhengHei\", system-ui, sans-serif"
    fontSize: 24px
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  body:
    fontFamily: "\"Noto Sans TC\", \"PingFang TC\", \"Hiragino Sans\", \"Microsoft JhengHei\", system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "0em"
  ui:
    fontFamily: "\"Noto Sans TC\", \"PingFang TC\", \"Hiragino Sans\", \"Microsoft JhengHei\", system-ui, sans-serif"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0em"
  mono:
    fontFamily: "\"SFMono-Regular\", \"SF Mono\", Consolas, \"Liberation Mono\", Menlo, monospace"
    fontSize: 13px
    fontWeight: 500
    lineHeight: 1.5
    letterSpacing: "0em"
rounded:
  none: 0px
  sm: 10px
  md: 16px
  lg: 22px
  pill: 999px
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
components:
  shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "{spacing.xl}"
  surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xl}"
  display-banner:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.display}"
    rounded: "{rounded.none}"
    padding: "{spacing.xl}"
  section-title:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.headline}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  muted-surface:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.muted}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  code-token:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.mono}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  primary-action:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  ready-badge:
    backgroundColor: "{colors.success}"
    textColor: "{colors.on-success}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "{spacing.sm}"
  review-badge:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-danger}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "{spacing.sm}"
---

# Community Translation Workbench

## Overview

This review desk serves community translators and moderators who need to compare Traditional Chinese, English, and Arabic source variants before a segment can be handed off. The tone is calm, exact, and operational. The product keeps the primary task visible: scan the six segments, isolate the three that need review, and inspect terminology without opening a separate workflow.

The visual language is an archive-index hybrid with precision-instrument discipline. It favors aligned reading surfaces, explicit status, and a single memorable interaction: opening a segment-specific review panel that reveals term-by-term guidance instead of a generic detail drawer.

## Colors

Color is reserved for roles, not decoration.

- `canvas` is the page field and supports the outer shell.
- `surface` is the reading surface for segments and the review panel.
- `ink` is the primary reading color.
- `muted` is for supporting metadata, notes, and secondary explanation.
- `primary` marks the active control and the primary review action.
- `success` marks segments that are already deliverable.
- `danger` marks segments that still need review.

Chroma appears only when it carries state or action. Stable information stays neutral so the status labels, term guidance, and reading order remain clear when the palette is reduced.

## Typography

The system uses one CJK-safe sans stack across display, reading, and UI roles so the interface remains coherent in Traditional Chinese, English, and Arabic contexts.

- `display` is for the opening proposition and the workspace summary.
- `headline` is for section and segment titles.
- `body` is for segment copy and review notes.
- `ui` is for chips, buttons, labels, and status text.
- `mono` is reserved for compact token-like values such as numbers and short codes.

Long Traditional Chinese passages stay at comfortable line length with relaxed rhythm. English and Arabic text may break naturally inside the same surface without resorting to remote fonts or image-based text. The Arabic copy keeps its own script direction and remains readable as a live text block.

## Layout

The page uses a bounded shell, a strong opening block, a filter row, and a content/workspace split.

- Desktop places the comparison list and the review panel side by side so the reviewer can scan and inspect without losing context.
- Mobile collapses into a single reading column: summary, filters, segments, then the review panel when opened.
- The first viewport keeps the top task visible without forcing a scroll through decorative content.
- The workspace relies on intrinsic sizing, `minmax(0, 1fr)`, and `min-width: 0` so long multilingual copy can shrink safely.

Spacing is modular rather than uniform. The hero gets more breathing room than each segment; inside a segment, the language blocks stay close enough to compare line by line.

## Elevation & Depth

Depth stays restrained. The page uses a light canvas, flat surfaces, a visible border, and only a small shadow on the review panel to signal that it is an active comparison surface. There is no glass effect, no heavy blur, and no competing card stack.

The review panel is the only transient layer. It opens from the selected segment, returns focus on close, and never replaces the primary list.

## Shapes

Corners are moderately rounded to keep the interface humane but serious.

- Segment surfaces use `22px` radius.
- Buttons and filters use `16px` radius for a calmer control shape.
- Status pills use full pill rounding to read as state labels rather than geometry experiments.

The shape language is consistent across controls, surfaces, and status markers. No component becomes a novelty object.

## Components

- The shell wraps the full page and establishes the reading field.
- Filter pills switch between all segments and the review-only subset.
- Segment surfaces contain the three language variants for a single translation unit.
- Status badges state whether a segment is deliverable or still under review.
- The open-review action reveals the selected segment's terminology guidance in the panel.
- The review panel presents source, explanation, and revision advice in one place so the reviewer can compare quickly.

Unsupported details such as borders, shadows, and responsive reflow live in the Markdown body rather than the token frontmatter. The runtime code consumes the same semantic roles everywhere instead of redefining colors per page.

## Do's and Don'ts

- Do keep the six-segment structure intact and preserve the three review-flagged items.
- Do keep Arabic copy in live text with `lang="ar"` and `dir="rtl"`.
- Do keep the first review entry wired to the open-panel hook.
- Do keep the filter controls honest: they only hide and reveal existing segments.
- Don't rely on hover for content discovery.
- Don't use remote assets, icon fonts, or translated image text.
- Don't claim translation correctness, publication, or accessibility conformance from the design document alone.
