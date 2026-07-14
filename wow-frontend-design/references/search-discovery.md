# Search, answer, and generative discovery

Use this reference when public discovery, SEO, AEO, GEO, rich results, multilingual indexing, AI search/crawlers, or agent-readable interaction is in scope. Optimize a truthful user experience that machines can retrieve and understand; never promise ranking, citation, indexing or generated-answer inclusion.

## 1. Separate the terms and evidence

- **SEO**: helps search systems discover, crawl, render, index, understand and present public pages.
- **AEO**: a market term for making useful answers easy to retrieve and cite. It has no single cross-platform standard or guaranteed answer-box recipe.
- **GEO**: an emerging research/market term for visibility in generative answers. The original [KDD 2024 paper](https://doi.org/10.1145/3637528.3671900) used controlled black-box experiments; its results vary by domain and do not prove a durable production ranking formula.

Google's current official position is that AEO/GEO for its generative Search features remains SEO: no special schema, `llms.txt`, AI markup, artificial mentions, forced “chunking”, or writing format is required. This does not remove operational controls: verify the current Search Console generative-AI inclusion control, Googlebot/snippet directives, and the separate Google-Extended policy. Other services may define different crawlers or experimental files, so route them by documented platform need rather than adding universal cargo cult.

## 2. Freeze public URL and locale policy

Before implementation record:

```text
public/private route → canonical URL → index/snippet policy → language/region URL
→ hreflang set/x-default → content owner/date → structured-data type → crawler policy
→ sitemap/feed → share surface → measurement owner
```

- Private, staging, account, cart, internal search/filter permutations and ephemeral design labs do not become indexable by accident.
- Every public page has one stable, descriptive URL and truthful status/redirect. Use crawlable `<a href>` internal links; client-side click handlers alone are not discovery.
- Put unique descriptive `<title>`, a useful page-specific meta description, canonical and locale alternates in initial HTML when possible. JavaScript must not contradict the initial canonical.
- Use separate URLs for materially translated/localized pages. Set exact `lang`, keep self-referential and reciprocal `hreflang`, use valid language/region tags, and add `x-default` only for a real fallback. Do not auto-redirect crawlers/users solely from guessed language/IP without an accessible choice.
- For `zh-Hant`, distinguish Taiwan/Hong Kong content and terminology when material. Do not canonicalize distinct translations to a different language merely because the topic matches.

Use the current Google guidance for [multi-regional sites](https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites) and [localized versions](https://developers.google.com/search/docs/specialty/international/localized-versions), WHATWG HTML metadata/link semantics, and the product's actual routing/deployment contract.

## 3. Make essential meaning retrievable

- Return useful semantic HTML at a stable URL. Keep the subject, primary answer, product facts, terms, prices, authorship, dates and evidence in text—not only canvas, video, images, hover state or a post-interaction client store.
- Keep one coherent primary user purpose; related subtopics are allowed when they help that purpose. Use descriptive heading hierarchy, lists/tables/definitions where they fit, stable anchors, captions/transcripts and meaningful link text. This improves people and assistive/agent navigation; it is not “keyword density” or a requirement to split content into arbitrary chunks.
- State the direct answer near the question only when that is the best reading experience. Follow it with limits, method, examples, evidence and next action. Do not manufacture repetitive FAQs or rewrite every heading as a query.
- Identify who created/reviewed material, how/when it was produced or updated, first-hand evidence, sources and conflicts where readers would reasonably expect them. Do not invent credentials, reviews, citations, dates, locations, availability or brand claims.
- Preserve provenance for AI-assisted material and disclose material automation when users would reasonably ask how it was created. This is a product-trust and accountability rule, not a proven ranking factor. Scaled low-value paraphrase, doorway pages, hidden text and generated citation spam are release blockers.

People-first content and spam boundaries come from [Google Search Essentials](https://developers.google.com/search/docs/essentials), [helpful-content guidance](https://developers.google.com/search/docs/fundamentals/creating-helpful-content), and [spam policies](https://developers.google.com/search/docs/essentials/spam-policies). Apply the same honesty to other retrieval systems.

## 4. Use structured data as a truthful duplicate of visible facts

- Select only a current, platform-supported type that represents the page's primary visible content. Schema.org vocabulary is broader than any search engine's supported rich-result set.
- Prefer maintainable JSON-LD when the platform supports it. Supply required properties and only accurate recommended properties; connect entities with stable `@id` where useful.
- Visible HTML, canonical URL, locale, price/status/date/image and JSON-LD must agree. Never add fake reviews, FAQ, organization, author, offer, location or event data to gain a feature.
- Structured data may create eligibility for a currently supported search feature; it is not a rich-result or ranking guarantee. Validate syntax with Schema.org tooling and platform behavior with the current Google Rich Results Test/Search Console or corresponding provider tool after deployment.
- Keep image URLs crawlable and rights-cleared. Social Open Graph/Twitter metadata, favicons, web manifests and structured data are different surfaces with different consumers.

Follow the current [Google structured-data policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies) and the page-type-specific guide. A formerly supported rich-result type may become limited or removed; do not freeze an old search gallery in this skill.

## 5. Control crawl, index, snippets and model uses separately

- [`robots.txt` is RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html) crawl guidance, not authentication, authorization or a secrecy boundary. Sensitive content needs access control/removal.
- A crawler must fetch a page to see its `noindex`/snippet meta. Do not disallow the same URL in `robots.txt` and assume the bot can read a hidden `noindex`.
- Use HTML robots meta for pages and `X-Robots-Tag` for non-HTML or response-level policy. Record `index/noindex`, snippet/image preview policy and crawler-specific deviations explicitly.
- Search, training and user-directed retrieval can use different agents. Current examples include OpenAI `OAI-SearchBot` versus `GPTBot`, and Anthropic `Claude-SearchBot`, `ClaudeBot`, and `Claude-User`. OpenAI documents that user-triggered `ChatGPT-User` requests may not follow `robots.txt`; Anthropic documents robots controls for `Claude-User`. Verify each provider instead of transferring one crawler's behavior to another. Let the site owner choose each available policy; never silently allow training to improve search visibility or block user-directed retrieval by accident.
- WAF/CDN/challenges/geo/auth must match the chosen public policy. Do not weaken bot/security controls broadly; verify documented user agents/signatures/IP mechanisms and rate limits with each current provider.
- An XML sitemap lists canonical public URLs only, with truthful `lastmod`; it helps discovery/freshness but does not guarantee indexing. Use IndexNow only when the deployment/operator opts in and protects its key.

Provider controls change. Verify current [OpenAI bot guidance](https://developers.openai.com/api/docs/bots), [Anthropic crawler guidance](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler), [Google crawler list](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers), [Google robots controls](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag), [Search generative-AI control](https://support.google.com/webmasters/answer/16908024), and [Bing Webmaster Guidelines](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a) at implementation time.

## 6. Preserve renderability and page experience

- Return successful HTTP responses, deterministic metadata and useful content without requiring unsupported browser state, login, geolocation, consent dismissal or a long client-side waterfall.
- Allow required CSS/JS/images to be fetched under the chosen policy. Use progressive enhancement and test rendered HTML with provider inspection tools; “Google can render JavaScript” is not a promise that every render is scheduled or successful.
- Keep Core Web Vitals, accessibility, mobile task design, content stability and security within project gates. A fast empty shell or hidden keyword block is not search quality.
- Agent-readable interaction starts with the same native semantics, labels, names, states and predictable focus that assistive technology needs. ARIA cannot repair a visually misleading or unsafe transaction.

See [Google JavaScript SEO](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics), [Bing Webmaster Tools](https://www.bing.com/webmasters/), and [OpenAI agent accessibility guidance](https://help.openai.com/en/articles/12627856-publishers-and-developers-faq).

## 7. Measure without self-deception

Record by platform, URL, locale, query/task cohort, device and time:

- crawl/index/structured-data errors, canonical selection and sitemap freshness;
- impressions, clicks, referrals, engaged sessions, conversion quality, downstream returns/cancellations and server logs;
- generative visibility/citations as repeated samples across prompts/runs/time, not one screenshot or a model's self-report;
- content changes and confounders such as season, brand campaign, index update, model/version and competing sources.

Use Google Search Console, Bing Webmaster Tools and provider referral/reporting where available. Google and Bing AI-performance reports can be rolling, sampled or preview features; record their availability and definitions with every dataset. A passing validator proves syntax/eligibility only. It does not prove indexing, ranking, rich results, answer selection, citation, traffic, trust or conversion. Keep analytics consent/privacy and bot traffic classification separate from product-user metrics.

## 8. Release blockers

- public canonical/hreflang/status contradicts routing or visible locale;
- essential content/links exist only after an inaccessible client interaction;
- public page accidentally `noindex`, private/staging page accidentally indexable, or sensitive data treated as protected by robots alone;
- structured data is hidden, stale, fabricated, misleading or inconsistent with visible content;
- generated doorway/citation/mention spam, generic FAQ markup added only as an AEO trick, cloaking, keyword stuffing or fake freshness;
- claiming guaranteed rank, snippet, citation, rich result, AI answer inclusion or conversion;
- enabling a search/training/user crawler without the owner's explicit content-use policy;
- adding `llms.txt`, special AI markup, arbitrary content chunking or third-party GEO tactics as universal requirements without a documented consumer and test.
