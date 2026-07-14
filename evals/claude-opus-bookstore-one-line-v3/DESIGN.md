---
version: alpha
name: 硯臺書局 Inkstone Books
description: A Traditional Chinese independent bookstore presented as a curated reading table, where books read as physical stock rather than a card grid.
colors:
  primary: "#B23A2E"
  on-primary: "#FBF7EF"
  canvas: "#F4EDE0"
  surface: "#FBF7EF"
  on-surface: "#241E19"
  muted: "#6B6157"
  border: "#D8CCB8"
  focus: "#1E5F74"
typography:
  display:
    fontFamily: "\"Noto Serif TC\", \"Songti TC\", \"Georgia\", serif"
    fontSize: 44px
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: 0.01em
  title:
    fontFamily: "\"Noto Serif TC\", \"Songti TC\", \"Georgia\", serif"
    fontSize: 22px
    fontWeight: 600
    lineHeight: 1.35
  body:
    fontFamily: "system-ui, \"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.75
  label:
    fontFamily: "system-ui, \"PingFang TC\", \"Noto Sans TC\", sans-serif"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.4
  price:
    fontFamily: "\"Noto Sans TC\", system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.2
    fontFeature: "\"tnum\" 1"
rounded:
  sm: 3px
  md: 6px
spacing:
  xs: 6px
  sm: 10px
  md: 16px
  lg: 28px
components:
  buy-button:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  quiet-surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  ghost-button:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
---

# 硯臺書局 Inkstone Books

## Overview

硯臺書局是一間專注於文學、人文與獨立出版的實體選書店的線上門面。讀者多半有明確的閱讀品味，來這裡不是被行銷推著走，而是像走進書架前抽出一本、翻兩頁、決定帶不帶走。

介面的核心隱喻是「一張擺滿書的桌子」：桌面版把書當成立在架上的書脊來索引，行動版把書平放成封面卡片方便單手翻閱。密度偏編輯性而非儀表板式——留白讓標題呼吸，清單處則允許緊湊掃讀。情緒定調為沉靜、可信、帶手感；絕不喧鬧或炫技。

## Colors

- `canvas`：頁面底色，暖紙色，模擬未漂白紙張。
- `surface`：卡片與內容區塊底色，比 canvas 略亮。
- `on-surface`：主要墨色文字，接近純黑但帶暖調。
- `muted`：次要資訊（作者、出版資料、頁數）。
- `border`：分隔線與書架格線，低對比。
- `primary`（硃砂紅）：**只在使用者可以行動時出現**——購買、加入書袋、啟用中的篩選、目前所在導覽項。它不是裝飾色，不用於大面積背景或純標題。
- `focus`：鍵盤焦點外框，藍綠色以與硃砂紅明確區隔，避免行動色與焦點色混淆。

狀態不只靠顏色：啟用中的篩選同時有底色、粗體與勾號；售罄同時有灰字與「售罄」標籤。

## Typography

- `display`：頁面主標題，宋體骨架，承載書店的文氣。
- `title`：書名與區塊標題。
- `body`：介紹與段落，行高 1.75 讓中文透氣。
- `label`：按鈕、篩選、導覽等功能性文字。
- `price`：價格專用，啟用表格數字 `tnum` 以利對齊比價。

中文不使用正向字距與英文式小型大寫眉標。長書名允許換行，不裁切；混排的 ISBN、年份等拉丁數字保留半形。

## Layout

桌面版採 12 欄暖紙網格，內容主寬約 68rem，閱讀段落另以 42em 限制行長。目錄頁左側為篩選欄，右側為書脊索引架。

行動版轉換：導覽收進頂部列與全螢幕選單；篩選欄改為頂部可展開的揭露區；書脊架改為單欄封面卡片堆疊（見 Shapes 的書脊說明）。間距使用 `spacing` 節奏，區塊之間刻意疏密交替——寬鬆的介紹段落之後接緊湊的書目清單。

## Elevation & Depth

以色調層次與細邊框表達層級，而非大量陰影。書脊/封面僅用一道貼近紙面的短陰影模擬實體厚度，光源統一自上方。彈出選單使用單層 scrim。不使用玻璃模糊或多重浮動陰影。

## Shapes

形狀語言取自書本實體：直角為主，僅書脊與卡片用 `rounded.sm`／`rounded.md` 的極小圓角模擬裁切邊。書脊索引在桌面為直立矩形，hover 時輕微傾斜與位移（`prefers-reduced-motion` 下改為僅色彩與外框變化，位置不動）；行動版書脊平放為封面卡片，資訊完全等價。此簽名效果之外的內容在無 JavaScript、無動態時仍可完整閱讀。

## Components

- `buy-button`：硃砂紅實心，購買與加入書袋的主要行動。hover／active 以加深與下壓表達，於 Markdown 而非 token 描述。
- `ghost-button`：紙面底、墨字、細框的次要行動（如「查看詳情」）。
- `quiet-surface`：介紹與內容區塊的基礎紙面容器。

所有元件在 rest／hover／focus-visible／disabled（售罄）狀態皆有非顏色區別。焦點使用 `focus` 色外框，與行動色分離。

## Do's and Don'ts

- Do 讓硃砂紅只代表可行動之處，其餘保持紙墨中性。
- Do 在行動版把書脊轉為封面卡片，保持資訊等價而非只把桌面壓窄。
- Don't 把每個區塊都包成同一種圓角卡片。
- Don't 在中文標題套用英文式字母間距或小型大寫眉標。
