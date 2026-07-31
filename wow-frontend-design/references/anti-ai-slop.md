# Product-specific post-render review

Use this reference only after a runnable interface has been rendered. It reviews whether the visible result is supported by product evidence; it does not choose a direction, prescribe a style, replace task-specific quality gates, or award originality.

## Boundary

An anti-slop finding is a visible claim, region, or overall concept whose product relevance cannot be explained from available evidence. Interchangeability is a review signal, not a defect by itself.

Familiar patterns are allowed when they clearly support the task, preserve an existing system, or reduce accessibility, platform, learning, or implementation risk. Conventional structure may be the correct product-specific choice. Do not demand novelty, ban a technique, count stylistic devices, or require a signature effect.

Judge only the rendered product surface and the evidence available for that surface. Route component, interaction, responsive, motion, accessibility, security, and implementation defects to their owning references and gates.

Reconcile every explicit negative constraint before the product-swap check. Match the visible result and implementation values to the forbidden pattern and the chosen alternative recorded before coding. A qualified, softened, renamed, or rationalized instance of the same pattern is still a contradiction unless the brief explicitly permits that exception. Confirm the contradiction from the fresh render and repair the smallest owning system decision; do not rewrite `DESIGN.md` to excuse the result.

## Review

Apply these checks to representative rendered routes and states:

1. **Truth** — Identify material visible facts, proof, assets, and claimed outcomes. Confirm that each is official, observed, explicitly supplied, clearly labelled as a placeholder, or honestly described as local/simulated. Unsupported plausibility is a finding.
2. **Product swap** — Mentally replace the product name, logo, and accent color. If the concept, hierarchy, and material copy still imply the same unrelated product, record a candidate. Confirm it only when product evidence supports a more specific alternative; a familiar task-appropriate pattern is not a failure.
3. **Earned region** — For each identity-bearing or attention-dominant region, identify the product noun, verb, content relationship, dataset, authorized asset, cultural context, or verified brand invariant it expresses. A region with no product job is a finding when it competes with or distorts the task; quiet or conventional regions need no novelty justification.
4. **Evidence ceiling** — Limit every review claim to the strongest available evidence. Source inspection cannot establish a rendered result, a screenshot cannot prove interaction, and this review cannot prove usability, accessibility conformance, brand fidelity, originality, award quality, or production readiness.

## Recognizable generated-UI defaults

The supplied four-panel meme is a pattern collage, not one broken layout. Treat these as convergence signals to inspect in the rendered product, not automatic bans:

- **Side-tab accent card** — a thick bright stripe attached to the edge of an otherwise generic rounded card.
- **Letter-spacing theatre** — extreme tracking, usually on uppercase labels or display copy, used as a substitute for a typographic idea.
- **Pill/status reflex** — a glowing dot, “Live”, eyebrow, or capsule badge added because the surface feels empty, without a real state owner or transition.
- **Card shell repetition** — empty rounded panels, nested cards, or the same hero → metrics → features arrangement repeated regardless of the product’s information model.

Cross-check adjacent tells from the same family: one font used everywhere, oversized icon tiles, decorative gradients/glows, repeated tiny uppercase kickers, low-contrast gray text, redundant labels, and motion without a task or state purpose. The current [Impeccable slop catalogue](https://impeccable.style/slop/) describes these as recurring generated-UI patterns and separates deterministic source/browser checks from broader review judgments.

Do not “fix” a confirmed candidate by swapping in a different trendy pattern or by banning a valid component. Require a product noun, verb, dataset, state transition, or content relationship for the region; then compare the fresh render against the declared alternative. A pill, card, stripe, tracking choice, or familiar font is acceptable when that job and evidence are explicit.

## Structural slop tells

The supplied screenshot is a useful warning that AI slop is often a broken composition, not merely a fashionable palette. Review these tells from a fresh render, then route the confirmed defect to its owning layout, typography, component, or content rule:

1. **Text/container disagreement** — a heading, label, or value is clipped, crosses a card seam, disappears under a sibling, or is forced into extreme tracking to fit. Measure the text box against its owning container at every declared viewport and at the project’s text-spacing stress settings. Do not accept `overflow: hidden`, `nowrap`, or `text-overflow` as a repair unless truncation is an explicit product behavior with an accessible full-value path; CSS overflow can otherwise hide content, and WCAG reflow requires no loss of information or functionality at narrow widths. See [MDN text-overflow](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/text-overflow), [WCAG 1.4.10 Reflow](https://www.w3.org/WAI/WCAG21/Understanding/reflow.html), and [WCAG 1.4.12 Text Spacing](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing).
2. **Decorative grid without a content model** — equal cards, seams, giant empty panels, or a split frame are present without a distinct task, proof, dataset, or narrative beat for each region. Replace the shell only when the product evidence supports a clearer grouping; do not fill empty space with more cards or labels.
3. **State reduced to ornament** — a glow, dot, pill, or animated badge implies “live”, “ready”, or “selected” without a semantic owner, readable label, update behavior, and non-motion fallback. Route the defect to component and interaction review; decoration may reinforce a state but cannot be its only evidence.
4. **Viewport treated as a crop mask** — the desktop composition is simply enlarged, clipped, or overlaid on mobile instead of re-composed around the mobile task. Verify route, content order, focus order, and geometry at the narrowest declared profile; a screenshot that looks dramatic because it hides content is a failure, not an art direction.
5. **Surface vocabulary outruns product vocabulary** — repeated rounded containers, gradients, noise, badges, or uppercase microcopy occupy more visual area than the nouns, verbs, evidence, and next actions that explain the product. Remove the lowest-value surface and re-measure hierarchy before adding a new effect.

These are diagnostic hypotheses, not a reverse style catalogue. A deliberate overlap, dashboard grid, badge, or truncation remains valid when its product job, responsive behavior, semantic owner, and fresh evidence are explicit.

## Review result

Report only confirmed findings and unresolved candidates:

```text
finding or candidate → route/state/viewport → product evidence or gap → user impact → smallest owning repair → proof status
```

Keep the result concise. Do not produce a taste score or a generation decision record. A clean result means only that this bounded post-render review found no evidenced truth or product-specificity failure.
