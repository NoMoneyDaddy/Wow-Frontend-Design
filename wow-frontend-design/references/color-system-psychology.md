# Color systems, contrast, and psychology

Use this reference when selecting, implementing, or auditing color; supporting light/dark/high-contrast appearances; or making claims about emotion, trust, persuasion, brand meaning, or conversion.

## Keep four questions separate

1. **Access:** can people perceive text, controls, focus, charts, and state?
2. **System:** does each semantic role behave consistently across surfaces and states?
3. **Identity:** does the palette express verified brand or product meaning?
4. **Behavioral hypothesis:** is a proposed color effect contextual, ethical, and testable?

A palette can be accessible but incoherent, coherent but off-brand, or attractive without causing the claimed behavior. Never use one result to prove another.

## Contrast is a rendered-pair property

For WCAG 2.2 A/AA work, apply the official criteria and exceptions rather than a remembered slogan:

- normal text and text in images: at least `4.5:1`;
- qualifying large text: at least `3:1`;
- essential control/state boundaries and graphical objects needed to understand content: at least `3:1` against adjacent colors;
- color is never the only cue for an instruction, link, status, selection, error, chart series, or required field.

Sources: [WCAG 2.2 contrast minimum](https://www.w3.org/TR/WCAG22/#contrast-minimum), [non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast), and [use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color).

Measure the colors that actually render. Alpha, gradients, images, video, blend modes, filters, shadows, antialiasing, overlays, disabled state, hover, and parent backgrounds can invalidate a token-pair calculation. Sample worst-case areas of dynamic backgrounds and provide a stable scrim or solid fallback when the range cannot be bounded.

An evaluator can freeze known opaque sRGB token pairs and run the included advisory calculator:

```bash
python3 <skill-dir>/scripts/contrast_pair_audit.py <evaluator-owned-pairs.json>
```

The manifest must state the actual foreground/background appearance and required ratio. Missing pairs, alpha/compositing, media, browser rendering, and conformance remain outside this check; the implementation model must not edit the manifest to make a run pass.

Do not treat these as shortcuts:

- an OKLCH lightness difference does not prove a WCAG contrast ratio;
- grayscale does not simulate every color-vision difference;
- a Lighthouse/axe pass does not prove all rendered pairs or full WCAG conformance;
- APCA experiments do not replace the contrast algorithm required by the currently claimed WCAG version;
- disabled-control exceptions are not permission to make essential instructions illegible.

Focus must be visible, unobscured, and distinguishable in every supported appearance. WCAG 2.2 `2.4.13 Focus Appearance` is AAA, not AA; do not mislabel it, although its area/contrast model is a useful stronger product target.

## Build semantic roles, not a hex collection

Freeze roles before values:

```text
canvas → surface-1 → surface-2 → overlay
text-primary → text-secondary → text-disabled
border-subtle → border-strong → focus
action → action-hover → action-pressed → action-disabled
selected → info → success → warning → danger
data-1…n → data-reference → data-missing
```

For each relevant component, audit this matrix:

```text
role × surface × default/hover/focus/active/selected/disabled/loading/error/success
     × light/dark/increased-contrast/forced-colors
```

Color roles need non-color companions: label, icon, pattern, position, outline, or shape. Status and brand colors must not silently share a role when that makes decoration look actionable or makes an action look like an error.

Keep independent record dimensions orthogonal. Urgency, lifecycle status, due state, assignment, and selection must not recolor one another's label. The same semantic value uses the same role and non-color cue wherever it appears; an overdue row may emphasize its due label or boundary, but must not silently turn an unchanged lifecycle status into an error state.

Use Oklab/OKLCH when perceptually steadier ramps, interpolation, or controlled chroma are useful, with sRGB-compatible fallbacks and gamut testing. CSS Color 4 describes the spaces and their interpolation properties; it does not guarantee accessible contrast or device equivalence. See [CSS Color Module Level 4](https://www.w3.org/TR/css-color-4/).

When the support matrix needs progressive enhancement, put the broad fallback first and the wide-gamut value second:

```css
:root {
  --brand-action: #365fe0;
  --brand-action: oklch(57% 0.18 254);
}
```

The quoted `oklch()` string is also valid in official `DESIGN.md` color frontmatter; see [design-md-contract.md](design-md-contract.md). Keep the source-of-truth role synchronized with the CSS fallback pair. Test out-of-gamut clipping/mapping and the resolved browser color at every supported appearance instead of treating the authored OKLCH coordinates as rendered evidence.

Define:

- a lightness ladder with named surface and text roles;
- a chroma budget: where vivid color is permitted and why;
- a hue policy for action, status, data, and brand roles;
- a gamut/fallback policy for wide-color values;
- a data-palette policy for adjacency, labels, missing values, and print/export.

## Appearance is a composition, not an inversion

When light/dark support is in scope, implement at least the system preference. Offer a `system | light | dark` control only when product context or user need justifies an app-specific setting. A complete three-state implementation has:

- `color-scheme` matching only the appearances the surrounding UI truly supports;
- semantic token values independently tuned for each appearance;
- `prefers-color-scheme` as the system source, with explicit choice overriding it;
- persistence only after explicit choice, guarded against unavailable storage;
- an early, CSP-compatible initialization path that avoids a wrong-theme flash;
- live response to system changes while `system` remains selected;
- theme-aware native controls, focus, scrollbar behavior where styleable, icons, charts, illustrations, images, code, syntax highlighting, embeds, email/share previews, and browser UI metadata;
- separate light and dark visual captures at the same route, state, viewport, locale, and content;
- `forced-colors: active` and increased-contrast behavior that does not preserve decorative brand color at the cost of system legibility.

Dark surfaces usually need independently calibrated foregrounds, muted text, borders, chroma, imagery, and elevation. Pure inversion, pure black everywhere, bright white body text, or a low-opacity border copied from light mode often produces glare or lost hierarchy. Raised dark surfaces may become lighter, but depth must remain consistent with the product's material grammar. Platform guidance is a reference, not a universal web mandate: [Apple Dark Mode](https://developer.apple.com/design/human-interface-guidelines/dark-mode) and [Apple Color](https://developer.apple.com/design/human-interface-guidelines/color).

### Cross-platform preference boundary

The web contract comes from [CSS Color Adjustment Level 1](https://www.w3.org/TR/css-color-adjust-1/) and [Media Queries Level 5](https://www.w3.org/TR/mediaqueries-5/): author color schemes, system preference media, and forced user palettes are distinct mechanisms. `prefers-contrast` may report `more`, `less`, `custom`, or `no-preference`; do not treat every match as “increase contrast.” In forced colors, prefer system colors and preserve user overrides; use `forced-color-adjust` only for a narrow semantic reason, never to protect branding from the user's accessibility palette.

Native guidance informs device testing but does not transfer property-for-property to the web. Windows Contrast Themes use a small user-selected palette ([Microsoft Contrast Themes](https://learn.microsoft.com/en-us/windows/apps/design/accessibility/high-contrast-themes)); Android expects system theme, contrast, dynamic color, system UI, splash, and font preferences to be handled by the native theme contract ([Android themes](https://developer.android.com/design/ui/mobile/guides/styles/themes)); Apple light/dark, increased contrast, differentiate-without-color, reduce-transparency, invert-colors, and visionOS behavior differ again. Record actual OS, browser/runtime, input, font scaling, contrast/theme setting, and real/emulated device. A Chromium desktop forced-colors capture does not prove iOS Safari, Android Chrome/WebView, or a native client.

## Color psychology: evidence, not a lookup table

Reject deterministic recipes such as “blue creates trust,” “red increases conversion,” “green means sustainable,” or “black is premium.” They collapse several different outcomes:

- perceptual salience;
- learned association;
- affect or preference;
- semantic interpretation;
- task speed/error;
- memory;
- click, purchase, retention, or other behavior.

Research supports contextual relationships, not a universal UI palette. Elliot and Maier describe color effects as dependent on context and meaning ([2014 review](https://doi.org/10.1146/annurev-psych-010213-115035)). Ecological valence theory relates preference to affective responses toward associated objects rather than fixed hue essence ([Palmer & Schloss, 2010](https://doi.org/10.1073/pnas.0906172107)). Cross-national work finds both recurring patterns and language, nation, geography, and age variation; neither similarity nor difference authorizes a deterministic conversion rule ([Jonauskaite et al., 2020](https://doi.org/10.1177/0956797620948810), [Jonauskaite et al., 2024](https://doi.org/10.1111/bjop.12687)).

Before using a psychological claim, record:

```text
claim → exact outcome → population/locale/context → source and evidence type
      → transfer assumption → alternative explanations → harm/ethics guardrails
      → validation method → status: SUPPORTED | HYPOTHESIS | REJECTED | UNKNOWN
```

Brand history, category convention, copy, imagery, price, shape, layout, prior exposure, device, lighting, and interaction state can dominate hue. Preserve explicit brand associations; mark observed or inferred associations as hypotheses. Never infer a user's personality, ability, culture, or vulnerability from a color preference.

For experiments, predefine the primary outcome and guardrails, keep copy/layout/function constant, sample the target locale and appearance modes, check accessibility first, and retain neutral/error metrics—not only clicks. A statistically different CTA click rate does not prove trust, comprehension, long-term value, or a general color law. Do not use false urgency, disguised ads, asymmetric consent, or error-like color merely to increase action.

## Weak-model contract

Require this compact record before implementation:

```text
COLOR ROLES: semantic role → meaning
LIGHTNESS LADDER: canvas/surface/text/border hierarchy
CHROMA BUDGET: where vivid color may appear
STATE DISTINCTION: color + non-color cue
APPEARANCE: system/light/dark/contrast support and fallback
PSYCH CLAIM: SUPPORTED | HYPOTHESIS | REJECTED | UNKNOWN
TEST: rendered pair/state/viewport/appearance and evidence tool
```

If the model cannot supply a meaning and a test, reduce the palette to neutrals plus one action color. Never let the model's own ratio estimate, color name, confidence, or screenshot description count as evidence.

## Release blockers

- Required text, focus, control, status, or graphical information fails the applicable rendered contrast requirement.
- Color is the sole carrier of required meaning.
- A supported appearance exposes unreadable text, invisible boundary/focus, wrong native-control scheme, or incompatible imagery.
- Dynamic media can pass beneath text without a bounded contrast treatment.
- A psychological or conversion claim is presented as fact without applicable evidence.
- A theme is declared supported from source keywords without rendered, stateful checks.
