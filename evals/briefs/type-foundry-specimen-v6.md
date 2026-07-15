# 繁中字體鑄造所樣張庫

為字體設計師建立繁體中文單頁樣張工具。使用者要切換橫書／直書，比較繁中標點、英文、數字與 fallback，並調整一個短樣張。必須包含 `data-eval="specimen-workspace"`、`data-eval="writing-toggle"`、`data-eval="specimen"`、`data-eval="fallback-note"` 與可鍵盤操作的 `data-eval="outline-toggle"`。

點擊 writing toggle 後，樣張必須真正在 `horizontal-tb` 與 `vertical-rl` 間切換，並同步更新 `aria-pressed`。鏤空字只能用在短展示文字；forced-colors 或不支援時要回到實心可讀字。mobile 若直書會破壞主要任務，必須提供明確退出／橫書策略，不能把正文壓成一字寬長柱。

視覺方向：鉛字樣本冊、校樣紙與精密框線；字體與字距是主角，特效不可套滿所有元件。
