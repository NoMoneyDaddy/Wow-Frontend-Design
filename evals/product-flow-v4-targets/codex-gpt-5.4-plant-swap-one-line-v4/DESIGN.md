---
version: alpha
name: Plant Exchange Commons Design System
description: Visual contract for a neighborhood-first plant exchange platform built around browsing, trust, and local reciprocity.
colors:
  primary: "#29543B"
  on-primary: "#F5F1E8"
  surface: "#F7F3EA"
  on-surface: "#1E2A22"
  accent: "#8A431D"
  on-accent: "#FFF7F0"
  muted-surface: "#E7E0D1"
  muted-ink: "#4F5E54"
  line: "#B8B19F"
typography:
  display:
    fontFamily: "\"Iowan Old Style\", \"Palatino Linotype\", serif"
    fontSize: 48px
    fontWeight: "700"
    lineHeight: 1.08
    letterSpacing: "-0.02em"
  body:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", system-ui, sans-serif"
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 1.7
    letterSpacing: "0em"
  ui:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", system-ui, sans-serif"
    fontSize: 15px
    fontWeight: "600"
    lineHeight: 1.4
    letterSpacing: "0.01em"
rounded:
  sm: 10px
  md: 20px
spacing:
  md: 18px
  lg: 28px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  button-accent:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  base-surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  panel-muted:
    backgroundColor: "{colors.muted-surface}"
    textColor: "{colors.muted-ink}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  divider-rule:
    backgroundColor: "{colors.line}"
    textColor: "{colors.on-surface}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    height: 1px
---

# Plant Exchange Commons Design System

## Overview

這個系統服務想交換盆栽、扦插與照護經驗的社區住戶。整體語氣要可靠、溫暖、略帶手作感，不做商城式促購，而是讓「分享與換養」成為主角。版面以索引與紀錄感為核心，讓使用者快速判斷植物狀態、交換條件與交接方式。

## Colors

深葉綠是主要行動色，只用於可執行操作、目前所在頁與重要導引。米色畫布提供像紙本交換簿的背景，讓資訊密度可以提高但不冷硬。陶土橘只用於提醒「可交換」與需要回應的社群訊號，不作大面積背景。柔和灰綠承接次要說明與社區規則，避免次級資訊看起來像禁用。

## Typography

展示與段落標題使用帶書卷感的襯線字，強化交換札記與植物標本卡的氣質。內文與介面控制使用傳統中文系統黑體堆疊，優先保證 `zh-Hant` 可讀性、數量資訊穩定與行動裝置清晰度。英文品種名與時間資訊可混排，但不以全大寫做階層。

## Layout

桌面版採雙軸結構：主要內容區負責瀏覽或閱讀，側邊欄承接規則、交接資訊與社區提示。行動版會把首要任務提前，先看到導覽、頁面標題、目前狀態與主要行動，再把規則與補充內容收束成短段落與可點開區塊。三頁都維持同一個頁首、導覽節奏、卡片尺度與按鈕位置規律。

## Elevation & Depth

層次主要靠底色切換、細框線與局部深色區塊建立，不依賴厚重陰影。互動面板像被壓在社區布告欄上的紙張，使用溫和陰影與邊線表示可操作性；覆蓋式選單在小螢幕以實心底片呈現，避免透明材質降低閱讀。

## Shapes

外框以中等圓角搭配少量直角分隔線，模仿盆器標籤與紙卡的混合感。大區塊保留呼吸空間，標籤與膠囊只用在狀態與分類，不讓整頁退化成同質圓角卡片陳列。插畫性裝飾採葉片與格線節奏，維持簡潔，不壓過內容。

## Components

主要按鈕固定使用深葉綠，代表確認瀏覽、提出交換或查看詳情。陶土橘按鈕僅用於需要社群回應的次主行動，例如啟動篩選或發送交換訊息。列表卡與細節面板共享同一種底板與標題階層；狀態標籤使用相同字重與膠囊節奏，但實際邊框、分隔線、黏性底部操作列與行動版抽屜選單等細節以頁面 CSS 實作，不在 token frontmatter 擴充不受支援的欄位。

## Do's and Don'ts

- Do 讓每個頁面都先回答「這株植物是否適合交換、交換條件是什麼、下一步在哪裡」。
- Do 在行動版把主要操作維持在首屏或拇指容易抵達的位置。
- Don't 把網站做成價格導向商城、假裝成交成功，或捏造社群數據。
- Don't 用同一種卡片與相同節奏鋪滿所有區域；列表、札記、規則與詳情要有不同密度。
