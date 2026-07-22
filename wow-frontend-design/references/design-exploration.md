# Design exploration and temporary labs

Use this reference when the user needs materially different directions, an interactive design lab, component variants, or structured visual feedback. Exploration is a decision tool, not permission to duplicate the application or leave prototype routes behind.

## 1. Decide whether variants are useful

Use variants when a real choice remains about hierarchy, interaction model, density, art direction, or product voice. Do not generate a fixed number by habit.

- focused repair with clear evidence: implement one bounded direction;
- one important ambiguous axis: compare two directions;
- several coupled high-impact axes: normally compare two or three, adding another only when it tests a named unresolved hypothesis;
- an existing approved brand/design system: vary composition or behavior inside it, not the brand itself.

Every variant shares the same product facts, primary task, required states, locale stress strings, representative data, viewport/state matrix, and preserve invariants. Change named axes—not copy, facts, and fixtures simultaneously.

Write a variant manifest:

```text
variant id → hypothesis → changed axes → held-constant axes → expected benefit → risk → states/viewports → selection evidence
```

### Fast multi-direction draft pass

When the user requests multiple direction drafts to confirm style, or a named high-impact ambiguity would make a full build wasteful, run a fast multi-direction draft pass before production. Each draft is a coherent direction group, not a colorway or a single tile. Use the smallest decisive set: normally three groups for an explicit open style choice, two for a binary hypothesis, and a fourth only when it answers another named question.

Hold the product truth, task, real or representative content, data fixture, required behavior, brand invariants, and comparison conditions constant. Each group must express a different product hypothesis through several compatible changed axes—such as composition, typography, density, material, imagery, and motion character—not through palette or decoration alone. Require this minimum comparable slice from every group:

- the same representative route at a declared desktop profile;
- the mobile transformation of that route;
- one decision-critical state or interaction specimen;
- a terse rationale naming product evidence, changed and held axes, identity carrier, implementation risk, and what would disqualify it.

Build only to the fidelity needed to make the visual and interaction direction observable. Reuse deterministic content fixtures and existing preview infrastructure, but do not let a shared shell force the candidates into one composition. Do not build three production implementations, connect production services, complete every route, extract speculative shared abstractions, or polish expensive motion before selection. A draft may simplify data plumbing; it may not fake factual content, hide a required action, or become a screenshot-only facade.

When comparison conditions freeze a first-viewport contract, budget the vertical stack before styling: brand, value statement, required decision context, and primary action. Defer every non-required block below that action; do not let repeated summary cards displace it. Keep required safety, consent, or comparison evidence before the action when the decision depends on it.

Use fresh project-pinned Playwright captures under the same browser, fixture revision, locale, theme, viewport, and preference settings. Show individual captures at readable size and optionally assemble a labelled overview board for navigation; the overview does not replace the source captures. If rendering is unavailable, report that style confirmation is blocked rather than treating prose, code, or an old screenshot as visual proof.

Preserve the first faithful/current-state render as an immutable baseline. Every candidate records its parent and changed axes; never overwrite the baseline or let a mutable “latest” artifact become ancestry. A wireframe, canvas draft, or decision specimen helps compare a material ambiguity, but it is not implementation or acceptance evidence.

Define exclusion gates and decision criteria before revealing candidate identities. When specialist judgments are independent, collect them independently before discussion; a reviewer should score only dimensions supported by their evidence. Keep disagreement and unresolved criteria instead of manufacturing consensus.

## 2. Inspect before asking

Detect the project, current visual tokens, component patterns, framework/version, package manager, routes, and available preview/test surface first. Ask only questions whose answers change the exploration materially:

- target component/page/workflow and mutation scope;
- user/audience context and top task;
- explicit likes, dislikes, references, brand constraints, and must-preserve behavior;
- information density, device/input context, and accessibility/localization needs;
- which decision the variants should resolve.

Do not make the user answer a generic brand quiz when the repository or supplied reference already contains the evidence. Translate named brands into attributes and behaviors; never clone their assets or layout.

## 3. Isolate the lab safely

Prefer an existing Storybook, component preview, fixture route, test harness, or a disposable project outside production routing. When a temporary in-app route is genuinely needed:

- freeze an exact owned file manifest and unique temporary root before writing;
- keep production data, authentication, analytics, indexing, service workers, and destructive actions out of the lab;
- use local deterministic fixtures with explicit fictional/provenance labels;
- add no public navigation, sitemap, canonical, telemetry, or deployment exposure;
- preserve CSP, routing, SSR/hydration, and dependency conventions;
- prevent the lab from becoming a privileged bypass around authorization or feature flags.

Cleanup deletes only the exact owned manifest after confirming no unowned files changed. Never run a broad recursive delete based only on a conventional folder name. On cancel or failure, restore only the temporary integration edits and report anything that could not be removed. Retain a design decision record only when the user/project wants it.

## 4. Compare rendered behavior, not thumbnails alone

During the fast draft pass, render the shared minimum slice plus only the extra state, content extreme, or composition transition that could reverse the direction decision. Apply cheap exclusion checks for preserved content/actions, obvious overflow, unreadable contrast, unusable focus, and impossible mobile transformation. Run the full affected state and viewport matrix only for the selected direction.

With two or more rendered candidate directions in the same frozen comparison cohort, whether produced in one batch or isolated runs, route matched surface, viewport, and state observations through the optional `scripts/cross_output_template_audit.cjs` telemetry in [research-validation-loop.md](research-validation-loop.md). Treat its candidates as advisory prompts for product evidence and paired rendered review; never make a match a release blocker or a non-match proof of originality.

For the selected direction, render with the same frozen conditions and cover:

- the same declared representative viewport profiles plus affected composition transitions; when support is unknown, sample mobile and desktop conservatively without inventing a product contract;
- default, loading, empty, error, success, long-content, and relevant interaction states;
- keyboard/no-hover, reduced-motion, zoom/reflow, `zh-Hant`, expanded pseudo-locale, and claimed RTL context;
- browser/runtime and fixture revision.

Structured feedback attaches to a region and state:

```text
variant + route + viewport + state + region → keep/change/remove → reason → importance → confidence/open question
```

Do not collect only “A/B/C” votes. Record which hypothesis succeeded, which invariant failed, and whether feedback concerns content, hierarchy, identity, interaction, accessibility, or implementation cost.

## 5. Select and synthesize without reward hacking

The implementing model may summarize tradeoffs but cannot declare its own visual score authoritative. Use deterministic failures as exclusions, rendered evidence for observed craft, user preference for subjective fit, and specialist/human review for high-risk domains.

Choose one direction or an explicitly compatible synthesis. Do not combine every liked detail into a collage. Record:

```text
selected thesis → kept axes → rejected axes and why → invariants → implementation delta → verification plan
```

When the user requested style confirmation, present the fresh groups before production work and treat selection as the material direction checkpoint. If the user delegated selection, apply the predeclared product-fit and task criteria and record the reason instead of pausing. Freeze a selected style contract covering composition, typography, density, color roles, material, imagery, motion character, mobile transformation, preserved behaviors, and forbidden drift. Later production evidence must compare the selected implementation with this contract; do not reuse the draft captures as release evidence.

Implement through the real design system and production route only after selection. Re-run the normal release gates; a working lab is not evidence that production integration works.

## 6. Weak-model controls

- Give one variant contract and writable surface at a time.
- Keep fixtures and evaluator assertions outside its writable path.
- Require an output manifest; reject extra routes, dependencies, files, analytics, or external assets.
- Do not reveal a hidden visual rubric as testable keywords.
- Blind screenshots by variant id and model provenance before subjective review.
- Treat cleanup, output-count, schema, build, and browser failures separately from taste.
