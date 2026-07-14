# Data-visualization color and access

Use this reference for charts, maps, KPIs, dashboards, scientific/financial graphics, legends, or any UI where color encodes data.

## Start from the analytical task

Record:

```text
question → data type → transformation/denominator → mark/position
→ color role → comparison/reading task → uncertainty/missing state
→ interaction → text/table alternative → evidence
```

Choose position, aligned length, order, label, shape, line style, or texture before asking hue to carry precise comparison. Color may reinforce structure; it must not be the only path to required meaning.

## Match palette to data semantics

- **Sequential:** ordered magnitude from low to high; use a perceptually ordered lightness/chroma path.
- **Diverging:** meaningful center/reference with two ordered sides; state what the center means. Do not use it merely because two hues look dramatic.
- **Qualitative/categorical:** unordered distinctions; limit simultaneous categories from the rendered task, and use direct labels, grouping, shape, or interaction as category count grows.
- **Cyclic:** direction/time/phase that wraps; endpoints must join semantically and perceptually.
- **Binary/status:** use explicit labels/icons/patterns and product status semantics, not hue alone.

ColorBrewer's cartographic research is useful for sequential, diverging, and qualitative scheme design, but map palettes do not automatically transfer to every chart, background, or UI state. See [ColorBrewer](https://colorbrewer2.org/), the [ColorBrewer paper](https://doi.org/10.1559/152304003100010929), and Brewer's [diverging-scheme research](https://doi.org/10.1179/caj.1996.33.2.79).

Avoid rainbow/spectral ramps for ordered magnitude unless the physical domain and audience convention genuinely require them and discontinuities are addressed. They can invent boundaries and unequal visual steps; see [Crameri et al., 2020](https://doi.org/10.1038/s41467-020-19160-7) and [Nuñez et al., 2018](https://doi.org/10.1371/journal.pone.0199239).

## Contrast and adjacency

- Test essential marks against their backgrounds and the least-contrasting adjacent areas under the applicable WCAG non-text rule.
- Test labels, axes, annotations, tooltips, and embedded numbers as text.
- Distinguish zero, neutral/reference, missing, suppressed, masked, not applicable, out-of-range, below detection, uncertainty, selection, and loading; transparency alone is ambiguous.
- Light/dark themes need independently tuned palettes, grids, labels, selection, hover, reference lines, and tooltip surfaces.
- Do not use a color-vision simulator as proof. Test non-color redundancy and representative users/assistive paths when risk warrants it.
- Printing, export, projector, HDR/wide-gamut, and screenshot/compression paths may change appearance; include only supported paths.

Use [color-system-psychology.md](color-system-psychology.md) for general contrast and appearance rules. Color-emotion associations do not define truthful data encoding.

## Labels, legends, and nonvisual access

- Prefer direct labels when they remain legible; otherwise keep legend order and spatial mapping stable.
- Expose a concise chart title, purpose, main pattern, important exceptions, units, period, source/provenance, and update time.
- Provide underlying values or an equivalent table/download when users need exact lookup or nonvisual exploration. Follow [W3C complex images](https://www.w3.org/WAI/tutorials/images/complex/) for appropriate alternatives.
- Interactive charts need keyboard-reachable controls, visible focus, stable accessible names, useful summaries, and a bounded strategy for many data points. ARIA on thousands of raw marks is not automatically usable.
- Tooltips cannot be hover-only and cannot contain the sole copy of required values.
- Traditional Chinese labels need actual locale terms, punctuation, units, dates, and compact-layout tests; do not rotate or shrink them into illegibility to preserve a desktop chart.

## Mobile transformation

Do not squeeze a wide dashboard into a narrow viewport. Depending on the task:

- prioritize the primary series/KPI;
- switch comparison to small multiples or a scrollable table with clear affordance;
- move filters into an accessible sheet while keeping active filters visible;
- provide a focused detail view instead of tiny marks;
- preserve data and context when orientation changes;
- keep touch exploration from blocking page scroll without an intentional gesture contract.

## Motion and truthfulness

Animation may show change, causality, filtering, or continuity. It must not delay exact values, exaggerate magnitude, reorder without explanation, or hide data on reduced motion. Freeze or replace continuous chart motion, preserve state across interruption, and keep static/export output meaningful.

Reject truncated or inconsistent axes, area/volume encodings that exaggerate values, 3D perspective that distorts comparison, cherry-picked ranges, missing uncertainty, and color scales whose semantic center does not match the data.

## Weak-model contract

```text
QUESTION / AUDIENCE:
DATA TYPE + TRANSFORM + UNIT:
MARK/POSITION:
PALETTE TYPE + CENTER/ORDER:
NON-COLOR REDUNDANCY:
ZERO/MISSING/UNCERTAINTY:
LIGHT/DARK/CONTRAST:
MOBILE + KEYBOARD + TABLE/TEXT ALTERNATIVE:
TRUTHFULNESS CHECK:
```

## Release blockers

- Required value/category/state is encoded only by color, hover, animation, or canvas pixels.
- Palette ordering/center/category mapping contradicts the data semantics.
- Missing/zero/suppressed values are visually conflated.
- Scale, axis, area, perspective, aggregation, or animation materially misrepresents the data.
- Exact values or an equivalent nonvisual path required by the task are unavailable.
- A light/dark/mobile state makes labels, marks, selection, or reference lines unreadable.
