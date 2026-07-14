---
version: alpha
name: 山域救援任務協調台
description: 高密度指揮員工作台；精準、克制、可掃讀。語彙取自地形標記、座標、無線電頻道與耐候現場符號。
colors:
  primary: "#0F1923"
  on-primary: "#E8EDF2"
  surface: "#161F29"
  on-surface: "#C8D4DF"
  surface-raised: "#1E2A36"
  on-surface-raised: "#D6E1EA"
  surface-overlay: "#243040"
  border-subtle: "#2A3A4A"
  border-strong: "#3D5268"
  ink-primary: "#E8EDF2"
  ink-secondary: "#8FA8BF"
  ink-disabled: "#4A6278"
  action: "#3D8BCD"
  action-hover: "#5AA3DD"
  focus: "#5AA3DD"
  danger: "#C0392B"
  on-danger: "#FFFFFF"
  warning: "#B07D2A"
  on-warning: "#FFF3CD"
  success: "#2E7D4F"
  on-success: "#D4EDDA"
  priority-critical: "#C0392B"
  priority-high: "#B07D2A"
  priority-normal: "#2E6B9E"
  status-active: "#3D8BCD"
  status-standby: "#5A6E7E"
  status-resolved: "#2E7D4F"
typography:
  display:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif"
    fontSize: 22px
    fontWeight: "600"
    lineHeight: 1.2
    letterSpacing: -0.01em
  heading:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif"
    fontSize: 15px
    fontWeight: "600"
    lineHeight: 1.3
    letterSpacing: 0em
  body:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif"
    fontSize: 14px
    fontWeight: "400"
    lineHeight: 1.6
    letterSpacing: 0em
  meta:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, PingFang TC, Noto Sans TC, monospace"
    fontSize: 12px
    fontWeight: "400"
    lineHeight: 1.4
    letterSpacing: 0.02em
  label:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif"
    fontSize: 11px
    fontWeight: "600"
    lineHeight: 1.3
    letterSpacing: 0.06em
rounded:
  none: 0px
  sm: 2px
  md: 4px
  lg: 6px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
components:
  button-primary:
    backgroundColor: "{colors.action}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink-secondary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  record-card:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.on-surface-raised}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  nav-item:
    backgroundColor: "transparent"
    textColor: "{colors.ink-secondary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  nav-item-active:
    backgroundColor: "{colors.surface-overlay}"
    textColor: "{colors.ink-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  status-badge:
    backgroundColor: "{colors.surface-overlay}"
    textColor: "{colors.on-surface-raised}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  summary-stat:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink-primary}"
    typography: "{typography.heading}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
---

# 山域救援任務協調台

## Overview

目標使用者是山域救援指揮員，同時監看多個責任區的任務進度、通訊狀態與隊伍負荷。工作情境高壓、資訊密集，需要一眼識別優先等級與任務階段，不需要行銷說服力。

設計性格：精準、克制、耐候。視覺語彙源自地形圖圖例、無線電頻道標示與現場座標符號。色調以深海軍藍為地底，以金屬灰為內容層，以冷藍為可操作元素。

密度：高。每筆任務以對齊列或緊湊卡呈現，讓指揮員橫向比較多任務而不逐頁點開。

## Colors

顏色語意規則：

- `primary`（#0F1923）：頁面底板，提供深度錨點。
- `surface`（#161F29）：主工作區基層。
- `surface-raised`（#1E2A36）：任務記錄容器與面板。
- `surface-overlay`（#243040）：懸停高亮、已選狀態、次要面板。
- `action`（#3D8BCD）：僅用於可操作的連結、按鈕、互動焦點。不用於純資訊裝飾。
- `danger`（#C0392B）：只表示真正的危險或嚴重超時。不用於急迫度高但未超時的任務。
- `warning`（#B07D2A）：時限接近或高急迫度，非實際危險。
- `success`（#2E7D4F）：任務已結案或回報安全。
- `priority-critical` / `priority-high` / `priority-normal`：急迫度是獨立語意維度，不與任務階段或時限混用。
- `status-active` / `status-standby` / `status-resolved`：任務階段獨立上色，不與急迫度染色互相干擾。

非顏色備援：急迫度同時搭配圖示（●▲■）與欄標籤；階段搭配狀態標籤文字；時限搭配倒數數字。所有語意維度皆有非顏色識別，符合使用色彩不作為唯一識別手段的原則。

## Typography

字型角色：

- `display`：頁面標題與任務區塊大標，強調地點或任務編號。
- `heading`：欄標題、區塊副標。
- `body`：任務描述、隊伍資訊等主要閱讀內容。
- `meta`：座標、時間戳記、無線電頻道等技術數據，使用等寬字族，確保數字對齊與可辨度。
- `label`：欄標籤、狀態徽章、緊湊按鈕；全大寫僅用於拉丁字母縮寫（如 UTM、GPS），不施於中文。

中文排版：`line-break: strict`；`word-break: normal`；body 行高 1.6 適合密集中文閱讀。不在中文段落施加 letter-spacing 擴字。

## Layout

桌面：三欄式管理台框架。最左為固定側欄導覽（200 px）；中間為主工作區（彈性），以帶欄標的橫向表格或比較列呈現八筆以上任務；右側為選中任務的詳情面板（320 px，預設摺疊）。

最大內容寬度：1440 px，留頁邊距 24 px。任務列欄寬固定或以 minmax 控制，確保欄標籤與數值不換行。

行動端（< 768 px）：側欄改為頂部緊湊標題列加漢堡選單；任務工作區轉為優先 inbox，以卡片垂直排列，僅顯示急迫度、階段、任務名稱、時限；詳情區摺疊為頁內展開。不把桌面表格縮小，而是重新選擇呈現維度與順序。

## Elevation & Depth

以色調深淺表達層次，不依賴大型陰影：

- 底板（`primary`）最深，提供空間錨點。
- 工作區（`surface`）略淺一層。
- 任務容器（`surface-raised`）再淺，形成自然群組感。
- 選取/懸停（`surface-overlay`）最淺，作為互動狀態。

細線邊框（`border-subtle`）用於行間隔；`border-strong` 用於分區。無大型模糊或多層陰影。

## Shapes

形狀語言：工具性、矩形優先，圓角極小（2–6 px）。圓角大小對應元件尺寸，而非裝飾趨勢。現場儀器介面與地形圖的形狀語彙。

- 任務記錄容器：4 px 圓角。
- 按鈕與狀態徽章：2–4 px 圓角。
- 側欄導覽項目：2 px 圓角。
- 無膠囊、無大圓角卡片、無玻璃擬態。

## Components

**任務記錄（record-card）**：每筆含急迫度指示器（顏色＋符號）、任務編號、地點、階段徽章、時限倒數、責任區、隊伍、無線電頻道。桌面以表格列呈現，行動端以卡片呈現，兩種呈現共用同一 DOM 記錄，以 CSS 控制欄位可見性與排列。

**狀態徽章（status-badge）**：固定寬度，文字不換行。急迫度、階段、時限三種徽章各有獨立語意色彩，不互相繼承。

**摘要統計列（summary-stat）**：頁面頂部帶數字的 KPI 格，顯示總任務數、進行中、高急迫度計數。此列為輔助，不取代主工作區的完整任務列表。

**導覽（global-nav）**：側欄固定導覽；行動端摺疊為抽屜，使用 `aria-expanded`、焦點管理、Escape 關閉。

不支援的細節（不放入 token frontmatter）：邊框顏色、陰影細節、hover 過渡時長、任務列選取高亮、抽屜動畫、表格橫向捲動行為、列印樣式。

## Do's and Don'ts

- 使用顏色同時搭配非顏色識別符（符號、標籤、數值）區分語意維度。
- 急迫度、任務階段、時限三種維度顏色規則各自獨立，不互相染色。
- 危險色（`danger`）只用於真正危險情境或確認超時，不用於「高急迫度但未超時」。
- 行動端重新構成優先 inbox，不縮小桌面表格。
- 不使用大型 hero 區、行銷 CTA、pricing、testimonials、玻璃擬態、霓虹漸層或裝飾性卡牆。
- 不在中文 UI 文字中使用大量全大寫眉標。
- 不在同一語意維度內混用兩套顏色系統。
