---
version: alpha
name: 社區修繕咖啡館預約
description: 以維修單與紙材氣質包裹的繁體中文預約流程，先說清楚物件，再選時段，最後在本機完成確認與回編輯。
colors:
  primary: "#6F3C27"
  on-primary: "#FFF8F2"
  surface: "#F8F1E8"
  on-surface: "#241912"
  muted-surface: "#ECE0D1"
  muted-ink: "#665549"
  error: "#A13D32"
  on-error: "#FFF8F4"
  success: "#2F694F"
  on-success: "#F4FBF7"
typography:
  headline:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", \"Segoe UI\", sans-serif"
    fontSize: 40px
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "-0.02em"
  body:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", \"Segoe UI\", sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "0em"
  label:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", \"Segoe UI\", sans-serif"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "0.02em"
  caption:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", \"Segoe UI\", sans-serif"
    fontSize: 13px
    fontWeight: 500
    lineHeight: 1.45
    letterSpacing: "0.01em"
rounded:
  sm: 8px
  md: 14px
  lg: 20px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
components:
  shell:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xl}"
  intro-card:
    backgroundColor: "{colors.muted-surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  primary-button:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  secondary-button:
    backgroundColor: "{colors.muted-surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  support-chip:
    backgroundColor: "{colors.muted-surface}"
    textColor: "{colors.muted-ink}"
    typography: "{typography.caption}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  alert-error:
    backgroundColor: "{colors.error}"
    textColor: "{colors.on-error}"
    typography: "{typography.caption}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  alert-success:
    backgroundColor: "{colors.success}"
    textColor: "{colors.on-success}"
    typography: "{typography.caption}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
---

# 社區修繕咖啡館預約

## Overview

這是一個繁體中文單頁預約流程，面向帶著故障家電前來的社區使用者。整體氣質像修繕單與紙材，不追求華麗包裝，而是用安定、清楚、可回復的步驟，讓手機上的預約草稿先成形，再回頭慢慢編輯。

## Colors

主色只在使用者能採取行動、確認狀態或完成回饋時出現。`surface` 與 `muted-surface` 承載紙張與工作台的安靜層次，`on-surface` 與 `muted-ink` 保持主要內容可讀，`error` 與 `success` 只用來表達欄位錯誤、草稿確認與狀態回饋。這個配色的情緒判斷屬於 `HYPOTHESIS`：它支持溫暖、可信、務實的感受，但不把色相效果當成普遍心理定律。

## Typography

標題使用較緊的層級與稍低的字距，讓中文標語保有紙本標籤感。內文與欄位說明維持中性閱讀節奏，避免過度裝飾或全大寫眉頭式排版。標籤與按鈕用較高字重，確保在小螢幕與長字串下仍能掃讀。數字與時段資訊沿用同一閱讀字體，不另外引入分離的展示字族。

## Layout

桌面版採雙欄：主要流程在左，草稿與提醒在右，讓使用者可一邊操作一邊確認內容。手機版改成單欄直向流程，先顯示任務與第一步，再把輔助說明與草稿摘要往下放，主要操作維持在容易碰到的位置。中文閱讀區保留約四十個全形字內的節奏，避免桌面與平板把段落拉得過長；步驟切換只改變可見區塊，不改變語意順序。

## Elevation & Depth

整體以平面紙材為主，靠邊線、留白與少量陰影分層。只有主要流程卡與確認摘要有較明顯的浮起感，其他輔助資訊保持更低的存在感。這讓修繕單的視覺秩序清楚，但不會把每個區塊都做成同樣重量的圓角卡片。

## Shapes

形狀語言偏方正、略柔和，像可書寫的工作單，而不是消費型儀表板。按鈕與欄位有一致的中等圓角；狀態標籤更小、更克制。確認摘要可以帶一點票根與修繕單的感覺，但不使用誇張氣泡、玻璃擬態或過度圓潤的裝飾。

## Components

主要元件是主按鈕、次按鈕、文字欄位、支援標籤、錯誤提示、成功提示、流程卡與確認摘要。主按鈕只負責往下一步或完成草稿確認；次按鈕只負責回到編輯。欄位保持原生語意與清楚標籤，錯誤提示連結到對應欄位並可直接回焦點。確認摘要會在完成後保留已選物件與時段，並清楚標示尚未傳送遠端；操作列要占據自己的版面，不覆蓋欄位或提示文字。

## Do's and Don'ts

- Do 保留可回頭編輯的草稿感，讓確認不是不可逆的終點。
- Do 把錯誤放在欄位附近，並維持可鍵盤操作的流程。
- Do 在手機上重新安排層級與空間，讓主要動作留在拇指可及處。
- Don't 把這個流程說成已經遠端送出或完成正式預約。
- Don't 用通用 SaaS 的玻璃、霓虹、英雄大圖或懸浮大卡片來包裝。
- Don't 讓每個區塊都用同樣的圓角、陰影與密度，避免紙材感被抹平。
