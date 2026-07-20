# Model and capability routing

Use this reference when choosing models, orchestrating strong/weak builders and reviewers, running multi-model comparisons, or operating without the full toolchain. Route by evaluator-owned capability evidence and task risk—not by the model's self-rating.

## 1. Keep three routers separate

1. **Task router**: `AUDIT | BUILD | RETROFIT | POLISH | REPAIR`, project stack/version, product context, and risk select the relevant skill references.
2. **Capability router**: actual file, command, browser, screenshot, measurement, and review capabilities limit what evidence statuses are possible.
3. **Model router**: a caller/evaluator-owned profile maps work to a model lane. The model cannot assign its own tier, approve a fallback, or judge its acceptance.

Do not infer capability from a brand name such as “mini,” “Haiku,” “Pro,” or “Opus.” Model aliases, versions, tools, context limits, providers, and behavior change. Record the exact run provenance.

Model routing is an evaluator optimization, not an Agent Skills compatibility layer. The installed Skill package stays model-neutral; only executable script/runtime requirements belong in the support matrix.

### 結論：routing 不是假議題，model-name branching 才是

模型路由確實能在特定分布上改善品質／成本，但「強／弱」不是穩定的一維排序。模型可能會寫 code，卻無法可靠選 Skill、操作工具、看圖、保留 locale 或完成長流程；同一模型也會因 adapter、context、effort、工具、權限與 evaluator 不同而改變表現。因此：

- 不在 `SKILL.md` 內問模型「你是誰／你有多強」再分支；Agent Skills 規格本身也沒有標準 `model` frontmatter 欄位。
- Claude Code 的 `model` 位於 subagent／host 設定，正好說明選模屬於編排層，不是 Skill 的自我認知。
- 一個 generic probe 只證明那個 probe。不要用一次 tool call、小謎題或合法 JSON 就把所有設計／工具／locale 能力升級。
- 用離線、held-out、任務相近的重複實測建立起始 profile；用真正任務中的 schema、工具、browser、invariant 與 evidence 結果做執行期降級。
- 維持一份 canonical Skill 加漸進式 references。只有 host context 確實容不下完整 core 時才用 compact adapter，並視為不同 cohort；不要人工維護會漂移的 `skill-lite`／`skill-full` 兩份真相。

## 2. Inputs are caller-owned

Before execution, freeze:

```text
case/task id → mode/scope → risk class → model/provider/version/effort → context set/hash → tool allowlist → writable paths → budget → evaluator/policy version → fallback policy
```

For a cross-host run, also emit `scripts/capture_runtime_profile.py` into evaluator-owned storage. It records OS/release/architecture, Python, encodings and timezone plus bounded caller declarations for environment kind, shell, Node, browser and font profile. It does not execute those tools or inspect host identity, environment variables or network; therefore declarations still need setup-log, lockfile or browser-report evidence. Do not infer remote/container/CI state from a vendor logo or ambient environment variable.

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

Build the profile from held-out, product-diverse cases using the same frozen Skill, adapter, toolchain and evaluator revisions. Key each cell by `task × locale × surface × risk`; measure output-contract validity, invariant preservation, unsupported claims, deterministic behavior, locale/mobile failures, and blind craft review separately. Repeat runs because one seed is not a capability estimate. Record `attempts = eligible_runs + infrastructure_failures`; infrastructure failures never count as successful or failed model runs.

The included schema-v2 `scripts/model_profile.example.json` is evaluator-owned input. `scripts/route_model.py` fails closed to `CONSTRAINED`, requires at least three complete eligible independent runs before `STANDARD`, rejects evidence from another surface, separates infrastructure failures, prevents high-risk auto-upgrades, and can bind a frozen profile hash. Keep the profile and router outside the implementation model's writable surface.

```bash
python3 scripts/route_model.py /evaluator/model-profile.json \
  --task BUILD --locale zh-Hant --surface product-ui --risk medium \
  --capability write --capability command --capability browser \
  --runtime-provider <provider> --runtime-model <exact-model-or-recorded-alias> \
  --runtime-model-version <version-or-unknown> \
  --runtime-skill-revision <hash> --runtime-adapter-revision <hash> \
  --runtime-toolchain-revision <hash> --runtime-evaluator-revision <hash> \
  --expected-profile-sha256 <frozen-sha256>
```

The router compares every runtime binding to the profiled identity and revisions; any drift caps the run at `CONSTRAINED`. The caller injects the returned lane into the run contract. The model may report a missing capability and request a downgrade; it cannot promote itself.

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

## 4. Runtime automatic downgrade

The start lane comes from the caller-owned profile. After execution begins, evaluator-observed events may keep or lower it; no event, self-report, confidence, successful retry, or fluent explanation can raise it inside the same run. Give every event a stable evaluator-owned `failure_key`; different layout, route, state, tool or root cause must not share the same three-attempt fuse.

Use evaluator-owned [`../scripts/runtime_events.example.json`](../scripts/runtime_events.example.json) with [`../scripts/runtime_downgrade.py`](../scripts/runtime_downgrade.py):

```bash
python3 scripts/runtime_downgrade.py /evaluator/runtime-events.json
```

Schema v2 records the evaluator-owned, monotonic `mutation_attempts_used` on every event and a run budget no greater than the core's three attempts. Once exhausted, every action that could authorize another mutation becomes `HAND_OFF_BEST`; changing a failure key cannot reset it. Timeout or tool retry advice is not mutation authority.

| Observed event | Automatic response |
| --- | --- |
| logs or evaluator artifacts still advance at inactivity timeout | extend the bounded timeout; do not downgrade |
| transient tool failure or repair finding, attempts 1–2 | retry or repair, run the narrow check, keep the current lane |
| declared same-key fuse is reached | cap at `CONSTRAINED`, stop blind retries, and hand off the best artifact as partially verified; the fuse can stop earlier but never extends the core's three-total-mutation-attempt budget |
| output schema, preserve invariant, or evidence wording fails | cap at `CONSTRAINED`; narrow, restore, or remove the unsupported claim, then continue |
| browser/visual/other verification capability is unavailable | cap at `CONSTRAINED`; continue safe implementation and mark only the affected gate `UNVERIFIED` |
| safe mutation capability is missing, or security/permission policy blocks mutation | move to `ADVISORY`; stop mutation and preserve diagnostics |
| implementation crosses evaluator-owned files or policy | cap at `CONSTRAINED`; discard that attempt and restart in a fresh isolated surface |

An ordinary visual or test finding is not evidence that the whole model is weak; it stays in the self-repair loop. Downgrade on the measured failure class, not on the model's apology or confidence. Automatic downgrade changes scope, checkpoints and evidence ceiling—not the user's product requirements, safety policy, or evaluator gate.

Do not auto-upgrade after recovery. A higher lane needs a new externally authorized run against a fresh, versioned profile built from independent eligible evidence.

## 5. Deterministic routing algorithm

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

## 6. Reference/context routing

This router inherits the canonical reference lifecycle from `SKILL.md`; it narrows a lane but never defines another bundle or raises the reference cap. Weak models often degrade when every reference is loaded. Supply:

- core `SKILL.md`;
- the core-defined initial bundle, then only the whole references owned by the current decision stage;
- one dominant task reference and at most one proven cross-domain dependency in the same turn;
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

## 7. Strong/weak collaboration versus benchmarking

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

## 8. Provider mapping lives outside the skill

The skill defines roles and evidence requirements. The caller maps them to available models, for example through CLI flags, an API router, CI matrix, or organization policy. Keep this mapping versioned outside `SKILL.md` so model aliases and prices can change without changing design standards.

Required run record:

```text
provider + exact model/version + alias resolution if known + effort/reasoning + tool list + permission mode + context hash + skill revision + case/run id + token/cost/time budget + fallback actually used + infrastructure errors
```

If exact version resolution is unavailable, say so. If a fallback occurred, record both models and exclude the run from a single-model comparison.

## 9. Research basis and limits

- [Agent Skills specification](https://agentskills.io/specification) defines Skill metadata, instructions and progressive resources, but no portable model selector. [Claude Code subagents](https://code.claude.com/docs/en/sub-agents) place model selection in host-owned agent configuration.
- [Agent Skills evaluation guidance](https://agentskills.io/skill-creation/evaluating-skills) recommends realistic cases, old/no-Skill baselines, repeated runs, timing/token evidence and investigation of variance; one successful demo is not a profile.
- [Agent Skill Framework for small and medium models](https://arxiv.org/abs/2602.16653v3) reports that very small models struggled with Skill selection while some 30B–80B configurations benefited. It covers a limited task/model sample and does not create a universal parameter-count threshold.
- [RouteLLM](https://arxiv.org/abs/2406.18665) demonstrates learned quality/cost routing, but its Arena-only router fell near random on out-of-distribution MMLU and GSM8K; training-distribution similarity mattered.
- [LLMRouterBench](https://aclanthology.org/2026.findings-acl.1881/) confirms model complementarity while finding several complex/commercial routers did not reliably beat a simple baseline under unified evaluation, with persistent recall gaps and diminishing returns from larger pools.
- [FrugalGPT](https://arxiv.org/abs/2305.05176) shows cascades can reduce cost and that cheaper models sometimes answer queries a nominally stronger model misses; models are not a strict total order.
- [Large Language Models Cannot Self-Correct Reasoning Yet](https://openreview.net/forum?id=IkmD3fKBPQ) found intrinsic self-correction can fail or degrade reasoning without external feedback. This supports external gates, but its reasoning-task result is not proof that all self-repair is useless.
- [Amazon Bedrock intelligent prompt routing](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-routing.html) is production evidence that external routing is feasible, while its documented English-only optimization and lack of application-specific performance inputs show why a generic vendor router cannot certify this Skill's `zh-Hant` product work.

Treat paper and vendor results as routing hypotheses. Only this Skill's frozen cases, exact model/adapter/toolchain, target locale/surface and independent evaluator can promote a local profile.
