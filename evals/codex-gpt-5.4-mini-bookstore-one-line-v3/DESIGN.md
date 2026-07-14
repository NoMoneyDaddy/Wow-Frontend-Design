---
version: alpha
name: 藏頁書局
description: 以紙感編目、暖色行動與清楚的書目層級，支撐書店瀏覽、比較與單本決策。
colors:
  primary: "#8A4B2A"
  on-primary: "#FFF7EF"
  surface: "#FBF7F2"
  surface-soft: "#F0E6D8"
  on-surface: "#241B16"
  muted: "#6E6258"
  success: "#2E6A4A"
  danger: "#A5483B"
typography:
  display:
    fontFamily: '"Iowan Old Style", "Songti TC", "Noto Serif TC", "Times New Roman", serif'
    fontSize: 3.25rem
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  title:
    fontFamily: '"Iowan Old Style", "Songti TC", "Noto Serif TC", "Times New Roman", serif'
    fontSize: 1.75rem
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  reading:
    fontFamily: '"PingFang TC", "Noto Sans TC", "Microsoft JhengHei", -apple-system, BlinkMacSystemFont, sans-serif'
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.7
    letterSpacing: "0"
  ui:
    fontFamily: '"PingFang TC", "Noto Sans TC", "Microsoft JhengHei", -apple-system, BlinkMacSystemFont, sans-serif'
    fontSize: 0.9375rem
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "0.01em"
  numeric:
    fontFamily: '"SFMono-Regular", "Menlo", "Consolas", monospace'
    fontSize: 0.9375rem
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0"
spacing:
  xs: 0.5rem
  sm: 0.875rem
  md: 1.25rem
  lg: 2rem
  xl: 3.5rem
rounded:
  sm: 0.5rem
  md: 1rem
  lg: 1.5rem
  pill: 999px
components:
  page-shell:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.reading}"
    padding: "{spacing.lg}"
  panel:
    backgroundColor: "{colors.surface-soft}"
    textColor: "{colors.on-surface}"
    typography: "{typography.reading}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "{spacing.sm}"
    height: 2.75rem
  button-secondary:
    backgroundColor: "{colors.surface-soft}"
    textColor: "{colors.on-surface}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "{spacing.sm}"
    height: 2.75rem
  chip:
    backgroundColor: "{colors.surface-soft}"
    textColor: "{colors.on-surface}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "{spacing.xs}"
    height: 2.25rem
  status-success:
    backgroundColor: "{colors.success}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "{spacing.xs}"
    height: 2rem
  status-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "{spacing.xs}"
    height: 2rem
  book-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.reading}"
    rounded: "{rounded.lg}"
    padding: "{spacing.md}"
  book-cover:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.title}"
    rounded: "{rounded.md}"
    width: 8rem
    height: 11rem
---

# 藏頁書局

## Overview

藏頁書局面向想快速找到一本合適書的人。重點不是把商品堆滿，而是讓人先看懂類型、價格、現貨與內容深度，再進一步比較。

視覺性格是安靜、精準、帶一點紙本溫度。主視覺使用暖棕行動色，版面以紙色與淺層次承載內容，避免把每個區塊都做成同一種卡片。

## Colors

色彩只做三件事：建立閱讀層級、標出可行動元素、提示狀態。

- `primary` 是唯一強調色，用在主要按鈕、當前選取與書脊標記。
- `surface` 與 `surface-soft` 建立紙面與托盤差異，承載內容與比較。
- `on-surface` 與 `muted` 區分標題、正文、說明與中繼資料。
- `success` 與 `danger` 只表示可驗證的庫存與交易狀態，不拿來裝飾。

色彩不承擔心理效果的證明；這個系統不主張「某種顏色會讓人信任」，只主張它能清楚告訴使用者現在能做什麼、正在發生什麼。

## Typography

標題使用襯線字感，讓書名像被翻開；正文與介面文字使用無襯線，確保長篇資訊、價格與狀態可快速掃讀。

- `display` 用於首頁主標與單本書名。
- `title` 用於區段標頭與卡片標題。
- `reading` 用於說明、摘要與段落內容。
- `ui` 用於導覽、按鈕、篩選與標籤。
- `numeric` 用於價格、庫存與統計數字，維持對齊與比較性。

繁體中文文字保留自然斷行，不用機械式全大寫或過度字距。長書名、出版社名與 ISBN 需要能在小螢幕完整閱讀或合理折行。

## Layout

整體採單一內容寬度加上兩種密度帶：首頁偏敘事，目錄偏比較，書頁偏決策。

- 桌面版首頁用大標題、推薦區與分類導覽建立節奏。
- 桌面版目錄用可掃描列表與右側篩選輔助比較。
- 桌面版書頁用主資訊與購買動作並列，讓決策不必來回跳轉。

手機版不是把桌面疊成一欄而已。它會：

| 區域 | 桌面角色 | 手機對應 | 順序 | 互動 | 延後/移除 |
| --- | --- | --- | --- | --- | --- |
| 全域導覽 | 固定頂欄 | 緊湊導覽列 | 1 | 直接連結 | 次要說明 |
| 首頁主視覺 | 品牌與入口 | 壓縮為標題加精選書脊 | 2 | 點擊進站 | 大面積留白 |
| 分類比較 | 並列瀏覽 | 可滑動的分類帶 | 3 | 點選篩選 | 次要說法 |
| 目錄清單 | 多欄比較 | 單列書目卡 | 4 | 搜尋與篩選 | 右側輔助欄 |
| 書頁決策區 | 兩欄決策 | 先看封面與價格，再下滑看細節 | 5 | 立即購買/加入 | 非必要側欄 |

版面間距以閱讀節奏為準。首頁保留較大的段落間距，目錄縮緊以支撐掃描，書頁則在資訊與操作之間留出穩定呼吸。

## Elevation & Depth

不使用厚重陰影。層次主要靠紙色差、邊界、內距與重疊關係建立。

- `surface` 是頁面底。
- `surface-soft` 是托盤、卡片與工具列。
- 需要突出的區塊使用邊界更清楚、內距更深的方式，而不是不斷加陰影。

書封是本系統唯一明顯的色塊重心，因此它的飽和度可以高於介面本體。

## Shapes

形狀語言是圓角矩形加少量直線切面，像書頁邊與書脊標籤的結合。

- 主要容器使用中等圓角。
- 按鈕與標籤使用膠囊形，降低誤讀。
- 書封保留更明確的框感，讓它在大量文字中仍像實體物件。

## Components

共享元件如下：

- `page-shell`：整頁基底，統一紙色與正文。
- `panel`：承載摘要、分類與補充資訊。
- `button-primary`：主要動作，例如購買、加入書單或查看目錄。
- `button-secondary`：次要動作，例如回到首頁或改變篩選。
- `chip`：分類、條件與書籍屬性標籤。
- `book-card`：清單與推薦區的單本資訊容器。
- `book-cover`：封面區塊，用色塊與字標替代外部圖片。

狀態處理：

- hover 與 focus-visible 必須同時可辨識。
- 選取狀態以顏色與邊界同時表達。
- 缺貨、可預購與到貨中使用不同文案，不只靠顏色。

手機上，卡片不縮小到難讀，而是改成更短的層次、更少欄位與更明確的主次順序。

## Do's and Don'ts

- Do 用書名、作者、價格與供貨狀態說清楚這本書值不值得看。
- Do 保留同一套色彩與字級語法跨三個頁面。
- Do 讓手機先看到最重要的書、價格與行動。
- Don't 讓每個區塊都長得像同一種卡片。
- Don't 用外部圖片或網路資源當作必要內容。
- Don't 讓導覽、篩選與購買在小螢幕上依賴 hover。
