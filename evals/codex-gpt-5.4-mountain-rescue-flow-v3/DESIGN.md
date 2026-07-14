---
version: alpha
name: "山域救援任務協調台設計系統"
description: "供山域救援指揮員比對責任區、通訊、時限與隊伍負荷的高密度調度介面。"
colors:
  primary: "#163245"
  on-primary: "#F5F7F5"
  surface: "#F3F1EA"
  on-surface: "#182126"
  muted: "#61727C"
  accent: "#2E657E"
  success: "#2E6A52"
  warning: "#A06A1B"
  danger: "#A13D31"
typography:
  display:
    fontFamily: "\"Noto Sans TC\", \"PingFang TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 2.625rem
    fontWeight: "700"
    lineHeight: 1.12
    letterSpacing: "-0.02em"
  title:
    fontFamily: "\"Noto Sans TC\", \"PingFang TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 1.25rem
    fontWeight: "700"
    lineHeight: 1.3
  body:
    fontFamily: "\"Noto Sans TC\", \"PingFang TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 1rem
    fontWeight: "500"
    lineHeight: 1.55
  label:
    fontFamily: "\"Noto Sans TC\", \"PingFang TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 0.875rem
    fontWeight: "600"
    lineHeight: 1.35
  mono:
    fontFamily: "\"SFMono-Regular\", \"JetBrains Mono\", monospace"
    fontSize: 0.875rem
    fontWeight: "600"
    lineHeight: 1.4
rounded:
  sm: 0.375rem
  md: 0.75rem
  lg: 1rem
spacing:
  xs: 0.375rem
  sm: 0.75rem
  md: 1rem
  lg: 1.5rem
  xl: 2rem
components:
  shell-sidebar:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  summary-surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  nav-item-current:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  action-button:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  record-row:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  priority-chip-high:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  status-chip-active:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  due-chip-late:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  due-chip-safe:
    backgroundColor: "{colors.success}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
---

# 山域救援任務協調台設計系統

## Overview

此系統服務山域救援指揮員。介面重點不是展示，而是讓使用者在壓力下快速比對責任區、任務急迫度、無線電可用度、到期時限與隊伍負荷。視覺語法採「精密地形儀表」：中性地表底、深色控制艙、細線分區、定量字重與克制色彩，讓危險只在真正超時或高風險時出現。

## Colors

`primary` 是控制艙深藍灰，只用於全域導覽、主要操作與穩定框架。
`accent` 是通訊與進行中的工作色，用於目前頁面、進行中階段與可追蹤焦點，不表示危險。
`warning` 只表示高急迫度或即將到期的注意狀態，不與任務階段混用。
`danger` 只表示真正超時或危險事件，不挪作品牌色。
`success` 只用於時限安全或通訊穩定這類正向運作訊號。
`surface` 與 `on-surface` 承擔主要閱讀；`muted` 僅用於次要註記、座標標籤與說明。

## Typography

顯示字與閱讀字共用支援繁體中文的無襯線家族，減少字體切換噪音。`display` 給頁面標題與核心數值，保持緊實但不做裝飾性大寫。`body` 用於任務資料列，維持高密度下的穩定閱讀。`label` 用於狀態晶片與導覽。`mono` 只給座標、頻道與時間碼，建立儀表感與欄位對齊。中文行高偏寬鬆，避免在窄螢幕下壓縮成難掃讀的字塊。

## Layout

Desktop 採三段式 shell：左側全域導覽、中段任務主列表、右側輔助摘要與交接清單。主要比較發生在任務列表橫列，固定欄意義，讓責任區、隊伍、急迫度、階段與時限能並讀。

Mobile 不是縮小 desktop。轉換後先保留頁面標題與值班摘要，再把任務列表改為優先 inbox：每筆任務先顯示責任區、隊伍、急迫度、時限，再折疊次要通訊與座標。導覽改為頂部按鈕開啟的抽屜，右側輔助欄下沉到主內容尾端。

## Elevation & Depth

此產品不靠浮誇陰影建立層級。主要用地表色差、細框線、局部加深背景與少量陰影區分固定 shell、摘要模組與任務列。臨時層只有 mobile 導覽抽屜與遮罩；它們必須顯著高於內容，但不搶奪任務色彩語意。

## Shapes

形狀語言來自地圖格網與耐候裝備標記：外框以低圓角為主，區塊邊緣俐落，狀態晶片採短圓角矩形，不使用膨脹藥丸。大區塊圓角略大於資料列，讓固定 shell 與內容模組可一眼分層。禁止每個元素都套同一種厚重卡片外觀。

## Components

`shell-sidebar` 是深色控制艙，承載導覽與交班狀態。`summary-surface` 是高資訊密度的淺色摘要模組，需保持短標籤單行。`record-row` 是任務唯一資料來源；desktop 以欄列比較，mobile 轉為兩欄資訊塊，但保持同一筆 DOM 與同一組狀態晶片。

急迫度、階段與時限各自有獨立色規則。高急迫度可用 `priority-chip-high`，進行中階段可用 `status-chip-active`，超時才可用 `due-chip-late`。若同一筆任務同時高急迫且超時，兩個晶片各自表達，不互相染色。

元件邊框、分隔線、sticky 行為、mobile 抽屜動畫與資料列響應式重排屬於實作細節，保留在執行碼中，不額外擴充 YAML 屬性。

## Do's and Don'ts

- Do 讓任務列表維持固定欄位語意，方便橫向比較與快速掃描。
- Do 在 mobile 先露出最需要決策的任務資訊，把次要欄位延後。
- Do 讓危險色只出現在真超時或真風險。
- Don't 把工作台做成行銷 hero、卡片牆或發光儀表板。
- Don't 用同一顏色同時表示急迫度、階段與期限。
- Don't 讓短按鈕、隊名或狀態籤在窄寬度意外換行或裁切。
