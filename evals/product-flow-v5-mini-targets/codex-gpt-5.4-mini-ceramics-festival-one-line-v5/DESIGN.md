---
version: alpha
name: 秋陶祭
description: 秋日陶藝祭的共用視覺契約，讓作品、節目與造訪資訊維持同一種溫度與節奏。
colors:
  primary: "#7B3F19"
  onPrimary: "#FFF8EF"
  surface: "#FBF4EA"
  onSurface: "#231815"
  surfaceRaised: "#F0E2D1"
  onSurfaceRaised: "#4A392C"
  accent: "#44663E"
  onAccent: "#F6FBF4"
  success: "#2E5E44"
  onSuccess: "#F2FBF6"
  warning: "#8A4F12"
  onWarning: "#FFF8ED"
  danger: "#8A392A"
  onDanger: "#FFF6F3"
typography:
  display:
    fontFamily: "\"Noto Serif TC\", \"Iowan Old Style\", Georgia, serif"
    fontSize: 3rem
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "0em"
  headline:
    fontFamily: "\"Noto Serif TC\", \"Iowan Old Style\", Georgia, serif"
    fontSize: 1.75rem
    fontWeight: 700
    lineHeight: 1.15
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
    lineHeight: 1.3
    letterSpacing: "0em"
  mono:
    fontFamily: "\"SFMono-Regular\", \"Cascadia Mono\", \"IBM Plex Mono\", monospace"
    fontSize: 0.9375rem
    fontWeight: 500
    lineHeight: 1.5
    letterSpacing: "0em"
rounded:
  xs: 6px
  sm: 12px
  md: 20px
  lg: 30px
spacing:
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
components:
  baseSurface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.onSurface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  raisedPanel:
    backgroundColor: "{colors.surfaceRaised}"
    textColor: "{colors.onSurfaceRaised}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xl}"
  buttonPrimary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.onPrimary}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  buttonSecondary:
    backgroundColor: "{colors.surfaceRaised}"
    textColor: "{colors.onSurfaceRaised}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  badgeAccent:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.onAccent}"
    typography: "{typography.ui}"
    rounded: "{rounded.xs}"
    padding: "{spacing.sm}"
  badgeSuccess:
    backgroundColor: "{colors.success}"
    textColor: "{colors.onSuccess}"
    typography: "{typography.ui}"
    rounded: "{rounded.xs}"
    padding: "{spacing.sm}"
  badgeWarning:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.onWarning}"
    typography: "{typography.ui}"
    rounded: "{rounded.xs}"
    padding: "{spacing.sm}"
  badgeDanger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.onDanger}"
    typography: "{typography.ui}"
    rounded: "{rounded.xs}"
    padding: "{spacing.sm}"
---

# 秋陶祭

## Overview

秋陶祭是一個以秋日、手感與火候為核心的陶藝祭網站。它的任務不是把資訊堆滿，而是讓訪客很快看懂「值得看什麼、何時來、出發前要準備什麼」。

整體語氣要安靜、溫暖、可信，帶著作品剛出窯時的乾淨與餘溫。避免科技產品式的發光、雜訊與誇張噱頭；讓材質、節奏與留白自己說話。

## Colors

- `primary` 是爐火與泥土的主動色，只能用在主要行動、關鍵標記與需要被立即注意的節點。
- `surface` 與 `surfaceRaised` 是紙感底色，分別承接一般內容與稍微靠前的內容。
- `accent` 是植物與器皿邊緣的輔助色，用來標示分流、分類與次要強調。
- `success`、`warning`、`danger` 只處理結果與狀態，避免把裝飾誤寫成行動。
- 藍紫霓虹、玻璃感或高飽和漸層不屬於這個系統；秋天的色彩應該偏向土、茶、葉與窯火。

## Typography

展示標題使用襯線體，讓節慶感更像刊物與展冊；正文與介面使用無襯線體，讓節目、路線與提醒能在手機上快速掃讀。等寬字體只用在時間、編號與路線標籤。

中文內容維持正常字距，不做機械式加字距或全大寫處理。長標題與多行說明要能自然換行，避免為了版面而壓縮內容。

## Layout

頁面寬度採中心對齊的閱讀欄與較寬的活動欄雙層結構。主內容維持可讀的行長，節目與造訪資訊則允許更寬的對照區，方便掃描時間、類別與交通方式。

| Region | Desktop role | Mobile equivalent | Order | Interaction | Defer/remove |
| --- | --- | --- | --- | --- | --- |
| 開場區 | 大圖文並列，先建立節慶感再交代行動 | 文字先行，作品圓盤下移到次屏 | 1 | 靜態閱讀，主按鈕直達節目與造訪 | 次要說明收斂為短句 |
| 節目清單 | 右欄補充，幫助比較場次與路線 | 先顯示可篩選場次，再顯示補充建議 | 2 | 篩選、掃讀、點選細節 | 次要備註延後顯示 |
| 造訪工具 | 交通方式並列，方便比較 | 改成單一方式切換，減少同屏資訊 | 3 | 點選切換，查看對應準備清單 | 不必要的旁註折疊 |

## Elevation & Depth

深度主要靠色面差、邊框與輕微陰影，不靠厚重玻璃或滿版光暈。內容本身要像器物一樣有層次，而不是每個區塊都像浮起來的卡片。

## Shapes

形狀語言來自陶輪、器緣與窯口：圓角要柔，但不是泡泡感。按鈕保留清楚的邊界，內容卡片保留穩定的角度，讓整體看起來像手工器物的整理，而不是任意圓角堆疊。

## Components

- `baseSurface` 承接說明段、導覽與一般文字。
- `raisedPanel` 承接比較、卡片與補充資訊。
- `buttonPrimary` 只給最重要的行動，例如前往節目或規劃造訪。
- `buttonSecondary` 用於次要導覽與切換。
- `badgeAccent`、`badgeSuccess`、`badgeWarning`、`badgeDanger` 分別處理類別與狀態。
- 節目頁使用可篩選清單，造訪頁使用方式切換，首頁使用重點卡與火候圓盤。這些元件共享同一套色面與圓角，不另開第二系統。

## Do's and Don'ts

- Do 讓每個路由都有明確用途：認識活動、查看節目、準備出發。
- Do 用真實可行的說明文字，保留路線、時間與提醒的可更新性。
- Don't 編造售罄數字、票價、得獎紀錄或現場保證。
- Don't 把整站做成通用 SaaS 卡片牆，也不要用節慶裝飾掩蓋資訊結構。
