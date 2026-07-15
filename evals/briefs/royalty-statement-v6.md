# 獨立音樂版稅結算

為音樂人建立繁體中文單頁版稅工作台。使用者切換本期／上期、檢視 6 筆來源與一筆異常款項，並以鍵盤或 touch 開啟資料點說明。

必須包含 `data-eval="royalty-workspace"`、`data-period-value="current"`、`data-period-value="previous"`、6 個唯一 `data-eval="royalty-row"`／`data-record-id`、`data-eval="royalty-chart"`、至少 6 個有可及名稱的 `data-eval="chart-mark"`、`data-eval="anomaly"` 與 `data-eval="chart-tooltip"`。切換上期後總額與可見狀態必須更新。顏色不能是唯一資料編碼。

視覺方向：唱片內頁、會計對帳單與節拍網格；數字對齊、正負狀態與小型資料視覺優先，避免把 KPI 全做成相同卡片。
