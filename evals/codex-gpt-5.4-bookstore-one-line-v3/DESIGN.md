---
version: alpha
name: 折角書局視覺系統
description: 紙本索引卡與書脊層架語法，服務以探索與選書為核心的獨立書局網站。
colors:
  primary: "#A0432D"
  on-primary: "#FFF8F0"
  surface: "#F4E7D6"
  on-surface: "#241B17"
  muted-surface: "#E8D7C3"
  muted-ink: "#6C5A51"
typography:
  display:
    fontFamily: "\"Iowan Old Style\", Baskerville, \"Times New Roman\", serif"
    fontSize: 3.4rem
    fontWeight: "700"
    lineHeight: 1.05
    letterSpacing: -0.03em
  body:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 1rem
    fontWeight: "400"
    lineHeight: 1.75
  ui:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 0.95rem
    fontWeight: "600"
    lineHeight: 1.4
rounded:
  sm: 0.45rem
  md: 0.9rem
  lg: 1.6rem
spacing:
  sm: 0.5rem
  md: 1rem
  lg: 1.5rem
  xl: 2.5rem
components:
  hero-title:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.display}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xl}"
  body-copy:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  button-secondary:
    backgroundColor: "{colors.muted-surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.ui}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  shelf-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  shelf-row:
    backgroundColor: "{colors.muted-surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  note-label:
    backgroundColor: "{colors.on-surface}"
    textColor: "{colors.surface}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
---

# 折角書局視覺系統

## Overview

這套系統給想慢慢挑書、比對題材、記住書感的人。概念是「像在索引卡與書脊之間翻找方向」：大標像館藏題簽，列表像層架，強調閱讀路徑而不是促銷噪音。桌面版保留並列比較與留白節奏；手機版改成單手可讀、先看分類再看細節，主要動作貼近拇指區。

## Colors

`primary` 是唯一高彩度行動色，只用在可點擊主動作與重點書脊標記，不拿來鋪滿大面積背景。`surface` 是暖紙色，負責主要閱讀面；`muted-surface` 是較深的層架底，用來放列表、篩選與次要區塊。`on-surface` 是主要墨色，`muted-ink` 是說明、出版資訊與次要數據。狀態不只靠顏色，還會搭配底線、框線、位置與字重差異。

## Typography

展示層使用襯線字列，負責書感與記憶點；內文與介面用繁中優先的無襯線字列，確保長文、書名、副標、出版資訊都能穩定換行。桌面版標題容許較大對比；手機版會縮短標題行寬，避免第一屏只剩裝飾。英文書名、ISBN、數字價格維持原文，不做強制全形化。

## Layout

桌面採 12 欄但視覺上更像「主桌面＋層架」：大段內容不全塞卡片，讓主故事、書列、資訊欄有不同寬度與節奏。內容寬度上限控制在易讀範圍，長文區另設閱讀行長。手機版變成三段式：品牌與導覽先收斂、主要書單前置、次要說明延後，書籍詳情頁的側欄則改成底部黏附動作區。

## Elevation & Depth

階層主要靠色階、框線與局部陰影，不做厚重浮空卡。大區塊像鋪在桌面的紙張；列表列像嵌入木層架的索引條。只有導覽抽屜、重點推薦與書籍資訊面板會用較明顯陰影，讓使用者知道哪個區域可互動、哪個區域是閱讀面。

## Shapes

整體形狀偏直角紙片與裁切書標，圓角只留在按鈕、標籤與面板邊角，避免每個元素都同一個大圓角。粗框與細框並用：粗框給主標題與封面模擬，細框給列表、導覽與資訊欄。裝飾線條像層架導軌，需始終服務導覽或分隔，不可變成無意義花紋。

## Components

主按鈕採深赭紅底，永遠代表「往前走」；次按鈕維持紙面或層架色。`shelf-row` 是跨頁共用的書目列語法，桌面版可並列書名、敘述、行動；手機版改成堆疊但保留同一筆資料與同一個操作出口。導覽在桌面直接顯示，手機變成可展開面板；這個面板不是全站遮罩式模態窗，因此不做焦點陷阱，但會同步 `aria-expanded`、支援 Escape、並在點選連結後自動收合。

## Do's and Don'ts

- Do 用暖紙色、墨色、書脊標記、層架分隔來建立一致的書店語言。
- Do 讓首頁、書目頁、書籍頁共用同一組色票、字體、按鈕與列表元件。
- Don't 把所有內容都做成平均卡片格線。
- Don't 用高彩背景、玻璃效果或促銷式數據破壞閱讀節奏。
