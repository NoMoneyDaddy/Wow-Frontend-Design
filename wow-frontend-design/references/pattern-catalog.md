# Pattern catalogue router

Use this reference when a request names a page block or UI component but does not yet establish whether that pattern fits. This is a coverage map, not a template menu. Select from task/content/state evidence, then route to the specialized contract.

## 1. Pattern decision record

```text
named pattern → user task/content relationship → simpler native/existing option → selected behavior → desktop/mobile transformation → states/data/trust → accessibility/security/performance → evidence
```

Reject a pattern when it only fills space, imitates a gallery, duplicates another region, hides weak content, or adds a runtime with no product role.

## 2. Content and brand blocks

| Patterns covered | Use when | Guardrails and routes |
| --- | --- | --- |
| **Announcements, Hooks, Heroes, Calls to Action** | a timely change, proposition, or next action genuinely needs priority | keep one truthful focal message and consequence; no manufactured urgency, auto-dismissed essential notice, generic two-CTA hero, or motion-gated copy. Route creative, brand, localization, mobile. |
| **Features, Comparisons, Pricing Sections, Stats & KPIs** | users must understand capability, choose, or verify value | use real comparable attributes, units, terms, update time, source, caveats, and decision order; no invented metrics, crossed-out prices, fake scarcity, or unequal comparison framing. Route product interface, data/table, security for transactions. |
| **Clients, Team Sections, Testimonials, Profiles, Avatars** | identity/provenance builds legitimate trust or enables a task | require consent/source and truthful relationship; never fabricate logos, people, quotes, ratings, portraits, or endorsements. Handle absent/private identity and resilient user media. |
| **FAQs, Texts, Lists, Timelines** | the content has real questions, sequence, chronology, or reference value | use semantic headings/list/time, searchable/direct links when useful, and honest reading order; do not hide core terms in accordions or number decorative steps as a fake process. |
| **Galleries, Images, Videos** | media is evidence, product, portfolio, instruction, or deliberate atmosphere | provenance/license, art direction, captions/alt/transcript, controls, responsive sources, poster/failure, LCP/data budget. Route visual storytelling and advanced media. |
| **Backgrounds, Borders, Gradients, ASCII Art** | the visual grammar assigns texture, separation, diagram, code/craft voice, or atmosphere | decoration never carries sole meaning or reduces contrast; ASCII needs a plain-text/semantic equivalent and robust monospace/wrapping; gradients/borders follow semantic roles, not novelty. |
| **Footers, Navigation Menus, Sidebars, Docks** | information architecture or frequent peer/action access requires persistent structure | correct landmarks/current state, keyboard/touch/safe areas, compact mobile replacement, overflow and focus; dock is not a generic premium trope. |

## 3. Product UI components

| Patterns covered | Contract focus |
| --- | --- |
| **Accordions, Tabs, Steppers, Onboarding** | correct persistence/sequence, visible progress, deep-link/history where product expects it, no hidden errors, Back/Forward and mobile transformation |
| **Alerts, Badges, Tags, Notifications, Toasts, Progress, Spinner Loaders, Empty States** | severity/status semantics, visible and announced update without noise, persistence/dismissal, no color-only state, real progress versus indeterminate, truthful empty cause and useful retry/next action |
| **Buttons, Links, Toggles, Checkboxes, Radio Groups** | native element/action versus navigation, label and hit target, focus/pressed/checked/disabled/read-only, pending/double-submit, destructive consequence |
| **Inputs, Text Areas, Forms, Search Bars, Selects, Date Pickers, Sliders** | visible labels/instructions, autocomplete/input purpose, locale/date/number/IME, paste, validation and recovery, native-first control, async race and keyboard/touch behavior |
| **Dropdowns, Menus, Popovers, Tooltips, Dialogs / Modals** | correct pattern taxonomy, trigger/state/name, top layer, dismiss/Escape, focus movement/return, background interaction, positioning/viewport, touch equivalent |
| **File Uploads, File Trees** | permission, type as hint not trust, byte/count/name/path limits, progress/cancel/retry, malware/active-content boundary, hierarchy keyboard behavior, partial failure |
| **Tables, Paginations, Numbers, Charts & Data Viz, Dashboards** | data relationships, units/source/freshness, density/comparison, sort/filter/selection/bulk scope, exact-value equivalent, pagination/virtualization, mobile summary/detail without lost decisions |
| **Cards, Grids & Bento** | only when items share a useful scan/comparison model; establish focal hierarchy, semantic reading order, container behavior and unequal priority instead of equal rounded boxes |
| **Calendars** | locale/time zone/week start, range and unavailable state, keyboard grid behavior, agenda/list alternative, density and mobile schedule composition |
| **AI Chats** | model/provider identity, streaming/stop/retry/edit, citations/provenance, tool/action confirmation, unsafe output rendering, privacy/retention, cost/rate limit, accessible transcript and failure |
| **Sign Ins, Sign ups** | password manager/passkey/autocomplete, accessible authentication, error/recovery, verification/rate limit, privacy/terms, session/redirect/CSRF—not conversion tricks |
| **Icons** | coherent licensed family, recognizable metaphor, optical sizes, use-site accessible name, RTL/state pair, SVG trust/optimization; route SVG system |

The detailed cross-state/component rules live in [component-composition.md](component-composition.md); security-sensitive flows load [frontend-security.md](frontend-security.md).

## 4. High-risk expression layer

These patterns are not selected from taste or award-gallery frequency. Promote one only after the content/product layer is usable and the pattern decision record proves a product-specific role.

| Patterns covered | Admission test | Mandatory gates and routes |
| --- | --- | --- |
| **Marquees, auto-moving Carousels, ambient/hero Videos** | motion or time genuinely communicates sequence, continuity, product behavior, or atmosphere that a static composition cannot carry as well | visible controls, pause/stop, no motion-gated content, captions/transcript/poster, slow/failure state, reduced static result, off-screen pause, data/energy budget. Route motion, visual storytelling, advanced media. |
| **Custom Scroll Areas, scroll-linked scenes, Cursors** | the native input/scroll model cannot express a named product task or spatial relationship | preserve native scroll/selection and browser navigation, keyboard/touch/no-hover alternative, focus/zoom, interruption/cleanup, reduced motion. Scroll hijacking and cursor replacement default to rejected. Route motion, interaction audit, mobile. |
| **Maps, Globes** | location, topology, route, or spatial comparison is essential to the task | DOM address/list/search or table alternative, keyboard/touch/zoom, attribution/license, privacy/API key, tile/data failure, geolocation consent, clustering, bounded rendering and static fallback. Route advanced media, security, data visualization. |
| **Shaders, WebGL/Three spatial scenes** | a measured product-specific material, spatial, simulation, or data behavior cannot be expressed more cheaply | semantic DOM/poster first, feature/asset/compile/context failure, bounded loop/DPR/assets, target-device trace, reduced result, context restoration, cleanup, shader/source trust. Route advanced media, motion, security. |
| **Animated ASCII Art, generative backgrounds, heavy blend/blur effects** | the product concept assigns the effect a semantic or authored identity role | semantic/plain alternative, contrast over every state/frame, font/wrapping or render fallback, effect budget, reduced transparency/motion, forced colors, failure cleanup. Route visual material, color, motion. |

Failure of an admission test routes back to a static/native pattern; it does not invite the model to justify the effect with adjectives. High-risk patterns never become the only content, navigation, evidence, or task path.

## 5. Composition families

Use the smallest family that serves the task:

```text
reading → heading/paragraph/list/timeline
choice → form/listbox/radio/comparison
browse → list/grid/gallery/map
operate → table/dashboard/master-detail
sequence → stepper/form/onboarding
transient support → disclosure/popover/tooltip
interrupt → dialog only when interaction outside must stop
status → inline state/alert/toast/notification based on persistence and action
```

Do not compose every available block. A route earns each region through content priority. A product application may have no hero, testimonials, pricing, gradient, bento, or footer; a focused editorial page may have no dashboard, cards, sidebars, or modal.

## 6. Mobile transformation prompts

For the selected pattern ask:

- Does persistent desktop context become a sheet, focused detail, bottom action, or progressive disclosure?
- What comparison/data must remain simultaneous rather than stacked?
- What hover, drag, pointer, keyboard shortcut, or wide visual needs a tap/button/summary alternative?
- What fixed UI collides with safe area, browser chrome, landscape, or virtual keyboard?
- Which media needs a different crop/poster/density rather than a smaller copy?
- Can a user resume the task after interruption, navigation, error, or authentication?

## 7. Verification gate

Verify the selected pattern in its real composition—not only an isolated demo:

- semantics/name/role/state and actual keyboard/focus/touch behavior;
- empty/one/many/long/async/error/permission/offline and A→B→A cleanup;
- 320/390/tablet/desktop plus adjacent transition widths, zoom, long `zh-Hant`, RTL claims;
- reduced motion, forced colors, no-hover, slow/failed media/network;
- security, privacy, rights, truth claims, console/network, build/hydration, lifecycle/performance;
- existing design-system/API compatibility and no unnecessary new dependency.
