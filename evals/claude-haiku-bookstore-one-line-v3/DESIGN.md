---
version: alpha
name: Bookstore Design System
description: Traditional Chinese bookstore with warm, curated aesthetic and accessible commerce
colors:
  primary: "#2C2416"
  on-primary: "#FFFFFF"
  surface: "#FAF8F3"
  on-surface: "#2C2416"
  surface-variant: "#F0EDE6"
  on-surface-variant: "#59574E"
  accent: "#C4732F"
  on-accent: "#FFFFFF"
  success: "#4CAF50"
  error: "#D32F2F"
  focus: "#2C2416"
typography:
  display:
    fontFamily: "Georgia, 'Times New Roman', serif"
    fontSize: 36px
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: -0.015em
  headline:
    fontFamily: "Georgia, 'Times New Roman', serif"
    fontSize: 24px
    fontWeight: 700
    lineHeight: 1.3
  subheading:
    fontFamily: "Georgia, 'Times New Roman', serif"
    fontSize: 18px
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: system-ui
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
  body-small:
    fontFamily: system-ui
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  ui:
    fontFamily: system-ui
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.5
rounded:
  none: 0px
  sm: 4px
  md: 8px
  lg: 12px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "12px 24px"
  button-secondary:
    backgroundColor: "{colors.surface-variant}"
    textColor: "{colors.on-surface}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "12px 24px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.sm}"
    padding: "10px 12px"
  link:
    textColor: "{colors.accent}"
---

# Bookstore Design System

## Overview

A Traditional Chinese bookstore website that treats books as curated objects worthy of discovery. The design prioritizes trust through clear information architecture, warm typography that reflects the bookstore's personality, and straightforward commerce. Audience: book lovers seeking both discovery and purposeful purchase. Density: moderate—sufficient detail for informed choice without overwhelming browsing. Emotion: welcoming authority, not austere; curated, not mercenary.

## Colors

- **Primary (dark brown #2C2416):** Page background, headings, body text, primary navigation. Authority and warmth without corporate coldness.
- **Surface (cream #FAF8F3):** Content cards, input fields, modals. Evokes book pages and natural materials.
- **Surface variant (light taupe #F0EDE6):** Secondary containers, disabled states, subtle grouping.
- **Accent (warm copper #C4732F):** Call-to-action buttons, links, category highlights. Earthy, actionable without aggression.
- **Success/error (green/red):** Status-specific meaning only; never the sole visual cue.

Color carries semantic meaning: warm surfaces welcome; copper invites action; neutral chrome recedes. Test contrast over every layered state. Dark mode: invert lightness while preserving warmth—cream becomes #3C3A35, brown becomes #F5F3F0, copper shifts to #D89B4F. Status and brand colors remain distinguishable in grayscale and forced colors.

## Typography

**Display (serif, 36px, 700):** Homepage hero and major section titles. Serif choice signals editorial authority and book culture.

**Headline (serif, 24px, 700):** Page and card headings. Maintains hierarchy and personality.

**Subheading (serif, 18px, 600):** Secondary headings, filter labels, category names.

**Body (sans, 16px, 400, 1.6 line-height):** Product descriptions, blog, long-form content. Clean, readable at narrow mobile and extended desktop widths. Line length capped at 68ch for comfortable reading.

**Body-small (sans, 14px, 400):** Metadata, pricing, publication details, secondary actions.

**UI (sans, 14px, 500):** Button labels, form labels, navigation, controls. Higher weight for clarity in compact UI.

For Traditional Chinese: use region-aware fallbacks; preserve full-width punctuation; allow 1.6–1.8 line height for comfortable reading. Keep body lines comfortable; avoid stretching Chinese text across wide screens. Use `font-feature: traditional` where supported for regional glyph forms.

## Layout

**Desktop (1024px+):** Content max-width 1200px, centered, with 32px side gutters. Two-column or three-column layouts where content supports comparison or persistent filtering. Header sticky, navigation horizontal with secondary menu on hover.

**Tablet (768–1023px):** One column, narrower gutters (16px), simplified navigation. Persistent bottom navigation for frequent destinations. Full-screen overlay for secondary menu.

**Mobile (320–767px):** Single column, 16px gutters. Bottom navigation bar (44px safe-area inclusive) for 4–5 frequent destinations. Full-screen overlay menu for secondary links. Hero and featured sections reduced height but not removed.

**Spacing rhythm:** Major sections separated by `spacing.xl` (48px); internal card groups by `spacing.lg` (24px); content within cards by `spacing.md` (16px). Reduce by one step on mobile.

## Elevation & Depth

Depth expressed through tonal layers and subtle borders, not heavy shadows. Card surfaces raise above canvas through light background color and 1px border on `surface-variant`. Overlays and modals use a semi-transparent scrim (40% opacity on primary) to isolate focus. Hover and focus effects use `outline` or border-color change, never shadow stacking. This keeps visual clarity and avoids rendering cost.

## Shapes

**Radius:** Consistent small radius (4–8px) applied to buttons, inputs, and cards. Deliberate exceptions: none on major sections and full-bleed media. Sharp corners signal precision and reading content; small radius signals interactive components.

## Components

**Button (primary):** Warm copper background, white text, 12px vertical / 24px horizontal padding. Hover: copper darkened 10%. Active: copper darkened 20%. Disabled: surface-variant background, muted text. Focus: visible 2px outline in primary color.

**Button (secondary):** Light taupe background, dark text. Otherwise follows primary button behavior.

**Card:** Cream surface, dark text, 8px radius, 16px padding. 1px border in surface-variant for subtle separation. Hover: slight upward shift (2px `transform: translateY`), shadow emergence (0 2px 8px rgba(0,0,0,0.1)), no color change. Mobile: remove hover effect; press state only.

**Input field:** Cream background, dark text, 4px radius, 10px padding. 1px border in on-surface-variant, focus: 2px border in accent. Placeholder text muted.

**Link:** Copper text, no underline by default, underline on hover and focus. Visited state: darken copper slightly.

**Navigation (desktop):** Dark background, white/light text, large horizontal items (16px padding), dropdown on hover with 300ms ease-in-out. Highlights primary destination in accent color.

**Navigation (mobile):** Bottom bar, 5 items max, icon + label, white/light background, dark text. Active item uses accent color. Pressing item opens primary route or triggers menu overlay.

Responsive component behavior: maintain one interactive identity across sizes. A desktop filter sidebar becomes a full-screen overlay sheet on mobile with identical filter state and form controls. Do not create hidden duplicates with repeated IDs; recompose via CSS or use mutually exclusive templates with equivalent focus and state.

All states include at least one non-color cue: outline, position, weight, underline, or icon change. Form errors marked with error color plus bold descriptive text. Selection marked with accent color plus checkmark icon.

## Do's and Don'ts

- **Do:** Use serif type for book culture authority; clean sans for functional UI. Treat the bookstore as a trusted curation, not a generic marketplace.
- **Do:** Keep color semantic and minimal. Copper means action; brown means primary content; error and success only for status.
- **Do:** Test all interactive states and responsive breakpoints with real content—book titles, prices, descriptions, ratings.
- **Do:** Support Traditional Chinese (`zh-Hant`) as the first-class language; use region-aware fallbacks for Taiwan/Hong Kong glyph preference.
- **Don't:** Overuse shadows or depth effects. Tonal separation and borders are sufficient.
- **Don't:** Add effects not named in the visual grammar. No gradients, glows, or animations without a product task.
- **Don't:** Change type roles per page. Maintain consistent hierarchy across all routes.
- **Don't:** Invent a second design system for edge cases; extend or normalize the existing tokens.
