# 社區文化補助審查台

為審查委員建立繁體中文單頁工作台。主要任務是從 6 件申請案篩選待討論案件、加入待選名單、比較兩案並開啟決策對話框；錯誤後可重試，所有結果都明示為本機模擬。

必須包含 `data-eval="grant-board"`、6 個唯一 `data-eval="proposal-row"`／`data-record-id`、`data-filter-value="discussion"`、每案的 `data-eval="shortlist-action"`、`data-eval="compare-a-action"` 與 `data-eval="compare-b-action"`、`data-eval="compare-panel"`、`data-eval="decision-action"`、`data-eval="decision-modal"`、`data-eval="retry-action"`。Mobile 必須提供 `data-eval="next-proposal"` 的逐案導覽，不得保留三欄窄文字。決策對話框要有可及名稱、focus containment、Escape、背景 inert／scroll lock 與 focus return。

視覺方向：評選表、註記與文化場館識別；權限與風險語氣冷靜，重要操作清楚但不過度警示。
