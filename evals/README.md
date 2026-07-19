# 現行評測與受控建置

本目錄只支援一份規範性標準：`wow-frontend-design/SKILL.md`。`build:current` 是唯一受控建置入口；它不維護平行 Skill 版本，也不把舊產物或舊截圖當成新證據。

`evals/` 是 repository evaluator，不屬於安裝後自動執行的 Skill runtime。一般 Skill package 仍可只靠 `SKILL.md`、按需 references、scripts 與 assets 使用。

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

Contract 只允許 bounded `click`、`fill`、`press`、`select` 與 `assert` steps；可檢查 visible、attribute、text、count 及完全位於指定 viewport 內。`fully-visible-in-viewport` 必須排在所有互動前，語意才是未捲動的首屏；一般 assertion 會在兩秒內 bounded polling，`animations-inactive-for` 則對整段明示的觀察窗做一次連續判定；scenario 結束後另留 300ms 捕捉延遲 runtime error。它與 Axe、overflow、runtime error 使用同一個 Playwright gate 與最多兩輪 repair，不另建第二套 runner。Manifest 的 contract provenance 欄位只保存 schema、bytes、hash 與 case／step 數；HTML gate／repair history 只保存 bounded case／step ID。失敗步驟的 evaluator-authored locator、accessible name 與 `segment` 可進入 bounded repair prompt，但不會進 receipt、manifest 或發布產物；輸入值、預期狀態文字及外部絕對路徑不會進 repair prompt。Contract 是 evaluator 定義的 deterministic acceptance，不取代 fresh screenshot、獨立 craft review 或完整 E2E。

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
      {"id": "keep-release-phrase", "action": "assert", "selector": "h1", "expect": "text-segment-on-one-line", "segment": "放行"},
      {"id": "heading-fit", "action": "assert", "selector": "h1", "expect": "no-content-overflow"}
    ]
  }]
}
```

- `font-face-loaded` 同時要求 selector 的 computed `font-family` 使用指定 family，且頁面的 `FontFaceSet` 內有同名、狀態為 `loaded` 的 `@font-face`；它不證明字形完整、區域字形正確、授權或美感。
- `line-count-between` 量測 horizontal writing mode 的實際 text client rects；上下限是 evaluator 對這份固定內容與 viewport 的契約，不是通用最佳行數。
- `last-line-graphemes-at-least` 使用 grapheme cluster 而不是 UTF-16 code unit，適合確認固定短標題沒有一字尾行；不要對可任意變動的 user content 設成全域 gate。
- `text-segment-on-one-line` 要求 evaluator 明示的 literal segment 在唯一 locator 的可見文字中恰好出現一次，且其 rendered grapheme rects 位於同一列。它不做 Unicode 正規化、斷詞或字典猜測；不存在、重複、裁切或 vertical writing mode 都失敗。
- `no-content-overflow` 要求 selector 有非零 client box，再比較 scroll/client geometry；只對 block/container 使用，且該區域不應是合法 scroll container。
- `active-animation-count-between` 量測 selector subtree 內 `pending`／`running` 的 Web Animations API 數量；可在互動後證明有限動畫確實啟動，或在 reduced-motion profile 證明沒有 active animation。
- `animations-inactive-for` 要求 selector subtree 在 `duration_ms` 的 `50–1000` ms 觀察窗內每個 animation frame 都沒有 `pending`／`running` 動畫；任一 frame 出現即失敗且不重試，適合證明 reduced-motion 沒有延遲啟動。每個 case 最多一個觀察窗；它不是任意 sleep，也不證明非 Web Animations runtime 已停止。
- `animations-settled` 以同一個兩秒 bounded polling 等待 subtree 不再有 active animation。把它與最終產品 state assertion、rapid retrigger／reverse 動作一起使用；「已停止」不代表 timing、easing 或美感良好。
- `inline-start-aligned-with` 以原子雙元素快照比較 evaluator 指定、唯一且在 composed tree 可見的水平書寫元素之 logical inline-start；LTR 比左邊界、RTL 比右邊界，容許 `1 CSS px` 次像素差，並要求相隔 `50ms` 的兩次快照位置穩定。它只證明固定 viewport 下的相對 box 對齊，不判定 optical correction 或所有內容都該共用同一錨點。
- v2 可使用 opt-in `mobile-motion` profile；它與既有 `mobile` 同為 `390×844`，但前者設為 `reducedMotion: no-preference`、後者維持 `reduce`。只有 contract 實際引用時才增加該 profile，讓 evaluator 在固定 viewport 下分離一般動效與 reduced result，不增加普通 smoke 的預設矩陣。

這些是 deterministic proof，不會自行挑選字體、判定排版漂亮或操縱 GSAP、Lottie、Rive、View Transition 等 runtime 的內部 timeline。候選字體、fallback、長文、resize 與具體 motion frame 仍須由 evaluator 提供固定 fixture，並以 fresh rendered craft review 收口。

`--case-mode patch` 使用相同契約，並必須用 `--patch-lane polish|repair` 明示它是受限呈現調整（`POLISH`）或有證據的缺陷修復（`REPAIR`），不建立平行 lane。Retrofit／patch 必須提供 seed 與至少一個 `--allow-change`；任何未授權修改、刪除、重新命名、新增路徑、file／directory mode 漂移、空目錄遺失、seed 漂移或輸出集合漂移都會拒絕發布。Manifest 只保存 mode、實際 Skill lane、seed file/directory hashes 或 modes 與 observed mutation，不保存外部絕對路徑或 brief 內容。

Runner 不開放 shell 讀檔。小型 seed 會在 hash 重驗後，以最多 256 KiB 的 strict UTF-8 untrusted JSON 放入初始 prompt；每次 repair 另以最多 512 KiB 的當前 output snapshot 提供最小修正所需內容。檔案內的 instruction-like text 一律視為資料，retrofit／patch 的 repair prompt 也會重申原 mutation allowlist；超出 context quota 會 fail closed，不會改成開放 shell 或截斷內容。

Runner 會：

1. 把現行 Skill 複製成唯讀 snapshot，並記錄來源 hash。
2. 要求 Codex 只產生 caller 明列的相對輸出。
3. 以 process group、hard deadline、inactivity deadline、輸出 byte budget 與 exact-output inventory 約束執行。
4. 驗證 Codex log policy、輸出路徑與 `DESIGN.md` clean contract。
5. 對 HTML 以 fresh Playwright Chromium context 執行可見內容、console、resource、網路邊界、root overflow 與 Axe smoke。
6. 將 deterministic failure 壓成 bounded repair packet，連同 hash-verified current output snapshot 交給同一模型與 reasoning effort 做最小修正；每輪只重驗受影響面。
7. 只有全部 release gates clean 時，才以原子 rename 發布 staged artifact，並寫入 runner-owned `run-manifest.json` 與 evaluator receipt。若 repair fuse 觸頂，則把最後一個已驗證 checkpoint 移到 evaluator-owned quarantine、保持 target 空白並回傳失敗 receipt；quarantine 不是可發布成品。

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
