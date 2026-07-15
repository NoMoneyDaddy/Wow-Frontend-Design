---
version: alpha
name: Island Voice Archive
description: Editorial archive system for browsing island oral-history recordings in Traditional Chinese.
colors:
  primary: "#1F4A49"
  on-primary: "#F7F2E8"
  canvas: "#F3EDE1"
  on-canvas: "#1D2426"
  surface: "#E4D9C8"
  on-surface: "#1D2426"
  muted-surface: "#D4C7B4"
  line: "#4C565A"
typography:
  display:
    fontFamily: 'Baskerville, "Noto Serif TC", "PingFang TC", serif'
    fontSize: 52px
    fontWeight: "700"
    lineHeight: 1.08
    letterSpacing: "-0.02em"
  title:
    fontFamily: '"Noto Serif TC", "PingFang TC", "PMingLiU", serif'
    fontSize: 28px
    fontWeight: "600"
    lineHeight: 1.3
    letterSpacing: "0em"
  body:
    fontFamily: '"PingFang TC", "Noto Sans TC", "Microsoft JhengHei", sans-serif'
    fontSize: 17px
    fontWeight: "400"
    lineHeight: 1.72
    letterSpacing: "0em"
  label:
    fontFamily: '"PingFang TC", "Noto Sans TC", "Microsoft JhengHei", sans-serif'
    fontSize: 14px
    fontWeight: "600"
    lineHeight: 1.45
    letterSpacing: "0.04em"
rounded:
  none: "0px"
  sm: "8px"
  lg: "22px"
spacing:
  xs: "6px"
  sm: "12px"
  md: "18px"
  lg: "28px"
  xl: "40px"
components:
  page-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.on-canvas}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "{spacing.lg}"
  archive-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  vertical-ribbon:
    backgroundColor: "{colors.muted-surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.title}"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  utility-chip:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  rule-label:
    backgroundColor: "{colors.line}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
---

# Island Voice Archive Design System

## Overview

這是一個給一般讀者與研究者共同使用的島嶼聲音檔案探索頁。核心行為不是播放，而是先理解題名、講者、節錄、採集脈絡與權利條件，再決定是否進入逐筆閱讀。視覺語法採用「編輯式索引」：像田野筆記、錄音帶標籤與檔案盒的編排秩序，但保持可掃讀、可比較、可在手機上快速切入。

## Colors

`canvas` 是帶紙感的暖底色，承接長文閱讀與檔案感。`surface` 用於索引面板、紀錄列與導覽抽屜，形成明確但不浮誇的層次。`primary` 只用在可採取下一步的主動作與可聆聽狀態，避免把整頁染成宣傳語氣。`line` 是標籤與分隔的深色墨線，用於建立檔案盒、座標與欄位秩序，而不是做厚重陰影。`muted-surface` 專供直排索引帶與輔助編輯註記，不用來承載主要互動。

## Typography

展示層使用高對比襯線，讓題名與檔案標題具備文獻感。標題層以適合繁中題名的襯線系統延續正式感。內文與欄位標記使用穩定的無襯線，支撐長摘要、權利說明與採集資訊。繁中正文避免機械式大寫眉標；標記的層級靠字重、間距與欄位秩序建立。長題名與雙語地名允許換行，但年份、狀態與短按鈕必須維持單行。

## Layout

桌機版由三個區域構成：導覽與上下文、直排編輯索引帶、主檔案閱讀面。首屏同時顯示品牌、目前檔案範圍與下一步動作。主要檔案列表採開放式列排與欄位帶，不把每筆內容做成同尺寸卡片。手機版改成短水平導言，保留與直排帶相同的內容意圖，但不把長直排擠進窄螢幕；導覽縮成按鈕加抽屜，檔案列改為單欄閱讀順序，先題名與狀態，再摘要與採集資訊。

## Elevation & Depth

層次靠紙面深淺、邊線與留白建立，不靠漂浮卡陰影。主閱讀面與索引帶使用不同底色，像同一個檔案盒中的分隔頁。臨時表層只有 mobile 導覽抽屜，使用深色遮罩與單一 raised surface，避免多重材質混用。

## Shapes

整體形狀語言偏直線、檔案標籤切角與細邊框，對應錄音帶標籤與索引卡。大多數容器保持接近方正，只讓主要面板與按鈕有小半徑，避免把內容做成柔軟的通用卡牆。直排索引帶維持硬邊，作為整頁最像「檔案分頁」的識別構件。

## Components

`page-shell` 是所有頁面與區塊的共同閱讀底。`archive-panel` 承載檔案摘要、欄位與逐字節錄，桌機與手機都沿用相同面板語意，但重排其欄位順序。`vertical-ribbon` 專門放地名、索引與直排節錄；手機不保留直排，而改用同內容意圖的水平導言。`button-primary` 只用於明確下一步，如跳到可聆聽檔案。`utility-chip` 用於主題、語言與導覽輔助，不充當主要按鈕。`rule-label` 用於座標、權利與狀態標示；更細的邊線、背景紋理與 responsive 排法維持在實作層，不寫入 token frontmatter。

## Do's and Don'ts

- Do 讓題名、講者、摘要、採集資訊與權利條件各自有清楚欄位與閱讀順序。
- Do 在桌機保留直排索引帶，在手機改寫成短水平等價內容。
- Do 讓可聆聽與不可播放狀態被明確區分，並以文字說清楚原因。
- Don't 把全部錄音做成同尺寸卡片或假播放器。
- Don't 用英雄區漸層、發光或 SaaS 指標牆取代真實檔案內容。
