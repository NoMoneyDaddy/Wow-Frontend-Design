# 現行評測與受控建置

本目錄只支援一份規範性標準：`wow-frontend-design/SKILL.md`。`build:current` 是唯一受控建置入口；它不維護平行 Skill 版本，也不把舊產物或舊截圖當成新證據。

`evals/` 是 repository evaluator，不屬於安裝後自動執行的 Skill runtime。一般 Skill package 仍可只靠 `SKILL.md`、按需 references、scripts 與 assets 使用。

## 快速多方向草稿

`drafts:current` 是 `build:current` 的 style-calibration wrapper，不是第二套 builder。它在同一次受控 BUILD 內產生 2–3 個方向頁面，固定使用 `references/design-exploration.md`，再呼叫現行 final-only capture 取得同一 manifest 下的 fresh desktop/mobile PNG。這個流程只支援 greenfield 草稿；不做 production integration、release acceptance、勝者判定或 award claim。

草稿 wrapper 會在同一次 Playwright capture matrix 內同步取得 rendered macro fingerprints，並重用現行 `cross_output_template_audit.cjs` 產生跨稿結構與低解析視覺語法 telemetry。它不多開一次 browser；advisory 只把 `review_required` 設為 true，不能自動淘汰方向、觸發 release failure，或證明原創、美感與產品適配。原本 final capture 未提供 draft convergence contract 時，不產生這兩個 sidecar，receipt schema 維持不變。

計畫檔必須是 evaluator-owned、schema-closed JSON：

```json
{
  "schema_version": 1,
  "cohort_id": "marketplace-directions-1",
  "partition": "validation",
  "locale": "zh-Hant",
  "surface": "marketplace-home",
  "decision_question": "哪一種資訊層級最能支援可信任的探索？",
  "held_constant_axes": ["product-facts", "content-fixture", "functional-behavior", "comparison-conditions"],
  "selection_criteria": ["主要任務清晰", "品牌辨識度", "手機轉化成立"],
  "variants": [
    {
      "id": "editorial-index",
      "hypothesis": "以策展索引建立可信任的探索節奏。",
      "changed_axes": ["composition", "typography", "density"],
      "expected_benefit": "大量內容仍保有來源與層級。",
      "risk": "可能壓低立即行動的能見度。",
      "disqualifier": "主要行動在手機首屏不可見。"
    },
    {
      "id": "task-led-market",
      "hypothesis": "以任務與快速比較縮短選擇路徑。",
      "changed_axes": ["information-hierarchy", "interaction-emphasis", "mobile-transformation"],
      "expected_benefit": "更快抵達可比較的結果。",
      "risk": "可能降低品牌敘事的記憶點。",
      "disqualifier": "方向退化成通用卡片牆。"
    }
  ]
}
```

先建立兩個新的空目錄，且保持在 authoring repository 外：

```bash
npm run drafts:current -- \
  --plan /absolute/evaluator-root/cohort-plan.json \
  --brief /absolute/evaluator-root/brief.md \
  --cohort-root /absolute/evaluator-root/cohort-output \
  --log-dir /absolute/evaluator-root/private-logs
```

成功時最後才以 `0600` 建立 `draft-cohort-receipt.json`。Receipt 綁定 plan、base/effective brief、Skill tree、run manifest、outputs、capture receipt、capture matrix、macro observations、template audit 與 evaluator tools，但不保存 brief 內容或絕對私人路徑。Convergence summary 固定列出四類 advisory 數量、受影響方向與 `advisory_only` policy；任一 build、fresh capture、provenance 或 telemetry drift 失敗都不產生成功 receipt。草稿 PNG 只能支持這次方向選擇；選定後仍須重新正式實作、重新截圖並執行 affected release matrix。

### 兩分鐘決策 checkpoint

先以可讀尺寸展示同批 fresh captures。使用者只需回覆一行，例如：`選 editorial-index｜原因：資訊層級最清楚｜調整：主操作再突出`。執行代理把這句話轉成 evaluator-owned、schema-closed JSON；不要要求使用者重填 route、viewport、state 或 evidence label，也不要把 `review_required` 當成自動淘汰。

```json
{
  "schema_version": 1,
  "cohort_id": "marketplace-directions-1",
  "action": "select",
  "variant_id": "editorial-index",
  "authority": "user_confirmed",
  "reason": "資訊層級最清楚。",
  "adjustments": ["主操作再突出。"],
  "convergence_reviewed": true
}
```

`action` 只允許 `select`、`revise`、`stop`。`select` 可帶 0–3 個不改變 thesis、可在正式實作後以 fresh evidence 驗證的微調。需要再次看草稿、跨稿借用或改變 thesis 時才用 `revise`；它必須指定一個 base variant 與 1–3 個具體調整，先形成一個 fresh child，不能直接把未渲染拼貼宣稱為 selected。`stop` 的 `variant_id` 必須是 `null`。若 convergence 有 advisory，繼續選稿或修稿前必須看過 paired captures 並明示 `convergence_reviewed: true`；這仍不是缺陷、排名或 release gate。

將 decision JSON 設為 `0600`，另建一個新的空 output directory，然後記錄不可覆寫的決策。`authority` 只允許 `user_confirmed`、`human_reviewer_confirmed` 或使用者明示委派的 `user_delegated`；這是決策來源聲明，不證明真實身份或獨立性：

```bash
npm run drafts:decide -- \
  --cohort-root /absolute/evaluator-root/cohort-output \
  --log-dir /absolute/evaluator-root/private-logs \
  --decision /absolute/evaluator-root/draft-decision.json \
  --output-root /absolute/evaluator-root/decision-output
```

成功時以 `0600` 建立 `draft-decision-receipt.json`，自動綁定原 cohort receipt、capture set、選定方向的 desktop/mobile labels、held constants、selection criteria 與 convergence summary。它只建立 selection lineage：只有 `select` 交給唯一的 production `BUILD` lane；`revise` 只要求一個 bounded fresh child 並回到同一 checkpoint，`stop` 不進 production。草稿 HTML 與 PNG 都不得升級成 release evidence。

## 受控建置

```bash
npm run build:current -- \
  --brief /absolute/path/brief.md \
  --target /absolute/path/output \
  --log-dir /absolute/path/logs \
  --output DESIGN.md \
  --output index.html
```

預設 forward-test builder 是 `gpt-5.4-mini`，reasoning effort 是 `high`。可用 `--model` 與 `--reasoning-effort low|medium|high|xhigh` 明示覆寫；receipt 只記錄請求值，不把它當成服務端已履行或品質已通過的證明。

每次 initial build 固定載入 `references/creative-direction.md` 與 `references/no-visual-first-pass.md` 的完整內容作為 controlled Skill context；可額外提供一次 `--skill-reference references/<safe-name>.md`，但不能重複，也不能由 brief 或 seed 內容決定。選取只接受現行 Skill source 內已驗證的 regular non-symlink、strict UTF-8 Markdown；absolute path、`..`、未知路徑、NUL、單檔超過 64 KiB 或合計超過 128 KiB 都 fail closed。這是核心 reference lifecycle 的 controlled external-evaluator 分支：builder context 原樣帶進每輪 repair，外部 evaluator 執行 quality gates 並只回傳 bounded findings，不把 gate reference 或 acceptance instructions 加入可寫模型 context。

Receipt、每次 attempt 與 manifest 的 `skill_references` 只保存相對 path、bytes、SHA-256 與 `total_bytes`，不保存 reference 內容。`ExecutionSpec` 會把這組 provenance 與 source tree、ephemeral installed Skill snapshot 在執行前後逐項重驗；任何 selected content、path 或 hash drift 都拒絕結果，完整 Skill tree 的 mode 也在每次 execution 內前後重驗。Shell tool 仍存在，但契約只容許 inert no-op，任何其他 command 都會在 trace policy 拒絕且不得發布；network、外部讀取與其他整合維持停用。Raw evaluator trace 可能含模型自行複述的 Skill 文字，因此保持 private，Skill references 不應存放機密。

Greenfield 沿用上方命令。Retrofit 或 patch 使用 evaluator-owned、位於 repository／log／target 之外的小型 frozen seed，並明列唯一可變路徑；seed 其餘檔案必須逐 byte 與 mode 保持不變：

```bash
npm run build:current -- \
  --brief /absolute/evaluator-root/brief.md \
  --target /absolute/evaluator-root/output \
  --log-dir /absolute/evaluator-root/logs \
  --case-mode retrofit \
  --seed-root /absolute/evaluator-root/frozen-project \
  --allow-change styles.css
```

需要驗證特定產品關鍵路徑時，可再傳 evaluator-owned 的 declarative Playwright contract：

```bash
npm run build:current -- \
  --brief /absolute/evaluator-root/brief.md \
  --target /absolute/evaluator-root/output \
  --log-dir /absolute/evaluator-root/logs \
  --output DESIGN.md \
  --output index.html \
  --browser-contract /absolute/evaluator-root/browser-contract.json
```

最小 contract：

```json
{
  "schema_version": 1,
  "cases": [{
    "id": "mobile-primary-task",
    "page": "index.html",
    "profile": "mobile",
    "steps": [
      {"id": "action-in-first-viewport", "action": "assert", "selector": "[data-primary-action]", "expect": "fully-visible-in-viewport"},
      {"id": "activate", "action": "click", "selector": "[data-primary-action]"},
      {"id": "state-changed", "action": "assert", "selector": "[data-task-state]", "expect": "text-includes", "value": "Ready"}
    ]
  }]
}
```

Contract 只允許 bounded `click`、`fill`、`press`、`select` 與 `assert` steps；可檢查 visible、attribute、text、count 及完全位於指定 viewport 內。`fully-visible-in-viewport` 必須排在所有互動前，語意才是未捲動的首屏；一般 assertion 會在兩秒內 bounded polling，`animations-inactive-for` 則對整段明示的觀察窗做一次連續判定；scenario 結束後另留 300ms 捕捉延遲 runtime error。它與 Axe、overflow、runtime error 使用同一個 Playwright gate；initial build 加最多兩輪 adaptive repair，共三次 mutation attempts，不另建第二套 runner。同一完整 failure state 重現、形成 cycle，或 HTML 修復使 design gate 回歸都會立即停止；不同 finding 也不能重設全域預算。Manifest 的 contract provenance 欄位只保存 schema、bytes、hash 與 case／step 數；HTML gate／repair history 只保存 bounded case／step ID。失敗步驟的 evaluator-authored locator、accessible name，以及白名單化且 bounded 的 assertion／action 參數可進入 repair prompt，但不會進 receipt、manifest 或發布產物；raw runtime diagnostics、candidate DOM 與外部絕對路徑不會進 repair prompt。Contract 是 evaluator 定義的 deterministic acceptance，不取代 fresh screenshot、獨立 craft review 或完整 E2E。

先凍結 brief 支持的可觀察語意，再選不依賴候選 DOM 排列的最小 locator／assertion：

- `click` 應指向使用者實際可操作、能接收 pointer event 的表面。若 radio／checkbox 以透明 input 加可見 label 客製，點 evaluator 明列的 label／control surface，不要把 `pointer-events: none` 的 input 當點擊目標；Playwright 仍會執行 [actionability checks](https://playwright.dev/docs/actionability)。
- v1 `text-includes` 保留 raw descendant `textContent` substring 語意，會受 source whitespace 影響，也不排除 hidden descendants；只用於已凍結、沒有隱藏替代文字的精確 leaf state。v2 的公開可見狀態改用 `rendered-text-includes`：它要求唯一 HTMLElement locator 在 composed tree 可見，並以瀏覽器 `innerText` 排除未渲染後代。兩者都一次驗證一個 brief 已固定的事實；不要把分置 sibling spans 的時間、名稱或狀態拼成候選 DOM 才可能連續出現的字串。
- `no-content-overflow` 只在該 element 的 client box 本身就是 brief 凍結的版面邊界、且 scroll extents 有契約意義時使用。不要僅因 locator 是 heading 或文字節點就拿它推論 glyph crop 或排版品質：字形 ink／line box 可能讓 scroll geometry 大於 client geometry，即使內容沒有被裁切；文字換行與詞組完整性改用對應的 rendered text assertions。

`schema_version: 2` 保留全部 v1 行為，並加入按需的 rendered typography／layout assertions；v1 不接受這些新 assertion，避免既有 strict contract 靜默改義：

```json
{
  "schema_version": 2,
  "cases": [{
    "id": "desktop-type-proof",
    "page": "index.html",
    "profile": "desktop",
    "steps": [
      {"id": "font-loaded", "action": "assert", "selector": "[data-display-type]", "expect": "font-face-loaded", "family": "Approved Display"},
      {"id": "heading-lines", "action": "assert", "selector": "h1", "expect": "line-count-between", "min_lines": 1, "max_lines": 3},
      {"id": "heading-tail", "action": "assert", "selector": "h1", "expect": "last-line-graphemes-at-least", "count": 2},
      {"id": "keep-release-phrase", "action": "assert", "selector": "h1", "expect": "text-segment-on-one-line", "segment": "放行"}
    ]
  }]
}
```

- `font-face-loaded` 同時要求 selector 的 computed `font-family` 使用指定 family，且頁面的 `FontFaceSet` 內有同名、狀態為 `loaded` 的 `@font-face`；它不證明字形完整、區域字形正確、授權或美感。
- `line-count-between` 量測 horizontal writing mode 的實際 text client rects；上下限是 evaluator 對這份固定內容與 viewport 的契約，不是通用最佳行數。
- `last-line-graphemes-at-least` 使用 grapheme cluster 而不是 UTF-16 code unit，適合確認固定短標題沒有一字尾行；不要對可任意變動的 user content 設成全域 gate。
- `text-segment-on-one-line` 要求 evaluator 明示的 literal segment 在唯一 locator 的可見文字中恰好出現一次，且其 rendered grapheme rects 位於同一列。它不做 Unicode 正規化、斷詞或字典猜測；不存在、重複、裁切或 vertical writing mode 都失敗。
- `rendered-text-includes` 要求唯一 HTMLElement locator 與其 composed ancestors 可見、有非零 box，並在 evaluator 啟動時捕獲的原生 `innerText` 中包含 literal value；它排除 `display:none` 等未渲染後代，不接受頁面覆寫 getter 後偽造的結果。`rendered-text-excludes` 要求唯一 HTMLElement locator；若 element 或 composed ancestor 的 `display`／`visibility`／`opacity` 使其不渲染就通過，否則要求 trusted `innerText` 不含指定 literal。若允許舊 control 隱藏，contract author 應用穩定 selector 定位，因 role locator 預設不解析 hidden element。替換型成功、錯誤或復原狀態要把正向新狀態與負向舊標籤／舊動作成對凍結，避免只因成功字串出現就放過仍可見的矛盾 UI。若舊 control 改名後繼續存在，contract author 還要執行它並斷言下一個可見狀態；runtime 不會從排除舊字串自動推論新動作有效。這些 assertion 都不證明語句美感、live-region 宣告或未明列的完整互動流程。
- `no-content-overflow` 要求 selector 有非零 client box，再比較 scroll/client geometry；只在該 box 是 evaluator 凍結的版面邊界且該區域不應合法捲動時使用。它不是 heading glyph crop、字形 ink 或 line box 的檢查器。
- `active-animation-count-between` 量測 selector subtree 內 `pending`／`running` 的 Web Animations API 數量；可在互動後證明有限動畫確實啟動，或在 reduced-motion profile 證明沒有 active animation。
- `animations-inactive-for` 要求 selector subtree 在 `duration_ms` 的 `50–1000` ms 觀察窗內每個 animation frame 都沒有 `pending`／`running` 動畫；任一 frame 出現即失敗且不重試，適合證明 reduced-motion 沒有延遲啟動。每個 case 最多一個觀察窗；它不是任意 sleep，也不證明非 Web Animations runtime 已停止。
- `animations-settled` 以同一個兩秒 bounded polling 等待 subtree 不再有 active animation。把它與最終產品 state assertion、rapid retrigger／reverse 動作一起使用；「已停止」不代表 timing、easing 或美感良好。
- `inline-start-aligned-with` 以原子雙元素快照比較 evaluator 指定、唯一且在 composed tree 可見的水平書寫元素之 logical inline-start；LTR 比左邊界、RTL 比右邊界，容許 `1 CSS px` 次像素差，並要求相隔 `50ms` 的兩次快照位置穩定。它只證明固定 viewport 下的相對 box 對齊，不判定 optical correction 或所有內容都該共用同一錨點。
- 普通 smoke 固定執行 `desktop`（`1440×1000`）、`mobile`（`390×844`）與 `narrow`（`320×800`）；`narrow` 是窄幅重排壓力測試，不增加 final craft acceptance 的截圖種類。
- v2 可使用 opt-in `mobile-motion` profile；它與既有 `mobile` 同為 `390×844`，但前者設為 `reducedMotion: no-preference`、後者維持 `reduce`。只有 contract 實際引用時才增加該 profile，讓 evaluator 在固定 viewport 下分離一般動效與 reduced result。

這些是 deterministic proof，不會自行挑選字體、判定排版漂亮或操縱 GSAP、Lottie、Rive、View Transition 等 runtime 的內部 timeline。候選字體、fallback、長文、resize 與具體 motion frame 仍須由 evaluator 提供固定 fixture，並以 fresh rendered craft review 收口。

Generic HTML smoke 會額外記錄 visible horizontal `h1`／level-one ARIA heading 的 `single_han_last_line_heading_count`。每頁／profile 最多掃描前 16 個 matching elements、每個最多 512 UTF-16 code units，並以 `heading_scan_count` 與 `heading_scan_truncated` 明示 coverage。它由實際 rendered grapheme geometry 得出，只是 novel-discovery advisory：不影響 gate status、不回傳文字，也不觸發自動修復。若 fresh screenshot 確認固定文案真的有孤字，再由 evaluator contract 明示 `last-line-graphemes-at-least` 或 exact `text-segment-on-one-line`；不要以中文斷詞猜測取代內容契約。

`--case-mode patch` 使用相同契約，並必須用 `--patch-lane polish|repair` 明示它是受限呈現調整（`POLISH`）或有證據的缺陷修復（`REPAIR`），不建立平行 lane。Retrofit／patch 必須提供 seed 與至少一個 `--allow-change`；任何未授權修改、刪除、重新命名、新增路徑、file／directory mode 漂移、空目錄遺失、seed 漂移或輸出集合漂移都會拒絕發布。Manifest 只保存 mode、實際 Skill lane、seed file/directory hashes 或 modes 與 observed mutation，不保存外部絕對路徑或 brief 內容。

Runner 不開放 shell 讀檔。小型 seed 會在 hash 重驗後，以最多 256 KiB 的 strict UTF-8 untrusted JSON 放入初始 prompt；每次 repair 另以最多 512 KiB 的當前 output snapshot 提供最小修正所需內容。檔案內的 instruction-like text 一律視為資料，retrofit／patch 的 repair prompt 也會重申原 mutation allowlist；超出 context quota 會 fail closed，不會改成開放 shell 或截斷內容。

Runner 會：

1. 把現行 Skill 複製成唯讀 snapshot，並記錄來源 hash。
2. 要求 Codex 只產生 caller 明列的相對輸出。
3. 以 process group、預設 30 分鐘 hard deadline、`min(10 分鐘, hard deadline)` inactivity deadline、輸出 byte budget 與 exact-output inventory 約束執行；兩個 deadline 都可由 CLI 明示覆寫，且 inactivity 不得超過 hard。
4. 驗證 Codex log policy、輸出路徑與 `DESIGN.md` clean contract。
5. 對 HTML 以 fresh Playwright Chromium context 執行可見內容、console、resource、網路邊界、root overflow 與 Axe smoke。
6. 將 deterministic failure 壓成 bounded repair packet，連同 hash-verified current output snapshot 交給同一模型與 reasoning effort 做最小修正；每輪只重驗受影響面。
7. 只有全部 release gates clean 時，才以原子 rename 發布 staged artifact，並寫入 runner-owned `run-manifest.json` 與 evaluator receipt。`trace_observed` 只記錄 `completed_item_counts` 與終端 token usage，不收錄模型文字或檔案內容，讓候選比較能辨識修復成本退步。若 repair fuse 觸頂，則把最後一個已驗證 checkpoint 移到 evaluator-owned quarantine、保持 target 空白並回傳失敗 receipt；quarantine 不是可發布成品。

若獨立 Playwright evaluator 不可用，Skill 可以繼續交付 runnable artifact，但相關 rendered claim 必須是 `UNVERIFIED`。模型自己的截圖、分數或完成宣告不能取代 evaluator receipt。

Current runner 的 `status: completed` 只表示 exact-output、`DESIGN.md` clean 與 deterministic HTML/Chromium/Axe smoke 通過；它不等於 screenshot acceptance、novel discovery、獨立 craft review、完整 release matrix 或商業上線核准。需要這些 claim 時，caller 必須提供獨立的 fresh Playwright evidence plane，否則維持 `UNVERIFIED`。

## Fresh 視覺證據與獨立 craft acceptance

截圖不進 build／repair loop。只對最後一份 `status: completed` 的 current build 執行一次：每個 HTML output 固定擷取 `1440×1000` 桌機與 `390×844` 手機 viewport，各用 fresh BrowserContext。這避免中間輪次、舊圖或另一份 source 冒充本次證據。

真正的 validation／test case 必須放在 evaluator-owned root，不能 commit 到 authoring repository。repo 內的 `current-craft-case.example.json` 只是 schema 範例；`product_cases.json` 仍只做公開 coverage，不是 held-out prompt。case 一旦把具體 feedback 回流 authoring，就視為 development data，不再稱為 held-out。

```bash
npm run capture:current -- \
  /absolute/evaluator-root/workspace \
  /absolute/evaluator-root/case.json \
  /absolute/evaluator-root/evidence-run-001
```

Capture command 會拒絕既存 evidence directory，capture 前後重驗 `run-manifest.json` 與所有 output hashes，並在失敗時移除本輪 partial cohort。成功後只留下本次 viewport PNG 與 `capture-receipt.json`；receipt 綁定 case、brief、Skill tree、manifest、outputs、Playwright/Chromium 與每張 PNG 的 hash、尺寸、viewport、locale、state。

獨立 reviewer 仍使用現有 `quality_result.json`、evaluator-owned `policy.json` 與 `ledger.json`，不新增第二套分數。完成 reviewer verdict 與 ledger 後，用 current acceptance wrapper 收口：

```bash
npm run accept:current -- \
  /absolute/evaluator-root/workspace/quality-result.json \
  --ledger /absolute/evaluator-root/ledger.json \
  --policy /absolute/evaluator-root/policy.json \
  --workspace-root /absolute/evaluator-root/workspace \
  --case /absolute/evaluator-root/case.json \
  --capture-receipt /absolute/evaluator-root/evidence-run-001/capture-receipt.json \
  --run-manifest /absolute/evaluator-root/workspace/run-manifest.json
```

`VERIFIED` 必須同時符合既有 deterministic／novel-discovery gates、evaluator release acceptance、完整核心 craft floor，且三個核心 craft 維度都實際引用本次所有 fresh screenshots。Reviewer 只取得 frozen brief、當次 receipt、screenshots 與 evaluator-owned policy；不取得模型 arm、舊圖或前次分數。回流只報 aggregate failure family，避免污染 validation/test partition。

信任邊界仍是 unsigned evaluator contract，不是密碼學證明。`independent: true` 只有在 reviewer 與 policy 實際位於 model write scope 外、且 builder 完成後才啟動時才可信。

## 現行檔案邊界

- `run_current_skill_build.py`：公開 CLI、repair loop、原子發布與 receipt。
- `codex_isolated_build_core.py`：受控 Codex 執行、snapshot、資源限制與 log policy。
- `current_skill_repair.py`：finding 正規化、root-cause 去重、repair packet 與收斂判定。
- `validate_design_md_clean.py`：pinned `@google/design.md` clean 驗證包裝。
- `playwright_html_smoke.cjs`：fresh Chromium/Axe acceptance smoke。
- `playwright_browser_runtime.cjs`：共用 Playwright network、popup、Service Worker 與 lifecycle policy。
- `capture_current_visual_evidence.cjs`：final-only fresh 桌機／手機證據與 provenance receipt。
- `validate_current_craft_acceptance.py`：把現有 craft policy／ledger 綁回 frozen case、current manifest 與 fresh capture set。
- `validate_codex_log_policy.py`：bounded stdout/stderr 與敏感輸出政策。
- `product_cases.json`、`trigger_cases.json`：通用產品與 trigger fixtures，不是已發布成果。
- `platform-support.json`：現行 package、script、runner 與 browser 的 evidence-bounded 支援快照。

## 基準與 Darwin 迭代

產品交付與 Skill 優化是兩個迴路：

- 產品交付預設使用現行 production runner 設定。
- Darwin／回歸評測主要以 `gpt-5.4-mini` 明示覆寫，讓較受限模型暴露指令、排版、互動與自修正缺口。
- accepted 與 candidate 必須使用同一 brief、模型、reasoning effort、工具鎖、輸出契約與 evaluator；較強模型不得悄悄進入其中一個 arm。
- 模型名稱是 evaluator 參數，不是另一份 Skill 版本或規則集。
- 只有 held-out 改善、現行 hard gates 乾淨且獨立 rendered review 支持時，才接受 Skill 改動。

最小 benchmark invocation：

```bash
npm run build:current -- \
  --brief /absolute/path/held-out.md \
  --target /absolute/path/run \
  --log-dir /absolute/path/logs \
  --model gpt-5.4-mini \
  --reasoning-effort high \
  --output index.html
```

不要把同一批輸出反覆加入規則後再稱為 held-out。不要保存舊 screenshot cohort 來替代 fresh replay；只有最新 source/build、fresh context、明示 viewport/state 與當次 receipt 能支持當次 claim。

## 驗證

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 wow-frontend-design/scripts/validate_installability.py wow-frontend-design --repository-root .
python3 wow-frontend-design/scripts/validate_platform_support.py evals/platform-support.json --repository-root .
python3 wow-frontend-design/scripts/validate_trigger_cases.py evals/trigger_cases.json --references wow-frontend-design/references
python3 wow-frontend-design/scripts/validate_product_cases.py evals/product_cases.json
node --check evals/capture_current_visual_evidence.cjs
python3 -m py_compile evals/validate_current_craft_acceptance.py
```

`npm run audit:html -- <path>` 是可選的 pinned Nu HTML Checker；它只提供 markup conformance signal，不證明視覺、互動、可及性或商業品質。
