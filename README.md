<p align="center">
  <img src="assets/wow-frontend-design-banner.svg" alt="WOW Frontend Design：跨模型、跨框架、跨語系的前端設計 Agent Skill" width="100%">
</p>

<p align="center">
  <a href="https://github.com/NoMoneyDaddy/Wow-Frontend-Design/actions/workflows/ci.yml"><img alt="Quality workflow" src="https://github.com/NoMoneyDaddy/Wow-Frontend-Design/actions/workflows/ci.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/github/license/NoMoneyDaddy/Wow-Frontend-Design?style=flat-square"></a>
  <a href="https://github.com/NoMoneyDaddy/Wow-Frontend-Design/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/NoMoneyDaddy/Wow-Frontend-Design?style=flat-square"></a>
  <a href="https://github.com/NoMoneyDaddy/Wow-Frontend-Design/commits/main"><img alt="Last commit" src="https://img.shields.io/github/last-commit/NoMoneyDaddy/Wow-Frontend-Design?style=flat-square"></a>
</p>

<h1 align="center">WOW Frontend Design</h1>

一套可攜式、production-oriented 的前端設計執行與品質閉環 Agent Skill，用來把產品需求轉成可運作、可驗證、可修正的高辨識度前端。它不是元件庫或固定美學百科；會依偵測到的框架、host、工具、裝置、語系與既有系統調整流程。繁體中文與不只縮放寬度的手機版面／互動是核心能力。可攜不等於所有模型／平台都已實測，也不保證一次生成即可上線。

Portable Agent Skill for designing, building, auditing, and refactoring distinctive, production-oriented frontends—with first-class Traditional Chinese and mobile UX. Portability is not universal empirical certification.

## 它解決什麼

- 從空專案建立概念、設計系統、版面、互動與 production code。
- 偵測既有專案的框架、入口、樣式、i18n、測試與風險，再做最小安全修改。
- 建立「概念句、版面語法、色彩規則、範圍相稱的 authored distinction」；新建／大改才加入招牌時刻，局部修復不擴張範圍。
- 手機版會重排、替換、延後或改變互動，不只把桌面欄位改成直向。
- 內建繁中、CJK、長翻譯、RTL、字型 fallback 與 locale QA。
- 納入 WCAG 2.2 AA、Core Web Vitals、reduced motion、鍵盤、zoom、錯誤狀態與效能驗證。
- 模型不自報強弱：外部、分任務能力 profile 決定起始 lane；實際 schema／工具／驗證結果只能自動降級，不能自行升級。
- 維持一份精簡核心與按需載入的直接 references；不分叉 `lite`／`full` 兩套真相，短 context host 只作明示降級 adapter。
- 內建 motion 技術階梯、SVG 信任／嵌入／授權管線與靜態風險稽核器。
- 驗證失敗會自動回送 AI 做 bounded 最小修正並局部重驗。受控 release runner 只有在全部 gates clean 時才發布；觸頂時保留 evaluator-owned quarantine 與失敗 receipt，不能把它改稱完成品。
- 缺少驗證工具時，先沿用已安裝且與 lockfile 相符的工具；新增套件、修改 lockfile 或使用 evaluator cache 都必須在 caller 已授權的範圍內。未授權時保留網站產物並把受影響 claim 標為 `UNVERIFIED`，不做 global install。

## 相容與安裝

本專案遵循開放的 [Agent Skills specification](https://agentskills.io/specification)，只維護 `wow-frontend-design/SKILL.md` 這一份規範性標準。Codex、Claude Code、GitHub Copilot、Gemini CLI 或自訂 wrapper 只要正確實作該標準，就應載入同一份 package；host 安裝與 discovery 仍需各自驗證。[腳本支援說明](PLATFORM_SUPPORT.md)與[一次性 runtime 快照](evals/platform-support.json)只追蹤 Python、OS、現行 evaluator 與 Playwright Chromium，不把未測模型列成 Skill 缺口。安裝路徑、5 分鐘成功流程、remote sandbox、版本 pin、更新與卸載由 [`INSTALL.md`](INSTALL.md) 單一維護。

## 使用

新專案：

```text
Use $wow-frontend-design to create a premium Traditional Chinese travel journal.
Desktop should feel editorial; mobile should use a distinct thumb-first journey.
```

既有專案：

```text
Use $wow-frontend-design to inspect this repository and redesign the checkout.
Preserve routes, APIs, analytics, and the current framework. Verify mobile, errors, and zh-Hant.
```

不確定如何描述時，只要說明產品、使用者與主要任務；skill 會推導可逆的設計方向，只在答案會實質改變範圍或架構時提問。

實際流程是：檢查專案與可用能力 → 分類建置／重構／修復範圍 → 建立設計 thesis 與 `DESIGN.md` → 實作真實狀態與 mobile transformation → 驗證 → 自動修正 → 交付。一般互動工作流觸頂時可保留最佳可預覽 artifact、證據與下一個動作，標為 `PARTIALLY VERIFIED`；受控 release runner 則只保留 quarantine，發布 target 維持空白。

多路由、新產品流程或資訊層級尚未收斂時，可先產生互相綁定的 `site-manifest.json` 與 `wireframe-plan.json`。它們分別描述 IA／權限／發現意圖，以及區域／內容極端值／狀態／互動／手機轉換；crawler 用的 XML Sitemap 是第三種獨立 artifact。低風險元件修補不強制 wireframe，實作需求也不能停在 wireframe。

建立或變更視覺系統時，Skill 會在頁面組合前建立／更新 repository-root `DESIGN.md`。官方格式接受 quoted `oklch()`；production CSS 仍保留 sRGB fallback 與 rendered contrast 檢查。驗證器優先使用與 lockfile 相符的 `@google/design.md`；若工具不存在且未獲安裝授權，網站產物仍可繼續，但文件驗證必須標為 `UNVERIFIED`。

## 文件

- [安裝與 host 路徑](INSTALL.md)
- [Agent Skills 相容性與腳本支援](PLATFORM_SUPPORT.md)
- [資安回報政策](SECURITY.md)
- [Skill 核心流程](wow-frontend-design/SKILL.md)
- [評測方法與重現方式](evals/README.md)
- [腳本 runtime 支援快照](evals/platform-support.json)

## 授權

[MIT](LICENSE) © 2026 奶爸 and contributors。研究來源、`NOASSERTION` 邊界與 evaluator 開發依賴見 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)；上游 Skill 僅作批判性研究，不代表其文字、程式或資產已被併入本專案。
