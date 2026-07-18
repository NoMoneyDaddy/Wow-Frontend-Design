# Creative direction

Use this reference to turn content and product strategy into an authored visual system.

## Contents

1. Extract meaning
2. Adapt to audience, task, and preference
3. Generate directions
4. Define the visual grammar
5. Compose with hierarchy
6. Create or preserve authored distinction
7. Avoid convergence

## 1. Extract meaning

Answer from evidence before choosing a style:

- Who is this for, and what must they accomplish?
- What should the experience feel like: trusted, urgent, intimate, rigorous, playful, ceremonial, rebellious, calm?
- What content is uniquely valuable: product detail, data, people, place, process, collection, chronology, comparison?
- What must be remembered ten minutes later?
- What existing brand equity must remain recognizable?

For existing brands, classify every source and rule as `explicit`, `observed`, `inferred`, or `unknown`. A screenshot, campaign, legacy route, competitor, or locale variant is not proof of a system invariant. Use [brand-system-fidelity.md](brand-system-fidelity.md) for the extraction and campaign boundary.

Compress the answer into a concept sentence:

> `[Product truth] expressed through [visual/interaction behavior], so [audience outcome].`

Good: “A conservation archive reveals repaired layers instead of hiding them, so visitors feel the care behind every artifact.”

Weak: “A modern, clean site with bold colors and smooth animations.”

## 2. Adapt to audience, task, and preference

Map evidence to design behavior before choosing a style:

| Context signal | Likely design response |
| --- | --- |
| High-stakes, infrequent task | Explicit steps, visible status, restrained motion, recovery and trust evidence |
| Expert, repeated workflow | Higher information density, keyboard paths, stable placement, shortcuts and customization |
| New or low-literacy audience | Familiar patterns, plain language, progressive disclosure, strong feedback |
| Exploratory story or cultural content | Editorial pacing, rich media, spatial discovery with clear orientation |
| Transaction or comparison | Comparable attributes, price/terms clarity, persistent decision context, error prevention |
| Operational data | Precise hierarchy, compact numerics, state color rules, fast scan and filtering |
| Community or user content | Identity, provenance, safety/moderation states, resilient unknown content lengths |
| Mobile/interrupted context | Shorter decision path, thumb reach, resumable state, lower rendering cost |

Use this as a reasoning aid, not a stereotype table. Do not infer visual taste, ability, income, gender, age, or culture from demographics. Prefer user research, supplied references, product evidence, analytics, or explicit assumptions that can be corrected.

Translate preferences into attributes:

- “I like this site” → identify its density, type contrast, pacing, geometry, imagery, and motion—not its exact composition.
- “Make it premium” → ask or infer which kind: quiet precision, material craft, editorial authority, exclusivity, or high-touch service.
- “Make it young” → reject the stereotype; identify energy, participation, speed, humor, or subculture evidence instead.
- Conflicting preferences → preserve the underlying intent while protecting readability, task success, accessibility, performance, and brand consistency.

Create a trace before implementation. Treat behavioral/design research as a hypothesis with a transfer assumption; use [behavioral-design-evidence.md](behavioral-design-evidence.md) when a claim invokes psychology, persuasion, attention or conversion:

```text
Evidence / stated preference → design decision → affected component → validation method
```

If a major decision cannot be traced to product meaning, audience need, user preference, or a verified constraint, simplify or remove it.

## 3. Generate directions

For an empty build or broad redesign without an approved direction, generate only enough alternatives to resolve a named choice—normally two, sometimes three—and make them differ in more than palette. For focused repair or polish, derive one direction from the existing system instead of expanding scope. An audit reports the existing direction and risks; it does not invent alternatives unless comparison was explicitly requested. When alternatives are in scope, first freeze the known brand, language, core-content, workflow, accessibility, safety, and technical invariants. Give each alternative a different product hypothesis for the named choice, then change the smallest coherent axis set that makes the hypothesis observable. At least one changed axis must materially alter hierarchy, content representation, or task behavior; add dependent axes only when evidence makes them necessary. Record changed axis → product basis → expected task/layout consequence → validation method. Palette-only restyling, effect-only novelty, unrelated axis churn, and a preselected style-label bundle do not count. The following axes are prompts for product-derived reasoning, never a catalogue, required vocabulary, or bundle to copy:

- composition: axial, editorial, modular, radial, spatial, dense, sparse;
- typography: expressive serif, grotesk, humanist, mono, variable, CJK-led;
- geometry: sharp, cut, soft, stamped, ruled, irregular, continuous;
- material: paper, glass, ink, fabric, light, metal, cartographic, screen-native;
- imagery: documentary, macro, diagrammatic, generative, typographic, data-led;
- motion: inertial, stepped, elastic, mechanical, cinematic, scroll-linked, state-driven;
- interaction: browse, compare, construct, reveal, tune, trace, collect, navigate.

Reject a direction that violates a frozen invariant or fails an essential task, accessibility, safety, or feasibility boundary; a distinctiveness score cannot offset a blocker. Score each remaining direction 1–5:

| Criterion | Question |
| --- | --- |
| Product fit | Does it clarify the product and top task? |
| Distinctiveness | Would the layout still be recognizable in grayscale? |
| Usability | Is the reading and action path obvious? |
| Accessibility | Can it survive contrast, zoom, keyboard, and reduced motion? |
| Feasibility | Can it be built and verified within scope? |

Choose the highest evidence-backed direction. Combine directions only when their rules are compatible.

If the brief explicitly asks for award quality or an immersive brand/portfolio experience, use [award-quality-lens.md](award-quality-lens.md) only after choosing a product-fit direction. Do not start from an award-gallery trope and reverse-engineer a product around it.

## 4. Define the visual grammar

### Color

Give color a job. Define roles such as canvas, surface, ink, muted ink, action, status, selection, data series, and focus. Add one sentence that controls chroma, for example:

- “Vermilion appears only when the user can act.”
- “Color encodes time; older records lose saturation.”
- “Product materials carry color; interface chrome remains neutral.”

Check contrast on actual layered and moving backgrounds, not token pairs alone. Use color plus text, shape, or position for status.

Use [color-system-psychology.md](color-system-psychology.md) for the semantic appearance matrix, rendered contrast, and evidence boundary for color-emotion or conversion claims. A named mood is a creative direction; it is not proof that a hue causes that emotion or behavior.

### Typography

Assign roles before font families:

- display voice: identity and emotional register;
- reading voice: body clarity across target scripts;
- functional voice: controls, data, labels, and compact UI;
- numeric behavior: tabular, proportional, slashed zero, units.

One family may fill all roles if its range is strong. Verify the exact weights and glyph coverage. Do not simulate unavailable bold or italic. Avoid tiny uppercase Latin labels as a universal hierarchy device, especially in CJK interfaces.

### Shape and depth

Choose one geometry family and a small number of exceptions. Radius is not decoration; relate it to product character and component scale. Prefer borders, tonal separation, overlap, or whitespace before defaulting to large shadows.

For a system spanning borders, type, component states, light, material, effects, and motion, freeze the craft rules in [visual-material-system.md](visual-material-system.md) before styling individual components.

### Texture and imagery

Choose imagery that carries evidence or atmosphere. Set crop, aspect ratio, color treatment, caption, and loading behavior. Decorative texture must remain subtle at different pixel densities and never reduce text contrast.

### Motion

Define:

- entry behavior;
- state-change behavior;
- navigation behavior;
- signature behavior;
- reduced-motion equivalent.

Reuse a small duration and easing vocabulary. Motion should explain causality, preserve orientation, or create emphasis. It must not hold content hostage.

## 5. Compose with hierarchy

Before component markup, record one composition proof for each representative route/state in working notes or the `Layout` section of `DESIGN.md`, never in product copy:

```text
frame/state → F1 dominant anchor → F2 counterweight/support
→ reading/action path → dense/quiet transition → anchored grid break, if earned
→ representative/sparse/dense content pressure → track/representation response
→ mobile equivalent → explicit failure signal
```

- Derive `F1` from the top task or most valuable content. Use scale, position, contrast, density, and whitespace so an independent reviewer can find it without accent color. `F2` must support, compare with, or deliberately counterweight `F1`; it is not a second arbitrary hero.
- Give every major region a place in the reading/action path. Focused flows may have one primary next action; dashboards, documentation, and multi-workspace products may preserve several grouped actions. Do not invent one global CTA.
- Name one real density or pacing transition. Repeated units must remain comparable; unique content should use sequence instead of a fake equal grid. Important content may escape a generic container when safe.
- Pressure-test each task-bearing major region with representative, sparse, and dense reachable content. Recompose its track or representation when sparse content becomes stranded in an oversized surface or dense content obscures the reading/action path; while preserving required content and equivalent access, reduce, combine, summarize, disclose, or show an earned overview instead of adding filler or decoration. Quiet space remains valid when it deliberately shapes reading around an anchored task region and does not detach required context or action; geometry alone is not a failure.
- Break alignment only from a visible anchor. A task-appropriate single column is valid; asymmetry, F/Z patterns, and a fixed number of regions are never quotas.

After the first runnable slice and before color/effect polish, compare matched desktop and mobile frames with the same content. Blur, inspect in grayscale, and disable optional effects. Recompose the representation, order, track sizes, or grouping when `F1`/`F2` order disappears, major regions become equal in width/density/silhouette without a task reason, a grid break has no anchor, the page has no density shift, or mobile loses the reading/action path. Do not attempt to repair a failed composition proof by changing palette, adding shadows, increasing radius, or adding motion.

## 6. Create or preserve authored distinction

For empty builds and broad redesigns, decide whether identity is best carried by the information model, workflow, composition, content cadence, material, illustration, or an authored behavior. Create a new signature only when product evidence gives it a user/task job; `none` is valid when added salience would reduce scanning, trust, safety, accessibility, or performance. For focused repair, audit, or polish, name the existing identity to preserve and add no new effect unless it directly solves the scoped problem.

When an authored behavior is earned, derive it from the product noun or verb:

| Product truth | Possible authored behavior |
| --- | --- |
| layers / history | peel, restore, compare, trace |
| precision / instruments | tune, calibrate, measure, align |
| collection / archive | index, reveal provenance, spatial browse |
| collaboration / voices | converge, harmonize, annotate, hand off |
| growth / ecosystem | branch, cluster, react, propagate |
| movement / journey | route, orbit, progress, change perspective |

When a signature is in scope, define its static state first. Then add interaction. Ensure a user can understand the meaning without discovering the effect.

## 7. Avoid convergence

Apply the evidence boundary and deterministic gates in [anti-ai-slop.md](anti-ai-slop.md). “Avoid convergence” does not mean forcing novelty: familiar patterns stay when task, platform, accessibility, or existing-brand evidence earns them.

Before finalizing, compare the design against common defaults:

- Could the logo and copy be swapped with another startup unchanged?
- Is the identity only a font plus accent color?
- Is the hero the only distinctive section?
- Do all cards, buttons, and images share one arbitrary radius?
- Does motion repeat the same fade-up everywhere?
- Is mobile simply desktop in one column?
- Did convenience choose the layout instead of content?

Treat each “yes” as a hypothesis, not a quota. Revise when the repeated defaults make the product interchangeable or weaken its task; keep a familiar pattern when product evidence, convention, or accessibility justifies it.
