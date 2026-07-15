---
version: alpha
name: Harbor Cold Chain Handoff Console
description: Visual contract for a Traditional Chinese port cold-chain night-shift handoff workstation.
colors:
  primary: "#123645"
  on-primary: "#F2F7F8"
  surface: "#F4F1E8"
  on-surface: "#15212A"
  signal-now: "#A13A24"
  on-now: "#FFF4F1"
  signal-doc: "#765B1F"
  on-doc: "#FFF8E9"
  signal-watch: "#1D5B53"
  on-watch: "#EFFCF8"
  signal-stale: "#5D4C73"
  on-stale: "#F8F3FF"
typography:
  headline:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", \"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 34px
    fontWeight: "700"
    lineHeight: 1.15
    letterSpacing: "-0.03em"
  body:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", \"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 1.6
    letterSpacing: "0em"
  label:
    fontFamily: "\"SFMono-Regular\", Consolas, \"Liberation Mono\", Menlo, monospace"
    fontSize: 13px
    fontWeight: "600"
    lineHeight: 1.45
    letterSpacing: "0.02em"
  metric:
    fontFamily: "\"SFMono-Regular\", Consolas, \"Liberation Mono\", Menlo, monospace"
    fontSize: 18px
    fontWeight: "700"
    lineHeight: 1.2
    letterSpacing: "-0.01em"
rounded:
  none: "0px"
  sm: "8px"
  md: "14px"
  lg: "22px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  shell-header:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  summary-surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  priority-now:
    backgroundColor: "{colors.signal-now}"
    textColor: "{colors.on-now}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  priority-doc:
    backgroundColor: "{colors.signal-doc}"
    textColor: "{colors.on-doc}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  priority-watch:
    backgroundColor: "{colors.signal-watch}"
    textColor: "{colors.on-watch}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  stale-banner:
    backgroundColor: "{colors.signal-stale}"
    textColor: "{colors.on-stale}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
---

# Harbor Cold Chain Handoff Console

## Overview

此介面服務港口冷鏈夜班調度員，使用情境是高密度、低容錯、短時間交接。視覺概念是「像溫度記錄紙一樣可追溯，像碼頭標線一樣可快速判讀」，讓值班者先看到現在必須處理的批次，再辨認文件等待、持續觀察與感測可信度。

## Colors

色彩只做語意分工，不做情緒裝飾。深藍綠 `primary` 是殼層與導覽，代表穩定的操作框架；淺米 `surface` 是工作紙面，承接高密度內容。`signal-now` 只用在需要立即處理的交接壓力，`signal-doc` 表示文件或封條流程卡點，`signal-watch` 表示可持續觀察的冷鏈狀態，`signal-stale` 只標記資料快照老化與本地示意限制。食安風險、處理階段、放行期限與感測狀態在實作中仍需搭配文字、邊線與位置，不可只靠色彩。

## Typography

主體採用繁體中文系統無襯線，確保夜班桌機與手機都能穩定顯示。`headline` 給頁面標題與班別切面，保持緊密但不壓縮的層級。`body` 用於紀錄內容與說明。`label` 與 `metric` 使用等寬字氣質，模擬封條、櫃號與感測編碼的操作語彙，讓櫃號、時間與溫差容易掃讀。避免英文化全大寫眉標與過度字距，保持 `zh-Hant` 的自然閱讀節奏。

## Layout

桌面版採雙欄工作台：左側是全域導覽與班別定位，右側是交接摘要、篩選列與批次面板。批次紀錄本體以單一資料列重組，不複製桌機與手機 DOM。手機版改成異常優先 inbox：先顯示班別、快照狀態、篩選入口與立即處理批次，再把交接摘要壓縮到後段。主要按鈕、溫差、期限與狀態都需維持單行可讀，不允許偶發換行或裁切。

## Elevation & Depth

層次來自紙面、碼頭欄柵與封條邊框，而不是大量陰影。殼層使用深色背景固定框架，工作區採平面紙質底搭配細邊線。需要被注意的區塊以左側厚邊、頂部標線與局部色帶提升，而不是整張卡片浮起。暫態層僅用於手機導覽抽屜。

## Shapes

幾何語言偏向封條與標籤：外框方正、局部圓角收邊、小面積斜切標籤。大區塊圓角只留在摘要模組與導覽殼層，紀錄列保持較硬朗的結構，對應港區標線與冷鏈紙本交接質感。

## Components

共享元件分成殼層、摘要面板、優先權標籤與資料過期提示。批次列在桌機像高密度工作列，在手機會重組成縱向卡面，但仍維持同一個資料來源與同一組語意欄位。元件狀態需支援預設、焦點、選取中的篩選、局部讀取失敗、重試中與本地示意恢復。邊線粗細、次要標註、記錄紙紋理與欄位響應式折疊不放進 frontmatter，而在實作中以共用 CSS 變數維持一致。

## Do's and Don'ts

- Do 把優先權、期限、處理階段與感測可信度拆開表達，讓交接者能在 30 秒內做排序。
- Do 在手機把「現在要做什麼」放到首屏附近，而不是先展示完整摘要。
- Don't 把工作台做成 hero、卡片牆、行情銷售頁或裝飾性儀表板。
- Don't 用同一種紅色取代所有異常語意，也不要把靜態示意寫成已連線成功。
