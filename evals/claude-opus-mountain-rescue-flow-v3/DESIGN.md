---
version: alpha
name: 山域救援任務協調台
description: 高密度救援指揮工作台的視覺契約，急迫度、任務階段與時限為獨立語意。
colors:
  primary: "#1F5C4D"
  on-primary: "#F4F7F5"
  canvas: "#12181B"
  surface: "#1A2226"
  surface-raised: "#222E33"
  ink: "#E8EEEB"
  muted-ink: "#9FB0AA"
  border-subtle: "#2E3C41"
  focus: "#7FD4B8"
  priority-critical: "#E8B04B"
  priority-high: "#C9CE6E"
  priority-routine: "#7FA6A0"
  status-standby: "#8FA4AC"
  status-active: "#5FB0C9"
  status-recovery: "#9E86C4"
  due-overtime: "#D8603C"
  due-tight: "#C9A24B"
  due-clear: "#6E8F86"
typography:
  page-title:
    fontFamily: "system-ui, -apple-system, PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif"
    fontSize: 26px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: 0em
  section-label:
    fontFamily: "system-ui, -apple-system, PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif"
    fontSize: 13px
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: 0.02em
  body:
    fontFamily: "system-ui, -apple-system, PingFang TC, Noto Sans TC, Microsoft JhengHei, sans-serif"
    fontSize: 15px
    fontWeight: 400
    lineHeight: 1.6
  data:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.4
    fontFeature: "tnum"
rounded:
  sm: 4px
  md: 8px
spacing:
  xs: 6px
  sm: 10px
  md: 16px
  lg: 24px
components:
  nav-item:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.section-label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  summary-cell:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink}"
    typography: "{typography.data}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  record-row:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  action-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.section-label}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
---

# 山域救援任務協調台

## Overview

這是登入後的救援指揮工作台，供指揮員同時監看多個責任區的任務。核心任務是「比較」：在數十筆任務間快速掃讀急迫度、通訊狀態、任務階段、時限與隊伍負荷，並判斷下一步指派。

個性克制、精準、耐候。視覺語彙取自地形圖、無線電通訊與現場標記，而非行銷語言。密度高，但以安靜的分區與對齊維持可掃讀性。此工作台不使用大型 hero、行銷 CTA、pricing、testimonials 或裝飾性卡牆。

## Colors

底色為低反光的深墨綠灰 `canvas`，模擬夜間指揮台螢幕，長時間監看不刺眼。`surface` 與 `surface-raised` 以微弱明度差表達分層，避免每張卡片都投影。

顏色的核心規則是三個獨立語意維度不得互相染色：

- **急迫度（priority）** 使用暖中性階：`priority-critical`（琥珀）、`priority-high`（黃綠）、`priority-routine`（灰綠）。表示任務本身的重要程度。
- **任務階段（status）** 使用冷色相：`status-standby`（灰藍）、`status-active`（青）、`status-recovery`（紫）。表示任務生命週期，與急迫度正交。
- **時限（due）** 只有超時或逼近才升溫：`due-overtime`（橙紅，僅代表真正超時的危險）、`due-tight`（逼近時限的黃）、`due-clear`（充裕的靜綠）。

橙紅 `due-overtime` 是唯一的危險色，僅在真正超時時出現，絕不用於一般急迫度或階段。每個維度除顏色外都附文字標籤與形狀（圓點／方點／斜線），不以顏色為唯一線索。`focus` 為高明度青綠，於任何表面上皆清晰可見。

## Typography

`page-title` 為頁面標題；`section-label` 用於導覽、欄位標頭與按鈕，維持一致的功能聲音。`body` 為任務描述與地名等閱讀文字。`data` 為等寬字體，用於座標、時間、頻率與隊伍數，啟用 `tnum` 使數字在欄位間精確對齊比較。

繁體中文使用 PingFang TC／Noto Sans TC 字族，避免簡體字形混入。不對中文段落施加正值字距，不使用裝飾性英文大寫小標。短標籤與狀態文字以 `white-space: nowrap` 保持單行，不換行、不裁切。

## Layout

Desktop 為固定側邊導覽 + 主工作區的殼層。主工作區上方為頁面標題與摘要格，下方為任務比較表，利用寬度做橫向比較：責任區、急迫度、階段、時限、隊伍、座標並排對齊，數字欄右對齊。內容寬度隨視窗延展，但欄位以 `minmax()` 維持關係。

Mobile 重新構成為「任務優先 inbox」：側邊導覽收合為頂部精簡列與 modal 選單（`mobile-nav-toggle`）；任務表捨棄橫向欄位，改為依急迫度與時限排序的堆疊卡片，每卡以徽章重新表達三個語意維度，次要座標與頻率移入摘要行。這不是縮小的 desktop 表格，而是不同的閱讀與操作順序。

## Elevation & Depth

以明度分層與 `border-subtle` 表達層級，不濫用陰影。僅 modal 選單使用 scrim 與單一陰影表示暫時浮起。表格列以極淡的交替底色與邊界區隔，維持掃讀節奏。

## Shapes

方正、克制的幾何，圓角僅 `sm` 與 `md` 兩級，呼應地圖網格與現場標記牌的直角語言。語意徽章以小圓點、方點、斜線區分維度，形狀本身即為非顏色線索。

## Components

`nav-item` 為導覽項目，具 current 狀態（左側 `focus` 色標記與加深底色）。`summary-cell` 為摘要格，顯示彙總數字，不取代任務列表。`record-row` 為單筆任務容器，桌機為表格列、行動裝置為卡片，但共用同一語意來源與 `data-record-id`。`action-primary` 為主要操作按鈕。

hover、focus、current 等變體以獨立命名與 `border`／底色表達；邊框、陰影與 modal 行為記於本文，不寫入 token frontmatter。徽章顏色一律搭配文字標籤與形狀。

## Do's and Don'ts

- Do 讓急迫度、階段、時限三個維度各自使用其色階與非顏色線索，維持語意正交。
- Do 讓 desktop 以橫向欄位比較、mobile 以優先排序 inbox 重構，共用單一任務資料來源。
- Don't 用橙紅 `due-overtime` 表達一般急迫度或階段；它只代表真正超時的危險。
- Don't 加入 hero、行銷 CTA、玻璃擬態、霓虹漸層或滿版紅色警報。
