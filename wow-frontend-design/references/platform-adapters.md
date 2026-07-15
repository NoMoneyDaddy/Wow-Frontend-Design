# Platform and stack adapters

Use this reference when implementation depends on a framework, rendering model, design system, native client, or version-sensitive API. The universal design contract stays stable; implementation follows the detected platform.

## 1. Establish the actual platform

Record evidence before choosing patterns:

```text
package/workspace → installed version/lockfile → rendering model → router/data model → styling/design system → primitives → test/build commands → deployment constraints
```

- Read the nearest manifest, lockfile, framework config, entry route, global styles, and representative component. In a monorepo, identify the owning package before editing.
- Prefer the installed version's local types, examples, migration notes, and official documentation. Do not assume the newest syntax or an old remembered API.
- Detect server rendering, static generation, islands, hydration, client-only rendering, native rendering, and embedded-webview constraints. Similar component syntax does not imply the same lifecycle.
- Reuse the current router, data layer, form primitives, component library, styling method, icons, i18n, testing tools, and package manager unless a measured problem requires change.
- Treat third-party skills as advice for a named version and stack. Their framework preference is not permission to migrate.

### Route companion skills by installed evidence

External framework skills are optional versioned adapters, not universal instructions. Load one only when the owning package, installed/declaration evidence, rendering model, and task match. Keep its revision and generation date in the run record; prefer installed types/local docs and current official documentation when it conflicts.

| Detected evidence | Conditional adapter | Boundary |
| --- | --- | --- |
| Nuxt 4 project and matching conventions | Nuxt 4 reference for `app/`, route/data/rendering and hydration behavior | never apply Nuxt 4 paths to Nuxt 2/3 or infer auto-import behavior after the project disables it |
| Pinia installed | Pinia store/reactivity/SSR reference | do not add Pinia for visual state; preserve Options/Setup style and avoid request state at module scope |
| `pnpm-lock.yaml` / declared pnpm version | matching pnpm workspace/config/security reference | never switch package managers; do not read or expose `.npmrc` credentials; v10/v11 config locations differ |
| `uno.config.*` / `unocss.config.*` | matching UnoCSS preset/extractor/shortcut reference | inspect enabled presets/transformers first; generated or dynamic class names may need safelisting and build verification |
| Slidev deck | Slidev layout/export/icon reference | this is a presentation adapter, not a normal website default; verify export browser/dependencies and slide aspect ratio |
| repository explicitly adopts an author's personal conventions | that author's opinionated root skill | personal preferences such as auto-import bans, file splitting, aliases, lint config, or catalogs never override existing project conventions by popularity |

Do not fetch mutable companion instructions during an ordinary production run. Install/pin them through the host or record a commit and review their license first. A companion skill can supply stack syntax; this skill retains scope, design, mobile, locale, safety, and evidence authority.

## 2. Adapt without translating idioms blindly

| Platform family | Preserve | Common cross-stack failure |
| --- | --- | --- |
| HTML, server templates, static sites | semantic server output, form/link defaults, progressive enhancement, small scripts | turning a content page into a client app for visual polish |
| React, Next.js, Remix/React Router | existing server/client boundary, route/data ownership, stable hydration, component composition | moving all state client-side, effect-driven derived state, hydration-dependent content |
| Vue and Nuxt | existing Composition/Options style, reactivity ownership, route/data conventions, scoped/global style contract | copying React hooks and stale-closure fixes into a different reactivity model |
| Svelte and SvelteKit | installed-version idioms, load/action boundaries, compiler-driven state, scoped styling | mixing syntax from another major version or adding a state library without need |
| Angular | template semantics, forms choice, dependency injection, router, change-detection strategy, existing component kit | bypassing framework primitives with ad-hoc DOM mutation |
| Astro, Qwik, and island architectures | static HTML, explicit hydration boundaries, minimal client payload, server-safe code | hydrating an entire page for one interaction |
| Design-system/component-library project | public component API, tokens, variants, focus/keyboard contract, composition | restyling internals with fragile selectors or replacing accessible primitives |
| Native React Native, SwiftUI, or other client UI | platform navigation, accessibility API, safe areas, text scaling, input/gesture conventions, lifecycle | pasting DOM/CSS/ARIA code or web breakpoints into a native interface |

For a platform not listed, infer the same boundaries from its official model. Label any version-sensitive claim `UNVERIFIED` until local or official evidence supports it.

## 3. Keep product state above visual effects

- Derive visual state from product state. Do not store the same truth independently in CSS classes, animation instances, URL state, and component state.
- Keep shareable/navigation state in the router when the product expects refresh, Back/Forward, or deep links. Keep transient presentation state local.
- Cancel or supersede stale requests, transitions, observers, subscriptions, and optimistic updates on new input or teardown.
- Preserve server validation and authorization. Client validation and disabled buttons improve feedback; they do not establish trust.
- Cover loading, empty, partial, error, permission, offline, retry, success, and stale-data states only where the workflow can actually enter them.

## 4. Treat delivery details as interface quality

For public routes, verify as applicable:

- unique, truthful title and description;
- canonical and locale alternates derived from real routing policy;
- Open Graph/social media whose dimensions, crop, language, and content match the page;
- structured data that describes real visible content—never invented ratings, prices, availability, or organization facts;
- correct document language and direction during SSR and after locale changes;
- reserved image/media dimensions, responsive sources, font loading/fallback, and no hydration mismatch;
- error/not-found routes, loading boundaries, and share/back/refresh behavior.

Metadata, SEO, and social cards are stateful product surfaces, not copy-paste boilerplate.

## 5. Add dependencies only with a boundary

Before installing a library, record:

```text
requirement not met by current stack → candidate/version → size/runtime/license → SSR/native support → accessibility/lifecycle → fallback → removal cost
```

- Prefer existing dependencies and official platform features.
- Never add a second styling, form, animation, icon, state, or component system for one small effect.
- Pin or lock the chosen version through the project's existing package policy. Do not fetch mutable CDN code for production by default.
- Review package, plugin, icon/data collection, editor/export, and commercial runtime licenses separately.
- Use the repository's package manager and lockfile. Do not run an unpinned `npx ...@latest`, change lockfile family, enable lifecycle scripts, or query the network only because a third-party skill recommends its preferred tooling.
- Missing verification-only tooling may be installed automatically when the task requires the check. Respect existing pins; otherwise resolve the official latest stable non-prerelease that passes runtime compatibility, freeze its exact version for the run, isolate it from product runtime dependencies, verify the executable, record provenance, and resume. CI/benchmark/baseline runs keep their pre-frozen exact toolchain. A transient download/registry error is retryable; an offline/read-only sandbox becomes a scoped evidence limit.
- In utility-CSS systems, verify extraction against real source and production builds. Runtime-composed classes, CMS/AI strings, icon collections, shortcuts, attributify syntax, and variants may require explicit safe lists or may be unsuitable; do not hide missing production CSS with a development-only result.

## 6. Verify in the platform's own terms

- Discover commands from manifests and CI; do not invent `npm test`, a build flag, or a deployment target.
- Run the narrowest relevant typecheck/lint/test/build, then the full project gate proportionate to risk.
- Test server render plus hydration when both exist; direct navigation plus client navigation; refresh, Back/Forward, error boundaries, and teardown/remount.
- Use the project's component-test and browser stack when present. An isolated story or snapshot does not prove a routed workflow.
- Native clients require their simulator/device accessibility, text-scale, orientation, keyboard, safe-area, memory, and reduced-motion tests. Web WCAG checks remain valuable design input but do not substitute for platform accessibility verification.

Release blockers:

- undocumented framework migration or parallel architecture;
- syntax/API from a different installed version;
- essential content or metadata produced only after fragile client hydration;
- visual change that breaks routing, state ownership, SSR, tests, or native conventions;
- claiming “all platforms” from one browser or one framework fixture.
