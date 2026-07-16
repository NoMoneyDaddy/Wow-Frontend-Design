# Changelog

本專案依 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/) 維護；版本遵循 [Semantic Versioning](https://semver.org/)。完整評測證據另見 [`evals/RESULTS.md`](evals/RESULTS.md)。

## [Unreleased]

### Added

- Portable CI contract smoke：用固定 Python 3.12 在 `ubuntu-latest`、`macos-latest`、`windows-latest` 驗 Skill installability、平台／capability ledger 與 focused tests；新增不讀 hostname／user／home／IP／environment、不執行外部 probe 的 runtime provenance helper，以及 `--report` 機器可讀缺口摘要。Workflow 尚未完成的 cell 不會自動升級。
- 一次性 script runtime 支援快照：Agent Skills package 依標準驗證，不按模型品牌分格；12 個固定 cell 精確涵蓋 23 個 installed Python entrypoint、CI／POSIX evaluator 與主流 browser backend，綁定 5 個官方來源座標。Validator 拒絕漏列／重複 script、未知來源、路徑逃逸、stage 矛盾與任何下次查核日期欄位。
- 中文標題逐行量測 gate：重建 `h1–h3` 可見字元行，將意外的一字末行回送自動修復，並納入 v6 evidence validator。
- 角色字級與字型研究：補入 GogoShark、PixelCake、Apple／Notion／Claude／Stripe／Uber／Mastercard `DESIGN.md`、MindStudio 選型文章、`getdesign@0.6.24`、`design-ai` 與 `emfont` 的可取模式及 schema／授權／預覽失敗／npm-repo 漂移／隱私邊界。
- `sk1llz` registry 與官方 Material Web 的 pinned 稽核：加入 manifest／分類可取模式、remote installer path／hash／symlink／staging／rollback／隱形 Unicode 防護，並明示 Material Web maintenance mode 與 exact-version adapter 邊界。
- `skill-repo-skill`、`darwin-skill`、Microsoft SkillOpt 與 CodeLove 比較研究：加入基線／候選比較、正反 trigger、重複 run、held-out validation、best-so-far／rollback 與獨立 evaluator 邊界。
- 官方 `greensock/gsap-skills` pinned 研究：加入 portfolio／AI dashboard／digital magazine／產品站／scroll narrative 的節奏契約，Hero、ScrollTrigger、dashboard preview、login→dashboard 的 runtime／cleanup／reduced-motion／refresh／驗證規則，並記錄上游範例與文件缺陷而不盲從。
- FWA／CSS Design Awards／CSS Winner／Awwwards 官方評選研究與 `top-design` pinned 稽核：新增選用型 award-quality lens，保留概念、signature moment、敘事節奏與 craft 啟發，拒絕自評得獎、固定美學配方、預設 smooth scroll 與壓過繁中／UX／可及性／效能的戲劇化。
- installability gate 會拒絕未由 `SKILL.md` 直接連結的 Markdown reference／adapter，讓孤兒指令文件在 CI 失敗而不是靠人工盤點。
- 新增 `SECURITY.md`，明示支援版本、敏感／非敏感回報邊界與目前尚未啟用 GitHub private vulnerability reporting 的限制。
- v6 evidence publisher：原子更新 8 案 manifest、generation ledger、64 張 PNG、auditor／Skill／研究筆記 hash，正式 lint report 可用顯式 `--overwrite` 續跑。
- evaluator-owned runtime downgrade 狀態機：進度延長 timeout、可恢復錯誤重試、三次同錯熔斷、驗證能力局部降級、權限／安全停止 mutation，並禁止同一 run 自動升級。
- Darwin-style ratchet 紀錄：三輪候選各完成 generation 與 64 張 audit，劣於基準即拒絕晉級，不以 clean `DESIGN.md` 取代 browser acceptance。
- 分層品質結果 schema 與 validator：硬 gate、independent craft vector、award lens、maintainer efficiency 分開；required `FAIL`／`UNVERIFIED` 會使結果 ineligible、保持 `weighted_total=null` 並禁止 `VERIFIED`。
- 常駐 Codex resource monitor：單一 Python process 以 0.5 秒週期量測 log／staging quota，取代 shell 每 0.1 秒反覆啟動多個程序。

### Changed

- Skill 維護流程把 standards-compatible package 與 executable runtime 分離；model routing 只屬於 evaluator 品質策略。Python／OS／POSIX evaluator／browser 支援採逐階段 ratchet，並要求 privacy-bounded runtime profile；caller declaration 不再能單獨升級為實測證據。
- README、INSTALL、平台說明、評測文件、公開 capability ledger 與 CI 改為引用同一份有界支援快照，未實跑平台維持未驗證；`SKILL.md` 核心不綁定這份一次性外部狀態，避免把安裝研究載入每個設計任務或冒充既有 v6 已用新版核心重跑。
- CI 更新並固定至官方最新穩定版 `actions/checkout@v7.0.0`、`actions/setup-python@v6.3.0`、`actions/setup-node@v7.0.0` 與 GitHub CLI `v2.96.0`，移除舊版 Node.js 20 Action 警告並保持可重現安裝。
- `SKILL.md` 由 333 行／約 5,942 words 收斂為 211 行／約 2,939 words：只保留 trigger、不可違反規則、reference router、七階段狀態機、自修復與 terminal behavior；詳細排版、元件、模型、驗證與研究規則維持在直接 references／scripts。
- `project_scan.py` 預設輸出 JSON，要求 project root 位於明示 `--authorized-root`，並對 symlink、FIFO／device、超限檔案與 Markdown／控制字元注入 fail closed。
- 最新繁中排版／layout／hierarchy／字型／色彩研究落實到 Skill 與全部 8 個 v6 網站；最終 ledger 為 8 repairs／0 promotions，公開契約修正後重新發布 64 張截圖。
- model profile 升級為 schema v2：依 task／locale／surface／risk、Skill／adapter／toolchain／evaluator revision 與 eligible run 路由；infrastructure failure 不計入模型成績。
- Codex case runner 依 caller model 與案例載入最小固定 context；v6 mini 實際輸入由 190,732 bytes 降至 145,024–161,274 bytes，manifest 保留選取清單，尚不宣稱速度改善。
- README 只保留產品說明、成果與實際使用流程；host 安裝範例、remote sandbox、pin、更新與卸載集中到 `INSTALL.md`，並新增 5 分鐘 discovery smoke。
- 評分改為 run validity → required hard gates → independent craft vector → optional award lens → maintainer efficiency 五層決策；v6 明確標為 development/regression closure，不再暗示 held-out validation。
- 以 pinned `darwin-skill` 與兩個獨立 judge 做 advisory ratchet；只採用「新 authority／material side effect 才停下確認」的 bounded checkpoint，拒絕頻繁 STOP、單一總分與重複 blacklist 等會降低 UX／證據完整性的 generic 建議。

### Fixed

- 安全稽核後關閉 shell quote／command-substitution trace 繞過、特殊檔／巨檔／深層 JSON 阻塞或耗盡、Codex 產物無大小上限、重複截圖冒充多個狀態，以及公開 evidence 洩漏本機絕對路徑等風險。
- v6 generation matrix 與公開測試契約統一為使用者指定的 `gpt-5.4-mini` 單一 cohort，移除預設會路由到不支援 v6 cases 的 Claude 分支。
- 修正補助審查 mobile dialog 的狀態 badge 搶走標題主軌，以及字體樣張 mobile hero 只剩「較」一字；窄回歸與第二輪完整 64 張 audit 均無 finding。
- 修正 evaluator 對 CJK／Latin measure、正文 parent container、長標題、task peer layout 與已翻譯術語的 false positives；新增對應 regression tests。
- 修正繁中標題以 `ch` 壓窄、正文右側無意義空白、介紹段落偏置、無語境英文 UI、假 CSS 圖解與 sticky 遮擋。
- 修正繁中改派表單觸發瀏覽器原生英文驗證泡泡，改由頁內繁中錯誤狀態與焦點回復處理。
- 修正 evaluator 偷綁小寫 size value、`data-step`、grant hidden ID／slot 與 royalty 私有狀態；改用語意輸入、可見狀態及 brief 公開 A/B／逐案 hook。
- 修正包材摘要 sticky 遮擋與口述歷史寬卡窄文；窄回歸 28 張、完整回歸 64 張均無 deterministic findings。
- 修正 runtime downgrade 把跨錯誤累積誤當「連續三次」，以及 progress timeout 延長錯算一次失敗；interleaved failure 與 progress→timeout 都有 regression test。
- generation retry 依 timeout kind 與 failure class 分流；hard-runtime、output-limit 與安全 policy rejection 不再盲目跑滿三次。

### Removed

- 移除已由 `product_cases.json` 與現行 `TEST_PLAN.md` 取代的 `evals/benchmark-matrix.md`。
- 合併兩份完全相同的 Claude showcase `BRIEF.md`，改由 `evals/briefs/showcase.md` 作唯一來源。

## [0.2.0] - 2026-07-15

### Added

- 使用者／開發者體驗契約：單次需求完成探索、設計、實作、驗證、自修復與交付。
- 驗證失敗自動回送 AI 的修復迴圈，保留最佳可用產物、截圖與局部驗證證據。
- 缺少驗證工具時，依既有 pin 或最新穩定相容版解析成精確版本，於專案本地／evaluator cache 安全補齊並續跑；benchmark 保持凍結工具鏈。
- Traditional Chinese／English 分語系行長、段落、語氣、標題語意換行、直書與橫書配置規則。
- 狀態 × viewport 驗證、CSS specificity、窄欄文字、大面積空洞與互動後版面重組檢查。
- 特效選擇器、效果預算、鏤空字體 fallback、forced-colors 與非真實 CSS art 邊界。
- `DESIGN.md` runtime conformance map、quoted `oklch()` 與 sRGB fallback／gamut 驗證規則。
- evaluator lockfile 更新到 stable `@google/design.md@0.3.0` 與 `playwright@1.61.1`；runner 從 lockfile 讀取精確版本。
- 四個 `gpt-5.4-mini` v5 測試主題與問題來源；其舊截圖已在新 cohort 前清空。
- `gpt-5.4-mini` v6 自修復 cohort：8 個產品、12 routes、4 種 device profiles、64 張最終截圖與 8/8 clean `DESIGN.md`。
- v6 evidence validator：綁定 model、repair provenance、manifest、auditor、viewport、DPR、PNG hash 與完整 inventory。
- 正文 browser-owned auto-wrap、完整 content-column flow、禁止非意圖 `<br>` 與 non-wrapping prose 的規則和自動 gate。
- 繁中注音／ruby 的語意標記、調號順序、OpenType 字型授權、跨引擎相容性、fallback 與驗證規則。
- 中文段落模式、標點光學置中、孤字／標題尾行、長 URL、混合文字間距與現代 CSS 換行邊界；明確拒絕舊式逐字 spacer／`wbr` DOM 改寫及全域 `break-all`。
- 跨產品、跨狀態、跨 viewport 的完整測試方案與執行紀錄。

### Changed

- 將 `BLOCKING` 重構為內部 `REPAIR REQUIRED`；一般視覺問題不再成為使用者端拒絕。
- 同根因三次修復仍失敗時交付 `PARTIALLY VERIFIED` 最佳版本；`BLOCKED` 只保留給權限、環境、安全或不可恢復錯誤。
- 長時間 runner 以 inactivity timeout 加 hard ceiling；輸出持續前進時延長等待，重試保留 attempt 與前次診斷。
- README 聚焦產品說明、安裝、使用與成果展示；評測方法與細節移至 `evals/`。
- 清除所有舊測試截圖與其發布 manifest；新截圖會在目前 Skill 完成自修復測試後重新建立。

### Fixed

- 修正 visual auditor 對 `zh-Hant-TW` 的錯誤 exact-locale 判定。
- 排除 screen-reader-only 文字的可見裁切假陽性。
- CJK 段落改用 script-aware measure，不再套用 English-only 行長判定。
- 補上 mobile open-state 窄欄、短操作標籤換行、段落 leading 與必要 hook 檢查。
- Playwright 瀏覽器補裝改用實體 `cli.js`，避免 `.bin` symlink 被安全檢查誤判。
- 修正 v6 補助審查 mobile navigation 互動定位的 evaluator false positive，並補 regression test。
