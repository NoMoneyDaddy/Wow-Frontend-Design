# 循環包材三頁規格配置器

建立繁體中文三頁工具：`index.html` 配置尺寸與用途、`materials.html` 選擇材質與回收條件、`summary.html` 顯示價格與衝突摘要。三頁共用同一 DESIGN.md、root tokens、header/nav shell，且互相可達。

每頁都要有 `data-eval="configurator-shell"` 與跨頁導航。首頁要有 `data-eval="size-option"`、`data-eval="use-option"`、`data-eval="config-summary"`；材質頁要有 `data-eval="material-option"` 與 `data-eval="conflict-message"`；摘要頁要有 `data-eval="price-summary"`、`data-eval="reset-action"`。至少一種尺寸＋材質組合會顯示可恢復衝突。mobile summary 必須改成不遮住內容的可操作區域。

視覺方向：工業打樣、模切線與循環材料標記；框線與材質層次精準，禁止用 CSS 假造認證 logo。
