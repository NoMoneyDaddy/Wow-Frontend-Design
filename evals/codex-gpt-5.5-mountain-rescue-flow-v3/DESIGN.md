---
version: alpha
name: 山域救援任務協調台
description: 登入後救援指揮工作台的克制高密度視覺系統。
colors:
  primary: "#245347"
  on-primary: "#FFFFFF"
  canvas: "#F4F1EA"
  on-canvas: "#16201D"
  surface: "#FFFFFF"
  on-surface: "#16201D"
  surface-muted: "#E7E1D6"
  on-muted: "#4D5B55"
  border: "#C8C0B3"
  action: "#245347"
  focus: "#0D6E8A"
  danger: "#A5382F"
  warning: "#8A5A12"
  success: "#2F6B4F"
typography:
  display:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 34px
    fontWeight: 700
    lineHeight: 1.18
    letterSpacing: 0em
  heading:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 20px
    fontWeight: 700
    lineHeight: 1.35
    letterSpacing: 0em
  body:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: 0em
  data:
    fontFamily: "'SF Mono', Menlo, Consolas, monospace"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.45
    letterSpacing: 0em
rounded:
  sm: 4px
  md: 8px
spacing:
  sm: 8px
  md: 16px
  lg: 24px
components:
  shell-surface:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-canvas}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  page-title:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-canvas}"
    typography: "{typography.display}"
    rounded: "{rounded.sm}"
    padding: "{spacing.lg}"
  section-title:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.heading}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  nav-current:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  action-button:
    backgroundColor: "{colors.action}"
    textColor: "{colors.on-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  danger-status:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-primary}"
    typography: "{typography.data}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  warning-status:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.on-primary}"
    typography: "{typography.data}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  success-status:
    backgroundColor: "{colors.success}"
    textColor: "{colors.on-primary}"
    typography: "{typography.data}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  muted-tag:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.on-muted}"
    typography: "{typography.data}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  focus-indicator:
    backgroundColor: "{colors.focus}"
    textColor: "{colors.on-primary}"
    typography: "{typography.data}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  border-sample:
    backgroundColor: "{colors.border}"
    textColor: "{colors.on-surface}"
    typography: "{typography.data}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
---

# 山域救援任務協調台

## Overview

此系統服務山域救援指揮員。使用情境是長時間監看、多區比較、通訊不穩與時限壓力並存。視覺目標是精準、克制、高可掃讀；產品語彙來自地形圖、座標格、無線電頻道與耐候現場標記。

主要工作不是瀏覽宣傳內容，而是快速比較任務急迫度、任務階段、期限與隊伍負荷。摘要只提供全局掃描，任務列表才是決策主體。

## Colors

`primary` 是穩定指揮色，用於目前導覽、主操作與關鍵定位，不表示危險。`danger` 只表示真正危險或超時。`warning` 表示注意或中高負荷，但不能替代期限或階段。`success` 表示通訊、派遣或任務條件穩定。急迫度、階段與期限必須各自有文字與位置，不可只靠顏色互相覆蓋。

底色採暖灰紙面與白色工作面，模擬耐候任務板。邊線用低彩度灰棕，讓長時間閱讀不被高彩度干擾。焦點色使用深青，需在淺底上可辨識。

## Typography

介面以系統字體與繁體中文優先 fallback 呈現。`display` 只用在頁面標題與重大狀態。`heading` 用於區塊標題與任務名稱。`body` 用於說明與導覽。`data` 用於座標、頻道、時間、隊伍代號與短狀態，採等寬字提高掃描一致性。

中文不加額外字距。短按鈕與狀態字保持單行；長任務名稱可換行，但不得擠壓同列狀態。

## Layout

桌面版使用產品 shell：左側固定導覽、上方任務標題與摘要、主工作區的多欄比較表。寬度用於同時比較責任區、急迫度、階段、期限、隊伍與通訊狀態。

手機版改為任務 inbox：頂部壓縮導覽，任務依行動優先排序呈現，先顯示任務名稱、責任區、期限與通訊狀態，次要座標與隊伍負荷放入任務內文。手機不是單純把桌面欄位堆疊，而是將比較任務改成逐筆判斷與快速篩選。

## Elevation & Depth

深度以邊線、色面與細微陰影區分，不使用玻璃擬態或發光。常駐區塊維持低陰影；浮出的手機導覽才可有較明顯陰影。危險狀態不靠大面積紅色背景，避免長時間監看造成警示疲乏。

## Shapes

形狀採小半徑與直線網格。`sm` 用於標籤、按鈕、導覽項；`md` 用於面板與任務容器。例外只允許在地形掃描圖與狀態脈衝符號，因為其來源是等高線與無線電波。

## Components

導覽需要明確目前位置與鍵盤焦點。任務容器必須保留唯一記錄識別，並分開呈現 `record-priority`、`record-status`、`record-due`。摘要面板只呈現整體掃描，不可取代列表。

狀態標籤必須同時使用文字與位置。期限標籤可用危險色標示超時；急迫度不可自動染紅整筆任務；任務階段不可使用與期限相同的視覺規則。

## Do's and Don'ts

- Do 使用高密度比較、穩定欄位與清楚狀態文字。
- Do 在手機把任務改成優先 inbox，保留快速判斷路徑。
- Do 讓危險色只表示真正危險或超時。
- Don't 建立 landing page、hero、pricing、testimonial 或行銷 CTA。
- Don't 使用霓虹漸層、玻璃擬態、裝飾性卡牆或滿版紅色警報。
- Don't 讓急迫度、任務階段與期限共用同一套語意顏色。
