# Anti-AI-slop contract

Use this contract during BUILD, broad RETROFIT, and any request for distinctive, premium, memorable, or award-level frontend work. It prevents interchangeable output without turning novelty into a quota.

## Boundary

`AI slop` means output whose form, content, interaction, or confidence is not earned by the product evidence. It includes interchangeable defaults, content-free decoration, fabricated proof, dead demo interactions, and self-certified quality.

Familiar patterns are allowed when they are the clearest task-appropriate pattern, follow the existing design system, or reduce accessibility and platform risk. Do not replace a correct table, native control, or conventional checkout merely to look unusual. Distinction is proportional to scope: a focused repair may preserve identity instead of inventing one.

Never use a mechanical quota such as “no gradients,” “exactly three asymmetries,” or “every page needs a signature effect.” Those rules create a different kind of sameness.

## Decision record

For every suspicious default or proposed signature, record one terse row:

```text
signal → product/task evidence → keep or replace → affected region/state → proof still required
```

Missing product evidence means remove or simplify the effect. Existing-system evidence may justify keeping a familiar pattern.

## Seven failure classes

### 1. Content and provenance

- vague headlines that could name any product;
- invented metrics, clients, testimonials, prices, people, awards, availability, or social proof;
- a local demo that claims an email, payment, upload, save, sync, or support ticket succeeded remotely;
- copy that explains the design, breakpoint, evaluator, or anti-slop strategy to customers;
- plausible-sounding facts that have no source or explicit placeholder label.

### 2. Information architecture and surface mismatch

- landing-page anatomy forced onto dashboards, settings, editors, checkout, support, or data tools;
- every route becoming `hero → feature cards → CTA`;
- a gallery, card grid, carousel, or bento used where comparison, scanning, sequence, or bulk action requires a table, list, timeline, tree, or form;
- decoration receiving more hierarchy than the primary task or current state.

### 3. Composition defaults

- every region having the same width, spacing, radius, shadow, and density;
- all information placed in floating rounded cards or pills;
- equal three-column grids regardless of content weight;
- the hero carrying the only visible identity while the rest collapses into a component-library demo;
- desktop compressed or stacked into mobile without changing priority, disclosure, navigation, density, or input behavior.

### 4. Visual defaults

- unearned purple/blue glow, gradient text, glass panels, blobs, noise, faux chrome, or generic black-and-gold “luxury” styling;
- mixed icon families, emoji used as product icons, arbitrary radii, and shadows with conflicting light directions;
- decorative uppercase microcopy applied mechanically to CJK;
- too many simultaneous type, color, material, border, texture, and lighting effects;
- imagery or empty gradient boxes presented as factual product evidence.

### 5. Motion defaults

- every element fading upward on scroll;
- smooth-scroll hijacking, custom cursors, marquee, parallax, tilt, preloader, shader, or globe without a named product job;
- motion without trigger, interruption, cleanup, reduced-motion result, touch equivalent, or static fallback;
- continuous work with no visibility pause or bounded resource cost.

### 6. Interaction and state defaults

- dead filters, controls that only change their own styling, unreachable errors, or retry that repeats the same state;
- success that remains after later invalid input, or contradictory visible and announced state;
- overlays without background isolation, scroll lock, focus containment, Escape, and reliable focus return;
- storing only a DOM node for focus return when re-render can replace it; store a stable trigger identity and resolve the live element on close;
- mobile interactions that still depend on hover, precision pointing, wide comparison, or desktop side panels.

### 7. Verification and code-generation defaults

- “verified,” “accessible,” “responsive,” “zero errors,” or a score without matching evaluator evidence;
- source keywords or a screenshot used as proof of behavior they cannot establish;
- giant generated components, duplicated markup, unexplained dependencies, or a specialized runtime for a trivial effect;
- the implementation model editing its gate, grading itself, or converting missing evidence into a pass.

## Deterministic gates

Run these in order. A failure blocks polish until it is repaired.

1. **Truth gate** — Mark each material fact `official`, `observed`, `inferred`, `placeholder`, or `unknown`. Remove fabricated proof and describe client-only outcomes honestly.
2. **Task-surface gate** — Name the primary noun and verb. Confirm that the chosen surface supports them; a product dashboard must not inherit landing-page anatomy by default.
3. **Product-swap gate** — Mentally swap the product name, logo, and accent color. If the concept and most copy still fit an unrelated product, derive the design again from product evidence.
4. **Representation gate** — For every card/grid/carousel, name why it is better than list, table, form, timeline, tree, or open composition for this content and task.
5. **Silhouette gate** — Inspect grayscale and region silhouette. The reading order, task hierarchy, and density shifts must survive without accent color or decorative effects.
6. **Earned-region gate** — Trace each distinctive region to a product noun, verb, material, dataset, cultural context, or verified brand invariant. Remove signatures with no trace.
7. **Mobile-transformation gate** — Record what mobile reorders, replaces, defers, condenses, or moves into thumb reach. “Stack” alone is not a transformation.
8. **State-roundtrip gate** — Exercise A→B→A, valid→success→invalid, an actually reachable failure, and a retry that changes or recovers state. Label simulated/local-only results.
9. **Effect and dependency gate** — Give every effect and dependency one job, lifecycle, fallback, and cost boundary. Prefer the smallest runtime that does the job.
10. **Evidence-ceiling gate** — A claim cannot exceed the strongest independent evidence. Static inspection cannot prove rendered, browser, touch, assistive-technology, or formal-conformance behavior.

## Weak-model repair order

Do not ask a weak model to “make it less generic” in one subjective step. Repair in this fixed order:

1. semantics, truth, and provenance;
2. task-surface match and information architecture;
3. composition hierarchy and representation choice;
4. brand fidelity, typography, material, and authored distinction;
5. real mobile transformation;
6. motion and progressive enhancement;
7. independent browser evidence and honest handoff.

After each step, re-run only its named gate. Preserve raw output for before/after comparison. A remake produced with a changed skill revision is remediation evidence, not a controlled same-context model ranking.

## Review result

Report concrete findings, not a universal taste score:

```text
class → affected route/state → product evidence → user impact → smallest repair → proof status
```

Independent human or rendered review remains necessary for subjective craft. Passing this contract means the output avoided known convergence and truth failures; it does not prove originality, brand fidelity, usability, accessibility, award quality, or production readiness.
