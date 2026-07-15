---
version: alpha
name: 海岸口述歷史
description: 以潮汐刻度、田野筆記與檔案紙建立的繁體中文三頁典藏視覺契約。
colors:
  canvas: "#F4EEE3"
  on-canvas: "#1F2A31"
  surface: "#FFF9F0"
  on-surface: "#1F2A31"
  muted-surface: "#E7DDCB"
  on-muted-surface: "#4F5D66"
  primary: "#184E57"
  on-primary: "#F8F3E8"
typography:
  display:
    fontFamily: '"Iowan Old Style", "Baskerville", "Songti TC", "Noto Serif TC", serif'
    fontSize: 52px
    fontWeight: 650
    lineHeight: 1.04
    letterSpacing: "-0.02em"
  headline:
    fontFamily: '"Iowan Old Style", "Baskerville", "Songti TC", "Noto Serif TC", serif'
    fontSize: 28px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  body:
    fontFamily: '"PingFang TC", "Noto Sans TC", "Microsoft JhengHei", system-ui, sans-serif'
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.8
    letterSpacing: "0em"
  fine:
    fontFamily: '"PingFang TC", "Noto Sans TC", "Microsoft JhengHei", system-ui, sans-serif'
    fontSize: 13px
    fontWeight: 500
    lineHeight: 1.5
    letterSpacing: "0.02em"
rounded:
  sm: "10px"
  md: "16px"
  lg: "24px"
  pill: "999px"
spacing:
  xs: "6px"
  sm: "10px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  xxl: "48px"
components:
  page-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-canvas}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xl}"
  masthead:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  hero-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xl}"
  record-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  media-fallback:
    backgroundColor: "{colors.muted-surface}"
    textColor: "{colors.on-muted-surface}"
    typography: "{typography.fine}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.fine}"
    rounded: "{rounded.pill}"
    padding: "{spacing.md}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.fine}"
    rounded: "{rounded.pill}"
    padding: "{spacing.md}"
  footnote:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-canvas}"
    typography: "{typography.fine}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
---

# 海岸口述歷史

## Overview

這是一個以繁體中文閱讀為中心的三頁典藏站：`index.html` 提供入口與閱讀順序，`archive.html` 讓人快速掃描口述整理條目，`story.html` 讓人進入長篇敘事與註解。整體語氣不是博物館式陳列，而是把潮汐刻度、田野筆記與檔案紙整理成能查、能讀、能回到前一頁的閱讀系統。

受眾是想快速找線索、確認年代、比對船名與地點的讀者。頁面優先保留清楚導覽、短路徑與可靠的文字密度，並用一條細小的潮汐刻度作為三頁共同的辨識點。這個刻度不是裝飾，而是定位工具：首頁看方向，典藏頁看序列，故事頁看段落節奏。

## Colors

色彩只負責三件事：紙面、墨色與行動。

- `canvas` 與 `surface` 是兩層紙感背景，讓頁面看起來像整理過的檔案，而不是空白容器。
- `on-canvas` 與 `on-surface` 承擔正文與標題的主要閱讀對比。
- `muted-surface` 與 `on-muted-surface` 只用在缺檔說明、補充註記與媒體替代區，避免它們與主要內容競爭。
- `primary` 與 `on-primary` 只用在可採取行動的按鈕與關鍵導覽。

色彩不承擔情緒保證；它的角色是清楚分層與清楚指向。紙面偏暖，墨色偏冷，讓「檔案」與「潮線」同時成立，但不把任何色相當作可信度或感受的證明。

## Typography

展示標題使用襯線語氣，讓長篇口述具有節目單與編目頁的重量。內文使用穩定的無襯線中英混排堆疊，確保繁中長句、英文船名與年份都能在沒有外部字型時維持可讀性。

- `display` 只用在首頁主標與故事頁大標。
- `headline` 用在區塊標題與記錄名稱。
- `body` 是所有主要段落、列表與導覽文字的預設。
- `fine` 用在標籤、註腳、元資料與按鈕文字。

正文維持橫書，避免把內容壓成直欄。若需要短直書標籤，只能作為輔助識別，且在手機版必須改回水平可讀形式。

## Layout

三頁共用同一個頁首、導覽與紙面殼層，差別在於內容密度與閱讀路徑。

| 區域 | 桌面角色 | 手機對應 | 順序 | 互動 | 延後或移除 |
| --- | --- | --- | --- | --- | --- |
| 全站頁首 | 固定識別與互相導頁 | 緊湊標頭與單列導覽 | 1 | 直接點選 | 無 |
| 首頁英雄區 | 方向、概念與主行動 | 首屏摘要加一個潮汐刻度 | 2 | 直接進入典藏或故事 | 過大的封面感 |
| 典藏索引 | 可掃描的條目列表 | 單欄順序列表 | 2 | 點入條目查看線索 | 任何假圖片或空白容器 |
| 長篇故事 | 連續閱讀與註解側欄 | 單欄正文，註解順排 | 2 | 滾動與回到索引 | 只在桌面才可見的資訊 |

內容寬度控制在適合繁中長文的範圍，桌面以兩欄或單欄加側註為主，手機版改為單欄、較短標題與較低密度，避免首屏被大標題和裝飾區塊吞掉。

## Elevation & Depth

層次主要靠紙面差異、細邊線與少量陰影，而不是玻璃、霓虹或厚重浮層。首頁與典藏卡片可略微抬起，註腳與缺檔區則保持更安靜的平面，讓主要閱讀面先被看見。

## Shapes

形狀語言是圓角文件夾與清楚的框線。按鈕採膠囊形，卡片採中等圓角，頁面殼層採較大的圓角。沒有任何一個元件需要銳利裝飾或任意異形；唯一的節奏變化來自潮汐刻度與記錄序列。

## Components

- `page-shell` 是三頁共同的外殼，負責紙面背景、內距與主閱讀色。
- `masthead` 是頁首與導覽的共同樣式，提供站名、頁面識別與互導連結。
- `hero-panel` 用於首頁的方向區，承載一句概念、兩個主要行動與潮汐刻度。
- `record-card` 用於典藏條目與故事中的補充卡片，維持相同的紙面語法。
- `media-fallback` 只在沒有可信照片或影像時使用，明確說明缺檔，不冒充圖片。
- `button-primary` 與 `button-secondary` 分別對應主要與次要導覽。
- `footnote` 用於故事頁註解與出處說明。

所有頁面都保留同一組 root tokens 與相同的 header/nav shell。若某個區塊在手機上改成另一種排列方式，必須保留同一份內容與相同的可達目的地，不可以用新的、無關的替代內容來湊出響應式結果。

## Do's and Don'ts

- Do 讓首頁先說明閱讀順序，再讓使用者進入索引或故事。
- Do 讓典藏頁像條目表，不要把它做成五顏六色的宣傳牆。
- Do 讓故事頁維持長文節奏，並把媒體缺席說清楚。
- Do 在手機上重新排列內容與導航密度，而不是只是把桌面版疊成一列。
- Don't 用 CSS 圖形冒充歷史照片或實物影像。
- Don't 讓標題把首屏全部占滿，讓閱讀者還沒看到內容就先被版面壓住。
- Don't 分裂出另一套頁面樣式來假裝同一個系統。
