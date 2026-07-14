---
version: alpha
name: 城市詩祭設計系統
description: 面向一般讀者的城市詩祭探索網站視覺契約。以鉛字排印、詩刊留白與節目摺頁美學為基礎，呈現明確編輯判斷，內容先行。
colors:
  primary: "#1A1714"
  on-primary: "#F5F0E8"
  secondary: "#6B3A2A"
  on-secondary: "#F5F0E8"
  surface: "#F5F0E8"
  on-surface: "#1A1714"
  surface-alt: "#EDE7D9"
  on-surface-alt: "#1A1714"
  accent: "#8B1A1A"
  on-accent: "#F5F0E8"
  muted: "#5C5248"
  border: "#C8BFB0"
  focus: "#8B1A1A"
typography:
  display:
    fontFamily: "Georgia, '標楷體', 'DFKai-SB', serif"
    fontSize: 56px
    fontWeight: "700"
    lineHeight: 1.05
    letterSpacing: -0.02em
  headline:
    fontFamily: "Georgia, '標楷體', 'DFKai-SB', serif"
    fontSize: 32px
    fontWeight: "700"
    lineHeight: 1.2
    letterSpacing: -0.01em
  subheading:
    fontFamily: "'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 18px
    fontWeight: "600"
    lineHeight: 1.4
  body:
    fontFamily: "'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 1.75
  caption:
    fontFamily: "'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 13px
    fontWeight: "400"
    lineHeight: 1.5
  nav:
    fontFamily: "'PingFang TC', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif"
    fontSize: 15px
    fontWeight: "500"
    lineHeight: 1.4
  vertical-display:
    fontFamily: "Georgia, '標楷體', 'DFKai-SB', serif"
    fontSize: 22px
    fontWeight: "700"
    lineHeight: 1.8
    letterSpacing: 0.05em
rounded:
  none: 0px
  sm: 2px
  md: 4px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
  xxl: 96px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.nav}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm} {spacing.md}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    typography: "{typography.nav}"
    rounded: "{rounded.none}"
    padding: "{spacing.sm} {spacing.md}"
  event-record:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "{spacing.lg}"
  nav-global:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.nav}"
    rounded: "{rounded.none}"
    padding: "{spacing.md}"
  status-available:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.secondary}"
    typography: "{typography.caption}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs} {spacing.sm}"
  status-full:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.muted}"
    typography: "{typography.caption}"
    rounded: "{rounded.sm}"
    padding: "{spacing.xs} {spacing.sm}"
---

# 城市詩祭設計系統

## Overview

城市詩祭探索網站服務一般詩文讀者，以手機或桌機探索詩人、場地、日期與活動。視覺語言取材鉛字排印、詩刊留白與節目摺頁：奶白底紙、深墨文字、暗紅點綴，讓內容本身承擔識別責任。密度隨版面節奏起伏——直排詩題、橫排活動索引、大段留白——以編輯判斷取代裝飾性模板。

個性詞對：沉靜、精確；拒絕浮誇。

## Colors

**語義角色**

- `primary`（#1A1714）：深墨黑。用於導覽底色、主要文字、強調邊線。
- `on-primary`（#F5F0E8）：奶白。用於深色底上的文字與圖標。
- `secondary`（#6B3A2A）：磚紅棕。用於詩人姓名、分類標籤的輔助色調。
- `accent`（#8B1A1A）：暗紅。唯有可互動動作時出現（連結 hover、焦點環、報名按鈕）。
- `surface`（#F5F0E8）：奶白底紙。頁面畫布。
- `surface-alt`（#EDE7D9）：略深奶白。交替列、區塊分隔。
- `muted`（#5C5248）：褪墨灰。次要資訊、元資料、已截止狀態。
- `border`（#C8BFB0）：淺棕邊線。細格線，模擬印刷分欄規。
- `focus`（#8B1A1A）：焦點環色，與 accent 一致。

色彩規則：彩度只在使用者可操作時出現（暗紅 accent）。頁面其餘部分保持低彩度印刷色調。

## Typography

**角色分工**

- `display`：中文大標，使用方楷或 Georgia，傳達詩刊封面感。
- `headline`：活動標題與章節標題，同字族較小尺寸。
- `subheading`：無襯線，導覽分組、欄位小標。
- `body`：無襯線，活動摘要，行高 1.75 保留中文呼吸空間。
- `caption`：元資料（日期、場地、名額）行內標籤。
- `nav`：全域導覽與按鈕，中等字重，固定尺寸。
- `vertical-display`：直排詩題區，楷體或 Georgia，字距略寬以配合直排節奏。

不使用大寫英文眉批作為主要層次裝置。中文標題不強制字距拉開。

## Layout

**桌機**：單頁三段佈局。頂部固定導覽（64px）、中央 1200px 最大寬度內容區、全幅頁尾。活動索引採用雙欄非等寬網格（左欄 2fr 活動列表、右欄 1fr 直排詩題插件）。直排區域與活動列表並列，形成直排／橫排視覺對話。

**Mobile 轉換**：
- 直排詩題區轉為水平短詩句帶（橫式，保留文字直立）。
- 雙欄收合為單欄，活動列表優先。
- 全域導覽收入漢堡選單抽屜。
- 每個活動 record 僅顯示核心資訊，隱藏次要欄位以保持可掃視性。

內容行長最大 `68ch`，避免中文在寬螢幕過度延伸。

## Elevation & Depth

以筆墨邊線與色調差分層：

- 活動 record 間用 `1px border-bottom` 分隔，無浮起陰影。
- 導覽固定時加 `border-bottom: 2px solid primary` 強調邊界。
- 互動 hover 以背景色切換至 `surface-alt` 表達。
- 無裝飾性卡片陰影或玻璃效果。

## Shapes

全站幾何：方正，`rounded: none` 為預設。活動狀態小標籤允許 `rounded: sm`（2px）作為最大弧度，模擬印章切角。不使用大圓角、pill 或 blob。

## Components

**event-record**：活動索引的基礎單元。以橫線分隔，非浮起卡片。桌機展示詩人、標題、日期、場地、簡介、名額狀態；mobile 縮減為標題、日期、場地、狀態。每個 record 必須有 `data-eval="record"` 與唯一 `data-record-id`。

**nav-global**：深墨底奶白字固定頂欄。含品牌名稱（左）、主要連結（右）。Mobile 收折時顯示漢堡按鈕（`data-eval="mobile-nav-toggle"`）。焦點環用 accent 色，確保在深色底上對比可辨。

**status badge**：名額狀態標籤。「尚有名額」用 secondary 色，「名額已滿」用 muted 色；非僅依賴顏色，同時以文字傳達狀態。

**vertical-type region**：`data-eval="vertical-type"`，`writing-mode: vertical-rl`，字元直立（`text-orientation: upright`）。桌機呈現 3–4 行直排詩句，與活動列表並列；mobile 轉為水平短句帶，或以 `writing-mode: horizontal-tb` 等價呈現，不把長直排硬塞進窄螢幕。

## Do's and Don'ts

- Do 以邊線、留白、型別層次表達視覺深度，不用浮起陰影卡片。
- Do 讓直排區域與橫排索引形成排版對話，不把直排當純粹裝飾。
- Do 確保狀態資訊同時有顏色與文字兩種冗餘呈現。
- Do 在 mobile 使用真正的構圖轉換，不只是 `flex-direction: column`。
- Don't 使用外部字型、圖片或網路請求。
- Don't 把 dashboard KPI、定價、見證、裝飾漸層 hero 引入編輯內容網站。
- Don't 讓按鈕、日期、場地文字意外換行或溢位。
- Don't 宣稱未實際執行的畫面、WCAG 或互動驗證。
