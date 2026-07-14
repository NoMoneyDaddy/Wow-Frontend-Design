---
version: alpha
name: 巷口書架設計系統
description: 獨立書局網站的視覺契約，以書脊索引、安靜閱讀與清楚選書為核心。
colors:
  primary: "#4B241A"
  on-primary: "#FFF8EF"
  surface: "#FFF8EF"
  on-surface: "#241815"
typography:
  display:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif"
    fontSize: 44px
    fontWeight: 750
    lineHeight: 1.12
    letterSpacing: 0em
  body:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.7
    letterSpacing: 0em
rounded:
  small: 6px
  medium: 8px
spacing:
  compact: 8px
  regular: 16px
components:
  primary-action:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.small}"
    padding: "{spacing.regular}"
  reading-surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.medium}"
    padding: "{spacing.regular}"
---

# 巷口書架設計系統

## Overview

BRIEF: 幫我做書局網頁。

這是給社區讀者、送禮選書者與常來翻架的讀者使用的三頁書局網站。核心任務是快速理解書局氣質、瀏覽書目、查看一本書的選書理由。概念是「一本書從書脊被抽出來」，用可掃描的索引、安靜紙面與明確行動，讓讀者覺得書局有整理、有溫度，但不裝飾過度。

## Colors

`primary` 是深褐色，只用在主要行動、目前頁面與重點索引線，代表書脊和木架。`surface` 是紙張底色，承載長文與書目資訊。`on-surface` 是主要文字。介面避免多彩裝飾；分類可用細線、標籤文字與位置，不單靠顏色傳達狀態。

## Typography

`display` 用於頁面主標與關鍵書名，字重較高但不使用負字距。`body` 用於導覽、段落、書目摘要與按鈕。文件以繁體中文為主，設定寬鬆行高，長標題允許自然換行；英文書名、ISBN 與路徑保留原文。

## Layout

桌面使用窄閱讀欄與寬書架區交替：首頁先給書局定位，再展示今日選書與到店資訊；目錄頁以可掃描清單和分類欄呈現；單書頁以書名、選書理由、購買資訊和相近閱讀形成決策路徑。手機版改成優先讀取：導覽壓成短列，首屏保留主標與主要行動，書目由多欄索引改為縱向清單，側欄資訊移到主內容之後。

## Elevation & Depth

深度主要靠紙面色、細邊線、留白和書脊條紋建立。陰影很少使用，只能在可互動項目聚焦或 hover 時提供輕微層級。沒有玻璃模糊、發光或大型背景特效。

## Shapes

半徑小而克制，呼應書角與標籤貼紙。大區塊不包成卡片；卡片只用於單本書、營業資訊或可點擊項目。索引線、書脊條和分隔線保持方正，讓書架感比圓角更強。

## Components

主要按鈕使用 `primary-action`。閱讀型區塊使用 `reading-surface`，但頁面不得把所有內容都塞進同一種卡片。書目項目要同時有分類、書名、作者、摘要與可操作連結。焦點狀態使用清楚外框；hover 只加強邊線或位移，不隱藏必要資訊。

## Do's and Don'ts

- Do 讓書脊索引、分類線與文字節奏貫穿三頁。
- Do 在手機上縮短決策路徑，把主要行動放在標題附近。
- Do 用真實但未宣稱庫存的示範書目文案；未知事實不可寫成保證。
- Don't 使用外部圖片、字體、腳本或未授權素材。
- Don't 用簡體中文、空泛科技感、紫藍漸層或浮動儀表板。
