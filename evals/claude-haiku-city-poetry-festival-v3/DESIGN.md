---
version: alpha
name: 城市詩祭探索
description: Editorial poetry festival discovery site with vertical Chinese typography as signature element.
colors:
  canvas: "#FEFDFB"
  surface: "#F5F3EF"
  ink: "#2A2622"
  ink-muted: "#6B6560"
  action: "#8B4513"
  action-muted: "#D4A574"
  focus: "#2A2622"
  selection: "#E8E0D8"
typography:
  display:
    fontFamily: "Georgia, 'Times New Roman', serif"
    fontSize: 48px
    fontWeight: 400
    lineHeight: 1.1
    letterSpacing: -0.02em
  reading:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', 'PingFang TC', 'Noto Sans TC', sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.7
    letterSpacing: 0
  label:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', 'PingFang TC', 'Noto Sans TC', sans-serif"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0.02em
rounded:
  sm: 2px
  md: 4px
spacing:
  xs: 8px
  sm: 16px
  md: 24px
  lg: 32px
  xl: 48px
components:
  button-primary:
    backgroundColor: "{colors.action}"
    textColor: "{colors.canvas}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "12px 20px"
  card-event:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  global-nav:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
---

# 城市詩祭探索

## Overview

An editorial poetry festival discovery site for general readers exploring poets, venues, dates, and events. Designed for thoughtful reading and intentional content priority, with Chinese vertical typography as a core design signature. The interface respects editorial pacing, generous whitespace, and clear hierarchy over decorative uniformity.

Target audience: Poetry enthusiasts and curious readers on mobile and desktop seeking festival information through curated editorial sequencing.

Personality: Contemplative, precise, authoritative—the voice of a literary journal or program booklet. Not marketing-driven; not a SaaS dashboard.

## Colors

**Canvas** (`#FEFDFB`): Primary background. Warm, paper-like tone.

**Surface** (`#F5F3EF`): Secondary surface for event containers and grouped content. Subtle tonal lift for hierarchy.

**Ink** (`#2A2622`): Primary text and primary navigation. Deep brown for warmth and literary formality.

**Ink-muted** (`#6B6560`): Secondary text, dates, metadata, and descriptive details. Reduced emphasis for supporting information.

**Action** (`#8B4513`): Buttons, links, and interactive states. Warm brown derived from traditional Chinese ink stamps.

**Focus** (`#2A2622`): Focus ring and keyboard indicator. Must remain visible and unobscured.

**Selection** (`#E8E0D8`): Current navigation state and selected records. Subtle tonal emphasis.

Color appears only when carrying editorial meaning (action, current state, metadata hierarchy). No decorative gradients, glows, or unnecessary chroma.

## Typography

**Display** (Georgia serif, 48px, 400): Main festival title and section headlines. Expressive serif voice for literary authority.

**Reading** (System sans + CJK fallback, 16px, 400, 1.7 line height): Event descriptions, poet bios, and body content. High legibility with comfortable line length and CJK support. Line-break: strict for Chinese; normal for mixed Latin.

**Label** (System sans + CJK fallback, 14px, 500): Dates, venues, poet names, status indicators, and buttons. Functional, compact voice. Uppercase sparingly; preserve Chinese natural case.

**Vertical Chinese** variant: Reading face, same metrics, applied with `writing-mode: vertical-rl` and `text-orientation: mixed`. Chinese characters remain upright; Latin numerals and punctuation rotate naturally. Used as editorial signature in homepage showcase section.

Long text must wrap intentionally. Labels must not clip unexpectedly; test at 200% zoom and 320px viewport. Mixed Latin/numerals with Chinese use natural spacing; no forced letter-spacing on body copy.

## Layout

**Page width and content measure:** Canvas spans full viewport. Reading content (event descriptions, poet bios) constrained to ~65 characters (±14em), with generous margins. Lists and structured data may use grid composition when comparison or scanning is the task.

**Spacing rhythm:** Governed by `{spacing}` tokens. Section hierarchy alternates dense event indices with quiet whitespace. No fixed-height text containers; let content breathe.

**Mobile composition:** Content reorders by reading priority. Vertical-text showcase becomes a horizontal bar or scroll region (see Mobile Transformation). Navigation toggles to compact header button. Event records preserve single-column reading order; art direction, density, and navigation change per context.

**Desktop:** Vertical Chinese section occupies a dedicated editorial spread, revealing the signature moment. Event grid may use multiple columns when records are comparable; index and detail remain accessible sequentially.

**Grid and flexbox:** Intrinsic sizing with `minmax()` and `clamp()` for responsive continuity. Single-column base; widen gracefully to tablet and desktop. Avoid `100vw` (prevents scrollbar accommodation).

## Elevation & Depth

Hierarchy is expressed through:

- **Tonal separation:** Surface over canvas for grouped events. Ink over surface for text hierarchy.
- **Whitespace:** Quiet zones between sections. Generous margins around featured content.
- **Borders:** Subtle 1px border only on specific components; not a universal decoration.
- **Shadows:** None. Depth comes from tonal, spatial, and compositional contrast.
- **Typography scale:** Display > reading > label. No faux weights or italic synthesis where real faces exist.

## Shapes

- **Radius:** Minimal, functional. `rounded.sm` (2px) for subtle button and input rounding only. `rounded.md` (4px) for event containers and optional grouped regions.
- **No arbitrary shapes:** All geometry serves hierarchy or readability. No rounded-corner maximalism.
- **Vertical text as shape language:** The editorial showcase section uses full-height vertical Chinese as a geometric and semantic element, balanced by horizontal layouts elsewhere.

## Components

### Global Navigation (`data-eval="global-nav"`)

Desktop: Persistent horizontal header with festival title (left), navigation links (center), and site identity (right). Anchored at viewport top.

Mobile: Compact header with title and toggle button (`data-eval="mobile-nav-toggle"`). Menu contents appear in overlay/sheet on toggle, fully contained with focus lock and Escape support.

State: Active/current route highlighted in selection tone. Focus remains visible and 44×44px minimum hit target.

### Event Record (`data-eval="record"`, unique `data-record-id`)

Semantic container for one festival event. Contains poet name, title, date, venue, capacity/status, and description.

Desktop: Surface container with padding. May display in grid or list context depending on primary task (browsing vs. comparison).

Mobile: Single-column, stacked layout. Maintained content order. Same semantic record identity and focus behavior.

States: Hover (action tone text), focus-visible (focus ring 2px around container), selected (optional selection color). No decorative overlay on mobile hover.

### Vertical Text Showcase

Desktop: `data-eval="vertical-type"` region with `writing-mode: vertical-rl`. Displays Chinese poetry or thematic text vertically. Characters remain upright (not rotated); pure writing-mode implementation.

Mobile: Transforms to horizontal-scroll bar or condensed short-form horizontal layout. Same content, different composition. No vertical scrolling trap on narrow screens.

### Button (Primary)

Background: action tone. Text: canvas. Typography: label weight. Padding: 12px 20px. Radius: sm. Hit target: ≥44×44px.

States: Default, hover (action-muted background), focus-visible (2px focus ring), active (pressed darker), disabled (ink-muted, cursor not-allowed).

No box-shadow. Focus ring uses focus color at 2px with sufficient contrast.

### Field and Input

Minimal styling. Inherits reading typography. Border: 1px subtle border or 2px focus ring on focus-visible. Placeholder is example text, not label. Real label element paired with input. No synthetic bold/italic.

Support IME composition; do not submit or filter on keydown during `isComposing`. Handle paste, deletion, and undo naturally. Autofill accepted.

## Do's and Don'ts

- **Do** use editorial pacing and whitespace as design tools. Let content sequence guide the eye.
- **Do** preserve vertical Chinese as a real, meaningful design signature. Not decoration; not forced onto every route.
- **Do** keep event records semantically consistent across responsive sizes. One record, two compositions.
- **Do** test long Traditional Chinese text, mixed Latin/numerals, and 200% zoom without clipping labels.
- **Do** maintain 4.5:1 text contrast (normal), 3:1 (large text and controls) across all states and backgrounds.
- **Don't** create duplicate event cards in hidden desktop/mobile copies. Compose one source with responsive CSS.
- **Don't** add motion, parallax, glows, or gradients without a named editorial purpose.
- **Don't** use card grids as a default. Choose the representation (list, index, grid, detail) from the task.
- **Don't** hide essential information behind hover or interaction; reveal it at all breakpoints.
- **Don't** force vertical text onto mobile or truncate it invisibly. Provide a mobile-appropriate equivalent.
- **Don't** present empty gradient boxes as festival imagery. Use provided content or explicit illustration.

