# WCAG 2.2 A/AA conformance checklist

Use this reference when a project targets or claims WCAG 2.2 AA. This is a working applicability checklist, not a replacement for the normative [WCAG 2.2 specification](https://www.w3.org/TR/WCAG22/) and its linked Understanding documents.

## Conformance rules first

- Mark every criterion `pass`, `fail`, or `not applicable`, with evidence.
- Meet every applicable Level A and AA criterion. Scores and partial percentages cannot compensate for failures.
- Evaluate complete pages, every responsive variation, and each complete process in scope—not only sampled components or the happy path.
- Include third-party and embedded content that is part of the claimed page unless a documented conformance rule applies.
- Treat automated tools as discovery aids. Verify semantics, keyboard paths, reading/focus order, timing, media, errors, authentication, and rendered states manually.
- Do not claim AA if any applicable criterion is untested or fails. Report “AA-oriented” or “not fully audited” instead.

## Perceivable

### 1.1 Text alternatives

- [ ] **1.1.1 A — Non-text Content:** Give meaningful non-text content an equivalent; mark decoration so assistive technology ignores it; handle controls, tests, sensory content, CAPTCHA, and complex visuals appropriately.

### 1.2 Time-based media

Mark not applicable only after confirming no relevant media exists.

- [ ] **1.2.1 A — Audio-only and Video-only (Prerecorded):** Provide the required transcript or equivalent alternative.
- [ ] **1.2.2 A — Captions (Prerecorded):** Caption prerecorded synchronized media.
- [ ] **1.2.3 A — Audio Description or Media Alternative (Prerecorded):** Provide audio description or a full media alternative as applicable.
- [ ] **1.2.4 AA — Captions (Live):** Caption live synchronized media.
- [ ] **1.2.5 AA — Audio Description (Prerecorded):** Provide audio description for prerecorded video content.

### 1.3 Adaptable

- [ ] **1.3.1 A — Info and Relationships:** Programmatically expose structure, labels, groups, table relationships, and visual meaning.
- [ ] **1.3.2 A — Meaningful Sequence:** Keep reading and interaction order meaningful when presentation changes.
- [ ] **1.3.3 A — Sensory Characteristics:** Do not rely only on shape, color, size, visual location, orientation, or sound in instructions.
- [ ] **1.3.4 AA — Orientation:** Do not lock portrait or landscape unless essential.
- [ ] **1.3.5 AA — Identify Input Purpose:** Use programmatic input purposes for fields collecting user information.

### 1.4 Distinguishable

- [ ] **1.4.1 A — Use of Color:** Do not use color as the sole carrier of information, action, response, or distinction.
- [ ] **1.4.2 A — Audio Control:** Let users pause/stop or independently control audio that starts automatically for more than three seconds.
- [ ] **1.4.3 AA — Contrast (Minimum):** Meet 4.5:1 for normal text and 3:1 for qualifying large text, with only the documented exceptions; never round a failure up.
- [ ] **1.4.4 AA — Resize Text:** Support 200% text resizing without loss of content or function, except documented exceptions.
- [ ] **1.4.5 AA — Images of Text:** Use real text when the presentation can be achieved with text, except customizable or essential cases.
- [ ] **1.4.10 AA — Reflow:** Reflow at 320 CSS px width (commonly 400% at 1280px) without two-dimensional scrolling, except content that inherently requires it; for content designed to scroll horizontally, including vertical writing, use 256 CSS px height.
- [ ] **1.4.11 AA — Non-text Contrast:** Reach 3:1 for essential component states and graphical information against adjacent colors, subject to documented exceptions.
- [ ] **1.4.12 AA — Text Spacing:** Preserve content and function when users override line, paragraph, letter, and word spacing to the criterion values.
- [ ] **1.4.13 AA — Content on Hover or Focus:** Make additional hover/focus content dismissible, hoverable, and persistent unless an exception applies.

## Operable

### 2.1 Keyboard accessible

- [ ] **2.1.1 A — Keyboard:** Make all functionality operable through a keyboard interface without timing-specific keystrokes, except essential paths.
- [ ] **2.1.2 A — No Keyboard Trap:** Let focus leave every component using standard or clearly instructed methods.
- [ ] **2.1.4 A — Character Key Shortcuts:** Let users turn off, remap, or focus-scope single-character shortcuts.

### 2.2 Enough time

- [ ] **2.2.1 A — Timing Adjustable:** Let users turn off, adjust, or extend applicable time limits, with only documented exceptions.
- [ ] **2.2.2 A — Pause, Stop, Hide:** Control moving, blinking, scrolling, or auto-updating content that meets the criterion conditions.

### 2.3 Seizures and physical reactions

- [ ] **2.3.1 A — Three Flashes or Below Threshold:** Keep flashing within the allowed threshold.

### 2.4 Navigable

- [ ] **2.4.1 A — Bypass Blocks:** Provide a way to bypass repeated content.
- [ ] **2.4.2 A — Page Titled:** Give each page a descriptive title.
- [ ] **2.4.3 A — Focus Order:** Keep sequential focus order meaningful and operable.
- [ ] **2.4.4 A — Link Purpose (In Context):** Make each link purpose understandable from its text or programmatic context.
- [ ] **2.4.5 AA — Multiple Ways:** Provide more than one way to locate pages in a set, except steps in a process.
- [ ] **2.4.6 AA — Headings and Labels:** Make headings and labels describe topic or purpose.
- [ ] **2.4.7 AA — Focus Visible:** Ensure keyboard-operable UI has a visible focus indicator.
- [ ] **2.4.11 AA — Focus Not Obscured (Minimum):** Ensure author-created content does not entirely hide the focused component.

### 2.5 Input modalities

- [ ] **2.5.1 A — Pointer Gestures:** Provide a single-pointer, path-independent alternative to multipoint or path gestures unless essential.
- [ ] **2.5.2 A — Pointer Cancellation:** Avoid committing on pointer-down when the criterion requires cancellation, reversal, or an up-event.
- [ ] **2.5.3 A — Label in Name:** Include visible control text in its accessible name.
- [ ] **2.5.4 A — Motion Actuation:** Provide a UI alternative and allow motion activation to be disabled, unless operated through an accessibility-supported interface or motion is essential.
- [ ] **2.5.7 AA — Dragging Movements:** Provide a non-drag single-pointer alternative unless dragging is essential or user-agent controlled.
- [ ] **2.5.8 AA — Target Size (Minimum):** Make pointer targets at least 24×24 CSS px or satisfy a documented Spacing, Equivalent, Inline, User Agent Control, or Essential/legally-required exception. Keep 44×44 as a stronger internal touch target where practical.

## Understandable

### 3.1 Readable

- [ ] **3.1.1 A — Language of Page:** Programmatically identify the page language.
- [ ] **3.1.2 AA — Language of Parts:** Identify language changes in passages and phrases, except proper names, technical terms, indeterminate language, and vernacular context.

### 3.2 Predictable

- [ ] **3.2.1 A — On Focus:** Focus alone does not trigger a context change.
- [ ] **3.2.2 A — On Input:** Changing a control does not unexpectedly change context unless users were advised.
- [ ] **3.2.3 AA — Consistent Navigation:** Keep repeated navigation in the same relative order unless users change it.
- [ ] **3.2.4 AA — Consistent Identification:** Identify same-function components consistently.
- [ ] **3.2.6 A — Consistent Help:** Keep repeated help mechanisms in the same relative order unless users change it.

### 3.3 Input assistance

- [ ] **3.3.1 A — Error Identification:** Identify input errors and describe them in text.
- [ ] **3.3.2 A — Labels or Instructions:** Provide labels or instructions when input is required.
- [ ] **3.3.3 AA — Error Suggestion:** Suggest a correction when known and safe.
- [ ] **3.3.4 AA — Error Prevention (Legal, Financial, Data):** Make consequential submissions reversible, checked, or confirmable.
- [ ] **3.3.7 A — Redundant Entry:** Auto-populate or make repeated information selectable within the same process, with documented exceptions.
- [ ] **3.3.8 AA — Accessible Authentication (Minimum):** Do not require a cognitive-function test unless an allowed alternative, assistance, object recognition, or personal-content mechanism applies.

## Robust

### 4.1 Compatible

- [ ] **4.1.2 A — Name, Role, Value:** Programmatically expose names, roles, states, properties, and user-settable values; notify assistive technology of changes.
- [ ] **4.1.3 AA — Status Messages:** Expose status messages programmatically without moving focus unnecessarily.

## Evidence record

For each criterion, record:

```text
SC:
Applicability: applicable | not applicable (reason)
Pages/processes/variations checked:
Tools and manual method:
Evidence:
Result: pass | fail | unverified
Defect/follow-up:
```

If scope, content, or UI states change after the audit, re-evaluate affected criteria and complete processes.
