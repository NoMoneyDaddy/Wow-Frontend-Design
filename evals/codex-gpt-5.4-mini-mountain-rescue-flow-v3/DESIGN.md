---
version: alpha
name: 山域救援任務協調台
description: 繁體中文高密度任務工作台，供指揮員同時比較責任區、通訊狀態、急迫度、時限與隊伍負荷。
colors:
  primary: "#174B5D"
  on-primary: "#F6F5F0"
  canvas: "#F2F0EA"
  surface: "#FFFDFC"
  surface-strong: "#E7E1D7"
  text-primary: "#172026"
  text-secondary: "#56656D"
  border-subtle: "#D7D0C5"
  border-strong: "#A7B0B6"
  action: "#2E7A8B"
  on-action: "#F4FBFD"
  warning: "#C28B24"
  on-warning: "#1B1405"
  danger: "#C94E43"
  on-danger: "#FFF8F6"
  success: "#2E7A59"
  on-success: "#F2FBF5"
typography:
  display:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 2rem
    fontWeight: "700"
    lineHeight: 1.1
    letterSpacing: "-0.03em"
  heading:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 1.125rem
    fontWeight: "700"
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  body:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 1rem
    fontWeight: "400"
    lineHeight: 1.6
    letterSpacing: "0"
  ui:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 0.9375rem
    fontWeight: "600"
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  mono:
    fontFamily: "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"
    fontSize: 0.9375rem
    fontWeight: "600"
    lineHeight: 1.3
    letterSpacing: "0"
spacing:
  xs: 0.375rem
  sm: 0.625rem
  md: 1rem
  lg: 1.5rem
  xl: 2rem
rounded:
  sm: 0.5rem
  md: 0.875rem
  lg: 1.25rem
components:
  shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.text-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  topbar:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.display}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  nav-item:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-secondary}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  nav-item-active:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  stat-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  record-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  badge-priority-critical:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-danger}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  badge-priority-high:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.on-warning}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  badge-priority-normal:
    backgroundColor: "{colors.surface-strong}"
    textColor: "{colors.text-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  badge-status:
    backgroundColor: "{colors.surface-strong}"
    textColor: "{colors.text-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  badge-due-soon:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.on-warning}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  badge-due-overdue:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-danger}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  badge-due-steady:
    backgroundColor: "{colors.surface-strong}"
    textColor: "{colors.text-secondary}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  primary-action:
    backgroundColor: "{colors.action}"
    textColor: "{colors.on-action}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  secondary-action:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
---

# 山域救援任務協調台

## Overview

這是一個給山域救援指揮員使用的登入後工作台。重點不是展示，而是讓人快速掃讀、比較、分派與回收任務。

受眾需要同時盯住責任區、通訊品質、急迫度、時限與隊伍負荷，所以介面採取密集但有秩序的資料編排。

概念句：

> 山域救援任務的地形、通訊與期限，以指揮桌面的精準比較呈現，讓指揮員先抓住最危急的點，再快速分派隊伍。

本系統的作者性來自「地形索引帶」：以狹長的等高線摘要區把山域語彙帶進工作台，但不把它做成大型主視覺。

## Colors

色彩只做語意，不做裝飾。

- `canvas` 是整體背景，保持低刺激，讓高密度內容可長時間閱讀。
- `surface` 是主要承載面，用在面板、任務列與統計卡。
- `surface-strong` 是次級底面，用在分隔、膠囊標籤與低優先提示。
- `primary` 是系統主色，用在登入後的頂欄與目前導覽。
- `action` 只給可執行、確認後的操作與焦點導引。
- `warning` 只表示需要注意的急迫或接近時限。
- `danger` 只表示真實危險或已逾時。
- `success` 只表示已穩定、已接通或已回收。

急迫度、任務階段與時限彼此獨立，不共用同一種警示色。階段標籤以中性或冷調背景為主，不冒充風險警報。

## Typography

- `display` 用在頁面標題與最上層任務總覽。
- `heading` 用在工作區區塊標題。
- `body` 用在任務摘要與說明。
- `ui` 用在按鈕、標籤、導覽與膠囊狀態。
- `mono` 用在代碼、時間、通聯與座標類資料。

繁體中文內容維持自然行距與正常字距，不用英語式全大寫眉標。短數字與代碼保持等寬呈現，方便比對。

## Layout

桌面版以兩欄工作台處理比較：左側是任務隊列，右側是責任區、通聯與隊伍負荷的輔助資訊。摘要列橫跨上方，提供總量、逾時、弱訊號與待命數。

手機版不是把桌面縮小，而是重新編排成優先任務匣：先看摘要，再看任務，再看支援資訊。導覽壓成單列橫向捲動的膠囊列，避免狹窄寬度下失去可掃讀性。

| 區域 | 桌面角色 | 手機等效 | 順序 | 互動 | 延後 / 移除 |
| --- | --- | --- | --- | --- | --- |
| 頂欄與導覽 | 任務識別、快速跳轉 | 纖薄頂欄 + 橫向膠囊導覽 | 1 | 直接點選，維持單行可掃讀 | 不做大型選單 |
| 摘要列 | 總量與警示概覽 | 先讀的四格摘要 | 2 | 純展示，提供入場資訊 | 不取代任務列表 |
| 任務隊列 | 主要比較與分派 | 優先任務匣 | 3 | 卡片內直接讀取階段、時限、隊伍與通聯 | 不拆成兩份資料 |
| 支援資訊 | 責任區、通聯、隊伍負荷 | 次級支援區塊 | 4 | 展開閱讀，作為補充上下文 | 壓後，但不移除 |

## Elevation & Depth

層次主要靠底色、邊界與間距，不靠玻璃、霓虹或厚陰影。

任務列用左側語意邊條快速標記急迫度。統計卡與輔助卡只用輕微陰影與邊框，保持安靜。

## Shapes

形狀系統偏向地圖標籤與裝備牌：卡片有中等圓角，膠囊標籤較小且穩定，按鈕不使用過度圓滑的娛樂感輪廓。

短按鈕、狀態文字與通聯資料都以單行優先。必要時只允許任務摘要換行，不讓標籤和按鈕撐開版面。

## Components

- `shell` 承載整個登入後工作台，固定使用 `canvas` 背景與主文字色。
- `topbar` 是登入後的任務識別區，承載系統名稱、頁面標題與快速跳轉。
- `nav-item` 與 `nav-item-active` 用於主要導覽，桌面版可平鋪，手機版可壓縮為可橫向掃視的膠囊列。
- `stat-panel` 用於摘要數字，數量、標籤與說明必須一起出現。
- `record-card` 用於每筆任務；左側語意邊條可跟隨急迫度，但卡片本身保持可比較、可掃描。
- `badge-priority-*`、`badge-status` 與 `badge-due-*` 分別承擔急迫度、階段與時限，不可互相交換。
- `primary-action` 用於最重要的頁內跳轉。
- `secondary-action` 用於次要但仍屬產品流程的跳轉。

此頁的特殊區塊是地形索引帶。它只在這個產品語境中存在，目的是幫助指揮員把地形、責任區與通聯問題放進同一個比較框架。

## Do's and Don'ts

- Do 保持任務資料高密度但不擁擠。
- Do 讓繁體中文、數字、代碼與時間都能穩定掃讀。
- Do 讓危險色只在真危險與逾時時出現。
- Do 在手機上重排優先順序，不只是單欄堆疊。
- Don't 做大型主視覺、pricing、testimonial、玻璃擬態或霓虹漸層。
- Don't 讓急迫度、階段與時限共用同一種語意色。
- Don't 產生桌面與手機兩份獨立資料副本。
- Don't 把輔助摘要做成任務列表的替代品。
