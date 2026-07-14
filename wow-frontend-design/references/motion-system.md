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
- Decide transparent versus full-frame background deliberately. Reserve the final aspect ratio and keep the poster visible until the player is ready.
- Keep meaningful text as semantic DOM. If native Lottie text is used, verify bundled font family names, glyph coverage, license, shaping, CJK/RTL behavior, loading, and fallback; vectorized text is artwork, not accessible/localizable copy.
- Inspect `ip`, representative transition/extreme frames, midpoint, and `op - 1` in the exact renderer. Check layer order, masks/mattes, crop, easing, blank frames, interpolation, looping seam, and asset failure at each target size/theme.
- Name semantic beat frames and capture the loop-seam pair; a smooth scrub or valid JSON is not evidence that the intended micro-story reads correctly.
- Expose play/pause/state controls when required. Under reduced motion or data constraints, do not instantiate/autoplay the scene; render the named poster/final state.
- Pause off-screen/background playback and destroy player, observers, event listeners, decoded images, and canvases on teardown. Repeated mount/unmount must not multiply loops.

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

- browser screenshots before, during when useful, and after the effect;
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
| [GSAP](https://github.com/greensock/GSAP) | 26,561 stars | Custom [no-charge standard license](https://gsap.com/standard-license), not MIT | powerful defaults can encourage unnecessary ScrollTrigger/pinning; review license and profile. |
| [Lenis](https://github.com/darkroomengineering/lenis) | 14,359 stars | MIT | anchors require configuration; nested scrolling and platform limits need direct tests. |
| [Lottie-web](https://github.com/airbnb/lottie-web) | 32,008 stars | MIT runtime; source artwork rights separate | large JSON, masks, nodes, parsing, and no automatic reduced-motion behavior. |
| [Rive WASM](https://github.com/rive-app/rive-wasm) | 953 stars | Runtime MIT; editor/export/service plans separate | canvas/WASM/GPU lifecycle and accessible equivalents remain application work. |

Also review the official [GSAP Agent Skills](https://github.com/greensock/gsap-skills) only for GSAP-specific implementation. Their MIT skill license does not convert the GSAP runtime license into MIT.

The [UI Skills registry](https://www.ui-skills.com/skills) is a useful discovery layer for animation vocabulary, motion-performance review, and production-audit patterns. Treat its fixed timing, easing, blur, mechanism, or reduced-motion recipes as author heuristics until target-browser evidence validates them.
