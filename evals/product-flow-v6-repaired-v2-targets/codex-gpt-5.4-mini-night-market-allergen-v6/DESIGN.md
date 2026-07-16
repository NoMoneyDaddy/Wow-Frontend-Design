---
version: alpha
name: 夜市過敏原隨身指南
description: "以高對比標籤與快速篩選協助使用者在夜市環境中查找攤位，並在攤商資訊上再次確認花生風險。"
colors:
  primary: "#F2B54C"
  on-primary: "#201407"
  canvas: "#100C09"
  surface: "#1A1511"
  on-surface: "#F6EFE6"
  action: "#66D7C7"
  on-action: "#08211F"
typography:
  display:
    fontFamily: '"Noto Sans TC", "PingFang TC", "Microsoft JhengHei", system-ui, sans-serif'
    fontSize: 34px
    fontWeight: 800
    lineHeight: 1.08
    letterSpacing: "-0.02em"
    fontFeature: "normal"
    fontVariation: "normal"
  body:
    fontFamily: '"Noto Sans TC", "PingFang TC", "Microsoft JhengHei", system-ui, sans-serif'
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "0em"
    fontFeature: "normal"
    fontVariation: "normal"
  label:
    fontFamily: '"Noto Sans TC", "PingFang TC", "Microsoft JhengHei", system-ui, sans-serif'
    fontSize: 14px
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0.01em"
    fontFeature: "normal"
    fontVariation: "normal"
  numeric:
    fontFamily: '"Noto Sans TC", "PingFang TC", "Microsoft JhengHei", system-ui, sans-serif'
    fontSize: 14px
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0em"
    fontFeature: "tnum"
    fontVariation: "normal"
spacing:
  page: 16px
  section: 24px
  panel: 16px
  control: 12px
  rail: 20px
rounded:
  sm: 10px
  md: 16px
  lg: 24px
  pill: 999px
components:
  shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    padding: "{spacing.page}"
  hero:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-surface}"
    typography: "{typography.display}"
    padding: "{spacing.section}"
  search-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.pill}"
    padding: "{spacing.control}"
    height: 48px
  filter-chip:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "{spacing.control}"
    height: 36px
  filter-chip-active:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "{spacing.control}"
    height: 36px
  counter:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.primary}"
    typography: "{typography.numeric}"
    rounded: "{rounded.pill}"
    padding: "{spacing.control}"
    height: 36px
  record-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.panel}"
  record-detail:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.panel}"
  primary-action:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "{spacing.control}"
    height: 44px
  index-rail:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.rail}"
  offline-note:
    backgroundColor: "{colors.action}"
    textColor: "{colors.on-action}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "{spacing.panel}"
---

# 夜市過敏原隨身指南

## Overview

這是一個繁體中文單頁指南，面向在擁擠夜市裡快速查找攤位、篩選「不含花生」並展開單筆資訊的使用者。內容必須維持誠實語氣：攤商資訊只作現場詢問前的參考，不可寫成醫療保證，也不可把未核實的安全性說成確定結果。

## Colors

暖金是唯一主要行動色，只出現在可操作的按鈕、啟用中的篩選與數量提示上。青綠只作次要輔助與離線提醒，避免和主要行動互搶焦點。深色 canvas 與 surface 承載大部分閱讀面，讓整體像夜市招牌一樣有節奏，但讀字優先於發光效果。

## Typography

標題用較重的 display 角色，強調快速掃視；內文、卡片與提醒都用同一組可讀的繁中無襯線系統字，避免風格與可讀性分家。標籤與數字分別承擔短標籤與計數，短操作文案保持單行，不靠縮小字級硬塞。

## Layout

版面以單頁索引為主。手機先看標題、搜尋、篩選與結果數，再往下進入攤位清單，所有主要操作都在第一屏可達。桌機增加右側索引欄，放置區域捷徑與提醒，但不把工作區切碎成多個同等權重的卡片區。

頁首在桌機改為左右雙欄：左側保留標題、說明與數量摘要，右側放快速確認區，讓開場敘述有足夠內容承載，不留下空泛的大面積留白。手機則維持單欄堆疊，先保證搜尋與篩選的單手可達性。

搜尋與篩選不跳頁，展開資訊也不離開目前攤位。詳情要內嵌在同一張卡裡，讓使用者在擁擠環境中少做回頭動作。空結果要明確說明原因，並提供回到全量清單的最短路徑。

## Elevation & Depth

層次主要靠對比、邊線與間距，不靠玻璃、霓虹或重陰影。卡片是可獨立掃讀的 surface，詳情展開時仍保留在原卡內，避免資訊抽離後失去上下文。深度只服務閱讀順序與操作狀態，不做純裝飾。

## Shapes

形狀語言以圓角矩形與膠囊標籤為主。卡片保持中等圓角，讓資訊像夜市攤牌一樣有邊界但不過度柔化；按鈕與篩選用更圓的膠囊，幫助使用者快速辨識可點擊區。短字標籤維持一行，避免在窄螢幕上被拆成兩層。

## Components

`shell` 定義整頁基底，`hero` 放置標題與說明，`search-field` 和 `filter-chip` 負責快速縮小清單，`counter` 回報目前顯示的攤位數。`record-card` 和 `record-detail` 承載每筆攤位資料，`primary-action` 只用在清除條件這類回到起點的短操作，`index-rail` 只在桌機補充索引，`offline-note` 明示資料為攤商提供、需現場再次確認。

`hero` 在桌機是一個雙欄開場區，右側的快速確認區用來承接最短操作路徑與提醒，避免左側敘述軌過度變窄。手機則把這段資訊疊成一欄，維持單手掃視。

每個攤位卡都必須同時保留名稱、狀態與展開控制，不能用另一個頁面或另一套重複資料替代。狀態色只顯示篩選與行動，不把安全判斷包裝成保證。

## Do's and Don'ts

- Do 把「不含花生」寫成攤商提供的標示，並保留現場再確認的提醒。
- Do 讓搜尋、篩選與展開在同一頁完成。
- Do 在手機上先保留主要操作，再讓索引與補充資訊退到次要位置。
- Don't 把攤商標示寫成醫療保證。
- Don't 用霓虹濾鏡、浮誇玻璃或全頁卡片模板遮住可讀性。
- Don't 讓短操作標籤換行成兩行。
