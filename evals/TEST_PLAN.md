# 測試方案：v6 執行紀錄、v7 研究結果與後續優化路線

狀態：v6 固定 cohort `COMPLETED`（2026-07-15）；v7 roadmap `IN PROGRESS`。

v7 狀態（2026-07-18）：development instrumentation 與 A4 pilot 已執行；A4 因 deterministic findings 增加及 civic desktop material regression，未晉級為全域品質改善。v7 尚未完成 sealed promotion。Playwright evidence 已可編譯為 bounded repair packet；P0 consumer、P1 affected selector／best-artifact ratchet、P2 source-layout supporting registry、P3a zero-screenshot breakpoint／P3b normal-reduce motion sidecar、P4a categorical dominant-template advisory、P5a same-scope lint capability inventory、P6a cohort work-budget fuse，以及 P7 source-bound paired-decision compiler 已以合成 fixture 與契約回歸驗證 selective generation、actual-diff selection、target-full／cohort-full fallback、append-only fuse receipt、transactional promotion、source/advisory 去識別、unavailable 降級、bounded transition 收斂、fresh-context motion regression confirmation、跨 brief 近似骨架提示、不執行專案 script 的 lint discovery、generation／wall budget 觸頂停止，以及缺 sealed/source-bound evidence 時禁止升格。尚未執行 live model/browser repair cycle；P3/P4 sidecar、lint runtime adapter 與真實 P7 sealed bundle 也尚未進 live cohort，因此自動修正能力維持 `PARTIALLY VERIFIED`，不得把「runner／probe／decision compiler 已實作」轉述成「live cohort 已修正」、「所有 breakpoint 已覆蓋」、「符合 reduced-motion 可及性標準」、「已自動證明美感／原創性」、「lint 工具已可用／已通過」或「candidate 已可 promotion」。

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
- Agent Skills package 相容性只依標準與 installability gate；不按模型品牌分支。Python scripts、OS、POSIX evaluator 與主流 browser backend 只以本版 `platform-support.json` 的 stage-by-stage evidence 宣稱；官方文件與 repo 實測不得互相代替。這是一次性快照，不排定下次查核日期。

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

- 先用 `capture_runtime_profile.py` 記錄不含 host identity／environment dump 的 OS、architecture、Python、timezone 與 caller-declared shell／Node／browser／font profile；declaration 必須另綁 setup log 或 browser report。
- 只允許 workspace、project cache 或 evaluator cache。
- existing pin 優先；無 pin 才查官方 stable、排除 prerelease、解析相容版本並固定 exact version。
- 禁止 global install、第二套 lockfile family、產品 runtime dependency 漂移與 lifecycle script。
- tool-resolution record 包含 reason、source、version、scope、command、attempt 與 result。
- `--resume` 只續跑缺失／失敗階段，不能覆蓋已通過證據。
- GitHub Actions 另跑 `ubuntu-latest`、`macos-latest`、`windows-latest` 的 Python contract smoke；workflow 設定本身不能把未完成 cell 升級為通過。

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

## v7 歷史候選計畫：分階段優化與獨立供應鏈 lane

狀態：以下保留 v7 開跑前的原始 lane 設計，供 provenance 與未完成 sealed promotion 使用；現況以文件頂端 v7 狀態及「2026-07-18 後續持續優化路線」為準。A1–A4 development instrumentation／pilot 已執行，sealed validation／test 尚未完成，也不屬於 v6 證據。模型固定為使用者指定的 `gpt-5.4-mini`，禁止 silent fallback；新候選仍須等前一輪接受或拒絕並封存後另開 cohort。

| Lane | 單一假設 | 候選可改範圍 | 不得混入 |
| --- | --- | --- | --- |
| `v7-A1` | 更短、以 rendered result 為準的繁中標題／段落契約，能減少意外孤字、過窄文字軌與無意義右側空白，又不抹平合理 editorial rag | `references/typographic-layout.md`；evaluator fixture／assertion 另計，不是 Skill candidate | intrinsic grid/flex、原生控制項、色彩、動畫、framework adapter、registry security |
| `v7-A2` | intrinsic layout 與中間寬度／短高度防禦規則能減少擠壓、裁切與單字長柱 | 前一輪結案後另行凍結 | A1、native controls、視覺風格重設 |
| `v7-A3` | 原生控制項與 mobile viewport 契約能改善 IME、autofill、keyboard、safe area 與 focus recovery | 前一輪結案後另行凍結 | A1/A2、component-library adoption |
| `v7-B` | shadcn／第三方 registry 與 mutable audit payload 可在 mutation 前被固定、預覽、限制與驗證 | evaluator／security fixtures only | 不參與 A-lane 視覺改善分數，也不推導通用 shadcn 設計規則 |

`v7-B` 是獨立 release gate，可以拒絕不安全候選，但不能讓 `v7-A1` 因安全測試數量增加而取得視覺改善分數。A1 通過後才能規劃 A2，不把三個可疑原因塞進一次 Darwin 迭代。

### 開跑前 go／no-go

以下全部成立才可開始 generation：

1. 目前研究與計畫先通過 diff review、回歸並提交；working tree 乾淨。以 accepted commit 加上完整 package manifest 固定所有實際載入的 `SKILL.md`、references、adapter、scripts 與 metadata hash，不只記核心檔 hash。
2. 建立 evaluator-owned v7 case manifest、run schema、browser inventory、screenshot inventory 與 evidence validator；hidden prompt、selector、權重及 expected DOM 不在 implementation model 可讀／可寫範圍。
3. 每個新 deterministic rule 先用手刻 failing fixture、nearby valid counterexample、nearby invalid fixture 跑通；沒有反例就不進模型測試。
4. pinned Chromium／Firefox／WebKit、字型、locale、Node／Python、Codex CLI、`@google/design.md`、Playwright、runner、auditor 與 dependency lock 通過 smoke；下載完成不等於測試完成。
5. 用兩個公開 development pilot case 驗證 runner、timeout、repair、截圖 decode/hash、匿名配對與 resume。Pilot 只除錯 harness，不算 promotion evidence。
6. 依 pilot 記錄凍結每階段 inactivity timeout 與 hard ceiling。持續產生有效 log／artifact 只延長 inactivity deadline；若撞 hard ceiling，保留進度並把該 attempt 分類為 infrastructure incomplete，再 fresh retry，不改寫成模型失敗或成功。

Active cohort 開始後，candidate、case split、prompt、evaluator、gate、瀏覽器與工具版本全部不可修改。任何 evaluator defect 使該 cohort 無效；修正、補 regression、重新凍結後另開 ID。

### 研究假設與邊界

- `text-wrap: balance`／`pretty` 只能提供候選斷行；是否通過取決於每個引擎實際 line fragments、右側空白、孤字、語意單位與 fallback。禁止以 property presence 代替結果。
- 能通過 Chromium 不代表 Firefox、WebKit、Safari 或實體手機。每份證據記錄 engine、channel、version、OS、headless、fonts、locale、DPR、touch／`isMobile` 與 emulation/device。
- 跨引擎不做 exact-pixel equality。相同 pinned engine 才做 screenshot regression；跨引擎比較結構、互動、overflow、focus、字級層級、斷行風險與人工 craft。
- 不用 UA sniffing 切換 layout／功能。測試關閉 enhancement 或 feature query 不成立時，核心任務仍可完成。
- CLReq 的孤字、標點禁則、直排與參考行長用來造極端 fixture；不把書籍正文的兩端對齊或固定字數變成所有網站的硬規格。
- 外部 Skill、registry 與稽核規則只在 cohort 開始前解析、固定 revision／content hash 並封存。執行中來源漂移必須標成 evidence failure，不得靜默改變 gate 或替 candidate 追分。

### Sealed case 與比較組

- `development`：2 個公開新 case，只供 A1 最多 3 輪 bounded candidate 編修與 affected test；每輪只改同一候選資產的一個明示假設。連續兩輪沒有 deterministic 改善，或任一輪引入高優先級退步，就停止，不用增文換取主觀分數。
- `sealed validation`：4 個未進 authoring context 的新 case。最佳單一 candidate 才能進場；accepted／candidate 以相同 case、模型、effort、工具、資料與 evaluator 做 3 組 paired eligible runs，執行順序隨機且保留 attempt history。Infrastructure retry 不取代模型品質失敗。
- `sealed test`：2 個未使用 case，只在 validation 通過後跑 accepted／candidate 各一次。失敗即拒絕 candidate；不可讀取 hidden 細節修正後重跑同一 test。
- `no-skill` 只在 development 與 validation 各做一個預先指定的診斷 run，用來確認 Skill 是否提供正值；不與不同重複數的 accepted／candidate 合併評分，也不能抵銷 candidate regression。
- case family 錯開繁中 editorial／直排、密集 dashboard、原生表單、commerce、scroll narrative、低資訊產品頁與混合 CJK／Latin 長資料；公開的只有 family、主要任務與 claim boundary，完整 prompt／權重／selector／expected DOM 留在 evaluator-owned repo 外目錄。
- v6 只作 release regression，不可再當 held-out。若 runner／auditor／browser bytes 未變，可只跑 candidate 對 frozen accepted evidence；任一 evaluator byte 改變就必須在新 evaluator 下重跑 accepted 與 candidate，禁止跨 gate 直接比較。

### 分層瀏覽器矩陣

| Lane | Browser／OS | Viewport | 目的 |
| --- | --- | --- | --- |
| stress sweep | pinned Chromium／Linux | `360×800`、`390×844`、`768×1024`、`1024×600`、`1280×720`、`1440×1000` | 所有 case、危險 state、連續 resize 與自動修復 |
| engine parity | pinned Chromium、Firefox、WebKit／同一 CI OS | `390×844`、`1024×600`、`1440×1000` | 相同 route／state／fixture 的結構、斷行與互動差異 |
| Safari-near | pinned WebKit／macOS | `390×844`、`1440×1000` | 字型、media、safe-area、viewport 與 WebKit 特有風險；仍不宣稱 branded Safari |
| public channel smoke | stable Chrome／Edge，僅在產品支援需要時 | `390×844`、`1440×1000` | codec、enterprise policy 與 stable-channel regression；未跑即 `not_run` |

Firefox/WebKit binary 必須與 Playwright lock 對應。若環境無 macOS 或 branded channel，保留 `not_run`，不得用 Linux Chromium 補寫成通過。實體 iOS／Android 仍是另一個 device cohort。

### Adversarial fixtures

每個適用 case 至少組合下列風險，不只分開測 happy path：

1. 一字／一字加標點末行、三行長標題、短 display copy、繁英混排、數字單位、長 URL／hash、未斷使用者輸入。
2. `balance`、`pretty`、`stable`、不支援 enhancement 與 custom font 失敗；記錄每行文字、行數、行寬、container 寬與末行字數。
3. A2 保留 fixture：Grid/Flex `min-content`、`min-width:auto`、固定高度、圖片比例、scrollbar、sticky、overlay 與互動後新增錯誤／摘要；不得用來指導 A1 candidate。
4. 共用 regression：瀏覽器縮放／text spacing、fallback font、forced colors、reduced motion、深淺主題與缺圖；字型另測 cold／warm cache、慢速／阻擋／失敗載入，記錄 font CSS、request／bytes、text visibility、FCP／LCP／CLS 及換字型前後 line fragments。
5. A3 保留 fixture：`select`、date/color/file input、autofill、原生 validation、password manager、IME、paste、mobile virtual keyboard 與 focus return。
6. A3 保留 fixture：`safe-area-inset-*`、`svh`／`lvh`／`dvh`、landscape、短高度、overscroll 與固定底部操作。
7. A1 fixture：橫排與直排的標點、欄序、ruby／Bopomofo、選取／複製與 mobile 橫排 fallback；垂直 specimen 不得觸發橫排孤字規則。
8. v7-B fixture：既有 shadcn 專案分別使用 Radix／Base、不同 Tailwind／icon／alias 與本地修改元件；registry 包含官方、第三方、transitive dependency、redirect、CSS/plugin、env example、越界 target、symlink 與 overwrite。斷言 `view`／dry-run／diff 可追溯、未授權 mutation 為零、合法新增仍可編譯；這些結果只進 security/release gate。

### 必要截圖與盲審

- 每個 eligible generation 都必須至少保存 desktop base、mobile base 與一個關鍵 interaction state；A1 affected case 再保存 compact mobile 與 `1024×600` 中間／短高 viewport。缺任一必要 PNG、decode、尺寸、DPR、hash 或 provenance 就是 incomplete run。
- stress sweep 在 pinned Chromium 跑所有寬度；engine parity 只對預先指定的危險 route/state 跑三引擎，並各自截圖。遇到 deterministic finding，自動保存 failure 與 repair 後同 route/state/engine/viewport 的 before／after；不能只保留修好的圖。
- blind craft review 使用匿名 artifact ID、隨機 accepted/candidate 左右順序與相同 viewport/state contact sheet。Reviewer 只看 brief、畫面和 raw measured evidence，不得看到 arm、candidate diff、模型自評或前輪結論。
- 盲審分開記錄 hierarchy／spacing、繁中換行／段落節奏、product fit、mobile composition 與視覺缺陷；tie 是合法結果。它只能判斷 craft non-regression，不能覆蓋安全、互動、證據或 deterministic failure。

### Gate 與自修復

硬 gate 只處理可重現缺陷：核心任務 fallback 消失、overflow／裁切／遮擋、焦點或 scroll lock 失效、可讀文字低於要求、標題或正文意外孤字、title track 大面積無意義留白、原生控制項失去 label／value／error，以及證據或瀏覽器身分不實。`balance` 產生不同但仍合理的 rag、不同 rasterization、平台原生控制項外觀與有意圖的 editorial composition 交給 blind craft review，不自動改成同一外觀。

每個 finding 回送 `case → route → state → engine → OS → viewport → locale → fixture → measured failure → screenshot/hash`。兩個 loop 分開計數：

- **artifact repair**：同一輸出、同一 failure key 最多 3 次自修；有進度只延長 inactivity timeout。三次仍失敗就保存最佳 artifact、before／after 與 `PARTIALLY VERIFIED`，不得再改 Skill 規則救單一頁面。
- **Skill optimization**：development 最多 3 個 A1 candidates；每個 candidate 先跑 fast、再跑 affected，保留 accepted best-so-far 與 rejected diff。只有最佳 candidate 進 sealed validation，sealed failure 不回流同一輪 authoring。

### Promotion ratchet

Candidate 只有在以下全部成立時才能取代 accepted Skill：

1. installability、security、accessibility、evidence integrity、`DESIGN.md`、runtime mapping、required screenshot inventory 與 v6 regression 無退步；
2. sealed validation 的 paired deterministic vector 至少一個預先指定 failure family 嚴格改善，且所有更高優先級 family 不增加、沒有新增 case／engine failure；不得用總分互相抵銷；
3. 匿名 blind craft 配對中 candidate 不得出現多數 material loss；任何跨兩次 eligible run 重複的標題層級、段落節奏、右側空白、孤字或 mobile composition 嚴重退步直接拒絕；
4. selected reference names／bytes、input tokens、首個可用 artifact 時間、完整 wall time、重試次數與 flaky rate 保持在開跑前凍結的預算內；較便宜不能補償硬 gate，較漂亮不能補償缺證據；
5. v7-B security gate 通過；untouched sealed test 一次通過。任一失敗就拒絕 candidate、保留 accepted best-so-far，不修改 hidden test 追分。

新 cohort 完成前，只能稱這份內容為研究與測試計畫。README 不新增成果圖或通過宣稱；執行後再更新 `RESULTS.md`、evidence ledger、`CHANGELOG.md` 與展示。Darwin 9 維分數只作結構診斷，不是 promotion authority；實際決策以上述 paired evidence ratchet 為準。

## 2026-07-18 後續持續優化路線

這份路線用來限制範圍與避免「再加一個 scanner」的死循環。每輪只接受一個可歸因候選；先完成最高優先級的 exit criteria，再依實際 repair receipt 的問題分布決定下一輪。工具數量、規則數量、截圖數量與主觀總分都不是進度。

| 順序 | 單一能力缺口 | 候選邊界 | 必須證明的 exit criteria | 本輪不做 |
| --- | --- | --- | --- | --- |
| P0 | repair packet consumer 已完成 | evaluator-owned `packet → selective regeneration → narrow retest` runner；只處理 packet 明示的 `variant × case_id`；P0 以 frozen full matrix 作保守 fallback | 合成測試已證未失敗 target byte/hash 不變、同一 failure key 三輪熔斷、append-only receipt、full fallback 與 transactional promotion；未執行 live cycle | 新增 scanner、改 Skill 視覺規則、安裝套件 |
| P1 | affected matrix 與最佳產物選擇已機械化；待 live cycle | 用 issue class、實際 output receipt diff、宣告支援矩陣映射取代 P0 的常態 full-cohort fallback；新增 lexicographic best-artifact contract | 合成測試已證原失敗格必重跑；任何 rendered 變更擴大到完整 target matrix；未知範圍維持 full cohort；失敗保留 evaluator-owned deterministic best 而非最後產物。尚未取得 live model/browser receipt | 用 finding 總數抵銷核心任務／runtime regression；用 bytes/hash 抵銷 deterministic quality |
| P2 | source-layout registry 已完成 synthetic acceptance；待 live cycle | 以 hash-pinned contract 接入單一 source probe；固定高可信 allowlist、claim boundary、dedupe key、subject receipt 與最多三筆 advisory | 注入 fixture 已走完整 repair cycle；工具不可用、未知 code/schema、truncated scan 都明示 unavailable；advisory 不改 failure key、rank、promotion 或 Playwright authority。尚未取得 live model/browser receipt | 一次接入所有工具、外洩產品文字、把 unavailable 當 clean、讓 advisory 直接阻斷發布 |
| P3 | P3a breakpoint 與 P3b normal/reduce sidecar 已完成 fixture acceptance；待 live cohort | 零截圖 Chromium breakpoint probe 只在 categorical mode change 周圍收斂；motion probe 只在 normal 觀測到標準 Web Animations 時建立 reduce context，禁止注入全域極短 duration CSS | fixtures 已證 599–600px transition、fresh-context overflow confirmation、normal/reduce task regression 雙重重播、無 motion 不執行 reduce、animation/sample budget fail-closed、零 PNG/trace/video 與來源去識別；sidecar 不進 failure key/rank/promotion。尚不宣稱 cross-engine、touch、height、zoom、physical device、WCAG 或視覺品質 | 每個像素寬度截圖、以動畫數量評美感、用 reduce CSS 全域清零代替產品行為 |
| P4 | P4a exact／categorical dominant-template advisory 已完成 fixture acceptance；paired live cohort 待執行 | 以 product thesis、產品證據、內容結構與 locale 為條件；繁中 line fragments 與 task completeness 維持原硬 gate。跨產品工具只比較相同 surface/viewport/state 的 landmark、flow、track-count/balance、region role/representation、coarse visual order 與 histogram；不讀 palette/font/copy、不算 novelty score | fixtures 已證 spacing/radius/60↔65% track 微調無法隱藏同骨架；90/10 task weighting、CSS visual-order 交換、shared primitive、同 case route 不誤報；receipt 對輸入順序穩定且只是 advisory。live cohort 仍需 paired blind craft review，才能判斷 product-specific／美感 | 固定美學 preset、字型／色彩黑名單、近似分數追分、用 novelty 抵銷 usability；若連續兩個 frozen cohort 只有 false positive，停用 near candidate而不加權 |
| P5 | P5a Biome／Stylelint／ESLint same-scope capability inventory 已完成 fixture acceptance；P5b runtime adapter 目前熔斷為 `NOT_APPLICABLE` | 只讀 bounded package declarations、精確 config filenames 與 lint/check script names；不讀 script body、不載入 config、不執行命令。只有 P5a 在同一 scope 回報 `runtime_verification_required`，且 evaluator 能固定 local binary identity/version、config/parser/plugins、cwd、scope、diagnostics 與禁止寫入／對外的執行邊界時，才可另開 P5b 單一候選 | fixtures 已證 exact/range/protocol 只描述 manifest 字串、跨 workspace 不誤配、backup/disabled config 不誤認、script body/`--fix` 不外洩。現行 repo 無可用的 local lint toolchain，因此不安裝、不造 mock executor、不嘗試 `npx`／global binary／未知 script；任一 runtime provenance 或隔離條件缺失都只可 `UNVERIFIED`／`VERIFICATION_CAPABILITY_MISSING` | 把 Stylelint/Biome/ESLint 變成必要依賴；因 exact manifest 字串宣稱已 pin；執行名稱含 lint 的未知 script；把靜態 clean 升格為 rendered pass；在進入條件未改變時重開 P5b |
| P6 | P6a cohort work-budget fuse 已完成 fixture acceptance；待 live receipt 驗證真實停止行為 | 啟動前凍結 packet target hash、全 cohort generation／full verification／step-entry wall budget；在 generation、narrow capture、full verification、promotion 前檢查 | fixtures 已證多 target aggregate 上限、deadline 於 capture／promotion 前停止、staged best 與未經 narrow 的 inflight artifact 分離保存、staged receipt 明示 `pre_promotion_only` 而不宣稱 full matrix、usage unavailable、不增加 screenshot；成本永不參與 rank。尚未取得 live cycle receipt | 把步驟間 wall fuse 說成可中斷進行中的操作；估算 token／費用；以便宜或快速抵銷缺證據／品質退步；用局部 repair rank 冒充跨 Skill deterministic gain |
| P7 | paired-candidate 四態 decision compiler 已完成 fixture acceptance；真實 sealed bundle 待 evaluator-owned cohort | 唯讀套用 frozen promotion ratchet；accepted package／toolchain 從 manifest 重算，development／validation／三組 pair／sealed-test 雙 arm 各自綁定不可重用的 evaluator receipt；每個 arm 必須 source-bind generation/output/visual/attempt，pair 內 brief/input/execution 相同 | fixtures 已證 hard gate／較高優先 regression／material craft loss／budget exceeded／sealed test failure不可互相抵銷；同 path/content、同 pair/test evidence 或 run source、arm input drift、缺 attempt、單一呈現順序、缺 pair／hash drift／not-run 均 fail-closed；sealed test 不重用 validation brief/input/source。工具無 model/browser/network/promotion authority，現行 `pilot_ready` 只可 unavailable | 用總分、commit、repair rank 或主觀美感替代 sealed deterministic vector；把 source-bound receipt 說成重新驗過 raw screenshot；把 eligible-for-acceptance 當自動 promotion；因缺 bundle 繼續盲修 |
| P8 | 跨 candidate history fuse 延後；目前不得實作 | 只有同一 track／baseline／split／toolchain／candidate family 已存在至少兩份各自完整、來源唯一且狀態為 `REJECTED_STOP:no_strict_deterministic_improvement` 的真實 P7 receipt，才可建立 evaluator-owned、唯讀、hash-bound history receipt | 進入 P8 前先機械證明兩份 receipt 的 context 相同、candidate identity 與 evidence source 不重用、決策可重算；目前沒有第一份 frozen P7 receipt，因此 exit criteria 尚無真實輸入，Darwin fuse 生效 | 用 synthetic fixtures 冒充跨 candidate 歷史；從 commit message、主觀 judge 或單一 reject 推論連續無增益；在沒有新 receipt 時反覆重開 P8 |
| P9 | v2 focused-control obscuration repair gate 已完成 fixture acceptance；待 live cohort | hidden spec 只可宣告 1..8 個與 task step 綁定的 form control／primary action；每 target 兩個 fresh context，只有 simple opaque author-created fixed/sticky rectangle 的穩定全遮蔽可進 repair authority | fixtures 必須證明 v1/result schema 1 不漂移、v2/result schema 2 exact keys、full/partial/behind/transparent/blend/legacy clip/complex ancestor paint、外部 request、兩次 geometry drift、DOM/occluder/partition bounds、evidence derivation與 repair target mapping；unavailable 阻斷 clean 且不可成為產品修正；每個 matrix item 仍只有原本一張 screenshot。claim 僅限 named browser/profile/state 的 programmatic focus | 用 screenshot 猜遮擋；對 partial/transparent/complex geometry 下 repair 結論；把 programmatic focus 說成 keyboard、virtual-keyboard、AT 或 WCAG conformance；掃描所有 focusable DOM 取代 evaluator-declared task controls |
| P10 | fully obscured required click 的 incomplete-execution ledger 已完成 fixture acceptance；待 live cohort | 只處理 P9 coverage complete 且 confirmed control 精確綁定 hidden click step 的反例；產生 outcome-specific result schema v3，v1/v2 exact result contract不變 | fixtures 必須證 blocked click 從未執行／force、prefix completed、blocked/suffix incomplete、assertions 未評估、stepId 與 focus evidence 可重算、raw selector/value/copy/error 不外洩、repair packet只投影一筆既有 focus finding，且仍只有一張 screenshot；generic timeout、focus unavailable與 selector defect不可成產品修正 | 捕捉 Playwright raw error當 prompt；把未執行 step標 completed；把未評估 assertion標 failed；用 `force:true` 製造假通過；擴張成通用 action timeout classifier |
| P11 | required product text 的 direct clipping gate 已完成 fixture acceptance；待 live cohort | 限 product heading／prose 的 target 自身 client box；scroll/client delta 必須超過 tolerance，且 grapheme Range rect 必須在 box 外；只接受 ellipsis、inline clip、line-clamp、block clip 四種 direct mechanism | fixtures 必須證 fit/sub-tolerance clean、兩軸候選選對 block mechanism、normal line-height 與 complex paint fail closed、named focusable scroll region 不成 hard finding、其他 scroll 只 advisory、copy/selector 不進 prompt、repair packet 拒絕偽造 delta；零新增 screenshot | 掃 ancestor／pseudo content；把可捲動內容當裁切；用 scroll size 單獨下結論；擴張到 editorial/display/interactive、AT/cross-engine/整體美感；為此增加 screenshot 或新套件 |

### 每輪固定協定

1. 凍結一個 candidate、公開契約、對照組、典型 prompt、反例 fixture、nearby valid counterexample 與預期 claim boundary。
2. 先跑最窄 deterministic gate；有改善後，P0 使用已凍結 full matrix，P1 起才使用 affected matrix，未知範圍仍回到 full matrix；再跑 installability、完整 regression 與兩個獨立 judge。P0 full matrix 會重跑驗證格，但只保存原 failure／repair before-after 與新 finding 的截圖，不重複保存無關 clean 畫面。主觀 judge 不可覆蓋硬 gate。
3. 接受時自動 commit 並記錄 commit、測試輸出、工具版本、來源與下一個新問題；拒絕時保留 rejected diagnosis，回復 accepted best-so-far，不修改 active evaluator 追分。
4. 同一 failure key 三次失敗即熔斷；連續兩個 Skill candidates 沒有 deterministic 改善，或連續兩輪只有主觀小幅收益，停止該假設並回到 backlog。若新增 checker 沒有真實 counterexample 與 repair path，也停止。
5. 每三個 accepted commits 或每次 evaluator schema 變更後跑完整 contract suite（在 receipt 記錄本輪實際 test/run/skip 數）、Skill installability、v7 preflight 與一個代表性 Playwright smoke；一般快速修正不重拍無關頁面。

### 研究來源分級與採用結果

- **規範與官方文件（normative／primary）**：[W3C CSS Text Level 3](https://www.w3.org/TR/css-text-3/) 與 [CLReq](https://www.w3.org/TR/clreq/) 定義語言與換行邊界；它們用來造 fixture，不用來宣稱瀏覽器實作已通過。[Playwright best practices](https://playwright.dev/docs/best-practices)、[visual comparisons](https://playwright.dev/docs/test-snapshots) 與 [trace viewer](https://playwright.dev/docs/trace-viewer-intro) 支持 user-facing locator、web-first assertion、同環境 screenshot baseline，以及只在失敗／retry 保存 trace；本計畫因此不對每次成功 run 錄 trace或擴張截圖。
- **聚焦遮擋邊界（normative／primary）**：[WCAG 2.4.11](https://www.w3.org/TR/WCAG22/#focus-not-obscured-minimum) 把 author-created content 完全遮住 receiving keyboard focus 的元件列為反例；[Playwright `locator.focus()`](https://playwright.dev/docs/api/class-locator#locator-focus) 與 [`scrollIntoViewIfNeeded()`](https://playwright.dev/docs/api/class-locator#locator-scroll-into-view-if-needed) 提供可重現的 programmatic probe。本 evaluator 只把這些來源用於 bounded counterexample，並以兩個 fresh context 重現；沒有 physical keyboard／virtual keyboard／AT 證據，因此不宣稱 WCAG conformance。
- **Required click actionability（官方文件）**：[Playwright actionability](https://playwright.dev/docs/actionability) 明定 click 會檢查 Visible、Stable、Receives Events 與 Enabled；[Locator click API](https://playwright.dev/docs/api/class-locator#locator-click) 說明 actionability timeout 會 throw。P10 因此只在 P9 已以兩個 fresh context 證明 simple opaque overlay 位於 target 上方時，才把該 click 記為 blocked；不保存 timeout message，也不從一般 timeout反推產品缺陷。
- **必要文字裁切（normative／primary）**：[CSS Overflow Level 3 `text-overflow`](https://www.w3.org/TR/css-overflow-3/#text-overflow) 定義 inline overflow 的 clip／ellipsis 呈現，[CSS Overflow Level 4 `line-clamp`](https://www.w3.org/TR/css-overflow-4/#line-clamp) 定義限制可見行數的語意。P11 只用它們建立 direct target counterexample；實際 finding 還必須有超過 tolerance 的 scroll/client delta 與文字 Range rect，且不把規範語意外推成跨 engine、AT 或整體閱讀品質證據。
- **工具官方文件（adapter boundary）**：[Stylelint CLI/options](https://stylelint.io/user-guide/cli/) 支持 read-only diagnostics 與明示 fix；disable reporting 可抓無理由／無效／多餘抑制。[Biome CSS rules](https://biomejs.dev/linter/css/rules/) 區分 safe/unsafe code action。兩者都只在既有 project pin/config 成立時啟用，不能證明 rendered quality。
- **同類 Skill（方法參考）**：[Microsoft frontend-design-review](https://github.com/microsoft/skills/blob/main/.github/skills/frontend-design-review/SKILL.md) 的 task/craft/trust 分層與 [gstack design-review](https://github.com/garrytan/gstack/blob/main/design-review/SKILL.md) 的 finding-level before/after／revert 紀錄有參考價值；固定點數、字型禁令、效果配方、runtime-specific orchestration 與把主觀 grade 當 promotion gate 不採用。
- **Reddit 實務觀察（advisory only；擷取 2026-07-18）**：[AI-assisted Playwright workflow 討論](https://www.reddit.com/r/Playwright/comments/1umqvix/whats_missing_from_this_aidriven_e2e_testing/)提出 AI 較適合 evidence gathering／boilerplate，而非唯一 final skeptic；[E2E 投資範圍討論](https://www.reddit.com/r/webdev/comments/1r9ubwa/e2e_testing_for_frontend_developers_whats/)偏向保留 critical user flows、降低脆弱測試量。它們是未經本專案證明的實務假設，只用來設計反例；實際規則仍須由官方文件、固定 fixture 與本 repo evidence 證明。動態內容／字型 rasterization 的視覺噪音邊界直接採 Playwright 官方文件，不由 Reddit 推導。

P0–P7 與 P9–P11 的離線契約已完成 synthetic acceptance；P5b 與 P8 只有在上述可機械檢查的進入條件改變後才可重開。下一輪最高優先級是取得一份真實 full-matrix `repair_required` packet，再以單一 target／單一 generation 執行有預算的 live model + Playwright repair cycle；可能產生外部費用時仍須先取得明確授權。若授權或真實輸入尚未成立，只能從新的 deterministic counterexample 選一個有 repair path 的最小候選，不得以新增 scanner、mock runtime、更多截圖或主觀分數代替 live evidence。Pretext 在具備穩定 CLI、versioned result schema 與 bounded computed-style provenance 前不進自修正閉環。在 live cycle 與 sealed promotion 完成前，自修正能力維持 `PARTIALLY VERIFIED`。
