# v7 A4 development pilot report

## Decision

Do not promote A4 as a global quality win. Keep the task-completeness and logical-axis guidance as defensive reference rules, but treat their effect on one-shot generation as **UNVERIFIED** until a later cohort removes the civic desktop regression and demonstrates instruction adherence.

This is a development-pilot conclusion, not sealed benchmark evidence.

## Frozen identity and evidence

- Cohort: `v7-a1-task-safe-vertical-flow`
- Baseline: `78157b64a7ef67ba8944c7430092474297ce7516`
- Candidate: `v7-a4`; only `wow-frontend-design/references/typographic-layout.md` changed in the generated package.
- Model: exact `gpt-5.4-mini`; silent fallback disabled.
- Frozen evaluator commit used to revalidate evidence: `4706e57`.
- Manifest SHA-256: `e0cc5832e1d18b897541efba8f55b63b1d6df346f2838afdb22fafa4eb58f6d0`.
- Fast-gate ledger SHA-256: `ee88fb1ef9c6743eda4f2cd13fc8cf34f6180b61b07ec77f22d1560b873b78e0`.
- Evidence validation: `16 screenshots, 16 finding runs`; desktop/mobile, base/interaction, Chromium.
- All four official generated targets completed with zero-error/zero-warning `DESIGN.md` gates. One earlier candidate-nature invocation exhausted two lint retries and remains quarantined outside the repository; it was not substituted into the official matrix.

The evaluator-owned artifacts remain outside the repository under `.wow-v7-a4-pilot`. Their four successful run-manifest SHA-256 values are:

- accepted civic: `75ab9b2d79019daaffab9c4cc1c4b4f56104a51a229007a3901e1cacd00440f5`
- candidate civic: `45fa77ac24108906088dd5d29a7fd6fdc3653272cc5ada30457bc3b5c9c5fef4`
- accepted nature: `34c6f4f20272769ca690747291d00990a403bac891bdaaf2097bdf2a22a04d41`
- candidate nature: `52e046531149c1d086e10737ae4f191e1ad06f1e14d9f7849b8a2abb9a515d14`

## Automated comparison

Both variants had zero runtime issues. Typography/layout findings increased from `12` for accepted to `18` for candidate.

- Candidate improved nature heading-orphan frequency in the desktop/mobile sample.
- Candidate introduced `a1_layout_column_void` on both civic and nature desktop states.
- Candidate civic desktop placed a short summary beside a much taller comparison region, leaving a large shared-row void and narrowing three dense comparison cards.
- Candidate nature still used `min-height` and `align-self: center` for vertical content and omitted `max-inline-size`; the generated implementation did not follow the new canonical recipe.

## Paired blind review

Two independent reviewers saw anonymized A/B images with label order reversed between pairs. After unblinding, both reviewers agreed on all four representative pairs:

| Pair | Preferred variant | Main reason |
| --- | --- | --- |
| civic desktop base | accepted | wider title/columns and no short-summary sidebar void |
| civic mobile interaction | candidate | clearer card spacing, state, actions, and summary |
| nature desktop base | candidate, medium confidence | better horizontal reading composition, but vertical-column void remained severe |
| nature mobile interaction | candidate | complete horizontal fallback and clearer saved-state feedback |

The candidate won three representative pairs but failed the no-regression ratchet because the civic desktop regression was high-confidence and the automated finding count increased. A small development sample cannot justify averaging away that regression.

## New issue and retained improvement

The pilot exposed a closed-loop observability defect: exhausted generation retries previously discarded actionable `@google/design.md` findings and the hash of the linted input. The runner now writes an exclusive, evaluator-owned failure receipt with bounded error/warning messages, per-attempt `DESIGN.md` hashes, brief/package/model/CLI/cohort bindings, and pinned-linter provenance. It does not embed generated HTML, raw logs, the brief body, or the full linter payload.

The reference change remains useful as a defensive contract because it is technically correct and independently reviewed:

- composition repair must not delete comparison evidence, state, validation feedback, primary actions, or result summaries;
- vertical writing uses the logical inline axis for physical height and must not use peer height or grid stretch to fake balance;
- mobile keeps an equivalent horizontal presentation.

These rules are safeguards, not evidence that every weak-model first pass follows them.

## Claim boundary and next experiment

A later cohort should test an executable repair loop, not another prose-only variation: run the rendered checker, feed only its bounded findings and evidence locators into a minimal repair pass, then recapture the failing state. Promotion requires zero new runtime failures, no accepted-to-candidate regression in either case, and a reduced or equal finding count across the frozen matrix.

Official layout basis: [CSS Writing Modes Level 3](https://www.w3.org/TR/css-writing-modes-3/), [CSS Logical Properties and Values Level 1](https://www.w3.org/TR/css-logical-1/), and [MDN `inline-size`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/inline-size).
