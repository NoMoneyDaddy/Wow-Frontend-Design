# Localization and multilingual layout

Use this reference for every interface containing user-facing language. Treat localization as a layout input, not final copy replacement. Chinese typography guidance here is informed by the continuously updated W3C CLReq Draft Note; it is not a conformance certification.

## Contents

1. Locale policy
2. Traditional Chinese first-class support
3. Typography and line breaking
4. Cross-language resilience
5. Bidirectional text and IME input
6. Localization QA

## 1. Locale policy

- Preserve the user's language and the product's established terminology.
- Use valid BCP 47 tags such as `zh-Hant`, `zh-Hant-TW`, `en`, or `ar`; choose region only when behavior or vocabulary is region-specific.
- Separate message identifiers from display strings in multilingual products.
- Use locale-aware APIs for dates, times, numbers, currency, lists, plural rules, collation, and relative time.
- Never concatenate translated sentence fragments. Use complete messages with named placeholders.
- Do not encode locale in flags; language and country are not equivalent.
- Keep accessible names, metadata, errors, empty states, email text, and social previews localized too.
- Preserve user-entered names and content. Do not transliterate without a product requirement.

## 2. Traditional Chinese first-class support

Preserve an explicit or clearly detected script. If the user writes `zh-Hans`/Simplified Chinese, keep it unless conversion is requested; if the user writes `zh-Hant`/Traditional Chinese, keep it. Only when Chinese input is script-ambiguous and no script or market is specified, default product-owned copy to Traditional Chinese.

For `zh-Hant` work:

- Prefer a market-specific tag such as `zh-Hant-TW` or `zh-Hant-HK` when vocabulary, glyphs, or punctuation are regional. Use `zh-Hant` only for genuinely region-neutral Traditional Chinese content.
- Use Traditional characters consistently. Do not mix Simplified Chinese through copied labels, generated copy, or fallback assets.
- Match regional vocabulary. Examples vary by market: `帳號/賬號`, `影片/視頻`, `程式/程序`, `資訊/信息`. Do not “correct” an established glossary casually.
- Prefer natural Chinese information order over translated English syntax.
- Avoid unnecessary English uppercase eyebrows, forced letter spacing, and slash-heavy microcopy around Chinese headings.
- Use full-width Chinese punctuation in Chinese sentences. Keep Latin punctuation inside code, identifiers, URLs, or English spans.
- Do not use a Simplified-only font or image containing mismatched glyph forms.
- Review machine conversion between Simplified and Traditional Chinese; character conversion alone does not localize vocabulary or meaning.

Example font stack for a neutral sans interface:

```css
:root {
  --font-sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
    "PingFang TC", "Noto Sans TC", "Microsoft JhengHei", sans-serif;
}

:lang(zh-Hant) {
  font-family: var(--font-sans);
  line-break: strict;
  word-break: normal;
}
```

Do not apply `overflow-wrap: anywhere` to all Chinese content: it can split proportional Western words at arbitrary points. Apply it only to URLs, identifiers, or unbroken user content that demonstrably overflows; mark language spans correctly and use appropriate hyphenation where supported.

Choose brand fonts only after confirming Traditional Chinese glyph coverage and the required weights. A Latin display face can pair with a CJK reading face, but align apparent size, stroke contrast, and baseline optically.

## 3. Typography and line breaking

- Use [typographic-layout.md](typographic-layout.md) to calibrate measure, line height, wrapping, spacing, and vertical writing. Its numeric ranges are comparison candidates, not universal optima.
- Avoid Latin-style positive tracking on Chinese paragraphs. Apply tracking only to deliberate short display treatments.
- Keep body lines comfortable rather than stretching Chinese copy across wide screens.
- Prevent punctuation from becoming visually stranded. Use browser line-breaking behavior and manual non-breaking spans only for essential names, dates, or short units.
- Keep numbers and units together when necessary, but do not create large unbreakable blocks.
- Use `text-wrap: balance` or `pretty` as progressive enhancement, then verify fallback wrapping.
- Use real vertical writing (`writing-mode: vertical-rl` with appropriate `text-orientation`) only when editorial meaning justifies it; never rotate the text container. Provide the same readable content horizontally for controls, dense product text, and constrained responsive modes.
- Never bake text into images merely to control line breaks.

## 4. Cross-language resilience

Design for these stress cases:

- German or Finnish expansion;
- short Chinese or Japanese labels changing visual balance;
- Arabic or Hebrew RTL order;
- mixed Latin/CJK names and numbers;
- plural categories beyond singular/plural;
- long personal names, addresses, currencies, and time zones;
- user-selected 200% text size;
- fonts loading late or not at all.

Implementation rules:

- Use logical CSS properties and direction-aware icons.
- Mirror spatial navigation icons in RTL when they indicate direction; do not mirror universal media, brand, or check icons blindly.
- Avoid fixed-width buttons and fixed-height text containers.
- Allow navigation labels to grow or switch composition.
- Keep icons and labels semantically paired even when order changes.
- Format data at display time with locale APIs; store canonical values.
- Provide a locale switcher that names languages in a recognizable form and preserves the current route when possible.

## 5. Bidirectional text and IME input

- Derive the document `lang` and `dir` from the trusted locale at server render and after an intentional locale change. Do not guess document direction from one user-entered string.
- Isolate mixed-direction user data with semantic boundaries such as `bdi` or a carefully scoped `dir="auto"`; keep labels, values, icons, punctuation, and focus order coherent. Do not globally force `unicode-bidi` or visual-order text to make one screenshot look correct.
- Preserve phone numbers, codes, URLs, paths, timestamps, and mixed CJK/Latin identifiers as logical data. Test selection, copying, truncation, ellipsis, and screen-reader order—not only visual alignment.
- Treat invisible bidi controls in filenames, identifiers, code-like content, logs, and security-sensitive comparisons as a review risk. Preserve legitimate language content while escaping or visibly identifying controls where the product context requires it.
- Support IME composition. Do not submit, search, filter, validate, format, slugify, or reject text on `keydown` while `event.isComposing` is true. Handle `compositionstart/update/end`, `beforeinput`, and `input` according to the framework/browser contract.
- Pressing Enter during Chinese/Japanese/Korean candidate selection must not trigger form submission or commands. Do not normalize full-width characters, move the caret, or replace the controlled value mid-composition.
- Test paste, autofill, deletion, undo/redo, emoji/grapheme clusters, dead keys, speech input, and mobile virtual keyboards when those paths affect the workflow. Key-code-only logic is not text-input support.

## 6. Localization QA

Verify at least:

1. source locale;
2. Traditional Chinese (`zh-Hant`);
3. an internally defined expanded pseudo-locale (30–100% is a stress heuristic, not a language standard);
4. an RTL locale when the product claims RTL support;
5. mixed-script user content.

Check:

- no clipped or overlapping text;
- headings wrap intentionally;
- controls keep accessible names and visible labels aligned;
- dates, prices, units, list punctuation, and sorting are correct;
- navigation and breadcrumbs preserve direction and hierarchy;
- font fallback does not create tofu, wrong glyph variants, fake weights, or large layout shifts;
- screenshots, SVG text, charts, canvas, and generated metadata are localized;
- search and input accept the target script;
- Chinese/Japanese/Korean IME composition completes without premature submit, filtering, validation, caret jumps, or lost characters;
- mixed RTL/LTR content preserves logical reading, copy/paste, focus, icon direction, truncation, and accessible order;
- translated error and empty states remain actionable.

If a native speaker review was not available, say so. Do not describe automated or model-generated copy as culturally verified.
