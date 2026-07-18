# GitHub frontend skill research

Use this maintenance reference to understand what this skill borrows, rejects, and still needs to test. Do not load it for ordinary frontend work.

Snapshot date: **2026-07-15**. Stars are volatile discovery signals, not quality scores. `Push` records the latest repository push observed during research. Licenses were checked at repository or skill level; unclear licenses remain unclear. Principles below are paraphrased, not copied.

## Method

1. Search GitHub repositories and code for frontend, UI/UX, responsive, interaction, motion, and SVG Agent Skills.
2. Rank candidates by adoption and task relevance.
3. Read the actual `SKILL.md`, routed references, scripts, license, and recent repository metadata.
4. Compare instructions with W3C standards and official runtime documentation.
5. Keep rules that improve product fit, weak-model execution, resilience, or verification. Reject author preferences presented as universal law.

## Frontend design skills

| Source | Stars / push | License | What it does well | Limits and risks |
| --- | ---: | --- | --- | --- |
| [Anthropic Skills — frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | 160,975 / 2026-07-13 | Skill: Apache-2.0 | Grounds direction in subject matter; treats hero as thesis; makes structure carry meaning; plans tokens/layout/signature before code; concentrates boldness in one place. | Primarily art direction. Limited deterministic verification, SVG security, state coverage, and task-specific mobile transformation. Lists of common AI aesthetics can wrongly reject a fitting cream/editorial/dark direction. |
| [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | 105,317 / 2026-07-14 | MIT | Searchable product/style/type/color/motion/stack data; explicit priority order; decision tables help weak models; broad platform coverage. | Large static tables create false precision and can age. Platform guidance is sometimes mixed. Lookup-driven styling can become stereotype-driven design or a palette recommender. |
| [Addy Osmani Agent Skills](https://github.com/addyosmani/agent-skills/tree/main/skills/frontend-ui-engineering) | 78,077 / 2026-07-12 | MIT | Strong engineering bridge: state ownership, loading/empty/error coverage, component boundaries, concrete viewport checks, anti-template guidance. | React/Tailwind bias; some fixed size/line-count rules are mechanical; older accessibility references and mobile examples can still collapse to stacking. |
| [Wshobson Agents — UI Design](https://github.com/wshobson/agents/tree/main/plugins/ui-design/skills) | 37,888 / 2026-07-14 | MIT | Separates visual, responsive, and interaction concerns; content-driven breakpoints; container queries; logical properties; motion purposes such as feedback and continuity. | Many generic framework snippets. Fixed duration recipes and blanket `0.01ms` reduced-motion CSS do not guarantee an equivalent result. Source rules occasionally simplify WCAG details. |
| [Vercel Agent Skills — web-design-guidelines@f8a72b9](https://github.com/vercel-labs/agent-skills/tree/f8a72b9603728bb92a217a879b7e62e43ad76c81/skills/web-design-guidelines) | 29,048 / 2026-07-07 | Skill repo: unclear; fetched rule source: MIT | Terse `file:line` findings; useful candidate checks for semantics, labels, focus, URLs, safe areas, hydration, images, long content, reduced motion, and CLS. | Its 39-line Skill fetches a second mutable `main` document at review time. Review-focused, not a creative-direction or repair system. English copy rules and several blanket performance/layout fixes do not transfer safely to every locale, browser, or product. |
| [Huashu Design](https://github.com/alchaincyf/huashu-design) | 21,388 / 2026-07-02 | MIT | Verifies real product/brand facts and assets; prefers honest placeholders over invented claims; gets evidence-bearing images before composition; asks for visual browser inspection. | Very large context cost; workflows can overreach into assets, watermarking, or subagents; explicitly less suited to production applications; remote brand assets still need provenance and license review. |
| [Google Stitch Skills](https://github.com/google-labs-code/stitch-skills) | 7,352 / 2026-07-13 | Apache-2.0 | Extracts a design source of truth; keeps structure prompts separate from tokens; targeted edits beat full regeneration; variants change named axes while holding others fixed. | External-service dependency. Taste rules include aggressive defaults such as constant animation or forced mobile stacking that do not generalize. |
| [Ibelick UI Skills](https://github.com/ibelick/ui-skills) | 3,677 / 2026-07-13 | No repository license detected at pinned revision | Clean progressive disclosure; routes topic → current stack → most specific skill; minimal accessibility fixes with concrete snippets; native semantics first. | Reuse rights are unclear; study and independently paraphrase only. Strong Base UI/Tailwind/Motion preferences; many author opinions are written as absolutes; duration/truncation rules are not universally valid. |
| [GoodUX Skills](https://github.com/zz41354899/goodux-skills/tree/c1a1fc9ae9c275abb0c86d114ab654285fd68bff/.agents/skills) | not used / 2026-07-14 | Skill subtree: MIT; root unclear | Separates research stages; rejects invented personas; connects interviews, IA validation, and realistic usability tasks to evidence. | Fixed sample/persona/variant counts and Next.js/Shadcn/Tailwind assumptions are not universal. The style catalogue encourages stereotype lookup; several routed paths are broken; installer mutation requires separate review. |

## UI Skills registry review

[UI Skills](https://www.ui-skills.com/skills) described itself as a registry of 140 skills on the snapshot date. It is useful for discovery, not evidence that every listed instruction is correct, current, compatible, licensed, or suitable for this skill. Resolve every useful entry to its source repository, then check its revision, license, routed references, and claims before adoption.

The exhaustive canonical-source matrix, stale-link audit, topic counts, and per-repository value/boundary review live in [ui-skills-ecosystem.md](ui-skills-ecosystem.md). The matrix covers all 47 canonical sources rather than only the visually obvious entries.

The full registry was classified by relevance rather than copied into the core prompt:

| Class | Treatment in this skill |
| --- | --- |
| Visual direction, responsive adaptation, typography, color, interaction, motion, accessibility, performance, hardening, audit, and browser testing | Inspect representative skills; convert durable ideas into project-neutral contracts and executable checks. |
| React/Vue/Svelte/Next/Three.js or component-library instructions | Load only when the detected project uses that stack or the task requires it. Do not pollute the universal core. |
| Slides, video, Web Audio, cloning, framework migration, and unrelated engineering routers | Out of scope unless the user's task explicitly enters that domain. |

Representative source audit:

| Source / registry entries | Stars / push | License | What is worth adopting | What must not become a universal rule |
| --- | ---: | --- | --- | --- |
| [Ibelick UI Skills](https://github.com/ibelick/ui-skills): root router, baseline UI, accessibility, metadata, motion performance | 3,677 / 2026-07-13 | No repository license detected at pinned revision | Route to the smallest relevant instruction set; keep the current stack; cite exact violations; batch reads before writes; pause off-screen motion; distinguish layout, paint, and composite work. | Study and paraphrase only. “Transform/opacity” is a starting point, not proof of performance. Hard blur caps, bans on particular mechanisms, and author tooling preferences still require device traces and project context. |
| [Impeccable](https://github.com/pbakaus/impeccable): adapt, audit, harden, impeccable, overdrive | 46,484 / 2026-07-13 | Apache-2.0 | Ask for platform and use context; test empty/error/permission/offline and long/RTL/CJK content; separate measurable audit from taste critique; match wow to marketing, application feedback, data, or invisible performance; iterate in a browser. | AI-aesthetic scores are subjective. Industry palette scripts, universal touch/duration formulas, and “anti-pattern” lists can punish a fitting direction. Its blanket `0.01ms` reduced-motion recipe is incomplete, and simplified text-size claims must be checked against WCAG rather than copied. |
| [Emil Kowalski Skills](https://github.com/emilkowalski/skills): animation vocabulary, design engineering, animation audit | 12,550 / 2026-07-11 | MIT | Name the actual motion pattern; choose purpose and frequency before timing; preserve physical continuity; make gestures interruptible; audit the entire motion system instead of polishing one isolated transition. | Fixed duration bands, mandatory custom easings, blanket keyboard-animation bans, and one treatment for every button are preferences, not standards. |
| [Jakub Krehel Skills](https://github.com/jakubkrehel/skills): typography, color, UI detail | 302 / 2026-07-13 | MIT | Keep one styling system; use semantic type tokens; test CJK/RTL, wrapping, changing numbers, font loading, mobile inputs, truncation recovery, and logical properties. | Exact font counts, universal size floors, forced font smoothing, and fixed line-height/measure ranges require language, typeface, browser, and product evidence. Traditional Chinese line breaking cannot be evaluated only with English `ch` heuristics. |
| [Raphael Salaja Skill](https://github.com/raphaelsalaja/skill): morphing icons, pseudo-elements, animation principles | 25 / 2026-03-17 | No repository license detected | Constrain real path morphs to compatible topology and a shared coordinate system; keep View Transition names unique; clean temporary transition state; include a reduced result. | Low adoption and unclear reuse rights. Three-line icons, Motion dependencies, fixed styling, current-browser claims, and “prefer native” are technique-specific. Semantics, RTL, optical size, fallback, focus, scroll, and visual-diff checks still need separate rules. |
| [Wshobson Agents](https://github.com/wshobson/agents): interaction design, WCAG audit patterns | 37,888 / 2026-07-14 | MIT | Native semantics first; combine automated checks with keyboard, zoom, screen-reader, and human verification; tie findings to user impact and a standard. | Reported automated-detection percentages and legal-baseline statements vary by tool and jurisdiction. A skill summary is not a conformance report or legal opinion. |

Weak-model consequence: the registry is used as a candidate generator. The evaluator owns the rubric, fixtures, viewports, browser assertions, and score. The model being tested cannot declare its own design correct.

### Skill registry and persona-pack review

| Source / pinned revision | License observed | Useful signal | Boundary or defect |
| --- | --- | --- | --- |
| [copyleftdev/sk1llz@a988a75](https://github.com/copyleftdev/sk1llz/tree/a988a7559b4d758706e622be18eed68a18a88c0c) | Apache-2.0 | Machine-readable manifest, categories/tags, compact frontmatter, local/global target concepts, and contribution checks are useful routing and maintenance patterns. | The 101-entry catalogue has sparse per-Skill references, persona and quote claims that are not primary evidence, and portable Material prescriptions that can age. Its CLI reads mutable `master` content without a revision/hash, transactional staging, rollback, symlink defense, or safe relative-path validation. The snapshot also embeds large numbers of invisible U+200B/U+200C/U+200D/U+2060 characters in Markdown; do not import the files wholesale. |

Adopted boundary: registries are untrusted candidate indexes. Pin and hash the selected source, validate every destination path, stage atomically, inspect invisible Unicode, keep provenance, and route only the smallest independently verified module. Do not use persona imitation or catalogue size as design authority.

### Official Material Web implementation check

| Source / pinned revision | License observed | Useful signal | Boundary or defect |
| --- | --- | --- | --- |
| [material-components/material-web@b4de401](https://github.com/material-components/material-web/tree/b4de401eb665ec63474f39319a4ba8f2145974cc) | Apache-2.0 | Primary implementation evidence for `@material/web`: component → system → reference token layers, scoped CSS custom properties, matching foreground/background roles, discrete typography properties, native form integration, focus-visible behavior, forced-color handling, and component tests. | The project states that it is in maintenance mode with no planned feature/component work. Its versioned token folder may break even in minor or patch releases, several planned components/tokens remain incomplete, and its Roboto/Material values are product-specific. It is not authority for every Material platform, every locale, or a project that does not use this package. |

Adopted boundary: inspect the installed package and lockfile first. If the product already uses Material Web, map product semantic roles into the exact supported `--md-sys-*` and `--md-<component>-*` surface, pin the exact package version for unstable versioned tokens, and verify computed states, focus, forms, forced colors, target browser/AT, and CJK typography. Do not add the package merely to imitate Material styling, and do not copy values or APIs from mutable `main`.

### Official shadcn/ui and mutable audit-rule check

| Source / pinned revision | License observed | Useful signal | Boundary or defect |
| --- | --- | --- | --- |
| [shadcn-ui/ui@3a12463](https://github.com/shadcn-ui/ui/tree/3a124632a6afa16afe127351d5bec85b402b2a86) and its [official Skill](https://github.com/shadcn-ui/ui/blob/3a124632a6afa16afe127351d5bec85b402b2a86/skills/shadcn/SKILL.md) | MIT | Treats shadcn as open project-owned source rather than an opaque dependency; inspects `components.json` and exact CLI project info; distinguishes Radix/Base, icon library, aliases, Tailwind and installed components; uses `view`, `--dry-run`, and `--diff` before mutation; preserves local composition and requires approval before overwrite/preset replacement. | These are framework-adapter rules, not universal design law. “Beautiful defaults” do not prove product distinction. The five official eval prompts check generated structure/text but provide no browser run, screenshot, Traditional Chinese/RTL, assistive-technology, cross-browser, registry-security, or performance evidence. |
| [Vercel web-design-guidelines Skill@f8a72b9](https://github.com/vercel-labs/agent-skills/blob/f8a72b9603728bb92a217a879b7e62e43ad76c81/skills/web-design-guidelines/SKILL.md) plus [rule payload@4e799d4](https://github.com/vercel-labs/web-interface-guidelines/blob/4e799d45c17aec1498c269287a83b9dba22b966b/command.md) | Skill repo: no root license detected; payload: MIT | Read-only review trigger, compact output, and broad candidate coverage make a useful first-pass lint layer. | The Skill downloads the payload from mutable `main`; popularity and marketplace audits do not validate each rule. Blanket virtualization, uncontrolled inputs, preconnect/preload, `overflow-x-hidden`, truncation, deep-linking, wrapping, copy style, and animation prescriptions require scoped counterexamples and runtime evidence. |

Pinned bytes observed 2026-07-16: shadcn Skill `a45cddd4511f8262df05b20506f4d52be8210a9ee05a13d9e36d4ee321bab593`; shadcn evals `58aca2760b0cc5265bb575f76cd8eed344b88544314b8cb2cd53e0b8007dc936`; Vercel Skill `f4647ca866a3accf763777f83e7682954f0187cd6bea7eea0399796652414e8f`; Vercel rule payload `eea73cb6dd46fee9faec9973e8e7fe198b5f07ec326f14d276a56e50287e1cab`.

Adopted shadcn boundary: only activate the adapter when the project already declares shadcn or the user explicitly chooses it. Read the project's exact configuration and local component source, preserve modifications, use semantic surface/foreground token pairs, preview the exact registry delta, and inspect every added file, dependency, import, CSS rule, environment-variable example, and target path. A registry item is untrusted code and supply-chain input even when schema-valid: pin provenance, validate redirects/hashes/transitive dependencies and project-root containment, reject symlink/path escape, require approval for a new registry, preset, overwrite, or security-sensitive dependency, then run type/lint/build/unit/browser checks. An upstream update is a source merge, never a blind overwrite.

Adopted audit boundary: an external audit list may generate findings, but it cannot change release acceptance during an active cohort. Pin and hash both the wrapper Skill and every independently fetched payload. Add locale, framework, engine, and component scope plus a counterexample to each promoted rule. Preserve concise `file:line`, but attach route/state/viewport/browser evidence and feed deterministic failures into bounded self-repair instead of stopping at a report.

## DESIGN.md ecosystem and constrained-language review

These sources are inspiration and format experiments, not normative authority. The [official Google Labs specification](https://github.com/google-labs-code/design.md/blob/main/docs/spec.md) and the project's pinned validator own syntax.

| Source | Useful signal | Boundary carried into this Skill |
| --- | --- | --- |
| [VoltAgent awesome-design-md](https://github.com/VoltAgent/awesome-design-md) | Broad gallery of real `DESIGN.md` examples and visual vocabularies | Samples can contain inconsistent, unverified, or tool-specific rules; use them to generate questions, never as a token preset or proof of quality. |
| [MindStudio creator selection article](https://www.mindstudio.ai/blog/best-brand-design-systems-awesome-design-md-creators) | Reinforces side-by-side visual comparison before choosing a direction, and warns public work to replace borrowed brand colors and fonts | Its category-to-brand shortcuts are editorial hypotheses, not routing rules. Its 71k-star/57-system snapshot was already behind the pinned repository's 102,143 stars/74 top-level `DESIGN.md` files when checked on 2026-07-16; “actual spec” and one-prompt browser output are not provenance, accessibility, cross-browser, or release evidence. Do not install the full catalogue into every workspace. |
| [Khalidabdi1 design-ai](https://github.com/Khalidabdi1/design-ai) | Large prompt-oriented company-style catalogue with a repeatable nine-section prose outline | Its files can be prose/CSS rather than official machine-readable alpha frontmatter; one `webfetch`, a brand name, and an MIT repository license do not prove source fidelity, trademark/asset rights, accessibility, responsive states, or official-schema validity. Use as discovery only. |
| [designmd.app](https://designmd.app/) | Large browsable catalogue makes comparison and discovery efficient | Catalogue inclusion and self-description are not lint, runtime conformance, accessibility, license, or visual-verification evidence. |
| [bergside awesome-design-skills](https://github.com/bergside/awesome-design-skills) | Pairs design documents and Agent Skills, exposing useful routing patterns | Many entries are shallow or schema-divergent; inspect source/license and independently validate every borrowed rule. |
| [Refero DESIGN.md template](https://styles.refero.design/design-md/design-md-template) | Concise section ordering and specific material/type language | Decorative hairlines and style values remain contextual; a `0.5px` rule is not portable until DPR/zoom and semantic role are tested. |
| [LLMs and DSLs](https://martinfowler.com/articles/llm-and-dsls.html) | Separates model-assisted abstraction from deterministic parsing/schema/typechecking | Keep official frontmatter small and strict; route parser diagnostics into automatic repair, and put unsupported effects/responsive rationale in prose instead of inventing YAML. |

The gallery's [Apple analysis](https://github.com/VoltAgent/awesome-design-md/tree/main/design-md/apple) is a useful counterexample as well as inspiration. Its role-named type tokens, display/text separation, responsive hero ladder, component references, and explicit known-gaps section are reusable documentation patterns. Its current frontmatter also contains unitless dimensional zeros that conflict with the pinned official linter contract, and its prose contains internal weight inconsistencies. Fixed Apple tracking, proprietary-font substitution, micro-legal size, breakpoint, and product-copy claims are not portable to `zh-Hant`. Preserve the questions and structure; regenerate and lint project-owned values.

The pinned Notion, Claude, Stripe, and Uber READMEs contain only a three-line redirect to `getdesign.md`; they do not substantiate the MindStudio use-case labels. Their accompanying `DESIGN.md` files are explicitly “Inspired” analyses with useful role separation, responsive-collapse notes, touch-target hypotheses, font-license caveats, and known gaps, but also contain brand-specific values and categorical prescriptions. At capture time all four redirected preview pages rendered only “Something went wrong” in Chrome. A redirect, broken preview, repository popularity, or polished prose must therefore reduce confidence, not silently promote the sample into a canonical spec. Route by the user's task, content, locale, assets, constraints, and observed runtime behavior; compare only a small relevant candidate set, then rebuild project-owned tokens and verify the exact output.

The requested `npx getdesign@latest add` capture resolved to npm `getdesign@0.6.24` (registry integrity `sha512-PMoplVmv9jhgaGWYFnO6n1hTehNXgXUxHXEO+VepPiiGgFLFbtBe+h0JSVoJ05OWjLHXrzLRo8VKjpLOA7Ujgw==`). Six downloaded samples all failed the project's pinned official `@google/design.md@0.3.0` clean gate: Mastercard had no YAML contract; Apple had 8 warnings; Claude 19; Stripe 11; Uber 21; Notion 30. Findings included insufficient declared contrast, unused tokens, unsupported component sub-tokens, and a `Stripi` identity typo. Mastercard, Apple, and Claude bytes matched the pinned repository revision, while Stripe, Uber, and Notion matched neither that revision nor current repository `main`. Treat npm tags and repository revisions as separate mutable supply chains: record the resolved package version/integrity and file hash, lint before activation, and never let `latest` silently become the project contract.

Catalogue size is not evidence density. Sampling the current `design-ai` Apple file shows a coherent prose outline but no official frontmatter, deterministic references, capture date per claim, interaction/error-state evidence, or lint result. Do not copy a company file into the project root as instructed by the catalogue. Extract only project-relevant hypotheses, replace brand/trademark/assets with authorized product evidence, generate canonical tokens under [design-md-contract.md](design-md-contract.md), and validate the exact runtime.

Adopted boundary: a clean `DESIGN.md` is necessary contract evidence, not runtime proof. Maintain a role-to-runtime-token map and compare computed values in default and interaction states at mobile and desktop widths. A state selector can violate a documented mobile column rule, and a local paragraph rule can violate documented leading while official lint remains clean.

## Evidence from model-tier testing

[Anthropic Skills PR #210](https://github.com/anthropics/skills/pull/210) describes a community A/B study across 50 prompts and three model tiers using anonymized screenshots and a blind judge. Its reported direction—explicit guidance helping the smaller model most—is useful, but the judge was still a model and the change was not a universal benchmark.

Adopt the stronger method:

- fixed briefs spanning product categories and user contexts;
- same tools, skill version, budget, viewports, and evaluator rules;
- hidden functional checks plus anonymized screenshots;
- independent browser evidence and human review for subjective craft;
- report ties, failures, infrastructure blocks, and sample size—not only wins.

## WebGL and Three.js skill review

These are research coordinates, not vendored dependencies. README license claims do not replace a repository `LICENSE`; no-license material is studied and independently paraphrased only.

| Source / pinned revision | License observed | Useful signal | Boundary or defect |
| --- | --- | --- | --- |
| [CloudAI-X/threejs-skills@b1c6230](https://github.com/CloudAI-X/threejs-skills/tree/b1c623076c661fc9b03dac19292e825a5d106823) | No repository license detected; README claims MIT | Topic taxonomy, instancing/LOD/compressed assets, basic disposal reminders | Targets `r160+`, lacks full context-loss/static-fallback/security lifecycle, treats risky `preserveDrawingBuffer`/power preference as defaults, and uses post-processing APIs that later changed. |
| [dgreenheck/webgpu-claude-skill@af2319b](https://github.com/dgreenheck/webgpu-claude-skill/tree/af2319bd01bb7cc881267a9ef42cafdaf5e9029d) | No repository license detected; README claims MIT | Feature/limit checks and device-loss thinking | WebGPU loss does not implement WebGL context loss; private renderer internals and repeated-init cleanup are risky. |
| [PlayableIntelligence/game-creator@4e64b83](https://github.com/PlayableIntelligence/game-creator/tree/4e64b83b5fe400b34ad3a484d9b4a6090b26d512) | No repository license detected; docs claim MIT | Measure before deciding on instancing | Fixed object-count/performance multipliers came from one M1 Pro/SwiftShader environment and cannot become device tiers. |
| [Threejs Awesome Graphics Skills@4013721](https://github.com/scottstts/Threejs-Awesome-Graphics-Agent-Skills/tree/40137219958c88a7413b9417ceae3f893a1518e8) | Root MIT; package declares `MIT AND GPL-3.0-only`; some bundled-source provenance unclear | Strong fixed seed/camera/DPR image pipeline, screenshot regression and render-target diagnostics | Mixed/unclear rights prevent wholesale integration; context loss and runtime security still incomplete. |
| [TerminalSkills@dbbb6f0](https://github.com/TerminalSkills/skills/tree/dbbb6f0c4b4b480f38c0ede5efb6d718770ae1ef) | Apache-2.0 | Basic WebGL/Three taxonomy with clear repo license | Claimed WebGL1 fallback conflicts with a WebGL2-only implementation; lacks complete cleanup, loss, CORS and poster contracts. |

Adopted synthesis: pin the Three minor; capability-test; keep a semantic static poster until a successful first frame; own one render loop; make teardown idempotent; rebuild after context restoration; treat GPU assets/shaders as untrusted; tier quality from target-device traces rather than UA, fixed DPR or copied object thresholds. Current Three.js behavior must be checked against its own release/docs during implementation.

## Motion, cloning, and immersive-skill review

| Source / pinned revision | License observed | Useful signal | Boundary or defect |
| --- | --- | --- | --- |
| [LottieFiles motion-design-skill@f9a8a04](https://github.com/LottieFiles/motion-design-skill/tree/f9a8a041b85185ee4881b3471d3415e939aac772) | MIT | Purpose/emotion/narrative questions, frequency-aware choreography, named motion patterns, context/reduced-motion prompts | Fixed personalities, timing bands, mandatory secondary/ambient layers, overshoot, and “always three layers” are author hypotheses, not release gates. |
| [freshtechbro claudedesignskills@1da73fe](https://github.com/freshtechbro/claudedesignskills/tree/1da73febff0c3e1dfefc07f8a5ef8f7d1dfdb6cd) | MIT | Progressive disclosure, technology-specific routing, packaged references/scripts/assets, lifecycle examples | Very large duplicated catalogue; 2024–2025 trend labels, mutable CDN samples, UA/device heuristics, fixed budgets, and autoplay/loop examples age quickly and need primary-source verification. |
| [199-biotechnologies motion-dev-animations-skill@3feedfb](https://github.com/199-biotechnologies/motion-dev-animations-skill/tree/3feedfb4dba8adae40fc9a5f9a23e3dda2121205) | MIT | Natural-language trigger description, compact workflow, progressive references, configuration schema and validator | “120fps”, GPU-only, fixed framework/package generations, generic fade-up patterns, and self-reported schema booleans are not performance/accessibility evidence. Private Next router patterns are upgrade-sensitive. |
| [iart-ai web-animation-skills@b6dba3e](https://github.com/iart-ai/web-animation-skills/tree/b6dba3eb759726845a44163ff0bad70dd9e7fbb6) | MIT | Separates accessibility/performance/Lottie/page-transition skills; deterministic seek frames and contact sheets improve visual verification | Standalone HTML is not every product's output contract. Blanket near-zero duration, fixed 60/120fps claims, “transform/opacity only,” and unpinned CDN examples oversimplify semantics, paint/composite cost, and reduced motion. |
| [GreenSock GSAP Skills@aed9cfd](https://github.com/greensock/gsap-skills/tree/aed9cfd3277740755f6bfc1155c7aa645403b760) | MIT for Skill content; GSAP runtime has separate no-charge standard license | Strong API routing for timeline labels/position parameters, scoped React cleanup, top-level ScrollTrigger ownership, refresh after layout change, and pin-child separation | Not a product-motion strategy. It conflicts with current docs on `refreshPriority`, has a Nuxt cleanup hook defect, treats `duration: 0` as the reduced path, and overstates `will-change`, compositor, and numeric-scrub performance. Verify against the installed GSAP version and rendered behavior. |
| [wondelai top-design@326b380](https://github.com/wondelai/skills/blob/326b3801223ad277ae7082ff85435ba1d36e1903/top-design/SKILL.md) | MIT | Concept-before-code, signature moment, density rhythm, related-element choreography, micro-state craft, and performance/reduced-motion prompts are useful candidates for explicit immersive work | Its self-awarded `10/10`, arbitrary category weights, fixed 10:1 type ratio, font/color/easing bans, default smooth scroll and award prediction are not evidence. They conflict with product fit, native scroll, CJK wrapping, mobile transformation, and evaluator independence when treated as universal gates. |
| [TechbyWebCoder Clone_Website@06fb7c3](https://github.com/TechbyWebCoder/Clone_Website/tree/06fb7c3af939bd2acfa69671dbfac8faa1b436f8) | No repository license; README says all rights reserved | Broad clone categories and local asset inventories can inspire evaluation prompts for commerce, streaming, chat, food, and video layouts | Do not copy code or brand assets. It lacks a reproducible reference-capture/diff contract, rights manifest, semantic/accessibility depth, state coverage, and exact visual evidence; educational “clone” labeling is not permission. |
| [deveshpunjabi 3d-website-skill@98f4cd4](https://github.com/deveshpunjabi/3d-website-skill/tree/98f4cd4bfdf4cbb87c0f40d59d681158c490e9a5) | MIT | Purposeful 3D, one-scene restraint, progressive fallback, asset compression, mobile/touch/error/cleanup reminders, eval fixtures | Awwwards comparison, niche palette stereotypes, default dark/glow/particles, UA or hardware-count device decisions, and fixed triangle/byte/FPS budgets can manufacture generic spectacle or false confidence. |

Adopted synthesis: motion is opt-in and frequency-aware; animated icons keep familiar static meaning; runtime selection follows the smallest sufficient tier; deterministic semantic frames, reduced mode, failure fallback, interruption, and cleanup become evidence. Award-oriented skills provide candidate creative heuristics only: official award criteria stay a separate, opt-in evaluator lens, and no implementation model predicts its own award. Clone repositories are candidate test dimensions, never reference truth without capture, rights, interaction, and matched screenshot comparison. 3D remains behind the stricter contract in `advanced-media.md`.

## Skill repository and self-optimization review

| Source / pinned revision | License observed | Useful signal | Boundary or defect |
| --- | --- | --- | --- |
| [netresearch skill-repo-skill@a8c0a25](https://github.com/netresearch/skill-repo-skill/tree/a8c0a25070390e80b771b3bc857619a01c311a6a) | MIT code/templates; CC-BY-SA-4.0 documentation split | Separates human-facing `README.md` from runtime `SKILL.md`; makes references reachable from the core router; turns mechanical requirements into scripts/checkpoints; adds repository, packaging, release, provenance, and failure-verification contracts. | Its file inventory, dual-license policy, SEO rules, marketplace sync, and organization conventions are repository-specific. Adopt the reachability and verification principles, not its headings or prose. |
| [darwin-skill@7c7b790](https://github.com/alchaincyf/darwin-skill/tree/7c7b7909b630dc3b5cbb91bd4bcb1b10bfb1f894) | No repository license detected | Combines structural and behavioral evaluation, compares a baseline with a candidate, uses an explicit keep/revert ratchet, and requests an evaluator independent from the authoring model. | Absolute LLM scores, a fixed rubric, and a fixed size multiplier can reward verbosity or evaluator taste. The repository cannot be copied, and automated Git mutation is inappropriate inside an unrelated user worktree. |
| [Microsoft SkillOpt@57333f3](https://github.com/microsoft/SkillOpt/tree/57333f3406436a90a2b5feec4aad74ddb33d6e85) | MIT | Separates train/validation/test data; gates candidates on held-out validation; preserves best-so-far state, rejected trajectories, edit budgets, and rollback. | It is a dataset/API-backed research optimizer rather than an ordinary per-request runtime. A mutable or model-controlled gate can overfit; semantic-density bonuses are diagnostics, never quality proof. |
| [CodeLove comparison](https://codelove.tw/@tony/post/3jAvJx) | Mutable secondary article | Reinforces with/without-Skill runs, repeated trials, mean/variance, flaky detection, positive/negative trigger cases, and output-based evaluation. | It summarizes tools rather than replacing their pinned source and code. Re-check claims against the exact revision before changing the acceptance contract. |

Adopted architecture: keep one canonical Skill core with triggers, invariants, routing, state transitions, repair behavior, and terminal states. Put detailed domain guidance in directly linked references and fragile deterministic work in scripts. Do not maintain separate `lite` and `full` sources: the orchestrator supplies an external capability profile, while observed tool/schema failures can only downgrade the same workflow. Every Skill edit must beat the current accepted version on frozen regression cases and held-out validation without regressing security, accessibility, maintainability, context cost, or trigger precision.

## Adopted synthesis

1. Product truth, top task, audience context, and real assets precede style.
2. If changing only the product name leaves the thesis intact, redesign it.
3. Structural marks such as `01/02/03` require a real sequence or index meaning.
4. For new builds or broad redesigns, derive the minimum sufficient identity from product evidence; use a signature only when it has a task job, and allow `none` when restraint better protects the product. Focused repair preserves identity and scope.
5. Resolve conflicts in this order: user safety, security, privacy, legal/rights, and data/transaction integrity → accessibility and essential task completion → interaction correctness and resilience → performance → visual novelty. Escalate rather than trade away a higher-order constraint.
6. Product/platform tables are prompts for reasoning, never stereotype lookup.
7. Breakpoints come from content failure, not device names.
8. Mobile needs a transformation table; “everything becomes one column” is not a result.
9. Every data surface covers loading, empty, partial, error, permission, offline, and success as applicable.
10. External dynamic rules record a commit/version; external skill and runtime licenses are separate.
11. A design-system adapter uses the installed package/version and its official implementation; copied persona summaries cannot override it.
12. Audit findings use `file:line — failure — fix`, followed by browser proof for rendered behavior.
13. A weak model cannot accept its own output. Freeze evaluator-owned checks and reconcile every verified claim with evidence.
14. Validation is an internal self-repair loop. Repair-required findings return structured evidence to the implementation model automatically; users receive the best artifact, not an intermediate rejection.

## Explicit rejections

- Star count as a proxy for correctness.
- Fixed aesthetics attached to industries or demographics.
- “Premium” as preloader + custom cursor + smooth scroll + parallax + pinning.
- Banning a popular font, color, or layout when product evidence supports it.
- One universal duration, breakpoint, component line count, or mobile column count.
- Mixing WCAG, Apple HIG, Material, and author preference without labeling scope.
- Fetching mutable external instructions during verification without recording the revision.
- Executing a remote Skill manifest without safe-path, symlink, hash, staging, rollback, and invisible-Unicode checks.
- Copying large blocks from unclear or incompatible licenses.
