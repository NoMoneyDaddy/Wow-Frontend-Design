# Production implementation

Use this reference while turning the design thesis into maintainable code.

## Contents

1. Respect the stack
2. Build durable foundations
3. Implement interaction and motion
4. Handle assets and media
5. Preserve accessibility and resilience
6. Protect performance

## 1. Respect the stack

- Reuse the project's framework, router, state, styling, component, and test conventions.
- Prefer platform features and existing dependencies. Add a dependency only when it clearly reduces risk or complexity.
- Keep server and client boundaries intentional. Do not move static presentation into client JavaScript without a reason.
- Preserve semantic HTML through component abstractions.
- Keep secrets and private endpoints out of frontend code; use the project's environment-variable mechanism.
- Handle fallible data and asset loading explicitly.

If starting from zero, choose the smallest stack that satisfies routing, content, state, deployment, and team needs. A single page may need only HTML/CSS/JS; a product app may justify a framework.

### Formal production cadence

Carry the selected style contract, frozen product contract, fixtures, and implementation delta into formal work; do not restart discovery or direction unless new evidence invalidates them. Reuse compatible draft source through the real architecture, but never preserve disposable markup merely because it is already rendered.

Use a dependency-ordered production pass: first semantics and data/state ownership, then responsive composition and access behavior, then only consumed system roles and reusable primitives, then visual finish and admitted motion, and finally expansion to related routes. Complete one task path across these layers before polishing disconnected regions; extract shared structure only after repeated task roles prove it.

Run the cheapest owning-layer check after each bounded edit and a fresh targeted Playwright replay after each coherent batch. Run project gates and the full declared affected matrix at the release candidate, then replay any scope touched by a repair. Do not rerun every expensive gate after an unrelated small edit. Never use a green narrow loop as release evidence or skip the final fresh matrix.

## 2. Build durable foundations

Define semantic tokens, not component-specific color names:

```css
:root {
  --color-canvas: ...;
  --color-surface: ...;
  --color-ink: ...;
  --color-muted: ...;
  --color-action: ...;
  --color-focus: ...;
  --space-page: clamp(1rem, 3vw, 3rem);
  --measure-reading: 68ch;
  --duration-fast: 140ms;
  --duration-base: 260ms;
  --ease-out: cubic-bezier(.2, .8, .2, 1);
}
```

- Use one reset and one box-sizing policy.
- Set media to responsive defaults and reserve intrinsic dimensions.
- Keep reading measure independent from outer layout width.
- Use `clamp()` for continuity, but keep minimums readable and maximums intentional.
- Prefer component-local container queries when a component appears in multiple shells.
- Keep specificity shallow. Avoid `!important` except documented integration boundaries.
- Use variants or data attributes for component states; do not create one-off selector chains.
- Use logical properties for direction resilience.
- Keep z-index values in a small named layer system.

## 3. Implement interaction and motion

Use [motion-system.md](motion-system.md) for the selection ladder, runtime lifecycle, reduced-motion contract, library/licensing boundaries, and verification matrix.
Use [platform-adapters.md](platform-adapters.md) when framework versions, SSR/hydration, routing/data ownership, component libraries, monorepos, or native clients affect the implementation. Use [advanced-media.md](advanced-media.md) for Canvas, WebGL, Three.js, shaders, 3D, video, or sound.
Use [frontend-security.md](frontend-security.md) when user/CMS/AI content, identity, payments, storage, external URLs, embeds, telemetry, or browser security policy crosses a trust boundary.

- Start from a complete static state.
- Use JavaScript to enhance, not to reveal essential content that CSS hid by default.
- Prefer CSS for simple state transitions; use JavaScript or animation libraries for coordinated state, physics, or timeline needs already justified by the concept.
- Animate transform and opacity when possible. Measure before animating layout-heavy properties.
- Pause continuous loops with visibility and intersection state.
- Debounce or coalesce scroll/resize work with `requestAnimationFrame` where appropriate.
- Cap canvas/WebGL DPR and object counts. Reallocate expensive buffers sparingly.
- Gate fine-pointer effects behind `(hover: hover) and (pointer: fine)`.
- Implement a reduced-motion result, not merely a media-query stub. Preserve meaning with an instant state, shorter transition, or static frame.
- Make carousels, drag surfaces, canvases, and custom controls keyboard and screen-reader operable or provide an equivalent control.
- Treat modal navigation as a complete state machine: open, lock background scroll, move and contain focus, close by explicit control, close after an in-menu navigation choice when appropriate, close by Escape, restore prior focus, and remove every temporary attribute/class on all exit paths.
- Exercise form validation outside the `submit` handler. Native constraint validation can prevent `submit` from firing, so clear stale success on `input` and handle `invalid` or use a deliberate `novalidate` custom-validation flow. Test valid submission followed by an invalid attempt.
- Give anchored headings `scroll-margin-block-start` when sticky UI could cover the destination.
- Do not block paste in text, password-manager, verification-code, or payment fields. Validate and normalize the resulting value instead.
- Warn before leaving only when an actual unsaved user change would be lost; clear the guard after save/discard and do not trap ordinary navigation.
- Test native form controls, especially `<select>`, in the shipped light/dark/forced-color combinations; declare `color-scheme` only for modes the surrounding UI truly supports.

## 4. Handle assets and media

Use [svg-system.md](svg-system.md) for icons, illustrations, data visualization, sprites, untrusted SVG, sanitization, optimization, and rendered verification.

- Use user-provided or properly licensed assets and record attribution where required.
- Do not hotlink search results or use remote assets with unknown rights.
- Generate purposeful CSS/SVG visuals when they support the concept and remain maintainable.
- Classify every material SVG by asset type, trust, embedding mode, accessibility intent, and provenance before choosing inline markup, `<img>`, a sprite, or an active document.
- Treat user-supplied SVG as active untrusted markup. Optimization tools such as SVGO do not replace sanitization, parser limits, isolated storage, or upload controls.
- Do not use empty gradient rectangles as substitutes for evidence-bearing product, place, person, or editorial imagery. Use supplied/licensed/generated assets, an explicitly illustrative product-specific SVG, or recompose the page so missing media is not pretending to be proof.
- Give meaningful images useful `alt`; use empty `alt` or `aria-hidden` for decoration.
- Art-direct crops by viewport; one desktop crop rarely serves a narrow hero.
- Use responsive image sources and modern formats when available.
- Reserve dimensions and lazy-load below-fold media. Do not lazy-load the likely LCP asset.
- Avoid icon-font dependencies. Use one coherent SVG icon family or existing project library.
- Namespace SVG IDs used by gradients, masks, filters, markers, clip paths, and `aria-labelledby`; verify every reference after optimization and component duplication.
- Never use emoji as production icons unless the product intentionally depends on platform emoji variation.
- Verify font files, licenses, subsets, glyph coverage, weight mapping, and `font-display`. Provide robust fallbacks.

## 5. Preserve accessibility and resilience

Use WCAG 2.2 AA as the everyday implementation baseline unless the project specifies a stronger standard, but do not call that conformance. Formal AA conformance requires an explicit scope, the full [wcag-aa-checklist.md](wcag-aa-checklist.md), and evidence for every applicable Level A and AA criterion across the complete pages, responsive variations, and processes in that scope. A weighted design score or automated scan cannot offset or establish conformance.

- Use landmarks, heading order, labels, descriptions, and native controls.
- Provide a skip link for substantial page navigation.
- Keep focus visible and unobscured; return focus after dialogs and menus.
- Meet applicable contrast thresholds across actual states and layered backgrounds: 4.5:1 for normal text, 3:1 for qualifying large text, and 3:1 for essential UI components and graphical objects. Do not round a failing ratio up to a pass; apply documented WCAG exceptions precisely.
- Make touch and pointer targets comfortably large and separated.
- Do not rely on color, hover, gesture paths, sound, or motion alone.
- Allow 200% text resize/zoom without loss of content or function. Separately verify reflow at 400% zoom or a 320 CSS px equivalent viewport; for content designed to scroll horizontally, including vertical writing, verify the 256 CSS px height equivalent.
- Preserve browser navigation, selection, copy, and expected keyboard behavior.
- Announce async success and errors appropriately without excessive live-region noise.
- Keep dynamic accessible names and descriptions synchronized with visible counts, pressed states, prices, validation, and status changes.
- Keep loading, empty, error, offline, permission, and partial-data states actionable.
- Sanitize or safely render user-controlled rich content according to the stack.

## 6. Protect performance

Use these user-experience targets as a practical baseline for field data at the 75th percentile, segmented by mobile and desktop. All three metrics must meet the good threshold for a Core Web Vitals pass:

- LCP ≤ 2.5 s;
- INP ≤ 200 ms;
- CLS ≤ 0.1.

Then:

- keep the critical rendering path lean;
- avoid shipping animation or component libraries for one small effect;
- split code by route or heavy capability when the stack supports it;
- preconnect and preload only proven critical origins/assets;
- remove unused weights, icons, CSS, and third-party scripts;
- prevent hydration work for static content where architecture permits;
- test under CPU and network constraints, not only a fast development machine;
- keep the signature moment bounded so performance loss never becomes the memorable feature.

Do not trade comprehension or accessibility for a synthetic score. Fix large bottlenecks first and report measured evidence.
