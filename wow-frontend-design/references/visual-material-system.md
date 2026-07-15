# Visual material and craft system

Use this reference when borders, type, component color, depth, light, texture, visual effects, or animation must form one coherent interface language.

## Start with one material sentence

Describe how the interface behaves as a visual object:

```text
material → edge behavior → light/depth model → surface hierarchy → motion character
```

Examples are hypotheses, not presets: archival paper with ruled edges and stepped reveals; precision instrument with hairlines and mechanical state changes; luminous spatial display with a bounded ambient layer and crisp controls.

The sentence must serve product meaning. Do not mix paper grain, glass blur, neon bloom, plastic buttons, deep shadows, and spring motion simply because each looks polished in isolation.

## Borders and edges

Borders may separate, group, indicate state, define hit area, or express material. Name the job before styling.

- Define `subtle`, `default`, `strong`, `focus`, `selected`, and `danger` roles instead of per-component opacity guesses.
- Align border radius with component scale and nesting. A child radius normally derives from the parent's inner curve, padding, and border width; one arbitrary radius everywhere erases hierarchy.
- A CSS `1px` line can map to different device pixels and antialias differently across DPR, transforms, zoom, and fractional layout. Inspect at target DPR/zoom; do not depend on a subpixel hairline to carry essential state.
- Prefer whitespace or tonal separation when a border adds noise but no grouping information.
- In tables, decide between row rhythm, column guides, section rules, and full cell grids from the scan task. Full boxes around every cell often obscure hierarchy.
- Interactive boundaries and focus need sufficient adjacent contrast; decorative dividers do not become required non-text contrast merely by existing.

CSS defines border/background/shadow paint order and geometry; it does not choose a good material system. See [CSS Backgrounds and Borders Level 3](https://www.w3.org/TR/css-backgrounds-3/).

## Typography as structure and material

Route font licensing, CJK coverage, loading, subsetting, and fallback details through [typography-webfonts.md](typography-webfonts.md). Then define visible behavior:

- roles: display, reading, functional, numeric/code;
- axes: size, optical size, weight, width, grade, slant, tracking, line height;
- script behavior: Traditional Chinese punctuation, Latin/CJK baseline and visual-size balance, fallback metrics, numerals, units, emphasis, ruby where applicable;
- density: measure and paragraph rhythm for reading; stable width/tabular numerals for comparisons;
- failure: no synthetic bold/italic unless intentional, no hidden text while fonts fail, no layout-breaking metric swap.

Hierarchy needs more than size. Use a limited combination of weight, width, spacing, placement, rule, and contrast. Tiny uppercase Latin eyebrow labels are not a universal replacement for real CJK hierarchy. Inspect rasterization at actual sizes and weights; a specimen at 72px does not prove UI text at 13–16px.

## Component color and state

Use the semantic roles and appearance matrix in [color-system-psychology.md](color-system-psychology.md). A component recipe records:

```text
surface + text + icon + border + focus + state overlay
× default/hover/focus/active/selected/disabled/loading/error/success
× light/dark/increased-contrast/forced-colors
```

Do not let hover be the only affordance, disabled be a low-opacity version of everything, selected look identical to focus, or brand color simultaneously mean action, success, and decoration. Keep comparable controls optically equal even when label lengths or glyph shapes differ.

## Light, depth, and shadow

UI shadows are a communication model, not physically correct rendering. Still, internal consistency matters:

- Choose one dominant light direction or an intentionally ambient/no-direction system.
- Map elevation to overlay/occlusion/interaction need, not prestige. A card does not need a shadow merely because it is a card.
- Keep shadow offsets, softness, spread, opacity, and highlight direction compatible across components.
- Use contact shadows or border/tonal changes for near surfaces; larger/softer shadows for truly separated layers. Avoid equally dramatic shadows on nested surfaces.
- Dark mode needs new surface and shadow values; copying black shadows onto near-black or simply inverting light mode loses depth.
- Over photography, video, gradients, and canvas, bound the background range with a scrim or stable surface before placing required text/controls.

Treat platform systems as case studies. For example, Apple's material guidance ties thickness/transparency to legibility and context; it is not a reason to copy platform glass into every web brand. See [Apple Materials](https://developer.apple.com/design/human-interface-guidelines/materials).

## Transparency, blur, texture, and glow

Every effect needs a semantic job and fallback:

| Effect | Defensible jobs | Common failure |
| --- | --- | --- |
| transparency/blur | preserve spatial context for an overlay | unstable contrast, GPU cost, generic glass identity |
| grain/noise | material cue, banding control | dirty text, compression shimmer, high paint cost |
| glow/bloom | bounded active/live/emissive signal | everything looks active; text loses edge contrast |
| gradient | light/material field, data or state transition | decorative gradient stack with no hierarchy |
| blend/filter | controlled art direction | browser differences, unreadable fallback |

Set an effect budget: affected area, layers, blur radius, animation, target devices, fallback, and evidence. Test `forced-colors`, reduced transparency where available, printing/export if relevant, low-power/mobile conditions, and effect-disabled rendering. Essential hierarchy cannot depend on backdrop filtering or compositing support.

## Select effects; do not distribute them everywhere

Run every proposed effect through this selector:

```text
product meaning → target role → semantic job → visual priority
→ affected area/count → fallback → contrast/input/motion cost → rendered evidence
```

- Default to one signature effect and only the supporting effects needed to make it coherent. Repeating a special effect on every component destroys hierarchy and raises fallback cost.
- Permit an effect only when its target role and job are named. A border may group, separate, show state, or express material; hollow display type may create one editorial/technical signature. “Looks premium” is not a job.
- Keep body prose, form labels/values, errors, warnings, legal terms, prices, transaction data, and ordinary buttons solid and immediately readable.
- Treat decorative `0.5px` hairlines as optical experiments only after target DPR/zoom inspection; never let them carry essential state or boundary meaning.

Hollow/outlined type is opt-in display treatment, not a global typography mode. Start with a solid fallback, enable the stroke only when supported, and restore solid system text in forced colors:

```css
.outline-display {
  color: var(--outline-fallback);
}

@supports (-webkit-text-stroke: 1px currentColor) {
  .outline-display {
    color: transparent;
    -webkit-text-stroke: 1px var(--outline-stroke);
  }
}

@media (forced-colors: active) {
  .outline-display {
    color: CanvasText;
    -webkit-text-stroke: 0;
  }
}
```

Inspect actual Traditional Chinese and Latin glyphs at the target font, weight, size, browser, DPR, zoom, background, and fallback font. A stroke that works on a large Latin display word may close counters, thin radicals, or disappear on CJK. Never make a transparent fill the only declaration; unsupported rendering must remain readable.

Visible assets have a stricter boundary than abstract surface geometry. Do not fake products, people, places, logos, evidence, photographs, illustrations, or icons with CSS/div art, handcrafted SVG, text symbols, or placeholder boxes. Use approved source assets, generated image assets when authorized, or a matching icon library. CSS may form non-factual structural geometry such as a bounded divider, grid, mask, or material field when it has a named job and fallback.

## Motion belongs to the same physics

Use [motion-system.md](motion-system.md) for runtime and accessibility. Make motion agree with the material:

- rigid/instrumental systems favor precise, short, damped changes;
- paper/layer systems may reveal, fold, mask, or slide from a meaningful edge;
- spatial systems may use depth and parallax only when orientation remains clear;
- state feedback is faster and smaller than navigation or narrative transition.

Record `purpose → origin/target → duration/easing → interrupt/reverse → reduced result`. A modal should emerge from or relate to its trigger/context, exit without leaving stale state, and never delay access to required content. Avoid using the same fade-up for every section.

## Craft audit

Inspect rendered desktop and mobile states, not tokens alone:

1. Blur the screenshot: are focal point and surface levels still clear?
2. Convert to grayscale: do composition and hierarchy survive without destroying required color cues?
3. Inspect at 100%, 200%, 400%/reflow, target DPR, light/dark, and forced colors.
4. Compare repeated edges, radii, icon strokes, baselines, numerals, shadows, highlights, and animation origins.
5. Disable effects, custom fonts, images, and motion separately; core meaning and operation must remain.
6. Capture the same route/content/state before and after; record browser, viewport, DPR, theme, locale, and preference media.
7. Turn every optional effect off and verify that task hierarchy remains; then inspect the effect only on its selected roles to confirm it has not spread to all components.

## Weak-model freeze card

```text
MATERIAL:
EDGE ROLES:
TYPE ROLES/AXES/FALLBACK:
SURFACE + COMPONENT STATE MATRIX:
LIGHT DIRECTION + DEPTH LEVELS:
EFFECT BUDGET + FALLBACK:
MOTION PHYSICS + REDUCED RESULT:
RENDERED TEST MATRIX:
```

If two adjacent choices contradict this card, remove the less meaningful effect. A model's adjectives such as “premium,” “soft,” “cinematic,” or “high contrast” are not evidence.

## Release blockers

- Required component state relies on a hairline, shadow, color, or animation that disappears in a supported context.
- Type fallback, script coverage, synthetic style, or font loading breaks reading or layout.
- Light direction, edge, radius, surface, and motion rules conflict enough to obscure hierarchy.
- Blur/glow/media creates unbounded text or control contrast.
- A continuous or expensive effect has no budget, pause/cleanup, reduced result, or static fallback.
- Light/dark variants are mechanical inversions or are claimed without rendered inspection.
- Hollow/outlined type is applied to required reading, form, error, legal, price, or transaction content; lacks a solid fallback; or becomes illegible in CJK, fallback fonts, forced colors, or supported DPR/zoom.
- A visible factual or iconic asset is approximated with CSS/div art, text symbols, placeholder boxes, or handcrafted SVG.
