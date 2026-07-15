---
version: alpha
name: 社區植栽交換設計系統
description: 只交換植物、不販售植物的社區網站視覺契約。
colors:
  primary: "#2F6B4F"
  on-primary: "#FFFFFF"
  canvas: "#FAF7EF"
  on-canvas: "#1F2B24"
  surface: "#FFFFFF"
  on-surface: "#1F2B24"
  secondary: "#6E4F2E"
  on-secondary: "#FFFFFF"
  accent: "#A94F2D"
  on-accent: "#FFFFFF"
  muted: "#E7DED1"
  on-muted: "#3D473F"
  focus: "#184E77"
typography:
  headline:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 42px
    fontWeight: 750
    lineHeight: 1.12
    letterSpacing: "0em"
  title:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 24px
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "0em"
  body:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "0em"
  label:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 14px
    fontWeight: 650
    lineHeight: 1.35
    letterSpacing: "0em"
rounded:
  sm: 4px
  md: 8px
spacing:
  xs: 6px
  sm: 10px
  md: 16px
  lg: 24px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  button-secondary:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.on-secondary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  surface-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  muted-strip:
    backgroundColor: "{colors.muted}"
    textColor: "{colors.on-muted}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  accent-badge:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  focus-marker:
    backgroundColor: "{colors.focus}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  page-title:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-canvas}"
    typography: "{typography.headline}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  section-title:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.title}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
---

# 社區植栽交換設計系統

## Overview

BRIEF: 幫我做一個只交換植物、不販售植物的社區網站。

此系統服務社區居民用餘苗、插枝、盆器、照護時間互相交換植物。介面要像一張可查閱的鄰里交換簿：可信、溫和、清楚，不把交換關係包裝成商店。主要任務是快速找到可交換植栽並提出一則不含金錢的交換邀請。

## Colors

綠色只代表可交換與主要行動；棕色代表規範、照護條件與社區承諾；陶土色標示提醒與限制，例如「不販售」。焦點藍只用於鍵盤焦點與狀態定位，不承擔品牌情緒宣稱。色彩心理主張狀態為 `UNKNOWN`，本系統不宣稱顏色會提高信任或交換意願。

## Typography

字體採系統字與繁體中文優先 fallback，避免外部字體請求。`headline` 用於頁面主標與關鍵交換承諾，`title` 用於區段與植栽名稱，`body` 用於說明、照護與規範，`label` 用於按鈕、狀態與欄位標籤。中文段落不加字距，行高保留足夠閱讀空間，混合拉丁名稱與數字時保持自然斷行。

## Layout

桌面版採「交換簿」結構：左側或上方提供持續導覽，主要區域用不等寬欄位呈現焦點刊登、規範與交換步驟。瀏覽頁以列表和篩選為主，細節頁讓植栽資料與交換表單並置。手機版把導覽壓成可換行的頂部列，優先顯示所在地、交換狀態與主要行動；桌面並排比較在手機改為依序閱讀與可點選篩選。

## Elevation & Depth

深度以紙張層次、細邊線和輕微陰影呈現，避免玻璃、強烈光暈或厚重卡片堆疊。重複項目可使用 8px 以下圓角卡片；規範、流程和頁面區段以開放式排版或橫向條帶建立節奏。

## Shapes

形狀語言來自植物標籤與交換票據：小圓角、清楚邊框、局部切齊。圓角上限為 8px，主要例外是小型狀態籤以 4px 保持像實體標籤的邊界感。

## Components

按鈕必須清楚區分主要交換行動與次要閱讀行動。狀態籤需同時用文字說明，不只靠顏色。表單錯誤、成功、空狀態都以本頁文字回饋；成功只代表本機示範狀態，不暗示遠端送出或真實媒合完成。每頁的 root token、導覽、焦點樣式、按鈕、列表、表單與卡片基礎規則必須一致。

## Do's and Don'ts

- Do 使用繁體中文、真實交換語境和清楚的「不販售」規範。
- Do 讓植物照護條件、交換地點、交換方式在列表中可掃描。
- Do 在手機優先露出主要行動、交換狀態和社區邊界。
- Don't 使用價格、購物車、付款、折扣、促銷或成交語言。
- Don't 以外部圖片、假會員數、假評價或未知授權素材製造社群證據。
- Don't 為不同頁面重定義顏色、字體、圓角或按鈕語言。
