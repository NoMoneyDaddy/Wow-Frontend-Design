# GitHub frontend skill research

Use this maintenance reference to understand what this skill borrows, rejects, and still needs to test. Do not load it for ordinary frontend work.

Snapshot date: **2026-07-14**. Stars are volatile discovery signals, not quality scores. `Push` records the latest repository push observed during research. Licenses were checked at repository or skill level; unclear licenses remain unclear. Principles below are paraphrased, not copied.

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
| [Vercel Agent Skills — web-design-guidelines](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines) | 29,048 / 2026-07-07 | Root unclear; rule source MIT | Fresh audit rules and terse `file:line` findings; strong coverage of semantics, forms, focus, URLs, safe areas, hydration, images, and CLS. | Fetch-at-runtime harms reproducibility unless a commit is pinned. Review-focused, not a creative-direction system. English copy rules do not transfer to Traditional Chinese. Some generic fixes can hide root causes. |
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

## Adopted synthesis

1. Product truth, top task, audience context, and real assets precede style.
2. If changing only the product name leaves the thesis intact, redesign it.
3. Structural marks such as `01/02/03` require a real sequence or index meaning.
4. For new builds or broad redesigns, concentrate expressive risk in one product-specific signature; focused repair preserves identity and scope.
5. Resolve conflicts in this order: user safety, security, privacy, legal/rights, and data/transaction integrity → accessibility and essential task completion → interaction correctness and resilience → performance → visual novelty. Escalate rather than trade away a higher-order constraint.
6. Product/platform tables are prompts for reasoning, never stereotype lookup.
7. Breakpoints come from content failure, not device names.
8. Mobile needs a transformation table; “everything becomes one column” is not a result.
9. Every data surface covers loading, empty, partial, error, permission, offline, and success as applicable.
10. External dynamic rules record a commit/version; external skill and runtime licenses are separate.
11. Audit findings use `file:line — failure — fix`, followed by browser proof for rendered behavior.
12. A weak model cannot accept its own output. Freeze evaluator-owned checks and reconcile every verified claim with evidence.

## Explicit rejections

- Star count as a proxy for correctness.
- Fixed aesthetics attached to industries or demographics.
- “Premium” as preloader + custom cursor + smooth scroll + parallax + pinning.
- Banning a popular font, color, or layout when product evidence supports it.
- One universal duration, breakpoint, component line count, or mobile column count.
- Mixing WCAG, Apple HIG, Material, and author preference without labeling scope.
- Fetching mutable external instructions during verification without recording the revision.
- Copying large blocks from unclear or incompatible licenses.
