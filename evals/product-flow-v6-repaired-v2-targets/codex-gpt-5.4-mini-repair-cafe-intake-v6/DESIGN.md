---
version: alpha
name: 社區修繕咖啡館
description: 以維修單與紙材感支撐三步預約流程，讓手機上的物件預約清楚、可回頭修正、可完成確認。
colors:
  primary: "#2E6F5E"
  on-primary: "#FFFFFF"
  canvas: "#F4EDE2"
  on-canvas: "#2A221C"
  surface: "#FFF9F1"
  on-surface: "#3A2F28"
  danger: "#8C4A3A"
  on-danger: "#FFF8F5"
typography:
  display:
    fontFamily: "\"Noto Serif TC\", \"PingFang TC\", \"Microsoft JhengHei\", serif"
    fontSize: 44px
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "0em"
  reading:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.7
    letterSpacing: "0em"
  functional:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0em"
spacing:
  page: "24px"
  panel: "20px"
  cluster: "12px"
  control: "16px"
  chip: "8px"
rounded:
  sm: "10px"
  md: "16px"
  lg: "24px"
  pill: "999px"
components:
  page-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-canvas}"
    typography: "{typography.reading}"
    padding: "{spacing.page}"
  booking-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.reading}"
    rounded: "{rounded.lg}"
    padding: "{spacing.panel}"
  action-button:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.functional}"
    rounded: "{rounded.pill}"
    padding: "{spacing.control}"
  step-chip:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.functional}"
    rounded: "{rounded.pill}"
    padding: "{spacing.chip}"
  field-row:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.reading}"
    rounded: "{rounded.md}"
    padding: "{spacing.cluster}"
  error-note:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-danger}"
    typography: "{typography.functional}"
    rounded: "{rounded.md}"
    padding: "{spacing.cluster}"
---

# 社區修繕咖啡館

## Overview

主要使用者是帶著故障家電、腳步匆忙但需要把事情說清楚的人。介面要像維修單與工作臺標籤一樣可靠，語氣溫暖但不幼稚，讓使用者在手機上能先填物件、再選時段、最後回頭確認與修改。

概念句：社區修繕咖啡館把維修單的紙材感轉成清楚的三步預約流程，讓手機上的預約既有秩序，也保留返回編輯的餘地。

## Colors

底色維持溫暖的紙張與桌面感，避免把整個畫面染成高飽和品牌色。

- `canvas` 用於整頁背景與較寬的留白區。
- `surface` 用於表單卡、步驟面板與摘要區。
- `primary` 只用於主要行動、目前步驟與確認狀態。
- `on-*` 色只用於對應底色上的文字與圖示。

色彩的職責是分層與引導，不負責裝飾。選取、錯誤與完成狀態會再搭配形狀、邊框與文字說明，不讓顏色單獨承擔意思。

## Typography

標題可帶一點紙本標籤的分量，但正文必須保持清楚、自然、可快速掃讀。

- `display` 用於頁面主標與步驟標題。
- `reading` 用於說明文字、表單輔助語與確認摘要。
- `functional` 用於按鈕、步驟標籤與數字型資訊。

繁體中文文案以短句為主，保持正常換行與完整詞組，不用手工斷行去撐版面。長內容可以延伸，但不得把關鍵操作藏進狹窄欄位。

## Layout

桌面版採雙欄：左側是三步預約流程，右側是紙卡式提醒與摘要輔助。右欄提供背景說明與狀態檢查，不搶走主要表單。

手機版改成單欄，先讓物件資訊與時段選擇連續出現，之後才顯示提醒與確認摘要。主要按鈕留在手指容易觸及的位置，避免固定底欄壓住輸入內容。

頁面使用明確的內容寬度與分段間距，讓表單看起來像一份可完成的工作單，而不是一排等權重卡片。

## Elevation & Depth

層次主要靠紙感、邊框與色階差異建立，不依賴厚重陰影或玻璃效果。

- 主容器比背景更亮，像疊在桌面上的工作單。
- 摘要與提醒區使用較淺的底面與細邊框，表明它們是輔助資訊。
- 錯誤狀態用邊框與文字共同提示，避免只有顏色變化。

## Shapes

整體形狀以溫和圓角為主，呼應社區工坊的手寫標籤與貼紙感，但不走玩具化。

- 面板使用中等圓角，讓內容像被整理好的單據。
- 按鈕採較完整的膠囊或大圓角，方便觸控辨識。
- 表單欄位保留清楚的邊界與足夠高度，讓修正輸入不費力。

## Components

- 預約表單：單一主欄位先完成物件資訊，再進入時段選擇與確認摘要。
- 步驟標籤：指出目前在第幾步，讓返回編輯時依然知道自己在哪裡。
- 主要按鈕：只在可前進或可確認的時候使用主色。
- 確認摘要：在本機畫面內呈現已整理好的內容，並提供返回編輯。
- 錯誤提示：貼近欄位顯示，並在送出失敗時把焦點帶回需要修正的地方。

行動版與桌面版共用同一組語意元件，只改排列與密度，不複製兩套不同真相。

## Do's and Don'ts

- Do 使用自然的繁體中文欄位名與說明。
- Do 保留返回編輯的路徑，讓使用者可以修正物件描述與時段。
- Do 把主要按鈕放在清楚可見的位置，並維持足夠點按面積。
- Don't 聲稱資料已送到遠端系統或店家後台。
- Don't 把桌面式雙欄硬塞到手機上。
- Don't 用裝飾性高飽和效果取代清楚的狀態提示。
