# Behavioral design evidence

Use this maintenance reference when a design claim invokes perception, cognition, persuasion, advertising, trust, or conversion. It prevents a research citation from becoming a universal UI recipe.

## 1. Label the evidence class

```text
standard/law/policy → hard boundary in its jurisdiction/scope
systematic review/meta-analysis → general evidence with heterogeneity
controlled experiment → result under its exact population/task/stimulus
field experiment → causal result in its product/channel/context
observational study → association; confounding remains
textbook/practitioner heuristic → candidate design hypothesis
author/auteur example → creative reference only
```

For every claimed principle record source, population/task, medium, effect measured, uncertainty/heterogeneity, transfer assumptions, design hypothesis, and project validation. Attention, fixation, recall, preference, click, comprehension, conversion, retention and wellbeing are different outcomes.

## 2. Perception and visual hierarchy

- Use proximity, common region and uniform connectedness to express true relationships; do not put every group in a card. See [Wagemans et al.](https://doi.org/10.1037/a0029333), [Palmer](https://doi.org/10.1016/0010-0285(92)90014-S), and [Palmer and Rock](https://doi.org/10.3758/BF03200760).
- Reduce competing feature congestion around a primary task, then test actual search/comprehension. [Visual clutter](https://doi.org/10.1167/7.2.17) and [visual-search guidance](https://doi.org/10.1038/s41562-017-0058) are diagnostic hypotheses, not usability scores.
- Reject claims that a Gestalt “law”, F/Z pattern, golden ratio, saliency map, or eye-tracking result guarantees reading order or understanding across language, viewport and interaction.

Make attention intent executable without pretending to predict fixation:

```text
route/state → top user task → required first-understood region → cue used
→ simultaneous competing cues → persistent/transient duration → failure risk
→ locale/viewport/input → behavioral or rendered check → result/evidence ceiling
```

- Preserve semantic/DOM order even when visual position changes; a salience cue cannot repair a wrong reading or focus order.
- Give size, position, contrast, whitespace, motion and novelty explicit jobs. Several high-salience cues may be valid for concurrent operational tasks, but they need grouping and priority instead of all claiming “primary”.
- Re-check at narrow mobile, long `zh-Hant`, grayscale, reduced motion, zoom and error/notification states. A beautiful default-state hierarchy can collapse when a banner, validation error, virtual keyboard or translated label appears.
- Use blur/squint, grayscale and silhouette review only as craft diagnostics. They do not measure understanding or replace task observation.
- Any persistent animation, saturated status color, badge count, toast or interruption must justify frequency and urgency. Do not steal attention from consent, safety, price, recovery or the user's current input.

### Visual convergence boundary

Visual convergence means independently generated outputs repeatedly collapse onto interchangeable structures, copy, effects or interaction patterns without product evidence. It is an output-diversity and product-fit problem—not a cognitive law and not proof that a familiar pattern is bad.

Use [anti-ai-slop.md](anti-ai-slop.md) only for the post-render product-swap and earned-region review. Representation belongs to [component-composition.md](component-composition.md); blur, grayscale, and silhouette remain bounded craft diagnostics here and in the applicable visual review. Test convergence with fixed briefs, retained raw outputs, anonymized rendered states, and an independent reviewer. A different palette, random asymmetry, or forced novelty does not count as product-specific distinction; one model pair or one judge cannot establish a general anti-slop effect.

## 3. Cognitive load, memory and choice

- Integrate text, visualization and controls that must be understood together; remove task-irrelevant competition; adapt density/progressive disclosure to expertise. Cognitive-load work began largely in learning/problem-solving contexts ([Sweller](https://doi.org/10.1207/s15516709cog1202_4), [Chandler and Sweller](https://doi.org/10.1207/S1532690XCI0804_2)) and includes important boundary critiques ([de Jong](https://doi.org/10.1007/s11251-009-9110-0), [expertise reversal](https://doi.org/10.1207/S15326985EP3801_4)).
- Miller's `7±2`, Cowan's approximate four, and Hick–Hyman findings are not menu, card, field or navigation hard limits.
- Choice overload is conditional. The original jam result does not prove “fewer choices always convert”; meta-analyses report substantial context and heterogeneity ([Scheibehenne et al.](https://doi.org/10.1086/651235), [Chernev et al.](https://doi.org/10.1016/j.jcps.2014.08.002)). Improve grouping, comparability, search, filtering, defaults and preview, then measure task success, error, reversal and time by expertise.

## 4. Choice architecture and ethics

Hard product rules:

- defaults are transparent, reversible and aligned with user interest;
- accept/reject, join/leave and consent/withdraw have reasonably symmetric visibility and effort;
- price, renewal, data use and consequences appear before commitment;
- cancellation, refusal, recovery and deletion remain findable and completable;
- evaluate understanding, mistaken choice, refunds, complaints, reversal, churn and vulnerable-user outcomes—not click/conversion alone.

Nudge effects are heterogeneous and publication bias is disputed ([defaults meta-analysis](https://doi.org/10.1017/bpp.2018.43), [nudging meta-analysis](https://doi.org/10.1073/pnas.2107346118), [bias reanalysis](https://doi.org/10.1073/pnas.2200300119)). Dark-pattern taxonomies and policy reports inform review but do not replace applicable legal advice: [Gray et al.](https://doi.org/10.1145/3173574.3174108), [Mathur et al.](https://doi.org/10.1145/3359183), [FTC](https://www.ftc.gov/reports/bringing-dark-patterns-light), and [OECD](https://doi.org/10.1787/44f5e846-en).

## 5. Advertising and conversion claims

Visual attention can guide creative hypotheses, but it does not establish incremental sales. Advertising effects can be small relative to behavioral variation, and observational attribution can disagree with randomized experiments ([Lewis and Rao](https://doi.org/10.1093/qje/qjv023), [Gordon et al.](https://doi.org/10.1287/mksc.2018.1135)).

- Separate proposition/creative, target audience, landing/product flow and channel.
- Distinguish feature clutter from meaningful complexity; preserve brand recognition and one clear action.
- Use randomized incremental tests with predeclared outcomes/power when causal conversion claims matter; measure sales, refunds, retention and complaints downstream.
- Heatmaps, eye tracking, clicks and model self-ratings are diagnostics. They cannot alone prove comprehension, trust, causality, “best design”, conversion or award quality.

## 6. Evaluation rule

Translate each research claim into a falsifiable project hypothesis:

```text
source result → transfer assumption → proposed interface change → expected user outcome
→ counter-risk → measurement → subgroup/locale/device → stop condition
```

If the transfer assumption cannot be defended, treat the source as inspiration only. Do not expose psychology labels as customer copy, stereotype a demographic, manipulate vulnerable users, or use a citation to bypass accessibility, privacy, safety and honest consent.
