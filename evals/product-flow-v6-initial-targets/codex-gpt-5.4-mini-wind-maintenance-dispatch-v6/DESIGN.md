---
version: alpha
name: "離岸風場維修派工台"
description: "以台灣離岸風場值班調度為中心的單頁派工工作台，將緊急工單、派船決策與本機模擬結果放在同一個視窗中。"
colors:
  primary: "#0F2B3A"
  on-primary: "#F2F8FB"
  canvas: "#08131A"
  surface: "#10212B"
  surface-raised: "#152938"
  on-surface: "#EAF3F7"
  accent: "#E2A33C"
  on-accent: "#111A22"
  success: "#4FBF9C"
  on-success: "#09211D"
  danger: "#D86A5E"
  on-danger: "#231112"
typography:
  display:
    fontFamily: '"Noto Sans TC", "PingFang TC", "Microsoft JhengHei", system-ui, sans-serif'
    fontSize: "2.25rem"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  title:
    fontFamily: '"Noto Sans TC", "PingFang TC", "Microsoft JhengHei", system-ui, sans-serif'
    fontSize: "1.375rem"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  body:
    fontFamily: '"Noto Sans TC", "PingFang TC", "Microsoft JhengHei", system-ui, sans-serif'
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "0em"
  ui:
    fontFamily: '"Noto Sans TC", "PingFang TC", "Microsoft JhengHei", system-ui, sans-serif'
    fontSize: "0.95rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "0.01em"
  mono:
    fontFamily: '"SFMono-Regular", "SF Mono", "Menlo", "Consolas", monospace'
    fontSize: "0.95rem"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "0em"
    fontFeature: '"tnum" 1'
rounded:
  sm: "0.4rem"
  md: "0.8rem"
  lg: "1.2rem"
  xl: "1.6rem"
spacing:
  xs: "0.375rem"
  sm: "0.625rem"
  md: "1rem"
  lg: "1.5rem"
  xl: "2.25rem"
components:
  page-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.xl}"
    padding: "{spacing.lg}"
  masthead:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.display}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  surface-base:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  surface-raised:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.ui}"
    rounded: "{rounded.md}"
    padding: "{spacing.sm}"
  button-secondary:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.on-surface}"
    typography: "{typography.ui}"
    rounded: "{rounded.md}"
    padding: "{spacing.sm}"
  chip-urgent:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  chip-success:
    backgroundColor: "{colors.success}"
    textColor: "{colors.on-success}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  chip-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-danger}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
---

# 離岸風場維修派工台

## Overview

這是一個給台灣離岸風場值班調度員使用的繁體中文單頁工作台。使用者帶著時間壓力進來，目標不是瀏覽，而是先辨識緊急工單，再查看其中一筆，最後把船班改派到可用窗口，並且得到清楚的本機模擬結果。

整體語氣要像海象儀表與航海圖的結合：精準、克制、可快速掃讀。產品不是通用 SaaS 儀表板，也不是卡片牆；它是高密度派工面板。

## Colors

色彩採低彩度深藍灰為底，讓畫面像夜間海圖與控制台，而不是黑金風格或紫藍發光版面。

- `canvas` 是整頁背景，維持最安靜的底層。
- `surface` 與 `surface-raised` 是主要內容層，分別承載清單與詳情。
- `primary` 只用在主標與海況橫幅，建立整頁的控制感。
- `accent` 是唯一高辨識狀態色，只能出現在緊急標記、主要動作與關鍵回饋。
- `success` 與 `danger` 只用在本機模擬成功與錯誤/重試回饋，避免把一般提示染成警示。

色彩的心理效果屬於 `UNKNOWN` 或 `HYPOTHESIS`，所以這份系統不宣稱某個色相會自動帶來信任或效率。色彩的責任只有兩個：分層與狀態。

## Typography

中文字採單一無襯線系統家族，優先顧及繁中字形與長字串穩定性。標題、內文、介面文字與數字共用一致的字形語調，避免介面像內容拼貼。

- `display` 用於頁首主標，控制第一眼秩序。
- `title` 用於區塊標題與被選取工單標題。
- `body` 用於說明、備註與長文內容，行距較寬，保留可讀性。
- `ui` 用於按鈕、篩選與標籤，保持短、硬、清楚。
- `mono` 用於工單編號、船班編號與時間數字，數字採等寬對齊，方便掃描。

繁中內容維持水平排版；不把欄位擠成假直排。長標題與說明要能在 200% 放大後維持自然換行。

## Layout

桌機是高密度主從視圖：左側看清單與篩選，右側固定放詳情與改派表單。手機改成單欄任務流，先看到摘要與清單，再往下進入詳情與改派，不做窄側欄。

| 區域 | 桌機角色 | 手機等效 | 順序 | 互動 | 延後/移除 |
| --- | --- | --- | --- | --- | --- |
| 海況總覽 | 顯示值班語境與窗口概況 | 壓縮成單一橫幅與計量條 | 1 | 只讀 | 移除大面積裝飾 |
| 篩選列 | 常駐篩選與搜尋 | 單列按鈕加搜尋框 | 2 | 點按、輸入 | 不改成側欄 |
| 工單清單 | 高密度對照與快速開啟 | 單欄卡片式清單 | 3 | 選取、切換篩選 | 欄位濃縮為標籤列 |
| 詳情面板 | 右側主從視圖與改派表單 | 清單下方完整步驟區 | 4 | 選取、改派、重試 | 不縮成窄欄 |
| 狀態回饋 | 右下提示與結果確認 | 貼近表單的即時訊息 | 5 | 成功、錯誤、空白 | 不使用全頁遮罩 |

## Elevation & Depth

這個介面只需要兩個主要深度層級：底層海圖背景與內容表面。靠邊界、間距與細線建立分層，不靠濃重陰影或玻璃模糊。

詳情面板可比清單稍微抬升，表示它是當前操作焦點；但它仍然是可讀內容，不是浮動魔法窗。成功、錯誤與空白訊息也使用表面區塊，而不是覆蓋全頁。

## Shapes

幾何語言偏實用：中等圓角、清楚邊界、低裝飾。按鈕與標籤可以柔和，但不能變成滿版膠囊牆。表格、欄位與摘要條都保持穩定矩形骨架，讓海圖感來自結構，不是來自特效。

## Components

- 頁首主標與海況橫幅使用 `masthead`，提供產品的視覺錨點。
- 清單與詳情分別使用 `surface-base` 與 `surface-raised`，形成穩定的主從關係。
- 主要改派按鈕使用 `button-primary`；次要控制與回退操作使用 `button-secondary`。
- 緊急標籤使用 `chip-urgent`，成功與錯誤回饋分別使用 `chip-success` 與 `chip-danger`。
- 工單列、選取狀態、空白狀態與錯誤狀態都必須能單獨成立，不依賴動畫才看得懂。
- 表格在桌機保留欄位對照；在手機改為單欄卡片式排列，但仍由同一份資料驅動，不能做出兩份互相打架的 DOM。
- 詳情表單只能描述本機模擬改派，不得暗示真實船班已同步完成。

## Do's and Don'ts

- Do 把 `accent` 留給緊急與主要動作，保持整頁只有一個真正醒目的狀態色。
- Do 讓 8 筆工單與 3 筆緊急工單都能在鍵盤下操作與篩選。
- Do 在空白、錯誤、重試與成功之間保留明確差異。
- Do 在手機上改變資訊順序與操作路徑，不只是把桌機版壓窄。
- Don't 把詳情縮成窄側欄。
- Don't 用假資料假裝真的完成了船班同步。
- Don't 讓每個區塊都像同一個圓角 SaaS 卡片。
- Don't 用多餘色彩、發光、玻璃與浮動裝飾來冒充精準感。
