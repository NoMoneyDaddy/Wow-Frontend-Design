# Quality gates and self-repair

Use this reference to verify and automatically repair a frontend before calling it verified. These gates steer the implementation loop; they are not a rejection UI for the user. Award-level intent does not excuse fragile implementation.

## Contents

1. Required evidence
2. Three-pass review
3. Viewport and state matrix
4. Layered quality decision
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

An evaluator may depend on exact hooks only when the brief or integration contract names them. Do not hardcode unannounced IDs, value casing, wrapper structure, slots, or state attributes. Drive semantic inputs and judge observable task outcomes; when deterministic automation truly needs another hook, add it to the public brief and regression-test the contract before the next frozen cohort.

Preserve a usable preview after every attempt. Classify findings before acting:

- `REPAIR REQUIRED`: deterministic task, runtime, accessibility, content, or layout failure; fix automatically, run the narrow check, then the affected regression matrix.
- `MANUAL VISUAL`: rendered composition or craft judgment; repair automatically only when the evidence and intended direction are clear, otherwise retain it as an advisory note.
- `ADVISORY`: bounded or unproven risk, or optional refinement; disclose it without calling it a pass. It never blocks artifact delivery but may limit the affected claim.
- `EVIDENCE UNAVAILABLE`: the subcheck could not stabilize or record provenance; preserve the report and mark only the affected claim `UNVERIFIED`. Never abort the cohort or upgrade unavailable evidence to a pass.
- `EVALUATOR DEFECT`: valid counterexample or faulty measurement; preserve the counterexample and fix, freeze, and test the evaluator before touching product code.

Evidence-only visual issues remain page-result scoped: bind each to route/page, state, viewport, screenshot, and bounded error provenance. Never move one into a cross-page comparison record or infer a gap without its source record.

Withhold only the `verified` claim while a repair-required finding remains. Do not hide, delete, or refuse to hand off the latest contract-valid artifact. Preserve exact `DESIGN.md` linter messages and case identity in evaluator-owned evidence before visual capture. Across an isolated repair boundary, pass only bounded rule/category IDs and counts; never copy raw brief text, URLs, selectors, console text, or private paths into a model prompt. The user never relays diagnostics or restarts the Skill between attempts. Stop after three total attempts, or earlier when the declared same-key fuse is reached. A normal workflow returns the retained artifact, screenshots, and logs as `PARTIALLY VERIFIED`; a controlled release runner instead keeps its publish target empty and quarantines that artifact with the exact unresolved evidence. Use `BLOCKED` only for unavailable required infrastructure, missing authority, unsafe action, or unrecoverable build/runtime failure.

Deduplicate repeated violations by root component, rule, and fix while retaining affected-route/instance counts. A scanner's severity is input, not release priority: order by user impact, reachability, task criticality, frequency, and confidence. Mark false-positive review and manual follow-up explicitly. Live-DOM source mappings, selectors, accessibility trees, and framework debug metadata are useful pointers, not proof that the proposed source edit is correct.

When known, include the exact source file in the repair packet together with route, state, viewport, evidence, screenshot, and bounded error provenance.

For accessibility regression reports, distinguish `new`, `fixed`, `pre-existing`, and `unverified` findings against the same pinned tool/ruleset and evaluator-owned baseline. Never mutate Git branches or stashes merely to compute this diff; use a clean evaluator checkout, worktree, build artifact, or recorded baseline.

Source inspection can suggest risk. It cannot prove rendered layout, touch size, focus visibility, contrast over motion, or absence of overflow. Automated scans and sampled route matrices cannot establish WCAG conformance by themselves; assess every applicable A/AA criterion across complete pages, responsive variations, and complete processes.

Before rendered verification, run the dependency-free source layout risk audit when the project contains supported HTML/template/style files:

    python3 <skill-dir>/scripts/source_layout_audit.py <project-root> --authorized-root <workspace-root>

Use its file/line evidence to inspect forced body breaks, globally destructive CJK breaking, prose wrapping disabled in CSS, Latin-`ch` heading measures, and fixed-height text clipping. Medium findings are review candidates. High findings may enter automatic repair only after checking selector scope and intended role. Always confirm the result with computed browser geometry and matched screenshots; source text alone cannot prove a rendered defect or a successful repair.

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
- CJK display headings use script-aware measures, preserve compact lexical units, and do not depend on Latin `ch`, one browser's `auto-phrase`, or an unverified `nowrap` patch;
- wide headers/cards have no underfilled title or intro track, displaced right-column intro, or balanced short lines hiding a large unused region without a task-bearing peer;
- Traditional Chinese interface chrome and dynamic states are Chinese-first; preserved English terms are proper names/codes or appear after a Chinese term in first-use parentheses;
- spacing rhythm varies intentionally with content density;
- color obeys its declared semantic rule;
- supported appearances independently preserve semantic surface/text/border/action/status hierarchy; dark mode is not a mechanical inversion and a lone media-query token block is not accepted as complete behavior;
- imagery, icons, radii, borders, depth, and texture form one language;
- each large visual or dedicated track has a named information/task role and provenance; decorative/`aria-hidden` regions do not displace the primary task or create a narrow text rail;
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

Do not impose one screenshot quota on every user project. During an automatic repair, first recapture the failed route/state at one representative desktop and one true mobile browser profile. When that narrow result passes, run the affected breakpoints, states, locales, engines, and routes selected by the diff and declared support. A broad refactor expands the affected matrix because shared tokens, primitives, routing, state ownership, or layout foundations have greater blast radius. A release or formal support claim still requires the complete declared matrix.

### Bounded discovery artifact

For a completion claim, bind `novel-discovery` to an evaluator-owned JSON report with schema `1`, not a successful command or arbitrary file. It contains a non-empty `probes` array and a `findings` array. Each probe records `id`, route, viewport, state, method, outcome (`pass`, `candidate`, or `blocked`), and non-empty evidence. Each finding records its `novel:<surface>:<state>:<symptom>` ID, severity, reproduction, expected and actual result, owner, and confirmation evidence. `clean_after_probes` has no findings; `findings` has at least one. A finding is confirmed only when `confirmation.replays >= 2`; otherwise it remains advisory. Empty, command-only, blocked, or unconfirmed evidence cannot support `VERIFIED`.

The packaged Playwright evaluator freezes its plan to the first declared route, desktop and mobile profiles, and two fresh replays per profile. It checks every reachable focusable control in each replay and accepts only measurable non-color focus geometry. A blocked probe is evaluator/infrastructure advisory, not a product repair finding. Disclose discovery advisories and keep acceptance out of a clean pass; only confirmed findings enter product repair.

## 4. Layered quality decision

Do not collapse validity, product quality, award comparison, and Skill efficiency into one score. They answer different questions and must remain separate.

### A. Run validity and infrastructure

First establish that the requested model, frozen Skill/evaluator, artifact hashes, attempt history, and evidence chain are valid. Infrastructure failure is neither a product pass nor a product failure. An invalid run cannot enter release comparison.

### B. Required completion gates

Record every required, applicable gate as `PASS`, `FAIL`, or `UNVERIFIED`; use `NOT_APPLICABLE` only with a reason. Any required applicable `FAIL` or `UNVERIFIED` means:

```text
eligible = false
weighted_total = null
release != VERIFIED
```

This rule is machine-enforced when a structured result is requested. Completion validation must pass `validate_quality_result.py` with the evaluator-owned `--ledger` and frozen `--policy`, its model-writable `--workspace-root`, and any additional evaluator-required `--require-gate` values; `--structure-only` checks shape and cannot validate a release. Ledgers are append-only repair histories: the latest event for a repeated label or artifact path is authoritative, and one label reused across command and artifact kinds is ambiguous. The policy must bind each positive reference to the exact scoped claim type and exact command, cwd, and command hash or to a current hashed artifact. `VERIFIED` automatically requires a passing required/applicable `novel-discovery` gate, evaluator-recorded release acceptance, and `OBSERVED` rendered evidence; rendered paths must use the approved policy artifact path, not a label alias. A high craft judgment can never compensate for a broken primary task, inaccessible action, data/safety failure, missing required evidence, or invalid run.

For a machine-readable handoff, start from [quality_result.example.json](../scripts/quality_result.example.json) and run:

```bash
python3 <skill-dir>/scripts/validate_quality_result.py <result.json> \
  --ledger <evaluator-root>/ledger.json \
  --policy <evaluator-root>/policy.json \
  --workspace-root <evaluator-root>/workspace \
  --require-gate novel-discovery
```

Use more `--require-gate` values for evaluator-specific gates. Required applicable `FAIL` or `UNVERIFIED`, a missing discovery gate, implementation-owned ledger/policy, unapproved command, unbound evidence, or a rendered label alias makes the result ineligible and prevents `VERIFIED`.

### C. Independent core craft vector

Only a reviewer independent from the implementation may judge craft, and only from the frozen brief plus matched evidence. Report dimensions independently; do not total them by default.

| Dimension | Review evidence |
| --- | --- |
| Concept and coherence | One thesis governs type, color, composition, imagery, and motion |
| Visual design and typography | Clear hierarchy, crafted rhythm, robust type and color system |
| Usability and content | Top tasks and reading order work across states |
| Mobile experience | Distinct composition and input model; no shrink-and-stack shortcut |
| Originality and authored distinction | Product-specific identity proportional to scope; no forced effect in focused repair |
| Accessibility | Automated/manual evidence; separate all-applicable-A/AA gate when conformance is required |
| Localization | `zh-Hant`, expansion, mixed script, and claimed RTL behavior checked |
| Performance and resilience | Frozen project budgets, failure states, progressive enhancement |
| Code quality | Existing conventions preserved; build/tests pass; diff is focused |

Use `UNVERIFIED`, `CONCERN`, `ACCEPTABLE`, or `STRONG` with evidence and uncertainty. If a controlled benchmark needs numeric anchors, freeze the rubric, weights, missing-evidence policy, reviewer aggregation, and threshold outside the implementation context before the run. Do not expose held-out prompts, selectors, exact benchmark failure catalogues, weights, or release thresholds to the builder. A numeric result remains evaluator-specific and must be `null` whenever layer A or B is ineligible.

`VERIFIED` has a non-numeric core craft floor: `concept-coherence`, `visual-typography`, and `originality` must each be `ACCEPTABLE` or `STRONG` from a named independent reviewer with evaluator-bound evidence. The evaluator-owned policy must attest the reviewer ID, rubric version, exact status, evidence references, and uncertainty for all three; a model-writable result cannot promote its own verdict. `ACCEPTABLE` is scope-proportional: a focused repair may preserve an existing identity or deliberately add no effect, but it cannot leave concept fit, rendered hierarchy/type, or product-specific authorship `CONCERN` or `UNVERIFIED`. Keep the release `PARTIALLY_VERIFIED` until those three dimensions receive the required evaluator verdict; use `BLOCKED` only for the separately defined authority, infrastructure, safety, or unrecoverable-runtime conditions. Other craft dimensions remain risk- and scope-routed through their applicable hard gates; this floor cannot compensate for any failed, missing, or ineligible hard gate.

### D. Optional award-program lens

When the user explicitly requests award-quality, immersive, cinematic, portfolio, campaign, FWA, CSSDA, CSS Winner, or Awwwards comparison, additionally apply [award-quality-lens.md](award-quality-lens.md) after layers A–C. Keep one selected program's published dimensions in a separate view. Award-lens observations can trigger repair when evidence is clear, but cannot certify an award, predict selection, or compensate for a core gate failure.

### E. Maintainer efficiency and Skill optimization

Context bytes/tokens, selected reference count, first usable artifact latency, wall time, retries, repairs, tool installs, test runtime, flake rate, evidence coverage, recurrence, and user-relay count are maintainer metrics. They may break ties only after safety, data integrity, required gates, evidence coverage, and independent craft are non-inferior. They are not product-quality points.

Record rubric version, evaluator, artifacts, uncertainty, reviewer disagreement, and release blockers; compare models only under the same brief and evidence. A review is not a WCAG conformance result, award prediction, or external certification. When WCAG 2.2 AA is required, every applicable A and AA criterion must separately pass.

For accessibility, define the evidence matrix separately: automated rules; keyboard and zoom; Chromium accessibility-tree checks where available; and named screen-reader/browser combinations for the product's declared support. An AX tree is not VoiceOver, NVDA, JAWS, TalkBack, or Narrator evidence. Do not claim assistive-technology support that was not actually operated.

For performance, freeze project-specific budgets before implementation: route/asset JavaScript and CSS, image/font/media weight, main-thread/animation behavior, and applicable Core Web Vitals or lab diagnostics. A default budget copied from another product is a hypothesis, not a release fact.

The core craft vector spans design, usability, creativity, content, responsive implementation, accessibility, semantics, animation, and performance. It is not mapped to Awwwards scoring or any other award system.

## 5. Internal completion gates

Do not call the work verified with any of these. Route each reachable, in-scope item back through automatic repair; these items do not by themselves justify a user-facing rejection:

- core route, build, lint, type, or test failure introduced by the change;
- inaccessible primary action or keyboard trap;
- any applicable WCAG 2.2 A/AA failure when AA is required, including contrast below the exact applicable threshold, missing labels, or essential content hidden behind motion/JavaScript;
- accidental horizontal scroll or clipped core content at a required viewport;
- unintentionally wrapped or clipped short action labels, or hidden responsive DOM copies that duplicate IDs, state, focus targets, or evaluator identities;
- forced `<br>` or source-newline composition in ordinary body/list copy; prose disabled from normal wrapping; or a narrow paragraph cap that leaves most of an otherwise empty wide content surface unused;
- a Traditional Chinese display heading hard-capped with Latin `ch`, compressed into four or more lines while usable inline space remains, ending in an accidental one-character line, or patched with a non-breaking phrase that overflows another required width/locale/zoom/font;
- secondary badges, metadata, or controls taking a heading's primary inline track and causing an avoidable orphan fragment; recompose the region before shrinking the title;
- a later major header/grid child rendered above an earlier DOM sibling without an intentional accessible reorder, or a large decorative peer track that displaces the primary task without a named role;
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
