# Product discovery and usability research

Use this optional reference only when the user requests discovery, interviews, personas, information architecture research, or usability testing, or when a material product decision cannot be made safely from existing evidence. It must not force a small build or repair through a ceremonial five-stage process.

## 1. Keep evidence and hypothesis separate

Use this chain:

```text
research objective → falsifiable question → participant/fixture criteria → observed behavior or sourced quote → interpretation → design decision → validation status
```

Never invent participants, quotes, interview results, analytics, pain points, personas, completion rates, or research consensus. When research is unavailable, write `hypothesis` or `unknown`, choose a reversible implementation, and state what evidence would change it.

Do not infer ability, culture, income, motivation, or visual preference from age, gender, region, disability, job title, or another demographic. Segment only when task, permission, behavior, context, or decision needs materially differ.

### Route the method from the question

Do not select the familiar method first. Record:

```text
decision at risk → question → behavior or attitude → why/how or how-many/how-much
→ natural/scripted/limited/no product use → available product maturity
→ method → can answer → cannot answer → complementary evidence
```

Direct observation and self-report answer different questions; qualitative evidence is suited to mechanisms and repair ideas, while quantitative evidence estimates frequency or magnitude only under its sampling and measurement assumptions. Product phase and practical limits influence the choice but do not turn a method into proof of another outcome. Treat method maps as routing guidance, not rigid classifications. See Nielsen Norman Group's current [research-method selection framework](https://www.nngroup.com/articles/which-ux-research-methods/) and state the transfer limits for the actual decision.

## 2. Interview without leading

Before recruiting or contacting anyone, obtain authorization and define data handling, consent, privacy, compensation, recording, retention, and deletion. Prefer questions about a recent real event:

- “上次處理這件事時發生了什麼？”
- “你先看哪裡？接著做了什麼？”
- “哪一步讓你停下來？你當時怎麼判斷？”

Avoid pitching the solution, asking whether a participant “likes” a proposed feature, supplying the expected vocabulary, or turning one quote into a universal need. Record exact observation separately from interpretation and confidence.

## 3. Validate information architecture

A sitemap or model-generated category tree is a proposal, not evidence. For material IA changes:

1. inventory real content, objects, tasks, ownership, permissions, lifecycle, and search terms;
2. propose labels and grouping with source/provenance;
3. choose an appropriate validation method such as open/closed card sorting, tree testing, search-log analysis, support-ticket review, or task observation;
4. define success and disagreement handling before results arrive;
5. retain minority/high-risk paths instead of optimizing only the average route.

Do not prescribe a universal participant count. Select sample and stopping criteria from research method, role diversity, task risk, expected effect, recruitment limits, and saturation; report uncertainty.

## 4. Test tasks, not instructions

Usability tasks should describe a realistic goal and starting context without revealing the control, label, or steps being tested. Freeze the route/state, fixture, device/input, locale, and task success criteria first.

Record separately:

```text
attempted/completed → time or steps when meaningful → errors/recovery → observed path/quote → facilitator intervention → interpretation → confidence → follow-up
```

Completion rate, time, clicks, heatmaps, saliency, satisfaction, and preference measure different things. None alone proves understanding, trust, accessibility, conversion, brand fidelity, or wellbeing. Accessibility evaluation and complete-process checks remain separate.

Never run external submissions, purchases, messages, uploads, production writes, or participant recruitment without explicit authorization and safe fixtures. A prototype must label simulated/local outcomes honestly.

## 5. Route the result back into design

- Convert a supported finding into a task, content, IA, state, mobile, or component rule.
- Keep contradictory evidence and affected segments visible.
- Pair every design decision with the observation or hypothesis that supports it.
- Re-test the smallest risky assumption before broad visual polish.
- Do not make research theater block a low-risk reversible change; mark the evidence ceiling and continue when authorized.

### Cross-channel journey evidence

Use an experience or journey map only when the service spans meaningful time, locations, channels, teams, or touchpoints. Keep it separate from a product user flow. Build participant journeys individually before consolidating them; merge only genuinely shared stages and retain materially different paths.

For every stage or event, keep actor, context, action, thought/feeling report, touchpoint, dependency, breakdown, source, and confidence distinguishable. A sourced quote is not an observed action, and an inferred emotion is not a participant report. Empty regions and contradictions become research questions rather than invented content. GOV.UK's [experience-map guidance](https://www.gov.uk/service-manual/user-research/creating-an-experience-map/) requires prior user evidence and preserves cross-service events and dependencies; use it as practitioner guidance, not a universal deliverable.

## Source and adoption boundary

The interview/persona/IA/usability structure above was independently paraphrased after critical review of the MIT-licensed `.agents/skills` subtree in [zz41354899/goodux-skills at `c1a1fc9ae9c275abb0c86d114ab654285fd68bff`](https://github.com/zz41354899/goodux-skills/tree/c1a1fc9ae9c275abb0c86d114ab654285fd68bff/.agents/skills). The repository root had no detected license at review time, so its website and installer are not treated as reusable material.

Do not adopt its fixed participant/persona/variant counts, fixed severity-to-schedule mapping, framework stack, industry-to-style catalogue, or one-skill-only rule. Do not run its installer: installation behavior and existing-directory replacement require a separate security review and explicit authorization.

## Legal open reading references

- [Introduction to Human-Computer Interaction](https://introductiontohci.org/) is a free, current HCI textbook published under CC BY-NC-ND 4.0. Use it as reading/reference; do not remix its text into this MIT Skill.
- [政府網站營運交流平台：以使用者為中心的設計](https://www.webguide.nat.gov.tw/guidelines/442/show) is a Traditional Chinese Taiwan-government reference for UCD context. Its official status does not make every recommendation universal; verify the current service, audience, and accessibility requirements.
- [智慧財產局 UI/UX 設計指引](https://tiponet.tipo.gov.tw/TIPO_UIUX/) is a Traditional Chinese service-specific example. Extract transferable questions and patterns only; do not treat one agency's implementation as a universal component library.
- [SixArm UI/UX Design Guide](https://github.com/SixArm/ui-ux-design-guide/tree/a0bff754e4c9777931c6ba1aedb0382e10a18a71) is a glossary-style overview of user-centered design, information architecture, progressive enhancement, localization, accessibility, and end-to-end testing. Use it to widen the question set, not as empirical proof or a visual recipe. Its EPUB says all rights reserved and the pinned repository exposes no reusable license, so independently paraphrase only bounded ideas and copy no text or artwork into this MIT Skill.
