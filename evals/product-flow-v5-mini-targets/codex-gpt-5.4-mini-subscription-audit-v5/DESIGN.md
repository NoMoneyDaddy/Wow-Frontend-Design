---
version: alpha
name: 家庭訂閱稽核系統
description: "繁體中文家庭共同帳本的訂閱支出稽核頁，聚焦續訂風險、用途重疊與低使用率的快速判讀。"
colors:
  canvas: "#F4F0E8"
  on-canvas: "#142322"
  surface: "#FFFDFC"
  on-surface: "#1B2422"
  muted-surface: "#E7ECE7"
  on-muted-surface: "#29403C"
  primary: "#184A45"
  on-primary: "#FFFFFF"
  accent: "#A44D28"
  on-accent: "#FFFFFF"
typography:
  display:
    fontFamily: "\"Iowan Old Style\", \"Palatino Linotype\", \"Noto Serif TC\", \"Source Han Serif TC\", serif"
    fontSize: 40px
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "0em"
  reading:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.7
    letterSpacing: "0em"
  ui:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", system-ui, sans-serif"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0em"
  numeric:
    fontFamily: "\"SFMono-Regular\", \"SF Mono\", \"Roboto Mono\", monospace"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0em"
    fontFeature: "tnum"
rounded:
  sm: 10px
  md: 18px
  lg: 24px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
components:
  page-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-canvas}"
    typography: "{typography.reading}"
    padding: "{spacing.xl}"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.reading}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xl}"
  panel-muted:
    backgroundColor: "{colors.muted-surface}"
    textColor: "{colors.on-muted-surface}"
    typography: "{typography.ui}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  button-accent:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.ui}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
---

# 家庭訂閱稽核系統

## Overview

這是一個給家庭共同檢視訂閱支出的稽核頁，不是促銷頁，也不是交易頁。主要使用者是要和家人一起判斷「哪些服務快到期、哪些用途重疊、哪些長期低使用」的人，因此內容順序必須先給出總月費與續訂壓力，再給出可討論的明細。

視覺方向採「校準過的家庭帳本」：版面像一份有邊界的稽核文件，語氣直接、資訊密度高，避免浮誇裝飾。獨特性來自續訂地平線圖與可切換的檢視，而不是額外的宣傳效果。

## Colors

色彩只做三件事：承載紙張感的底、承載內容的表面、標示可操作或需討論的重點。

- `canvas` 與 `surface` 分別代表整頁背景與主要閱讀面，維持低彩度、低干擾。
- `primary` 只在選取、主要控制與續訂重點上出現，避免整頁都像行銷強調色。
- `accent` 只用在需要家人立刻注意的討論標記，例如低使用率或需要對照的提醒。
- `muted-surface` 只承載次要說明、狀態標籤與輔助資訊，不拿來表達主要行動。
- 所有色彩都必須同時有文字、位置或圖樣線索；顏色不能單獨承擔風險判讀。

色彩心理的主張只保留為 `UNKNOWN` 或情境假設，不把任何顏色當成固定的信任或省錢保證。

## Typography

標題使用帶有紙本感的襯線語氣，讓頁面有稽核文件的判讀重量；內文與控制項使用清楚的繁體中文無襯線系統字，維持長文字、日期與數字的可掃讀性。數字欄位採等寬數字，以便縱向比較月費、日期與剩餘天數。

長服務名稱、付款人名稱與說明文字都可以自然換行，不使用固定高度去壓字。繁體中文維持正常字距，不做機械式拉寬；行高保留連續閱讀的節奏。

## Layout

桌面版以稽核儀表區加明細表構成：上方先看摘要、續訂地平線與討論提示，再往下看完整表格。視覺化與明細共用同一組資料，不複製兩份內容。

手機版改成一欄式閱讀：先看總月費與即將續訂數，再看篩選控制與續訂地平線，最後進入逐筆明細。篩選控制放在指尖可及的位置，表格在窄寬下轉成逐筆資訊塊，但保留同一份語意結構。

## Elevation & Depth

深度不靠大量陰影。主要以底色、邊線、留白與少量陰影區分層級：頁面底最輕、閱讀區次之、互動控制最清楚。只有可操作的控制與被選取的檢視才獲得更強的對比。

## Shapes

形狀語彙以穩定的圓角與直角網格為主：摘要卡、控制列與圖表模組採柔和圓角，表格維持直線與清楚分隔，避免整頁都變成一樣的膠囊或浮卡。

## Components

`page-shell` 負責整體背景與閱讀字色，`panel` 承載圖表與主要模組，`panel-muted` 承載次要說明與狀態標籤。`button-primary` 是唯一的強主動作語氣，`button-accent` 只在討論提醒或低使用率提示上出現。

篩選按鈕、續訂地平線與明細表都使用同一套資料來源。桌面版保留 table 的語意；手機版只改變呈現與排列，不建立第二份隱藏資料。圖表每個資料標記都需要可讀數值或文字標籤，不能只靠顏色。

## Do's and Don'ts

- 要先顯示總月費、即將續訂數與重疊用途，再讓使用者進入逐筆判讀。
- 要讓桌面與手機讀取的是同一份訂閱資料，而不是兩個互相分裂的版本。
- 要保留繁體中文自然換行、等寬數字與明確的篩選狀態。
- 不要把篩選解釋成已取消或已修改訂閱。
- 不要把任何費用或節省效果包裝成財務建議。
- 不要用外部資產、網路依賴或只靠顏色的圖表傳達關鍵資訊。
