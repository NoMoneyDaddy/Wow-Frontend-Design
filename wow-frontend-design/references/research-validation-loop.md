# Research and validation feedback loop

Use this reference when maintaining the Skill, integrating upstream guidance, or turning model/browser/reviewer findings into durable improvements.

## Preserve evidence before fixing

Record a stable case ID, task/locale, Skill and adapter hashes, exact model/provider/alias resolution, auth mode, tools, prompt/context hashes, writable files, output manifest, commands, browser/version, viewports/preferences, raw findings, screenshots, and timestamps. Keep raw model output immutable. Put repairs in a new run or clearly separated corrected artifact.

## Classify the root cause

```text
KNOWLEDGE       missing/wrong research or platform rule
INSTRUCTION     rule exists but is ambiguous, too long, or not routed
MODEL           supplied contract was ignored or hallucinated
HOST/ROUTING    alias, context, tool, auth, or fallback contamination
IMPLEMENTATION  code defect under an adequate contract
EVALUATOR       false positive/negative, weak fixture, mutable gate
SUBJECTIVE      craft disagreement needing blind rendered review
```

Do not repair a host failure by weakening the design rubric, or repair one ugly screenshot by adding a universal style ban.

## Put the control at the lowest reliable layer

| Finding | Durable destination |
| --- | --- |
| evidence or concept boundary | focused reference with primary sources and transfer limits |
| weak model skips a critical step | short immutable contract/freeze card |
| project type needs different guidance | trigger/reference routing or platform adapter |
| exact syntax/security invariant | scanner plus regression tests |
| interaction/state transition | evaluator-owned browser assertion |
| rendered hierarchy/craft | matched screenshots plus independent/blind review |
| unsupported self-claim | evidence policy/ledger, never more self-reflection |
| model/provider alias contamination | runner provenance and fail-closed preflight |

## Require a counterexample

Every fix needs:

1. the original failing fixture;
2. a nearby valid case that must remain valid;
3. a nearby invalid case that must still fail;
4. an explicit claim boundary;
5. the cost in context, false positives, runtime, bundle, or creative freedom.

Run the narrow regression first, then the complete suite. Three identical failed repair attempts trigger the workflow fuse; preserve the evidence and escalate rather than guessing indefinitely.

## Promote research cautiously

Prefer current standards, official platform/framework documentation, systematic reviews, and original peer-reviewed work. Record revision/date, applicable population/platform, outcome, limitations, and license. Community Skills and popular repositories are design hypotheses and implementation examples, not authority or permission to copy.

Research becomes a normative Skill rule only when it is broadly transferable, safety/access critical, or explicitly bounded. Contextual findings become a decision question or experiment. Aesthetic opinion stays a reviewer heuristic. Deprecated or contradicted guidance is removed with a migration note and regression coverage.

## Prevent benchmark overfitting

- Keep held-out cases outside the implementation model's writable surface.
- Compare product-diverse tasks, locales, states, frameworks, and mobile transformations.
- Separate infrastructure, contract validity, accessibility, behavior, performance, and blind visual craft scores.
- Repeat stochastic runs; never infer a model tier from one page.
- Measure context/token cost and reference routing after adding guidance.
- Do not let a better benchmark score justify worse maintainability, accessibility, or design convergence.

## Case study: Design Skill Comparison Lab

Reviewed 2026-07-15: [designskill.qiaomu.ai](https://designskill.qiaomu.ai/) (page publication date 2026-07-04). This mutable community experiment exposes 80 live pages across ten task types and eight variants. Treat it as a useful benchmark-design hypothesis, not an authority, reusable asset library, or independent model ranking.

Transfer these methods:

- separate constrained product tasks from open creative tasks; one score cannot represent both discipline and visual range;
- cover marketing, dense data, portfolio/editorial, multi-step validation, component states, error recovery, deliberate diversity, commerce, mobile-first composition, and data storytelling;
- hold each task brief and technical boundary constant inside a cohort, while changing the task family between rounds to limit memorization;
- evaluate real interactions, focus/error recovery, touch behavior, motion and route consistency in addition to screenshots;
- compare visual distinction and production acceptance as separate axes;
- use negative constraints and deterministic preflight for known failure modes, but keep a positive product thesis and authored-detail requirement so bans do not merely raise the floor;
- publish real artifacts in a task switcher or screenshot gallery, while linking every showcase to its blocker report and provenance.

Do not inherit its conclusions directly. The site discloses one sample per variant/task, qualitative author scoring rather than multi-reviewer blind scoring, spot-checked rather than exhaustive interaction tests, and home-field advantage for the author's fused Skill. The evolving page also mixes older round-count wording with the current 80-page inventory. It does not expose the complete exact-model, prompt/context-hash, run-ledger, timeout, failure, or per-artifact hash provenance required by this Skill. Its scaled iframe previews are good discovery UI, not viewport or accessibility evidence. Recreate the useful task dimensions with evaluator-owned manifests, immutable attempt history, exact provider cohorts, automated browser assertions, decoded screenshot hashes, and an independent craft review.

## Close the loop

```text
observe → preserve → classify → research → place control → add counterexamples
        → fix → narrow test → full test → independent review → version/release note
```

Mark the result `verified`, `partially verified`, `rejected`, or `unresolved`. Link the finding to the exact changed rule/test and the rerun evidence. If the result depends on a subjective rendered judgment, say so; a scanner exit code cannot close it.
