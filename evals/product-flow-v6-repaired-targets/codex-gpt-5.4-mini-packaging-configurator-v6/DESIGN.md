---
version: "alpha"
name: "循環包材三頁配置器"
description: "以工業打樣、模切線與循環材料標記建立三頁式繁體中文配置器。"
colors:
  canvas: "#F6F2EA"
  surface: "#FFFFFF"
  surface-strong: "#E9E2D7"
  text: "#1B1F23"
  text-muted: "#4B535B"
  primary: "#234B46"
  on-primary: "#FFFFFF"
  accent: "#355E2A"
  on-accent: "#FFFFFF"
  warning: "#E8C65A"
  on-warning: "#1B1F23"
  border: "#B9B0A1"
typography:
  display:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", system-ui, sans-serif"
    fontSize: 40px
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.03em"
    fontFeature: "\"kern\", \"liga\""
  body:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "0em"
    fontFeature: "\"kern\""
  label:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", system-ui, sans-serif"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "0.02em"
    fontFeature: "\"tnum\", \"kern\""
  mono:
    fontFamily: "\"SFMono-Regular\", \"SF Mono\", \"Menlo\", \"Consolas\", \"PingFang TC\", \"Noto Sans TC\", monospace"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.5
    letterSpacing: "0em"
    fontFeature: "\"tnum\", \"kern\""
rounded:
  none: "0px"
  md: "16px"
  lg: "24px"
  pill: "999px"
spacing:
  page: "24px"
  card: "16px"
  panel: "20px"
  button: "12px"
  chip: "8px"
  line: "1px"
components:
  canvas-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.text}"
    typography: "{typography.body}"
    padding: "{spacing.page}"
  panel-surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.panel}"
  elevated-panel:
    backgroundColor: "{colors.surface-strong}"
    textColor: "{colors.text}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.card}"
  display-banner:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    typography: "{typography.display}"
    rounded: "{rounded.md}"
    padding: "{spacing.card}"
  primary-action:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "{spacing.button}"
  secondary-action:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "{spacing.button}"
  selection-chip:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "{spacing.chip}"
  support-note:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-muted}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "{spacing.card}"
  code-pill:
    backgroundColor: "{colors.surface-strong}"
    textColor: "{colors.text}"
    typography: "{typography.mono}"
    rounded: "{rounded.pill}"
    padding: "{spacing.chip}"
  warning-callout:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.on-warning}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.card}"
  separator:
    backgroundColor: "{colors.border}"
    rounded: "{rounded.none}"
    height: "{spacing.line}"
---

# 循環包材三頁配置器

## Overview

這組三頁工具面向包裝工程、採購、永續與打樣協作角色，核心任務是把尺寸、用途、材質與回收條件放在同一個決策面上。視覺語法採精準、克制、可追蹤的工業打樣語言，使用模切線、標記框、量測尺規與回收標籤感，讓配置不是看起來像行銷頁，而是像一個可反覆檢查的工作面。

概念句：循環包材的尺寸與材質以打樣尺規與材料標記被一起讀懂，讓使用者能快速比對、看見衝突，並回到可回收方案。

## Colors

色彩只做三件事：承載工作面、標示可操作點、提醒可恢復衝突。

- `canvas` 與 `surface` 形成安靜的紙張底，讓尺寸和材質先被讀見。
- `primary` 只用在目前可執行的主動作，例如前往下一頁或套用修正。
- `accent` 只用在選取狀態與回收標記，代表使用者已確定的方案，不代表警告。
- `warning` 只用在可恢復衝突，語意是「要調整」，不是「已失敗」。
- `border` 與 `surface-strong` 用於模切線、框線與層次，不承擔情緒。

色彩不做證書、徽章或認證 logo 的偽裝；回收資訊必須用文字與結構說明，不靠圖樣裝飾冒充背書。

## Typography

字體角色分成四層：

- `display` 用於頁名、段落標題與測量感較強的數字，維持精準、簡短、可掃描。
- `body` 用於說明、條件、提示與回收註記，保留繁中閱讀舒適度。
- `label` 用於選項名稱、按鈕、狀態標籤與導覽，讓控制面在小尺寸下仍能明確。
- `mono` 用於尺寸、價格、規格與比例數字，讓比對更穩定。

繁中內容一律維持直排外的水平閱讀；所有長文保持正常斷行，不把中文擠成單字元窄欄。短標題可在桌機展現 1 到 2 行，手機則優先保住可讀 measure 與按鈕可點擊性。

## Layout

版面是單一共用 shell，三頁共享同一個頭部、導覽與內容欄寬。桌機使用左右結構，讓導覽、狀態與內容可以同時存在；手機改為垂直流，先看標題與當前配置，再看選項，最後才是次要說明。

主要區塊的順序固定為：品牌與導覽、當前配置摘要、主操作區、補充說明。首頁先處理尺寸與用途；材質頁先處理材質選擇與衝突回復；摘要頁先展示價格與衝突，再提供重設與回退。

手機版的摘要區改成貼近拇指的可操作區域，但必須留在正常文件流中，不用固定或黏住的浮層遮住尺寸、用途或材質內容。若需要強調操作，改用同頁內的按鈕列與足夠間距，而不是把 summary 疊到內容上。

## Elevation & Depth

深度只來自三種來源：框線、底色差與局部高亮。大部分面板保持平面，避免每張卡都像漂浮元件。當內容需要注意時，用 `surface-strong` 或 `warning` 拉出層次，讓衝突、選取與成功狀態可直接比對。

陰影只做很輕的結構提示，不做戲劇化效果。這個產品的可信感來自量測與對齊，不來自玻璃、霓虹或濾鏡。

## Shapes

形狀語言以直角與中等圓角為主，像模切版、標籤與工業樣板。角落不做過度柔化，保持可追蹤的邊界。頁首的圓環與標記刻度是唯一的產品專屬視覺記號，象徵材料循環、回收路徑與配置狀態的連動。

## Components

- `canvas-shell` 作為整頁底層，承擔背景、文字與基礎內距。
- `panel-surface` 與 `elevated-panel` 用於選項、摘要與說明，分別代表主要內容與次級內容。
- `display-banner` 用於頁首的主標與量測圖示區。
- `selection-chip` 用於目前已選尺寸、用途與材質。
- `primary-action` 與 `secondary-action` 分別代表前進與回退、套用修正與重設。
- `warning-callout` 用於可恢復衝突，內文必須同時說明原因與修正方向。
- `separator` 只做節點分隔，不承擔語意。

選項元件在桌機與手機維持相同語意，不複製兩套 DOM。每個選項都要有明確的選取、聚焦、停用與錯誤表現；衝突訊息在狀態解除後必須即時消失。
手機上的 summary 與動作列以正常流程排列，必要時可以靠近拇指區，但不應蓋住前面的標題、選項或說明。

## Do's and Don'ts

- Do 保持同一份配置狀態跨頁傳遞，並同步到網址與本機儲存。
- Do 用文字與結構說明材質、用途與回收條件。
- Do 在手機上保留可操作區域與安全邊界，不要用浮層蓋掉內容。
- Do 讓衝突可以被修正，而不是只顯示警報。
- Don't 偽造認證 logo、獎章或第三方背書。
- Don't 把手機版做成桌機簡單堆疊。
- Don't 在未確認的情況下宣稱環保、回收或價格結論已被外部驗證。
- Don't 讓衝突訊息或成功狀態在修正後殘留。
