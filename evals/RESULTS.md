# Evaluation results

Recorded through 2026-07-16. These are bounded test results, not a claim that every model, framework, locale, or product category has passed.

## Codex v6 self-repair cohort

Method classification: **development/regression closure, not held-out validation**. The same cases informed Skill rules, evaluator counterexamples, candidate selection, and final acceptance. The evidence below credibly closes this frozen cohort; it does not by itself prove generalization or candidate superiority on unseen tasks.

This published cohort used only the exact requested model `gpt-5.4-mini`, one frozen Skill revision, eight intentionally different products, 12 routes, and four device profiles. The first matrix completed 7/8; the repair-cafe output was rejected by output policy and then completed on a fresh bounded retry. The final initial generation ledger therefore records 8/8 completed without hiding attempt history.

Initial browser review left night-market allergen and royalty statement clean. Six targets received the smallest diagnostic repair. After broader Traditional Chinese typography, hierarchy, locale and layout research was folded into the latest Skill, all eight targets were reviewed again and changed relative to the previous repaired root:

| Target | Latest bounded repair |
| --- | --- |
| Wind maintenance | replaced Latin-width heading behavior with strict CJK wrapping and a font-relative measure |
| Type foundry | removed the narrow title cap, widened prose, localized fallback language, retained the vertical-to-horizontal recovery path, and added a compact-mobile display step that prevents a one-character final line |
| Repair cafe | returned title, introduction and form copy to one aligned reading flow without detached right-side prose |
| Night-market allergen | replaced the `ch` prose cap with a font-relative `em` measure |
| Royalty statement | aligned the hero summary with the heading, widened its readable column, and explained `tabular figures` in Chinese |
| Packaging configurator | replaced three narrow columns with purpose/action columns plus a spanning summary; removed a non-informative CSS dieline and obstructing sticky behavior |
| Oral-history archive | removed `11ch–18ch` title/body caps across all three routes, restored browser-owned wrapping, and localized the media fallback label |
| Grant review | removed narrow heading/body caps, preserved one intentional phrase, localized `shortlist` and `modal` UI copy, and moved secondary dialog status below the full-width mobile title track |

Earlier repaired passes found additional signals: oral-history prose still needed correction, and grant-review mobile interaction timed out because the evaluator targeted a hidden desktop action. The evaluator defect received a regression test before the product cohort was rerun. Later false positives in CJK/Latin measure, parent-container flow, heading detection, task-peer layout and translated terminology were likewise corrected in the evaluator rather than hidden by product changes.

A later Darwin-style candidate loop ran three complete `gpt-5.4-mini` generations and three 64-screenshot audits (192 PNG captures). `DESIGN.md` stayed 8/8 clean in every round, but the candidate finished with six targets carrying deterministic findings. Because it was worse than the accepted baseline, the ratchet rejected it and no candidate target or screenshot was promoted. The final publication instead repaired the accepted artifacts: it removed the packaging summary obstruction, converted the oral-history featured record into a real content/annotation split, sized footer surfaces around their reading measure, and made grant comparison/navigation hooks explicit in the public brief.

The evaluator also stopped depending on unannounced implementation details: package size selection now operates a semantic enabled radio without assuming lowercase `value="s"`; repair and royalty transitions use observable state; grant comparison uses brief-owned A/B and next-proposal hooks. The Codex runner now selects references by caller model and case. For the eight mini cases the embedded trusted context fell from 190,732 bytes to 145,024–161,274 bytes (15.4–24.0% less). This is a measured input reduction, not yet a latency or quality claim; the routed prompt needs its own future generation cohort.

Matched manual screenshot review then found a real defect the deterministic report had missed: grant-review status badges consumed the mobile dialog title track, leaving `策` alone on the final line. The evaluator was extended to reconstruct visible `h1–h3` line fragments and reject an accidental one-character CJK final line. Its first full 64-screenshot run immediately found the same class of defect in the type-foundry title, which was repaired with a tested mobile type step and balanced fallback. The second full run completed 64/64 with zero findings. This is a bounded counterexample-driven evaluator repair, not proof that every typographic craft defect is now machine-detectable.

Final bounded evidence:

- generation ledger: 8/8 current targets with latest-Skill repair provenance, before/output hashes and source-manifest hashes;
- official `@google/design.md@0.3.0` verifier: 8/8 clean, zero errors and warnings;
- browser inventory: 64/64 PNG across desktop `1440×1000` DPR 1, tablet `834×1112` DPR 2, mobile `390×844` DPR 3, and compact mobile `360×800` DPR 3;
- mobile profiles: Android Chromium UA, touch, `isMobile=true`, mobile screen and visual viewport—not width-only resize;
- final post-orphan-gate rerun: 64/64 screenshots and 8/8 targets with zero deterministic visual, runtime, network, body-flow, heading-flow, layout-flow, locale-flow, interaction or cross-page token-drift findings;
- screenshot publication: all 64 final PNG files were replaced by the post-contract output and rebound to the auditor/report by SHA-256; no rejected-candidate screenshot was promoted.

Artifacts: [`product-flow-v6-repaired-v2-generation-results.json`](product-flow-v6-repaired-v2-generation-results.json), [`product-flow-v6-repaired-v2-design-md-results.json`](product-flow-v6-repaired-v2-design-md-results.json), [`product-flow-v6-visual-results.json`](product-flow-v6-visual-results.json), [`product-flow-v6-repaired-v2-targets/`](product-flow-v6-repaired-v2-targets/), and [`../assets/product-flow-v6/`](../assets/product-flow-v6/).

Reproduce the evidence-integrity gate:

```bash
python3 wow-frontend-design/scripts/validate_product_flow_v6_evidence.py \
  evals/product-flow-v6-visual-results.json --repository-root .
```

This proves only this exact model/cohort, frozen evaluator, Chromium device emulation, and checked states. It does not certify physical phones, Safari/Firefox, OS assistive technology, formal WCAG conformance, real-user usability, production performance, or general model ranking.

## Platform, OS and environment snapshot

The one-version [`platform-support.json`](platform-support.json) snapshot records 32 host, operating-system, browser/device, environment and model cells against 22 reviewed official source coordinates. Each cell keeps install, discovery, invocation, implementation, browser and visual stages independent. The validator rejects missing inventory, unknown sources, unsafe artifacts, evidence/status contradictions and any scheduled recheck field.

Current positive evidence remains narrow: the Codex CLI `gpt-5.4-mini` v6 cohort has external pinned-Chromium visual evidence; Ubuntu CI validates installation, source/tests and checked-in evidence; macOS development evidence lacks a fully bound host-version/architecture/font manifest. Claude Code has historical generated outputs but failed strict browser acceptance. Copilot, Gemini CLI, Claude API, claude.ai, WSL, native Windows full harness, Firefox, WebKit, physical iOS/Android, read-only-home remote and exact local-model cohorts remain documented or untested—not silently promoted.

Official pages are mutable, but this file intentionally contains no next-review date: it describes only this repository version. A future release must replace it with a newly reviewed snapshot if maintainers choose to perform another platform review.

A three-OS GitHub Actions Python contract smoke is now configured for `ubuntu-latest`, `macos-latest` and `windows-latest`, following GitHub's documented matrix and explicit `setup-python` pattern. It validates installability, the platform/capability ledgers and focused portable tests, and emits a privacy-bounded runtime profile. Configuration is not execution evidence: macOS and Windows cells remain unpromoted until the workflow completes on those runners.

## Darwin advisory optimization audit

The trusted `alchaincyf/darwin-skill` source was pinned at commit `7c7b7909b630dc3b5cbb91bd4bcb1b10bfb1f894`. Two independent judges applied its nine-dimension rubric and runtime-neutrality scan to the current Skill plus three dry-run prompts: a Traditional Chinese mobile disaster-information build, a React returns-dashboard retrofit, and a read-only vertical/ruby literature audit. Runtime red-light matches were 0; both judges selected checkpoint design as the weakest safe dimension. The accepted one-line candidate now pauses only for new authority or material side effects and explicitly keeps ordinary authorized repair automatic.

The judges' advisory baseline totals differed (`89.7/100` and `83.1/100`); after the one-line candidate both independently returned `KEEP` (`90.3/100` and `84.3/100`). This disagreement and small delta demonstrate why the scalar is not an acceptance gate. Dry-run ratio was 100%, Darwin's published weights sum to 99 rather than the claimed 100, and no with-Skill/no-Skill rendered pair was produced. The candidate therefore remains subject to this repository's machine hard gates, complete unit/regression suite, evidence integrity, and human diff review. Generic Darwin suggestions to add frequent visual STOP markers, centralize duplicate blacklists, ban capability-bounded language, or let a weighted total choose the winner were rejected because they would worsen user experience, context cost, or evidence safety.

## Model routing and runtime downgrade contract

Research does not support a stable, self-reported `strong/weak` scalar. Agent Skills has no portable model selector; model routing studies show useful cost/quality trade-offs, but also distribution shift, model-recall gaps, and cases where simple baselines match complex routers. The repository therefore keeps model identity and initial routing outside the Skill:

- schema-v2 capability cells are keyed by task, locale, surface and risk, and bind the exact Skill, adapter, toolchain and evaluator revisions;
- only eligible independent runs count toward a higher lane; infrastructure failures are recorded separately;
- runtime events can keep or lower a lane, never raise it; ordinary repair findings self-correct first, while the third consecutive identical failure triggers bounded handoff of the best artifact;
- missing verification narrows the evidence claim, while missing safe mutation or a security/permission block changes the run to advisory.

Focused unit cases for [`route_model.py`](../wow-frontend-design/scripts/route_model.py) and [`runtime_downgrade.py`](../wow-frontend-design/scripts/runtime_downgrade.py) passed locally. That proves the encoded state machine and schema invariants only; no new model profile was promoted, and the v6 `gpt-5.4-mini` cohort remains the only current published visual cohort.

## Codex v5 mini product-flow cohort

Four intentionally different Traditional Chinese themes were generated with the exact requested model `gpt-5.4-mini` and one frozen pre-optimization Skill. Generation completed 4/4 targets across five attempts; the rail case retried once after isolated output policy rejected external temporary Skill-path access. After the evaluator lockfile moved to stable `@google/design.md@0.3.0`, all four frozen `DESIGN.md` files were re-linted and remained clean with zero errors and warnings. The old screenshot set and screenshot-bound visual report were intentionally cleared on 2026-07-15 before the next full cohort.

Mobile was a browser mobile profile—not width-only resize: `390×844` CSS viewport, DPR 3, Android Chromium user agent, touch, and `isMobile=true`. This still does not certify physical-device browser chrome, keyboard, GPU/font rendering, OS accessibility services, thermal behavior, or real touch latency.

| Theme | Deterministic repair-required evidence | Rendered/manual finding |
| --- | --- | --- |
| Rail rebooking | required disruption hook missing | confirmation state leaves a large unexplained left-side void and a detached lower-right summary |
| Subscription audit | mobile filter remains 8 instead of 4 because `display:block` overrides native `[hidden]` | dense mobile records need state-specific spacing review |
| Community translation | mobile review-open state restores desktop columns; segment list is 66px; action label wraps into a tall narrow control | severe one-character/word columns destroy Chinese, English, and Arabic comparison |
| Ceramics festival | three homepage card paragraphs render `line-height: 1.2` | semantic heading breaks and oversized mobile regions weaken rhythm |

The evaluator itself also had two defects and was fixed before these findings were promoted: a valid `zh-Hant-TW` tag was rejected even though the brief did not require an exact tag, and screen-reader-only clipped text was counted as visible. Paragraph measurement is now script-aware; long CJK text uses effective full-width characters rather than an English-only heuristic.

Retained evidence: [`product-flow-v5-mini-generation-results.json`](product-flow-v5-mini-generation-results.json), [`product-flow-v5-mini-design-md-results.json`](product-flow-v5-mini-design-md-results.json), and [`product-flow-v5-mini-targets/`](product-flow-v5-mini-targets/). The frozen generation Skill SHA-256 is `0e6337f3f4638c255908ca60b779782103aaecdc70d09001e0d4f2b44b919c47`. The table above is historical diagnosis, not currently published visual evidence.

This raw cohort intentionally remains immutable. The current Skill now treats these findings as internal self-repair input: automatically return code/route/state/viewport/measure/screenshot to the implementation loop, apply the smallest fix, run the narrow check, then regression. The benchmark's nonzero acceptance exit preserves evidence; it is not the end-user flow and does not justify hiding the usable artifact. The current post-optimization result is the separate v6 cohort above.

## Codex v4 product-flow cohort

Recorded on 2026-07-15 in Asia/Taipei (generation timestamps are UTC). Three fixed Traditional Chinese product themes were generated with the same frozen pre-optimization Skill using requested identifiers `gpt-5.4-mini`, `gpt-5.4`, and `gpt-5.5`. All 9 targets completed across 13 attempts; 3 targets required retry. The pinned `@google/design.md@0.2.0` gate reported 9/9 clean with zero errors and warnings.

The updated Playwright auditor checked the same frozen HTML at desktop `1440×1000` and mobile `390×844` CSS viewports. Those screenshots and the visual report were intentionally cleared before the next full cohort. Two targets had no observed blocking issue at the time: harbor on `gpt-5.5` and plant swap on `gpt-5.4`. Seven targets retained at least one blocker.

| Theme | `gpt-5.4-mini` | `gpt-5.4` | `gpt-5.5` |
| --- | --- | --- | --- |
| Harbor cold chain | horizontal overflow; closed mobile navigation exposed | short action label wrapping/clipping | no observed blocker |
| Island sound archive | visible text clipping | critical collision; closed navigation; fixed/sticky obstruction; vertical-type failure | vertical-type failure |
| Plant swap | exact `lang="zh-Hant"` contract mismatch; short action label; fixed/sticky obstruction | no observed blocker | exact `lang="zh-Hant"` contract mismatch |

Retained evidence: [`product-flow-v4-generation-results.json`](product-flow-v4-generation-results.json), [`product-flow-v4-design-md-results.json`](product-flow-v4-design-md-results.json), and [`product-flow-v4-targets/`](product-flow-v4-targets/). The current Skill includes rules derived from these findings; its separate post-fix run is the v6 cohort above, not a retroactive change to v4.

## `gpt-5.4-mini` weak-model retrofit

Environment: OpenAI cloud provider, fixed skill, hostile retrofit fixture, evaluator-owned scorer, evidence ledger, and independent browser reviewer.

| Stage | Result | Evidence |
| --- | --- | --- |
| Initial implementation | Browser FAIL | Background scroll lock, internal-link focus, valid→invalid form state, media honesty, dynamic accessible name, input contrast, and duplicate desktop navigation exposed defects. |
| Repair implementation | Static commands passed | `fixture-check` and `js-syntax` have successful ledger events. Source-level behavior remained `INFERRED`. |
| First structured handoff | Scorer FAIL | The model used descriptive evidence labels instead of exact ledger keys. |
| Skill-guided calibrated handoff | Scorer PASS | Exact ledger labels were used; browser and WCAG claims remained unverified until independent review. |
| Independent browser review | Observed; no tested failure | 1440×1000 and 390×844: navigation, overflow, menu inert/focus, filtering, favorites, valid→invalid form state, honest illustration labels, favicon, console and network checked. Product media remains clearly labeled illustrative rather than factual photography. |

The failure→repair loop is intentional evidence that model self-confidence is not an acceptance gate. The raw one-off reports and screenshots stay outside the repository; the website fixture and advisory static checker remain reproducible here. Browser observations are not presented as a reproducible automated suite or formal WCAG/assistive-technology result.

## Structured site-planning contract

The checked-in site manifest, user flows, wireframe plan, and XML sitemap example pass a dependency-free cross-artifact validator. Twenty-four hostile unit tests cover duplicate/unsafe routes, parent and redirect cycles, private discovery leakage, non-reciprocal locale alternates, stale manifest hashes, missing required states, fake evidence, self-certification, placeholder content, scaled/stack-only mobile plans, missing touch fallbacks, happy-path-only flows, flow cycles, route/state/role mismatches, and sitemap drift/DTD input.

This is deterministic contract evidence only. No user study, visual-quality result, production crawl, indexing outcome, or model improvement follows from a valid planning artifact.


## Audience and preference adaptation — exploratory only

The same museum-domain task was explored with two materially different contexts:

- donor/trust context: purpose and safety before calls to action, disclosures and FAQ, low interaction noise;
- curator/power-user context: dense index, search-first workflow, keyboard use, comparison states, and batch actions.

The observed directions changed information architecture, density, interaction priority, and mobile transformations—not only colors. The raw prompts/outputs were not retained in this repository, so this is not reproducible benchmark evidence and must not be used to promote a model profile. A future scored claim needs frozen briefs, independent runs, artifacts, and the same evaluator.

## Claude CLI strong/weak product dashboard matrix

Claude CLI `2.1.183` successfully generated both fixed product-dashboard cases through the logged-in official account. The runner cleared inherited provider/model environment, used `--safe-mode`, allowed only `Write`, and published exactly three files only after the isolated output policy passed. Manifests retain brief, context, runner and output hashes. Claude CLI did not report the aliases' resolved exact model IDs, so the results are recorded as requested `haiku` and `opus` aliases—not provider-version certification.

Both received the same `briefs/product-dashboard.md`, trusted context revision, `CONSTRAINED` lane, tool surface and medium effort. Independent Playwright 1.61.1 checks used Chrome `150.0.7871.114` at `1440×1000` and `390×844`. Strict replay failed 4/4 viewport runs and exited 1 without DOM-click fallback; [`dashboard-playwright-acceptance.json`](dashboard-playwright-acceptance.json) retains the raw report. Diagnostic replay is separate and cannot upgrade acceptance. The screenshot-bound summary was cleared with the old screenshot set.

| Requested alias | Result | Observed strengths | Strict blockers |
| --- | --- | --- | --- |
| Haiku | FAIL | 8 rendered rows; filter/zero/restore; local state update; no page overflow; reduced-motion steady state | unreachable error path; retry reopens the same error; no overlay scroll lock/inert/focus return; remote-sounding success; mobile clear button can be pointer-obstructed; missing favicon; self-report exceeded its tool evidence |
| Opus | FAIL | 10 rows; filter/zero/restore; master-detail desktop; distinct full-width mobile detail; honest local/unsynced copy; local retry and stale-message cleanup | mobile background not inert; no focus containment; Escape leaves focus on a now-hidden detail heading because rerender replaced the saved row; missing favicon |

The Opus output was visually more product-specific in this one non-blind observation. One paired run cannot establish a model ranking, provider-wide quality, award quality, WCAG conformance, or general weak/strong performance.

The earlier `claude-{haiku,opus}-showcase/` directories are retained as raw exploratory output. They predate the hardened manifest path and are not scored as a controlled release cohort.

## Single Haiku remediation quota

After adding the anti-AI-slop contract, one additional Haiku invocation used the same product-dashboard brief under case `product-dashboard-remake`. The changed Skill context makes it remediation evidence, not a same-context comparison.

The runner rejected the output before publish because `styles.css` contained a URI scheme forbidden by the isolated output policy. No HTML/CSS/JS artifact or screenshot was accepted, and the run was not retried. [`rejected-run.json`](claude-haiku-product-dashboard-remake/rejected-run.json) records the exact boundary. This result shows fail-closed containment; it does not show design improvement.

No Claude run passed strict acceptance. Model self-reports remain diagnosis only.
