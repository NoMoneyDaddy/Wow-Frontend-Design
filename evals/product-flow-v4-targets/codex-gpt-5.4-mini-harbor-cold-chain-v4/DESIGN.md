---
version: alpha
name: 港埠冷鏈交接系統
description: "繁體中文高密度夜班交接台，將港口冷鏈批次、感測新鮮度與文件風險放在同一個掃讀節奏中。"
colors:
  canvas: "#08121A"
  surface: "#0D1B26"
  surface-strong: "#122433"
  primary: "#F0B35B"
  on-primary: "#14202B"
  on-surface: "#EFF5F8"
  info: "#68B0F2"
  success: "#63D6A1"
  warning: "#F2C85B"
  danger: "#EF7E79"
typography:
  display:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 34px
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  body:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "0em"
  ui:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", sans-serif"
    fontSize: 13px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.02em"
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
rounded:
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
components:
  shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  panel-strong:
    backgroundColor: "{colors.surface-strong}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  action:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  badge-info:
    backgroundColor: "{colors.info}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  badge-success:
    backgroundColor: "{colors.success}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  badge-warning:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  badge-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-primary}"
    typography: "{typography.ui}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
---

# 港埠冷鏈交接系統

## Overview

這是一個登入後的港口冷鏈夜班交接工作台，主角是需要在 30 秒內辨識「現在處理、等待文件、可持續觀察」的調度員。畫面以高密度、低容錯為原則，資訊要能被掃讀，而不是被裝飾稀釋。

概念句：港口冷鏈交接資訊透過受控的掃讀節奏與材料感介面被揭示，讓班別接手者更快判斷貨櫃風險、感測新鮮度與文件阻塞。

## Colors

色彩只負責語意，不負責氣氛堆疊。

- `canvas` 與 `surface` 建立夜間操作的深色背景層，讓工作區域在低光環境下維持穩定閱讀。
- `surface-strong` 用在被選取、需要停留或需要聚焦的區塊，不是一般裝飾卡片的預設。
- `primary` 只表示可行動、可接手、可確認的操作。
- `info` 表示感測器、回報新鮮度與資料可信度，不等於成功。
- `warning` 表示期限逼近、資料偏舊或需要留意的狀態。
- `danger` 只給逾期、斷訊或必須立即處理的風險，不拿來代替所有異常。
- `success` 只表示已恢復、已核對或已脫離風險，不用來粉飾尚未確認的狀態。

## Typography

文字系統以繁體中文長標籤與短代碼並存為前提。顯示字級用於頁面標題與關鍵摘要，正文承載批次細節，介面字級則用於按鈕、篩選、狀態與數值標籤。數字需保持清楚、緊湊、易掃讀，避免把櫃號、溫度、期限拆散成難以比對的碎片。

長中文詞組可換行，但批次編號、溫度、期限與狀態膠囊應優先維持單行，確保 320px 寬度下仍能快速掃描。沒有載入字體時，系統字體仍要保留相近的節奏與可讀性。

## Layout

桌面版使用左側全域導覽加右側主工作面，讓比較與掃讀可以同時發生。摘要區固定在工作面頂端，先給班別、碼頭、快照時間與風險概覽，再把批次清單放在下方。

手機版不是把桌面硬縮小，而是改成異常優先的 inbox：先顯示最需要處理的批次，再用可展開的導覽與精簡摘要保留背景脈絡。主要動作要留在拇指可及區，次要資訊收進列表內層。

篩選與排序列應該貼近清單，讓使用者不必離開工作面就能改變閱讀順序。任何固定元素都不能遮住品牌、標題或第一批次的關鍵資訊。

## Elevation & Depth

深度主要靠層級、邊界與色階，而不是大量陰影。背景最深，工作板稍亮，聚焦面再提一階；狀態 chip 只在需要標記語意時短暫抬升。資料過期與感測異常用邊框、底色和短標籤共同表達，不靠單一紅色覆蓋全部異常。

## Shapes

形狀語言偏向工業標籤、封條與記錄紙：圓角克制，區塊四角清楚，狀態膠囊小而密，像現場標籤而不是消費型圓角泡泡。批次卡片的左側溫控帶可作為識別語彙，像溫度紀錄紙上的連續痕跡。

## Components

- `shell` 用於整頁底層，保留夜間操作的穩定對比。
- `panel` 用於摘要與控制區，提供可掃讀的資訊承載面。
- `panel-strong` 用於需要停留或優先注意的區塊，例如異常清單或重試結果。
- `action` 只給可執行的主要操作，例如切換導覽、提交接手或重試本機示範狀態。
- `badge-info`、`badge-warning`、`badge-danger`、`badge-success` 分別承擔感測、期限、風險與恢復四類語意，避免把所有異常塗成同一種警示色。

批次表格在桌面上保持對齊欄位，在手機上改成 inbox 式卡片列，但同一筆批次只保留一個語意來源，不複製兩份獨立狀態。資料過期需要可見，感測失敗需要可重試，但兩者都必須明確標註為靜態 demo。

## Do's and Don'ts

- Do 保持繁體中文、低光可讀、密集掃讀與明確狀態分離。
- Do 讓桌面保留橫向比較，讓手機改成優先處理的 inbox。
- Do 把文件延遲、感測斷訊、溫度偏差與處理階段分開表達。
- Don't 把所有異常都變成紅色。
- Don't 做大型 hero、行銷 CTA、玻璃擬態、霓虹漸層或裝飾性卡牆。
- Don't 把靜態 demo 寫成即時港務或 IoT 連線承諾。
