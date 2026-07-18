# Interaction audit

Use this reference for interactive products, multi-step tasks, overlays, forms, navigation state, and browser-based review. It defines evidence coverage, not permission to mutate or submit real data.

## 1. Freeze the interaction manifest

Before browser work, list only in-scope interactions:

| ID | Route/state | Start condition | Action/input | Expected B state | Return action | Expected restored A state | Side-effect class | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Side-effect classes:

- `none`: local disclosure, tabs, hover/focus, client-only filters;
- `reversible`: draft/edit in an evaluator-owned test account with a documented undo;
- `external`: messages, purchases, invitations, production writes, uploads, public changes, or third-party actions.

Do not create fake production data or exercise an external side effect without explicit authorization and safe fixtures. Audit/report requests remain read-only.

## 2. Test A → B → A, not only the happy action

For each applicable manifest row:

1. Record A: URL, visible state, focus owner, scroll position, accessible name/state, console/network baseline.
2. Perform the authorized input through the real user path.
3. Record B and verify content, state, focus, announcement, URL/history, loading/error behavior, and duplicate submission protection.
4. Return through every applicable path: close button, Escape, Back, internal navigation, cancel, invalidation, retry, route unmount, or reload.
5. Verify restored A: no stale announcement, scroll lock, focus trap, timer, listener, pending request, URL parameter, or optimistic state.
6. Repeat rapid input and one failure path when the interaction is stateful or asynchronous.

Failure and retry must be reachable through the real user path. A retry that only reopens the same error is not recovery. If rendering replaces the opener, store a stable trigger identity and resolve the current live element before returning focus; a saved detached DOM node is not valid focus-return evidence.

For an isolated or client-only demo, visible success text must say that the result is local, simulated, queued, or unsynced as applicable. Never imply a server write, email, payment, upload, or support ticket occurred.

For destructive actions, verify confirmation, target identity, cancellation, error recovery, and authorization without executing a real irreversible change unless specifically approved.

## 3. Use a first-time-user lens

Check whether a person without project context can identify:

- the current place, next action, consequence, and escape path;
- whether a control is available, busy, selected, expanded, invalid, or complete;
- why an action failed and how to recover;
- whether visible state survives or intentionally resets across Back/Forward, reload, locale, and viewport changes.

Do not infer clarity from the component name or implementation intent. Observe the rendered label, surrounding content, focus order, and result.

## 4. Record honest coverage

```text
covered manifest rows / applicable manifest rows
covered return paths / applicable return paths
covered failure paths / applicable failure paths
```

List exclusions and blockers. A short duration, high percentage, clean console, axe pass, or one screenshot does not prove the task is usable. Deduplicate shared root causes while retaining affected rows and routes.

Each finding should include:

```text
severity → manifest ID + route/state → reproduce → user impact → rendered/DOM/network evidence → suspected source location → smallest fix → same-path recheck
```

Source mapping is a pointer. Confirm the cause before editing.

## 5. Browser evidence discipline

- Keep one browser session when testing viewport transitions so route, data, and interaction state remain comparable.
- Capture before and after at the same viewport, locale, theme, motion preference, auth state, and fixture.
- Check DOM/accessibility state plus rendered output; neither alone is sufficient.
- Record browser/tool/version and raw artifacts. Do not use unpinned `@latest` browser tooling in a release gate.
