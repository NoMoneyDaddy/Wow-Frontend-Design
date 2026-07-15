# Changelog

本專案依 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/) 維護；版本遵循 [Semantic Versioning](https://semver.org/)。完整評測證據另見 [`evals/RESULTS.md`](evals/RESULTS.md)。

## [Unreleased]

### Changed

- CI 更新並固定至官方最新穩定版 `actions/checkout@v7.0.0`、`actions/setup-python@v6.3.0`、`actions/setup-node@v7.0.0` 與 GitHub CLI `v2.96.0`，移除舊版 Node.js 20 Action 警告並保持可重現安裝。

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
