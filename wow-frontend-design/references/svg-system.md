# SVG system

Treat SVG as structured markup, not a harmless image format. Choose its role, trust boundary, embedding, semantics, license, and verification before generating paths.

## Contents

1. Write the SVG contract
2. Choose the embedding mode
3. Build icons and illustrations
4. Build data visualization
5. Handle sprites and IDs
6. Secure user-supplied SVG
7. Optimize without damage
8. Animate responsibly
9. Verify and deliver
10. Tool and license notes

## 1. Write the SVG contract

For each asset, record:

```text
asset type → trust → embedding → semantic intent → viewBox/targets → ID namespace → motion → source/license → security/optimization → evidence
```

Required classifications:

- asset type: `icon | illustration | data-viz | sprite`;
- trust: `first-party | vetted-library | generated-untrusted | user-supplied`;
- embedding: `inline | img | css-background | external-use | document`;
- semantic intent: `decorative | meaningful image | interactive | complex data`.

Do not start with paths. Establish a positive `viewBox`, target sizes, color/stroke tokens, accessibility result, and provenance first.

## 2. Choose the embedding mode

| Mode | Good for | Benefits | Risks and requirements |
| --- | --- | --- | --- |
| Inline `<svg>` | themed icons, authored illustration, accessible or interactive graphics | full CSS/JS/DOM access | increases DOM; global ID collisions; untrusted content becomes active markup. |
| `<img src="x.svg" alt="…">` | cacheable meaningful or decorative images | stronger image-context isolation; simple responsive behavior | no internal CSS/DOM control; accessible name comes from `alt`; reserve dimensions. |
| CSS `background-image` | decoration only | no extra semantic node | no `alt`; never use for meaningful content. |
| Inline/external `<symbol><use>` | repeated icons | reuse and theming | IDs, CORS/CSP, same-origin, SSR, print, Safari, and assistive-technology behavior need testing. |
| `<object>`, `<iframe>`, `<embed>` or direct document | a deliberately active SVG application | isolated document behavior | active scripting/navigation boundary; avoid for untrusted assets and ordinary UI icons. |

User-supplied SVG must not be directly inlined. Prefer a sanitized, isolated image delivery path or rasterized derivative when interactivity is unnecessary.

## 3. Build icons and illustrations

### Icons

- Reuse the product's current icon system. Otherwise choose one coherent family and fix sizes, stroke/fill behavior, line caps, corner language, and optical weight.
- A decorative icon uses `aria-hidden="true"` and `focusable="false"` where legacy focus behavior matters.
- An icon-only button receives its accessible name on the button. Hide the SVG to prevent duplicate announcements.
- A standalone meaningful inline SVG uses an explicit image role and a non-empty accessible name, normally `aria-labelledby` pointing to unique `<title>` and optional `<desc>` IDs.
- Directional navigation icons may mirror in RTL; brand marks, media symbols, checks, and non-directional objects do not mirror automatically.
- Use `currentColor` when the icon should follow text/action state. Do not encode status by color alone.
- Do not convert functional labels into paths. Brand lettering may remain artwork only when an equivalent text name exists.

For a morphing state icon:

- use the same `viewBox`, path order, winding intent, and compatible point/command topology when performing true interpolation;
- do not force every symbol into a three-line construction; if the states do not share meaningful geometry, use rotation, displacement, or crossfade;
- put the accessible name and pressed/expanded state on the control, not on the changing decorative paths;
- if the control's action label changes after activation, update that label coherently and test the screen-reader result;
- switch to the final state immediately under reduced motion;
- compare intermediate frames at every shipped optical size so line weight, self-intersection, and alignment do not collapse.

[W3C ACT Rule 7d6734](https://www.w3.org/WAI/standards-guidelines/act/rules/7d6734/) requires SVG explicitly exposed as an image/graphics role to have a non-empty accessible name. [SVG 2 accessibility support](https://www.w3.org/TR/SVG/access) describes ARIA and `title`/`desc`; real browser/AT support still requires testing.

### Illustrations

- Give every illustration product-specific content. A generic gradient rectangle is not product evidence.
- Namespace `gradient`, `mask`, `clipPath`, `filter`, `marker`, `pattern`, title, and description IDs per component instance.
- Establish node, path-command, filter-area, byte, and animation budgets appropriate to the target devices.
- Use `max-inline-size: 100%; block-size: auto` or an equivalent responsive rule and reserve aspect ratio.
- Use `preserveAspectRatio="none"` only when distortion is intentional and verified.
- Prefer raster or Canvas for extreme node counts or filter-heavy artwork, while keeping essential meaning in DOM text.

### Generation workflow for icons and illustrative media

1. Write the semantic brief: product noun/action, decorative or meaningful role, visible context, target sizes/themes, style family, directionality, factual versus conceptual content, and prohibited motifs.
2. Search the existing product icon/asset system before generating. Reuse a coherent licensed family when it already expresses the concept; do not mix libraries to find a closer noun.
3. Generate only enough candidates to resolve a named shape/metaphor decision. Hold viewBox, stroke/fill grammar, optical weight, and corner/cap language constant while comparing the metaphor.
4. Select from a render sheet at actual smallest/largest sizes, light/dark/forced-color contexts, adjacent icons, and the real control/card—not from a large isolated artboard.
5. Normalize paths and IDs, add accessible treatment at the use site, record provenance/tool/model/license, then run security/optimization and before/after render checks.

For an icon family, persist a small `style-spec` artifact: viewBox and optical sizes, stroke/fill policy, cap/join/corner grammar, padding/overshoot, color behavior, RTL policy, naming, and exception rationale. Review the family together at 16/24/32/48 CSS px where those sizes ship; consistency cannot be proven one large icon at a time.

Treat every AI-generated SVG as `generated-untrusted`, even when the provider returns only an `<svg>` substring. Parse as XML with safe entity/network settings, enforce an element/attribute/URL allowlist, sanitize, then optimize and render-diff. SVGO is still not a sanitizer. Sending prompts, source images, logos, or product data to a remote generator requires explicit provider/data/cost authorization and provenance recording.

For favicon/PWA packages, define the required SVG/ICO/PNG/Apple-touch/maskable variants from the actual platform manifest. Verify links, MIME/dimensions, transparent/background behavior, maskable safe zone, light/dark appearance, caching, and install/share surfaces. Do not depend on `<text>` with an unavailable font, or upload a private mark to a third-party generator without consent.

For UI icons, prioritize immediate recognition, silhouette, optical centering, consistent negative space, and state-pair coherence over path cleverness. A generated icon that needs a tooltip to explain a standard action should normally yield to a familiar symbol plus visible label.

For illustrations, freeze the content claim. Conceptual/fictional imagery must be labeled when it could be mistaken for a real product, person, place, result, or evidence. Provide responsive art direction/crop and a useful static alt/description; do not embed unlocalizable UI copy inside the artwork.

## 4. Build data visualization

SVG and D3 do not create accessibility automatically. Provide:

- a concise chart name and summary;
- the main trend or conclusion in text;
- axes, units, legends, and visible labels;
- a data table, structured list, or long description when users need exact values;
- redundant shape, label, position, or pattern—not color alone;
- keyboard operation and visible focus for interactive marks;
- tooltips available through focus/tap, not hover only.

At thousands of marks, compare SVG DOM with Canvas/WebGL. If rendering moves to canvas, retain an equivalent semantic text/data layer and accessible controls.

## 5. Handle sprites and IDs

- Every `<symbol>` has its own `viewBox`.
- Prefix symbol and referenced IDs with a build/component namespace.
- Place context-specific accessible names at the use site, not inside a reusable symbol that appears in different meanings.
- Verify every `url(#id)`, `href="#id"`, `aria-labelledby`, mask, gradient, marker, and clip reference after bundling and optimization.
- Render several component instances on one page to expose collisions.
- For external sprites, test cache, same-origin/CORS, CSP, SSR/hydration, print, forced colors, and target browsers/assistive technology.

## 6. Secure user-supplied SVG

Treat extension and `Content-Type` as hints, not trust. The upload/render pipeline must:

1. enforce byte, decompressed size, XML depth, node, path segment, coordinate, filter area, and embedded-data limits;
2. parse with DTD, external entities, network resolution, and unsafe XInclude disabled;
3. require one valid SVG root and reject malformed namespace tricks;
4. remove or reject scripts, `foreignObject`, `on*` handlers, `javascript:` URLs, CSS imports, external `url()`, remote hrefs, and unexpected active animation/filter features;
5. sanitize with a maintained allowlist sanitizer such as [DOMPurify](https://github.com/cure53/DOMPurify) in an appropriate environment;
6. avoid modifying sanitized markup with a library that can reintroduce unsafe structures; sanitize again if rewriting is unavoidable;
7. store under random names and an isolated origin or image-serving boundary; restrict direct navigation;
8. prefer `<img>` image context or server-side rasterization when interactive SVG features are unnecessary;
9. test XSS, external requests, data URIs, `foreignObject`, duplicate/clobbering IDs, namespace mutation, XML expansion, and geometry/filter denial of service.

DOMPurify addresses markup XSS. It does not replace upload authorization, filenames, quotas, parser sandboxing, storage isolation, SSRF controls, or resource-exhaustion limits.

## 7. Optimize without damage

[SVGO](https://github.com/svg/svgo) removes redundant SVG data through configurable plugins. It is an optimizer, not a sanitizer.

- Pin the tool version and commit the config.
- Use different configs for icons, illustrations, diagrams, sprites, and accessibility-bearing SVG.
- Preserve a valid `viewBox`; current SVGO defaults disable `removeViewBox` because it removes scalability.
- Preserve names/descriptions needed by the actual embedding. Current defaults also disable `removeTitle`; do not infer that every title is the correct accessible name.
- Keep IDs referenced by CSS, scripts, `<use>`, gradients, masks, clips, filters, markers, and ARIA.
- Do not run destructive path merging or precision reduction blindly on logos, maps, charts, or small optical icons.
- Compare pre/post output at every target size and theme. A successful exit code is not visual equivalence.

Required post-optimization checks:

- parse succeeds and root/viewBox remain valid;
- no duplicate IDs and every reference resolves;
- accessible name/description remain present when required;
- no unexpected external requests or active content;
- rasterized before/after diff stays within the declared tolerance;
- narrow/wide, light/dark, forced colors, and zoom render correctly.

## 8. Animate responsibly

Read [motion-system.md](motion-system.md).

- Prefer group transforms and opacity; profile path morph, stroke-dash, masks, filters, and large painted regions.
- Essential meaning exists in the static state and is not revealed only through movement.
- Reduced motion removes large movement, parallax, morphing, and autoplay; show a designed static frame.
- Continuous effects pause off-screen and in background tabs, and expose pause controls when required.
- Interactive SVG has visible controls, keyboard alternatives, focus, and state announcements.
- Test multiple simultaneous instances on low-end target hardware.

## 9. Verify and deliver

Minimum rendered matrix:

- smallest and largest actual display sizes;
- 320 CSS px/reflow and 200% text resize where text/controls participate;
- light, dark, high contrast/forced colors as supported;
- keyboard, touch, no-hover, and reduced motion;
- inline plus the real deployment embedding mode;
- repeated component instances and localized long labels;
- sanitized malicious fixtures for user upload paths;
- before/after optimization render diff;
- console/network, bytes, nodes, path commands, paint/frame cost, and external requests.

Ship an asset manifest when SVG is material:

```text
source + license/attribution + tool/version + config + hash + viewBox/targets + semantic intent + trust/security policy + motion policy
```

Release blockers:

- missing accessible name on meaningful SVG or duplicate announcement in an icon button;
- meaningful content available only by color, hover, animation, or path text;
- direct inline rendering of untrusted SVG;
- broken/missing `viewBox`, unresolved references, duplicate IDs, or post-SVGO visual damage;
- runtime API icon dependency without offline/loading/CSP handling;
- icon, asset, editor, export, or collection license not verified;
- data visualization without an equivalent summary and access to values.

## 10. Tool and license notes

GitHub adoption snapshot, 2026-07-14:

| Tool | Stars | License boundary | Best fit / caution |
| --- | ---: | --- | --- |
| [D3](https://github.com/d3/d3) | 113,216 | ISC | Data scales/axes/joins; accessibility and high mark-count strategy remain application work. |
| [Heroicons](https://github.com/tailwindlabs/heroicons) | 23,673 | MIT | Curated 16/20/24px UI families; narrower subject coverage. |
| [Lucide](https://github.com/lucide-icons/lucide) | 23,433 | ISC plus MIT-derived icons | Broad coherent stroke icons; preserve family weight and check attribution terms. |
| [SVGO](https://github.com/svg/svgo) | 22,583 | MIT | Optimization with type-specific config; never a sanitizer. |
| [DOMPurify](https://github.com/cure53/DOMPurify) | 17,205 | Apache-2.0 | Maintained SVG/HTML/MathML XSS sanitizer; does not cover upload/DoS/SSRF. |
| [SVG.js](https://github.com/svgdotjs/svg.js) | 11,804 | MIT text in repository | Programmatic illustration/interaction; manage DOM scale, lifecycle, IDs, and security separately. |
| [Iconify](https://github.com/iconify/iconify) | 6,218 | Framework MIT; each icon set separate | Huge coverage; prefer build-time/local assets when runtime API would add CSP/privacy/availability risk. |
| [svg-sprite](https://github.com/svg-sprite/svg-sprite) | 1,986 | MIT | Multi-mode sprite generation; configuration and external-use behavior need target-browser tests. |

Agent Skills that output SVG diagrams can inform layout workflows, but research found that most omit sanitizer, license, accessible-name, render-diff, and malicious-fixture gates. Do not treat “generated valid XML” as a finished SVG system.

The UI Skills entries for morphing icons and pseudo-elements contributed useful topology, unique-name, and cleanup reminders. Their technique-specific dependencies, style values, and browser claims were not adopted as universal requirements.
