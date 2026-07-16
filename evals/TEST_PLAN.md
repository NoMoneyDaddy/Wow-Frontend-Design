# v6 完整測試方案與執行紀錄

狀態：`COMPLETED`。固定 cohort 已於 2026-07-15 完成。

方法定位：這 8 案同時參與缺陷發現、Skill／evaluator 修正、Darwin candidate 比較與最終回歸，因此是 **development/regression closure**，不是 held-out validation，也不證明 Skill 已泛化。下一次 promotion 必須另用未進 authoring context 的 sealed validation／test tasks，比較 accepted 與 candidate Skill，並對 stochastic case 重複執行。

## 執行摘要

- 模型固定為 `gpt-5.4-mini`。初始矩陣先完成 7/8；`repair-cafe-intake-v6` 因 output policy 被拒後依規則 fresh retry，最終 generation 8/8 完成，attempt history 未被隱藏。
- 初始 browser audit：2 案 clean；6 案出現可重現的文字流、layout、互動或 mobile composition finding，逐案回送診斷並局部修復。後續把繁中排版、hierarchy、locale 與 layout 研究落實到最新 Skill，再以同一邊界檢閱並修正全部 8 案。
- 口述歷史過窄／過寬正文、補助審查 hidden desktop action，以及 CJK／Latin measure、parent container、heading、task peer 與術語翻譯等 evaluator false positive，均先修 evaluator 並補 regression test；package、repair、royalty 與 grant interaction 改以公開 brief hook、語意輸入與可見結果判定。
- 三輪 Darwin 候選共跑 3 次 generation、3 次 64 張 audit；最終 6 案仍有 findings，ratchet 拒絕晉級並保留 repo 外診斷。人工並排檢閱後補上逐字 line-fragment 標題 gate，先修補助 dialog，再由第一次全矩陣抓出字體樣張同類孤字；窄修後第二次 64 張完整重驗為 8/8 targets、0 findings。generation ledger 記錄 8 repairs／0 promotions；官方 `DESIGN.md` verifier 8/8 clean。
- Mobile 與 compact-mobile 使用 Android Chromium UA、touch、`isMobile=true`、DPR 3 與 mobile screen／visual viewport；仍只屬 browser device emulation，不是實體手機。
- 64 張發布 screenshot 全部由最終 post-orphan-gate rerun 取代並重新計算 SHA-256；manifest、visual report、auditor、Skill 與研究筆記互相綁定，沒有沿用舊圖。

重驗完整性：

```bash
python3 wow-frontend-design/scripts/validate_product_flow_v6_evidence.py \
  evals/product-flow-v6-visual-results.json --repository-root .
```

## 目標

這一輪不只測「能不能生成頁面」，而是驗證目前 Skill 是否真的完成：

1. 一次需求走完 inspect → design → build → verify → repair → handoff。
2. `DESIGN.md` 在頁面組合前可被官方工具接受，且 token 真正映射到 runtime。
3. 驗證 finding 會自動回送 AI 修正，不要求使用者重送需求。
4. 繁中、英文、混合語系、直書、橫書、長字串與標題換行不破版。
5. 桌機、平板與 mobile-device emulation 是不同 composition，不是只改寬度；不把 emulation 說成實體手機。
6. 缺工具、timeout 與短暫下載失敗可安全補齊或重試，並保留最佳產物。
7. README 最後只展示完成修復且證據完整的結果。

不宣稱：實體手機認證、跨所有瀏覽器、正式 WCAG conformance、真實 Core Web Vitals、模型普遍排名或 award 品質。

## 凍結條件

開始前一次性凍結並寫入 generation ledger：

- provider：Codex。
- requested model：只用 `gpt-5.4-mini`；禁止 silent fallback。
- Skill、brief、runner、auditor、schema、test plan 與 lockfile 的 SHA-256。
- `@google/design.md@0.3.0`、`playwright@1.61.1`，或執行前經官方 stable channel 確認後另開變更，不在 active run 中升級。
- Node、Python、Codex CLI、OS、browser engine revision、locale、timezone 與字型環境。
- implementation builder 停用 browser/computer/subagent；外層 evaluator 獨立擁有瀏覽器、截圖與判定。
- 平台／OS／environment／model 支援只以本版 `platform-support.json` 的 stage-by-stage evidence 宣稱；官方文件與 repo 實測不得互相代替。這是一次性快照，不排定下次查核日期。

Active gate 開始後不得修改期待值或 auditor。發現 evaluator defect 時，該 run 標記無效；修 evaluator、補 counterexample test、重新凍結後再開新 run。

## 八個互相錯開的產品主題

| Case | 產品方向 | 主要壓力 | 必測狀態 |
| --- | --- | --- | --- |
| `wind-maintenance-dispatch-v6` | 離岸風場維修派工台 | 高密度資料、排序、狀態色、窄欄 | filter、empty、選取、重新派工、成功／失敗 |
| `type-foundry-specimen-v6` | 繁中字體鑄造所樣張庫 | 字體選擇、鏤空字、直書／橫書、混合 script | writing-mode 切換、長標題、fallback、forced colors |
| `repair-cafe-intake-v6` | 社區修繕咖啡館預約 | 多步表單、語氣、錯誤恢復、長輸入 | invalid、修正、確認、返回編輯、鍵盤流程 |
| `night-market-allergen-v6` | 夜市過敏原隨身指南 | thumb-first、標籤密度、短操作文字 | 搜尋、篩選、無結果、展開攤位、離線提示 |
| `royalty-statement-v6` | 獨立音樂版稅結算 | 數字／表格／資料視覺、正負語意色 | 期間切換、tooltip touch fallback、異常款項 |
| `packaging-configurator-v6` | 循環包材三頁規格配置器 | 元件尺寸、選項組合、跨頁 sticky summary | 配置、材質、摘要；衝突、價格更新、mobile summary、reset |
| `oral-history-archive-v6` | 海岸口述歷史三頁典藏 | 低資訊 editorial、多路由、長段落 | 首頁、典藏、故事頁；長文、腳註、媒體 fallback |
| `grant-review-board-v6` | 社區文化補助審查台 | 權限語氣、比較、批次操作、對話框 | 待選名單、A/B 比較、對話框焦點、錯誤／重試 |

Brief 需固定 audience、主要任務、內容極端值、必要 interaction hook、mobile transformation 與 acceptance focus。Evaluator 只能依 brief 公開的精確 hook 或可觀察結果操作；不得偷綁未公開 ID、value 大小寫、wrapper、slot 或 state attribute。不得在 brief 內指定視覺答案或複製 v4／v5 主題。

## 執行階段

### 0. Harness preflight

模型開始前先完成：

- 本輪 evaluator 固定 v6 case／route／state inventory，並以 report schema、auditor hash 與 evidence validator 防止 drift；通用 manifest-driven inventory 留待下一個 schema 版本，不在 active cohort 中改期待值。
- 實作同一 target 的 remediation mode；每輪保存 before／after、diagnostic、diff、hash 與 screenshot。
- 建立通用 evidence validator，拒絕 stale hash、額外／缺少圖片、錯誤 viewport、被隱藏 retry 與 auditor drift。
- 對 tool resolver 實測 existing pin、缺 package、缺 browser、transient failure、無網路、唯讀 cache 與不相容 runtime。
- 先跑 unit、syntax、Skill installability 與 `DESIGN.md` CLI smoke test。

### 1. Initial generation

- 8 cases 各以全新空 target 執行。
- 每 case generation infrastructure 最多 3 attempts。
- timeout 以 inactivity 判斷；log 或 evaluator artifact 持續增加時延長 soft deadline，但不超過 hard ceiling。
- fresh retry 只接收一行有界、標記為 untrusted 的前次 diagnostic。現行 hardened policy 只自動重試 inactivity timeout 與一般 generation failure；hard-runtime、output-limit、contract/security policy rejection 不盲目重跑，需先分類與明示 remediation。
- 不覆蓋成功 target，不把 retry 次數隱藏成單次成功。
- Runner 由 caller 的 `model × case` 選取最小固定 reference 集並把清單寫入 manifest；模型不自報能力。每次 cohort 凍結實際清單與 hash，路由變更必須另開 cohort 才能比較速度或品質。

### 2. `DESIGN.md` gate

每個 target 檢查：

- 官方 lint：0 errors、0 warnings。
- quoted `oklch()` 合法；production CSS 同時有 sRGB fallback。
- root token、component role、spacing、radius、type role 與 effect policy 有 runtime 對應。
- 不存在 orphan token、sample value、無單位 dimensional zero 或無法解析的 reference。
- 色彩檢查使用實際 component foreground/background pair，不只掃色票。

Finding 自動送回修復；只重跑該 target lint，再跑 8-case contract regression。

### 3. Browser interaction

每個 case 至少覆蓋：

- primary task 的 A→B→A 路徑。
- keyboard traversal、focus visibility、modal／drawer containment、Escape 與 focus return。
- filter／search、empty、invalid、error、retry、success 與 stale-message cleanup。
- mobile navigation 的 open／closed state、scroll lock、inert background、touch target 與 sticky obstruction。
- console error、failed request、HTTP >=400、unexpected external request 均為空。
- reduced motion；支援 theme 時測 light、dark、system；forced colors 至少做結構檢查。

不得用 DOM click fallback 升級 acceptance。Diagnostic continuation 可保留後續觀察，但 verdict 仍維持失敗。

### 4. Responsive and typography matrix

| Profile | CSS viewport | DPR | Device contract | 範圍 |
| --- | --- | --- | --- | --- |
| Desktop | `1440×1000` | 1 | mouse、非 mobile UA | 所有 route／base state |
| Tablet | `834×1112` | 2 | touch、tablet UA | 所有 route／base state |
| Mobile | `390×844` | 3 | Android Chromium UA、touch、`isMobile=true` | 所有 route／base state |
| Compact mobile | `360×800` | 3 | Android Chromium UA、touch、`isMobile=true` | 每 case 主 route 與最危險 state |

這是 mobile-device emulation，不是假裝成實體手機。Evidence 必須記錄 UA、touch、`isMobile`、DPR、screen、visual viewport 與 orientation。實體 iOS／Android 若日後有遠端裝置才另開 cohort；沒有就明示 `UNVERIFIED`。

文字矩陣：

- 繁中正文、英文正文、繁英混排、數字／單位、URL／email、Arabic sample 與 200% text spacing。
- semantic title wrap、不可斷短操作標籤、表格數字對齊、長輸入、CJK 標點與孤行風險。
- 橫書使用 script-aware measure；直書必須有明確語意、欄序、標點、fallback 與 mobile 退出條件。
- component 使用 intrinsic sizing；不得因 `min-width:auto`、固定欄寬或高 specificity 把文字壓成單字／單字元長柱。

### 5. Visual evidence and manual review

最低發布 inventory：

- 12 routes × desktop／tablet／mobile base state：36 張。
- 8 cases 的 compact-mobile 主 route：8 張。
- 每 case 一個關鍵互動 state，desktop＋mobile：16 張。
- 合計至少 60 張 PNG；任何多 route／多 state 增量都必須進 manifest。

每張圖需完整 PNG decode、尺寸／DPR／SHA-256、route、state、theme、locale、browser revision 與 auditor hash。Screenshot 不是單獨 QA；判定同時使用 brief、DOM/runtime 量測、互動結果與同 viewport/state 的 before／after 組合。

人工視覺檢查：

- 版面平衡、大面積空洞、群組關係、卡片／元件間距、邊框與字色層級。
- 標題語意換行、段落節奏、語氣、閱讀順序與繁中／英文密度差異。
- 特效只依 effect selector 使用；每個畫面最多一個 signature effect，不要求所有元件都有特殊效果。
- 鏤空字必須有 readable fallback、forced-colors fallback，且不可套到長正文或關鍵操作。
- 禁止用 CSS／div／手刻 SVG 偽造應有來源與授權的 icon、logo、照片或資訊圖。

### 6. Automatic repair loop

分類固定為：

- `REPAIR REQUIRED`：自動回送 case、route、state、viewport、finding code、量測與 screenshot。
- `MANUAL VISUAL`：意圖明確才自動修；純偏好保留 advisory。
- `ADVISORY`：不阻斷交付。
- `EVALUATOR DEFECT`：先修 evaluator，不動產品。

每次只修最小根因，先跑 narrow gate，再跑受影響 regression。相同根因最多 3 repairs；仍失敗時保存最佳可用網站、before／after screenshot 與下一個可執行命令，標為 `PARTIALLY VERIFIED`。只有缺權限、必要基礎設施不可用、安全風險或不可恢復 build/runtime failure 才用 `BLOCKED`。

### 7. Developer and remote-sandbox experience

在本機與一個無 writable home 假設的 remote-like sandbox 各做 smoke test：

- 只允許 workspace、project cache 或 evaluator cache。
- existing pin 優先；無 pin 才查官方 stable、排除 prerelease、解析相容版本並固定 exact version。
- 禁止 global install、第二套 lockfile family、產品 runtime dependency 漂移與 lifecycle script。
- tool-resolution record 包含 reason、source、version、scope、command、attempt 與 result。
- `--resume` 只續跑缺失／失敗階段，不能覆蓋已通過證據。

### 8. Model routing and automatic downgrade

- 不接受模型自報 `strong`／`weak`。起始 lane 只讀 evaluator-owned schema-v2 profile；cell 以 task／locale／surface／risk 匹配，另綁 Skill、adapter、toolchain 與 evaluator revision。
- `attempts` 必須等於 eligible runs 加 infrastructure failures；只有至少 3 次獨立 eligible runs 且 contract／invariant 全過、無 unsupported claims 才能進 `STANDARD`。
- Profile 缺失、過期、hash 不符、surface 不符、工具不足或 high-risk 一律 fail closed；infrastructure failure 不換算成模型設計失敗或通過。
- Runtime event 只允許 lane 不變或降低。每個 root cause 使用 evaluator-owned `failure_key`，不同 route／state／工具／根因不得共用三次熔斷計數；測試 progress timeout、無進度 retry、第三次同錯熔斷、schema／invariant failure、缺 verification、缺 mutation、security／permission block 與 evaluator boundary violation。
- 一般 repair finding 前兩次保留 lane 並自修；第三次才停止盲修、保留最佳產物。成功 retry 不在同一 run 自動升級。
- 不用一次 generic probe 推論全域能力；probe 結果只限同一工具、契約與環境。更高 lane 必須以新 profile 開新 run。

## 通過標準

必須全部成立才發布 `VERIFIED` cohort：

- generation 8/8 完成，model selector 與 attempt history 完整。
- `DESIGN.md` 8/8 clean，runtime mapping 無 drift。
- 所有必要互動、route、state 與 viewport 完整；無 runtime／network blocker。
- deterministic visual findings 為 0；manual visual 無未解嚴重問題。
- automatic repair 至少以注入 fixture 證明 finding → repair → narrow rerun → regression 的閉環。
- 最少 60 張 screenshot 與所有 artifact hash 通過通用 validator。
- unit、lint、syntax、build、Skill installability、CI equivalent 全過。
- 平台快照 inventory、官方來源綁定、安全 artifact path 與 stage consistency validator 全過；`not_run` 不能被改寫成 `supported`。
- 結果文件明確分開 `VERIFIED`、`OBSERVED`、`INFERRED`、`UNVERIFIED`。

這些條件只能關閉 development/regression cohort。Skill promotion 另需 sealed held-out validation/test 無硬 gate 退步，且依「安全／資料／主要任務 → evidence coverage → deterministic defects → independent craft → runtime/context cost」順序比較；不得用加權總分抵銷前層失敗。

## 發布與清理

- raw attempts、trace、quarantine、未採用 screenshot 留在 repo 外 evaluator root。
- repository 只收最終 repaired targets、必要 reports、通過 validator 的 screenshot 與一份 machine-readable manifest。
- README 只放代表性桌機／平板／mobile 成果；完整 60+ 張 inventory 放 `assets/` 與結果頁，不把圖片數量當品質分數。
- 更新 `RESULTS.md`、`capability-status.json`、`CHANGELOG.md`、README 與第三方 notices 後才 commit／push。
- 不覆寫舊證據來製造改善；新 cohort 使用新 ID、Skill hash 與獨立 ledger。

## 啟動條件（已執行）

使用者說「開始測試」後，已依序執行 harness preflight、8-case generation、lint、browser、repair、完整回歸與發布。執行中只要仍有進度輸出就延長 soft timeout；未完成的 generation／lint／capture 依分類重試，沒有用 timeout 偽裝完成。
