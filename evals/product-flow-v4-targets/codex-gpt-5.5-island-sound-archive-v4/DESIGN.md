---
version: alpha
name: 島嶼聲音檔案館設計系統
description: 繁體中文 editorial archive，用田野索引、潮線與檔案標籤語彙組成可閱讀的聲音探索介面。
colors:
  primary: "#173B3F"
  on-primary: "#FFFFFF"
  canvas: "#F8F4EA"
  on-canvas: "#18211F"
  surface: "#FFFDF7"
  on-surface: "#18211F"
  field: "#E7DCC8"
  on-field: "#18211F"
  accent: "#8A3F2A"
  on-accent: "#FFFFFF"
typography:
  display:
    fontFamily: "Georgia, 'Times New Roman', 'PingFang TC', 'Noto Serif TC', serif"
    fontSize: 44px
    fontWeight: "700"
    lineHeight: 1.08
    letterSpacing: "0em"
  body:
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 1.65
    letterSpacing: "0em"
  meta:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, 'PingFang TC', monospace"
    fontSize: 13px
    fontWeight: "600"
    lineHeight: 1.45
    letterSpacing: "0em"
rounded:
  none: 0px
  small: 4px
  medium: 8px
spacing:
  compact: 8px
  regular: 16px
  broad: 32px
components:
  page-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-canvas}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "{spacing.broad}"
  primary-action:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.meta}"
    rounded: "{rounded.small}"
    padding: "{spacing.regular}"
  archive-surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.medium}"
    padding: "{spacing.regular}"
  field-strip:
    backgroundColor: "{colors.field}"
    textColor: "{colors.on-field}"
    typography: "{typography.meta}"
    rounded: "{rounded.small}"
    padding: "{spacing.compact}"
  editorial-title:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-canvas}"
    typography: "{typography.display}"
    rounded: "{rounded.none}"
    padding: "{spacing.compact}"
  accent-marker:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.meta}"
    rounded: "{rounded.small}"
    padding: "{spacing.compact}"
---

# 島嶼聲音檔案館設計系統

## Overview

這個系統服務一般讀者與研究者，讓使用者先辨認島嶼、年代、語言與權利脈絡，再進入逐字節錄。概念是「潮線上的田野索引」：聲音不是串流商品，而是帶有採集條件、講者關係與使用限制的檔案。

## Colors

底色採低彩度紙面色，承載長篇繁體中文閱讀；深青綠是主要行動、當前選取與檔案館識別，不用於錯誤或裝飾。陶土色只標示節錄、待整理與權利提醒，避免與主要行動混淆。色彩心理主張狀態為 `UNKNOWN`，本系統只宣告語意角色與可讀性目標。

## Typography

標題使用襯線與系統繁中字體 fallback，建立編輯刊物感；內文與控制採系統 sans，保留手機與長段逐字稿的穩定換行。等寬 meta 只用於年份、座標、長度、授權與索引號，不作為整頁裝飾。所有字距維持 `0em`，繁中段落以自然斷行與足夠行高處理。

## Layout

桌機以不對稱 editorial grid 組成：左側導覽與索引保持可掃描，中段是檔案列，右側以直排地名索引和節錄形成島嶼縱深。手機改為品牌、目前脈絡、探索入口、精簡索引與檔案列表的順序；直排內容改由水平摘要承接，不把長直排塞入窄螢幕。

## Elevation & Depth

深度主要來自紙面層次、細線、打孔標記與重疊索引條。陰影只用於浮動 mobile 選單，不用來把每筆資料做成同質卡牆。可互動表面以邊框、背景色與焦點外框標示。

## Shapes

形狀參考錄音帶標籤與檔案盒：小半徑、實線框、切齊欄線。圓角上限為 8px；主要區塊可以沒有外框，讓內容密度與閱讀順序先行。

## Components

主要按鈕使用深青綠底與白字；索引條使用紙標籤背景；權利與狀態以文字、位置和色彩共同呈現。每筆錄音是可選取的檔案列，桌機保留可比較欄位，手機改成題名、地點、狀態與摘要優先的緊湊條目。

## Do's and Don'ts

- Do 讓題名、講者、採集資訊、權利狀態與逐字節錄有不同層級。
- Do 在手機提供水平等價內容與可觸控的探索入口。
- Do 把不可播放狀態說清楚，不用假的播放器暗示音訊存在。
- Don't 使用 KPI 牆、SaaS 側欄、付費方案或通用漸層 hero。
- Don't 讓所有錄音變成同尺寸卡片，或讓直排只是假旋轉的橫排文字。
