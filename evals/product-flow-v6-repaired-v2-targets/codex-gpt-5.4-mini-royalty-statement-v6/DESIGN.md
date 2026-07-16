---
version: alpha
name: 獨立音樂版稅結算
description: 繁體中文單頁版稅工作台，以對帳單與節拍網格呈現來源、期別切換與異常提醒。
colors:
  canvas: "#F6F0E7"
  surface: "#FFFDF9"
  surfaceRaised: "#EDE4D7"
  ink: "#1A1613"
  muted: "#D9D0C5"
  border: "#C7B9A5"
  primary: "#BFDCD6"
  primaryInk: "#1A1613"
  success: "#D9E8D8"
  warning: "#F0DEB7"
  danger: "#F2D3D8"
  data1: "#D6E4F2"
  data2: "#EFD8C8"
  data3: "#E4DFB8"
  data4: "#E1D6EF"
  data5: "#D7E9E4"
  data6: "#EEDCCF"
typography:
  display:
    fontFamily: "'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 42px
    fontWeight: 700
    lineHeight: 1.12
    letterSpacing: "0em"
    fontFeature: "'tnum' 1"
    fontVariation: "normal"
  reading:
    fontFamily: "'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "0em"
    fontFeature: "'tnum' 1"
    fontVariation: "normal"
  functional:
    fontFamily: "'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0em"
    fontFeature: "'tnum' 1"
    fontVariation: "normal"
  numeric:
    fontFamily: "ui-monospace, 'SFMono-Regular', 'SF Mono', Menlo, Consolas, monospace"
    fontSize: 16px
    fontWeight: 500
    lineHeight: 1.1
    letterSpacing: "0em"
    fontFeature: "'tnum' 1"
    fontVariation: "normal"
spacing:
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
rounded:
  sm: 10px
  md: 16px
components:
  page-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.reading}"
    rounded: "{rounded.md}"
    padding: "{spacing.xl}"
  surface-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.reading}"
    rounded: "{rounded.md}"
    padding: "{spacing.xl}"
  surface-raised:
    backgroundColor: "{colors.surfaceRaised}"
    textColor: "{colors.ink}"
    typography: "{typography.reading}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primaryInk}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.lg}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.lg}"
  status-positive:
    backgroundColor: "{colors.success}"
    textColor: "{colors.ink}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  status-warning:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.ink}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  status-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.ink}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  chip-muted:
    backgroundColor: "{colors.muted}"
    textColor: "{colors.ink}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  chart-mark-1:
    backgroundColor: "{colors.data1}"
    textColor: "{colors.ink}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  chart-mark-2:
    backgroundColor: "{colors.data2}"
    textColor: "{colors.ink}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  chart-mark-3:
    backgroundColor: "{colors.data3}"
    textColor: "{colors.ink}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  chart-mark-4:
    backgroundColor: "{colors.data4}"
    textColor: "{colors.ink}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  chart-mark-5:
    backgroundColor: "{colors.data5}"
    textColor: "{colors.ink}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  chart-mark-6:
    backgroundColor: "{colors.data6}"
    textColor: "{colors.ink}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  rule-strip:
    backgroundColor: "{colors.border}"
    textColor: "{colors.ink}"
    typography: "{typography.functional}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
---

# 獨立音樂版稅結算

## Overview

這個工作台給音樂人、經紀與版權協作者一個可直接對帳的單頁介面。內容重點是期別切換、六筆來源的同欄比較、一筆異常款項與可點開的資料點說明。

視覺語氣介於唱片內頁與會計對帳單之間：乾淨、克制、帶有節拍感。數字先於裝飾，說明先於效果，所有辨識都要在鍵盤、觸控與窄螢幕下保持完整。

## Colors

`canvas` 是整頁底色，帶一點紙張暖度，讓版稅數字像印在工作底稿上，而不是漂浮在無關的黑盒子裡。

`surface` 用於主要內容面，`surfaceRaised` 只用在需要暫時抬升的區塊，例如摘要或被選取的資料點說明。兩者都維持低彩度，避免每一塊都像獨立卡片。

`ink` 是主要文字與數字色。`muted`、`border` 只負責次要底面、分隔與節拍線，不能取代內容層級。

`primary` 是本期與主要動作的強調色。它只用在目前被選取的期別、主要按鈕與焦點呼叫，不拿來當背景裝飾。

`success`、`warning`、`danger` 分別對應正向入帳、待確認異常與負向風險。這些狀態都要搭配文字或標記，不靠顏色單獨傳意。

`data1` 到 `data6` 是六筆來源的固定資料色。它們用在圖表與對應圖例，確保同一來源在不同期別之間仍可被辨識，但資料解讀仍需看數字與標籤。

## Typography

`display` 用在總額與頁面主標，尺寸大但行高緊湊，維持像唱片封面裡的標題區。

`reading` 用在段落、說明與來源描述，保持長句與繁中標點的可讀性。

`functional` 用在期別切換、標籤、次要按鈕與欄位名稱，強調清楚而不是搶眼。

`numeric` 用在金額、百分比與對帳欄位，採等寬數字與穩定字寬，讓正負數和小數點能在掃讀時對齊。

整體以繁體中文為主，保留長來源名、混合數字與單位的自然換行。短標籤維持橫排，避免把控制文字壓成窄欄直排。

## Layout

桌面版採左主右輔的對帳版面：左側是圖表與來源列表，右側是總額、期別切換與異常摘要。這讓比較與決策可以同時看見。

主標在桌面上保留完整寬度，和導語共用同一條起始軸；期別切換改為右側對齊的第二焦點，避免標題被過窄欄位截斷。

手機版改成單欄順序：標題與期別切換先出現，總額緊接其後，再是圖表與來源列表。最重要的動作留在拇指可及範圍，副資訊延後。

節拍線、分隔線與欄位對齊比厚重容器更重要。列表保持開放式排版，不把每一筆都包成同樣的浮起卡片，避免資訊平坦化。

| 區塊 | 桌面角色 | 手機對應 | 順序 | 互動 | 延後／移除 |
| --- | --- | --- | --- | --- | --- |
| 期別切換 | 立即切換本期與上期 | 置頂群組按鈕 | 1 | 點擊／鍵盤切換 | 不延後 |
| 總額摘要 | 主要決策數字 | 首屏大數字 | 2 | 隨期別即時更新 | 不移除 |
| 來源圖表 | 快速看分布與佔比 | 單欄堆疊圖表 | 3 | 點按或聚焦開啟說明 | 無 |
| 來源列表 | 逐筆對帳與比較 | 單列記錄 | 4 | 掃讀、比較、確認 | 不刪除欄位 |
| 異常款項 | 獨立提醒與人工核准 | 列表末端的獨立卡 | 5 | 閱讀與後續處理 | 不併入一般來源 |

## Elevation & Depth

深度只用來表達暫時性與選取狀態。一般區塊只靠底色、邊界與間距分層。

異常款項與資料點說明可比其他區塊略高一層，但仍保留紙感與對帳單的平面語氣，不使用玻璃、霓虹或漂浮陰影做主題。

## Shapes

角落採中等圓角，像唱片內頁上被裁順的紙角。主按鈕與標籤略收斂，列表與圖表則保留更直的邊，讓數字與節拍線維持秩序。

異常標記、狀態徽章與圖表標籤可以更圓，但不把整個頁面變成膠囊集合。

## Components

期別切換是第一級控制元件，必須同步更新目前顯示的總額、圖表與來源欄位。選中狀態要有文字與底色雙重提示。

總額摘要是唯一需要被立即讀到的數字區塊。它用大字體、穩定數字寬度與清楚的期別標籤呈現，不插入無意義的關鍵指標裝飾。

來源列以單筆記錄為單位，保留來源名、地區、金額、差額與狀態。每筆都能獨立被掃讀，也能和圖表對照。

圖表資料點是可聚焦的按鈕。點擊、觸控或鍵盤聚焦都會把詳細說明送進資料點說明區，讓圖表不是純裝飾，而是可操作的摘要。

異常款項獨立於正常來源列呈現，使用更明顯的狀態標籤與說明文，避免被折進一般來源之中。

主標、導語與摘要文案都維持繁中詞序，不再混用未翻譯的介面英文字。

## Do's and Don'ts

- Do 讓本期與上期在同一欄位結構中切換。
- Do 讓圖表、列表與摘要共享同一組來源資料。
- Do 用數字、標籤與狀態一起表達資料，避免只靠顏色。
- Do 保留繁中語序、可讀的長來源名與可鍵盤操作的說明入口。
- Don't 把每個區塊都做成相同圓角卡片。
- Don't 用華麗特效遮住對帳的主線。
- Don't 在手機上只做簡單堆疊而不改變優先順序。
- Don't 讓異常款項只靠顏色被辨識。
