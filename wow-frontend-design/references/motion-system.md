# Motion system

Use motion to explain change, preserve orientation, direct focus, or express one product-specific signature. Static comprehension comes first.

## Contents

1. Write the motion contract
2. Choose the smallest runtime
3. Build lifecycle and interruption
4. Provide a reduced-motion result
5. Protect mobile and scrolling
6. Handle SVG and asset runtimes
7. Verify behavior and performance
8. Source and license notes

## 1. Write the motion contract

For every material effect, record:

```text
effect → purpose → trigger → affected state/content → runtime → interrupt/cleanup → reduced result → evidence
```

Purpose must be one of:

- **feedback**: confirm an input or state change;
- **orientation**: explain where content came from or went;
- **focus**: direct attention without hiding other essential information;
- **continuity**: preserve object identity across layout or route changes;
- **signature**: express a product-specific noun or verb.

Delete effects that only mean “make it premium.” Define the complete static state before animating. Never hide essential copy or controls until JavaScript, a timeline, or an asset runtime finishes.

Create a small vocabulary rather than one duration everywhere:

- direct feedback: fast enough to feel connected to input;
- component state: long enough to explain causality without delaying reuse;
- navigation/continuity: bounded by comprehension and interruptible;
- ambient/signature: optional, sparse, pausable, and off-screen inactive.

Numbers are hypotheses. Verify them on the target product and input methods.

### Name the pattern before choosing the effect

Weak models often call every movement a “smooth transition,” then reach for the same fade-and-slide. Require a precise pattern:

| Pattern | Meaning | Common wrong substitution |
| --- | --- | --- |
| origin-aware enter/exit | an element appears from or returns toward its trigger | arbitrary slide from the viewport edge |
| shared-element continuity | the same object persists across states/routes | two unrelated elements crossfading |
| layout transition | surrounding geometry changes while identity stays stable | animating width/height continuously without measurement |
| path morph | one compatible vector topology interpolates into another | forcing unrelated SVG paths to distort |
| crossfade | identity or content changes without spatial travel | using a morph only because it looks advanced |
| scroll-triggered reveal | a one-time state starts after visibility threshold | binding every frame to scroll position |
| scroll-driven progress | progress intentionally follows scroll | a reveal observer pretending to be continuous progress |

Record frequency as `once | per navigation | per state change | per input | ambient`. The more often an effect repeats, the shorter, quieter, and easier to interrupt it should become. Remove repeated entrances from keyboard navigation and rapid operations when they delay the task; retain immediate focus and state feedback.

### Match wow to the product register

- campaign/editorial: one sensory signature may carry the thesis;
- product/app: feedback, continuity, speed, and state clarity create polish;
- data tool: legible change, stable comparison, and direct manipulation matter more than spectacle;
- utility/enterprise: fast recovery, predictable focus, and invisible performance may be the signature;
- playful/entertainment: expressive motion is valid when the audience, device budget, and reduced path support it.

Do not copy an award-site motion recipe into every product type. The signature must reinforce the product's noun, verb, or mental model.

### Compose a page narrative instead of repeating entrances

Treat the page as beats, not a list of elements waiting for the same fade-up. First write the static reading order and one sentence for each beat: `establish → reveal → explain → resolve/act`. Use density changes, stillness, typography, crop and whitespace before adding motion. A transition earns its place only when it explains the relationship between adjacent beats.

| Surface | Useful motion role | Candidate sequence | Default rejection |
| --- | --- | --- | --- |
| Creative-developer portfolio | authored identity and proof of craft | one signature hero sequence → selected-work reveal → case-study continuity | animating every heading, cursor replacement, or scroll smoothing as identity |
| AI intelligence dashboard | status, causality, comparison, continuity | shell appears immediately → real data/state settles → changed values or filters explain their effect | ambient loops, fake counting metrics, delayed task controls, or pinned work panels |
| Digital magazine | chapter orientation and editorial pacing | cover/lede establishes tone → section markers reveal once → optional reading progress | scrubbing body copy, splitting every CJK character, or interrupting normal reading |
| High-craft product site | product relationship and material change | hero establishes product → feature/state transforms in place → evidence and CTA resolve | spectacle without product evidence, mandatory preloader, or every section pinned |
| Scroll narrative | causal progress through a named story | native document establishes all beats → selected scene maps scroll progress to change → static conclusion | scroll hijacking, decorative parallax everywhere, or content available only inside a pin |

For a hero entrance, group by meaning rather than DOM order: shell/brand context → display phrase → supporting proposition/CTA → product proof. Keep the first usable frame meaningful; overlapping beats may create rhythm, but the CTA and heading must not wait on an asset or JavaScript completion. For CJK, animate phrase- or line-level wrappers chosen after real wrapping; do not blindly stagger individual ideographs or split ruby/annotation markup.

For a dashboard preview, animate only truthful state changes. A skeleton may resolve into data when data actually arrives; a filter may preserve object identity while values reorder; a chart may disclose a comparison without changing the values. Stop off-screen work and provide the exact-value/static result first. Motion must never imply that invented data is live intelligence.

For `login → dashboard`, authentication and navigation own the state. Submit feedback and errors stay immediate. After success, preserve focus, announcement, route history and scroll behavior; then use a feature-detected View Transition for true shared objects, or one scoped GSAP timeline when several independent layers need orchestration. Never delay authentication, hide an error, or make the dashboard unusable until a celebratory transition finishes.

### Decide whether an icon should move

Classify each icon as `static | state-pair | one-shot feedback | progress | decorative`. Static is the default. Add motion only when it confirms an input, explains a state change, preserves identity, or carries one bounded brand beat.

- Reuse the product's icon family. Keep viewBox, optical size, stroke/fill, cap/join, corner grammar, color behavior, and animation language coherent; do not mix a detailed animated illustration into a compact system-icon row.
- Keep the familiar silhouette and visible label for ambiguous or culturally variable actions. Motion reinforces meaning; it never becomes the only label, status, or instruction.
- Prefer user-triggered, non-looping playback for controls. Direct feedback starts with the input and resolves before repeated input can queue stale scenes. Hover polish is optional and must have keyboard/touch behavior that preserves the task without hover.
- Reserve continuous motion for real progress or a justified ambient role. Pause it off-screen/background, expose a control when required, and remove attention loops from frequently used navigation and form controls.
- Inspect the first, semantic transition, extreme, and final frames at every shipped optical size. A crisp large preview does not prove that a 16px or 24px icon remains recognizable.

Lordicon's official guidance is useful for family consistency, recognizable meaning, labels, restrained looping, and immediate feedback. Its specific timing bands and target sizes are product examples, not universal acceptance thresholds. The same boundary applies to secondary articles that recommend a single duration “sweet spot.”

## 2. Choose the smallest runtime

Escalate only when the lower tier cannot meet a named requirement.

| Need | Default | Escalate when | Required guardrail |
| --- | --- | --- | --- |
| Hover, focus, disclosure, local state | CSS transition | no escalation | Do not use `transition: all`; list properties. |
| Finite declarative sequence | CSS animation | runtime pause/seek/reverse is necessary | Content already exists; animation has a static end state. |
| Dynamic timing or imperative control | Web Animations API | framework orchestration is already justified | Retain `Animation` handles; cancel and clean up. |
| Same-document or route continuity | View Transitions | shared elements meaningfully represent the same object | Feature detect; unique names; immediate fallback; verify focus/scroll. |
| React/Vue layout, spring, or gesture system | Existing framework motion library | native tiers would duplicate substantial state/timeline work | Measure bundle and lifecycle; use the library's reduced-motion mechanism. |
| Complex reversible timeline, SVG choreography, scroll narrative | GSAP or existing timeline system | several synchronized stages, reversal, interruption, and authoring control are truly needed | Review runtime license; scope, revert, profile, and test low-end mobile. |
| Smooth-scroll synchronization | Native scrolling | only a justified WebGL/scroll-story synchronization need remains | Never default to Lenis; preserve anchors, Back, focus, modals, restoration, and native mode under reduced motion. |
| Designer-authored linear vector animation | Lottie | a controlled brand/story asset is cheaper than rebuilding it | Poster/static frame; pause off-screen; destroy on unload; limit JSON/nodes. |
| Interactive vector state machine | Rive | input-driven states reduce real application complexity | DOM equivalent, canvas/WASM/GPU budget, touch-scroll policy, cleanup. |

[Web Animations](https://www.w3.org/TR/web-animations-1/) gives user agents a native animation model; [View Transitions Level 1](https://www.w3.org/TR/css-view-transitions-1/) separates DOM updates from visual snapshots; [Scroll-driven Animations](https://www.w3.org/TR/scroll-animations-1/) is still a Working Draft, so capability checks and fallbacks are mandatory.

For Motion/Framer Motion, inspect the installed package and framework version before choosing imports or router patterns. Use `AnimatePresence`, layout animation, gestures, or shared layout only when they solve an actual state/continuity need. Avoid private router internals unless the exact framework version and upgrade risk are in scope. A schema that records `fps`, `gpuAccelerated`, or `reducedMotion` booleans is configuration intent, not measured proof.

### GSAP choreography contract

Use GSAP only after the runtime ladder selects it. The official GSAP Skills are useful API references, not a product-design decision system.

- Pin the installed `gsap` and optional `@gsap/react` versions in the project's package lock. Import only used plugins and call `gsap.registerPlugin(...)` before use so a production bundler does not tree-shake them away.
- Use one `gsap.timeline()` for a coordinated scene. Put shared defaults on the timeline, name semantic labels such as `establish`, `explain`, and `resolve`, and use position parameters for overlap. Do not chain unrelated `delay` values.
- Scope selectors and lifecycle. In React, prefer `useGSAP(..., { scope })`; wrap later callbacks with `contextSafe`. Otherwise create `gsap.context(..., scope)` and return `ctx.revert()`. A route change or unmount must not leave tweens, ScrollTriggers, listeners, or inline start states behind.
- Use `gsap.matchMedia()` for responsive composition and the runtime reduced-motion branch, then call `mm.revert()` at teardown. A reduced branch should construct the named static/final result and avoid scroll-scrub, large travel and continuous loops; setting only `duration: 0` is not sufficient lifecycle or semantic handling.
- Prefer GSAP transform aliases and `autoAlpha` when appropriate, but keep semantic content visible without enhancement. Bound `will-change` around measured animation; do not assume `transform`, opacity, numeric `scrub`, or a requestAnimationFrame wrapper proves performance.
- With ScrollTrigger, choose exactly one relationship: `toggleActions` for a discrete reveal, or `scrub` for progress that genuinely maps to scroll. Attach it to a top-level tween/timeline, not a child tween. Animate children of a pinned shell, not the pinned element.
- Create triggers in document order. If order must differ, verify `refreshPriority` against the installed GSAP documentation; higher priorities refresh earlier in current official docs. After fonts, images, async content or measured layout change, call `ScrollTrigger.refresh()` at a stable point; use `invalidateOnRefresh` for function-based values that must be recalculated.
- Development markers never ship. Kill/revert on teardown. Re-test anchors, focus, Back/Forward, short landscape, nested scrolling, dynamic type, mobile browser chrome and the final unpinned document.

For a ScrollTrigger product section, keep the product name, evidence and CTA in normal semantic DOM. Pin only when holding one stable product view while a small set of features changes is the clearest causal model. Define every scene's `trigger/start/end`, whether it is discrete or scrubbed, pin owner/spacing, refresh inputs, interruption, reduced static state and terminal document state. If removing ScrollTrigger makes the content order incoherent, repair the document before animating.

## 3. Build lifecycle and interruption

- Start from static, usable markup. Enhance after capability and preference checks.
- Keep state in product logic; animation reflects state and never becomes the source of truth.
- On new input, animations must reverse, retarget, finish, or cancel coherently. Do not queue stale transitions.
- Pause continuous work when its element leaves the viewport and when `document.hidden` becomes true.
- On route change/unmount, call the runtime's `cancel`, `revert`, `destroy`, or cleanup path and detach observers/listeners.
- Use `will-change` only immediately around a proven animation; remove it afterward.
- Prefer `transform` and `opacity`, but do not claim they are free. Filters, clip paths, large layers, text rasterization, and oversized compositing surfaces still require profiling.
- Batch layout reads before writes. A requestAnimationFrame wrapper does not cure layout thrashing by itself.
- Distinguish composite, paint, and layout work, then verify the real layer/paint result. `transform` and `opacity` can still create oversized layers or costly rasterization.
- Avoid long-lived `fill: forwards` as state storage. Commit the intended state deliberately, then release animation resources where appropriate.
- Preloaders may indicate a real blocking process; they must not manufacture delay, hide LCP content, or become a required entrance ceremony.

## 4. Provide a reduced-motion result

Use the user preference from [Media Queries Level 5](https://www.w3.org/TR/mediaqueries-5/#prefers-reduced-motion). The alternative must preserve meaning, order, and final state.

Reduce or remove:

- parallax, large translation, scale/zoom, rotation, depth travel, and auto-scrolling;
- smooth scrolling and scroll-scrubbed motion;
- autoplay video, Lottie, Rive, canvas, WebGL, and infinite ambient loops;
- flashes, rapid oscillation, and attention-stealing repetition.

Keep necessary state feedback through an instant update, static replacement, or restrained non-spatial change. Do not treat a blanket `0.01ms !important` rule as the full solution: it may leave loops, callbacks, scroll engines, or asset runtimes active and may skip the semantic final state.

For JavaScript systems:

- check the preference before creating expensive effects;
- react if the preference changes during the session;
- stop and dispose existing instances when it becomes `reduce`;
- test the actual reduced path, not only the presence of a media query.

[Motion's `useReducedMotion`](https://motion.dev/docs/react-use-reduced-motion) is one library-specific example; the contract applies regardless of runtime.

## 5. Protect mobile and scrolling

- Gate hover-only polish with `(hover: hover) and (pointer: fine)`; provide tap and keyboard equivalents.
- Keep touch cancellation, native page scroll, browser zoom, text selection, and system gestures intact.
- Test nested scroll containers, modal scroll lock, virtual keyboard, safe areas, short landscape, anchor links, Back/Forward, and scroll restoration.
- Avoid scroll-jacking. A scroll-linked narrative must leave the user in control and remain understandable when the effect is absent.
- Do not pin large sections merely to imitate an award-site trope. Confirm reading order, focus visibility, and escape routes while pinned.
- Reduce effect count, layer area, DPR, and asset complexity on constrained devices based on measurement—not user-agent stereotypes.
- Never use a desktop FPS counter as mobile evidence.

## 6. Handle SVG and asset runtimes

Read [svg-system.md](svg-system.md) for SVG semantics, IDs, security, and optimization.

- Prefer transform/opacity for SVG groups; profile path morphs, masks, filters, and thousands of DOM nodes.
- Do not animate text converted to paths when the text carries content.
- Lottie: compare SVG and Canvas renderers, JSON size, parse cost, node count, and masks; provide a poster and an accessible DOM description.
- Rive: cap canvas DPR, release WASM/GPU resources, preserve touch scrolling, and provide equivalent DOM information and controls.
- Essential charts and instructions cannot live only inside canvas or an animated vector state.

### Author and validate Lottie as a runtime asset

Before creating or accepting Lottie/dotLottie, freeze:

```text
source/tool → product purpose → emotional target/personality → setup/action/resolution → Lottie version/features → exact player/version/renderer → dimensions/fps/ip/op → background/alpha → fonts/images/precomps/slots → semantic beats/loop seam → loop/autoplay/control → fallback/description → limits/license → evidence
```

- Validate JSON/archive structure and reject impossible bytes, decompressed size, dimensions, frame range/rate, layer/node/keyframe counts, recursion, embedded data, and external asset URLs. A parse pass does not prove renderer compatibility.
- Author against the actual shipped player. Skottie, lottie-web SVG/Canvas, dotLottie, native mobile players, and editor previews support different subsets; a player-specific directory or slot convention never becomes a universal Lottie rule.
- Default new playback contracts to `autoplay: false` and `loop: false`. Enable either only when the recorded trigger/frequency requires it; never copy a demo's looping/autoplay flags into product UI.
- Decide transparent versus full-frame background deliberately. Reserve the final aspect ratio and keep the poster visible until the player is ready.
- Keep meaningful text as semantic DOM. If native Lottie text is used, verify bundled font family names, glyph coverage, license, shaping, CJK/RTL behavior, loading, and fallback; vectorized text is artwork, not accessible/localizable copy.
- For lottie-web SVG, provide renderer `title`/`description` only when the scene is exposed as a meaningful image; otherwise hide the decorative container and place the control's name/state on the owning DOM control. Do not let runtime metadata duplicate a button's accessible name.
- Inspect `ip`, representative transition/extreme frames, midpoint, and `op - 1` in the exact renderer. Check layer order, masks/mattes, crop, easing, blank frames, interpolation, looping seam, and asset failure at each target size/theme.
- Name semantic beat frames and capture the loop-seam pair; a smooth scrub or valid JSON is not evidence that the intended micro-story reads correctly.
- Expose play/pause/state controls when required. Under reduced motion or data constraints, do not instantiate/autoplay the scene; render the named poster/final state.
- Handle load/data failure by retaining the poster and semantic DOM result. Pause off-screen/background playback and call the player's supported `destroy` path; remove observers/listeners and release decoded images/canvases on teardown. Repeated mount/unmount must not multiply loops.

For a material motion system, keep a compact token manifest: named durations/easings, intended interaction class, reduced result, owner, and validated runtime. A “signature easing” is a brand hypothesis until actual controls, interruption, target devices, and user preferences verify it.

Motion personality, emotional intent, staging, and narrative can guide an authored brand scene. Fixed archetypes, universal duration tables, mandatory overshoot, and compulsory primary/secondary/ambient layers are creative hypotheses—not acceptance rules. Ambient motion is optional and must earn its lifecycle cost. Functional UI feedback should remain direct even when an illustration uses richer choreography.

## 7. Verify behavior and performance

Minimum matrix:

| State | Desktop | 390px touch | Keyboard | Reduced motion | Background/off-screen |
| --- | --- | --- | --- | --- | --- |
| Initial static content |  |  |  |  |  |
| Start / interrupt / reverse |  |  |  |  |  |
| Route or shared-element transition |  |  |  |  |  |
| Modal / nested scroll |  |  |  |  |  |
| Continuous or asset runtime |  |  |  |  |  |

Collect evidence:

- browser screenshots before, at named semantic/intermediate frames when useful, and after the effect; for animated icons and Lottie, include the smallest shipped size plus reduced-motion and failed-asset results;
- keyboard, no-hover, reduced-motion, anchor, Back/Forward, and focus assertions;
- console and failed network requests;
- cleanup after route changes and repeated mounts;
- off-screen/background CPU activity;
- performance trace under mobile CPU/network constraints;
- CLS/LCP impact and long tasks, layout invalidation, paint, layer, memory, and GPU evidence.

Release blockers:

- essential content waits for animation;
- state and visual result disagree after interruption;
- reduced mode still performs major movement, smoothing, or continuous work;
- scrolling, focus, Back, anchors, or modal locking breaks;
- repeated mounts leak listeners, animation handles, canvases, or GPU contexts;
- a library or premium asset is shipped without verified license terms;
- a signature effect causes material jank, layout shift, or battery/CPU load.

## 8. Source and license notes

Snapshot candidates from GitHub research:

| Runtime/source | Adoption snapshot | License boundary | Use carefully because |
| --- | ---: | --- | --- |
| [Motion](https://github.com/motiondivision/motion) | 32,795 stars | Core MIT; Motion+ products separate | bundle and framework lifecycle; performance differs by property and value type. |
| [GSAP](https://github.com/greensock/GSAP) | 26,561 stars | Current distribution uses GreenSock's [no-charge standard license](https://gsap.com/standard-license), not MIT; current official material says all plugins are free, including commercial use | use GSAP 3.13+ when migrating from the retired private registry; powerful defaults can encourage unnecessary ScrollTrigger/pinning; pin, review terms, and profile. |
| [Lenis](https://github.com/darkroomengineering/lenis) | 14,359 stars | MIT | anchors require configuration; nested scrolling and platform limits need direct tests. |
| [Lottie-web](https://github.com/airbnb/lottie-web) | 32,008 stars | MIT runtime; source artwork rights separate | large JSON, masks, nodes, parsing, and no automatic reduced-motion behavior. |
| [Rive WASM](https://github.com/rive-app/rive-wasm) | 953 stars | Runtime MIT; editor/export/service plans separate | canvas/WASM/GPU lifecycle and accessible equivalents remain application work. |

The official [GSAP Agent Skills@aed9cfd](https://github.com/greensock/gsap-skills/tree/aed9cfd3277740755f6bfc1155c7aa645403b760) provide compact core/timeline/ScrollTrigger/framework/performance API routing. Adopt timeline labels and position parameters, scoped `useGSAP`/`gsap.context()` cleanup, plugin registration, top-level ScrollTriggers, refresh after layout change, and pin-child separation. Do not copy the repository as an unquestioned gate: its ScrollTrigger text contradicts current official docs by saying lower `refreshPriority` runs first; its Nuxt page registers cleanup with a second `onMounted()` instead of `onUnmounted()`; its performance advice overstates compositor guarantees and numeric scrub; and its reduced-motion example equates the result with `duration: 0`. The Skill files are MIT, but that does not convert the GSAP runtime license into MIT.

The [UI Skills registry](https://www.ui-skills.com/skills) is a useful discovery layer for animation vocabulary, motion-performance review, and production-audit patterns. Treat its fixed timing, easing, blur, mechanism, or reduced-motion recipes as author heuristics until target-browser evidence validates them.

Additional research boundaries:

- [LottieFiles motion-design-skill](https://github.com/LottieFiles/motion-design-skill) contributes purpose, emotion, narrative, choreography, frequency, and context vocabulary. Mandatory ambient layers, fixed personalities, universal duration tables, and compulsory overshoot remain creative hypotheses.
- [airbnb/lottie-web](https://github.com/airbnb/lottie-web) is the runtime authority for its API, events, SVG renderer settings, performance notes, and `destroy` lifecycle. The MIT runtime license does not grant rights to animation artwork.
- [iart-ai web-animation-skills](https://github.com/iart-ai/web-animation-skills) contributes deterministic seek/freeze and contact-sheet verification ideas. Its standalone-HTML output shape, “transform/opacity only” framing, blanket near-zero reduced-motion net, and fixed frame-rate claims do not become universal gates.
