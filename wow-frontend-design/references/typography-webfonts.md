# Typography and webfont system

Use this reference when typography, font selection, custom/open-source fonts, CJK coverage, variable fonts, subsetting, or font loading is material. Typography is part of information architecture and product voice; a font gallery is only discovery.

Pair this with [typographic-layout.md](typographic-layout.md) when choosing rendered size, measure, leading, wrapping, vertical writing, spacing rhythm, or optical fit.

## 1. Write the type contract

```text
content/languages → reading context → type roles → family/face/version → glyph/feature coverage → fallback metrics → delivery/subset → privacy/CSP → license/notices → performance budget → evidence
```

- Choose body, display, UI, numeric/code, and data roles from content density, tone, reading length, device context, and language—not industry stereotypes.
- Use the fewest families, weights, styles, axes, and files that create a real hierarchy. A variable font is useful only when the shipped axes/ranges replace enough static files or enable a justified behavior.
- Test the exact released font binaries. A family name does not prove Taiwan/Hong Kong glyph forms, punctuation, Latin pairing, OpenType features, variable-axis behavior, or emoji/symbol coverage.
- Keep real text in the DOM. Do not path-convert headings merely to preserve typography.

## 2. Select and license open fonts

For every font file, record:

```text
family + source repository/release + version/hash + exact file + license + reserved font names + modification/subset status + required notice + allowed product surfaces
```

- Verify the license distributed with the exact font release. A webfont service or software repository license does not automatically cover every hosted font.
- OFL generally permits web embedding and commercial use. Pure WOFF/WOFF2 wrapping can remain unmodified only when the original font data and metadata are preserved; glyph/feature removal and most subsetting create a Modified Version. Check Reserved Font Names, naming requirements, and retain the license/attribution required by the exact release. Do not relabel an OFL font as MIT with the application.
- Treat desktop, web, app embedding, document/PDF, logo, video, server generation, and redistribution as separate rights when the font is not under a verified open license.
- Keep font notices in a machine-readable asset manifest or third-party notices file even when no visible attribution is required.

Strong open Pan-CJK starting points include the official [Noto CJK](https://notofonts.github.io/noto-docs/website/use/) and [Source Han Sans](https://github.com/adobe-fonts/source-han-sans) releases. They are candidates, not universal defaults; choose the correct Traditional Chinese Taiwan/Hong Kong region and test product vocabulary.

## 3. Build locale-aware fallback

- Declare correct document and component language so shaping, glyph selection, line breaking, speech, and generic fallbacks can adapt.
- Keep region-aware CJK fallbacks; do not assume one Han font has the preferred glyph forms for `zh-Hant-TW`, `zh-Hant-HK`, `zh-Hans`, `ja`, and `ko`.
- Test punctuation position, paired punctuation, mixed Latin/numerals, ruby/annotations, vertical text when used, bold/italic synthesis, rare names, symbols, currency, dates, and user-generated text.
- Prevent faux bold/italic where they damage CJK or brand text; load the real face or explicitly accept the fallback result.
- Match fallback metrics with `size-adjust`, `ascent-override`, `descent-override`, and `line-gap-override` only from measured fonts. Recheck clipping, line boxes, controls, and CLS.

Use [W3C Chinese Layout Requirements](https://www.w3.org/TR/clreq/) for Chinese composition behavior and [CSS Fonts Module Level 4](https://www.w3.org/TR/css-fonts-4/) for font matching/descriptors. Both still require target-browser rendering tests.

## 4. Deliver the smallest resilient font path

- Prefer WOFF2 for web delivery and keep original/source releases outside the public bundle when not required. WOFF2 is a transport format, not proof of a lawful or correct subset.
- Self-host when privacy, availability, version pinning, CSP, caching, or predictable performance matters. A third-party service adds DNS/TLS, outage, policy, referrer/IP, cache, and data-processing boundaries.
- Inline only the small `@font-face` declarations when it improves discovery; do not base64-inline large CJK fonts.
- Use `unicode-range` only with correct, non-overlapping subsets that preserve shaping/feature closure. Test punctuation and mixed-script runs; a codepoint list alone can omit required glyph substitutions.
- Preload only a proven first-view face actually used by above-fold text, with matching URL/format/type/CORS. Preload bypasses some `unicode-range` negotiation and can compete with the LCP image, CSS, or script.
- Choose `font-display` per role and measured arrival: `swap`, `fallback`, and `optional` have different readability, brand, and CLS tradeoffs. Do not set one global value by ritual.
- Cache immutable versioned font URLs; configure correct MIME/CORS; avoid mutable CDN URLs and query-dependent binaries that cannot be reproduced.
- Keep a complete system-font fallback. Font failure must preserve content, controls, line wrapping, and task completion.

The [W3C WOFF2 Recommendation](https://www.w3.org/TR/WOFF2/) defines the format. [web.dev font practices](https://web.dev/articles/font-best-practices) is implementation guidance, not a fixed project budget.

## 5. Treat dynamic subsetting as a data flow

Runtime glyph subsetting can reduce CJK bytes, but it may inspect and transmit rendered text. Freeze:

```text
DOM scope → fields excluded → exact characters sent → endpoint/operator → retention/logging → auth/consent → cache key → mutation/route updates → failure fallback → license/RFN → CSP → evidence
```

- Never send password, verification, payment, health, identity, private message, unpublished content, form value, or user-generated secret to a font service.
- Exclude inputs, textareas, editable regions, hidden/private nodes, and authenticated data by default. A visual class is not a privacy boundary.
- Handle text added after hydration/navigation without repeatedly scanning the entire DOM or leaking transient values.
- Bound request size/frequency, deduplicate glyphs locally, cancel stale work, and preserve a local fallback during service failure.
- A server-generated subset is a modified font; verify its license/name/notice and deterministic build provenance.

### emfont assessment

Pinned research source: [`elvisdragonmao/emfont@85158ad`](https://github.com/elvisdragonmao/emfont/tree/85158adc26313d73878b5ead0734d4540c46399a), service [font.emtech.cc](https://font.emtech.cc/fonts).

- The service software repository contains Apache-2.0 text, but each hosted font still needs its own license and exact-file provenance.
- Its documented CSS endpoint is convenient discovery/prototyping, but production still inherits third-party availability, CSP, cache, privacy, and version-drift risk.
- Its optional JavaScript runtime scans descendant `textContent`, placeholders, and input/textarea values, posts collected characters to the service, and stores response metadata in `localStorage`. Therefore it is opt-in only and prohibited for sensitive/authenticated scopes unless the product explicitly approves and constrains that data flow.
- Its `words=` URL mode can place requested characters in CDN, proxy, server, analytics, or browser logs. At the pinned audit date, the public `/privacy` and `/terms` routes returned 404 and no dependable retention policy or SLA was found; absence of a published policy is not permission to transmit product text.
- Prefer self-hosted, versioned, prebuilt subsets for stable product copy. Use dynamic remote subsetting only after privacy, licensing, failure, cache, and mutation behavior are verified.

The catalogue's “open source” label is a lead, not proof that every font has identical rights or complete Traditional Chinese coverage.

## 6. Verify typography as rendered behavior

Test at minimum:

- slow/blocked font, warm/cold cache, offline, and font-service failure;
- 320 CSS px, short mobile, desktop, 200% text resize, and 400%/reflow;
- `zh-Hant-TW`, claimed `zh-Hant-HK`, mixed Latin/numerals, long labels, rare/user names, and other shipped locales;
- every shipped weight/style/axis and synthetic-style behavior;
- fallback before/after swap: line count, control size, crop, focus, hit target, LCP and CLS;
- network requests, bytes by route/locale/face, cache headers, MIME/CORS/CSP, and duplicate downloads;
- legibility in light/dark/forced colors and on actual target displays.

Release blockers include missing glyphs/tofu in primary tasks, wrong regional forms that change product correctness, hidden text during a failed font load, unverified font rights, sensitive text sent to a font service, and layout/task breakage when the custom font is unavailable.
