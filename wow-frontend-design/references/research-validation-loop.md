# Research and validation feedback loop

Use this reference when maintaining the Skill, integrating upstream guidance, or turning model/browser/reviewer findings into durable improvements.

## Preserve evidence before fixing

Record a stable case ID, task/locale, Skill and adapter hashes, exact model/provider/alias resolution, auth mode, tools, prompt/context hashes, writable files, output manifest, commands, browser/version, viewports/preferences, raw findings, screenshots, and timestamps. Keep raw model output immutable. Put repairs in a new run or clearly separated corrected artifact.

## Freeze package and script-runtime evidence separately

Treat Agent Skills package compatibility as one standards contract. Do not create a model-brand support matrix or fork the Skill for Codex, Claude, Copilot or Gemini. Host-specific installation and discovery remain integration checks; model quality belongs to a separate evaluation cohort.

Track only executable runtime differences here: installed Python scripts, OS, required commands, POSIX evaluator assumptions, browser backend and visual evidence. Keep static → unit → Linux → macOS → Windows → browser → visual stages distinct. A configured job is not a completed run; Chromium is not Firefox/WebKit; browser emulation is not a physical-device result. Preserve `failed`, `partial`, `not_supported` and `not_run` instead of collapsing them into “supported”. Every non-test Python entrypoint bundled under `scripts/` must appear exactly once in the runtime matrix.

Before a portability run, capture privacy-bounded host provenance into evaluator-owned storage:

```bash
python3 <skill-dir>/scripts/capture_runtime_profile.py \
  --environment-kind ci \
  --shell-name github-actions \
  --node-version v22.18.0 \
  --browser-engine chromium \
  --browser-version 150.0.7871.124 \
  --font-profile-id ci-default-v1 \
  --network available --browser available --screenshots available
```

The helper does not inspect hostname, user, home, IP, environment variables, network or installed fonts, and does not execute external commands. Caller-supplied versions are declarations; bind them to setup logs, lockfiles or a browser report before promoting a claim. Keep only Agent Skills, Python CI and browser-runtime source coordinates in [platform-support-sources.json](platform-support-sources.json), and validate the repository-owned script matrix without adding an automatic recheck schedule. A newly configured CI cell remains `not_run` until its own completed run is preserved.

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

## Control system growth

Do not add a checker, schema field, screenshot, dependency, or universal rule merely because another edge case is imaginable. First show a reproducible defect, why the existing instruction or lowest reliable gate cannot express it, a valid counterexample, and the measured context/runtime/maintenance cost. Prefer clarifying a mother rule, fixing a false-positive boundary, or reusing one browser primitive over adding a parallel mechanism. A candidate that adds more surface than distinct claim coverage must replace or consolidate existing surface; otherwise reject it.

Freeze one scope-proportionate discovery pass before execution, including its routes, states, viewports, interactions, and cap. Stop a product loop after the acceptance contract passes once and that bounded pass has no open reproducible finding. A new ordinary finding outside the frozen pass queues for a separately authorized round instead of silently expanding the current loop. A reproducible safety, data-integrity, primary-task, or accessibility hard-gate finding immediately limits the affected claim to `PARTIALLY VERIFIED` or `UNVERIFIED`; preserve its evidence and open one explicitly bounded repair round.

A Skill round has three exits. Promote only when the candidate passes affected evidence plus every applicable release/held-out gate. Reject and roll back to best-so-far when an affected hard gate regresses or the bounded hypothesis fails. Preserve `PARTIALLY VERIFIED` or `UNVERIFIED` when required infrastructure remains unavailable after its bounded retry. Fire the no-gain fuse when two consecutive Skill candidates with the same failure key improve neither the lexicographic hard-gate vector nor distinct claim coverage while context/runtime/maintenance cost stays level or grows; retain best-so-far and stop. Passing evidence is a convergence signal, not an invitation to invent another probe.

## Promote research cautiously

Prefer current standards, official platform/framework documentation, systematic reviews, and original peer-reviewed work. Record revision/date, applicable population/platform, outcome, limitations, and license. Community Skills and popular repositories are design hypotheses and implementation examples, not authority or permission to copy.

Treat Context7 as retrieval provenance, not primary authority. When it is used, record the resolved library ID/version, lookup date, query scope, and the upstream source revision that supports the claim. Current Playwright lookup (2026-07-18) resolved `/microsoft/playwright/v1.61.0` for BrowserContext isolation and route/setup semantics; the versioned [browser-context](https://github.com/microsoft/playwright/blob/v1.61.0/docs/src/browser-contexts.md) and [BrowserContext API](https://github.com/microsoft/playwright/blob/v1.61.0/docs/src/api/class-browsercontext.md) sources support sharing one browser while giving every replay a fresh context, and document that routing disables HTTP cache while Service Workers can hide requests from interception. The installed patch is `playwright@1.61.1`; no evaluator behavior changes from the lookup alone. If retrieved text and a version-matched official upstream source differ, the version-matched official source governs, and retrieved prose must not be copied into runtime instructions as an evergreen rule.

Reviewed 2026-07-18 at [`microsoft/playwright-mcp@55679f5`](https://github.com/microsoft/playwright-mcp/blob/55679f5f3d4b4f3e2534ec0ce2fc5683ba2eaf3f/README.md#playwright-mcp-vs-playwright-cli), Apache-2.0. Its official comparison says CLI plus Skills avoids loading large tool schemas and verbose accessibility trees into the model context for high-throughput coding work, while MCP remains useful when persistent state and iterative page introspection outweigh token cost. Use that as a routing boundary only: neither interface proves product behavior without a source-bound replay and receipt from the pinned verification plane.

Research becomes a normative Skill rule only when it is broadly transferable, safety/access critical, or explicitly bounded. Contextual findings become a decision question or experiment. Aesthetic opinion stays a reviewer heuristic. Deprecated or contradicted guidance is removed with a migration note and regression coverage.

## Stage browser and typography findings as candidates

Reviewed 2026-07-16. Keep compatibility, rendered correctness, and craft as separate claims.

- Use a semantic, usable baseline and capability checks such as `@supports`; do not branch layout, effects, or interaction from a user-agent name. [MDN progressive enhancement](https://developer.mozilla.org/en-US/docs/Glossary/Progressive_Enhancement), [feature queries](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Conditional_rules/Using_feature_queries), and [UA detection guidance](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Browser_detection_using_the_user_agent) support this boundary.
- Treat [Baseline](https://web.dev/baseline) as a web-feature availability signal, not proof that this product looks, wraps, performs, or interacts correctly in its supported browsers.
- Name exact evidence. Playwright Chromium, its patched Firefox, and its WebKit build are distinct engine evidence; Playwright WebKit is not branded Safari and its Firefox is not branded Firefox. Use macOS WebKit for a closer Safari signal where applicable, and add branded stable Chrome or Edge only when that public channel matters. Do not promote configured or downloaded browsers to tested status. See [Playwright browser support](https://playwright.dev/docs/browsers).
- Compare exact pixels only within the same pinned engine, OS, fonts, data, route, state, viewport and preferences. Across engines, assert semantic structure, task behavior, overflow, collisions, focus, legibility, line-fragment risks and intended hierarchy; review expected rasterization and line-breaking differences instead of forcing pixel identity.
- Treat `text-wrap` as browser-owned progressive enhancement. The useful shorthand “`balance` for headings, `pretty` for prose” from this [iThome example](https://ithelp.ithome.com.tw/articles/10388750) is a hypothesis, not an acceptance rule. [WebKit's balance notes](https://webkit.org/blog/15383/webkit-features-in-safari-17-5/) document different engine line limits and show that balancing can leave substantial right-side whitespace; [WebKit's pretty analysis](https://webkit.org/blog/16547/better-typography-with-text-wrap-pretty/) explains that algorithms deliberately vary and rejects a universal heading/body recipe. Measure the resulting lines and fallback, not property presence. Prefer `stable` for editable text when repeated reflow would be disruptive.
- Use [CLReq](https://www.w3.org/TR/clreq/) to define Traditional Chinese fixtures: prohibited punctuation at line edges, mixed-script boundaries, horizontal and vertical writing, ruby/Bopomofo, and a final line containing one Han character or one character plus punctuation. Its 17–40-character book-body range, 48-character horizontal maximum, 55-character vertical maximum, justification practice, and orphan repair methods are editorial starting envelopes—not universal responsive-web gates. Test the product's font, medium, column and task before adopting them.
- Older readability articles can generate candidates, but their numeric recipes do not become standards. This [UISDC article](https://www.uisdc.com/improve-text-legibility) correctly frames size, whitespace, alignment and contrast as interacting decisions, while its fixed ratios and spacing values require current product evidence. Prefer current WCAG contrast/text-spacing requirements and rendered comparison over inherited golden ratios.
- The supplied [Zhihu readability article](https://zhuanlan.zhihu.com/p/30018110) was unavailable to the evaluator; an attributed [syndicated copy](https://www.woshipm.com/pd/850427.html) preserves its discussion of polarity, pure black/white, gray backgrounds and time-varying luminance. Its cited studies span different decades, displays, populations and reading tasks. Do not turn them into bans on dark mode, `#000`/`#fff`, or a timer-driven contrast change. Keep WCAG contrast, user-selected color scheme, forced colors, stable semantics and product-specific user testing as the gates; treat comfort or adaptive-luminance claims as opt-in research hypotheses.
- Treat CJK font delivery as a measured product tradeoff. This [Penchan case study](https://penchan.co/ai/coding/cjk-font-performance/) is useful evidence that a large CJK font stylesheet and many faces can dominate one site's cold load, but its 17-to-2-second result, system-font choice, self-hosting preference and `optional` recipe do not generalize by assertion. [web.dev's font guidance](https://web.dev/articles/font-best-practices) confirms the durable mechanisms: reduce faces, subset large CJK repertoires, use `unicode-range`, select `font-display` by role, preload only critical faces, keep metric-compatible fallbacks, and measure layout shift. Freeze network/profile/cache and compare CSS bytes, font requests/bytes, text visibility, FCP/LCP, CLS, line fragments and task completion before choosing system fonts, prebuilt subsets or a branded webfont.

Candidate deterministic gates need both a failing fixture and a nearby valid counterexample:

| Candidate | Fail signal | Required counterexample |
| --- | --- | --- |
| capability fallback | essential task disappears when the enhancement is unsupported | enhancement absent while baseline task remains usable |
| text-wrap result | one-character final CJK line, split compact term, overflow, or balance-created unused title track | intentional short display line or editorial rag remains allowed |
| intrinsic layout | flex/grid min-content, fixed height, URL, translation, zoom, or fallback font creates clipping or a one-character rail | genuinely narrow control, table, or vertical-writing region remains valid |
| intermediate geometry | layout passes named devices but fails between breakpoints or at short viewport height | intentional content-driven mode change remains stable in both directions |
| mobile viewport | browser chrome, virtual keyboard, safe area, sticky UI, `svh`/`lvh`/`dvh` obscures the task | non-fixed content without that risk is not forced into device-specific code |
| native controls | select/date/color/file, autofill, validation, focus, IME, zoom or forced colors loses label, value, error or action | native platform appearance differences remain acceptable |
| CJK font delivery | cold/slow/failed font delays visible text, shifts layout, changes critical wrapping, downloads unused faces, or loses required glyphs | intentional system-font variance or a measured branded face remains allowed |

Keep practitioner advice in the review layer. [Andy Bell](https://buildexcellentwebsit.es/) argues for intrinsic rules that guide the browser instead of rigidly micromanaging every size. [Ahmad Shadeed's defensive CSS](https://ishadeed.com/article/defensive-css/) supplies adversarial fixtures such as long content, flex wrapping, min-content traps, image ratios, scrollbars and short viewports; his [breakpoint analysis](https://ishadeed.com/article/too-early-breakpoint/) motivates intermediate-width testing. [NN/g's F-pattern analysis](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/) treats scanning as a response to weak hierarchy rather than a layout recipe. These are craft hypotheses for independent rendered review, not universal scanner failures.

Do not modify the accepted Skill merely because this research sounds plausible. First encode the candidate, counterexample, affected routes and exact claim boundary; then promote it only through the validation ratchet below.

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

For the frozen v7 two-case accepted/candidate comparison, `--gate fast` is an exact 16-artifact loop: two cases × accepted/candidate × base/interaction × desktop/mobile × Chromium. It is the repair/candidate gate, not release evidence. `--gate full` is the exact 60-artifact comparison: per case and variant, six Chromium base profiles plus desktop/short-desktop/mobile interaction replay in Chromium, Firefox, and WebKit. The ledger records the gate and the validator rejects mixed, missing, or extra inventory. Use full after a candidate wins the fast gate and for the final retained release comparison; a fast pass cannot be relabeled full.

Do not optimize only on greenfield generation. Each new validation family should contain, across its development/validation split, both a new/empty BUILD task and an existing-project RETROFIT task. The retrofit fixture must freeze public routes, component/API or state behavior, representative before screenshots, and user-owned design equity; at least one case should require controlled system/composition/architecture refactoring rather than CSS-only polish. Ask for a material direction choice only when the brief has not already resolved it. Score preserved behavior, migration scope, diff focus, before/after browser evidence, and removal of the evidenced structural debt separately from visual craft.

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
