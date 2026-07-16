# Site planning and wireframes

Use this reference when a request involves a multi-route site, unclear information architecture, a new product flow, a redesign with structural risk, or an explicit sitemap/wireframe/prototype deliverable. Skip it for a localized, low-risk component change whose routes, tasks, states, and content hierarchy are already known.

## Keep three artifacts separate

1. **IA sitemap** — routes, hierarchy, audiences, permissions, primary tasks, lifecycle, navigation, locale, and discovery intent.
2. **Wireframe plan / wireflow** — page regions, content priority, states, interactions, feedback, recovery, and desktop/mobile transformations.
3. **XML sitemap** — canonical indexable URLs for crawlers. It is not navigation, a product flow, or proof that a URL will be indexed.

Do not draw polished screens before the first two artifacts agree. Do not emit an XML sitemap from guessed routes or include authenticated, private, role-restricted, redirect, or `noindex` URLs.

## Evidence boundary

Every route and important region must be marked `provided`, `observed`, `hypothesis`, or `unknown`. Preserve the distinction:

- `provided`: the user or a named source supplied it.
- `observed`: found in the inspected project or a recorded test artifact.
- `hypothesis`: a design proposal to validate.
- `unknown`: material information is missing.

A wireframe is a planning artifact. It cannot self-certify comprehension, accessibility, usability, conversion, brand fit, or production readiness. Recall, visual saliency, preference, comprehension, task success, and conversion are different outcomes.

## IA sitemap contract

For each route record:

- stable route ID, normalized internal path, locale, parent, and lifecycle;
- page type, audience roles, visibility, primary task, and state triggers;
- primary/secondary/contextual/footer navigation placement;
- index/noindex, canonical URL, sitemap inclusion, alternates, and truthful `lastmod` when known;
- redirect target when applicable;
- evidence status and exact source references.

Reject duplicate normalized paths, unknown parents, parent cycles, orphaned public routes, external URLs in route paths, unsafe redirects, redirect cycles, private routes in public navigation, and non-indexable routes in XML sitemaps. Locale alternates must exist and be reciprocal.

## Wireframe fidelity ladder

Choose the least expensive fidelity that answers the uncertainty:

- `structural`: region hierarchy, content priority, navigation, and responsive order.
- `wireflow`: structural screens plus triggers, transitions, results, feedback, and recovery.
- `interactive_responsive`: deterministic local prototype for usability rehearsal across target viewports.

Do not use final visual polish to hide unresolved hierarchy or flow. Prototype code is disposable and must not be promoted to production without normal engineering review.

## Content and state coverage

Use representative content, not lorem ipsum. Include realistic extremes: long Traditional Chinese and mixed-script labels, empty collections, large counts, missing media, validation errors, permission boundaries, slow/loading states, and destructive-action recovery. Freeze only provided facts; label invented examples as hypotheses or fixtures.

Required states follow behavior, not page fashion:

| Trigger | Required states |
| --- | --- |
| `static` | default |
| `remote_data` | default, loading, empty, error |
| `form` | default, error, success |
| `auth_guard` | default, loading, permission |
| `mutation` | default, loading, error, success |

For each interaction record the initiating control, destination or changed region, visible result, feedback, failure recovery, keyboard path, and touch alternative. A hotspot with no feedback or recovery is incomplete.

## User-flow contract

A user flow is the short, product-level sequence used to complete one concrete goal. It is not a cross-channel journey map and not a list of available features. Record:

- one evidence-bounded audience role, goal, entry route, start step, and observable success criteria;
- each user trigger and the system response at the point of need;
- the page and required designed state for every step;
- the next primary step, risk, and recovery without discarding user effort;
- important alternate/error/permission paths and explicit success, abandoned, blocked, or recoverable-error exits;
- unknowns that require task analysis, contextual inquiry, analytics, or usability testing.

The primary chain must reach a terminal step and contain no accidental cycle or unreachable step. Alternate paths may intentionally return to a previous step for correction, but must explain the condition and recovery. An implementation-ready plan cannot be happy-path-only, and every active route must participate in at least one flow.

Map existing and proposed features back to these flows. Keep a feature only when it supports a named step, information need, system response, recovery, or safety constraint. A requested feature that interrupts the top task, duplicates another control, or has no evidenced point of need remains a hypothesis rather than automatically entering the interface.

## Page regions and hierarchy

Plan landmarks and heading hierarchy while arranging content. Each region needs a purpose, priority, content fixture, extreme case, and evidence status. Visual grouping does not replace semantic grouping. Forms, tables, diagrams, and dense dashboards may need alternate representations at narrow widths.

Use a simple saliency check only to inspect intended priority: after a brief exposure, ask what was noticed first. Do not treat recall as proof of comprehension or task success. Validate navigation labels and hierarchy with appropriate research such as card sorting or tree testing when the product risk warrants it.

### Choose a layout pattern from the task

Record `content operation → candidate pattern → focal anchor → reading/action sequence → mobile transformation → failure signal` before polishing. Common patterns are conditional:

- single-column flow for sustained reading or one focused decision;
- aligned comparison or split view only when users must compare or act while retaining context;
- grid/gallery/cards for independently browsable entities, not for turning every sentence into a container;
- master-detail for scanning records while preserving a selected record's context;
- magazine/F-like composition for scannable editorial density, with semantic headings carrying the hierarchy;
- horizontal rails only for a bounded collection with visible previous/next affordances and keyboard/touch alternatives;
- full-screen, animated, or immersive composition only when truthful media/evidence earns the space and the same task remains available without motion or media.

F-patterns, Z-patterns, thirds, symmetry, and asymmetry are teaching heuristics. They do not predict every user's gaze, comprehension, or conversion. Test the actual language, content density, task, viewport, input method, and reachable states; revert to a simpler structure when the pattern delays the top task or creates an unexplained track.

## Mobile is a transformation

For every desktop region choose one mobile action: preserve, reorder, replace, condense, defer, remove, or move to thumb reach. Record the equivalent access path and reason. Scaling the desktop canvas or merely stacking every region is not a mobile design.

Preserve task equivalence, not pixel equivalence. Keep essential controls reachable; replace dense tables when needed; provide touch alternatives for hover, cursor, drag, and precision interactions; respect safe areas, zoom, text expansion, and reduced motion.

## Prototype isolation

Interactive prototypes use local deterministic fixtures. Do not connect real authentication, payments, production APIs, personal data, analytics, or destructive actions. Shared prototypes require access control appropriate to their data. Record unknowns rather than inventing backend behavior.

## XML sitemap rules

Use absolute canonical URLs on approved origins. Each uncompressed sitemap is limited to 50,000 URLs and 50 MB. `lastmod` describes the page's meaningful last modification, not sitemap generation time. Sitemap submission is a crawl hint, never an indexing, ranking, AEO, or GEO guarantee.

## Research adoption boundary

- W3C WAI page-structure and information-design guidance informs landmarks, headings, labels, grouping, alternate representations, and responsive information structure.
- GOV.UK prototyping guidance informs fidelity choice, disposability, realistic interaction, and protection of shared prototypes.
- Nielsen Norman Group wireflows, card sorting, and tree testing inform flow representation and IA research selection.
- Nielsen Norman Group's user-flow, task-analysis, workflow, and error-recovery guidance informs goal scope, point-of-need controls, system responses, alternate paths, and effort preservation.
- Google Search Central and sitemaps.org define XML sitemap syntax and crawler boundaries.
- DayDayDing's practitioner article supplied useful prompts about real content, negative paths, roles, hierarchy, interaction detail, and responsive planning. Its undated/older tool survey is not treated as current tooling authority. The unsupported numerical claim that negative flows occur three-to-ten times as often as positive flows is not adopted.
- Figma's [website layout ideas](https://www.figma.com/resource-library/website-layout-ideas/) supplies a useful vocabulary for matching grids, split views, galleries, editorial flows, horizontal rails, interactivity, and animation to content. Its pattern descriptions, eye-path diagrams, and rule-of-thirds advice are discovery heuristics, not universal task or conversion evidence.
- YoungDay's [breathing layout article](https://www.youngday.com/breathtaking-web-design-layout.html) is a practitioner prompt to escape premature rectangle frames, build one focal region through contrast, and preserve proportion in asymmetry. Its geometry symbolism and aesthetic examples are not product facts or fixed recipes.
