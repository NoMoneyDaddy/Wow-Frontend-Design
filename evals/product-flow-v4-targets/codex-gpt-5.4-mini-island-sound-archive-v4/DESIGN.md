---
version: alpha
name: 島嶼聲音檔案館
description: 以繁體中文建立一個內容先行的島嶼聲音檔案探索網站，讓讀者在桌機讀脈絡、在手機快速找到一筆錄音。
colors:
  canvas: "#F5EFE8"
  surface: "#FFF9F1"
  ink: "#1F2629"
  muted: "#566168"
  primary: "#8A4E34"
  on-primary: "#FFF9F1"
typography:
  headline:
    fontFamily: "\"Noto Sans TC\", \"PingFang TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 2.375rem
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "0em"
  title:
    fontFamily: "\"Noto Sans TC\", \"PingFang TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 1.375rem
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0em"
  body:
    fontFamily: "\"Noto Sans TC\", \"PingFang TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.7
    letterSpacing: "0em"
  ui:
    fontFamily: "\"Noto Sans TC\", \"PingFang TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 0.9375rem
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "0em"
  vertical:
    fontFamily: "\"Noto Sans TC\", \"PingFang TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 1rem
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "0em"
spacing:
  xs: 0.375rem
  sm: 0.625rem
  md: 1rem
  lg: 1.5rem
  xl: 2rem
rounded:
  md: 0.875rem
  lg: 1.25rem
  pill: 999px
components:
  page-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
  archive-header:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.title}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  hero-banner:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.headline}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xl}"
  record-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  action-button:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "{spacing.sm}"
  chip:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.muted}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "{spacing.xs}"
  vertical-ribbon:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    typography: "{typography.vertical}"
    rounded: "{rounded.md}"
    padding: "{spacing.sm}"
---

# 島嶼聲音檔案館

## Overview

這是一個面向一般讀者與研究者的繁體中文聲音檔案探索頁。內容比裝飾更重要，閱讀比演示更重要；桌機可同時看見索引、脈絡與摘錄，手機則把同一批資訊濃縮成可快速掃描的直向清單與就地展開的細節。

## Colors

- `canvas` 是整體頁底，讓檔案紙感先於裝飾出現。
- `surface` 是卡片、標籤與欄位的承載面，和頁底保持輕微層次。
- `ink` 是主要文字與關鍵資訊，只要需要被可靠讀取，就用它。
- `muted` 是次要說明、時間、地點與補充欄位，不能拿來承擔主要訊息。
- `primary` 只給可操作的重點，例如選取、播放預覽或前往詳情。
- `on-primary` 只搭配 `primary` 使用，維持按鈕與標籤的可讀性。

色彩規則很簡單：中性色負責大部分閱讀，強色只在「可以採取動作」或「需要定位目前選取」時出現。這讓頁面保有檔案氣質，不會滑向一般行銷模板。

## Typography

- `headline` 用於頁首與主標，提供清楚但不浮誇的編輯聲量。
- `title` 用於錄音題名與分區標題，承擔內容辨識。
- `body` 用於摘要、節錄與採集說明，是整個頁面的閱讀基準。
- `ui` 用於按鈕、篩選、年代與權利狀態，讓功能文字比正文更精煉。
- `vertical` 用於直排索引與地名欄，作為桌機上的編輯語法。

繁中內容保留自然換行，不以英文字母式的縮排與追蹤去破壞中文節奏。長題名、地名與權利說明要能延展，不靠截斷假裝整齊。

## Layout

頁面採一個清楚的閱讀脊柱：上方是檔案身份與探索入口，中段是錄音索引，右側是當前選取錄音的詳情。桌機利用雙欄與直排區域建立編輯構圖；手機改為單欄順序，先看見品牌、脈絡與最近的一筆錄音，再往下掃完整清單與細節。

內容寬度維持可讀，而不是把所有區塊都壓成同寬卡片。記錄卡、詳情面與直排標籤使用不同的密度，讓讀者知道哪些是索引、哪些是正文、哪些是採集線索。

## Elevation & Depth

深度不靠厚重陰影，而靠紙面、邊界與排版層次。頁底像檔案紙，記錄卡像抽出的檔案條目，詳情面像打開的夾層。只有選取狀態與主要動作使用更強的對比。

## Shapes

形狀語彙偏向標籤、檔案盒與印記：圓角要克制，邊框要像標籤貼合紙面，直條與章戳只在需要定位與索引時出現。不要把每個區塊都做成同一種圓角外框。

## Components

- 檔案頭部：顯示品牌、目前脈絡、探索狀態與主要動作。
- 頁面外殼：承載整體底色、閱讀寬度與穩定的文字基準。
- 英雄橫幅：承載頁首主標與編輯聲量，讓檔案身份先被讀到。
- 錄音卡：承載題名、講者、語言、年代、長度、主題、授權與可聆聽狀態。
- 詳情面：顯示逐字節錄、採集資訊與補充脈絡，作為讀者停留的地方。
- 篩選膠囊：快速定位島嶼、主題與語言，不改變內容本身的結構。
- 直排索引：只在桌機作為編輯性標記，手機改成水平副標。
- 主要按鈕：僅用於切換選取、前往詳情或嘗試預覽，不做空泛宣傳。

## Do's and Don'ts

- Do 讓桌機與手機共享同一批檔案資料與選取狀態。
- Do 讓直排成為有意義的索引，而不是把容器整個旋轉來假裝直排。
- Do 讓不可播放的預覽誠實地標示為不可播放。
- Don't 把這個頁面做成儀表板、串流首頁或通用行銷版型。
