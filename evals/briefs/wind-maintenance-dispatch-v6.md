# 離岸風場維修派工台

為台灣離岸風場的值班調度員建立繁體中文單頁工作台。主要任務是在天候窗口縮短時，從 8 筆維修工單找出 3 筆「緊急」，查看其中一筆，重新指派船班並取得明確的本機模擬成功狀態。

必須包含 `data-eval="dispatch-workspace"`、8 個唯一 `data-eval="dispatch-row"`／`data-record-id`、`data-filter-value="urgent"`、`data-eval="open-dispatch"`、`data-eval="reassign-action"` 與 `data-eval="status-message"`。表格或同等語意資料結構要能由鍵盤操作；桌機可為高密度 master-detail，mobile 必須改成單欄任務流，不得把詳情擠成窄側欄。需有 empty、error/retry 與 success 文案，但不得假稱真的同步船班。

視覺方向：海象儀表與航海圖的精準感，低彩度深藍灰搭配單一高辨識狀態色；避免通用 SaaS 卡片牆。
