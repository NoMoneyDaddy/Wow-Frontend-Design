---
version: alpha
name: 社區文化補助審查台
description: 以繁體中文單頁工作台支援審查委員從待討論案件中加入 shortlist、比較兩案，並在本機模擬中送出決策。
colors:
  primary: "#23463E"
  on-primary: "#F7F3E9"
  surface: "#F4F0E8"
  on-surface: "#18231F"
  muted: "#56645F"
  danger: "#8E2F3B"
  on-danger: "#FFF6F7"
typography:
  display:
    fontFamily: "\"Baskerville\", \"Iowan Old Style\", \"Noto Serif TC\", \"Source Han Serif TC\", serif"
    fontSize: 52px
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "-0.01em"
  body:
    fontFamily: "\"PingFang TC\", \"Noto Sans TC\", \"Microsoft JhengHei\", system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "0em"
spacing:
  xs: 6px
  sm: 10px
  md: 16px
  lg: 24px
  xl: 32px
rounded:
  sm: 12px
  md: 18px
  lg: 28px
components:
  shell:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  section-heading:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.display}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  badge-muted:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.muted}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  badge-action:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  error-banner:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-danger}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
---

# Overview

這個系統服務的是文化補助審查委員，重點不是展示資訊量，而是把有限的判讀時間集中在可比較的證據上。整體氣質要像一份被仔細註記的評選檔案：冷靜、明確、可追溯，並且始終強調所有結果只是本機模擬。

## Colors

`surface` 是整體紙面與面板背景，`on-surface` 是主要閱讀文字，兩者形成穩定的工作底。`primary` 只給可立即採取的主動作、已選中的比較標記與關鍵確認狀態使用，避免讓每個元素都像可點擊操作。`muted` 只承擔次級資訊、時間、機構與註記，讓評語與證據層次分開。`danger` 與 `on-danger` 只出現在本機模擬錯誤與重試回饋，不拿來製造恐嚇感。

色彩規則是克制且明確的：紙色負責背景與表面，深墨綠負責動作，石墨灰負責說明，酒紅只負責錯誤。色彩不是情緒操作工具，而是狀態標記與閱讀分層工具。

## Typography

標題使用有書面感的襯線字重，讓工作台像審查檔案而不是一般 SaaS 面板；正文與控制項使用清晰的繁中無襯線字族，確保長句、數字與按鈕在桌機與手機都能穩定閱讀。說明文字保持正常字距，不用全大寫眉標，也不把中文做成追蹤字距的裝飾。`section-heading` 承接主標與區段標題，讓列表、比較面板與對話框的層級一致。

繁中內容以橫排為主，讓表單、比較、註記與操作順序保持自然。長姓名、地名、案名與備註都允許自然換行；必要時只對代號與短標籤做保護，不把整段文字鎖死。

## Layout

桌機以兩欄工作區組織：左側是六件申請案的審查列表，右側是比較面板與決策動作。每一列先用跨欄摘要承接申請案名稱與說明，再把預算、風險與動作放進第二層比較列，讓 prose 保持足夠寬的閱讀區，而不是被壓成狹窄的多欄文字。右側面板固定保留比較結果、短名單與送出控制，讓委員不用反覆來回捲動。

手機不是把桌機縮小成三欄窄字，而是改成逐案流程：一次只看一件申請案，透過前後切換在六案之間移動，接著加入 shortlist，再把兩案送入比較與決策。比較面板在手機上會落到當前案件之後，維持垂直步驟式摘要，決策按鈕仍在同一閱讀序列中。

## Elevation & Depth

深度主要透過紙面層次、邊線與留白建立，不靠大量陰影。主面板與對話框會比底色更實，讓焦點有明確邊界；錯誤與成功回饋使用獨立色塊，但不做玻璃或霓虹效果。因為內容本身就是證據，所以材質必須安靜。

## Shapes

形狀語彙偏向穩定、圓潤但不軟弱的圓角，對應文化場館、檔案註記與審查桌面。主按鈕、面板與對話框角半徑一致，讓互動零件有一致的組織感；比較標記與狀態徽章則更小、更緊湊，像手寫標籤而不是裝飾性膠囊。

## Components

工作區、列表列、比較標記、次要標籤、主按鈕、次要按鈕與錯誤橫幅都使用同一套色彩與字級關係。列表列是可操作的審查單元，不是純展示卡；短名單按鈕與比較按鈕要一眼可分辨，但仍維持同一份內容來源與狀態。

案件列在桌機上採上方摘要、下方資料列的分段排版；在手機上則只露出單一案件，搭配前後切換控制維持逐案審查節奏。這個轉換不新增另一份資料，也不複製另一套 DOM。

決策 modal 必須具名、可用鍵盤關閉、可返回焦點、並在錯誤後提供本機重試。重試狀態只表示本機模擬重新送出，不能暗示任何遠端成功或真實審批。

## Do's and Don'ts

- Do 以可比較的欄位、清楚的註記與穩定的狀態回饋支撐審查流程。
- Do 讓手機改成逐案閱讀與步驟式決策，而不是單純堆疊。
- Do 讓錯誤、重試與成功都保持冷靜而明示。
- Don't 把每一件案子都畫成同樣權重的卡片。
- Don't 用誇張警示、外部素材或假成果暗示真實送出。
- Don't 在介面中出現 evaluator、breakpoint 或設計流程說明。
