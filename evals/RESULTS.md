# Evaluation results

Recorded on 2026-07-14. These are bounded test results, not a claim that every model, framework, locale, or product category has passed.

## Codex v4 product-flow cohort

Recorded on 2026-07-15 in Asia/Taipei (generation timestamps are UTC). Three fixed Traditional Chinese product themes were generated with the same frozen pre-optimization Skill using requested identifiers `gpt-5.4-mini`, `gpt-5.4`, and `gpt-5.5`. All 9 targets completed across 13 attempts; 3 targets required retry. The pinned `@google/design.md@0.2.0` gate reported 9/9 clean with zero errors and warnings.

The updated Playwright auditor checked the same frozen HTML at desktop `1440×1000` and mobile `390×844` CSS viewports, retaining 30 decoded PNGs. Two targets had no observed blocking issue: harbor on `gpt-5.5` and plant swap on `gpt-5.4`. Seven targets retained at least one blocker.

| Theme | `gpt-5.4-mini` | `gpt-5.4` | `gpt-5.5` |
| --- | --- | --- | --- |
| Harbor cold chain | horizontal overflow; closed mobile navigation exposed | short action label wrapping/clipping | no observed blocker |
| Island sound archive | visible text clipping | critical collision; closed navigation; fixed/sticky obstruction; vertical-type failure | vertical-type failure |
| Plant swap | exact `lang="zh-Hant"` contract mismatch; short action label; fixed/sticky obstruction | no observed blocker | exact `lang="zh-Hant"` contract mismatch |

Evidence: [`product-flow-v4-generation-results.json`](product-flow-v4-generation-results.json), [`product-flow-v4-design-md-results.json`](product-flow-v4-design-md-results.json), [`product-flow-v4-visual-results.json`](product-flow-v4-visual-results.json), and [`product-flow-v4-targets/`](product-flow-v4-targets/). The README uses all 30 screenshots as a bounded feature/result showcase; those images are not an acceptance score. The current Skill includes rules derived from these findings, but it has not yet been regenerated against this cohort, so no post-fix pass is claimed.

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

Both received the same `briefs/product-dashboard.md`, trusted context revision, `CONSTRAINED` lane, tool surface and medium effort. Independent Playwright 1.61.1 checks used Chrome `150.0.7871.114` at `1440×1000` and `390×844`. Strict replay failed 4/4 viewport runs and exited 1 without DOM-click fallback; [`dashboard-playwright-acceptance.json`](dashboard-playwright-acceptance.json) retains the raw report. Diagnostic replay is separate and cannot upgrade acceptance. The bounded summary is in [`dashboard-browser-results.json`](dashboard-browser-results.json).

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
