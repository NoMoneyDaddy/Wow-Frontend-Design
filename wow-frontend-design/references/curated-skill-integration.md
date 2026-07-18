# Curated external Skill integration

Use external Skills as pinned, conditional research modules—not as a merged rule pile. The active project, user request, current standards, installed framework/version, and verified runtime behavior remain authoritative.

## 1. Route before loading

Write one compact routing record:

```text
intent → detected stack/version → risk → missing capability → selected source/path/revision → adopted rule → rejected conflict → verification
```

- Load the smallest source that fills a named gap. Do not load every design, taste, framework, audit, and media Skill into one model context.
- In a constrained or single-model run, prefer this Skill plus at most one domain adapter at a time. Finish the current checkpoint before replacing it with another adapter.
- Treat stars, catalogue size, model confidence, self-scores, and repeated aliases as discovery signals only.
- Never let an external Skill expand mutation scope, install tooling, transmit project data, browse authenticated surfaces, submit forms, or change Git state without the user's authorization.

## 2. Freeze the source boundary

Before reusing a rule, record repository, full content-addressed commit, path, retrieval date, and license evidence in [external-sources.lock.json](external-sources.lock.json) or an evaluator-owned equivalent. If text/code is copied rather than independently paraphrased, also retain the exact file hash and required notice.

- Never fetch mutable `main`, `@latest`, floating actions, CDN scripts, or reusable workflows during an ordinary project run.
- Prefer installed package types/docs and the project's lockfile for framework behavior. A pinned research Skill does not override the installed version.
- Re-audit when the pinned commit disappears, the content hash changes, the license changes, or the source redirects.
- A repository without a complete applicable license may be studied and paraphrased as facts or methodology; do not copy its expressive text or code into this MIT project.
- Keep third-party notices when copied MIT/Apache-2.0 material requires them. A framework license does not automatically license icon collections, fonts, templates, generated assets, editors, or export runtimes.

## 3. Conditional routing matrix

| Need | Useful source family | Adopt conditionally | Reject as universal |
| --- | --- | --- | --- |
| Optional visual style | Swiss Design, Taste, Impeccable | vocabulary, coherent grammar, focused refinement pass | mandatory grids, fonts, palettes, bans, durations, or “anti-slop” taste |
| Brief-to-direction reading | Taste skill | before choosing visual language, write one compact design read from page kind, audience, vibe, references, existing assets, and quiet constraints; let the brief and accessibility/trust constraints outrank personal taste | fixed variance/motion/density dials, one mandatory aesthetic, or asking for a preference when the brief already resolves it |
| Design exploration | 0x Design Lab, designer-skills | isolated variants, shared fixtures, structured regional feedback | fixed variant count, generic long interview, broad cleanup |
| Optional decision playground | Anthropic Playground | only an explicit playground request or one material unresolved visual/structural choice; one self-contained explorer with live preview and actionable prompt output | default activation, broad control panels, `open .html`, copied prompts as implementation or verification evidence |
| Aesthetic attention and audit | Anthropic aesthetics cookbook, Interface Design | prompt or inspect only the missing dimension; name domain, hierarchy, defaults, and one signature quality; use swap, squint, signature, and token checks as diagnostics | copy-pasted prompt blocks, blanket font/palette/motion bans, visual difference as quality proof, or a mandatory direction pause for a clear brief |
| Product planning and handoff | Design OS | separate outcome, data vocabulary, tokens, shell, section contract, and screen; keep component props/callbacks explicit; use varied realistic fixtures and bounded handoffs | mandatory ceremony for a clear brief, fixed React/Tailwind/palette/font/count recipes, or generated test specs/screenshots as executed evidence |
| Product discovery and usability | goodux skill subtree | non-leading interviews, no invented personas/quotes, IA validation, observation/inference separation | fixed sample/persona counts, five-stage ceremony, industry style lookup, fixed stack, destructive installer |
| UI engineering | Addy Osmani frontend UI | state ownership, complete states, composition, rollback | React/Tailwind assumptions and arbitrary size/depth thresholds |
| Design-tool workflow method | Figma MCP guide, Augment Figma workflow | inspect the exact target first; use precondition → bounded mutation → affected-item receipt → immediate structural/rendered check; existing components/tokens before external search; outer structure before incremental sections; one writer per mutable surface | requiring Figma/MCP for web delivery, treating a design export as production evidence, fixed operation counts/rate limits, a frame as sole product truth, or parallel writers on shared state |
| Evidence-backed design system | Open Design | bind normalized token roles to source references and confidence; report exact/alias/fallback coverage; validate declared references and resolved runtime values; treat fallback debt as a repair signal | importing its catalogues, fixed palettes or nine-section ceremony, installing its desktop/MCP runtime, or claiming brand fidelity from a generated `DESIGN.md` alone |
| Critique protocol | Open Design | version the result protocol; persist findings and degraded/failure state; require zero open must-fix items in addition to positive gates; keep below-threshold output clearly incomplete | role-play consensus, self-scored composites as acceptance, transcript volume as rigor, or `ship_best` below threshold as completion |
| Quality audit | Addy web quality, AccessLint, GitHub reviewer, Vercel guidelines, Nu HTML Checker | exact tool provenance, live DOM, before/after, root-cause dedupe; optionally run the pinned Nu checker for HTML/CSS/SVG conformance with Java 11+ already installed and `npm ci --ignore-scripts` | automation as conformance, mutable runtime fetch, runtime/JDK auto-download, stash/checkout mutation, overflow hiding; use W3C CSS Validator only as a second opinion and WPT/wpt.fyi only for a named browser-interoperability question rather than installing either suite |
| Framework adapter | Nuxt, Pinia, pnpm, UnoCSS, Slidev | only after exact installed version and conventions are detected | personal Antfu conventions as project law; cross-version syntax guesses |
| Platform component adapter | official Material Web implementation | existing `@material/web` version, real component API, semantic token mapping, focus/forced-color tests | installing Material only for style, copying `main` tokens, treating maintenance-mode APIs as universal |
| Candidate catalogue | UI Skills, UI UX Pro Max | retrieve candidates, then verify primary source/license/standard | stereotype lookup, false precision, duplicate aliases as consensus |
| Design distillation | frontend-distill | when a reference or existing page must be reverse-engineered, use deterministic Playwright extraction to produce a bounded raw bundle, `DESIGN.md`/`LAYOUT.md`, and design/layout tokens; label extracted facts versus inference and verify against the live target | treating extracted pixels or generated documents as product truth, scraping authenticated/external data, or using extraction instead of implementation evidence |
| Decision traceability | design-harness | link each visual/system decision to its source, constraint, experiment, and acceptance evidence; keep the decision record small enough to review and resume | copying its canvas/publish runtime, treating a diagram as a rendered proof, or inventing a source for an aesthetic choice |
| Component design contract | ui-design-brain, Material 3 references | for a named component, record purpose, semantic primitive, variants, states, keyboard/focus, responsive behavior, async/error/retry behavior, and anti-patterns; map only applicable token roles | importing a full catalogue, assuming Compose/Flutter APIs are Web APIs, or applying a component preset without a product job |
| Rendered visual audit | frontend-audit-skill, design-visual-frontend | compare the same route/state/viewport against pinned render evidence; include multi-viewport, focus/touch/reduced-motion states and browser provenance, then route root-cause findings into the repair loop | accepting a screenshot diff without DOM/interaction evidence, unpinned engines/fonts/data, or declaring visual quality from a single viewport |
| Visual thesis and material grammar | skeuos-gtk, cinematic-ui, PPVI | borrow an explicit material/lighting/composition thesis only when the brief earns it; document the job, responsive fallback, reduced-motion path, and one representative proof | copying a desktop theme, glass/film effects, fixed palettes, or aesthetic novelty as a universal quality gate |
| Text measurement and wrap prediction | chenglou/pretext | when typography or content volume makes character-count heuristics uncertain, optionally measure exact font/width/line-height/letter-spacing candidates with `prepare`, `layout`, `measureLineStats`, and line-range APIs; use results to target Playwright fixtures and diagnose wrap changes | adding a mandatory runtime dependency, treating canvas measurement as full CSS layout or browser acceptance, trusting stale/fallback fonts, or using it without matching `white-space`/`word-break`/`letter-spacing` |
| Browser diagnostics | browser-debugger-cli | borrow progressive command discovery, structured telemetry, semantic failures, bounded queries, and token-efficient evidence shaping for the existing Playwright audit output | direct CDP as the browser-control path, disabling web security, persistent browser sessions without lifecycle receipts, or installing a second browser automation stack |
| Code debugging workflow | debug-skill | borrow breakpoint → inspect context → step → re-run → preserve failure context for JS/TS runtime debugging when a concrete code path is ambiguous; keep logs and state bounded | installing `dap`, Go/debug adapters, or a debugger for visual acceptance; replacing Playwright interaction evidence with a source-level confidence claim |
| Skill registry or persona pack | sk1llz and similar manifests | machine-readable categories, tags, compact routing, contribution checks | persona imitation as authority, catalogue-wide ingestion, mutable installers, hidden formatting bytes |
| Role pack and workflow orchestrator | agency-agents-zh and agency-orchestrator | explicit role input/responsibility/output, dependency-aware sequencing, bounded parallel work, step acceptance, retry/resume records | persona prose as expertise, invented memory/research, fixed stacks/breakpoints/scores, mandatory multi-agent runtime, or external orchestrator installation |
| Motion/Lottie | LottieFiles, Diffusion Studio | intent vocabulary, thin authoring route, semantic frames, loop seam | fixed personality recipes, mandatory ambient layers, player-specific behavior as portable |
| SVG/icon assets | jezweb icon/favicons | inventory, style spec, optical-size render sheet | unsanitized AI SVG, automatic remote upload, universal `<title>` insertion |
| Three.js/media | CloudAI-X recipes | subsystem discovery after version detection | copying stale API examples, unbounded loops, UA routing, incomplete teardown |
| Layered product reasoning | layers-skills | move from user need → product strategy → interaction flow → surface implementation, and preserve the links between layers in the decision record; use observed behaviour to challenge assumptions | treating layers as a mandatory ceremony, inventing research, or allowing surface polish to override task/permission/state contracts |
| Design exploration workspace | SuperDesign | use only as an optional local ideation surface: fork bounded variants, keep source/decision/selected-result receipts, and return to the implementation plus Playwright evidence loop | installing its extension, using an infinite canvas as acceptance evidence, copying prompts/mockups into production, or assuming the unmaintained IDE repository is current |

Named sources are research coordinates, not installed dependencies or endorsements. See [github-skill-research.md](github-skill-research.md) and [ui-skills-ecosystem.md](ui-skills-ecosystem.md) for the critical review.

### Optional playground boundary

Keep the playground off in `DIRECT`. In `CHECKPOINT-GUIDED`, enable it only when the user explicitly requests an explorer or one unresolved visual/structural decision would materially change the implementation. Limit it to that decision surface, three to five cohesive presets, at most three review cycles, and two or three representative screenshots per cycle. Do not install the upstream plugin or copy its browser-launch command during an ordinary run.

Serve the single-file artifact from the authorized workspace and exercise its controls, presets, live preview, prompt output, keyboard path, responsive behavior, console/page errors, and copy feedback only with the project-pinned Playwright runtime. The selected result becomes a bounded design input, then the workflow returns to `DIRECT`. A working playground proves only the explorer; it cannot satisfy production routes, states, accessibility, performance, or completion gates, and it never replaces Playwright verification of the implemented frontend.

### Distill → decide → implement → audit

Use this four-boundary loop when an external reference, screenshot, or existing frontend is the design input:

1. **Distill:** collect only authorized route/state/viewport evidence with the pinned Playwright runtime. Emit facts, measurements, tokens, and unresolved observations; never emit a copied product identity.
2. **Decide:** record the smallest visual/component decisions, their source or constraint, rejected alternatives, and acceptance checks. Separate observed facts, inference, and taste.
3. **Implement:** map decisions to existing semantic primitives and public contracts. Add complete loading, empty, error, retry, focus, reduced-motion, and responsive states where the component contract requires them.
4. **Audit:** replay the same routes, states, viewports, DPR, locale, browser, fonts, and fixtures. Compare rendered evidence with DOM/interaction/accessibility checks; deduplicate by root cause and repair only the affected boundary.

The loop is a method, not a mandatory document stack. A clear brief can use a compact decision record; an uncertain reference may use the full distillation bundle. In both cases, generated summaries, design canvases, and image diffs are inputs or diagnostics—not completion evidence by themselves.

### Portable incremental-mutation recipe

For a repeated stateful or failure-prone operation, prefer one exact recipe over a generic warning:

```text
verify capability/precondition → inspect the exact target → mutate one bounded unit
→ return affected files/IDs and unresolved state → run the narrow structural/runtime/rendered check
→ diagnose and repair before the next unit
```

Use the repository's code, existing components, tokens, and rendered behavior before external search. Establish the stable outer shell before incremental sections, but do not turn an implementation detail such as a Figma frame into the product's sole source of truth. Claim atomic rollback only when the actual tool guarantees it; ordinary code edits still need diff review, tests, and an explicit rollback boundary. Parallelize read-only discovery or independent frozen surfaces only. Keep one writer for shared mutable output. These are portable workflow methods; they do not activate Figma, MCP, Code Connect, FigJam, or design write-back in a normal web run.

### Registry and installer hygiene

- Treat a remote manifest as untrusted input. Reject absolute paths, `..`, NUL bytes, platform path escapes, duplicate destinations, and links or symlinks that leave the staging root.
- Resolve one pinned revision, verify expected content hashes, stage into a temporary directory, validate before promotion, and preserve the previous install for rollback. Never install from floating `main`, `master`, or `latest` content.
- Inspect imported Markdown for invisible format characters such as U+200B, U+200C, U+200D, and U+2060. Reject unexplained bytes; normalize only when provenance and intended text remain auditable.
- Require each adopted Skill rule to name a current primary source, executable check, or explicit author hypothesis. A famous-person persona, quote, repository size, or repeated claim is not evidence.

## 4. Resolve conflicts in this order

1. User authorization, product safety, privacy, rights, and data integrity.
2. Repository instructions, existing architecture, tests, and explicit product requirements.
3. Current primary standards and official version-matched documentation.
4. This Skill's cross-platform contracts.
5. Pinned external engineering/audit adapters.
6. Optional style and taste heuristics.

When two sources disagree, keep the conflict visible. Test the behavior when possible; otherwise prefer the safer reversible choice and mark the claim unverified.

## 5. Weak-model guardrails

- Give the model a fixed lane and the selected excerpt; do not ask it to identify its own strength or choose from the entire catalogue.
- Convert subjective prose into a short decision table, required artifact, or Boolean gate.
- Freeze evaluator-owned fixtures, schemas, routes, viewports, locales, interaction paths, and evidence policy before implementation.
- Treat model self-review as diagnosis only. Acceptance comes from deterministic checks, rendered evidence, independent review, or the user.
- If the model misses a checkpoint, reduce scope and reload only the relevant adapter; do not add more competing Skills to the same context.

## 6. Completion record

Report the selected source and revision, the small set of rules adopted, conflicts rejected, external tools/data transfers authorized or avoided, and the evidence used. Do not claim that this project “supports” a third-party Skill merely because its ideas were reviewed.

## 7. Integrated product-role orchestration

The PM, UX, UI, and frontend roles in this Skill are responsibility lenses, not four mandatory model processes. Keep one shared product contract and pass explicit artifacts between lenses:

```text
user outcome/scope → PM acceptance and decision record
→ UX task/content/state/mobile structure
→ UI visual system/component/state contract
→ frontend implementation and migration record
→ source/browser/screenshot evidence → PM handoff or repair loop
```

Every stage names its input, decision, output, acceptance check, unresolved risk, and downstream owner. A single capable agent may execute the whole chain. When the host offers subagents, parallelize only independent bounded work whose inputs are already frozen—for example source audit and external research, or separate route inspections. Do not parallelize decisions that write the same files, share unresolved design direction, or depend on a prior stage's output. The primary agent owns synthesis, mutation scope, evaluator integrity, retries, progress, and the final claim.

AUTOMATIC mode follows the dependency graph and selects only reversible defaults; CHECKPOINT-GUIDED mode pauses at material direction/refactor-depth/final-candidate decisions; USER-DIRECTED mode consumes the user's already frozen choices. Preserve step outputs so an interrupted host can resume from the last verified boundary instead of replaying the whole project. Retry recoverable tool/process failures with fresh bounded attempts; route deterministic product findings into the existing repair loop, and never use role agreement as acceptance evidence.

Reviewed sources: [agency-agents-zh](https://github.com/jnMetaCode/agency-agents-zh) for explicit role mission/workflow/deliverable structure and [agency-orchestrator](https://github.com/jnMetaCode/agency-orchestrator) for dependency graphs, acceptance fields, retries, persisted outputs, feedback, and resume. The complete design department plus the frontend and senior-developer roles are reference lenses, not always-on personas. Their fixed framework recipes, breakpoints, automatic theme mandates, numeric success claims, persona memory, conversion manipulation, and unexecuted accessibility/performance claims were not adopted.

Route frontend-adjacent role references by an evidenced need:

| Need | Responsibility lens | Required output/boundary |
| --- | --- | --- |
| Broad product framing | product manager / senior project manager | outcome, non-goals, scope, decisions, acceptance, rollback; no invented market/user metrics or compulsory ceremony |
| Information architecture or uncertain flow | UX architect | routes/tasks/content/states/mobile transformation and implementation handoff; no universal navigation counts, theme mandate, or fixed breakpoints |
| Actual research or usability study | UX researcher | method, participants, observations, uncertainty, findings; never generate participants, quotes, sessions, or “validated” claims |
| Pre-research perspective check | persona walkthrough | a clearly labeled simulated hypothesis using supplied audience/task/context evidence; never present inner monologue, emotion, trust, conversion, or cultural assumptions as observed users or statistical evidence |
| Visual system and components | UI designer | `DESIGN.md`, roles/tokens, component states, responsive rules, design QA; avoid fixed scales/palette recipes and pixel identity across engines |
| Existing brand or campaign | brand guardian / visual storyteller | explicit/observed/inferred brand evidence, narrative job, asset provenance; no fabricated brand strategy or decorative story track |
| People imagery and localization context | inclusive visuals / localization specialist | stereotype/representation review and locale-specific evidence; do not infer demographics or turn one market's convention into all Chinese locales |
| Authorized generated imagery | image-prompt engineer | intended use, subject, environment, composition, light, material, aspect ratio, negative constraints, rights/provenance, responsive crop and fallback; do not generate assets by default or imitate living artists/brands/real people without authorization |
| Optional brand delight | whimsy injector | one task-supporting microcopy, state, or interaction with brand fit, locale review, reduced-motion/static fallback, accessibility and performance checks; never obscure errors/actions, shame users, add addictive loops, or make every component playful |
| Broad retrofit or structural debt | software architect / code reviewer | change boundary, alternatives, incremental seams, public-contract parity, focused review; no framework migration or style-preference review by default |
| Frontend implementation or advanced visual subsystem | frontend developer / senior developer | detected-stack implementation, semantic structure, maintainable boundaries, complete states, progressive enhancement, teardown and measured browser/performance evidence; no mandatory Laravel, Livewire, FluxUI, Three.js, dark mode, glass, magnetic effects, 60 fps, or fixed load-time claims |
| Untrusted content, auth, payments, storage, embeds, telemetry | security engineer | assets/trust boundaries/threats/mitigations/residual risk; no offensive testing or scope expansion without authorization |
| Production runtime/reliability | SRE | actual SLO/incident/observability evidence when the product has that operational scope; no invented uptime, traffic, or chaos exercise |
| Documentation requested | technical writer | audience, runnable instructions, checked examples, maintenance owner; README remains explanation/display, not an internal evidence dump |
| Accessibility release scope | accessibility auditor | exact browser/AT/tool/manual matrix and criterion evidence; no AA or screen-reader support claim from prompts or automation alone |
| Performance-sensitive change | performance benchmarker | frozen baseline/scenario/environment, before/after distributions and bottleneck evidence; no Lighthouse score as universal product quality |
| Test and handoff integrity | evidence collector / test-results analyzer / reality checker | provenance, reproduction, coverage boundary, failure families and claim labels; independent evidence outranks role agreement or self-score |
| New tool/dependency decision | tool evaluator | requirement, version, runtime/license/security/size, alternative, pin and removal cost; never install a catalogue by popularity |
| Skill-maintainer optimization | workflow optimizer | measured bottleneck, target flow, trial, regression and rollback; keep separate from a user's live product repair loop |

These lenses may be executed by one agent. Load or delegate only the row needed for the current task, and keep evaluator/security authority with the primary workflow.
