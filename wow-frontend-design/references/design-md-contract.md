# DESIGN.md contract

Use this contract for implementation work that creates or changes a project's visual system. `DESIGN.md` preserves visual intent across routes, sessions, agents, and tools; it does not replace route planning, wireflows, runtime components, or browser evidence.

Follow the [Google Labs DESIGN.md specification](https://github.com/google-labs-code/design.md/blob/main/docs/spec.md). The format is currently alpha, so pin the CLI version in the project before making lint or export results release gates.

Treat the machine-readable frontmatter as a small constrained DSL: parse/schema/reference/contrast errors are deterministic domain diagnostics that should return directly to the automatic repair loop. Keep unsupported effects, responsive behavior, localization, and rationale in prose instead of growing an ad hoc token language. This follows the general LLM/DSL boundary described by [Martin Fowler and Unmesh Joshi](https://martinfowler.com/articles/llm-and-dsls.html): let the model propose within a bounded language, then let deterministic tooling parse and reject invalid structure.

Use the official examples only to understand structure, not as aesthetic recipes: [Atmospheric Glass](https://github.com/google-labs-code/design.md/blob/main/examples/atmospheric-glass/DESIGN.md), [Paws & Paths](https://github.com/google-labs-code/design.md/blob/main/examples/paws-and-paths/DESIGN.md), and [Totality Festival](https://github.com/google-labs-code/design.md/blob/main/examples/totality-festival/DESIGN.md).

## Ownership

- Place one canonical `DESIGN.md` at the repository root unless an established monorepo convention proves that separately shipped brands need separate roots.
- For a new visual system, create it after the design thesis and before page composition.
- For an existing product, extract approved tokens, components, and rationale from production sources. Do not overwrite evidence with a new aesthetic guess.
- For an audit, read and compare the file without mutating it. For a focused repair that neither changes the system nor has an existing file, do not manufacture unrelated documentation.
- Treat token frontmatter as normative visual values. Treat prose as rationale and application guidance. Runtime shared tokens and components implement the contract; page-local copies do not.

## Required shape

Keep optional YAML frontmatter followed by the applicable canonical sections in this order:

1. `Overview`
2. `Colors`
3. `Typography`
4. `Layout`
5. `Elevation & Depth`
6. `Shapes`
7. `Components`
8. `Do's and Don'ts`

Use frontmatter for machine-readable color, typography, spacing, rounded, and component tokens supported by the pinned specification. Use `{group.token}` references instead of copying values when a component consumes an existing token. Keep responsive composition, localization behavior, motion purpose, data-visualization encodings, and page-specific exceptions in concise prose when the alpha token schema cannot represent them safely.

Use only these typography properties in frontmatter: `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing`, `fontFeature`, and `fontVariation`. Use only `px`, `em`, or `rem` for dimension tokens. Use a numeric or quoted numeric `fontWeight`; `lineHeight` may also be unitless.

Zero is not exempt from dimension syntax: write `letterSpacing: "0em"`, `rounded: "0px"`, or another valid unit-bearing zero where the property is dimensional. A bare or quoted `0` is invalid for `letterSpacing`, spacing, rounded, width, height, size, and component padding. Do not copy unitless CSS shorthand into the token schema.

Use only these component sub-tokens: `backgroundColor`, `textColor`, `typography`, `rounded`, `padding`, `size`, `height`, and `width`. Express hover, active, pressed, or other variants as separately named component entries. Put borders, shadows, blur, tracking rules, responsive transformations, and other unsupported details in the Markdown body instead of inventing YAML properties. If component tokens add no value, omit `components` rather than creating invalid fields.

Define `colors.primary` whenever colors exist. Reference defined colors from components when components exist. Remove genuinely unused tokens instead of accepting avoidable orphan warnings. Never copy the values from `assets/DESIGN.template.md`; it is a syntax example, not a default brand.

Quote the entire YAML scalar when a value contains commas, colons, `#`, braces, or a CSS font stack. For example, write `fontFamily: "SF Mono, Monaco, monospace"`; do not quote only the first family. YAML parsing warnings are contract failures even when the linter can recover.

The official color token accepts a valid CSS color string, including CSS Color 4 forms such as quoted `oklch()` values:

```yaml
colors:
  primary: "oklch(57% 0.18 254)"
```

This is compatible with the `DESIGN.md` syntax. It is not universal runtime compatibility. Preserve an sRGB fallback in production CSS when the support matrix requires it, gamut-test the target displays/browsers, and measure the resolved rendered pair. The linter converts supported colors to sRGB for its WCAG calculation while preserving the original token; that still cannot prove page compositing, alpha/media backgrounds, browser gamut mapping, or actual runtime token consumption.

Before closing frontmatter, perform this manual preflight even when command execution is unavailable:

1. every dimensional value, including zero, has an allowed unit;
2. every font stack is one wholly quoted scalar;
3. `colors.primary` exists and every declared color is referenced by a valid component entry or removed;
4. each component `textColor`/`backgroundColor` pair reaches 4.5:1 for normal text;
5. every reference resolves and every component key is on the supported whitelist.

This preflight reduces syntax mistakes; it does not turn an unexecuted official lint into a verified pass.

## Multi-page consistency

- Make every route consume the same shared CSS variables, theme configuration, and component primitives.
- When pages must be self-contained, repeat one byte-equivalent root-token block and shell primitive set across them; page-local CSS may compose content but must not redefine system values.
- Keep the same semantic role visually consistent across pages and breakpoints. A route may change composition, not redefine the brand.
- Record justified campaign or route exceptions in `DESIGN.md`; do not create an undocumented second system.
- Update `DESIGN.md` and runtime tokens in the same change when a system value changes.
- Keep a conformance map from every normative color/type/spacing/component role to the shared runtime token or primitive. Compare computed values on representative routes, states, and viewports after implementation.
- Treat clean lint as one-way syntax validation, not round-trip conformance. Detect runtime drift in both directions: every normative `DESIGN.md` role must resolve to rendered tokens/components, and any repeated runtime system value must either map back to the contract or be documented as a route exception.
- Use `site-manifest.json` for routes and content ownership, and `wireframe-plan.json` for page regions and responsive transformations. `DESIGN.md` owns visual identity, not IA.

## Verification

Prefer a project-pinned command, for example:

```bash
npx @google/design.md@0.3.0 lint DESIGN.md
```

For a new generated system, require zero errors and zero warnings. An extracted existing system may retain a warning only when the reason and migration owner are documented. Also compare representative routes at desktop and mobile sizes. A clean document cannot prove that rendered pages actually consume its tokens or remain visually consistent: state-specific CSS may contradict a documented one-column mobile rule, and page-local type may override the documented line height without creating a lint warning.

Resolve lint findings in this order, re-running the pinned linter after each pass:

1. YAML parse and scalar quoting.
2. Broken token references and unknown frontmatter properties.
3. Missing `primary` and orphaned tokens; reference intentional tokens from valid component entries or remove them from frontmatter and explain the styling rule in prose.
4. Component foreground/background contrast warnings; adjust the normative values rather than hiding the component.
5. Section order and other remaining warnings.

When an isolated generation attempt fails this gate, preserve the bounded linter summary and provide it to the automatic implementation repair loop as untrusted diagnostic context. Do not ask the user to resubmit, weaken or edit the pinned validator, silently accept warnings, or let the implementation model install a different CLI. Freeze the contract, template, linter version, validator, and runner hashes for the full evaluation run.

Do not declare the design contract complete until the final run is clean. If tools prevent the run, report `DESIGN.md lint: UNVERIFIED` and preserve the file for a later verifier.
