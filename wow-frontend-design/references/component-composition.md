# Component and product-interface composition

Use this reference for design systems, component libraries, product applications, dashboards, data-heavy tools, commerce flows, settings, and any interface where primitives must compose across states. Components are behavior contracts, not a gallery of styled rectangles.

Use [typographic-layout.md](typographic-layout.md) for relationship-based component/card gaps, density calibration, measure, wrapping, and optical alignment.

## 1. Separate the layers

```text
foundations → primitives → composites → product patterns → route composition
```

- **Foundations**: semantic color, typography, spacing, layout, shape, surface/depth, icon, motion, focus, density.
- **Primitives**: link, button, input, checkbox, radio, switch, select, label, icon, separator.
- **Composites**: field, menu button, tabs, combobox, popover, dialog, accordion, table controls, pagination.
- **Product patterns**: search/filter, compare, bulk action, CRUD, settings, checkout, upload, approval, onboarding, status/recovery.
- **Route composition**: information hierarchy, navigation, density, responsive transformation, loading/failure/permission, and cross-pattern state.

Keep foundations stable while product composition adapts. Do not expose every token as a prop, turn one component into a giant configuration DSL, or build a second component system beside the existing one.

## 2. Freeze each component contract

```text
purpose → native semantic/owned primitive → content slots → states → controlled/uncontrolled ownership → input methods → focus/keyboard → announcements → responsive/density → localization/RTL → async/error → security/permission → performance → tests
```

Required states are the states the product can actually enter, commonly:

```text
rest + hover + focus-visible + active + selected/current + disabled/read-only
+ loading/pending + empty + partial/stale + error + success + permission/offline
```

- Distinguish disabled from unavailable-with-explanation, read-only, permission-denied, and pending.
- Keep visible label, accessible name, validation, count, price, status, and pressed/expanded/selected state synchronized.
- Define content limits by graceful behavior, not fictional character caps. Test empty, one, many, long `zh-Hant`, mixed scripts, user content, and unknown media.
- Reuse mature project primitives for focus/keyboard/ARIA-heavy widgets. Custom combobox, date picker, tree, grid, or editor requires a real product constraint and full target-browser/AT tests.

Use this source order: native HTML → WCAG/WAI-ARIA → current [WAI-ARIA APG](https://www.w3.org/WAI/ARIA/apg/) → Open UI research → the product's platform design system. Start with APG only when native semantics are insufficient. APG examples teach patterns; Open UI explainers track evolving vocabulary; neither is automatic production compatibility proof.

For forms, freeze the label and group semantics, hint/error linkage, validation timing, retained input after failure, paste/autofill/password-manager/IME behavior, and focus destination. Use a linked error summary when a long or high-consequence flow benefits from one; do not add it mechanically to every short form. Never block paste or silently discard an invalid value.

## 3. Choose the representation from the task

| Need | Prefer | Do not default to |
| --- | --- | --- |
| sequential reading or activity | semantic list/timeline | equal cards for every sentence |
| compare the same attributes | table or aligned comparison | unrelated card interiors |
| scan many records and act | data table/grid with stable columns | one tall card per row on desktop |
| browse visual entities | media list/grid with meaningful focal hierarchy | identical dashboard cards |
| master-detail workflow | split view, table/list + detail | navigating away after every selection |
| one focused decision | form/step or clear detail surface | dashboard shell with irrelevant chrome |
| small mutually exclusive views | tabs when labels remain visible and few | hidden carousel or dropdown |
| optional supporting detail | disclosure/popover depending persistence | modal for ordinary reading |

Cards are containment tools, not a design system. Use open composition, rows, groups, sections, tables, and spatial relationships when a border/radius around every item flattens hierarchy.

## 4. Distinguish menu, select, combobox, popover, and dialog

- Site/product navigation is usually links in `nav`, not ARIA `menu`. `role=menu` implies application-menu keyboard behavior.
- A disclosure reveals nearby content. A menu offers actions. A listbox/select chooses values. A combobox combines input/selection with a popup. Do not style one generic “dropdown” and change labels.
- A non-modal popover is transient supporting UI; it must dismiss coherently, preserve focus order, and not hide essential escape/navigation.
- A modal dialog interrupts the rest of the page. Move focus to a deliberate target, contain only while open, prevent background interaction/scroll, provide an accessible name and close path, restore focus, and clean all state on every exit.
- Prefer native `<button>`, `<select>`, `<details>`, `<dialog>`, and the HTML popover API where their current support and behavior satisfy the target. Preserve the semantic element even when using top-layer behavior.
- Hover/focus content follows WCAG dismissible, hoverable, persistent requirements where applicable. Every hover path needs touch/keyboard access.

Use [WHATWG popover](https://html.spec.whatwg.org/multipage/popover.html) and [Open UI](https://open-ui.org/) to understand evolving platform behavior. Research/explainers are not finished cross-browser contracts.

## 5. Design tables and data grids deliberately

For semantic data relationships, keep a real table:

- use a useful `<caption>`, `<th>`, and correct header associations; apply `scope` for simple structures and explicit `headers`/`id` only when the structure truly needs it;
- keep sort/filter state visible and announced; a sortable header is a button with current direction, not a clickable `<th>` alone;
- align numbers, units, decimals, dates, status, and actions consistently; use tabular numerals where it improves comparison;
- preserve row identity during loading, selection, optimistic updates, errors, pagination, and virtualized rendering;
- keep bulk selection, count, scope (“this page” versus “all results”), undo/confirmation, and destructive consequences explicit;
- for a virtualized ARIA table/grid, expose truthful `aria-rowcount`/`aria-colcount` and rendered `aria-rowindex`/`aria-colindex`, pin the focused row/cell instead of unmounting it, and preserve stable identity;
- provide a non-virtualized Find/print/export or equivalent task path when virtualization would hide records from browser search, assistive technology, printing, or copy workflows;
- do not claim a virtualized grid works with keyboard/AT until row/column context, focus, off-screen state, scrolling, target screen readers, and those fallback paths are tested.

Mobile transformation depends on the primary comparison:

1. preserve a horizontally scrollable table with visible affordance/frozen key column when cross-column comparison is essential;
2. show a prioritized summary row and open a detail view when one record at a time matters;
3. allow column visibility controls when users understand the schema;
4. never turn cells into unlabeled stacked values or silently remove decision-critical columns.

Follow the [W3C tables tutorial](https://www.w3.org/WAI/tutorials/tables/) for semantic data tables; ARIA grid behavior is a separate interactive pattern.

Charts, maps, sparklines, heatmaps, and KPI graphics require a separate analytical contract. Route palette semantics, zero/missing/uncertainty states, non-color redundancy, truthful scales, mobile transformation, and table/text alternatives through [data-visualization-color.md](data-visualization-color.md).

## 6. Build material and surface hierarchy

Surface treatment expresses grouping, elevation, interaction, and state:

- start with canvas, base surface, raised/transient surface, scrim, and focus/selection roles only when the product needs them;
- use spacing, alignment, border, tonal difference, and overlap before shadows or blur;
- reserve elevation for real stacking/transience. A shadow on every card destroys depth hierarchy;
- glass/blur requires a reason, contrast over every background frame, a no-transparency/high-contrast result, and measured paint/GPU cost;
- borders, radius, texture, and shadows follow a small semantic scale with documented exceptions—not one universal radius on every object;
- state color and material remain distinguishable in grayscale, forced colors, dark mode, reduced transparency, and low-quality media.

Do not merge Material Design, Apple HIG, Fluent, Carbon, GOV.UK, or another system into a universal visual style. Use the system already adopted by the product or treat each as a platform/context-specific reference.

## 7. Compose for desktop and mobile

Desktop can expose persistent navigation, comparison, shortcuts, hover detail, batch tools, and master-detail context. Mobile should select the top task, change navigation/control placement, defer secondary detail, protect the virtual keyboard, and provide tap alternatives.

For every composite region record:

```text
desktop role → mobile equivalent → preserved task/data → changed order/control/density → focus/history behavior → removed/deferred reason
```

The visual representation may change without duplicating product truth. Keep one logical record key, state owner, accessible identity, and interaction path across modes; hidden desktop/mobile copies with repeated IDs, hooks, or independently mutable controls are a release defect.

Component responsiveness is container-driven when possible. Page breakpoints do not guarantee a component fits a sidebar, modal, embedded card, or translated label.

## 8. Weak-model assembly rules

Give a weak model:

1. the existing component inventory and approved primitives;
2. the route's content/data/state schema;
3. one representation choice with rationale;
4. exact state and interaction manifest;
5. desktop/mobile composition table;
6. forbidden outputs: new library, custom complex widget, generic card conversion, gate edits;
7. evaluator-owned behavior checks.

Require one vertical slice—route shell plus one complete product workflow—before multiplying components. Repeated visual consistency is not proof of component correctness.

## 9. Verify the composition, not only Storybook

- semantic DOM, accessible name/role/state, keyboard/focus, touch/no-hover, screen-reader combinations actually operated;
- light/dark/forced colors, reduced motion/transparency, 200% text and 400%/reflow;
- long `zh-Hant`, mixed scripts, RTL claims, empty/one/many items, async race, permission, offline, stale and failure states;
- direct navigation, Back/Forward, refresh, route unmount, overlay A→B→A, repeated open/close, rapid input;
- container widths around every transition, phone/short landscape/tablet/desktop, virtual keyboard and safe area;
- production build extraction/hydration, console/network, bundle/render cost, repeated mount cleanup;
- visual regression at real optical sizes and density modes without replacing behavior assertions.

Release blockers include an inaccessible primary composite, custom widget without complete keyboard/focus semantics, table relationships destroyed on mobile, hidden destructive scope, stale async state, a material layer that makes content unreadable, and a component API that duplicates product truth.
