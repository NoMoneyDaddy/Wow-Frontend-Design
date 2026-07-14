# Visual storytelling, photography, and cinematic language

Use this reference when photography, advertising imagery, art-directed hero media, film language, image-first exploration, or cinematic motion materially shapes the interface. Film and photography offer design hypotheses—not universal psychology.

## 1. Label the evidence class

Every imported principle needs one label:

| Class | Meaning | How it may constrain work |
| --- | --- | --- |
| `normative` | current standard or product safety/accessibility requirement | hard gate within its exact scope |
| `empirical` | peer-reviewed observation with population/task limits | testable hypothesis; record external-validity limits |
| `textbook` | established teaching/analysis framework | shared vocabulary, not measured truth |
| `auteur` | practitioner/artist method or style | optional inspiration only |

Do not turn “close-up means intimacy,” “blue means trust,” “rule of thirds wins,” “Z-pattern eyes,” “fast cuts convert,” or “parallax feels premium” into product facts. Audience, culture, language, task, content, viewing context, and prior exposure change the result.

## 2. Write the visual-story contract

```text
intent → audience/task → source_class/confidence → establishing state → focal anchor → depth layers → semantic beats → viewpoint/crop safe area → transition → motion budget → reduced state → asset truth/rights → evidence
```

- `establishing state`: the minimum context needed before detail.
- `focal anchor`: the task/content anchor, supported by salience without erasing alternatives.
- `semantic beats`: meaningful changes in content or state—not arbitrary scroll distances.
- `crop safe area`: what must survive mobile/desktop, localization, subject detection failure, and share-preview crops.
- `reduced state`: a complete static sequence with the same meaning and CTA.

## 3. Translate visual language safely

| Source concept | Useful web translation | Boundary |
| --- | --- | --- |
| framing and figure/ground | one legible focal layer, separation, deliberate negative space | no mandatory thirds/center formula |
| establishing → context → detail | content sequence and progressive disclosure | do not delay the top task for atmosphere |
| viewpoint and lens | crop, scale, perspective, evidence/detail relationship | angle has no fixed dominance/emotion meaning |
| depth and lighting | hierarchy through value, occlusion, scale, sharpness | protect text contrast over every frame |
| graphic/eyeline/action continuity | preserve focus and object identity across state changes | web state is not bound to film's 180-degree convention |
| cut, dissolve, track, pan | choose discontinuity/continuity that matches the state change | movement does not inherently improve engagement |
| rhythm | coordinate content density, pause, input, sound, and motion | no fixed millisecond/emotional formula |
| salience | local contrast can help a meaningful anchor | salience does not predict user intent or comprehension |

Use actual task order, headings, labels, and controls to carry meaning. The image/motion layer supports that structure; it never becomes the sole instruction, proof, price, comparison, or CTA.

## 4. Use image-first exploration without screenshot-driven UI

Image-first is appropriate for uncertain art direction, hero photography, illustration, material/light language, and campaign mood. It is not a substitute for information architecture or production UI.

```text
truthful content + task brief
→ low-cost composition sketches
→ only enough image directions to resolve named axes
→ select attributes, not a whole screenshot
→ extract tokens/layout/crop/asset/motion contracts
→ build semantic DOM and real states
→ compose desktop and mobile independently
→ compare rendered product to intent
→ verify interaction, localization, accessibility, performance, and rights
```

Hold the same copy, content inventory, subject, aspect ratios, and prohibited claims across image variants. Record what changed: viewpoint, crop, light, palette relationship, depth, texture, subject distance, or motion premise.

Reject image-to-code output that:

- flattens text/controls into pixels or absolute-positioned fragments;
- invents data, products, people, testimonials, awards, or brand assets;
- encodes one desktop canvas as the responsive specification;
- guesses fonts/assets/licenses from appearance;
- omits hover/focus/loading/empty/error/success and A→B→A behavior;
- uses a generated image as evidence of a working or accessible product.

Generated imagery is `generated-untrusted`: record provider/model/version, prompt/input provenance, data sent, rights uncertainty, disclosure needs, factual versus conceptual status, and static/alt/crop behavior.

## 5. Photography and advertising asset gate

- Define what the image proves or contributes. Atmosphere, product evidence, editorial documentation, portrait, and conceptual illustration are different truth claims.
- Preserve provenance, releases/consent, trademark/property constraints, license, modification, model/tool, and attribution.
- Never hotlink a search result or use a stock/AI image as a real customer, location, product result, newsroom event, or before/after proof.
- Art-direct subject position and crop for mobile, desktop, high-DPR, text expansion, social preview, and focal-point failure.
- Provide visible copy and useful alternative text outside burned-in text. Localize text in DOM, not in the photograph.
- Measure encoded bytes, dimensions, responsive sources, decode, LCP priority, color profile/HDR behavior, and low-data fallback.
- Advertising attention is not task completion or informed consent. Keep price, terms, material limitations, recurring billing, sponsorship, and consequential choices clear; never use salience or motion to obscure them.

## 6. Motion hard gates

- Follow WCAG 2.2 [Pause, Stop, Hide](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html), [Three Flashes](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html), and [Animation from Interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html) in their exact applicable scope.
- Respect [`prefers-reduced-motion`](https://www.w3.org/TR/mediaqueries-5/#prefers-reduced-motion). The static/reduced result retains story, reading order, orientation, and CTA.
- Treat [Scroll-driven Animations Level 1](https://www.w3.org/TR/scroll-animations-1/) as progressive enhancement while it remains a Working Draft.
- Continuous filmic layers require pause/off-screen/background behavior, no essential content dependency, and target-device evidence.

## 7. Evidence shelf

Use original sources; paraphrase within citation/licensing limits:

- Wagemans et al., Gestalt grouping and figure-ground organization, [DOI 10.1037/a0029333](https://doi.org/10.1037/a0029333).
- Itti, Koch, and Niebur, computational visual saliency, [DOI 10.1109/34.730558](https://doi.org/10.1109/34.730558).
- Wolfe and Horowitz, factors guiding visual attention, [DOI 10.1038/s41562-017-0058](https://doi.org/10.1038/s41562-017-0058).
- Smith and Mital, gaze in dynamic scenes and task effects, [DOI 10.1167/13.8.16](https://doi.org/10.1167/13.8.16).
- Smith, attentional theory of cinematic continuity, [DOI 10.3167/proj.2012.060102](https://doi.org/10.3167/proj.2012.060102).
- Cutting et al., historical Hollywood shot-length data, [DOI 10.1177/0956797610361679](https://doi.org/10.1177/0956797610361679); corpus trend, not a conversion rule.
- Elliot and Maier, color psychology review, [DOI 10.1146/annurev-psych-010213-115035](https://doi.org/10.1146/annurev-psych-010213-115035); external-validity limits remain.
- Jonauskaite et al., cross-cultural color-emotion associations, [DOI 10.1177/0956797620948810](https://doi.org/10.1177/0956797620948810).
- Palmer, Schloss, and Sammartino, visual aesthetics/preferences review, [DOI 10.1146/annurev-psych-120710-100504](https://doi.org/10.1146/annurev-psych-120710-100504).
- Yale Film Analysis: [cinematography](https://filmanalysis.yale.edu/cinematography/), [editing](https://filmanalysis.yale.edu/editing/), and [mise-en-scène](https://filmanalysis.yale.edu/mise-en-scene/); analytical vocabulary with no single fixed meaning.
- Academy [ACES documentation](https://docs.acescentral.com/) for image-production color pipelines—not a CSS color/emotion system.

Textbooks and auteur frameworks such as *Film Art*, *The Visual Story*, *Cinematography: Theory and Practice*, *The Photographer's Eye*, Stephen Shore, Albers, and Arnheim may supply vocabulary. Do not copy their text/figures or upgrade their methods into standards.
