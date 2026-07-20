# No-visual first-pass protocol

Use this reference when the host cannot render, inspect screenshots, operate a browser, or obtain visual feedback. It reduces first-pass risk; it cannot certify rendered quality.

## State the evidence ceiling

Without a render, these remain `UNVERIFIED`: actual wrapping, font rasterization/fallback timing, optical alignment, layered or media contrast, crop, overflow, sticky/overlay behavior, pointer/touch feel, animation quality, GPU cost, browser differences, and subjective craft.

Source inspection may produce `INFERRED` findings. Successful syntax, lint, build, unit, or static-audit commands may be `VERIFIED` only for the exact property they test. Never translate them into “looks good,” WCAG conformance, or browser support.

## Freeze a low-entropy direction

Before code, fill one card and stop generating alternatives:

```text
USER / TOP TASK / CONTENT ORDER:
CONCEPT + ONE VISUAL GRAMMAR:
EVIDENCE → REQUIRED VISUAL PROPERTY:
TYPE ROLES + REAL FALLBACKS + ROLE-SPECIFIC MEASURE / WRAP:
FOCAL ANCHOR + MAJOR-REGION COMPOSITION / HIERARCHY:
COLOR ROLES + OPAQUE CONTRAST PAIRS + APPEARANCES:
MATERIAL / EDGE / LIGHT / DEPTH:
MOBILE REORDER-REPLACE-DEFER TABLE:
ONE AUTHORED DISTINCTION OR PRESERVED IDENTITY:
MOTION PURPOSE + FREQUENCY + REDUCED RESULT, OR NONE:
PROHIBITED HIGH-UNCERTAINTY EFFECTS:
```

Translate evidence into required properties before choosing style tokens. Long reading may justify measure and line-height constraints, and night use may justify glare limits; neither justifies a font category, material metaphor, or palette. When evidence is insufficient, inherit proven project values, leave identity decisions unresolved, or choose only the smallest task-safe, replaceable values required to render. Treat fallback as scaffolding, never identity; an authored distinction may remain `none` until evidence supports one.

Prefer product evidence, stable layout primitives, semantic tokens, native controls, explicit aspect ratios, resilient wrapping, and conservative effects. Reuse detected project primitives. Do not add a new dependency, remote font, unstable CSS feature, shader, canvas-only content, dynamic text-over-media, complex blend stack, or crop-dependent meaning without a visual/runtime verifier and fallback.

## Three source passes

1. **Skeleton:** landmarks, heading/order, real content shapes, native controls, links, labels, all required states, no decorative motion.
2. **System:** tokens, type/fallback, grid/container, component state matrix, appearance tokens, declared viewport rules, intrinsic sizing, overflow safeguards, focus and reduced/forced-color paths. When no support matrix is declared, use 320/390/768/1440 only as conservative sampling.
3. **Identity:** only the frozen brand/material/signature; remove any effect not traceable to meaning or safely degradable.

After each pass, inspect the diff against the freeze card. This is self-correction, not independent evidence.

## Browserless checks

Run tools already present or safely resolved by the Skill's automatic tool contract:

- build, typecheck, lint, unit tests, framework static generation;
- HTML/JS/CSS parsing or project compiler checks;
- route/link/asset existence, output allowlist, dependency/license and font-source checks;
- advisory opaque token-pair contrast calculations, explicitly excluding alpha/media/rendered proof;
- source checks for semantic roles, complete state tokens, `color-scheme`, reduced motion, forced colors, focus, intrinsic media dimensions/aspect ratio, logical properties, min/max sizing, wrapping and overflow risks;
- deterministic interaction state tests that do not claim real focus, layout, paint, accessibility tree, touch, IME, or browser behavior.

When browser verification belongs to the requested workflow and browser policy permits the selected engine, the Skill may install an exact pinned browser/verifier into a project-local or evaluator-owned cache. Do not install globally, change application runtime dependencies, use mutable latest versions, upload private code/screenshots, or call an external visual service. If installation is impossible because the sandbox is offline/read-only or authority is missing, keep the page and mark rendered evidence unavailable. If image generation is available but rendering is not, generated art can explore mood; it cannot validate the implemented page.

## Prefer resilient patterns

- Use `minmax(0, 1fr)`, intrinsic sizing, `min-inline-size: 0`, wrapping, `clamp()`, and explicit media aspect ratios where appropriate.
- Avoid fixed content heights, negative-margin dependencies, text baked into images, hover-only access, and absolute positioning for unknown copy.
- Use real locale-shaped copy, long labels, missing/empty content, and representative numbers instead of short lorem ipsum.
- Keep key text and controls on stable opaque surfaces when their background range cannot be measured.
- Ensure mobile changes task priority or interaction, not only column direction.
- Keep no-JS/no-motion/static fallbacks understandable whenever the feature permits it.

These are safeguards, not universal style rules. Preserve intentional project behavior when evidence supports it.

## Handoff for one-pass environments

Return:

1. the frozen direction card;
2. exact files changed and behavior preserved;
3. exact commands and their narrow results;
4. a minimal preview command;
5. the first declared screenshots/states; when no support matrix is declared, start conservatively with 390×844 and 1440×1000, supported appearances, plus one consequential interaction or error state;
6. a risk list labelled `INFERRED` or `UNVERIFIED`.

If no later render is possible, ship only when the user accepts that evidence ceiling and the product's risk allows it. Formal accessibility, high-stakes transaction, security-sensitive overlay, complex motion/media, or award-level visual claims require real browser/human evidence before release.
