# 固定測試題 B：城市詩祭探索網站

建立繁體中文、面向一般讀者的城市詩祭探索網站。這是 editorial 內容網站，不是營運 dashboard、SaaS 後台或通用行銷模板。

## 使用者與視覺目標

- 使用者以手機或桌機探索詩人、場地、日期與活動內容。
- 視覺可取材城市詩刊、鉛字排印、節目摺頁與留白節奏；內容先行，呈現明確編輯判斷。
- 避免 dashboard KPI 牆、SaaS 側欄、pricing、testimonials、通用漸層 hero、假海報空框與裝飾性卡牆。

## 固定內容與外觀檢查點

- 使用 `lang="zh-Hant"`，呈現至少八個唯一活動，包含不同詩人、主題、場地、日期及名額狀態。
- 具備品牌／全域導覽、清楚內容入口、編輯式活動索引與可讀活動摘要；不可只剩相同卡片網格。
- 必須有一個真正的繁中直式排版區域，使用 `data-eval="vertical-type"` 與 `writing-mode: vertical-rl`。中文字保持直立，不可旋轉整個容器冒充直排。
- Desktop 明確呈現直排與橫排的關係；mobile 將該區轉為較短的水平等價構圖，不可把長直排硬塞進窄螢幕。
- 短按鈕、日期、場地與狀態文字不得意外換行、裁切或溢位。
- 每個活動容器使用 `data-eval="record"` 及唯一 `data-record-id`，供獨立視覺稽核比較 desktop／mobile 元件構成。
- 導覽使用 `data-eval="global-nav"`；若 mobile 有導覽按鈕，使用 `data-eval="mobile-nav-toggle"`。
- 所有資料只是靜態 demo。外觀驗證不要求報名後端、收藏同步或完整產品流程。

## 限制

- 不使用外部套件、網路資產或 network request。
- 沒有瀏覽器證據時，不得宣稱畫面、互動、可用性或 WCAG 已通過。
