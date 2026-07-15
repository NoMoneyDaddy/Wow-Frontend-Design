---
version: alpha
name: 港口冷鏈交接台設計系統
description: 夜班調度員用於辨識溫控貨物異常、文件等待與可觀察批次的高密度工作台視覺契約。
colors:
  primary: "#234A46"
  on-primary: "#FFFFFF"
  canvas: "#F3F1EA"
  on-canvas: "#16201F"
  surface: "#FFFFFF"
  on-surface: "#16201F"
  surface-rail: "#E6E1D2"
  muted: "#5D6864"
  border: "#B9B5A8"
  action: "#234A46"
  action-ink: "#FFFFFF"
  urgent: "#8B2F28"
  urgent-ink: "#FFFFFF"
  due: "#765019"
  due-ink: "#FFFFFF"
  food-risk: "#6F315F"
  food-risk-ink: "#FFFFFF"
  sensor: "#315E78"
  sensor-ink: "#FFFFFF"
  disconnected: "#4F3B2F"
  disconnected-ink: "#FFFFFF"
  stale: "#5D6864"
  stale-ink: "#FFFFFF"
  due-normal: "#EFE8D5"
  due-normal-ink: "#3E311A"
typography:
  display:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif"
    fontSize: 32px
    fontWeight: "750"
    lineHeight: 1.18
    letterSpacing: "0em"
  body:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif"
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 1.62
    letterSpacing: "0em"
  label:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif"
    fontSize: 13px
    fontWeight: "650"
    lineHeight: 1.35
    letterSpacing: "0em"
  numeric:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: 14px
    fontWeight: "650"
    lineHeight: 1.35
    letterSpacing: "0em"
rounded:
  xs: "2px"
  sm: "4px"
  md: "8px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "18px"
  xl: "28px"
components:
  shell-surface:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-canvas}"
    typography: "{typography.body}"
    rounded: "{rounded.xs}"
    padding: "{spacing.lg}"
  workspace-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  rail-panel:
    backgroundColor: "{colors.surface-rail}"
    textColor: "{colors.on-canvas}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  action-button:
    backgroundColor: "{colors.action}"
    textColor: "{colors.action-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  nav-current:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  metadata-text:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.muted}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: "{spacing.xs}"
  boundary-rule:
    backgroundColor: "{colors.border}"
    textColor: "{colors.on-canvas}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: "{spacing.xs}"
  urgent-chip:
    backgroundColor: "{colors.urgent}"
    textColor: "{colors.urgent-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: "{spacing.sm}"
  due-chip:
    backgroundColor: "{colors.due}"
    textColor: "{colors.due-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: "{spacing.sm}"
  due-normal-chip:
    backgroundColor: "{colors.due-normal}"
    textColor: "{colors.due-normal-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: "{spacing.sm}"
  food-risk-chip:
    backgroundColor: "{colors.food-risk}"
    textColor: "{colors.food-risk-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: "{spacing.sm}"
  sensor-chip:
    backgroundColor: "{colors.sensor}"
    textColor: "{colors.sensor-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: "{spacing.sm}"
  disconnected-chip:
    backgroundColor: "{colors.disconnected}"
    textColor: "{colors.disconnected-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: "{spacing.sm}"
  stale-chip:
    backgroundColor: "{colors.stale}"
    textColor: "{colors.stale-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.xs}"
    padding: "{spacing.sm}"
---

# 港口冷鏈交接台設計系統

## Overview

此系統服務登入後的港口冷鏈夜班調度員。使用者需要在中斷、低光與高責任的工作情境中，於短時間內分辨需要立即處理、等待文件與可持續觀察的批次。視覺語言採「封條、碼頭標線、溫度紀錄紙」的精密工作台感：密度高、邊界清楚、資訊可追溯，不使用行銷式英雄區或裝飾性證據。

## Colors

色彩只承載語意與操作狀態。深綠是全域動作與目前工作脈絡；磚紅只表示立即急迫；琥珀表示期限壓力，淡琥珀表示期限正常；紫褐表示食安風險；藍灰表示感測資料可信；深棕表示感測斷訊；中性灰表示資料過期、等待與次要資訊。相同語意在所有批次中維持同色，且每個狀態同時搭配文字、位置與邊線，不以顏色作唯一判斷。

## Typography

主要字體使用系統繁體中文堆疊，避免外部字體依賴。顯示字重用於產品名稱、交接摘要與工作區標題；內文維持較高行高以容納繁體中文；功能標籤保持短句與穩定高度；櫃號、溫度、期限、時間使用等寬數字以利橫向比較。中文字不加機械式字距，短狀態不可任意截斷。

## Layout

桌面版是左側產品 shell 加右側工作面，支援批次列的欄位對齊、快速掃讀與橫向比較。上方摘要提供班別、目前碼頭、需處理數與資料新鮮度，但不取代批次紀錄。手機版重組為異常優先 inbox：班別與全域導覽收斂，立即行動、局部讀取失敗恢復與關鍵溫控狀態靠近首屏；次要欄位進入每筆摘要的第二層。

## Elevation & Depth

深度主要由紙面色、碼頭標線式邊框與少量貼標陰影構成。基礎畫布偏暖，工作面為白色紀錄紙，左側導覽為耐候標籤底色。陰影只用於浮動手機導覽與需要脫離背景的狀態列；不以玻璃、霓虹或大面積模糊建立層級。

## Shapes

形狀半徑小且接近工業標籤。批次列使用細直線、左側語意條與角標，表達封條與表單欄位；主要面板可使用 8px 半徑，但狀態 chip 與控制按鈕使用 2px 或 4px，避免消費級卡片牆感。例外只允許在互動焦點與移動端浮層上使用較明確外框。

## Components

按鈕以深綠底白字表示可執行動作，次要控制使用白底與邊線。批次紀錄必須保留 `record-priority`、`record-status`、`record-due` 三個分離欄位；感測器錯誤可重試，但 demo 僅在本機切換狀態，不宣稱連線成功。導覽是一般連結與按鈕，不使用應用程式選單語意。手機導覽為可關閉面板，開啟時不遮住主要工作面起點。

## Do's and Don'ts

- Do 讓急迫、食安、期限、階段與感測可信度各自有固定文字、位置與色彩角色。
- Do 在手機首屏呈現最需要處理的批次與可恢復的局部失敗。
- Do 使用真實形狀的 demo 資料，但不得宣稱已連上港務、文件或 IoT 系統。
- Don't 建立 landing page、pricing、testimonial、行銷 CTA 或大型英雄區。
- Don't 把所有異常塗成同一種紅色，或用摘要取代批次工作面。
- Don't 使用外部字體、外部圖片、套件、玻璃擬態、霓虹漸層或裝飾性卡牆。
