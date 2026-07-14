---
version: alpha
name: 城市詩祭探索網站
description: 城市詩刊式活動索引，以直排卷首、鉛字節奏與清楚活動摘要支撐探索任務。
colors:
  primary: "#2B211B"
  on-primary: "#FFF8EC"
  canvas: "#F7F0E4"
  ink: "#241B16"
  muted: "#6B5B4D"
  action: "#8B2E1B"
  on-action: "#FFF8EC"
  notice: "#E8D8BE"
typography:
  display:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 44px
    fontWeight: 700
    lineHeight: 1.12
    letterSpacing: 0em
  body:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 17px
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: 0em
  label:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 14px
    fontWeight: 650
    lineHeight: 1.35
    letterSpacing: 0em
rounded:
  small: 6px
  medium: 8px
spacing:
  small: 8px
  medium: 16px
  large: 28px
components:
  page:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    padding: "{spacing.large}"
  button-primary:
    backgroundColor: "{colors.action}"
    textColor: "{colors.on-action}"
    typography: "{typography.label}"
    rounded: "{rounded.small}"
    padding: "{spacing.medium}"
  masthead:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.display}"
    rounded: "{rounded.medium}"
    padding: "{spacing.large}"
  event-record:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.small}"
    padding: "{spacing.medium}"
  status-note:
    backgroundColor: "{colors.notice}"
    textColor: "{colors.primary}"
    typography: "{typography.label}"
    rounded: "{rounded.small}"
    padding: "{spacing.small}"
  quiet-label:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.muted}"
    typography: "{typography.label}"
    padding: "{spacing.small}"
---

# 城市詩祭探索網站

## Overview

這是一個面向一般讀者的繁體中文 editorial 內容網站。視覺語氣取自城市詩刊、鉛字排印與節目摺頁；核心任務是快速理解詩祭主題，進入詩人、場地、日期與活動內容索引。介面避免假數據、排行榜牆與 SaaS 後台語言，讓活動摘要與編輯判斷成為第一層內容。

## Colors

`primary` 是鉛字深褐，只用於卷首、主要標題與強識別區。`canvas` 是紙面底色，承載長文與索引。`action` 是磚紅，只用於可操作入口與關鍵焦點，不作裝飾大片鋪色。`muted` 處理日期、場地、分類等次要文字。狀態資訊同時使用文字標籤與位置，不只靠色彩辨識。

## Typography

字體使用系統繁中堆疊，優先保留 `zh-Hant` 字形與可靠載入。`display` 用於刊名與章節標題，`body` 用於摘要，`label` 用於狀態、日期與控制。中文不加任意字距；短日期、場地與狀態標籤需維持同一行。桌面卷首使用真正直式排版，手機改為水平短序言，避免窄螢幕長直排造成閱讀負擔。

## Layout

桌面採編輯式雙欄：左側卷首以直排建立詩刊感，右側活動索引以不同密度的列表與焦點活動組成，不使用等重卡片牆。內容寬度受控，長文保持可讀行長。手機順序改為品牌、短序言、主要入口、活動列表；全域導覽收進按鈕開啟的面板，主要內容不依賴 hover。

## Elevation & Depth

深度以紙面層次、細線分隔、局部墨色反差建立。陰影只保留在 mobile 導覽面板等暫態層，不用大面積玻璃或發光效果。活動紀錄之間以編號、留白、分隔線與摘要密度形成層級。

## Shapes

形狀偏克制，`small` 用於按鈕與狀態，`medium` 用於卷首容器。圓角不是品牌主角；詩刊感主要由直排、欄線、紙色與文字節奏建立。

## Components

主要元件包含全域導覽、卷首、內容入口、活動紀錄與狀態標籤。活動紀錄在桌面保持索引式橫排資訊，在手機改成緊湊直向摘要，但保留同一筆資料與唯一識別。導覽面板需支援按鈕開關、Escape 關閉與焦點返回。

## Do's and Don'ts

- Do 讓日期、場地、詩人與摘要構成主要視覺節奏。
- Do 在桌面保留真正直排卷首，並在手機提供水平等價內容。
- Do 讓每筆活動有唯一識別與明確名額狀態。
- Don't 使用假見證、價格方案、KPI 牆或 SaaS 側欄。
- Don't 把所有內容放進相同卡片網格。
- Don't 用通用漸層、空海報框或裝飾性發光取代活動內容。
