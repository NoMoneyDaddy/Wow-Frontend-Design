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

Run the narrow regression first, then the complete suite. The loop is automatic: the user must not relay diagnostics or restart the Skill between attempts. Three identical failed repair attempts trigger the workflow fuse; preserve the best working artifact, screenshots, and evidence, then hand off `PARTIALLY VERIFIED` with the next executable action rather than guessing indefinitely or returning an empty rejection.

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

## Validation-gated Skill optimization

Treat a Skill edit as a candidate, not an improvement claim:

1. Freeze the current accepted Skill, evaluator, assertions, viewports, dependency lock, and task split.
2. Run both versions on the same training cases with and without the Skill when trigger value is under test. Repeat stochastic cases and report mean, spread, failures, and flaky assertions.
3. Allow the authoring loop to inspect training failures, but keep validation and test prompts outside its writable context. Include both should-trigger and should-not-trigger cases.
4. Accept only when held-out validation improves and hard safety, security, accessibility, evidence-integrity, trigger-precision, and packaging gates remain clean. Keep best-so-far and rejected-candidate history so rollback is deterministic.
5. Use an independent evaluator for rendered craft, then run the untouched test split once for the release record. A model cannot author the Skill, choose the rubric, and certify its own result.

Apply an edit budget: prefer one bounded hypothesis and its counterexample over a broad rewrite. Context length, reference fan-out, runtime, and false positives are part of the score. Line count or semantic density can flag bloat, but never accept a candidate by themselves. Normal user runs use the accepted Skill plus automatic repair/downgrade; benchmark optimization is a separate maintainer workflow and must not mutate Git automatically.

Keep the two loops separate:

- **Product repair loop**: one user's artifact; preserve preview, repair deterministic findings, narrow-test, affected-test, hand off. It may improve the current result but cannot claim the Skill generalized.
- **Skill optimization loop**: accepted vs candidate Skill; freeze training/validation/test partitions, evaluator and dependency/tool revisions; compare independent runs; promote only through the ratchet. It never modifies a user's live product as benchmark state.

Measure cost and quality together, but never total them into one compensating score:

| Family | Required measurements |
| --- | --- |
| Trigger/routing | should-trigger precision/recall, selected reference names/count/bytes, input tokens, adapter/lane, routing reason |
| User latency | time to first usable artifact, wall time, stage durations, progress checkpoints, user-relay count |
| Retry/repair | attempt count, retry cause, repair rounds, repeated failure key, fuse action, best-artifact preservation |
| Tooling | cold/warm install time, exact version, cache hit, download/probe time, product dependency drift |
| Verification | fast/affected/release runtime, evidence coverage, flaky assertion rate, screenshot count/bytes, recurrence after full regression |
| Output quality | required hard-gate vector, independent craft vector, remaining risks; optional award lens remains separate |

Select the best artifact lexicographically: safety/data integrity/primary task → required evidence coverage → deterministic defect vector → independent craft → runtime/context cost. A cheaper run cannot win by breaking a hard gate, and a prettier run cannot win by hiding missing evidence.

Use three test circles:

1. **Fast**: router, schema, retry/downgrade state machine, changed-reference checks, and one bounded smoke.
2. **Affected**: cases, routes, states, locales and viewports selected by the changed context/gate manifest.
3. **Release**: complete development regression, sealed held-out validation/test, evidence integrity, and independent blind rendered review.

The current v6 eight-case cohort is development/regression evidence because its findings influenced the Skill and evaluator. Do not relabel it held-out. New validation/test tasks must remain outside authoring context, cover unseen layout/locale/framework/interaction families, compare no-Skill/accepted/candidate where relevant, and repeat stochastic cases. The untouched test split runs once for release; return only aggregate failure families to future authoring, not hidden prompts, weights, selectors or expected DOM.

## Case study: Design Skill Comparison Lab

Reviewed 2026-07-15: [designskill.qiaomu.ai](https://designskill.qiaomu.ai/) (page publication date 2026-07-04). This mutable community experiment exposes 80 live pages across ten task types and eight variants. Treat it as a useful benchmark-design hypothesis, not an authority, reusable asset library, or independent model ranking.

Transfer these methods:

- separate constrained product tasks from open creative tasks; one score cannot represent both discipline and visual range;
- cover marketing, dense data, portfolio/editorial, multi-step validation, component states, error recovery, deliberate diversity, commerce, mobile-first composition, and data storytelling;
- hold each task brief and technical boundary constant inside a cohort, while changing the task family between rounds to limit memorization;
- evaluate real interactions, focus/error recovery, touch behavior, motion and route consistency in addition to screenshots;
- compare visual distinction and production acceptance as separate axes;
- use negative constraints and deterministic preflight for known failure modes, but keep a positive product thesis and authored-detail requirement so bans do not merely raise the floor;
- publish real artifacts in a task switcher or screenshot gallery, while linking every showcase to its finding report and provenance.

Do not inherit its conclusions directly. The site discloses one sample per variant/task, qualitative author scoring rather than multi-reviewer blind scoring, spot-checked rather than exhaustive interaction tests, and home-field advantage for the author's fused Skill. The evolving page also mixes older round-count wording with the current 80-page inventory. It does not expose the complete exact-model, prompt/context-hash, run-ledger, timeout, failure, or per-artifact hash provenance required by this Skill. Its scaled iframe previews are good discovery UI, not viewport or accessibility evidence. Recreate the useful task dimensions with evaluator-owned manifests, immutable attempt history, exact provider cohorts, automated browser assertions, decoded screenshot hashes, and an independent craft review.

## r/UXDesign community signal

Reviewed 2026-07-15: community discussions on [actual AI design workflows](https://www.reddit.com/r/UXDesign/comments/1tf2yea/actual_ai_design_workflows_in_2026/), [AI in enterprise design systems](https://www.reddit.com/r/UXDesign/comments/1tsy4sh/has_anyone_successfully_integrated_ai_into_a/), and [case-study length](https://www.reddit.com/r/UXDesign/comments/1uwdqj5/can_we_please_talk_about_case_study_length/). These are self-selected anecdotes, not representative research or normative evidence.

Useful hypotheses are screenshot QA, requirement-coverage checks, localization/research synthesis, editable code prototypes, and a persistent design-system description. Repeated risks are generic output, design-system/component drift, false confidence, and one-way “handoff-ready” claims. Therefore:

- frame AI work with exact task, route, state, locale, device, acceptance criteria, and editable artifact;
- keep `DESIGN.md` ↔ runtime conformance plus independent browser evidence;
- treat AI findings as hypotheses until a deterministic check or human review confirms them;
- do not let model self-review certify production handoff;
- preserve provenance and code that a designer/developer can inspect and revise.

The case-study discussion disagrees on a universal word count. Its durable signal is layered editorial hierarchy: lead with outcome and decision, make evidence scannable, and let interested readers expand into process detail instead of forcing every reader through one long narrative.

## Close the loop

```text
observe → preserve → classify → research → place control → add counterexamples
        → fix automatically → narrow test → full test → independent review
        ↖──────────────── repair required ────────────────┘
        → verified handoff / best-artifact partial handoff
```

Mark the result `verified`, `partially verified`, `rejected`, or `unresolved`. Link the finding to the exact changed rule/test and the rerun evidence. If the result depends on a subjective rendered judgment, say so; a scanner exit code cannot close it.
