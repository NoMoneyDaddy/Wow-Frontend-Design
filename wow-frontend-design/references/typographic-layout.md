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

### A1 checkpoint: make every wide column earn its occupied area

Before choosing a wide-screen grid, map each major region to its task stage, source order, expected content height, minimum readable width, and mobile position. A column is not justified merely because a compact card, vertical note, or control can fit beside the main content.

- Keep unrelated task stages in sequential full-width regions. Do not stack a short display note and a later form beside a long article when this leaves either column continuing alone through a large empty rectangle.
- Use two columns only when both regions belong to the same reading or task moment and benefit from simultaneous visibility. If one column ends while the other continues through another substantial component, move the later component below the shared row or recompose the parent grid.
- Preserve task completeness while repairing composition. Never remove, hide, or demote required comparison evidence, current selection/status, validation feedback, primary actions, or the resulting summary merely to eliminate a void or shorten the page. Recompose those elements into the task stage that owns them, then verify the complete default-to-result flow.
- Treat vertical writing as display content with its own measured block. It must not become a tall narrow spacer that determines the height of an otherwise unrelated article or form. Preserve the same semantic text as a horizontal region at an applicable declared narrow/mobile breakpoint.
- For a long horizontal Traditional Chinese product title with no simultaneous task peer, let the title and intro span their owning surface. If the title reaches four lines or ends with a stranded one- or two-Han tail, widen or recompose before reducing type size or editing copy.
- Do not apply a Latin `ch` cap directly to CJK product copy. Give extended prose a coherent reading surface, but do not leave that surface floating at the start of a substantially wider empty owner.
- Inspect the whole page after default and interaction states at declared representative viewport profiles. When none are declared, conservatively sample wide/short desktop plus 390 px and 360 px without inventing support. Reject a layout with a detached summary, a side stack outliving its peer, a large unexplained void, or a later control visually appearing before the content that explains it.

Record the major-region parent, reading order, each declared viewport composition, and the void or detachment signal in `DESIGN.md`. When browser evidence is unavailable, label the layout `UNVERIFIED`; source intent alone cannot prove that the columns remain balanced.

## 2. Calibrate reading measure and vertical rhythm

For extended Traditional Chinese horizontal reading, begin exploration around `17–40` full-width characters per line. CLReq reports this as common publication practice, with shorter lines usually no fewer than `10` and horizontal lines often no more than `48`; it is a research envelope, not a web conformance limit. Test at the actual phone and desktop widths. For mixed Latin/CJK, do not assume Latin `ch` predicts Han measure; prefer the rendered line count or a verified `ic`-based measure with a fallback.

Use these candidates to start comparison, not to bypass it:

| Role | Candidate to compare | Evidence to inspect |
| --- | --- | --- |
| long CJK body | `1.5–1.8` line height; roughly `20–40` Han characters | regressions, rereading, punctuation, 200% text, font fallback |
| compact UI copy | `1.35–1.6` line height; shorter measure | label clipping, target height, translation, scan speed |
| display heading | `1.05–1.3` line height; intentional 1–3 lines | glyph crop, punctuation, balanced fallback, hierarchy |
| paragraph separation | about `0.75–1.25` body line | grouping without breaking narrative continuity |

Measure the script that is actually rendered:

| Content | Primary measure | Starting comparison, not a pass threshold |
| --- | --- | --- |
| Traditional Chinese horizontal prose | full-width character count, rendered line count, punctuation at edges | explore roughly `17–40` Han characters |
| English horizontal prose | words/characters plus rendered line count | compare the USWDS `45–90` character envelope and roughly `66`-character long-form target |
| Mixed CJK/Latin/Arabic | per-language spans, visual line count, bidi and unbroken-run behavior | do not reduce the line to one global `ch` value |
| Vertical Chinese | characters per column, column count, progression, punctuation | explore roughly `10–40` characters; verify the real block size |

For automated triage, a long horizontal CJK paragraph below about `6em` inline size is a strong repair signal; `6–10em` deserves manual inspection. This is a defect heuristic for squeezed layouts, not a preferred reading measure. Exclude assistive-only text and inspect computed writing mode before applying it.

CLReq notes publication line gaps commonly around `50–100%` of the character frame. Use that only to justify comparing generous CJK leading; excessive leading can weaken line tracking. A Chinese proofreading study found spacing, line count, and their interaction affected time and detection, so validate the actual task instead of claiming a single fastest value.

Rhythm rules:

- derive spacing from the current type metrics and density mode, not isolated pixels;
- keep heading-to-content space smaller than the space before the next section;
- use one mechanism for flow gaps—parent `gap` or child margin—not stacked accidental margins;
- let content determine block height. Fixed-height text containers are exceptional and must survive font failure, translation, and text resize;
- align repeated baselines when it improves scanning, but allow optical correction for CJK punctuation, icons, and dissimilar font metrics.

Hierarchy and whitespace rules:

- choose one intended focal anchor per task region, then let heading, supporting copy, evidence, and action descend in a stable order; several equally large, saturated, or isolated elements destroy the entry point;
- use proximity semantically: keep a label, value, helper, and action close enough to read as one group, then use a larger outside gap before the next group;
- make title-to-intro spacing smaller than intro-to-next-region spacing unless the product's editorial system explicitly says otherwise;
- do not maximize occupancy. Quiet space is functional when it isolates the focal task or separates groups, but a narrow copy rail beside an empty track is still a defect;
- evaluate scale relationships with the exact font and script. Fixed claims such as “headings are always 2–3× body text” are comparison prompts, not cross-locale pass thresholds.

### Role-based type hierarchy

Choose a small role ladder before styling elements. Semantic heading rank describes document structure; it does not force one global visual size. Map each rendered role to a shared token, then keep the mapping stable across equivalent components.

| Role | Starting comparison | Typical job |
| --- | --- | --- |
| metadata/caption | `0.8125–0.9375rem`, `1.4–1.6` leading | short status, timestamp, helper; not extended prose |
| UI/body | about `1rem`, `1.5–1.75` CJK leading | controls, instructions, normal product copy |
| component title | `1.125–1.375rem`, `1.2–1.4` leading | card, field group, local decision block |
| section/dialog title | `1.375–2rem`, `1.1–1.3` leading | task region or focused overlay |
| page/display title | fluid from roughly `2rem`, `1.05–1.2` leading | one page-level focal anchor |

These values are a bounded candidate set, not an accessibility standard. Calibrate them with the exact `zh-Hant` font, density, distance, fallback, and text-resize behavior. Use role, size, weight, color, and proximity together, but do not make every axis shout. Adjacent roles need a visible distinction; nearby one-pixel size changes usually do not establish hierarchy by themselves.

- Give a dialog title its primary inline track before laying out badges, status, close controls, or helper metadata. On a narrow viewport, move secondary items below or into another region before reducing the title measure.
- Keep badges and eyebrows visibly subordinate to the title. They may share a row only when the title still produces a deliberate 1–3-line composition with no stranded final fragment at every required width.
- Use fluid type for expressive page headings and stable role tokens for dense product components. Do not make every heading fluid merely because `clamp()` is available.
- Compare computed role relationships, not HTML names alone. An `h3` used as a compact card label can be visually smaller than nearby body copy only when another cue preserves its structural role and the result remains clear to sighted users.

## 3. Set Chinese tracking and wrapping deliberately

- Keep ordinary Chinese body text at `letter-spacing: normal` or the font's intended solid setting. Do not spread every Han character to imitate Latin display typography.
- Never compress tracking to make a line fit. Eye-movement evidence shows decreased Chinese inter-character spacing can disrupt reading; increased spacing is not a universal improvement either.
- Reserve positive tracking for short display text, running heads, captions, poetry, or an audience-specific treatment that has been rendered and reviewed.
- Set the correct `lang`; use `line-break: strict` only where target-browser behavior is verified, keep general prose at `white-space: normal` and `word-break: normal`, and apply `overflow-wrap: anywhere` only to genuinely unbroken data such as URLs or identifiers. Do not apply `word-break: keep-all` to all Chinese prose: it can make mixed Latin/CJK strings or constrained components overflow.
- Keep semantic short units together—date + time, number + unit, a person's full short name—without wrapping entire sentences in `nowrap`.
- Use `text-wrap: balance` for short headings and `text-wrap: pretty` for prose only as progressive enhancement. `word-break: auto-phrase` may improve CJK phrase segmentation in a supporting engine, but dictionaries and fallback behavior vary. Verify the exact phrase boundaries and the fallback because CSS Text Level 4 behavior and support continue to evolve.
- Inspect line starts/ends for stranded punctuation, paired marks, ruby/annotation, Latin runs, and long user content. Manual `<br>` is allowed only when the content contract truly fixes the phrase and the responsive/fallback result is tested.

### Browser-owned body flow

- Treat normal paragraphs like a word-processor or text-board content column: the container establishes stable left/right edges and the browser fills each line until a legal break. Source newlines and visual card boundaries must not decide ordinary body wrapping.
- Choose the content column first, then let its paragraph use the available inline size. Do not set a narrow `max-width` on `p` while leaving most of its otherwise empty card unused. When a shorter measure is required, resize or align the containing region, or place real adjacent content in the remaining track.
- Compare the rendered text track with the owning header/card, not only with the immediate parent. On a wide desktop region, roughly half-width title or intro copy plus hundreds of pixels of unused space needs review unless the remaining track contains real navigation, status, evidence, comparison, or task controls. A decorative split, empty peer, or ordinary paragraph moved to the right does not earn the space.
- Use font-relative measures for font-relative reading goals. For horizontal CJK, prefer an `em`/verified `ic` cap plus rendered full-width-character checks; do not treat root-relative `rem` or Latin `ch` as a universal CJK measure.
- Short UI copy, forms, tables, and dynamic text normally use `text-align: start`. Extended Traditional Chinese editorial prose may compare `text-align: justify` with `text-justify: auto` or `inter-character`, but keep the final line start-aligned (`text-align-last: start`) and inspect punctuation, mixed Latin, links, and narrow screens. Justification is a content-mode choice, not a global locale rule.
- Do not insert `<br>` in paragraphs or list copy to imitate a screenshot. Split distinct ideas into semantic paragraphs and let the browser reflow them. A forced break belongs only to fixed display copy, a pull quote, poetry, or another explicit attention treatment; mark that intent in the component, provide an unforced fallback, and test every required width, locale, zoom level, and fallback font.
- Preserve normal wrapping under translation and user content. `white-space: nowrap` belongs to verified short atomic units, not sentences; `pre`/`pre-wrap` belongs to content whose whitespace is data, such as code or transcripts.

Choose the paragraph mode per content region; do not mix the signals accidentally:

| Mode | Paragraph boundary | Alignment and wrapping | Typical use |
| --- | --- | --- | --- |
| product/UI | compact semantic paragraphs or grouped rows | `start`; normal wrap | forms, settings, dashboards, task copy |
| web editorial | visible `margin-block` between `<p>` elements, usually no indent | compare `start` with tested justification | articles, guides, documentation |
| book-like editorial | first-line indent, little or no paragraph gap | tested justification or publication convention | deliberate reading/heritage experiences |
| display/poetry | author-approved phrase/line structure | scoped forced breaks with responsive fallback | verse, pull quotes, fixed campaign copy |

- Do not combine a two-character indent, a full blank line, and a large paragraph margin unless the editorial system intentionally requires all three. Never type ideographic spaces to simulate CSS indentation.
- The line-height and paragraph-gap examples in design articles—often around `1.5–1.75` and `0.5–1em`—are useful comparison candidates, not a universal recipe. Compare the exact font, column width, density, and reading task.
- A body weight such as `300`, a `62.5%` root size, or one hosted font stack is an implementation example, not a readability rule. Preserve user font scaling; select weight from rendered stroke clarity and ensure the fallback does not become too light or change line count catastrophically.

### Paragraph structure, tone, and semantic wrapping

- Separate plainness from tone. Plain language controls vocabulary, sentence structure, and information order; tone controls formality, warmth, address, and product voice. A friendly tone does not justify vague wording.
- Let each paragraph carry one main idea or task consequence. Lead with the decision, state, or action; put conditions and supporting detail after it. Prefer concrete verbs and nouns over evaluator or marketing adjectives.
- Keep product copy in the user's world. Do not write implementation claims such as “mobile-first,” “responsive,” or “crafted layout” into the interface.
- Use realistic short, average, long, error, and translated copy during layout. Placeholder length cannot prove rhythm.
- Treat headings as phrases, not arbitrary boxes. Inspect 1–3-line outcomes at adjacent widths and with fallback fonts; avoid orphaned particles, verbs detached from objects, stranded punctuation, and especially a final line containing only one Han character. Do not use Latin `ch` as a hard CJK heading cap: the unit follows the zero glyph and can produce a roughly half-Han track. Size the containing region first, then use a rendered Han line count or verified `em`/`ic` measure. If a forced display break earns attention on one width, verify a responsive unforced or differently composed version rather than preserving the same break everywhere.
- Inspect actual line rectangles and the owning track. If a multi-line heading's longest rendered line still occupies less than roughly `60%` of a wide empty track, first remove the artificial cap or rewrite the heading; balancing two equally short lines is not a successful composition. Short one-line titles may naturally end early and should not be stretched or justified.
- Use `text-wrap: balance` as progressive enhancement for short headings. Insert manual breaks only for fixed, approved copy after every required width and locale has been checked; never encode a line break inside a reusable heading component by default.
- Short action labels normally stay on one line. If the label wraps, either the component explicitly supports a multi-line action or the layout must recompose; do not squeeze a normal command into a tall narrow button.
- For an ordinary one-line action, protect the label with an atomic inline box and keep the control from shrinking below its content; move, stack, or widen the action group before applying smaller type. Do not place `nowrap` on sentences or use it to conceal an undersized layout.
- For normal multi-line Traditional Chinese product copy, compare a rendered line-height around `1.5–1.75` before choosing a tighter value. Display sizes, dense tables, and specialist reading modes may differ, but body paragraphs near `1.2–1.35` require explicit font/size/measure evidence and are a preflight risk.

### Punctuation, mixed scripts, and optical display alignment

- Keep full-width Traditional Chinese punctuation and corner-bracket quotation marks when the locale/editorial authority calls for them. Select a `zh-Hant-TW` or `zh-Hant-HK` font stack whose glyph forms and punctuation placement match the market; a font fallback that silently switches regional forms is a defect.
- CLReq describes up to `1/4em` between adjacent Han and Western letters/numerals in horizontal composition, except at line edges. Treat this as a composition envelope. Do not insert ordinary spaces between every script transition or rewrite the DOM with JavaScript: that changes copy, search, selection, accessibility, line breaking, and justification. `text-autospace` and `text-spacing-trim` are CSS Text Level 4 progressive enhancements; verify support and avoid double-spacing source text.
- Preserve line-start/line-end punctuation rules. Never add generated `<wbr>`, `<font>`, `<kbd>`, or hidden spaces after every Han character or punctuation mark. Those legacy workarounds predate current engines and damage semantics. Use correct `lang`, normal browser breaking, scoped `line-break`, and rendered boundary tests.
- Do not use global `word-break: break-all`, `line-break: anywhere`, or `word-break: keep-all` to make the right edge look full. Keep prose at normal breaking. Apply `overflow-wrap: anywhere` or a comparably scoped escape hatch only to verified unbroken data such as a raw URL, hash, or identifier, then test intrinsic sizing and copy behavior.
- Centered display headings can look optically offset when a full-width terminal punctuation glyph has asymmetric ink. Inspect the actual font and every wrap first. Prefer editing fixed display copy or a font-supported/predictable treatment; do not absolutely position live punctuation or add one-line padding without testing selection, copy, localization, zoom, and 1–3-line layouts.
- Avoid a single short semantic fragment on the last heading line. Prefer copy editing or `text-wrap: balance`/`pretty` as enhancement. If `auto-phrase` still splits a compact lexical unit, a short non-breaking span is acceptable only when that exact unit remains compact at every required width, locale, zoom, and fallback font and cannot create overflow; do not wrap the last words of arbitrary body paragraphs in `nowrap`.

## 4. Build real vertical writing

Use semantic text with CSS writing modes:

```css
.vertical-copy {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  inline-size: fit-content;
  max-inline-size: min(var(--verified-column-length, 28em), 70dvh);
  align-self: start;
}
```

- Do not rotate a horizontal container with `transform`. Rotation breaks line construction, punctuation behavior, selection geometry, sizing, and often reading order.
- `vertical-rl` lays lines from right to left. Use logical properties (`inline-size`, `block-size`, `margin-inline`, `padding-block`) and test scroll direction, source order, selection, copy, keyboard focus, and assistive output.
- In vertical writing, the inline axis is physical height and the block axis is physical width. Bound the rendered column length with a content-sized `inline-size` and an evidence-derived `max-inline-size` so short copy does not stretch while long copy can form additional columns along the block axis. A `max-width` cap only constrains the vertical box's block axis; it cannot prevent one unbounded, page-height column. The `28em` fallback and `70dvh` cap above are candidates to compare, not universal limits; replace the custom property with the rendered selection.
- Do not use grid stretch, `min-height: 100%`, viewport-height padding, or an unrelated peer's height to size a vertical note. Let the verified inline size own its height, keep the item at block/inline start, and move the note below the article when its complete text still makes the shared row substantially taller than the reading region. Never clip, mask, or scroll away required text to make the row look balanced.
- Keep ordinary Han characters upright; verify punctuation glyphs and positions. Test mixed Latin, numerals, dates, abbreviations, and units. Use upright or short horizontal-in-vertical runs only when the content convention calls for them.
- CLReq reports vertical publication lines commonly around `10–40` characters and often no more than `55`; use this only as a starting envelope. Avoid fixed inline sizes that clip a line after fallback-font or mobile changes.
- Use vertical writing where it adds editorial meaning. Dense controls, forms, tables, and task instructions need a readable horizontal composition.
- At breakpoints where vertical text no longer reads comfortably, render the same content as a horizontal equivalent and preserve the brief's identity/test hook. Do not merely hide the required vertical element and add unrelated copy.

### Semantic ruby and Bopomofo

When Traditional Chinese pronunciation is part of the content, keep the base character and annotation as data. Do not encode a reading by replacing the Han glyph with a combined “annotated character” font glyph, image, canvas, or generated SVG.

- Use simple, single-sided semantic `<ruby>` with explicit `<rb>` and `<rt>`. For Bopomofo, start from character-level mono ruby such as `<ruby><rb>我</rb><rt>ㄨㄛˇ</rt></ruby>`; it preserves the base/reading relationship and lets adjacent character pairs break independently.
- Follow the content authority for Unicode and tone order. CMEX's Mandarin convention places second/third/fourth tone marks after the Bopomofo sequence and the neutral-tone dot before it. Mandarin first tone is absence of a displayed mark and occupies no slot; do not insert U+02C9 merely because an input method uses it internally. Do not normalize Taiwanese/Hakka annotations to Mandarin sequences.
- Preserve source characters as spacing Bopomofo tone code points such as U+02CA/U+02C7/U+02CB. A font may substitute internally positioned glyphs through OpenType; source HTML must not pre-convert the reading to U+0301/U+030C/U+0300 combining marks just to imitate one font implementation.
- Keep interleaved ruby markup compact. Whitespace or source line breaks inside `<ruby>` can render as unwanted spaces in some browsers. Verify formatter output, DOM order, selection, copy, find-in-page, and fallback—not only the screenshot.
- When Bopomofo is shown inline without a Han base, separate complete syllables so two readings cannot merge visually or trigger the wrong font sequence. Treat this as linguistic content spacing, not ordinary letter tracking.
- Prefer simple interleaved mono/group ruby for a cross-engine baseline. Tabular ruby, double-sided ruby, `rtc`, jukugo behavior, and nested structures have uneven Blink/Gecko/WebKit layout support; use them only behind an explicit support matrix and fallback.
- Treat `ruby-position: inter-character` as progressive enhancement. W3C's 2026 browser review reports that simple ruby works across major engines, but Bopomofo side placement is still incomplete: WebKit positions the run vertically beside the base yet does not fully position tone marks, while Blink/Gecko keep it above. Never claim correct cross-browser Bopomofo from this property alone.
- Precise tone placement may require a provenance-checked OpenType font with appropriate `ccmp`, `vert`, `salt`, optional `hist`, or GPOS/GSUB behavior. Confirm the exact font license, version/hash, code-point sequence, feature activation order, HarfBuzz/CoreText behavior, loading/fallback, and each supported browser/OS. Do not apply a specialty Bopomofo font to the whole body as an untested workaround; it can change CJK/Latin metrics.
- Keep ruby annotation tracking at the font's expected solid setting unless that exact face proves otherwise. CMEX's 2019 GSUB sample warns that nonzero `letter-spacing` and inter-character justification can displace out-of-frame replacement glyphs. Test annotated prose inside justified paragraphs even when the surrounding Han body is allowed to justify.
- Keep three contracts separate: HTML ruby maps base ↔ reading; CSS/browser places the annotation around the Han base; OpenType shapes tone/coda positions inside the reading. The CMEX PDF explicitly covers only the third contract, not Bopomofo-to-Han placement or visual quality.
- Repository examples around `26%` or `30%` annotation size are historical implementation examples, not a universal accessibility token. Choose `rt` size, line gap, and annotation density for the actual typeface, audience, viewport, zoom and reading task. Provide a readable inline/expanded pronunciation mode when small ruby becomes illegible.
- Likewise, the PDF's roughly `2/3` tone-mark and `1/2` coda proportions are reference glyph-design ratios relative to a Bopomofo glyph, not a universal CSS `rt` size relative to the Han base.
- If correct right-side Bopomofo is essential and the target engine cannot render it, preserve semantic ruby and use an honest fallback—such as over-base annotation or an accessible pronunciation view. Do not fake success with image text or hide the annotation.
- Test horizontal and vertical base text, light tone and other tones, long annotated prose, line breaks, mixed unannotated text, custom-font failure, 200% text spacing/zoom, and the declared Blink/Gecko/WebKit matrix. Named screen-reader testing is required before claiming pronunciation accessibility; DOM semantics alone do not prove announcement behavior.

## 5. Choose fonts by measured behavior

CLReq's glyph-shaping section distinguishes four major Chinese composition styles—Song/Ming, Kai, Hei, and Fangsong—and documents their publication roles. It does not rank one as the universally most readable screen font. Map the role first, then verify the exact digital face: Song/Ming can carry long editorial text or heavier headings; Kai can distinguish quotations, dialogue, references, or an intentional official/editorial voice; Hei commonly supports UI, signs, headings, captions, and emphasis; Fangsong is a specialized literary/secondary-title voice. Do not substitute synthetic oblique CJK for any of these roles.

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

Before choosing Grid/Flex tracks, write a compact placement record for each major region:

```text
region → priority → information/task role → min/ideal/max inline size → state changes
       → mobile placement → vertical-writing placement → failure signal
```

- Use intrinsic sizing deliberately. Grid/flex automatic minimums and high-specificity state selectors can keep a desktop track alive on mobile, squeezing prose into a column without causing page overflow.
- A layout can fail without clipping: a detached confirmation summary, a large unexplained void, an oversized mobile navigation block, or a narrow text rail beside empty space still damages task flow.
- A dedicated visual track must earn its width through evidence, status, interaction, navigation, verified identity, or necessary atmosphere. Remove an `aria-hidden`/decorative peer column when it only forces a heading, form, table, or summary into an inferior measure. Do not replace a missing asset with CSS/div art or an empty frame.
- Prefer `minmax(0, 1fr)` or an explicit intrinsic minimum where a flexible track may shrink, and give text-bearing children `min-inline-size: 0`; then verify that the resulting measure is still readable.
- Recompose after interaction. Open panels, filtered result counts, validation messages, and success summaries need their own placement check instead of inheriting the default-state grid.

Horizontal and vertical composition have different placement rules. In horizontal Chinese, columns progress top-to-bottom and normal tables place the header row above. In vertical Chinese, text columns progress from right to left; table/header/caption placement must follow the intended vertical reading axis rather than rotating the horizontal layout. Keep forms, dense controls, and long task instructions horizontal unless an explicit product/editorial reason earns a vertical equivalent.

## 7. Verify the rendered typography system

### Optional Pretext measurement lane

[Pretext](https://github.com/chenglou/pretext) is useful when a character-count heuristic cannot explain a wrap, height, or label overflow. If `@chenglou/pretext` is already available in the authorized project, use its browser-font-engine measurement APIs as a fast preflight:

```ts
const prepared = prepareWithSegments(text, exactCanvasFont, {
  whiteSpace: computed.whiteSpace === "pre-wrap" ? "pre-wrap" : "normal",
  wordBreak: computed.wordBreak === "keep-all" ? "keep-all" : "normal",
  letterSpacing: parseFloat(computed.letterSpacing) || 0,
})
const stats = measureLineStats(prepared, contentWidth)
const layoutResult = layout(prepared, contentWidth, computedLineHeight)
```

Use the same loaded font, CSS width, `white-space`, `word-break`, `overflow-wrap`, `letter-spacing`, locale, and content fixture as the rendered page. Record the candidate's line count, max line width, height, and exact input. Use `layoutWithLines()` or `walkLineRanges()` for headings, buttons, chips, and mixed inline content where the final line matters. This can replace the current character-count estimate as a diagnostic signal, not as an acceptance claim.

The lane is optional and fail-soft. The packaged adapter at `scripts/pretext_typography_adapter.mjs` reports `unavailable` when the package or its required `OffscreenCanvas`/DOM canvas capability is absent; keep the existing Playwright/DOM path in that case. Its pinned contract models only horizontal `writing-mode`, `white-space: normal | pre-wrap`, `word-break: normal | keep-all`, finite pixel `letter-spacing`, and `overflow-wrap: break-word`; it returns `invalid` with `reasonCode: unsupported_css_text_behavior` for explicit CSS values it cannot reproduce instead of silently claiming a measurement. A measured result records the normalized options and its claim boundary. Run measurement in a browser-capable context for real font metrics. Pretext does not model complete CSS layout, grid/flex tracks, padding, pseudo-elements, line clamp, transforms, fallback timing, or browser accessibility. Confirm every candidate with `document.fonts.ready`, computed styles, Playwright screenshots, and the actual interaction viewport. Do not install it or edit a lockfile merely to make a visual claim.

### Evaluator-owned rendered proof lane

When the controlled evaluator provides browser contract v2, use its bounded assertions instead of converting the guidance above into new global heuristics:

- `font-face-loaded` proves that the selected element names the evaluator-approved family and a matching `FontFace` reached `loaded`; it does not prove glyph coverage, regional forms, license, fallback quality, or aesthetic fit;
- `line-count-between` proves the rendered horizontal line count for the exact content, font state, viewport, and browser in that case;
- `last-line-graphemes-at-least` catches an evaluator-declared stranded final fragment for fixed short display copy without counting UTF-16 code units as characters;
- `no-content-overflow` proves local scroll/client geometry only where the selected region is not meant to scroll.

The generic HTML smoke receipt also records a bounded `single_han_last_line_heading_count` advisory for visible horizontal `h1` or level-one ARIA headings whose rendered final line contains exactly one Han grapheme plus optional punctuation. It scans at most the first 16 matching DOM elements and at most 512 UTF-16 code units per element; `heading_scan_count` and `heading_scan_truncated` disclose coverage. This is a discovery lead, not a failure or repair instruction: CLReq defines the observable orphan shape, but a campaign lockup, poem, or deliberate stepped heading can use it intentionally. The receipt contains only per-page/profile counts and truncation state, never the heading text. Confirm the candidate in a fresh screenshot, then use evaluator-owned `last-line-graphemes-at-least` or `text-segment-on-one-line` only when the fixed copy makes the intended boundary explicit. Do not infer Chinese phrases from `Intl.Segmenter` word mode, add a global `keep-all`, or promote this advisory to a release gate.

Keep these thresholds outside model-owned output. A model must not inspect its result, invent a passing range, and then cite that self-authored contract as acceptance. Use separate cases or evidence for normal font, delayed/failed font, long locale, resize, and consequential interaction states; do not claim one default screenshot covers them.

Capture and inspect:

1. actual smallest supported phone, short phone, desktop, 200% text, and 400%/reflow;
2. normal and failed/late custom font, every required weight, long `zh-Hant`, mixed Latin/numerals, rare names, and user content;
3. representative short, average, and longest lines; punctuation at boundaries; headings wrapping to 1–3 intentional lines without Latin-`ch` CJK caps, compressed four-line fragments, or split lexical units;
4. vertical text with punctuation, Latin/numerals, the horizontal responsive equivalent, and preserved identity/test hook;
5. every density mode; cards with empty/short/long/error states; menus/overlays closed on first capture;
6. no text crop, horizontal overflow, fake truncation, fixed/sticky obstruction, or `overflow: hidden` used to conceal a failed measure.
7. default, filtered, expanded, validation, and success states for unexplained voids, detached summaries, squeezed columns, bloated controls, and specificity-driven breakpoint regressions.
8. ordinary paragraphs with browser-owned wrapping, no forced body `<br>`, no prose-wide `nowrap`/`keep-all`, aligned content-column edges, and no narrow paragraph floating inside an otherwise empty wide card.
9. major header/grid direct children preserve a coherent DOM/visual reading sequence; no later label or heading renders above an earlier sibling without an intentional, accessible reorder.

Record the tested font version, viewport, locale, content fixture, candidate values, selected tokens, and screenshot/result paths in the evidence. A clean token file without rendered evidence is not validation.

## Primary and official sources

- [W3C WCAG 2.2 Understanding 1.4.12: Text Spacing](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing)
- [W3C Requirements for Chinese Text Layout](https://www.w3.org/TR/clreq/)
- [W3C CSS Writing Modes Level 3](https://www.w3.org/TR/css-writing-modes-3/)
- [W3C CSS Logical Properties and Values Level 1](https://www.w3.org/TR/css-logical-1/)
- [MDN `inline-size`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/inline-size)
- [W3C CSS Text Module Level 4](https://www.w3.org/TR/css-text-4/)
- [W3C CSS Text Module Level 3](https://www.w3.org/TR/css-text-3/)
- [W3C CSS Box Sizing Level 3](https://www.w3.org/TR/css-sizing-3/)
- [W3C CSS Grid Layout Level 2](https://www.w3.org/TR/css-grid-2/)
- [W3C CSS Fonts Module Level 5](https://www.w3.org/TR/css-fonts-5/)
- [W3C Ruby Markup](https://www.w3.org/International/articles/ruby/)
- [W3C Ruby Styling](https://www.w3.org/International/articles/ruby/styling.en)
- [CMEX 數位排版中注音調號定位方式](https://www.cmex.org.tw/page.jsp?SN=&ID=33&la=0)
- [CMEX Bopomofo on Web](https://github.com/cmex-30/Bopomofo_on_Web/tree/f86d793b7995c276bd30a2b7146e9b6dfb34d1fc)
- [W3C WAI: Clear Words and Layout](https://www.w3.org/WAI/WCAG2/supplemental/objectives/o3-clear-content/)
- [GOV.UK content principles](https://www.gov.uk/government/publications/govuk-content-principles-conventions-and-research-background/govuk-content-principles-conventions-and-research-background)
- [Effects of line length, line spacing, and line number on Chinese proofreading](https://journals.sagepub.com/doi/10.1177/0018720813499368)
- [Eye movements of older and younger Chinese readers under inter-character spacing changes](https://jps.ecnu.edu.cn/EN/Y2020/V43/I1/68)
- Context examples only: [Carbon spacing](https://carbondesignsystem.com/elements/spacing/overview/), [GOV.UK spacing](https://design-system.service.gov.uk/styles/spacing/), [USWDS typography](https://designsystem.digital.gov/components/typography/)
- Context example only: [PixelCake 中文排版小技巧](https://pixelcake.com.tw/posts/chinese-typography-tips/) supports testing generous Chinese leading, near-normal body tracking, semantic paragraphing, and full-width punctuation. Its blanket alignment/line-breaking suggestions remain hypotheses; W3C CSS Text and CLReq control the interoperable rule.
- Context examples only: [GogoShark 字體與排版應用指南](https://www.gogoshark.com/blog/design/web-design/%E2%80%8B%E8%A8%AD%E8%A8%88%E5%B8%AB%E5%BF%85%E7%9C%8B%E7%9A%84%E5%AD%97%E9%AB%94%E8%88%87%E6%8E%92%E7%89%88%E6%87%89%E7%94%A8%E6%8C%87%E5%8D%97/) and [PixelCake 中文字體推薦](https://pixelcake.com.tw/posts/chinese-font-recommendations/) motivate role-based type, restrained family count, readable body faces, title/body contrast, and rendered CJK testing. Their fixed point/pixel/weight recipes, font rankings, broad serif/sans readability claims, and secondary license summaries are discovery hypotheses; verify current platform guidance and each exact font's official release/license.
- Context example only: VoltAgent's [Apple `DESIGN.md` analysis](https://github.com/VoltAgent/awesome-design-md/tree/main/design-md/apple) demonstrates role-named tokens and a responsive display ladder. Do not port its negative Latin tracking, fixed pixel sizes, proprietary SF Pro assumptions, micro-legal sizes, or breakpoint ladder to CJK. Its current unitless-zero and prose inconsistencies also show why gallery documents must be regenerated and passed through the pinned official linter.
- Context examples only: [夜月七境：中文網頁排版優化](https://piv.ink/chinese-layout-optimization/), [我是鐵：舒適的中文文章 CSS 排版](https://www.iamtie.com/2020/09/cssarticlesetting.html?m=1), [BFA：十項中文長文原則](https://www.bfa.com.tw/blog/ten-rules-that-make-articles-better-understood), and [白湯四物：中文網頁排版設計建議](https://www.fournoas.com/posts/chinese-web-typesetting-design-suggestions/) provide historical/practitioner hypotheses about paragraph rhythm, type roles, punctuation, and measure. Their fixed values, hosted-font recipes, DOM-rewriting hacks, and broad `break-all` advice are not adopted as standards.
- Context examples only: [Apple 中文排版細節](https://pudge1996.medium.com/apple-awsome-typographic-details-a5705d31417) and [探索 Web 字元換行規則](https://pudge1996.medium.com/wrap-rule-on-web-56a375c11043) motivate testing terminal-punctuation optical balance, orphan fragments, and unbroken URLs. Product-specific Apple/WeChat observations and 2021 browser behavior are not current cross-browser guarantees.
- Context examples only: [BFA 留白的藝術](https://www.bfa.com.tw/blog/5-design-skill-improve-blank), Figma's [visual hierarchy](https://www.figma.com/resource-library/what-is-visual-hierarchy/), and UXPilot's [visual hierarchy guide](https://uxpilot.ai/blogs/visual-hierarchy) support testing focal order, proximity, inside/outside spacing, progressive disclosure, and restrained visual competition. Their fixed font-count, body-size, heading-ratio, first-viewport, grid, and eye-path advice are starting hypotheses, not universal thresholds. UXPilot is a mutable product article, not independent empirical evidence.

## Legal open reading references

- [Flexible Typesetting](https://flexibletypesetting.com/) is available free from the author and is useful for responsive type relationships and testing. It does not supply universal token values.
- [Designing for the Web](https://designingfortheweb.co.uk/) is a free author/publisher edition covering practical web typography and layout. Treat its examples as context, then validate against current browser standards and this product's locale/content.

These editions may have non-commercial/no-derivatives terms. Link and paraphrase bounded methods; do not copy chapters, illustrations, or fixed value tables into this MIT repository.
