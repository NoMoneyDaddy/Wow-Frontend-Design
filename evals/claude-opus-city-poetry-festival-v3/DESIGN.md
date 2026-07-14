---
version: alpha
name: 城詩祭 City Poetry Festival
description: An editorial Traditional Chinese exploration site for a city poetry festival, drawn from letterpress typography and program-folder rhythm.
colors:
  primary: "#B4362C"
  on-primary: "#FBF7EE"
  ink: "#20201C"
  paper: "#FBF7EE"
  surface: "#F2ECDD"
  on-surface: "#20201C"
  muted: "#6B675C"
  border: "#D7CFBC"
  status-open: "#3D5A45"
  status-few: "#8A5A1A"
  status-full: "#7A736A"
typography:
  masthead:
    fontFamily: "\"Songti TC\", \"Noto Serif TC\", \"Source Han Serif TC\", serif"
    fontSize: 64px
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: 0.04em
  headline:
    fontFamily: "\"Songti TC\", \"Noto Serif TC\", \"Source Han Serif TC\", serif"
    fontSize: 30px
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: 0.01em
  body:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 17px
    fontWeight: 400
    lineHeight: 1.7
  meta:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.5
    letterSpacing: 0.02em
  vertical:
    fontFamily: "\"Songti TC\", \"Noto Serif TC\", \"Source Han Serif TC\", serif"
    fontSize: 22px
    fontWeight: 500
    lineHeight: 1.9
    letterSpacing: 0.12em
rounded:
  none: 0px
  sm: 2px
spacing:
  xs: 6px
  sm: 12px
  md: 20px
  lg: 36px
components:
  nav-link:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.meta}"
    rounded: "{rounded.none}"
    padding: "{spacing.sm}"
  action-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.meta}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  record-surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
  status-tag:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.status-open}"
    typography: "{typography.meta}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
---

# 城詩祭 City Poetry Festival

## Overview

城詩祭是一個以繁體中文為主的城市詩祭探索網站，讀者透過手機或桌機瀏覽詩人、場地、日期與活動摘要。產品真實：詩祭把街區當成刊物、把節目當成篇章。視覺取材城市詩刊、鉛字排印與節目摺頁的留白節奏，內容先行，呈現明確的編輯判斷，而非營運儀表板或通用行銷模板。

個性：沉靜、書卷、帶油墨溫度；絕不喧鬧或科技冷感。密度採「疏—密交替」：寬裕的提案段落後接密實的活動索引。

## Colors

- `paper`：主畫布，米白紙感，承載長篇閱讀。
- `surface`：活動索引與直排區的次級紙色，用微弱色差分層，不靠陰影。
- `ink`：主要文字與標題；在 `paper` 上對比約 12:1。
- `muted`：次要中繼資料（場地、時間），不與主文爭焦。
- `primary`（朱紅）：僅出現於可行動處與品牌印記，如報名連結、當前導覽、篇章編號；朱紅代表「可行動 / 現場」。
- `status-open`／`status-few`／`status-full`：名額狀態，永遠搭配文字標籤，非僅靠顏色。
- `border`：細分隔線，取代卡片邊框與陰影。

朱紅絕不用於大面積背景或裝飾漸層。

## Typography

- `masthead`：報頭與節慶識別，宋體帶正字距，表達刊物氣質。
- `headline`：活動與區段標題。
- `body`：長段閱讀，行高 1.7 讓中文呼吸。
- `meta`：日期、場地、狀態、導覽等功能性文字。
- `vertical`：直式排版區專用，字身直立、字距放寬，供直排閱讀。

不對中文段落施加正字距；字距僅用於報頭與直排的刻意處理。避免以細小英文大寫作為階層裝置。長字串（URL／代碼）才使用 `overflow-wrap`，一般中文維持自然斷行。

## Layout

Desktop：以 12 欄基準的編輯式版面。報頭橫跨全寬；提案段落限制在約 60 個中文字的閱讀寬度；直排區與橫排索引並置，明確呈現直橫關係。活動索引為編輯式列表，非等重卡牆，交替左右對齊與節奏。

Mobile：單一內容流，報頭縮短、導覽收進面板。直排區在窄螢幕轉為較短的水平等價構圖（橫向書名頁節奏），不把長直排硬塞進窄螢幕。索引改為聚焦式垂直序列，狀態與日期優先，次要文案延後。

間距採 `xs`–`lg` 語意刻度，配合 `clamp()` 流動。

## Elevation & Depth

以紙色分層、細邊界線與留白表達層次，全站不使用投影。直排區以微弱 `surface` 色塊與細分隔線與橫排區區隔。焦點樣式為朱紅外框，於任何背景皆可見。

## Shapes

近乎無圓角（`none`／`sm`），呼應鉛字方塊與摺頁的直角。分隔用線，不用外框膠囊。狀態標籤允許 2px 微圓角作為唯一例外。

## Components

- `nav-link`：全域導覽項目，當前項以朱紅標示並加下劃線，非僅顏色。
- `action-primary`：報名／詳情連結，朱紅底、紙色字，短標籤保證單行不換行。
- `record-surface`：每個活動容器（`data-eval="record"`），次級紙色、細分隔線。
- `status-tag`：名額狀態，顏色加文字雙重編碼。hover／current 等變體以另行命名項目表達，邊框與 mobile 轉換記於本文。

短按鈕、日期、場地與狀態文字以 `white-space: nowrap` 與足夠觸控尺寸避免換行、裁切或溢位。

## Do's and Don'ts

- Do 讓內容先行，索引呈現編輯判斷與疏密節奏。
- Do 直排區保持中文字直立，桌機呈現直橫關係，手機轉為水平等價。
- Do 名額狀態同時用顏色與文字。
- Don't 使用 KPI 牆、SaaS 側欄、pricing、假海報空框或裝飾性卡牆。
- Don't 以整個容器旋轉冒充直排。
- Don't 在客戶文案中暴露斷點策略或評估語言。
