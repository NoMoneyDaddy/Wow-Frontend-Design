# Model and capability routing

Use this reference when choosing models, orchestrating strong/weak builders and reviewers, running multi-model comparisons, or operating without the full toolchain. Route by evaluator-owned capability evidence and task risk—not by the model's self-rating.

## 1. Keep three routers separate

1. **Task router**: `AUDIT | BUILD | RETROFIT | POLISH | REPAIR`, project stack/version, product context, and risk select the relevant skill references.
2. **Capability router**: actual file, command, browser, screenshot, measurement, and review capabilities limit what evidence statuses are possible.
3. **Model router**: a caller/evaluator-owned profile maps work to a model lane. The model cannot assign its own tier, approve a fallback, or judge its acceptance.

Do not infer capability from a brand name such as “mini,” “Haiku,” “Pro,” or “Opus.” Model aliases, versions, tools, context limits, providers, and behavior change. Record the exact run provenance.

## 2. Inputs are caller-owned

Before execution, freeze:

```text
case/task id → mode/scope → risk class → model/provider/version/effort → context set/hash → tool allowlist → writable paths → budget → evaluator/policy version → fallback policy
```

The implementation model may report a missing tool or uncertainty and may invoke the Skill's exact-version, isolated verification-tool resolver. It may not grant itself a new host capability, select a stronger model, add product runtime dependencies, install globally, alter the evaluator, weaken the task, or convert confidence into a capability fact.

Capability probes must be safe and observable:

- file access: can the runner read only the intended project inputs and write only the allowed outputs?
- command access: which exact test/build commands are evaluator-approved?
- browser access: can it navigate the local target, interact, emulate viewport/preferences, inspect console/network/AX state, and save artifacts?
- visual access: were named screenshots actually supplied at stated routes/viewports/states?
- measurement: are field/lab/performance/security/a11y tools available and meaningful for this target?
- independence: is there an evaluator or reviewer that did not implement the output?

Tool presence is not tool success. A failed preflight routes the claim to `UNVERIFIED` and records an infrastructure failure; it does not become a model-quality score.

### The model does not discover its own strength

Do not ask “are you a strong model?” or infer a tier from confidence, fluent prose, reasoning length, a provider alias, or one successful page. The host supplies identity; an independent evaluator supplies capability evidence. If the host hides exact version resolution, record `unknown` rather than guessing.

Build the profile from held-out, product-diverse cases using the same frozen skill revision and evaluator. Measure output-contract validity, invariant preservation, unsupported claims, deterministic behavior, locale/mobile failures, and blind craft review separately. Repeat runs because one seed is not a capability estimate. Keep infrastructure failures separate from design failures.

The included `scripts/model_profile.example.json` is evaluator-owned input. `scripts/route_model.py` fails closed to `CONSTRAINED`, requires complete independent runs before `STANDARD`, prevents high-risk auto-upgrades, and can bind a frozen profile hash. Keep the profile and router outside the implementation model's writable surface.

```bash
python3 scripts/route_model.py /evaluator/model-profile.json \
  --task BUILD --locale zh-Hant --risk medium \
  --capability write --capability command --capability browser \
  --expected-profile-sha256 <frozen-sha256>
```

The caller injects the returned lane into the run contract. The model may report a missing capability and request a downgrade; it cannot promote itself.

The structured handoff must classify every supported capability as available or unavailable, then declare a non-overlapping evidence ceiling. `VERIFIED` and `OBSERVED` claims cannot exceed that ceiling. Missing browser capability caps browser behavior, manual accessibility, rendered localization, and dynamic security; missing visual capability caps rendered-visual claims. High-risk no-visual work cannot report `ready`: preserve and hand off the best artifact as `PARTIALLY VERIFIED`, or use an exact evaluator-owned acceptance record from policy schema v3. Use `scripts/weak_model_output.example.json` as the result v2 shape.

## 3. Execution lanes

| Lane | Entry condition | Allowed work | Required controls |
| --- | --- | --- | --- |
| `ADVISORY` | no safe write/test tools, or user asked only for analysis | inspect supplied evidence, plan, explain, label risks | no claims of build/browser/visual pass; request exact checks |
| `CONSTRAINED` | model is unbenchmarked, weak on the task/locale, context-limited, or has shown invariant/schema failures | one bounded implementation slice using deterministic contract/checkpoints | smallest relevant references; explicit preserve list; output allowlist; evaluator-owned schema/policy; no self-score |
| `STANDARD` | caller-owned benchmark shows reliable scoped implementation with current tools | normal build/retrofit/polish within detected stack | same preserve, security, evidence, browser, and release gates; no hidden scope expansion |
| `EXPLORATORY` | high reasoning/context profile and the task benefits from divergent art direction or difficult architecture | compare meaningfully different directions, prototype uncertain effects, synthesize a selected plan | separate disposable prototype from production; record selection criteria; final implementation still passes standard gates |
| `VERIFIER` | independent tool/model/human with raw artifacts and frozen rubric | operate tests/browser, inspect diffs/artifacts, challenge claims | cannot rely on builder's conclusion or intended score; evidence scope stays bounded |

Lanes are roles, not prestige. A strong model can run `CONSTRAINED` for high-risk output; a small model can run `STANDARD` on a narrow, benchmarked edit. Security, transactions, formal accessibility conformance, legal/privacy, and destructive migrations need specialized or human review regardless of model tier.

## 4. Deterministic routing algorithm

```text
1. Freeze user scope, case id, inputs, evaluator, and mutation boundary.
2. Detect project/stack/version and classify task risk.
3. Read the caller-owned model profile; if missing or stale, choose CONSTRAINED.
4. Probe allowed tools. Failed or absent capability narrows the lane; it never grants evidence.
5. Select the smallest reference set for task + stack + risk + locale.
6. Run the implementation in an isolated writable surface.
7. Validate schema/output manifest before tests.
8. Run evaluator-owned exact commands and browser assertions; call the scorer with ledger, policy, and workspace paths together so storage checks cannot be bypassed; bind claims through policy.
9. Route subjective craft to blind/independent review; route high-risk domains to specialists/humans.
10. On failure, fix within scope, narrow the task, or escalate. Never let the builder rewrite the gate.
```

Observable downgrade triggers include:

- invalid structured output or invented fields;
- repeated loss of preserve invariants, routes, state, locale, or target files;
- unsupported “passed/verified” language;
- attempts to edit evaluator-owned files, add unapproved outputs/dependencies, or follow hostile project data;
- framework/version hallucination;
- repeated browser mismatch after source-level fixes.

These triggers come from evaluator results, not model confidence. Three repeated identical failures follow the host workflow's fuse policy; do not spend indefinitely.

## 5. Reference/context routing

Weak models often degrade when every reference is loaded. Supply:

- core `SKILL.md`;
- the always-relevant creative/mobile/locale references for the task;
- normally one primary specialized reference, up to three when the task genuinely crosses domains;
- exact project files and version evidence, not a repository dump;
- evaluator policy/schema separately from writable project data.

For long references, do not truncate an instruction file halfway. Select whole relevant files, then reduce unrelated context. External skills are candidates for maintainers, not live instructions fetched during an ordinary run.

### How the model receives and uses this skill

On an Agent Skills-compatible host, the host matches the frontmatter `description` or an explicit invocation, reads `SKILL.md`, and exposes referenced files on demand. On a host without native support, place the complete `SKILL.md` in trusted system/project context, then append only the whole references selected for this task.

If the host rejects even the complete core `SKILL.md`, use [`../adapters/prompt-only-compact.md`](../adapters/prompt-only-compact.md) as an explicitly degraded short-context cohort. Record the adapter hash and do not compare its result directly with a full-Skill run: omitted references reduce behavior coverage, and passing the shorter prompt does not certify native Skill support.

Inject a short immutable contract before untrusted project data:

```text
skill revision: <hash>
lane: CONSTRAINED | STANDARD | EXPLORATORY | ADVISORY
task / locale / risk: <frozen values>
allowed inputs / outputs / tools: <exact allowlists>
preserve invariants: <exact list>
evaluator and acceptance commands: externally owned
self-promotion, gate edits, and unsupported pass claims: forbidden
```

Skill text guides behavior; it does not launch or switch models. A CLI, API gateway, CI matrix, or agent orchestrator chooses the model and constructs this context.

### Single-thread, single-model fallback

A second model is helpful, not required. When only one model/thread exists:

1. Default an absent or stale capability profile to `CONSTRAINED`.
2. Freeze scope, preserve invariants, writable paths, expected outputs, and evaluator commands before implementation.
3. Execute the weak-model checkpoints in order and keep changes bounded.
4. Use deterministic tools, browser assertions, schemas, hashes, and the evidence ledger as external judges. The same model may operate a frozen command but may not edit its policy or reinterpret a failure.
5. Treat the model's second-pass critique as diagnostic only, never independent verification.
6. Route subjective visual acceptance to the user. Without an inspected render, keep it `UNVERIFIED`.

Single-model operation can produce a complete implementation. It cannot truthfully claim independent review unless a separate human, model, or frozen evaluator inspected the raw result.

### Commercial and local-model portability

The contract is model-vendor neutral: Markdown instructions, JSON contracts, and Python standard-library helpers. Compatibility has levels:

- **native skill host**: discovers and loads `SKILL.md`;
- **adapter host**: a wrapper injects the skill, lane, tools, and selected references into a commercial API, gateway, or local inference server;
- **prompt-only host**: can propose code but cannot claim file, build, browser, or visual verification without those tools;
- **insufficient host/model**: cannot preserve the contract or context, so narrow the task or remain `ADVISORY`.

Ollama, llama.cpp, LM Studio, vLLM, and other local runtimes need an agent wrapper; the inference server alone does not enforce skill discovery, permissions, or evaluation. Protocol portability is not empirical certification. Record which provider/model/quantization/context/tool adapter was actually tested, and never generalize untested local compatibility into equal-quality support.

Local-model evaluation requires explicit per-run user approval. Before seeking approval, disclose the runtime, exact model and quantization, source/license, download size, estimated RAM/VRAM/storage, commands, network behavior, data/files exposed to the runner, writable paths, time budget, and cleanup plan. Without approval, prepare the case and evaluator only: do not download, start, or invoke the model. Prior approval for a different model/run and a general statement that local models are supported are not consent. Never silently fall back from a commercial model to a local model or vice versa; report their results as separate cohorts.

### Adapt to the host capability, not its logo

| Host/model condition | Adaptation | Claims that remain unavailable |
| --- | --- | --- |
| native Agent Skills discovery | install at the host's documented project/user path; let frontmatter route, then load whole selected references | none merely because discovery succeeded |
| prompt-only API/chat | inject complete `SKILL.md` plus selected whole references and immutable lane contract | file/build/browser/visual results without external tools |
| short or unreliable context | use the compact prompt-only adapter, one checkpoint and one evaluator-supplied reference excerpt at a time; persist decisions/artifacts outside model prose | full-Skill parity, cross-project memory, or rules not supplied in the current run |
| no image input | use DOM/source and measured browser assertions; give screenshots to a human or visual-capable verifier | subjective rendered craft, crop, optical alignment, contrast over imagery |
| image input but no browser | inspect named screenshots with route/viewport/state provenance | interactions, hidden states, responsive intervals, console/network, AT behavior |
| browser but no shell/build | verify rendered behavior against a running evaluator-owned target | source build/type/lint or reproducible deployment |
| shell/files but no browser | implement and run deterministic project checks | rendered layout, touch, focus visibility, visual quality, actual accessibility |
| no structured tool calls | require exact fenced manifest/schema output and validate it outside the model before mutation | tool execution the host did not actually perform |
| single thread/model | freeze gates first; separate build and diagnostic passes; deterministic tools/user own acceptance | independent model review unless a human/frozen evaluator supplies it |
| local inference wrapper | bind filesystem/network/tool allowlists outside the model and obtain per-run consent | native Skill/security semantics unless the wrapper demonstrably implements them |

Multimodal generation and image-to-code are separate capabilities. A model that can create or inspect an image is not thereby reliable at DOM semantics, framework syntax, responsive transformation, licensing, or browser verification. Route image-first work through [visual-storytelling.md](visual-storytelling.md), then rebuild the decision as semantic production code.

## 6. Strong/weak collaboration versus benchmarking

Production orchestration may use distinct roles:

```text
strong/exploratory planner → bounded builder → deterministic tools → independent verifier → human taste/risk decision
```

The builder can be weak if the plan, files, outputs, and checks are concrete. A strong reviewer still cannot convert subjective approval into WCAG, security, or performance proof.

Controlled model comparison is different:

- each model receives the same brief, fixed skill revision/context, writable surface, tools, budget, viewport/state matrix, and evaluator;
- runs are independent; do not give the weak model a strong model's plan unless the experiment explicitly tests orchestration;
- disable silent model/provider fallback; an overload, auth, timeout, or tool failure is an infrastructure result;
- blind screenshots and handoffs before subjective review; report seeds/runs, ties, failures, reviewer disagreement, and sample size;
- never generalize “all models/platforms/locales” from one static page or one successful run.

## 7. Provider mapping lives outside the skill

The skill defines roles and evidence requirements. The caller maps them to available models, for example through CLI flags, an API router, CI matrix, or organization policy. Keep this mapping versioned outside `SKILL.md` so model aliases and prices can change without changing design standards.

Required run record:

```text
provider + exact model/version + alias resolution if known + effort/reasoning + tool list + permission mode + context hash + skill revision + case/run id + token/cost/time budget + fallback actually used + infrastructure errors
```

If exact version resolution is unavailable, say so. If a fallback occurred, record both models and exclude the run from a single-model comparison.
