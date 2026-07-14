# Visual-regression evidence

Use this reference when capturing screenshots, comparing renders, maintaining visual baselines, or making visual-fidelity claims.

## Know what a screenshot can prove

A screenshot can support `OBSERVED rendered_visual` for its exact route, state, data, viewport, browser, OS, DPR, fonts, locale, theme, preferences, and revision. It does not prove interaction, accessibility-tree behavior, responsive ranges, other browsers/devices, performance, or overall design quality.

Pixel comparison detects paint differences relative to a baseline. It cannot decide whether the baseline or change is better, whether a difference is meaningful, or whether unchanged UI satisfies the brief. Playwright notes that rendering varies with OS, version, settings, hardware, power source, headless mode, and other environment factors; generate and compare baselines in a controlled environment. See [Playwright visual comparisons](https://playwright.dev/docs/test-snapshots).

## Capture provenance

For every artifact, record:

```text
case/run id → commit/build hash → route + state/fixture
→ browser engine/version + OS/image + headless/headed + render backend
→ viewport + DPR + zoom + color profile
→ locale/timezone/theme/color-scheme/contrast/motion/transparency
→ font files/hashes + load completion → network/data/time/random controls
→ wait condition + scroll/focus/overlay/caret state
→ screenshot MIME/decoded dimensions/SHA-256 + capture time
→ diff engine/version/options/color space + mask/style policy
```

Validate that the image fully decodes; magic bytes, marker scans and declared dimensions are insufficient. The bundled ledger fully decompresses and validates PNG scanlines with the standard library. It accepts common 8-bit baseline/progressive JPEG only when an evaluator-owned Pillow installation can both `verify()` and fully `load()` the image after strict table/component/scan preflight; without that decoder JPEG fails closed rather than treating marker structure as decode proof. Pin and record the evaluator decoder version in run provenance. Bind the artifact hash to the evidence event. Replacing or deleting an artifact invalidates the claim. A provenance layout inspired by artifact/build systems can be useful, but do not call it SLSA-compliant without satisfying the actual [SLSA provenance specification](https://slsa.dev/spec/v1.2/provenance).

## Make the page deterministic

- Use stable fixture data, time, timezone, locale, random seed, auth state, routes, and feature flags.
- Wait for the named UI condition, fonts, and required media—not a guessed sleep.
- Disable or seek deterministic animation only for regression capture; separately test real motion and reduced motion.
- Stabilize caret, focus, scrollbars, cursor, lazy content, ads, clocks, third-party embeds, and network errors deliberately.
- Mask only truly nondeterministic content. Never mask the component or state under review, an overflow defect, or a failed asset.
- Keep browser/OS/font/DPR baselines separate when rasterization differs materially.

Do not update baselines automatically merely because CI failed. A reviewer must see baseline, candidate, and diff hashes/artifacts plus the intended product/code change, update reason, and baseline owner/reviewer.

Classify a mismatch as `product regression`, `intended change`, `environment drift`, `baseline defect`, or `noise/unresolved`; never make threshold expansion the automatic fix.

## Use three layers

1. **Structural assertions:** role/name/state/content/count/geometry invariants where deterministic.
2. **Targeted visual regression:** stable components and critical routes/states with a frozen environment.
3. **Human/blind craft review:** hierarchy, brand fit, material coherence, photography/crop, motion character, and whether the result is actually good.

A pixel threshold is a noise tolerance, not an acceptance score. Prefer focused element baselines for stable components and representative full-page captures for composition. Keep mobile, desktop, light/dark, long-locale, error, overlay, and forced/reduced-preference cases risk-based rather than screenshotting every permutation without review capacity.

Distinguish a viewport capture from a full-page document capture. Full-page stitching can paint fixed, sticky, or transformed off-canvas UI at a document boundary where a user would not see it in the named viewport. Use an exact viewport capture for first-screen and closed-overlay claims; keep full-page captures separately labelled, and verify suspicious fixed-position artifacts in the live viewport before reporting a UI defect.

## Freshness and repository claims

If README or documentation says an image comes from a specific implementation, store a small manifest binding screenshot hash to source/build hash, capture command, viewport, state, and environment. CI can detect staleness; it cannot approve a new visual direction.

For generated/AI benchmarks, preserve the raw output before repairs. Put corrected output under a new run ID or explicit repaired directory. Never replace a weak-model failure screenshot with a hand-fixed page while keeping the original score/provenance.

## No visual environment

Follow [no-visual-first-pass.md](no-visual-first-pass.md). Provide the exact future capture matrix and keep visual claims `UNVERIFIED`; synthetic token checks and source inspection cannot create screenshot evidence.

## Release blockers

- Screenshot provenance, decoded integrity, source binding, or exact state is missing for a visual pass claim.
- The baseline was silently regenerated, comes from a different environment, or masks the changed subject.
- A pixel diff is used as the sole proof of accessibility, interaction, or design quality.
- Dynamic data/fonts/animation make a blocking baseline nondeterministic without a documented policy.
- Documentation screenshots claim freshness without a source/build binding.
