# Brand system fidelity

Use this reference when extracting a brand from existing products/assets, extending a design system, applying a campaign, or keeping several product surfaces recognizable. Brand fidelity is evidence management, not a mood-board guess.

## 1. Classify every source

Record each observation before deriving rules:

```text
source URI/file → owner/version/date/rights → scope → evidence status → rule → confidence → affected surfaces
```

Evidence status:

- **explicit**: an approved brand guideline, token source, owned asset, product terminology list, or documented component rule;
- **observed**: repeated in a current first-party product but not documented as invariant;
- **inferred**: a reversible hypothesis derived from several observations;
- **unknown**: missing, conflicting, obsolete, locale-specific, A/B, campaign, or otherwise not safe to infer.

Keep `unknown` visible. One page, screenshot, campaign, competitor, old route, or locale variant cannot prove a complete brand personality or system. Never invent logo rules, trademark rights, voice, audience beliefs, or a universal palette from absent evidence.

Suggested record:

```yaml
source:
  uri: string
  type: official_guideline | design_system | owned_asset | current_product | campaign | research | inference
  owner: string
  version: string
  observed_at: date
  rights: string
scope: master_brand | product_system | campaign | component | locale
status: explicit | observed | inferred | unknown
confidence: high | medium | low
rule:
  category: logo | color | typography | layout | icon | image | motion | voice | interaction
  invariant: boolean
  value: any
  allowed_variants: []
  prohibited_uses: []
```

## 2. Extract behavior, not only appearance

Audit:

- logo/wordmark variants, clear space, minimum size, co-branding, legal and asset rights;
- semantic color roles, contrast pairs, data/status behavior, light/dark/high-contrast constraints;
- type roles, exact font files/licenses, regional glyphs, numeric behavior and fallback;
- layout rhythm, density, grids, alignment, shape, surface/depth and exception logic;
- icon/illustration/photo art direction, crop, subject, treatment, caption and provenance;
- motion purpose, tempo, spatial continuity, reduced result and prohibited effects;
- product vocabulary, sentence structure, stable voice, contextual tone, error/safety language;
- interaction conventions, component states, focus/error behavior, destructive-action and trust boundaries.
- approved audience/market definitions, task and context research, support language and product analytics; do not turn demographics into taste, ability, income, or culture stereotypes.

Distinguish a reusable rule from a coincidence by checking multiple current first-party surfaces, states, locales and viewports. Preserve recognizable product behavior even when visual polish changes.

## 3. Separate system invariants from campaign overlays

| System invariants | Conditional campaign overlay |
| --- | --- |
| logo/wordmark, clear space, rights | approved campaign key visual |
| semantic color and status roles | bounded accent subset |
| core/UI typography and fallback | display headline treatment |
| components, states, focus, error | campaign photo/illustration/material |
| accessibility, interaction and safety | short-term motion and narrative pacing |
| stable voice and product terminology | channel/journey-specific tone and copy |

Every overlay records owner, approved source, start/end, applicable surfaces/locales, fallback, and forbidden overrides. A campaign may intensify expression; it must not silently replace accessibility, transaction semantics, product controls, master-brand assets, or long-lived system tokens.

Use official systems such as [W3C Design System](https://design-system.w3.org/), [GOV.UK Brand Guidelines](https://brand.design-system.service.gov.uk/), [USWDS](https://designsystem.digital.gov/), [IBM Design Language](https://www.ibm.com/design/language/), [Microsoft brand voice](https://learn.microsoft.com/en-us/style-guide/brand-voice-above-all-simple-human), and [Atlassian voice and tone](https://atlassian.design/foundations/content/voice-tone/) as examples of separation and governance—not as visual templates for unrelated products. The [Design Tokens Format 2025.10](https://www.w3.org/community/reports/design-tokens/CG-FINAL-format-20251028/) is a Community Group report, not a W3C Recommendation.

## 4. Treat personality and industry conventions as hypotheses

Brand-personality scales describe audience attribution under a study context; they are not a formula that maps “sincere” to a font, color or radius. Culture, language, category and familiarity change results. Useful critical sources include [Aaker 1997](https://doi.org/10.1177/002224379703400304), [Azoulay and Kapferer 2003](https://doi.org/10.1057/palgrave.bm.2540162), [Austin et al. 2003](https://doi.org/10.1080/0965254032000104469), and [Aaker et al. 2001](https://doi.org/10.1037/0022-3514.81.3.492).

- “Finance = blue and conservative”, “children = rounded and colorful”, and “luxury = black/gold serif” are priors to challenge, never generators.
- The [NN/g tone dimensions](https://www.nngroup.com/articles/tone-of-voice-dimensions/) can structure a workshop, but its small US study is not a universal cross-cultural scale.
- Preserve an existing authored distinction when evidence supports it. Create a new distinction only for a greenfield/broad redesign and record why it belongs to the product.

## 5. Produce a brand contract

Minimum handoff:

```text
explicit invariants + observed patterns + unresolved conflicts + unknowns
+ system tokens/components + campaign overlay boundary + locale behavior
+ assets/fonts with rights + preserve/change table + validation views
```

Make tone executable without pretending it is universal:

```text
voice axes: direct↔ceremonial, concise↔narrative, restrained↔expressive, expert↔guided
visual axes: dense↔spacious, geometric↔organic, quiet↔kinetic, documentary↔constructed
motion axes: immediate↔paced, mechanical↔elastic, planar↔spatial
context shifts: marketing / product / onboarding / error / safety / support / locale
prohibited claims, words, motifs, treatments and interactions
```

Axes describe an approved or proposed range; they do not prescribe a font, hue, radius, or animation without product evidence.

For retrofit work, list `preserve`, `improve`, `replace with approval`, and `unknown`. For greenfield work, label the proposed system as a design direction—not discovered brand truth. Verify recognizability and task success with representative users/owners where material; the implementing model cannot self-certify brand fidelity.
