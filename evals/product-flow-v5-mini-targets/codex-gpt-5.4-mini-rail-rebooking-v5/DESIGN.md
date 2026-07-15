---
version: alpha
name: 島線鐵路中斷改簽工作台
description: 以繁體中文呈現的中斷改簽工作台，讓旅客在壓力下比較替代方案、理解同行限制，並只停留在送出前確認。
colors:
  canvas: "#F3EEE5"
  surface: "#FFFDF9"
  muted-surface: "#E9E1D6"
  primary: "#17324A"
  on-primary: "#FFFFFF"
  on-surface: "#1B232B"
  muted: "#4D5A66"
  caution: "#6D430F"
  on-caution: "#FFF7EA"
  danger: "#6F2C2C"
  on-danger: "#FFFFFF"
typography:
  body:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", system-ui, sans-serif"
    fontSize: 17px
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: 0em
  ui:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", system-ui, sans-serif"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: 0.01em
  heading:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", system-ui, sans-serif"
    fontSize: 30px
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: 0em
  numeric:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", system-ui, sans-serif"
    fontSize: 15px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: 0em
rounded:
  sm: 10px
  md: 16px
  lg: 24px
spacing:
  xs: 6px
  sm: 10px
  md: 16px
  lg: 24px
  xl: 32px
components:
  shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
  stage:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xl}"
  hero-title:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.heading}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  disruption-alert:
    backgroundColor: "{colors.caution}"
    textColor: "{colors.on-caution}"
    typography: "{typography.ui}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  current-trip:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  option-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  option-meta:
    backgroundColor: "{colors.muted-surface}"
    textColor: "{colors.muted}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  numeric-callout:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    typography: "{typography.numeric}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  availability-badge:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-danger}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  summary-panel:
    backgroundColor: "{colors.muted-surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  primary-action:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  back-action:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
---

# 島線鐵路中斷改簽工作台

## Overview

這是一個給受阻旅客快速判斷的交易工作台，不是宣傳頁。內容先交代中斷原因與原行程，再讓使用者比較三個替代方案，最後只停在送出前確認。

受眾是在壓力下操作手機或桌機的旅客，核心需求是看懂差異、掌握同行限制、避免誤選。視覺語氣要冷靜、可信、偏工具感，讓人先找到能做的事，再看補差額與無障礙條件。

## Colors

色彩分工只服務判斷，不做裝飾。

- `canvas` 是整頁底色，帶一點紙感，讓內容區塊在壓力場景下仍然安定。
- `surface` 是主要閱讀面，放在方案、行程與按鈕周圍，保留乾淨的資訊層級。
- `muted-surface` 用在確認摘要與資訊標籤，讓次要資訊可被掃讀，但不與主要行動搶焦點。
- `primary` 只給主要動作與關鍵狀態，代表「可以前進」。
- `caution` 用在中斷警示帶，表示目前服務受影響，但必須搭配文字與結構一起出現。
- `danger` 只用於無法保證或名額緊張的提示，避免把危險、限制與一般資訊混在一起。
- `muted` 只給次要說明、時間輔助文字與補充標籤。

高彩度只允許出現在警示帶、主要動作與限制標籤。其他面積維持低彩度與高可讀性，讓差異先由文字與位置承擔。

## Typography

同一組繁中系統字體支撐全部角色，避免載入外部字型時改變版面。

- `body` 用於方案說明、條件與時間資訊，維持舒適閱讀。
- `ui` 用於按鈕、標籤與步驟提示，強調指令性。
- `numeric` 用於時間、差額與耗時，讓數字比較穩定。
- `heading` 用於頁名與摘要標題，字級較大、行高緊實，承擔第一眼辨識。

繁體中文正文保持正常字距，不用為了短句刻意拉字。長內容與混合數字需要自然換行，金額與時間要盡量保持同一視覺群組。

## Layout

版面先固定內容順序，再改變桌機與手機的排列方式。

- 桌機使用兩欄：左側先看中斷與原行程，右側並列三個替代方案，確認摘要在旁邊常駐，方便比較。
- 手機改成單欄長讀：中斷警示、原行程、方案清單、送出前確認，全部按一手閱讀順序往下展開。
- 主要內容寬度保持克制，不讓方案卡過寬；比較資訊以條列與區塊拆解，不靠多層卡片堆疊。
- 確認摘要在桌機可作為穩定側欄，在手機則退回內容流中，避免固定欄位遮住選項或操作。

這個介面的變換重點是「比較」改成「分步確認」，不是把桌機縮窄。手機保留完整差異、差額與無障礙資訊，只把並列比較換成更容易單手掃讀的順序。

## Elevation & Depth

深度只靠層次與邊界，不靠華麗陰影。

- 主要表面以扁平區塊與輕量邊界區分，讓資訊看起來像工作台而不是漂浮面板。
- 警示帶、方案列與摘要區用不同底色建立層級。
- 只有在確認摘要上允許更明顯的視覺聚焦，作為送出前的最後檢視區。

避免玻璃質感、強反光或大量景深，因為這類效果會在壓力下稀釋可讀性。

## Shapes

形狀語言偏向穩定、略帶軌道感。

- 方案與摘要使用中等圓角，讓內容柔和但仍像正式工具。
- 主要動作與次要動作保持較小圓角，維持指令感。
- 警示帶用較小圓角與緊湊內距，像一條插入工作流的警戒標記。
- 整體可用一條縱向路線線索串起中斷、方案與確認，形成產品專屬的導引感。

## Components

- `shell` 提供整頁背景與基本文字色，讓整體保持低干擾。
- `stage` 承載主要工作流，桌機與手機都共享同一組內容語義。
- `hero-title` 承接頁首的主標題與主要概念句，讓開場訊息有清楚的層級。
- `disruption-alert` 顯示停駛原因與當前風險，必須配合文字，不可只靠顏色。
- `current-trip` 說明原始行程、乘客組成與無障礙需求，讓替代方案有可比基準。
- `option-card` 呈現每個替代方案；卡片內以時間、轉乘、座位與無障礙條件分層。
- `option-meta` 承接次要說明，例如候補、車廂限制與補差額註記。
- `numeric-callout` 承接時間、抵達與差額這類需要穩定對齊的數字片段。
- `availability-badge` 標示座位不保證、名額緊張或暫不適用。
- `summary-panel` 收斂選定方案、同行限制與差額，作為確認前的最後核對。
- `primary-action` 是唯一主要前進動作，只在使用者已做出選擇後前進到確認摘要。
- `back-action` 回到方案清單並保留選擇，讓修改成本低。

桌機上，方案可以並列比較；手機上，每個方案改為單列可掃讀的 radio 區塊，摘要在確認後才出現。原生 radio 會保留，因為這是最穩定也最可預測的選擇控制。

## Do's and Don'ts

- Do 讓所有關鍵資訊同時可見：原行程、中斷原因、三個方案、差額、轉乘與無障礙條件。
- Do 讓選取、確認與返回修改都保有明確狀態。
- Do 把「未送出」說清楚，避免介面像是已經完成交易。
- Do 在手機上重排閱讀順序與摘要位置，保留單手操作的連續性。
- Don't 用紅色單獨代表所有問題。
- Don't 把手機版做成桌機的直向堆疊。
- Don't 隱藏欄位來換取整齊外觀。
- Don't 宣稱即時票況、實際送出、付款成功或法規／無障礙合規。
