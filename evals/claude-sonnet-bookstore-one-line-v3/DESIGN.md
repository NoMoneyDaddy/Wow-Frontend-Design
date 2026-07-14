---
version: alpha
name: 典藏書局設計系統
description: 以典藏索引為視覺語法的書局網站，溫暖紙質質感配合朱紅行動色，傳遞知識收藏的份量感。
colors:
  primary: "#C0392B"
  on-primary: "#FEFCF8"
  surface: "#FEFCF8"
  on-surface: "#1A1714"
  canvas: "#F5F1EA"
  on-canvas: "#1A1714"
  ink: "#1A1714"
  ink-muted: "#6B6358"
  ink-faint: "#9C9287"
  border-subtle: "#DDD5C8"
  border-strong: "#A8988A"
  action: "#C0392B"
  action-hover: "#A93226"
  surface-raised: "#FAF7F2"
  accent-literature: "#5B4A8A"
  accent-history: "#2E6B5E"
  accent-science: "#1A5276"
  accent-art: "#7D6608"
  accent-children: "#E07B1A"
typography:
  display:
    fontFamily: "Georgia, \"Noto Serif TC\", \"Source Han Serif TC\", \"Times New Roman\", serif"
    fontSize: 56px
    fontWeight: "700"
    lineHeight: 1.1
    letterSpacing: -0.01em
  headline:
    fontFamily: "Georgia, \"Noto Serif TC\", \"Source Han Serif TC\", \"Times New Roman\", serif"
    fontSize: 32px
    fontWeight: "700"
    lineHeight: 1.2
    letterSpacing: -0.005em
  subheading:
    fontFamily: "system-ui, -apple-system, \"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 20px
    fontWeight: "600"
    lineHeight: 1.4
  body:
    fontFamily: "system-ui, -apple-system, \"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 1.75
  caption:
    fontFamily: "system-ui, -apple-system, \"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 13px
    fontWeight: "400"
    lineHeight: 1.5
    letterSpacing: 0.01em
  meta:
    fontFamily: "system-ui, -apple-system, \"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 11px
    fontWeight: "600"
    lineHeight: 1.4
    letterSpacing: 0.08em
rounded:
  none: 0px
  sm: 2px
  md: 4px
  lg: 8px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  xxl: 64px
components:
  button-primary:
    backgroundColor: "{colors.action}"
    textColor: "{colors.on-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
  button-secondary:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
  book-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
  nav-link:
    textColor: "{colors.ink-muted}"
    typography: "{typography.caption}"
  tag:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.meta}"
    rounded: "{rounded.none}"
    padding: "{spacing.xs}"
---

# 典藏書局設計系統

## Overview

典藏書局服務熱愛閱讀的讀者，以知識收藏與發現為核心任務。視覺語法以「典藏索引」為主軸，取材於實體書局的書脊排列、分類標籤與索引卡，讓每位讀者感受瀏覽書架時的實質份量與脈絡感。

個性關鍵詞：典雅（elegant）、可信（authoritative）；絕不浮誇（never flashy）。

## Colors

**畫布色**（canvas `#F5F1EA`）：模擬舊書紙質的溫暖米色，作為全站基底。

**表面色**（surface `#FEFCF8`）：比畫布色略白，用於卡片、面板等提升層次感的區域。

**朱紅行動色**（primary/action `#C0392B`）：僅限於可操作的按鈕、連結、重點標記與書脊色帶標題。朱紅出現代表「此處可行動」。

**墨色層次**（ink `#1A1714`、ink-muted `#6B6358`、ink-faint `#9C9287`）：文字三層，主體、輔助、說明依次降低飽和度。

**分類色帶**：各文學類別有專屬輔助色，用於書脊左側色條及分類標籤。色彩僅輔助分類辨識，必須搭配文字標籤共同使用，不可單獨依賴色彩傳達意義。

- 文學：`#5B4A8A`（紫調）
- 歷史：`#2E6B5E`（墨綠）
- 科學：`#1A5276`（深藍）
- 藝術：`#7D6608`（金褐）
- 兒童：`#E07B1A`（橙色）

## Typography

**展示聲音**（display、headline）：明體（Serif）傳遞書局的學術份量與閱讀傳統，用於頁面大標題與書名展示。

**閱讀聲音**（body）：無襯線系統字型，清晰易讀，用於內文說明、書籍描述。

**功能聲音**（caption、meta）：與閱讀聲音同族，尺寸縮小，用於分類標籤、版本資訊、元資料。

中文排版規則：`line-break: strict`、`word-break: normal`，body文字行高1.75，讓中文長段落舒適呼吸。避免對中文標題施加過大字間距。

## Layout

桌面版採 12 欄格線，最大閱讀寬度 `1200px`，頁面留白 `clamp(1.5rem, 4vw, 4rem)`。書目清單區使用 3 欄或 4 欄展示，讓讀者如翻閱書架般掃視。

行動版導覽收入側抽屜，書目改為單欄或雙欄，書脊色帶縮減為左側 4px 標記條，關鍵操作（購買、加入書單）固定於畫面底部拇指區。

內容寬度上限：`measure-reading: 68ch`，避免長段落在寬螢幕上過度延展。

## Elevation & Depth

層次優先採用色調差異與邊框，而非陰影。

- **畫布層**：canvas 色
- **表面層**：surface 色（卡片、面板）
- **懸浮層**：`box-shadow: 0 2px 8px rgba(26,23,20,0.10)` 僅用於互動中的卡片 hover 狀態
- **遮罩層**：半透明 `rgba(26,23,20,0.48)` 用於行動版導覽開啟時的背景遮罩

## Shapes

全站以直角（`rounded.none: 0px`）為主要形狀語言，呼應書頁邊緣的工整感。唯有搜尋輸入框使用 `rounded.sm: 2px` 稍作柔化，其餘元素一律直角。不使用圓角卡片或膠囊按鈕，以維持典藏氛圍。

## Components

**button-primary**：朱紅底、米白字、無圓角、無陰影。Hover 時背景加深至 `action-hover`，過渡時間 140ms。

**button-secondary**：畫布色底、墨色字。用於輔助操作如「加入書單」。

**book-card**：表面色底、無圓角。左側 4px 色帶為該書分類色。標題使用 subheading，作者與定價使用 caption，分類標籤使用 meta。不加卡片陰影，透過色調區分表面與畫布層。Hover 時整張卡片升起一層淡陰影，過渡 140ms。

**nav-link**：墨色偏暗，hover 時轉為朱紅。不使用底線，以色彩傳達狀態，但 focus-visible 時顯示 2px 朱紅 outline。

**tag**（分類標籤）：畫布色底、小型全大寫追蹤字距。使用 meta 字型，搭配對應分類色前綴點，非純色彩標示。

書脊色帶（Signature Detail）：每本書展示時，左側或頂部 4px 實色條帶即為該書分類的書脊顏色，模擬書架書脊的視覺語言，是本設計系統的核心識別特徵。

行動版轉換：導覽列改為 hamburger + 全版面抽屜，書目格線改為 2 欄（＜480px 時單欄），底部固定購買列，安全區域 `env(safe-area-inset-*)` 保護。

## Do's and Don'ts

- Do 為每本書的書脊色帶使用正確的分類色，並搭配文字標籤。
- Do 朱紅色僅用於行動元素，不作為裝飾。
- Do 展示聲音（明體）用於書名與大標題；功能聲音（黑體）用於導覽與說明。
- Do 行動版確保購買按鈕在拇指可及範圍。
- Don't 用圓角卡片或浮動陰影裝飾所有元素。
- Don't 用單一色彩傳達分類，必須搭配文字標籤。
- Don't 在中文正文標題加入過大字間距。
- Don't 在不同頁面為同一語意角色使用不同色彩或字型。
