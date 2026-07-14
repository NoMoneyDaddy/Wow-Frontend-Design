---
version: alpha
name: "城市詩祭探索網站設計系統"
description: "繁體中文城市詩祭探索網站的單頁編輯式視覺契約，強調活動索引、詩人與場地比較、直排樣區與手機重排。"
colors:
  canvas: "#F4EDE4"
  surface: "#FFF8F1"
  ink: "#201713"
  muted: "#6F6258"
  primary: "#8A412A"
  on-primary: "#FFF7EF"
  success: "#21664D"
  warning: "#8D6218"
  danger: "#A04242"
typography:
  display:
    fontFamily: "\"Noto Serif TC\", \"Source Han Serif TC\", \"Songti TC\", serif"
    fontSize: 52px
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "-0.02em"
    fontFeature: "\"kern\" 1, \"liga\" 1"
  reading:
    fontFamily: "\"Noto Sans TC\", \"PingFang TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 17px
    fontWeight: 400
    lineHeight: 1.75
    letterSpacing: "0"
    fontFeature: "\"kern\" 1, \"liga\" 1"
  functional:
    fontFamily: "\"Noto Sans TC\", \"PingFang TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "0.01em"
    fontFeature: "\"kern\" 1, \"liga\" 1"
  numeric:
    fontFamily: "\"Noto Sans TC\", \"PingFang TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 15px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0"
    fontFeature: "\"kern\" 1, \"tnum\" 1"
spacing:
  page: 1.5rem
  section: 2rem
  cluster: 1.125rem
  tight: 0.625rem
  medium: 1rem
  loose: 1.5rem
rounded:
  sm: 0.5rem
  md: 0.875rem
  lg: 1.375rem
components:
  page-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.reading}"
    padding: "{spacing.page}"
  global-nav:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.functional}"
    padding: "{spacing.tight}"
  nav-link:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.muted}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.tight}"
  nav-link-current:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.tight}"
  action-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.functional}"
    rounded: "{rounded.md}"
    padding: "{spacing.medium}"
  action-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.functional}"
    rounded: "{rounded.md}"
    padding: "{spacing.medium}"
  lead-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.reading}"
    rounded: "{rounded.lg}"
    padding: "{spacing.loose}"
  record-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.reading}"
    rounded: "{rounded.md}"
    padding: "{spacing.cluster}"
  record-card-featured:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.reading}"
    rounded: "{rounded.lg}"
    padding: "{spacing.loose}"
  meta-line:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.muted}"
    typography: "{typography.numeric}"
    rounded: "{rounded.sm}"
    padding: "{spacing.tight}"
  status-open:
    backgroundColor: "{colors.success}"
    textColor: "{colors.on-primary}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.tight}"
  status-limited:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.on-primary}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.tight}"
  status-full:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-primary}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.tight}"
  vertical-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.display}"
    rounded: "{rounded.lg}"
    padding: "{spacing.loose}"
---

## Overview

這是一套給「城市詩祭探索網站」使用的單頁編輯式視覺契約。主要受眾是一般讀者，常在手機上快速瀏覽，也會在桌機上比較詩人、場地、日期與名額狀態。

視覺語氣走城市詩刊、節目摺頁與鉛字排印的路線。內容優先，裝飾退後。整體屬於 `Archive and index`，輔以 `Editorial narrative` 的段落節奏。

## Colors

`canvas` 是整頁紙感底色，只用在大面積背景。

`surface` 是內容承載面，用於導覽、精選區與活動條目。

`ink` 是主要閱讀文字與標題色。

`muted` 是次級說明、導覽非當前項與補充欄位。

`primary` 是唯一的行動與當前狀態強調色，只在可點擊或需要辨識的地方出現。

`on-primary` 只搭配 `primary`、`success`、`warning`、`danger` 等強色使用，確保標籤可讀。

`success`、`warning`、`danger` 只表示名額與入場狀態，不拿來裝飾內容。

色彩心理假設標記為 `REJECTED`。暖色不保證親近感，只作為可行動與狀態分化的語義訊號。

## Typography

`display` 用在主標、直排樣區與少量節奏性強的標題，採襯線字感。

`reading` 用在段落、摘要與活動說明，採無襯線、較高行距，確保長文可讀。

`functional` 用在導覽、按鈕、標籤與欄位名，密度較高但不追求壓縮。

`numeric` 用在日期、席次與名額資訊，固定數字節奏，便於掃讀比較。

繁中內容維持自然換行，不用機械式大寫字標當唯一層級手段。長標題與日期在 200% 文字縮放時仍需保留完整意思。

## Layout

桌機採雙軌編排：左側是內容導讀與活動索引，右側是直排樣區與編輯備註。活動條目以列表/索引方式閱讀，不做 KPI 牆或同權重卡片牆。

手機改成單欄順序：

1. 導覽與總覽。
2. 編輯導讀。
3. 活動索引。
4. 直排樣區改為較短的水平構圖。
5. 補充說明。

直排區在桌機與橫排索引形成對照；手機不硬塞長直排，改成短版橫向節目條。

## Elevation & Depth

以平面與薄邊界為主，只讓精選區比索引區稍微抬起。深度不靠厚陰影，而靠底色、留白、規則線與排序。

## Shapes

形狀語言是柔角矩形、細線與窄長標籤。圓角層級少而穩定，避免每個元件都長得一樣卻又沒有角色差異。

## Components

`global-nav` 提供站內入口與當前頁定位，桌機與手機都維持同一組連結。

`action-primary` 與 `action-secondary` 是導讀用按鈕，不做多重競爭的黏性操作。

`lead-panel` 承載編輯導言與精選說明，避免把關鍵內容切成裝飾卡。

`record-card` 與 `record-card-featured` 是活動條目，欄位順序固定，方便比較詩人、場地、日期與席次。

`status-open`、`status-limited`、`status-full` 只表示名額與入場狀態，不重複表達其他意思。

`vertical-panel` 是整個頁面唯一真正依賴 `writing-mode: vertical-rl` 的區域。它必須在桌機上可直接閱讀，且在手機上重組為短版橫向區塊。

## Do's and Don'ts

- Do 保持一個活動對應一個 `record`，桌機與手機共用同一份內容來源。
- Do 讓名額、日期、場地、狀態都能直接掃讀，不要藏進裝飾性圖塊。
- Do 讓直排樣區服務城市詩刊感，不要拿來炫技或塞進狹窄版面。
- Don't 重新長成 dashboard、SaaS 側欄、pricing 區或通用行銷模板。
- Don't 用假海報框、無意義漸層或重複卡片牆取代活動索引。
- Don't 把手機版做成只是把桌機往下堆。
