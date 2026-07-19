# Creative direction

Use this reference to turn product evidence into one specific, implementable direction. It owns the concept and minimum authored identity, not the technical recipes for typography, color, material, components, or motion.

## Contents

1. Freeze product evidence
2. Form the direction
3. Compare only when a decision is unresolved
4. Create, preserve, improve, or omit authored identity
5. Prove the direction in a runnable slice

## 1. Freeze product evidence

Answer from available evidence before naming a direction:

- Who is trying to accomplish what, in which context, with what consequence if the task fails?
- Which content, data relationship, artifact, process, place, or product behavior is uniquely valuable?
- What should remain understood or remembered after the task?
- Which existing brand, workflow, language, and product expectations must remain recognizable?
- Which preferences or rejections did the user state, and which choices remain genuinely open?
- Which accessibility, safety, performance, rights, device, and implementation constraints bound the result?

For an existing product, classify each source or claimed invariant as `explicit`, `observed`, `inherited`, `inferred`, or `unknown`. A screenshot, campaign, legacy route, competitor, or locale variant is evidence of that instance, not proof of a universal system rule. Use [brand-system-fidelity.md](brand-system-fidelity.md) when extracting an existing brand or separating a campaign from the durable system.

Do not infer visual taste, ability, income, gender, age, or culture from demographics. Prefer supplied research, first-party content, approved assets, product behavior, analytics with known scope, and explicit assumptions that the user can correct.

Translate a preference into its underlying intent and expected product consequence instead of copying the referenced implementation. Preserve the intent only while it remains compatible with task success, readability, accessibility, performance, safety, and established brand evidence.

Keep one compact trace:

```text
source and status → observation → direction decision → affected route/state → proof required
```

Treat design or behavioral research as a hypothesis with a transfer assumption. Use [behavioral-design-evidence.md](behavioral-design-evidence.md) when a claim invokes psychology, persuasion, attention, or conversion. If a material decision has no trace to product meaning, audience need, stated preference, preserved identity, or verified constraint, simplify it or leave it unresolved.

## 2. Form the direction

Compress the evidence into one working concept:

```text
product truth → perceptible behavior → user outcome
```

The product truth must name something supported by the evidence. The perceptible behavior describes what the experience makes clear or possible; it is not a style label, effect, palette, font category, layout archetype, or motion preset. The outcome must relate to the user's task or understanding rather than a claim that the interface feels polished.

Use the task representation and content order established by the core workflow or [component-composition.md](component-composition.md). Creative direction may strengthen their meaning, emphasis, and identity, but must not replace a correct task surface merely to appear unusual.

Name why the direction belongs to this product. Test the identity-bearing decision by removing the product name, logo, and accent color: if the same rationale remains equally defensible for an unrelated product, return to the evidence instead of adding novelty. Familiar patterns remain valid when the task, platform, accessibility, or existing system earns them.

Before implementation, name the evidence and task job for the attention-dominant display-type category, major-surface shape, and repeated control silhouette. A subject noun, mood, or claim of polish is not evidence for any of them. If a choice has no job, inherit a proven project rule or leave it unresolved; do not replace it with a preferred style. This is a traceability record, not a requirement to make these choices unusual or different.

Record an evidence-backed rejection only when the brief, existing product, or a material unresolved choice provides one. Do not invent a disliked trope or visual opposite merely to complete the record.

## 3. Compare only when a decision is unresolved

An empty build or broad redesign may compare two, occasionally three, directions only when a named material choice remains unresolved. Focused repair and polish inherit the existing direction unless evidence shows that direction is the root cause. An audit describes the current direction and risks; it does not invent alternatives unless comparison was requested.

Before comparison, freeze the product truth, top task, required content and states, brand and language invariants, accessibility and safety needs, preserved contracts, and implementation boundary. Each candidate must express a different product hypothesis for the unresolved choice and state:

```text
hypothesis → product evidence → observable task/content consequence → implementation impact → proof
```

Candidates do not differ merely because their colors, effects, or labels differ. Reject any candidate that violates a frozen invariant or essential task, access, safety, rights, performance, or feasibility boundary. Choose the candidate best supported by the declared outcome and evidence; do not convert subjective judgment into a numeric quality score. Combine candidates only when their rules and consequences remain coherent.

If the brief explicitly requests award-quality, immersive, campaign, or jury-oriented review, apply [award-quality-lens.md](award-quality-lens.md) only after selecting a product-fit direction. That lens cannot supply the product truth or override a blocker.

## 4. Create, preserve, improve, or omit authored identity

Record the identity decision as `create`, `preserve`, `improve`, or `none`, with its evidence and task job. Name the primary place where identity is carried without selecting from a style menu. Supporting decisions should reinforce that source rather than compete to become separate signatures.

- For an empty build or broad redesign, create only the minimum distinction the evidence earns.
- For retrofit, preserve established identity and improve only the part that blocks the requested outcome.
- For focused repair, audit, or polish, preserve by default and introduce no unrelated signature.
- Use `none` when extra salience would compete with scanning, trust, safety, accessibility, performance, or the existing system.

An authored behavior is optional. Admit one only when a product noun, verb, state, or relationship gives it a user or task job. Define the complete static state first, keep the meaning understandable without discovering the behavior, and route implementation, interruption, fallback, and reduced-motion details to the applicable technical reference.

## 5. Prove the direction in a runnable slice

Before implementation, keep a terse direction record:

```text
concept → evidence locators → preserved invariants → identity decision
→ attention-dominant grammar jobs or unresolved choices
→ affected route/state → expected task/content consequence → failure signal
```

The first representative slice must make the concept observable through real or clearly labelled content, the actual task representation, and the minimum system roles needed to render it. It must also preserve a useful static result and the mobile task transformation required by the core workflow. Do not delay a runnable slice to complete a direction deck or fill unused design-system categories.

After rendering, review the direction rather than a checklist of fashionable traits:

- Can a reviewer trace the identity-bearing decision to the recorded product evidence?
- Does it improve the intended task, content understanding, or preserved recognition?
- Does the rationale still depend on this product when name, logo, and accent color are removed?
- Does the direction remain understandable when optional effects are absent?
- Did implementation preserve the frozen contracts and avoid inventing unsupported product truth?

If the slice does not support the concept, revise the unsupported decision or return to the evidence. Do not repair a weak direction by adding decoration. Apply [anti-ai-slop.md](anti-ai-slop.md) only as the post-render product-specific review defined by the core workflow.
