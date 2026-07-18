# Mobile and responsive design

Use this reference to create a mobile experience with its own composition, navigation, and interaction logic.

## Contents

1. Start from mobile context
2. Write a transformation table
3. Apply mobile composition patterns
4. Engineer resilient responsive behavior
5. Verify real devices and awkward sizes

## 1. Start from mobile context

Assume mobile use may involve one hand, interruptions and context switching that increase memory demands, glare, slow networks, no hover, and an on-screen keyboard. Preserve the top task and product identity under those conditions.

Answer:

- What must be visible before the first scroll?
- What action belongs in the thumb zone?
- What context can appear on demand instead of at once?
- Which visual needs a new crop, viewpoint, or representation?
- Which desktop comparison becomes a stepper, tabs, disclosure, or focused detail?
- What can be deferred without hiding the product's value?

Define first-viewport task priority at the representative mobile height, not a fixed must-fit quota. Current context includes the minimum evidence or control a person must inspect or operate before making the next decision; a status label alone is insufficient when the underlying media, data, or comparison is required. When that context, a blocking permission/trust state, and the next action can coexist without compressing or truncating required content, prove that combination before secondary evidence. At large text/zoom, in a long locale, or on a short landscape viewport, keep required safety and consent content intact and place the next action directly after it, discoverable, reachable, and unobscured. Source order alone does not pass when a full desktop region displaces those needs; reduce or defer the secondary region behind a truthful, discoverable disclosure, sheet, focused detail, or route.

Do not begin with breakpoints. Begin with task order.

## 2. Write a transformation table

Create this before implementing responsive CSS:

| Region | Desktop role | Mobile equivalent | Mobile order | Interaction | Defer/remove |
| --- | --- | --- | --- | --- | --- |
| Global navigation | Persistent global choices | Compact header + modal sheet | 1 | Move/contain focus while open, close/Escape, restore focus | Secondary links |
| Frequent peer destinations | Persistent rail or tabs | Optional bottom navigation | Persistent | Normal tab sequence; never trap focus | Infrequent destinations |
| Hero visual | Atmosphere + proof | Cropped/reframed proof near title | 2 | Static or light response | Heavy ambient loop |
| Primary CTA | In hero cluster | Sticky or thumb-reachable action when justified | 3 | Tap | None |
| Comparison | Side-by-side columns | Focused cards, tabs, or horizontal rail | Later | Tap/swipe plus buttons | Tertiary attributes |

Every major region needs an explicit answer. “Stack” is not an answer unless the reading order and interaction remain optimal.

Keep one logical record and state source across responsive modes. A desktop table and mobile card may look different, but hidden duplicate DOM copies must not create repeated IDs, evaluator hooks, accessible identities, stale state, or two independently focusable controls. Share data, state, action, and accessible meaning—not necessarily one DOM composition. Recompose one semantic structure with CSS only while its representation, disclosure, and task path remain optimal; when the mobile task sequence or representation materially differs, render only the active composition from the same state/view model and prove state and focus parity in both directions.

Repeat the transformation table for reachable states, not only the default page. At minimum cross the affected viewport with `default`, `open/expanded`, `filtered`, `validation/error`, and `success/confirmation` when those states exist. A page that becomes mobile-safe only before interaction is not responsive.

## 3. Apply mobile composition patterns

### Navigation

- Keep the current location and primary action obvious.
- Use a bottom bar only for frequent peer destinations, usually 3–5 items.
- Use a sheet or full-screen menu for larger information architecture.
- For modal sheets, lock background scroll correctly, move focus into the sheet, contain focus only while open, return focus logically on close, support Escape, expose expanded state, and close after a navigation choice when the destination does not replace the page.
- Keep persistent bottom navigation in the normal tab sequence. Never trap focus inside it.
- Respect `env(safe-area-inset-*)` for edge-fixed controls.
- Render menus and sheets closed by default. Capture the default viewport before exercising the open state, then verify open, close, Escape, selection, background scroll, and focus return separately.
- When a fixed or sticky bar is justified, reserve matching content and safe-area space. Test its rectangle against the first heading, primary action, focused field, validation message, and final content; a bar that visually covers them fails even when the document can still scroll.

### Hero

- Recompose art direction; do not merely scale the desktop crop.
- Keep the proposition readable without waiting for animation.
- Avoid a decorative full-height hero that pushes all proof below the fold.
- Remove or background a decorative peer column when it squeezes the proposition or primary task. An `aria-hidden` region does not earn layout width merely because it looks like a diagram; use a real, provenance-checked asset when the visual is required.
- Use `svh`/`dvh` carefully; content must survive browser chrome, landscape, and short screens.

### Dense information

- Preserve the primary comparison dimension.
- Turn secondary context into details, sheets, tabs, or progressive disclosure.
- Keep data tables horizontally scrollable only when column relationships require it; freeze labels or provide a mobile summary.
- Give horizontal rails visible overflow, controls, or another affordance. Do not hide navigation in an invisible swipe.

### Forms and actions

- Keep labels visible; placeholders are examples, not labels.
- Use appropriate input types and `autocomplete` tokens.
- Keep validation near the field and provide a top-level error summary for long forms.
- Avoid fixed elements that collide with the virtual keyboard.
- Keep frequent actions reachable but avoid multiple competing sticky bars.

### Touch

- Aim for at least 44×44 CSS px touch areas even where the conformance minimum is smaller.
- Separate destructive and frequent actions.
- Do not make hover the only way to reveal information or controls.
- Provide tap alternatives for drag, pinch, or path gestures.

## 4. Engineer resilient responsive behavior

- Use content-driven mode changes. Add a breakpoint where the composition fails, not because a device label exists.
- Prefer fluid tokens with `clamp()` for type, spacing, and gaps; constrain line length separately.
- Use Grid/Flexbox intrinsic sizing, `minmax()`, `min()`, `max()`, and container queries where component context matters.
- Add `min-width: 0` to flexible children that contain long text.
- Audit selector specificity across responsive states. A desktop rule such as `.content-grid.review-open` can outrank a later mobile `.content-grid` rule and silently restore desktop columns after interaction. Match or intentionally exceed the state selector inside the media/container query, or move the responsive state into a lower-specificity architecture; verify computed grid/flex values after the state changes.
- Apply `box-sizing: border-box` to bounded layout primitives. Audit the sum of shell offsets, gaps, padding, and percentage/viewport widths; never use `overflow-x: hidden` as the fix for a child that exceeds the viewport.
- Use logical properties (`margin-inline`, `padding-block`, `inset-inline-end`) to support RTL and writing modes.
- Reserve media dimensions with `aspect-ratio` or explicit sizes to prevent layout shift.
- Avoid fixed heights for text containers.
- Reject de facto vertical text produced by a squeezed horizontal column. Intentional vertical Chinese uses `writing-mode`, correct column progression, punctuation, and a horizontal responsive equivalent; a one-character-wide horizontal paragraph is a layout failure.
- Avoid `100vw` inside pages with scrollbars; it commonly creates overflow.
- Cap canvas/WebGL device pixel ratio, pause off-screen loops, debounce expensive resize work, and reduce density on small or low-power devices.
- Support `prefers-reduced-motion`; consider `prefers-reduced-data` as an enhancement where available.

## 5. Verify real devices and awkward sizes

Test rendered output, not only CSS:

| Context | Minimum checks |
| --- | --- |
| 320px narrow | no clipped text, no accidental horizontal scroll, controls fit |
| 360–390px mobile | hero, nav, primary task, keyboard, safe areas, touch sizes |
| Short mobile / landscape | no trapped overlays, fixed UI does not consume the screen |
| 768px portrait tablet | intentional density; no “large phone” dead zone |
| 1024px landscape tablet | input-mode assumptions, nav transition, grid balance |
| 1280–1440px desktop | intended composition, keyboard, hover as enhancement |
| 1920px+ wide | content does not become sparse or unreadably wide |

At every size verify:

- task hierarchy, current context, and the next action or concurrent actions appropriate to the surface;
- content order and heading structure;
- navigation open/close and focus behavior;
- overlays, sticky elements, and scrolling;
- long labels and localized strings;
- image crop and signature moment;
- loading, empty, error, and success states;
- no unexpected overflow.
- no long prose squeezed below its script-aware useful measure, no tall multi-line command caused by a narrow track, and no large unexplained void or detached summary after state changes;
- no Traditional Chinese heading compressed by a Latin `ch` cap, no four-plus-line fragment created while usable inline space remains, and no compact lexical unit split only because a progressive line-breaking feature failed;
- short command labels remain intentionally one line unless the component contract explicitly allows wrapping; verify rendered line boxes and clipping, not only page overflow.
- fixed/sticky UI leaves the current primary content and focused control unobscured, including safe areas and the virtual keyboard.
- responsive alternatives preserve the same required content, semantics, and declared test/evaluator hook; only the presentation and interaction mode change.

For every modal menu, run this exact sequence: record page scroll → open → attempt background scroll and confirm it is locked → activate an internal destination and confirm the sheet closes with coherent focus → reopen → press Escape and confirm focus returns to the opener. Source presence is not evidence.

Capture separate mobile and desktop screenshots. A desktop screenshot narrowed by CSS is not proof of a designed mobile experience.

Viewport emulation is browser evidence, not automatically a physical-device claim. Record CSS viewport, DPR, user agent, touch capability, `isMobile`, browser engine, and whether the run used a simulator/emulator or physical device. A true mobile browser profile is stronger than width-only resizing; it still does not prove browser chrome, virtual keyboard, GPU/font rasterization, OS accessibility services, thermal limits, or real touch behavior. Use a simulator/emulator or device for risks that depend on those layers.

Keep one browser session and sweep adjacent widths around every observed mode change rather than checking only named devices. Start with coarse samples, then narrow the failing interval until the actual transition range is known. Verify both directions across that range with the same route, data, locale, zoom, theme, and open/closed interaction state; watch for a one-pixel overlap, hidden action, focus loss, stale overlay, crop jump, or accidental overflow between headline viewports.
