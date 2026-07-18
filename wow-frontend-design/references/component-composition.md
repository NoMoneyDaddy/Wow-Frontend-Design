# Component and product-interface composition

Use this reference as the single owner of task-to-representation decisions and component, state, and mobile contracts for product interfaces. It covers design systems, applications, dashboards, data-heavy tools, commerce, settings, and other surfaces where shared primitives compose into product behavior.

Route named patterns through [pattern-catalog.md](pattern-catalog.md), interaction replay through [interaction-audit.md](interaction-audit.md), visual-system rules through `DESIGN.md` and the routed visual references, and security-sensitive behavior through [frontend-security.md](frontend-security.md). Components are behavior contracts, not visual recipes.

## 1. Keep the composition layers explicit

```text
foundations → primitives → composites → product patterns → route composition
```

- **Foundations**: semantic color, typography, spacing, layout, shape, icon, motion, focus, and density roles owned by the visual system.
- **Primitives**: link, button, input, checkbox, radio, switch, select, label, icon, and separator.
- **Composites**: field, menu button, tabs, combobox, popover, dialog, accordion, table controls, and pagination.
- **Product patterns**: search/filter, compare, bulk action, CRUD, settings, checkout, upload, approval, onboarding, and status/recovery.
- **Route composition**: hierarchy, navigation, density, responsive transformation, state coverage, and cross-pattern ownership.

Keep foundations stable while route composition adapts. Extend the existing system instead of creating a parallel one. Do not expose every token as a prop or turn one component into a configuration language for unrelated tasks.

## 2. Choose representation from product evidence

Before selecting components, record this decision input:

```text
top task + data relationship + comparison need + stable record identity
+ task frequency + consequence/risk + content pressure + mobile context
```

The decision output must contain:

```text
chosen representation + rejected simpler alternative + proof to collect
```

The rejected alternative is the simplest credible option, not a straw man. Proof names the behavior, content extreme, and desktop/mobile state that would show the choice preserves the task. If evidence does not distinguish two options, choose the simpler native composition.

| Task/data need | Prefer | Simpler alternative to reject only with evidence |
| --- | --- | --- |
| sequential reading or activity | semantic list or timeline | plain ordered list |
| compare the same attributes | table or aligned comparison | compact definition list per item |
| scan many records and act repeatedly | data table/grid with stable columns and record keys | semantic list with row actions |
| browse visual entities | media list/grid with meaningful focal hierarchy | semantic media list |
| preserve list context while inspecting records | list/table plus detail region | navigation to a detail route |
| make one focused decision | form, step, or focused detail surface | one native form section |
| switch among a few peer views | tabs with persistent visible labels | headings with in-page links |
| reveal optional supporting detail | disclosure or non-modal popover according to persistence | inline supporting text |

Cards are containment tools, not a default representation. Prefer rows, groups, sections, tables, or open spatial relationships when repeated containers erase data relationships or action priority.

## 3. Freeze the behavior contract

For every new or changed primitive, composite, or product pattern, define:

```text
purpose → native semantic or owned primitive → content slots → public variants
→ state owner → controlled/uncontrolled boundary → input methods
→ accessible name/role/state → focus/keyboard → announcements
→ async/error/permission → responsive and density behavior
→ localization/RTL → performance boundary → contract tests
```

Required states are those the product can actually enter, commonly:

```text
rest + hover + focus-visible + active + selected/current + disabled/read-only
+ loading/pending + empty + partial/stale + error + success + permission/offline
```

- Distinguish disabled, read-only, pending, permission-denied, and unavailable-with-explanation.
- Keep visible label, accessible name, validation, count, price, status, and pressed/expanded/selected state synchronized.
- Define content limits by graceful behavior. Test empty, one, many, long `zh-Hant`, mixed scripts, user content, and missing or unknown media.
- Bind record-scoped title, metadata, controls, progress, evidence, and async results to one stable record key. Selection or navigation changes must not leave another region or delayed result bound to the prior record.
- Freeze form label/group semantics, hint/error linkage, validation timing, retained input after failure, paste/autofill/password-manager/IME behavior, and focus destination. Never block paste or silently discard invalid input.
- Prefer native HTML, then a mature project primitive. A custom combobox, date picker, tree, grid, or editor needs a product constraint and target browser/assistive-technology verification.

Use native HTML and WCAG/WAI-ARIA requirements first; use the current [WAI-ARIA APG](https://www.w3.org/WAI/ARIA/apg/) as pattern guidance when native semantics are insufficient. Examples and research vocabularies are not production compatibility proof.

## 4. Preserve semantic component identity

- **Navigation** uses links in `nav`; `role=menu` is reserved for application-menu behavior.
- **Disclosure** reveals nearby content; **menu** offers actions; **select/listbox** chooses a value; **combobox** combines input or selection with a popup.
- **Popover** is transient supporting UI and remains non-modal. **Dialog** interrupts the page, has an accessible name and explicit close path, contains interaction only while open, and restores focus when it closes.
- **Tabs** switch a small set of peer views and keep their labels visible; they do not hide a long route hierarchy.
- **Table** expresses row/column relationships. A sortable header owns a button and announced direction; bulk selection exposes count, scope, consequence, and recovery.
- **Grid/tree/editor** implies an interactive keyboard and focus model. Do not apply the role only to obtain styling or density.

For semantic tables, preserve caption/header associations, stable row identity, visible sort/filter state, aligned comparable values, and truthful selection scope. Virtualized tables/grids must preserve focus and row/column context, expose truthful indices/counts, and provide an equivalent Find, print, export, or non-virtualized task path when hidden records would otherwise become unreachable. Follow the [W3C tables tutorial](https://www.w3.org/WAI/tutorials/tables/) for data-table semantics.

Charts, maps, heatmaps, and KPI graphics have a separate analytical contract; route palette semantics, uncertainty, scales, non-color redundancy, and text/table alternatives through [data-visualization-color.md](data-visualization-color.md).

## 5. Keep one identity across desktop and mobile

For every composite region, record:

```text
region + desktop role + mobile equivalent + preserved task/data/record key
+ changed order/control/density + deferred or removed content and reason
```

Desktop may expose persistent comparison, shortcuts, batch tools, hover detail, or master-detail context. Mobile may reorder priorities, replace wide controls, move actions into thumb reach, or defer secondary detail. The representation may change; product truth, state ownership, accessible identity, and task outcome must not.

Choose the mobile table form from the comparison need: retain a scrollable table when cross-column comparison is primary; use a prioritized row plus detail when one record matters at a time; offer column controls only when users understand the schema. Never emit unlabeled stacked values or remove decision-critical columns silently.

Avoid independently mutable desktop/mobile copies, repeated IDs or evaluator hooks, and breakpoint-specific state owners. Prefer container-driven component adaptation because a page breakpoint does not prove a component fits a sidebar, dialog, embed, or expanded locale.

## 6. Verify the component-specific contract

Verify only applicable rows, but require evidence for every public behavior changed:

- **Primitive/control**: native semantics, accessible name/role/state, focus-visible, keyboard, touch/no-hover, disabled/read-only/pending distinctions, and long-label behavior.
- **Form/field**: label/group and error linkage, invalid input retention, IME/paste/autofill, submit pending/resolve/reject, duplicate prevention, and focus destination.
- **Disclosure/menu/popover/dialog/tabs**: semantic identity, trigger state, keyboard/touch operation, dismissal or selection behavior, focus containment/return where applicable, and cleanup after close/unmount.
- **List/table/grid**: stable record identity, sorting/filtering/pagination, selection scope, count and aggregate coherence, empty/loading/stale/error states, virtualization focus/context, and copy/Find/print/export equivalence where promised.
- **Record selection or async composite**: non-default record selection, selection change during pending work, stale-result prevention, and consistent title/metadata/evidence/actions/progress.
- **Responsive composite**: the declared desktop/mobile equivalence, content extremes near each container transition, phone/short-landscape/tablet/desktop composition, virtual keyboard, safe area, and no duplicated state or hooks.
- **Localized component**: long `zh-Hant`, mixed scripts, claimed RTL behavior, natural wrapping, atomic command labels, and state announcements.
- **Custom complex widget**: complete target-browser and assistive-technology keyboard/focus model, not only static ARIA attributes or a Storybook render.

Run component checks in the production build path when extraction, hydration, virtualization, or route mounting can change behavior. Visual regression may support the contract, but it cannot replace semantic, state, and interaction assertions.

Release blockers include an inaccessible primary composite, custom widget without complete keyboard/focus behavior, destroyed table relationships on mobile, hidden destructive scope, duplicated product truth, stale record-bound async state, or a public component API whose state ownership is ambiguous.
