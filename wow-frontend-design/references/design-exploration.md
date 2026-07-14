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

Render each variant with the same:

- mobile and desktop viewports plus the breakpoint where its composition changes;
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

Implement through the real design system and production route only after selection. Re-run the normal release gates; a working lab is not evidence that production integration works.

## 6. Weak-model controls

- Give one variant contract and writable surface at a time.
- Keep fixtures and evaluator assertions outside its writable path.
- Require an output manifest; reject extra routes, dependencies, files, analytics, or external assets.
- Do not reveal a hidden visual rubric as testable keywords.
- Blind screenshots by variant id and model provenance before subjective review.
- Treat cleanup, output-count, schema, build, and browser failures separately from taste.
