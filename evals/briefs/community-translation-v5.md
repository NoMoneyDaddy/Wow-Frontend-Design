# Community translation workbench brief

為地方防災資訊建立一個繁體中文介面的社群翻譯審校工作台。審校者需要比較繁體中文、英文與阿拉伯文段落，處理術語、方向性與數字混排問題，再決定是否標記為可交付。這是離線模擬資料，不是正式警報發布工具。

## 核心任務

畫面包含 6 個翻譯片段，至少涵蓋避難所地址、開放時間、緊急電話、用水提醒、藥物清單與寵物安置。預設顯示全部片段；可篩出 3 個「需審校」片段。每筆同時呈現來源繁中、英文譯文、阿拉伯文譯文與狀態，不能用 hover 才能看完整內容。

使用者可開啟第一個需審校片段的檢視面板，比較術語說明與修訂建議，再關閉返回列表。介面不可真的改動或發布警報。

## 雙向文字與排版

- 文件使用 `lang="zh-Hant"`；英文區段標示適當 `lang`，阿拉伯文區段必須使用 `lang="ar" dir="rtl"`。
- 電話、時間、路名編號與括號在 RTL 段落中仍應可讀，不可用反轉字串或 transform 假造。
- 中文、拉丁字與阿拉伯字的 fallback 字體要合理；不能靠遠端 webfont。
- 桌機允許並排比較，手機必須轉為清楚的閱讀順序，不能產生水平捲動或截字。
- 狀態不能只靠顏色；長句換行、段落行高與組件間距要支援逐句比對。

## 固定評測掛鉤

- 工作台：`data-eval="translation-workbench"`。
- 篩選群組：`data-eval="issue-filter"`。
- 「全部」控制：`data-filter-value="all"`；「需審校」控制：`data-filter-value="needs-review"`。
- 每個片段：`data-eval="translation-segment"` 與唯一 `data-segment-id`；預設 6 筆，篩選後 3 筆可見。
- 每個阿拉伯文內容：`data-eval="rtl-copy"`，並保留 `lang="ar" dir="rtl"`。
- 第一個需審校片段的開啟控制：`data-eval="open-review"`，使用 `aria-expanded` 與 `aria-controls`。
- 檢視面板：`data-eval="review-panel"`，初始不可見，開啟後可見。
- 關閉控制：`data-eval="close-review"`。

## 限制

- 不使用外部套件、網路資產或 network request。
- 不宣稱翻譯正確、法律有效、已發布、已保存或已通過人工審校。
- 沒有獨立瀏覽器證據時，不得宣稱雙向文字、響應式、可用性或 WCAG 已通過。
