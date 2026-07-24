<p align="center">
  <img src="assets/wow-frontend-design-banner.svg" alt="WOW Frontend Design" width="100%">
</p>

<p align="center">
  <a href="https://github.com/NoMoneyDaddy/Wow-Frontend-Design/actions/workflows/ci.yml"><img alt="Quality workflow" src="https://github.com/NoMoneyDaddy/Wow-Frontend-Design/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://agentskills.io/specification"><img alt="Agent Skills compatible" src="https://img.shields.io/badge/Agent%20Skills-compatible-315b78?style=flat-square"></a>
</p>

# WOW Frontend Design

一套 current-only 的前端設計 Agent Skill：從明確產品需求直接建置、接手或局部修復可運作的 Web 介面，並以 fresh Playwright 證據、受限自修正與外部驗收維持品質邊界。

它不是元件庫、固定風格 prompt 或美學百科。Skill 會先保留專案契約，再從產品任務、內容關係與既有系統推導版面、互動、排版與視覺語言；繁體中文與真正重組的 mobile UX 是一等能力。

## 核心能力

- **一套標準**：只維護 [`wow-frontend-design/SKILL.md`](wow-frontend-design/SKILL.md)，不依模型另建 lite／full 版本。
- **三種工作模式**：greenfield 對應 `BUILD`、既有系統改造對應 `RETROFIT`、局部 patch 對應 `POLISH` 或有證據的 `REPAIR`。
- **產品衍生設計**：辨識度必須落在任務結構、資訊關係或互動，不靠通用卡片、流行配色或裝飾堆疊。
- **跨 viewport 排版**：處理 CJK 斷行、長文、fallback、zoom、長翻譯與 desktop／mobile 的不同任務順序。
- **可用的核心流程**：主要操作、選取、篩選、表單、錯誤、成功與恢復狀態必須真的可運作。
- **證據閉環**：最新 source/build → deterministic gates → bounded repair → fresh desktop/mobile Playwright → evaluator-owned acceptance。
- **保守接手**：seeded retrofit／patch 只允許明列路徑變更；其他檔案、目錄、mode 與行為契約保持不變。

## 快速開始

先預覽並固定一個已審查的 commit，再安裝到指定 host。以下示範 Codex 使用者範圍：

```bash
PIN="$(gh api repos/NoMoneyDaddy/Wow-Frontend-Design/commits/main --jq .sha)"
gh skill preview NoMoneyDaddy/Wow-Frontend-Design "wow-frontend-design/SKILL.md@$PIN"
gh skill install NoMoneyDaddy/Wow-Frontend-Design wow-frontend-design/SKILL.md \
  --agent codex --scope user --pin "$PIN"
```

重新開啟 session 後做唯讀 discovery smoke：

```text
Use $wow-frontend-design to audit this repository read-only. Report the detected
project type, mutation boundary, available verification capabilities, and exact
evidence ceiling. Do not edit files or install tools.
```

> [!IMPORTANT]
> 安裝成功不代表特定模型、browser 或平台已完成產品驗收。Host 路徑、版本 pin、更新、remote sandbox 與卸載方式請以 [`INSTALL.md`](INSTALL.md) 為準。

## 使用方式

### 新建介面

```text
Use $wow-frontend-design to build a Traditional Chinese dispatch dashboard.
The brief, required interactions, preserved hooks, desktop task, and mobile task
are below. Finish the runnable interface and verify it with fresh Playwright.
```

### 接手既有專案

```text
Use $wow-frontend-design to retrofit this booking flow.
Preserve the framework, routes, API contracts, analytics, form names, and current
business logic. Recompose mobile behavior and verify the affected states.
```

### 先看多組風格草稿

```text
Use $wow-frontend-design to inspect this project, then produce three materially
different direction groups for the same representative route. Keep product facts,
content, functions, and comparison conditions fixed. Show fresh desktop/mobile
Playwright captures before production. I will select one direction.
```

若希望不中斷，可明示「由你依主要任務、品牌辨識與手機成立度選定後繼續」。Skill 仍會先顯示同批 fresh captures，記錄 `user_delegated` 與選擇理由，再以正式 production route 重新實作與取證；草稿 HTML／PNG 不會直接升格為可發布產物。

### 局部修復

```text
Use $wow-frontend-design to repair the confirmed mobile heading wrap and sticky
focus obstruction. Modify only styles.css; preserve every other path and behavior.
```

一句話需求即可開始。Skill 會先讀取專案證據，整理產品、使用者、核心任務、必要互動、不可破壞契約與未知項；只有會改變公開契約或授權，或使可執行交付無法安全完成的最小缺口才詢問，其餘採安全可逆假設繼續，並在 handoff 列出未阻擋上線的缺口。

## 工作流程

```text
Evidence freeze → Representation → Direction → System → Vertical slice
               → Pressure / repair / replay → Evidence-bounded handoff
```

1. 偵測框架、入口、tokens、語系、測試與 mutation boundary。
2. 從操作與內容關係選擇介面形式，再決定視覺方向。
3. 建立或更新 `DESIGN.md`，只定義實作實際使用的設計角色。
4. 先完成一條可運作的 vertical slice，再擴大路由或元件。
5. 跑專案 gates、fresh Playwright 與一個 bounded discovery probe。
6. 對已確認問題做最小修正並重播受影響矩陣；乾淨或觸及 fuse 就停止。

## 受控 evaluator

`evals/` 是本專案的 release／Darwin 評測工具，不會在一般 Skill 任務中自動執行。它需要 POSIX、Python 3.9+、Node.js、authenticated Codex CLI，以及 repository-pinned Playwright Chromium／Axe／`@google/design.md`。

```bash
npm ci
python3 -m unittest discover -s tests -p 'test_*.py'

mkdir -p /absolute/evaluator/run /absolute/evaluator/logs
npm run build:current -- \
  --brief /absolute/evaluator/brief.md \
  --target /absolute/evaluator/run \
  --log-dir /absolute/evaluator/logs
```

公開 runner 只發布 exact outputs 與 runner-owned manifest；deterministic failure 最多進入 bounded repair。截圖只針對最後一份 completed artifact，獨立 craft verdict 再由 `accept:current` 綁定 fresh receipt。

> [!NOTE]
> Static lint、Axe、HTML conformance 與 screenshot 各自只證明有限範圍；商業核准、完整 WCAG、真實裝置、跨組織 reviewer independence 與 cryptographic trust 仍是外部事實。

完整命令、seeded retrofit／patch、capture receipt、quality ledger 與 acceptance contract 見 [`evals/README.md`](evals/README.md)。

## 專案結構

```text
wow-frontend-design/   可安裝的 Agent Skill package
  SKILL.md             單一規範性核心與 reference router
  references/          按任務載入的設計與驗證知識
  scripts/             偵測、audit、evidence 與 portability 工具
evals/                 current build / capture / acceptance evaluator
tests/                 contract、runner、browser 與 script 回歸測試
```

## 文件

- [`INSTALL.md`](INSTALL.md)：安裝、host discovery、pin、更新與卸載
- [`PLATFORM_SUPPORT.md`](PLATFORM_SUPPORT.md)：package、script、OS 與 browser 支援邊界
- [`evals/README.md`](evals/README.md)：受控建置、fresh capture 與 acceptance
- [`SECURITY.md`](SECURITY.md)：資安問題回報
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)：研究來源與第三方聲明
