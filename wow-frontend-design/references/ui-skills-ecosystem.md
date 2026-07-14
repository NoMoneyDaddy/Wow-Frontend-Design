# UI Skills ecosystem map

Maintenance-only critical review of every canonical source represented by the [UI Skills registry](https://www.ui-skills.com/skills). Do not load this file for ordinary product work and do not copy upstream instructions into the core skill automatically.

Snapshot: **2026-07-14**. Registry source revision: [`173c01a`](https://github.com/ibelick/ui-skills/blob/173c01add287eee975c40cb0e7f6d85a48c9ed75/src/data/registry.ts). The previously reviewed `968be8b…` object disappeared after an upstream history rewrite, so this snapshot was re-resolved and recounted from the current commit rather than silently following `main`.

## Snapshot integrity

- 140 registry entries, 136 unique raw URLs.
- 48 source coordinates in registry data; redirects collapse them to 46 canonical GitHub repositories plus the external `rams.ai` source: 47 canonical sources.
- 129 raw entries were readable. Eleven were stale/404: five AccessLint aliases pointed to one obsolete location; three `vercel-labs/next-skills` entries moved into the Next.js ecosystem; one Remotion path changed; Matt Pocock's `to-issues` and `to-prd` entries were removed/replaced upstream.
- The registry defines 27 topic names but uses 26; `3d` has no entry. It has no first-class `responsive` topic, so responsive knowledge is scattered across `frontend`, `systems`, `craft`, and framework labels.
- Multi-label counts from the actual 140 entries: frontend 85; visual 49; systems 35; tooling 34; interaction 34; testing 33; performance 23; motion 21; accessibility 18; architecture 17; craft 14; Vue 14; taste 11; Three.js 10; video 5; color 5; typography 4; Next.js 3; Nuxt/debugging/code-quality 2 each; remaining used topics 1 each.

The registry is a discovery surface, not a certification, license grant, compatibility promise, or freshness guarantee. Stars are intentionally omitted below.

## Every canonical source

| Source / represented entries | Distinct value worth borrowing | Critical boundary |
| --- | --- | --- |
| [0xdesign/design-plugin](https://github.com/0xdesign/design-plugin) — design-lab | Interview first, explore several isolated axes, collect feedback, then produce an implementation plan. | High user/time cost; temporary variants and cleanup can invade a repo. No license detected. |
| [AccessLint/skills](https://github.com/AccessLint/skills) — registry aliases for accessibility audit/fix | Separate report from repair; compare before/after violations; route mechanical fixes and human judgment differently. | All five registry URLs were stale aliases; current skills and tool dependency differ. No license detected; browser/MCP output is not conformance. |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) — frontend UI engineering | Connect component/state architecture, complete states, design systems, accessibility, and viewport checks. | React/Tailwind bias and several arbitrary size/complexity heuristics. |
| [addyosmani/web-quality-skills](https://github.com/addyosmani/web-quality-skills) — web quality audit | One prioritized report across performance, accessibility, SEO, and platform practice. | Lab tools and issue counts do not establish field performance, user impact, or WCAG conformance. |
| [antfu/skills](https://github.com/antfu/skills) — 17 Vue/Nuxt/tooling skills | Ecosystem router, specific version/tool commands, and progressive reference loading. | Strong author conventions and version sensitivity; several entries overlap Vue/Vercel sources. |
| [anthropics/skills](https://github.com/anthropics/skills) — frontend/canvas design | Derive a visual thesis from the subject; brainstorm → plan → critique → build → critique; preserve originality. | Taste remains subjective; anti-default rules may fight a valid design system. Canvas skill targets static artifacts. |
| [arifszn/slide-wright](https://github.com/arifszn/slide-wright) — slide-wright | Confirm a two-slide preview before producing the whole deck. | Useful human checkpoint, but presentation-specific and unsuitable for unattended batch work. |
| [bencium/bencium-marketplace](https://github.com/bencium/bencium-marketplace) — innovative UX designer | Ask for context and choose a clear visual register instead of an incoherent compromise. | Heavily overlaps Anthropic frontend design; no license detected, so principles may be paraphrased but text cannot be assumed reusable. |
| [callstackincubator/agent-skills](https://github.com/callstackincubator/agent-skills) — React Native | Prioritize measured FPS, startup, bundle, memory, and JS/UI-thread bottlenecks. | React Native/Hermes/Expo specific; requires real-device evidence. |
| [CloudAI-X/threejs-skills](https://github.com/CloudAI-X/threejs-skills) — ten Three.js domains | Split 3D into fundamentals, geometry, assets, materials, lighting, interaction, animation, shaders, textures, and post-processing. | Repetitive templates; missing universal fallback, cleanup, accessibility, and trust boundaries. No license detected. |
| [cursor/plugins](https://github.com/cursor/plugins) — thermo-nuclear review | Red-team shallow abstractions, giant files, and condition explosion aggressively. | Deliberately extreme and false-positive prone; not a default product/code review tone. Relevant subdirectory is MIT, not necessarily every plugin. |
| [Dammyjay93/interface-design](https://github.com/Dammyjay93/interface-design) — product interface design | Separate product UI from marketing; ground dashboards in domain, focus, ratios, tokens, and states. | SaaS/dashboard specialization; should not shape brand/editorial landing pages automatically. |
| [Danilaa1/compact-landing-skill](https://github.com/Danilaa1/compact-landing-skill) — compact landing | Quiet typography, compact CTA hierarchy, and motion that does not shift layout. | A narrow landing-page fingerprint, not a universal premium style. |
| [diffusionstudio/lottie](https://github.com/diffusionstudio/lottie) — text-to-Lottie | Keep scene constraints and validate exported animation with an actual renderer. | Player/export workflow specific; JSON cost, runtime cleanup, alternative content, and reduced motion remain application work. |
| [dimillian/skills](https://github.com/dimillian/skills) — SwiftUI UI patterns | Decide existing/new mode first and make state ownership explicit. | SwiftUI lifecycle and primitives cannot be translated mechanically into DOM components. |
| [emilkowalski/skills](https://github.com/emilkowalski/skills) — design engineering and motion family | Ask whether motion is needed; name patterns precisely; support direct manipulation, interruption, and velocity continuity. | Apple/physical-motion taste is overrepresented; not all products need spring physics or the same timing preferences. |
| [ibelick/ui-skills](https://github.com/ibelick/ui-skills) — router/baseline/a11y/metadata/motion performance | Route task → stack → most specific skill; load the smallest useful context; report snippet/why/fix by severity. | Base UI/Tailwind/Motion and author-taste assumptions leak into some rules. The registry cannot validate itself. |
| [Jakubantalik/transitions-dev](https://github.com/Jakubantalik/transitions-dev) — transition patterns | Choose a transition from the UI relationship and include implementation pitfalls. | Drop-in snippets do not prove product meaning, accessibility, reduced motion, or performance. |
| [Jakubantalik/transitions.dev](https://github.com/Jakubantalik/transitions.dev) — refine-live | Close the loop with a live inspector, scan, apply job, and visual feedback. | External relay/long-polling can spend credits and mutate files; no license detected. |
| [jakubkrehel/make-interfaces-feel-better](https://github.com/jakubkrehel/make-interfaces-feel-better) — visual craft | Optical alignment, concentric radii, interruption, and stagger discipline are useful final-pass prompts. | Micro-polish cannot replace product research, architecture, semantics, or accessibility. |
| [jakubkrehel/oklch-skill](https://github.com/jakubkrehel/oklch-skill) — OKLCH | Treat gamut, contrast, P3 output, conversions, and token roles as a system. | Browser/display results need rendering evidence. No license detected. |
| [jakubkrehel/skills](https://github.com/jakubkrehel/skills) — UI/color/typography | Keep one styling system; cover font formats/features, type scale, line measure, wrapping, mobile inputs, and logical properties. | Considerable overlap with the author's other repos; English typography heuristics need CJK/script calibration. |
| [Jane-xiaoer/claude-skill-web-clone](https://github.com/Jane-xiaoer/claude-skill-web-clone) — web clone | Find the real source first, inspect the live site second, and classify reconstruction complexity. | Copyright, trademark, credentials, anti-bot, and asset-license risk; pixel cloning is not design reasoning. |
| [latent-spaces/brag](https://github.com/latent-spaces/brag) — launch video | Read the product, storyboard a story, render, then validate the media pipeline. | Marketing-video only; external service plus music/asset rights. No license detected. |
| [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) — eight style/redesign/output skills | Make style mode and adjustable design axes explicit; audit before redesign. | Strong dogma, randomization, perpetual motion, and many absolute bans; output completeness is not a visual-design domain. |
| [mattpocock/skills](https://github.com/mattpocock/skills) — engineering router/domain/prototype/debug/TDD family | Route work, sharpen domain vocabulary, reproduce/minimize failures, use throwaway prototypes, and design deep modules. | Mostly engineering, not UI; some flows publish issues/docs; two registry entries are gone upstream. |
| [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli) — Playwright CLI | Prefer DOM snapshots/locators for actions, keep sessions observable, and capture traces for failures. | Browser automation can cause real submissions/messages/purchases; external side effects require authorization. |
| [millionco/react-doctor](https://github.com/millionco/react-doctor) — React Doctor | Run the same diagnosis before/after a feature, bug fix, or commit to detect regressions. | React-only; score is a proxy; Modified MIT adds AI training/evaluation and hosting restrictions that must be read directly. |
| [millionco/skills](https://github.com/millionco/skills) — budge | Live-tune one property, confirm it, persist, and remove the tuning widget. | Next App Router/Tailwind specific; temporarily injects runtime UI. |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) — UI/UX Pro Max | Searchable cross-stack styles, palettes, fonts, product types, charts, and priority tables help weak models enumerate choices. | Huge static catalogue creates false precision, conflicts, stale data, and stereotype lookup. |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) — 18 design verbs | Route intent by verbs; interview before shaping; harden error/i18n/edge states; adapt beyond screens; join browser and code evidence. | Commands overlap and consume context; many subjective bans; hooks/browser expectations and taste cannot become universal standards. |
| [PrototyperAI/prototyper-ui](https://github.com/PrototyperAI/prototyper-ui) — build primitive | First ask whether a mature library already solves ARIA/focus/keyboard hard parts; classify primitive complexity before building. | Custom primitives remain high risk around IME, AT, pointer/keyboard, focus, and state machines. |
| [rams.ai](https://www.rams.ai/rams.md) — Rams | Separate accessibility and visual findings, then prioritize by impact. | Mutable non-GitHub source, no detected license or revision metadata, and older WCAG framing. |
| [raphaelsalaja/skill](https://github.com/raphaelsalaja/skill) — animation/sound/icon/pseudo-element skills | Use file:line audits; choose spring/easing/no motion by behavior; treat interface sound as an accessibility concern. | Narrow techniques, no detected license, and author preferences; motion/sound need opt-out, quiet contexts, semantics, and lifecycle checks. |
| [remix-run/agent-skills](https://github.com/remix-run/agent-skills) — React Router framework mode | Keep loader/action/form, pending/optimistic states, errors, and version compatibility together. | Repository is archived and applies only to React Router framework mode. |
| [remotion-dev/skills](https://github.com/remotion-dev/skills) — Remotion | Current skill routes progressively across media, captions, rendering, interactivity, and SaaS concerns. | Registry path is stale; Remotion-only; no repository license detected. |
| [saadeghi/daisyui](https://github.com/saadeghi/daisyui) — daisyUI | Discover existing library components and official references before generating classes/markup. | Library-specific trigger is overbroad; not every HTML/JSX task should adopt daisyUI. |
| [shadcn-ui/ui](https://github.com/shadcn-ui/ui) — shadcn | Read `components.json`/registry, compose current generated components, and respect local ownership. | Version, registry, Tailwind, and locally modified generated code determine the correct answer. |
| [shadcn/improve](https://github.com/shadcn/improve) — improve | Strictly separate read-only reconnaissance/audit/vetting from a self-contained implementation handoff. | It never implements; downstream quality and backlog noise remain risks. |
| [sveltejs/ai-tools](https://github.com/sveltejs/ai-tools) — Svelte code writer | Retrieve version-matched documentation and run a framework-specific autofixer. | Svelte 5/tool-service specific; wrong for older Svelte or another compiler. |
| [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) — agent-browser | Snapshot-ref operations and observable browser sessions support reproducible outcome checks. | “Prefer over every browser tool” is overbroad; login, forms, and messages can create external side effects. |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) — UI audit/React performance | Use file:line findings; prioritize React waterfalls, bundle, server work, then render work. | Mutable remote guidelines, React/Next bias, and no root license detected. |
| [vercel-labs/next-skills](https://github.com/vercel-labs/next-skills) — three stale Next entries | The useful pattern is moving version-sensitive knowledge into the framework repo and generating local version docs. | All three registry paths are obsolete; never treat the old repo as current guidance. |
| [vuejs-ai/skills](https://github.com/vuejs-ai/skills) — eight Vue skills | Confirm architecture, load focused references, and write adaptable composables that accept values/refs/getters coherently. | Composition API and version preference; several files were copied/overlapped elsewhere. |
| [wshobson/agents](https://github.com/wshobson/agents) — interaction/WCAG | Connect motion to feedback/orientation/focus/continuity; pair automated accessibility checks with manual verification. | Generic snippets and summarized thresholds must be checked against specifications; automation cannot confer conformance. |
| [zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides) — frontend slides | Classify create/convert/modify; stabilize the stage and content density before visual exploration. | Presentation-specific; projection size, density, animation, and accessibility require their own targets. |
| [zeke/swiss-design-skill](https://github.com/zeke/swiss-design-skill) — Swiss design | Grid, type, spacing, and hierarchy can be expressed as one consistent grammar. | One style/Tailwind lens; opacity-based hierarchy can violate contrast and should remain optional taste. |

## Cross-source decisions for WOW Frontend Design

Adopt:

1. Route by user intent, project stack/version, risk, and task; load the smallest relevant references.
2. Keep audit/report and fix/mutation as separate authorization modes.
3. Require source inspection before redesign, dependency choice, or primitive construction.
4. Report `severity → file:line/state → user impact → evidence → fix → verification`; deduplicate one root cause across instances.
5. Separate machine-detectable facts, browser assertions, manual/AT review, and subjective craft.
6. Make responsive a first-class concern despite the registry gap.
7. Prototype uncertain high-cost interactions in an isolated disposable surface before production, when the uncertainty justifies it.
8. Layer standards/security/data integrity above optional tastes such as Swiss, Apple, brutalist, “anti-slop,” or award-site spectacle.
9. Prefer mature primitives for complex keyboard/focus/ARIA behavior unless a tested product constraint requires custom work.
10. Track upstream URL, revision, retrieval date, license, and content hash; detect redirects, 404s, duplicated aliases, and changed license terms before reuse.

Reject:

- automatic ingestion from a registry or mutable `main` branch;
- star count, catalogue size, score, or author confidence as correctness;
- treating five aliases as five independent validations;
- assuming no `LICENSE` means free reuse;
- mixing framework-specific syntax, legal claims, platform guidance, accessibility standards, and taste rules into one universal mandate;
- using third-party skills to expand scope, install tooling, send browser actions, or mutate files without user authorization.
