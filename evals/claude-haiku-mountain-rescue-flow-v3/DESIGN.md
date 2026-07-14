---
version: alpha
name: Mountain Rescue Coordination Dashboard
description: High-density incident command surface for zone, team, and time-critical task monitoring.
colors:
  canvas: "#FAFBF9"
  surface-1: "#FFFFFF"
  surface-2: "#F0F1EF"
  text-primary: "#1A1C1E"
  text-secondary: "#6B7077"
  text-muted: "#9BA0A6"
  border-subtle: "#D8D9D7"
  border-strong: "#C4C5C2"
  focus: "#1A7EC7"
  success: "#1B6E3A"
  warning: "#B8860B"
  danger: "#A61C2E"
  info: "#0055B8"
  stage-received: "#E8EAED"
  stage-dispatched: "#B4D4FF"
  stage-active: "#66BB6A"
  stage-complete: "#9BA0A6"
typography:
  headline-xl:
    fontFamily: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang TC", "Noto Sans TC", "Microsoft JhengHei", sans-serif
    fontSize: 28px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: 0
  headline-lg:
    fontFamily: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang TC", "Noto Sans TC", "Microsoft JhengHei", sans-serif
    fontSize: 20px
    fontWeight: 600
    lineHeight: 1.3
  headline-sm:
    fontFamily: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang TC", "Noto Sans TC", "Microsoft JhengHei", sans-serif
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.4
  body-lg:
    fontFamily: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang TC", "Noto Sans TC", "Microsoft JhengHei", sans-serif
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.5
  body:
    fontFamily: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang TC", "Noto Sans TC", "Microsoft JhengHei", sans-serif
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  body-sm:
    fontFamily: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang TC", "Noto Sans TC", "Microsoft JhengHei", sans-serif
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.4
  label:
    fontFamily: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang TC", "Noto Sans TC", "Microsoft JhengHei", sans-serif
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1.3
  numeric:
    fontFamily: "Menlo", "Monaco", "SF Mono", monospace
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
rounded:
  sm: 4px
  md: 8px
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  2xl: 32px
components:
  button-primary:
    backgroundColor: "{colors.focus}"
    textColor: "{colors.canvas}"
    typography: "{typography.label}"
    padding: "8px 16px"
    rounded: "{rounded.sm}"
  button-secondary:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.text-primary}"
    typography: "{typography.label}"
    padding: "8px 16px"
    rounded: "{rounded.sm}"
  status-badge-success:
    backgroundColor: "{colors.success}"
    textColor: "#FFFFFF"
    typography: "{typography.label}"
    padding: "4px 8px"
    rounded: "{rounded.sm}"
  status-badge-warning:
    backgroundColor: "{colors.warning}"
    textColor: "#FFFFFF"
    typography: "{typography.label}"
    padding: "4px 8px"
    rounded: "{rounded.sm}"
  status-badge-danger:
    backgroundColor: "{colors.danger}"
    textColor: "#FFFFFF"
    typography: "{typography.label}"
    padding: "4px 8px"
    rounded: "{rounded.sm}"
  task-record:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
---

# Mountain Rescue Coordination Dashboard

## Overview

A field-operations dashboard for incident commanders managing rescue zones, team load, communications status, and time-critical task urgency. Information density and scanability are essential; danger color indicates only true danger or expired time. Urgency, task stage, and deadline state color independently to prevent false priority bleed. Desktop supports side-by-side zone comparison; mobile prioritizes a commander's task inbox with deferred context and accessible actions in thumb reach.

## Colors

**Canvas & Surfaces**
- `canvas` (#FAFBF9): page background
- `surface-1` (#FFFFFF): primary task card, record container
- `surface-2` (#F0F1EF): secondary interaction, summary zones
- `border-subtle`, `border-strong`: zone boundaries, subtle dividers, strong emphasis separators

**Text**
- `text-primary` (#1A1C1E): main reading hierarchy
- `text-secondary` (#6B7077): supporting metadata, zone info
- `text-muted` (#9BA0A6): inactive, historical, deferred state

**Interactive**
- `focus` (#1A7EC7): action buttons, clickable elements, keyboard focus ring
- `success` (#1B6E3A): completed tasks, healthy team status, all-clear
- `warning` (#B8860B): urgent but not expired; time-sensitive, yellow flag
- `danger` (#A61C2E): overdue task, critical team status, red flag only when truly critical
- `info` (#0055B8): comms state, informational badges

**Stage encoding** (task lifecycle color, not urgency override)
- `stage-received`: task intake, waiting dispatch
- `stage-dispatched`: en route, team mobilizing
- `stage-active`: on-site, rescue in progress
- `stage-complete`: mission concluded

When task stage and deadline urgency both apply, use separate badges or columns; never blend them into one color. A dispatched task with an approaching deadline shows both the dispatch color and a deadline indicator, not a hybrid.

## Typography

- **Headline XL** (28px, 600wt): page title, primary commander view name
- **Headline LG** (20px, 600wt): section headers (e.g., "任務概況", "責任區")
- **Headline SM** (16px, 600wt): zone name, team identifier, section emphasis
- **Body LG** (16px, 400wt): primary task content, readable prose
- **Body** (14px, 400wt): standard metadata, team roster, inline detail
- **Body SM** (13px, 400wt): supporting text, timestamps, secondary labels
- **Label** (12px, 500wt): button text, state badges, input labels
- **Numeric** (monospace, 14px, 400wt): coordinates, timers, team counts, IDs—tabular alignment

Font stack defaults to system UI, with explicit fallback for Traditional Chinese (`PingFang TC`, `Noto Sans TC`, `Microsoft JhengHei`). Line length stays below 80 characters for body text; headings may be shorter. Avoid tracking on Chinese body copy; use it sparingly on intentional display treatments.

## Layout

**Page structure:** shell with persistent global navigation, page title, summary area (not replacing task list), and main work region.

**Desktop (1024px+):** Two-column zone comparison or full-width task grid. Sidebar navigation stays fixed; task regions reflow into 2–3 comparable columns. Summary badges remain visible above the fold. Zone context and team sidebar defer to accordion or detail pane.

**Tablet (768–1023px):** Single-column task list with zone filter. Navigation collapses to top bar; summary stays in header. Zone detail accessible via disclosure or modal.

**Mobile (320–767px):** Task-prioritized inbox, sorted by deadline urgency. Compact header with mobile-nav button, search/filter deferred to drawer. Zone and team context in collapsible sections below task. Sticky "commander quick actions" bar at bottom (if warranted).

**Grid & spacing:** 12px base increment. Page padding: 16px mobile, 24px tablet, 32px desktop. Card padding: 12px. Column gap: 16px. Row gap: 12px. Reading measure: ~66 character width for body prose. Content max-width on desktop: 1280px; narrow mobile: 100vw – 16px margin (no fixed width that causes overflow).

## Elevation & Depth

No shadows or glass; use tonal layering (surface-1 over canvas, surface-2 for secondary UI) and borders for clarity. Task record containers use a subtle 1px `border-subtle` to separate from canvas. Focus ring is a 2px solid `focus` color on tab/keyboard navigation. Overlays (if any) use a scrim with transparent background and clear boundary. Depth hierarchy is expressed through whitespace, color change, and border placement—not elevation metaphor.

## Shapes

Minimal radius: 4px (`rounded-sm`) for buttons, small badges, input controls. 8px (`rounded-md`) for card containers and larger components. Exception: when touching screen edges on mobile, no radius. Borders are 1px solid; do not use decorative outlines or multiple borders on the same element.

## Components

**Button Primary** (blue, focus color, 8px padding, 4px radius): command actions, dispatch, status updates.
**Button Secondary** (surface-2 background, text-primary, 8px padding): dismiss, cancel, alternative paths.
**Status Badge Success/Warning/Danger** (4px padding, 4px radius, white text): task stage, team health, deadline state—each as a separate badge, never combined.
**Task Record** (white background, 12px padding, 8px radius, subtle border): one row per rescue task showing zone, team, stage (colored badge), urgency indicator, time, and quick actions (if space allows).
**Zone Summary** (surface-2, text secondary, compact layout): snapshot of one zone's active tasks, team load, comms state; clickable to expand or navigate to zone detail.
**Data Attributes:** Each record uses `data-eval="record"` with `data-record-id` for identity, `data-record-priority` for urgency level (high/medium/low), `data-record-status` for stage badge, and `data-record-due` for deadline timestamp. Global nav uses `data-eval="global-nav"`. Mobile nav toggle (if present) uses `data-eval="mobile-nav-toggle"`.

## Do's and Don'ts

- **Do** use separate color badges for task stage and deadline urgency; never blend them.
- **Do** keep numeric metadata (coordinates, team counts, time remaining) in monospace or aligned columns.
- **Do** reserve danger color (#A61C2E) for truly critical or overdue tasks; use warning (#B8860B) for time-sensitive but not yet expired.
- **Do** ensure buttons and short labels fit on one line at 320px; measure rendered text, not character count.
- **Don't** center-align task records or use a card grid with equal heights; use a list or comparable table structure.
- **Don't** add decorative gradients, glows, or parallax to task data; information clarity comes first.
- **Don't** hide navigation or essential state behind hover-only interactions on mobile.
- **Don't** use full-width red backgrounds or alert styles for non-critical notifications.
- **Don't** apply color from both the stage and urgency system to the same element; use adjacent badges instead.
