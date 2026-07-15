# Quality gates and self-repair

Use this reference to verify and automatically repair a frontend before calling it verified. These gates steer the implementation loop; they are not a rejection UI for the user. Award-level intent does not excuse fragile implementation.

## Contents

1. Required evidence
2. Three-pass review
3. Viewport and state matrix
4. Independent scorecard
5. Internal completion gates

## 1. Required evidence

Collect what the environment allows:

- successful build, typecheck, lint, and focused tests;
- screenshots of representative routes at mobile and desktop widths;
- screenshot provenance and source/build freshness when visual baselines or documentation images are used; follow [visual-regression-evidence.md](visual-regression-evidence.md);
- browser console and failed network request check;
- keyboard path and focus order check;
- accessibility scan plus manual review, and a complete applicable WCAG 2.2 A/AA checklist when AA conformance is required;
- reduced-motion and no-hover behavior;
- 200% zoom/text resize and 400% zoom or 320 CSS px equivalent reflow behavior;
- long Traditional Chinese and expanded-locale behavior;
- field CrUX/RUM evidence for Core Web Vitals when available, segmented by mobile/desktop at p75 with all three metrics passing;
- lab Lighthouse/trace evidence for regression and diagnosis only—TBT is an INP proxy, not an INP measurement;
- before/after comparison for retrofit work.
- public-route metadata and share preview checks when relevant: title, description, canonical/locale policy, truthful structured data, social crop, document language, and missing icon/asset requests.
- search/discovery checks when relevant: HTTP/index/snippet policy, crawlable internal links, canonical/hreflang agreement, rendered text, sitemap freshness, truthful page-type structured data, and separately authorized search/training/user-agent crawler policies;
- a `forced-colors: active` pass on supported desktop browsers for focus, controls, selected/current state, icons, charts, and custom surfaces;
- when appearance switching is supported, matched `system`, explicit light, and explicit dark runs covering persistence, live system changes, first-paint flash, native controls, images/icons/charts, focus, overlays, and increased/forced contrast;
- a trust/choice pass for pricing, renewal, consent, defaults, cancellation, destructive actions and vulnerable-user paths; compare acceptance/rejection effort and disclosure timing;

For every audit tool, record the exact version, browser/runtime, configuration, URL/build revision, authenticated state, wait condition, scope, timestamp, and raw artifact. Lighthouse, axe, browser engines, rule IDs, scoring, and report schemas change; do not hardcode removed audit names or compare scores across tool versions as if they were identical. Field Core Web Vitals and lab diagnostics remain different evidence classes.

Record executable checks with an evaluator-initialized `scripts/evidence_ledger.py` run and frozen evidence policy when available. Use one evaluator-owned root containing sibling `ledger.json`, `policy.json`, `artifacts/`, and a child `workspace/`; the implementation model may write only `workspace/`. Every ledger `run` must pass `--cwd <evaluator-root>/workspace` (or a descendant), every policy command `cwd` must resolve inside that workspace, and observed artifacts must remain under the evaluator root but outside the workspace. Pass the same child to scorer `--workspace-root`; never place ledger or policy in the implementation checkout. In the handoff, mark every material claim `VERIFIED`, `OBSERVED`, `INFERRED`, or `UNVERIFIED`, plus its semantic `claim_type`. A self-issued score is never verification; subjective craft needs actual rendered review and benefits from an independent reviewer.

Keep acceptance independent from implementation. Freeze evaluator-owned tests and schemas before asking a weak model to edit the product. Prefer browser outcomes over source keywords; pair unavoidable static assertions with behavior checks, strip comments first, and include separately owned or undisclosed checks. Any attempt to edit the gate, insert test-only keywords, fabricate an artifact, or weaken an assertion is a failed evaluation even when the command exits zero. A failed check returns structured evidence to the repair loop automatically; it does not require the user to resubmit the request.

Preserve a usable preview after every attempt. Classify findings before acting:

- `REPAIR REQUIRED`: deterministic task, runtime, accessibility, content, or layout failure; fix automatically, run the narrow check, then the affected regression matrix.
- `MANUAL VISUAL`: rendered composition or craft judgment; repair automatically only when the evidence and intended direction are clear, otherwise retain it as an advisory note.
- `ADVISORY`: optional refinement; never interrupts delivery.
- `EVALUATOR DEFECT`: valid counterexample or faulty measurement; fix and test the evaluator before touching product code.

Withhold only the `verified` claim while a repair-required finding remains. Do not hide, delete, or refuse to hand off the best working artifact. After three failed repairs of the same root cause, return the best artifact and screenshots as `PARTIALLY VERIFIED` with the exact unresolved evidence and next command. Use `BLOCKED` only for unavailable required infrastructure, missing authority, unsafe action, or unrecoverable build/runtime failure.

Deduplicate repeated violations by root component, rule, and fix while retaining affected-route/instance counts. A scanner's severity is input, not release priority: order by user impact, reachability, task criticality, frequency, and confidence. Mark false-positive review and manual follow-up explicitly. Live-DOM source mappings, selectors, accessibility trees, and framework debug metadata are useful pointers, not proof that the proposed source edit is correct.

For accessibility regression reports, distinguish `new`, `fixed`, `pre-existing`, and `unverified` findings against the same pinned tool/ruleset and evaluator-owned baseline. Never mutate Git branches or stashes merely to compute this diff; use a clean evaluator checkout, worktree, build artifact, or recorded baseline.

Source inspection can suggest risk. It cannot prove rendered layout, touch size, focus visibility, contrast over motion, or absence of overflow. Automated scans and sampled route matrices cannot establish WCAG conformance by themselves; assess every applicable A/AA criterion across complete pages, responsive variations, and complete processes.

When rendering is unavailable, route through [no-visual-first-pass.md](no-visual-first-pass.md). Browserless checks may release a low-risk artifact only with an explicit evidence ceiling; they cannot earn rendered-visual, browser, touch, assistive-technology, or formal-conformance acceptance. A structured high-risk no-visual result must be `blocked` or match an `accepted_by_evaluator` record in the evaluator-owned policy; builder-authored acceptance is invalid.

## 2. Three-pass review

### Pass 1 — comprehension and access

Verify:

- first focal point, content order, CTA clarity, and honest copy;
- an attention decision record for material salience: top task, first-understood region, cue, competing cues, state/viewport/locale, interruption risk and actual check; do not infer comprehension from fixation or saliency;
- heading hierarchy, landmarks, labels, alt text, and state announcements;
- keyboard operation, visible/unobscured focus, and overlay focus management;
- overlay state cleanup: background scroll lock, internal navigation close, Escape close, focus return, and expanded state synchronization;
- applicable text contrast (4.5:1 normal, 3:1 qualifying large), essential non-text contrast (3:1), 200% resize, and 400%/320 CSS px equivalent reflow;
- loading, empty, error, disabled, success, permission, and offline states as relevant.
- valid→success→invalid form recovery, including stale live-region text and native-validation paths that bypass `submit`;
- dynamic visible and accessible names/counts staying synchronized after interaction;

Fix failures and capture the same view again.

### Pass 2 — identity and craft

Apply [anti-ai-slop.md](anti-ai-slop.md) as an evidence-based convergence gate. Do not reward arbitrary weirdness, penalize familiar task-appropriate patterns, or let the implementing model certify its own taste.

Verify:

- concept is visible beyond the hero;
- type roles, line length, wrapping, optical alignment, and numeric treatment;
- spacing rhythm varies intentionally with content density;
- color obeys its declared semantic rule;
- supported appearances independently preserve semantic surface/text/border/action/status hierarchy; dark mode is not a mechanical inversion and a lone media-query token block is not accepted as complete behavior;
- imagery, icons, radii, borders, depth, and texture form one language;
- border roles, type axes, component state colors, light direction, shadows, transparency/effect budget, and motion physics agree with the declared material system;
- any in-scope signature feels authored rather than library-default; focused repairs preserve identity without inventing a new effect;
- motion timing has hierarchy and a meaningful reduced-motion equivalent;
- the page does not converge on generic card-grid SaaS output.
- explicit brand invariants are preserved; inferred rules and unknowns are not presented as official brand truth; a campaign overlay does not overwrite product-system safety or semantics;

Fix and compare in grayscale as well as color.

### Pass 3 — mobile and resilience

Verify:

- mobile transformation table is reflected in the rendered product;
- touch targets, thumb reach, safe areas, virtual keyboard, and landscape work;
- 320px, tablet, and wide screens have intentional compositions;
- long locales, Traditional Chinese, mixed scripts, and RTL claims survive;
- no accidental horizontal overflow or fixed-height clipping;
- no first-paint menu, dialog, or sheet left open unintentionally, and no fixed/sticky control covering the primary task or focused content;
- media crops and art direction work per viewport;
- continuous effects pause off-screen and reduced motion truly reduces motion;
- no console, hydration, broken asset, route, or network errors;
- performance stays within project budgets.

Run a final regression after fixes.

## 3. Risk-based viewport and state matrix

Build a compact matrix for the routes in scope. Use three layers instead of claiming every cell for every change:

1. **Smoke**: every changed route at one representative mobile and desktop viewport, primary task, console/network, keyboard path, and no unexpected overflow.
2. **Risk regression**: breakpoints, locales, states, browsers, input modes, rendering paths, and failure cases affected by the diff or product risk.
3. **Conformance/release**: the full declared support matrix and complete processes when making WCAG, browser-support, localization, performance, or public-release claims.

| Route/state | 320 | 390 | 768 | 1024 | 1440 | Keyboard | zh-Hant/long | Reduced motion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Primary route/default |  |  |  |  |  |  |  |  |
| Navigation open |  |  |  |  |  |  |  |  |
| Loading/empty/error |  |  |  |  |  |  |  |  |
| Key workflow complete |  |  |  |  |  |  |  |  |

Adapt rows to the product. Record why a row/cell is applicable, sampled, or excluded. Never test only the happy homepage, and never turn a sampled matrix into an all-routes or formal-conformance claim.

## 4. Independent scorecard

Only an evaluator independent from the implementation may calculate an acceptance score, and only after evidence collection. The implementation model may use the dimensions as a review prompt, but cannot total its own work, set missing evidence to full credit, or declare the threshold passed. If no independent evaluator is available, report the score as `UNVERIFIED` and use the Boolean internal completion gates.

| Dimension | Weight | Passing evidence |
| --- | ---: | --- |
| Concept and coherence | 15 | One thesis governs type, color, composition, imagery, and motion |
| Visual design and typography | 20 | Clear hierarchy, crafted rhythm, robust type and color system |
| Usability and content | 15 | Top tasks and reading order work across states |
| Mobile experience | 15 | Distinct composition and input model; no shrink-and-stack shortcut |
| Originality and authored distinction | 10 | Product-specific identity proportional to scope; no forced effect in focused repair |
| Accessibility | 10 | Automated/manual evidence; separate all-applicable-A/AA gate when conformance is required |
| Localization | 5 | `zh-Hant`, expansion, mixed script, and claimed RTL behavior checked |
| Performance and resilience | 5 | Core Web Vitals targets, failure states, progressive enhancement |
| Code quality | 5 | Existing conventions preserved; build/tests pass; diff is focused |

Do not ship a universal numeric threshold with the skill. A project or controlled benchmark may freeze its own evaluator-owned calibration target before implementation, but the implementing model cannot choose it, change it, or fill missing evidence with points. Record rubric version, evaluator, artifacts, uncertainty, reviewer disagreement, and release blockers; compare models only under the same brief and evidence. A score is not a WCAG conformance result, award prediction, or external certification. When WCAG 2.2 AA is required, every applicable A and AA criterion must separately pass; no weighted score can offset a failure.

For accessibility, define the evidence matrix separately: automated rules; keyboard and zoom; Chromium accessibility-tree checks where available; and named screen-reader/browser combinations for the product's declared support. An AX tree is not VoiceOver, NVDA, JAWS, TalkBack, or Narrator evidence. Do not claim assistive-technology support that was not actually operated.

For performance, freeze project-specific budgets before implementation: route/asset JavaScript and CSS, image/font/media weight, main-thread/animation behavior, and applicable Core Web Vitals or lab diagnostics. A default budget copied from another product is a hypothesis, not a release fact.

This is an independent internal quality model spanning design, usability, creativity, content, responsive implementation, accessibility, semantics, animation, and performance. It is not mapped to Awwwards scoring or any other award system.

## 5. Internal completion gates

Do not call the work verified with any of these. Route each reachable, in-scope item back through automatic repair; these items do not by themselves justify a user-facing rejection:

- core route, build, lint, type, or test failure introduced by the change;
- inaccessible primary action or keyboard trap;
- any applicable WCAG 2.2 A/AA failure when AA is required, including contrast below the exact applicable threshold, missing labels, or essential content hidden behind motion/JavaScript;
- accidental horizontal scroll or clipped core content at a required viewport;
- unintentionally wrapped or clipped short action labels, or hidden responsive DOM copies that duplicate IDs, state, focus targets, or evaluator identities;
- forced `<br>` or source-newline composition in ordinary body/list copy; prose disabled from normal wrapping; or a narrow paragraph cap that leaves most of an otherwise empty wide content surface unused;
- global `break-all`, `line-break: anywhere`, `keep-all`, generated `<wbr>`, per-character spacer markup, or DOM text rewriting used to fake CJK alignment; emergency breaking must be scoped to verified unbroken data and preserve copy/search/selection;
- a paragraph region that accidentally combines incompatible UI, web-editorial, book-like, or fixed-display spacing/indent/wrapping rules; or centered display punctuation/anti-orphan `nowrap` that breaks another width, locale, zoom level, or fallback font;
- mobile navigation, primary content, focused control, or form blocked by fixed/sticky UI or the virtual keyboard;
- a brief-required exact locale, route, filename, visible content equivalent, semantic hook, or evaluator hook changed or missing at any required viewport;
- modal/menu background scrolling, stale open state after navigation, lost focus on close, or contradictory form success/error announcements;
- unintentional Simplified Chinese in product-owned `zh-Hant` UI copy or assets; preserve legitimate quotations, names, source data, and user content, marking `zh-Hans` parts when needed;
- required ruby/Bopomofo whose base/annotation semantics, source code points, tone sequence, custom-font fallback, solid annotation tracking, line breaking, or declared browser placement is broken; `ruby-position: inter-character` without tested engine evidence is not a cross-browser pass;
- broken asset, severe layout shift, uncaught runtime error, or hydration failure;
- signature effect that ignores reduced motion or consumes unbounded resources;
- fabricated verification results, fake user data, or unlicensed assets.
- evaluator-facing rationale in customer copy, or illustrative gradients/empty boxes presented as factual product evidence.
- hidden or delayed material terms, forced continuity, disguised advertising, confirmshaming, obstruction, trick questions, preselected consent, or materially asymmetric accept/reject and subscribe/cancel paths;
- claims that attention, saliency, heatmaps, clicks, observational attribution, model preference, or self-score prove understanding, trust, incremental conversion, brand fidelity, award quality, or user wellbeing.
- misleading or contradictory canonical/hreflang/robots/structured data; generated search spam; or claims that a validator, `llms.txt`, special AI markup, content chunking, SEO/AEO/GEO tactic, or crawler access guarantees indexing, rank, rich results, answer inclusion or citation.

If tooling or access prevents a check, preserve the best artifact and report it as partially verified with the exact remaining risk and executable follow-up.
