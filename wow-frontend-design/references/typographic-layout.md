# Typographic layout and spacing

Use this reference when reading comfort, line length, leading, wrapping, vertical writing, component/card spacing, density, or optical type choice materially affects the interface. These are calibration rules, not universal aesthetic constants.

## 1. Separate evidence from starting values

```text
script + exact font + task + viewport + density + input method
→ candidate measures/spacing
→ rendered comparison
→ comprehension/task/overflow evidence
→ chosen tokens and exceptions
```

- Do not call one line length, line height, spacing scale, or card padding “optimal” for every product. Reading length, typeface metrics, script, age, visual acuity, display, and task change the result.
- WCAG 2.2 text-spacing values—`1.5` line height, `2` paragraph spacing, `0.12em` letter spacing, and `0.16em` word spacing—test whether content survives a user's overrides. They are **not** mandated author defaults or proof of ideal typography.
- Treat external design-system numbers as context-specific examples. Carbon's 2/4/8 increments, GOV.UK's responsive spacing, and USWDS's type/measure guidance do not become product requirements by citation.
- Prefer a small candidate set, compare rendered evidence, and record why the selected value fits this content. Do not tune only the hero screenshot.

## 2. Calibrate reading measure and vertical rhythm

For extended Traditional Chinese horizontal reading, begin exploration around `17–40` full-width characters per line. CLReq reports this as common publication practice, with shorter lines usually no fewer than `10` and horizontal lines often no more than `48`; it is a research envelope, not a web conformance limit. Test at the actual phone and desktop widths. For mixed Latin/CJK, do not assume Latin `ch` predicts Han measure; prefer the rendered line count or a verified `ic`-based measure with a fallback.

Use these candidates to start comparison, not to bypass it:

| Role | Candidate to compare | Evidence to inspect |
| --- | --- | --- |
| long CJK body | `1.5–1.8` line height; roughly `20–40` Han characters | regressions, rereading, punctuation, 200% text, font fallback |
| compact UI copy | `1.35–1.6` line height; shorter measure | label clipping, target height, translation, scan speed |
| display heading | `1.05–1.3` line height; intentional 1–3 lines | glyph crop, punctuation, balanced fallback, hierarchy |
| paragraph separation | about `0.75–1.25` body line | grouping without breaking narrative continuity |

CLReq notes publication line gaps commonly around `50–100%` of the character frame. Use that only to justify comparing generous CJK leading; excessive leading can weaken line tracking. A Chinese proofreading study found spacing, line count, and their interaction affected time and detection, so validate the actual task instead of claiming a single fastest value.

Rhythm rules:

- derive spacing from the current type metrics and density mode, not isolated pixels;
- keep heading-to-content space smaller than the space before the next section;
- use one mechanism for flow gaps—parent `gap` or child margin—not stacked accidental margins;
- let content determine block height. Fixed-height text containers are exceptional and must survive font failure, translation, and text resize;
- align repeated baselines when it improves scanning, but allow optical correction for CJK punctuation, icons, and dissimilar font metrics.

## 3. Set Chinese tracking and wrapping deliberately

- Keep ordinary Chinese body text at `letter-spacing: normal` or the font's intended solid setting. Do not spread every Han character to imitate Latin display typography.
- Never compress tracking to make a line fit. Eye-movement evidence shows decreased Chinese inter-character spacing can disrupt reading; increased spacing is not a universal improvement either.
- Reserve positive tracking for short display text, running heads, captions, poetry, or an audience-specific treatment that has been rendered and reviewed.
- Set the correct `lang`; use `line-break: strict` only where target-browser behavior is verified, keep general prose at `word-break: normal`, and apply `overflow-wrap: anywhere` only to genuinely unbroken data such as URLs or identifiers.
- Keep semantic short units together—date + time, number + unit, a person's full short name—without wrapping entire sentences in `nowrap`.
- Use `text-wrap: balance` for short headings and `text-wrap: pretty` for prose only as progressive enhancement. Verify the fallback because CSS Text Level 4 behavior and support continue to evolve.
- Inspect line starts/ends for stranded punctuation, paired marks, ruby/annotation, Latin runs, and long user content. Manual `<br>` is allowed only when the content contract truly fixes the phrase and the responsive/fallback result is tested.

## 4. Build real vertical writing

Use semantic text with CSS writing modes:

```css
.vertical-copy {
  writing-mode: vertical-rl;
  text-orientation: mixed;
}
```

- Do not rotate a horizontal container with `transform`. Rotation breaks line construction, punctuation behavior, selection geometry, sizing, and often reading order.
- `vertical-rl` lays lines from right to left. Use logical properties (`inline-size`, `block-size`, `margin-inline`, `padding-block`) and test scroll direction, source order, selection, copy, keyboard focus, and assistive output.
- Keep ordinary Han characters upright; verify punctuation glyphs and positions. Test mixed Latin, numerals, dates, abbreviations, and units. Use upright or short horizontal-in-vertical runs only when the content convention calls for them.
- CLReq reports vertical publication lines commonly around `10–40` characters and often no more than `55`; use this only as a starting envelope. Avoid fixed inline sizes that clip a line after fallback-font or mobile changes.
- Use vertical writing where it adds editorial meaning. Dense controls, forms, tables, and task instructions need a readable horizontal composition.
- At breakpoints where vertical text no longer reads comfortably, render the same content as a horizontal equivalent and preserve the brief's identity/test hook. Do not merely hide the required vertical element and add unrelated copy.

## 5. Choose fonts by measured behavior

Choose per role rather than searching for one “best” family:

| Role | Prioritize |
| --- | --- |
| long reading | Traditional Chinese coverage, open counters, stroke clarity, punctuation, comfortable metrics |
| compact UI | small-size clarity, stable widths, complete weights, unambiguous numerals/symbols |
| display/brand | distinctive voice without losing required glyphs or forcing image text |
| data/code | numeral differentiation, tabular forms where useful, units/symbols, alignment |

- Test the exact released binaries at the final CSS size and target displays. Family category alone—serif, sans, rounded, humanist—does not establish readability.
- Compare apparent size, stroke density, counters, punctuation, baseline, and line box. Equal CSS `font-size` does not mean equal optical size.
- Confirm Taiwan/Hong Kong glyph forms, product vocabulary, rare names, Latin pairing, symbols, and every shipped weight. Avoid synthetic styles unless explicitly accepted.
- Build a complete locale-aware fallback. Measure `font-size-adjust`, `size-adjust`, ascent/descent, and line-gap overrides before using them; metric matching must not crop glyphs or controls.
- Record source/version/hash, license, files, subset, privacy/CSP, loading behavior, and failed-font result. A beautiful font with unverified rights or broken fallback is a release defect.

## 6. Space components and cards by relationship

Use a compact token palette such as `4 / 8 / 12 / 16 / 24 / 32 / 48 / 64px` as a calibration set, then map semantic relationships to it. Do not expose raw values as arbitrary component props.

```text
icon ↔ label / metadata          smallest
label ↔ control / related rows  small
card internals / field groups   medium
sibling components              medium–large
section ↔ section               largest
```

- The parent layout owns the distance between siblings. The component owns its internal padding and state geometry.
- Related items must be closer than unrelated items. If every gap is equal, grouping disappears; if every surface has a border/radius, hierarchy flattens.
- Define comfortable and compact density modes as coherent token sets. Do not shrink only padding while leaving type, targets, and row rhythm mismatched.
- Preserve at least the product's target-size requirement and test touch, keyboard focus, 200% text, translated labels, error/help text, and virtual-keyboard conditions.
- Card padding must follow content density and available inline size. Compare `12/16px` compact, `16/24px` regular, and `24/32px` spacious candidates only where the content supports them; mobile may change the composition, not automatically halve every token.
- Use cards for meaningful containment, selection, drag, media entities, or independent states. Prefer open sections, rows, lists, tables, or dividers when content belongs to one continuous surface. Avoid nested cards unless each layer has a distinct interaction or stacking role.
- Align interactive rows optically, not just mathematically. Icons, CJK glyph boxes, badges, and numerals can need small documented corrections.

## 7. Verify the rendered typography system

Capture and inspect:

1. actual smallest supported phone, short phone, desktop, 200% text, and 400%/reflow;
2. normal and failed/late custom font, every required weight, long `zh-Hant`, mixed Latin/numerals, rare names, and user content;
3. representative short, average, and longest lines; punctuation at boundaries; headings wrapping to 2–3 lines;
4. vertical text with punctuation, Latin/numerals, the horizontal responsive equivalent, and preserved identity/test hook;
5. every density mode; cards with empty/short/long/error states; menus/overlays closed on first capture;
6. no text crop, horizontal overflow, fake truncation, fixed/sticky obstruction, or `overflow: hidden` used to conceal a failed measure.

Record the tested font version, viewport, locale, content fixture, candidate values, selected tokens, and screenshot/result paths in the evidence. A clean token file without rendered evidence is not validation.

## Primary and official sources

- [W3C WCAG 2.2 Understanding 1.4.12: Text Spacing](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing)
- [W3C Requirements for Chinese Text Layout](https://www.w3.org/TR/clreq/)
- [W3C CSS Writing Modes Level 3](https://www.w3.org/TR/css-writing-modes-3/)
- [W3C CSS Text Module Level 4](https://www.w3.org/TR/css-text-4/)
- [W3C CSS Fonts Module Level 5](https://www.w3.org/TR/css-fonts-5/)
- [Effects of line length, line spacing, and line number on Chinese proofreading](https://journals.sagepub.com/doi/10.1177/0018720813499368)
- [Eye movements of older and younger Chinese readers under inter-character spacing changes](https://jps.ecnu.edu.cn/EN/Y2020/V43/I1/68)
- Context examples only: [Carbon spacing](https://carbondesignsystem.com/elements/spacing/overview/), [GOV.UK spacing](https://design-system.service.gov.uk/styles/spacing/), [USWDS typography](https://designsystem.digital.gov/components/typography/)
