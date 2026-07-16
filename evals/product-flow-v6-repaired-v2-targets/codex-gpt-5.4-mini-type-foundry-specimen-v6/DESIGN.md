---
version: alpha
name: 繁中字體鑄造所樣張系統
description: 以校樣紙與精密框線呈現繁中字型樣張，專注橫直書切換、標點與 fallback 比較，以及可編修的短樣張。
colors:
  primary: "#202020"
  on-primary: "#FFF8F1"
  canvas: "#F4EBDD"
  on-canvas: "#201915"
  surface: "#FFF9F4"
  on-surface: "#201915"
  muted-surface: "#E7D8C8"
  on-muted-surface: "#56453C"
typography:
  display:
    fontFamily: "\"Iowan Old Style\", \"Baskerville\", \"Noto Serif TC\", serif"
    fontSize: 42px
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "0em"
  reading:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 17px
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "0em"
  functional:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 13px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.02em"
  specimen:
    fontFamily: "\"Noto Serif TC\", \"Iowan Old Style\", \"PingFang TC\", serif"
    fontSize: 28px
    fontWeight: 500
    lineHeight: 1.35
    letterSpacing: "0em"
rounded:
  sm: 6px
  md: 12px
  lg: 18px
  xl: 24px
spacing:
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
components:
  masthead-title:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-canvas}"
    typography: "{typography.display}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.functional}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
    height: 44px
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.functional}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
    height: 44px
  surface-panel:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-canvas}"
    typography: "{typography.reading}"
    rounded: "{rounded.xl}"
    padding: "{spacing.xl}"
  specimen-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.specimen}"
    rounded: "{rounded.xl}"
    padding: "{spacing.xl}"
  editor-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.reading}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  status-chip:
    backgroundColor: "{colors.muted-surface}"
    textColor: "{colors.on-muted-surface}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
---

# 繁中字體鑄造所樣張系統

## Overview

這是一個給字體設計師與排版工作者使用的繁中文樣張工作台。核心任務只有三件：切換橫書與直書、檢查繁中標點與英文/數字/fallback 的相容性、以及修訂一段短樣張。它不是展示型首頁，而是拿來反覆比對字面與框線的校樣工具。

整體語氣偏向校樣紙、鉛字與精密框線，而不是一般 SaaS 儀表板。最重要的內容是樣張本身，因此工具列只保留必要控制，不把介面包成一層層無意義的卡片。

## Colors

`colors.primary` 是深墨色，承擔主要動作、目前狀態與最重要的文字識別；它不是裝飾色。`colors.on-primary` 只在深墨底上出現，確保按鈕與標記可讀。

`colors.canvas` 與 `colors.surface` 是紙張兩層，前者用於整頁基底，後者用於樣張卡與輸入區。`colors.on-canvas` 與 `colors.on-surface` 都是正文與控制文字的安全深色。`colors.muted-surface` 與 `colors.on-muted-surface` 只用在提示芯與次要狀態，保持層次但不搶走樣張。

色彩情緒屬於 `HYPOTHESIS`，不是證據。這個系統只把顏色當成語義與可讀性工具：可操作、紙面層次、以及次要提示。沒有被定義為行為證據的色彩效果，一律視為未知。

## Typography

`display` 只用在頁首與少量宣示性標題，保留字形辨識度與校樣冊的聲調。`reading` 是說明、提示與輔助文字的工作字體。`functional` 是按鈕、切換與短標籤，字級較小但字重更穩定。`specimen` 專門服務樣張預覽，讓細部標點與字面比較成為視覺焦點。

繁中文字首選水平閱讀。長段說明維持舒適行長，不用一味拉寬。英文、數字與標點的比較依賴真實渲染，不靠字數想像。輸入內容可換行，但不把短樣張壓縮成一條細柱。

## Layout

桌面版採兩欄工作台：左側是編修與提示，右側是樣張預覽。閱讀順序是標題、切換控制、編修欄、預覽、fallback 提示。標題區與編修區都保留足夠文字量，避免寬欄只剩單一句總結。

行動版改成單欄，先保留切換與編修，樣張預覽往下排。直書只作檢視，不讓主要編修區被壓成狹窄長條；如果直書在窄螢幕上不利於修字，介面會明確提示回到橫書再調整。這裡的變化是重排與職責轉換，不是單純堆疊。
直書預覽在手機上仍必須收斂在可用視窗內，樣張框與控制列都以邏輯尺寸與換行自我約束，不用隱藏 overflow 來掩蓋版面外溢。

| Region | Desktop role | Mobile equivalent | Mobile order | Interaction | Defer/remove |
| --- | --- | --- | --- | --- | --- |
| Header | 產品標題與快速說明 | 同一區塊，縮短敘述 | 1 | 靜態識別 | 無 |
| Writing toggle | 方向切換主動作 | 同一按鈕，保留在首屏 | 2 | `aria-pressed` 切換 | 無 |
| Editor | 短樣張修訂 | 先於預覽呈現 | 3 | 輸入、即時同步 | 無 |
| Specimen preview | 直書/橫書比較 | 下移為第二重點 | 4 | 可捲動預覽 | 無 |
| Fallback note | fallback 與移動端出口說明 | 直接提醒回到橫書 | 5 | 讀取狀態 | 無 |

## Elevation & Depth

層次主要來自紙面底色、細線與內縮邊界，而不是投影堆疊。需要抬升感時，只用很輕的邊框與內陰影來分隔樣張、工具與提示。深陰影、玻璃感與連續發光都不在這個系統內。

## Shapes

形狀語言接近校樣紙與檔案卡：大面積容器偏方正，角落只保留中等圓角，讓框線讀起來像工具而不是玩具。按鈕與提示芯可以更圓一些，但樣張本體維持克制，不做過度膨脹的膠囊。

## Components

`masthead-title` 承接頁首主標，讓校樣冊的聲調先被看見。`button-primary` 用在最重要的切換與確認類控制。`button-secondary` 用在輔助控制與出口提示。`surface-panel` 承接編修區與說明區，讓它們像同一套校樣紙。`editor-field` 承接文字編修欄，讓輸入區維持可讀且不搶走樣張。`specimen-panel` 承接實際樣張預覽，字級、行距與內距都比一般說明更開闊。`status-chip` 只承接簡短狀態，不用來放長文。

樣張預覽的方向由同一份內容資料驅動，桌面與行動版只改版式，不複製兩份獨立狀態。`outline` 檢視只是一個檢查層，不改變內容本身。狀態芯只用來報告模式，不承擔主要內容。

## Do's and Don'ts

- Do keep Traditional Chinese as the product language and preserve the exact data-eval hooks required by the brief.
- Do keep the same specimen content source across horizontal and vertical modes.
- Do provide a clear return path to horizontal editing when vertical preview is harder to revise on mobile.
- Do keep status chips short and honest, so they support comparison instead of replacing it.
- Don't replace the workbench with a generic hero, floating dashboard cards, or decorative gradients that do not support comparison.
- Don't hide the specimen, editor, or toggle behind hover-only affordances or external assets.
- Don't invent a second system per breakpoint; let one token set and one content source drive all modes.
