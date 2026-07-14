# Frontend security boundaries

Use this reference when the interface renders user/CMS/AI content, accepts uploads, handles authentication or payments, embeds third parties, opens external URLs, uses `postMessage`, adds telemetry, or changes security headers. Frontend controls complement server enforcement; they do not create authorization by themselves.

## 1. Map trust and data flow

Record:

```text
source → trust/owner → validation/encoding → storage/cache → renderer/sink → browser capability → server enforcement → logging/privacy → failure test
```

- Treat URL params, API/CMS/AI output, uploads, local storage, cross-window messages, and third-party scripts as untrusted until a named boundary validates them.
- Preserve server authorization, validation, rate limits, CSRF policy, and audit behavior. A hidden/disabled button is only presentation.
- Never expose secrets, private endpoints, service credentials, source maps with sensitive content, or privileged decisions in client bundles.
- Use project threat models and security policy when present. Do not weaken CSP, cookie flags, iframe restrictions, or sanitization to make a visual feature easier.

## 2. Keep untrusted data out of executable sinks

- Prefer text/content APIs and framework escaping. Avoid `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `srcdoc`, `dangerouslySetInnerHTML`, `v-html`, template compilation, dynamic script construction, and string-to-code APIs.
- If rich markup is a real product requirement, define a minimal allowlist, sanitize with a maintained library in the correct environment, and test mutation/bypass fixtures. Do not modify sanitized markup with unsafe code afterward.
- Validate URL schemes and destinations before assigning `href`, `src`, CSS `url()`, redirects, downloads, or deep links. Reject `javascript:`, unexpected `data:`, credentialed URLs, control characters, and unsafe protocol-relative/external targets.
- SVG has its own active-content/parser/resource limits; follow [svg-system.md](svg-system.md). Markdown, MathML, rich text, syntax highlighting, and email previews need their own sink review.
- Consider Trusted Types where the supported environment and application architecture can enforce it; do not claim protection from a policy that silently passes arbitrary strings.

## 3. Constrain browser capabilities

- Build a CSP from the real resource inventory. Prefer nonces/hashes and narrow origins; avoid adding `unsafe-inline`, `unsafe-eval`, `*`, broad `data:`, or unbounded `connect-src` as a convenience fix.
- Self-host or pin third-party code where appropriate. For immutable cross-origin scripts/styles, review Subresource Integrity and CORS behavior. A CDN URL is not a license or integrity guarantee.
- External new-tab navigation needs a safe opener policy and an honest destination. Downloads need verified content type, filename, authorization, and origin.
- For `postMessage`, verify exact origin, expected `source`, message schema/type/size, and state before action. Never accept `*` for sensitive data or treat message content as HTML/code.
- Iframes use the smallest `sandbox`, `allow`, referrer, and origin permissions that work; provide a fallback and test focus, fullscreen, payments, clipboard, and navigation deliberately.
- Service workers, caches, offline storage, and client databases require versioning, logout/data-deletion behavior, stale-sensitive-data policy, and update recovery.

## 4. Handle identity and transactions at the right boundary

- Follow the current authentication architecture. Do not move durable bearer/session secrets into `localStorage` just to simplify UI code.
- Prefer server-managed secure cookie/session patterns when the architecture supports them; configure `Secure`, `HttpOnly`, and `SameSite` according to the real cross-site flow, then implement CSRF protection where applicable.
- Prevent duplicate submission visually and server-side. Idempotency, price, inventory, entitlement, and permission checks remain server responsibilities.
- Errors must help recovery without exposing tokens, stack traces, internal IDs, query details, or whether a protected account/resource exists beyond product policy.
- Logout, account switch, token expiry, permission loss, multi-tab state, Back/Forward cache, and optimistic rollback need explicit UI states and tests.

## 5. Inventory third parties and privacy impact

Before adding analytics, fonts, chat, maps, video, pixels, embeds, or asset APIs, record:

```text
vendor/domain → data sent → purpose → consent/legal policy → retention → CSP/cookie/storage → failure/fallback → owner/removal
```

- Do not add telemetry, fingerprinting, remote fonts/assets, or marketing SDKs merely for a design preview.
- Honor the project's consent and privacy policy before loading optional third parties; “anonymous” is not an evidence-free claim.
- Failure, blocking, slow network, and consent rejection must not break the primary task.
- Keep third-party script count and privileges minimal; review package, service, content, and asset licenses separately.

## 6. Verify the boundary, not keywords

Static discovery may look for dangerous sinks, external origins, inline script/style, insecure URLs, secret-like bundle strings, and missing lockfiles. It cannot prove safety.

Required dynamic/owned evidence as applicable:

- malicious payload fixtures reach the real renderer/upload/message path and remain inert;
- CSP is delivered as an actual response header and violation reports are reviewed; a meta tag or source string is not equivalent for every directive;
- cookies, storage, cache, service worker, logout, expiry, permission loss, and cross-tab behavior are inspected in browser tools;
- external requests match the declared domain/data inventory; blocked/failed third parties preserve the task;
- authorization and transaction invariants are tested at the server/API boundary;
- dependency/lockfile and build provenance are recorded; security advisories are triaged for the installed version and reachable use;
- results state scope, environment, tool version, fixtures, false-positive review, and remaining untested attack classes.

Release blockers:

- client-only authorization or price/permission trust;
- untrusted content reaching an executable HTML/URL/script/style/message sink without a verified boundary;
- secrets or session material exposed to bundles, URLs, logs, screenshots, artifacts, or model prompts;
- broad CSP/iframe/postMessage/third-party permission added only to make an effect work;
- security claim based only on grep, a package name, sanitizer presence, or a self-issued score.
