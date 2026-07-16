# Award-quality review lens

Use this reference only when the brief explicitly asks for award quality, an immersive brand experience, cinematic/scroll storytelling, a creative portfolio, or comparison with FWA, CSS Design Awards, CSS Winner, or Awwwards. It is a secondary review lens, not an award predictor or release gate.

## Contents

1. Evidence boundary
2. What the award programs actually publish
3. Transferable review dimensions
4. Narrative and motion review
5. `top-design` Skill review
6. Evaluator-owned workflow

## 1. Evidence boundary

- First pass the ordinary product, task, accessibility, localization, responsive, performance, rights, and security gates. An expressive score cannot offset a broken task, inaccessible action, misleading claim, clipped Traditional Chinese text, or unstable mobile layout.
- Treat official award rules as descriptions of each program's judging system, not universal design science. Public voting, jury availability, entry timing, and award quotas affect results independently of craft.
- Do not claim a predicted FOTD, SOTD, WOTD, Honorable Mention, Special Kudos, or numerical award score. The implementation model cannot score or accept its own work.
- Freeze the requested award lens and source retrieval date before implementation. If the award site changes its rules, update the research instead of silently preserving stale thresholds.
- Award-style motion is optional. A dashboard, high-stakes form, utility workflow, article, or localized product may earn distinction through clarity, data composition, typography, or interaction precision without cinematic effects.

## 2. What the award programs actually publish

Retrieved 2026-07-16 from the programs' own pages.

| Program | Published evaluation signal | Correct use | Do not infer |
| --- | --- | --- | --- |
| [FWA](https://thefwa.com/about/about-fwa/) | Mission-led rather than a public weighted rubric: cutting-edge creativity, innovation, progression, future thinking, and work that pushes boundaries; an international jury votes daily. | Ask whether one product-grounded idea advances the medium or makes a familiar interaction newly meaningful. | Do not invent percentage weights or treat spectacle, WebGL, smooth scroll, or novelty as mandatory. |
| [CSS Design Awards](https://www.cssdesignawards.com/about) | Jury WOTD plus public awards for `UI`, `UX`, and `Innovation`. Its current page says WOTD consideration averages above `8.00` (variable), Special Kudos above `6`, and public awards require more than 20 votes plus a judge average above `6`. UI means aesthetics/effects, UX means experience/functionality, Innovation means new development/design ideas. | Review visual interface, task experience, and technical/design originality as separate dimensions. | Thresholds and public votes are program operations, not internal acceptance scores or proof of usability. |
| [CSS Winner](https://www.csswinner.com/about) | Nominee review covers `Design`, `Usability`, `Content`, and `Functionality`; the site currently describes jury appraisal as 80% and public votes as 20%, with 75%+ having an edge for SOTD. | Keep aesthetics, usable interaction, content quality, and implementation completeness visible as separate evidence. | Public popularity does not prove product quality; a marketing campaign can affect the vote share. |
| [Awwwards](https://www.awwwards.com/about-evaluation/) | Published weighting: `Design 40%`, `Usability 30%`, `Creativity 20%`, `Content 10%`; minimum 18 jury members, three outlier scores removed, five-day voting. The current page lists Honorable Mention at jury score `6.5+`; SOTD remains competitive rather than a guaranteed threshold. | If an Awwwards comparison is requested, use its four named dimensions as a frozen comparison view and retain the program's weight labels. | Do not map the internal WOW scorecard to Awwwards, promise an award, or let visual design compensate for accessibility/performance blockers. |

FWA does not currently publish a comparable percentage formula on its About page. Secondary sites that assign FWA weights are not authoritative enough to become Skill rules.

## 3. Transferable review dimensions

Use evidence-backed questions, not aesthetic quotas:

| Dimension | Review questions | Evidence |
| --- | --- | --- |
| Concept / authorship | Is there one product-specific thesis? Would changing only the brand name leave the concept intact? Is the memorable moment derived from a real noun, verb, data shape, material, place, or user journey? | Concept sentence, source trace, grayscale silhouette, matched screenshots. |
| Visual design / UI | Do type, composition, color, imagery, borders, depth, and micro-details share a grammar? Are hierarchy and continuation clear before motion? | Computed tokens, desktop/mobile screenshots, contrast and font/glyph checks. |
| Usability / UX | Can users orient, complete, interrupt, recover, use keyboard/touch/zoom, and understand static/reduced results? | Primary-task replay, state matrix, focus/scroll/Back evidence, mobile transformation. |
| Creativity / innovation | Does a new treatment clarify this content or interaction? Is the novelty concentrated in one signature rather than sprayed across components? | Alternative comparison, static fallback, before/after behavior, product-fit rationale. |
| Content | Is the information specific, sequenced, localized, readable, and free of unexplained English or evaluator-facing copy? | Content inventory, `zh-Hant`/long-locale screenshots, wrap and reading-order checks. |
| Functionality / development | Are routes, interactions, loading/error states, cleanup, responsive behavior, and runtime fallbacks complete? | Build/tests, console/network checks, lifecycle tests, source/evidence hashes. |
| Performance / resilience | Does the effect remain responsive on target devices and survive reduced motion, missing assets, slow loading, interruption, and teardown? | Project-frozen budgets, traces, low-end target runs, no-motion/static evidence. |

Distinctive does not mean universally huge. Large display type, asymmetry, whitespace, hollow text, 3D, smooth scrolling, a custom cursor, parallax, and manual line breaks are selectors. Use only the ones earned by content, locale, platform, and verified fallback.

For Traditional Chinese:

- derive display scale from glyph density and available inline space rather than a Latin display/body ratio;
- keep browser-owned wrapping for ordinary copy and verify punctuation, mixed scripts, fallback fonts, zoom, and one-character final lines;
- manually compose only a named display role at tested breakpoints, with natural-wrap fallback rather than a universal `<br>` pattern;
- allow whitespace to pace a story, but do not leave title/body tracks accidentally half empty or squeeze content into long narrow columns.

## 4. Narrative and motion review

An award-oriented page still needs a legible static story. Write beats before timelines:

```text
Promise → proof → transformation → decision → consequence
```

For each beat record `message → visual state → transition cause → user control → reduced/static result`. Vary density and scale only where the message changes. One signature sequence plus restrained continuity is usually stronger than animation on every heading.

Apply the patterns in [motion-system.md](motion-system.md):

- Hero entrance establishes hierarchy and becomes usable immediately.
- ScrollTrigger is reserved for causal product/story progress; normal document flow contains every essential beat.
- Dashboard preview animation demonstrates truthful state transitions, not fabricated live activity.
- `login → dashboard` state is owned by authentication/navigation; the transition cannot delay success or hide an error.
- Native scrolling remains the default. A smooth-scroll runtime needs a specific synchronization need and tests for anchors, focus, Back/Forward, modal scroll lock, touch, reduced motion, and teardown.

Reject the award trope when it causes scroll hijacking, long pinned dead zones, unreadable kinetic text, decorative parallax on critical copy, delayed actions, layout shift, device overheating, or a mobile experience reduced to a disabled desktop effect.

## 5. `top-design` Skill review

Pinned source: [`wondelai/skills@326b380` `top-design/SKILL.md`](https://github.com/wondelai/skills/blob/326b3801223ad277ae7082ff85435ba1d36e1903/top-design/SKILL.md), MIT. The MCP Market Chinese page returned a Vercel `429` checkpoint during research, so the pinned repository—not the marketplace rendering—is the review source.

Useful candidate heuristics:

- define brand essence, visual tension, signature moment, and technical ambition before coding;
- design one screenshot-worthy moment from product meaning;
- use contrast between dense/sparse, intimate/expansive, and stable/transforming beats;
- choreograph related elements as a timeline rather than isolated effects;
- treat loading, focus, hover, selection, empty, error, and 404 states as part of craft;
- require reduced motion, non-blocking content, asset optimization, layout stability, and cleanup.

Do not adopt these as universal rules:

- a self-awarded `10/10` or claim that a score would win Awwwards;
- fixed custom weights, `10:1+` type ratios, blanket font/color/easing bans, or the claim that one popular font is automatically generic;
- default Lenis/Locomotive smooth scrolling, custom cursors, magnetic buttons, page preloaders, parallax, pinned sections, or per-line text animation;
- “60fps or nothing,” compositor/GPU assumptions, a Lighthouse score as field performance, or hard-coded LCP/CLS acceptance detached from the project's frozen budget;
- desktop-first art direction that becomes shrink-and-stack mobile, or manual headline breaks without CJK/locale/zoom fallback.

Use the source as a candidate generator. The existing product system, user task, locale, official platform guidance, measured runtime, and evaluator-owned evidence decide what survives.

## 6. Evaluator-owned workflow

1. Pass the core deterministic gates; auto-repair failures first.
2. If the brief explicitly requests an award lens, freeze one program or a named custom comparison. Do not average incompatible award systems.
3. Have an evaluator independent from implementation inspect matched desktop/mobile/reduced-motion screenshots and interaction evidence.
4. Record each observation as `dimension → evidence → issue → smallest repair → regression risk`.
5. Feed clear in-scope defects back through the normal self-repair loop. Keep subjective novelty disagreements advisory.
6. Re-run the affected task, locale, viewport, interaction, accessibility, performance, and evidence matrix after repair.
7. Report `OBSERVED` craft judgments separately from `VERIFIED` machine results. Final wording is “reviewed with the named award lens,” never “award-winning” or “guaranteed to win.”

The goal is memorable, product-specific craft with intact user control—not imitation of an award-gallery aesthetic.
