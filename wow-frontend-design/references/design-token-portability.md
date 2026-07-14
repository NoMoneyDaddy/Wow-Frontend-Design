# Design-token portability

Use this reference for design systems, multi-brand/theme products, cross-framework or cross-platform delivery, design-tool exchange, or token migrations. Do not force a token pipeline onto a small one-off page that only needs maintainable CSS custom properties.

## Separate format from architecture

The [DTCG Design Tokens Format Module 2025.10](https://www.w3.org/community/reports/design-tokens/CG-FINAL-format-20251028/) and [Color Module 2025.10](https://www.w3.org/community/reports/design-tokens/CG-FINAL-color-20251028/) are stable Community Group reports for interchange. They are not W3C Recommendations, do not choose a naming architecture, and do not prove that two tools preserve every extension or runtime behavior.

The format provides typed values, groups, aliases/references, composite values, extensions, deprecation, and JSON interchange. Project decisions still own:

- source of truth and write ownership;
- theme/brand/density/platform mode representation and resolution;
- primitive, semantic, and component naming layers;
- generated targets and fallback policy;
- versioning, migration, review, and visual verification.

Do not claim the base format standardizes a tool's proprietary “modes.” If a tool encodes modes as separate sets, group extension, files, or `$extensions`, document that mapping and test round trips. Critical meaning must not exist only in an opaque extension. The DTCG resolver report is useful but its published version metadata has known ambiguity; pin the exact document/hash and conformance fixtures instead of hard-coding a remembered resolver version.

## Use the fewest useful layers

A common architecture is optional, not law:

```text
source/primitive → semantic role → component role → platform output
```

- **Source/primitive** records an authored palette, dimension, type ramp, duration, or other raw value.
- **Semantic** records intent such as `text.primary`, `surface.raised`, `action.primary.background`, or `motion.feedback.fast`.
- **Component** exists only when a component needs a stable exception or public contract that cannot be expressed by semantic roles.
- **Platform output** translates units, naming, capabilities, and fallbacks; it is generated, not another source of truth.

Avoid both extremes: components referencing raw palette values everywhere, and thousands of component tokens that merely duplicate semantic aliases.

## Freeze the resolution contract

```text
token source/version/hash
→ selected brand/theme/contrast/density/platform modes
→ alias and group-extension resolution
→ validated typed graph
→ target transform/version
→ generated manifest/hash
→ component/render evidence
```

Fail on unresolved or circular aliases, invalid typed values, name collisions after target normalization, unsupported color spaces/units, lost extension data, and generated drift. DTCG names are case-sensitive, but some outputs normalize case; reject collisions before generation.

Keep theme semantics explicit. `light`, `dark`, increased contrast, and forced colors are not palette suffixes alone; the runtime source/override and platform behavior live in [color-system-psychology.md](color-system-psychology.md).

## Type and color rules

- Emit a valid `$type` or inherit it from an intentional group; never guess type from value shape.
- Preserve color space and alpha. Provide the project's required sRGB fallback before wide-gamut output.
- Treat composite border, shadow, gradient, typography, and transition tokens as value bundles, not proof the composed component is coherent or accessible.
- Do not place copy, component behavior, accessibility names, asset rights, or research conclusions into style tokens.
- A token called `accessible` or `highContrast` still needs rendered checks.

## Migration and governance

- Inventory real consumers before renaming or flattening aliases.
- Mark deprecated tokens with replacement and removal version; keep compatibility only for a bounded period.
- Generate change reports: added, changed, removed, deprecated, resolved-value changes, and affected consumers.
- Review semantic changes as product changes, even when the raw value is unchanged.
- Pin transformer/version/config and verify clean regeneration in CI.
- Keep credentials, private brand assets, and unreleased campaign data out of public token packages.
- Record licenses for tools and bundled token libraries; an interchange spec does not license third-party palettes, fonts, icons, or themes.

## Weak-model contract

```text
SCOPE: local CSS variables | shared design system | cross-tool | cross-platform
SOURCE OF TRUTH:
LAYERS USED AND WHY:
MODE RESOLUTION:
ALIAS/COLLISION/TYPE POLICY:
TARGETS + FALLBACKS:
DEPRECATION/MIGRATION:
GENERATED + RENDERED EVIDENCE:
```

If the repository already has tokens, extend its naming and generator instead of creating a parallel system. If no cross-tool need exists, prefer a small semantic token set in the detected stack.

## Release blockers

- Runtime or generated output can resolve the same semantic token differently without an explicit mode/platform contract.
- Alias cycles, missing values, normalized-name collisions, or unsupported types are silently accepted.
- Generated files drift from the reviewed source or are hand-edited without a round-trip policy.
- Raw palette tokens bypass semantic roles in reusable components without an evidenced exception.
- Tool round-trip loses values/extensions required for correct output.
- “DTCG-compatible” is claimed without validating the exact files and tool versions.
