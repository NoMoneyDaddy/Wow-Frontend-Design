# Evaluation results

Recorded through 2026-07-15. These are bounded test results, not a claim that every model, framework, locale, or product category has passed.

## Codex v6 self-repair cohort

This published cohort used only the exact requested model `gpt-5.4-mini`, one frozen Skill revision, eight intentionally different products, 12 routes, and four device profiles. The first matrix completed 7/8; the repair-cafe output was rejected by output policy and then completed on a fresh bounded retry. The final initial generation ledger therefore records 8/8 completed without hiding attempt history.

Initial browser review left night-market allergen and royalty statement clean. Six targets received the smallest diagnostic repair:

| Target | Reproducible initial problem | Repair outcome |
| --- | --- | --- |
| Wind maintenance | desktop/tablet lead exceeded the CJK reading measure | constrained the prose measure without changing mobile behavior |
| Type foundry | vertical-writing interaction caused mobile horizontal overflow | constrained logical size and wrapping while preserving the writing-mode switch |
| Repair cafe | sticky desktop action overlaid the textarea; prose was too wide | returned action to a non-obstructing layout and corrected CJK measure |
| Packaging configurator | mobile sticky summary covered headings, choices and actions | changed mobile summary/actions to a non-obstructing composition |
| Oral-history archive | body copy did not use an aligned readable content column | restored browser-owned wrapping, full content-column flow and CJK editorial alignment |
| Grant review | desktop descriptions were squeezed to about `5.47em` | redesigned the dense row so prose receives a readable column |

The first repaired browser pass found two more signals. Oral-history prose was still too wide and received one additional repair. Grant-review mobile interaction timed out because the evaluator targeted a hidden desktop action; this was classified as an evaluator defect, fixed with a regression test, and rerun without changing the product for the false positive.

Final bounded evidence:

- generation ledger: 8/8 current targets with repair/promotion provenance and source-manifest hashes;
- official `@google/design.md@0.3.0` verifier: 8/8 clean, zero errors and warnings;
- browser inventory: 64/64 PNG across desktop `1440×1000` DPR 1, tablet `834×1112` DPR 2, mobile `390×844` DPR 3, and compact mobile `360×800` DPR 3;
- mobile profiles: Android Chromium UA, touch, `isMobile=true`, mobile screen and visual viewport—not width-only resize;
- final findings: zero deterministic visual, runtime, network, forced-body-break, and non-wrapping-prose issues;
- manual review: all final screenshot content inspected; byte-identical screenshots remained tied to the inspected prior pass by SHA-256.

Artifacts: [`product-flow-v6-repaired-v2-generation-results.json`](product-flow-v6-repaired-v2-generation-results.json), [`product-flow-v6-repaired-v2-design-md-results.json`](product-flow-v6-repaired-v2-design-md-results.json), [`product-flow-v6-visual-results.json`](product-flow-v6-visual-results.json), [`product-flow-v6-repaired-v2-targets/`](product-flow-v6-repaired-v2-targets/), and [`../assets/product-flow-v6/`](../assets/product-flow-v6/).

Reproduce the evidence-integrity gate:

```bash
python3 wow-frontend-design/scripts/validate_product_flow_v6_evidence.py \
  evals/product-flow-v6-visual-results.json --repository-root .
```

This proves only this exact model/cohort, frozen evaluator, Chromium device emulation, and checked states. It does not certify physical phones, Safari/Firefox, OS assistive technology, formal WCAG conformance, real-user usability, production performance, or general model ranking.

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
