---
version: alpha
name: 植換所視覺系統
description: 只交換植物、不販售植物的社群網站視覺契約。
colors:
  primary: "#2D5B40"
  on-primary: "#FBF7EE"
  canvas: "#F5F0E6"
  surface: "#FFFDF8"
  on-surface: "#1E241C"
  muted: "#5B6658"
typography:
  display:
    fontFamily: '"Cormorant Garamond", "Noto Serif TC", "Iowan Old Style", Georgia, serif'
    fontSize: 54px
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  body:
    fontFamily: '"PingFang TC", "Noto Sans TC", "Microsoft JhengHei", system-ui, sans-serif'
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.7
    letterSpacing: "0em"
  ui:
    fontFamily: '"PingFang TC", "Noto Sans TC", "Microsoft JhengHei", system-ui, sans-serif'
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.01em"
spacing:
  xs: "6px"
  sm: "10px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  xxl: "48px"
rounded:
  sm: "12px"
  md: "20px"
  lg: "28px"
  pill: "999px"
components:
  page-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    padding: "{spacing.xl}"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "{spacing.md}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "{spacing.md}"
  chip:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "{spacing.sm}"
  chip-selected:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "{spacing.sm}"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  meta:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.muted}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "{spacing.xs}"
---

# 植換所視覺系統

## Overview

這個系統服務的是想交換植物的人，不是想買賣植物的人。
畫面要像一本活的交換索引：先看來源、狀態、照顧條件，再決定要不要接手。
語氣要可信、克制、帶一點標本卡的手感，讓交換行為本身比裝飾更明確。

## Colors

色彩只做三件事：承載紙感背景、標示可互動狀態、提示植物與照護的關鍵資訊。
底色與表面維持偏暖的紙白與葉綠灰，不用亮白或高飽和漸層搶走內容。
主色是深葉綠，只在主要行動、目前選取、可交換狀態出現。
中性色文字維持深墨色，次要說明用較低飽和的霧綠灰。
心理學主張不採信固定色彩公式；「綠色一定讓人更信任」在這裡是 `REJECTED`。

## Typography

標題使用帶手感的襯線語氣，讓頁面像植物標本冊而不是一般商品牆。
內文與控制項使用清楚的無襯線，確保長中文、數字、表單與狀態標籤都能穩定閱讀。
短標籤保留緊湊字距；中文正文不做機械式大寫或過度追蹤。
數字與日期要能在交換卡中快速掃讀，避免因字型風格犧牲資訊層級。

## Layout

桌面版用左右不對稱的索引式版面：主內容先講清楚交換意圖，側欄放補充規則或預覽。
行動版改成先看任務，再看細節，讓主要操作落在首屏與拇指可達區。
瀏覽頁把比較維度做成垂直清單與可切換篩選，避免把每株植物做成同權重的卡片牆。
發布頁則讓表單與預覽互相對照，桌面並排、行動端上下堆疊但保留同一份內容順序。

## Elevation & Depth

深度不靠重陰影，而靠紙面、邊線、留白與局部抬升。
只有主要容器與目前聚焦的互動元件才會略微浮起；其他區塊保持平面，像索引頁一樣安定。
需要分隔時用細邊線與色階，而不是把每一塊都做成相同圓角卡片。

## Shapes

形狀語言以標籤、卡片與長條膠囊按鈕為主，邊角圓潤但不軟到失去分類感。
交換標籤要像植物園的標本卡，保留直線、短欄位與清楚的欄目對齊。
例外只留給主要 CTA 與目前選取狀態，避免整站都被同一種圓角稀釋。

## Components

`page-shell` 定義整站的紙感底色與閱讀字色，所有頁面共用。
`panel` 是主要內容容器，承載索引、說明、預覽與表單區塊。
`button-primary` 只給最重要的動作，例如瀏覽交換或發布交換卡。
`button-secondary` 用於次級導覽與輔助動作，不冒充主要呼叫。
`chip` 與 `chip-selected` 服務篩選與狀態切換，讓行動版也能快速掃描與操作。
`field` 統一輸入框外觀，支援長中文與多行備註。
`meta` 放置小字、說明與時間標籤，維持低聲量但仍可讀。

## Do's and Don'ts

- 要把「只交換、不販售」說清楚，讓價格邏輯不要進站內語言。
- 要用交換原因、照護條件與取件方式建立信任。
- 要讓長中文、長品種名與備註在手機上可讀。
- 不要用商品陳列的誇張光澤去包裝活體植物。
- 不要把所有內容都做成同樣大的卡片。
- 不要讓色彩替代標籤、圖示或文字狀態。
