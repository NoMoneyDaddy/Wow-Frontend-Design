# Model evaluation fixtures

這些案例用來評測 `wow-frontend-design` 在不同模型上的行為，不是品質宣傳素材。Fixture validator 只證明資料結構與內部參照一致；只有實際 host/model integration run 才能證明 Skill activation 或 reference routing。

`playwright_dashboard_audit.cjs` 會重播固定 dashboard 的桌機／手機行為矩陣，不修改模型產物。以 repo 根目錄的 `package-lock.json` 安裝固定 Playwright 版本；使用系統瀏覽器時設定 `CHROME_EXECUTABLE_PATH`，再傳入 Haiku 與 Opus 的本機 URL。預設是 acceptance mode：任何互動失敗會非零退出，禁止 DOM click fallback。`--diagnostic` 才允許 fallback 以繼續觀察，但 verdict 永遠是 `diagnostic_only`。輸出的 JSON 是互動證據，不是視覺品質分數。

```bash
npm ci --ignore-scripts
CHROME_EXECUTABLE_PATH=/absolute/path/to/chrome npm run audit:dashboards -- \
  http://127.0.0.1:4178/ http://127.0.0.1:4179/
```

## 更新截圖與 hash 證據

截圖、capture script、Playwright lock 與來源檔案互相以 SHA-256 綁定。更新任何一項後，必須在同一個受控環境重新產生 manifest；不可手改 hash 讓 validator 變綠：

```bash
npm ci --ignore-scripts --no-audit --no-fund
python3 -m http.server 4175 --bind 127.0.0.1 --directory evals/weak-model-showcase
CHROME_EXECUTABLE_PATH=/absolute/path/to/chrome npm run capture:showcase -- http://127.0.0.1:4175/
python3 wow-frontend-design/scripts/validate_screenshot_manifest.py assets/screenshots.json --repository-root .
```

Dashboard replay 也必須以固定 brief、兩個原始 model artifact、相同瀏覽器與 `package-lock.json` 重跑。Acceptance 應保留真實非零 exit；diagnostic JSON 只能保存 continuation evidence。重算 `dashboard-browser-results.json` 的 hash 後，再跑 `validate_dashboard_evidence.py`。若無法重跑原始環境，就保留舊證據並明確標 stale／不可比較，不得只換 hash。

## 目前案例

- `trigger_cases.json`：Skill 是否應啟用，以及啟用後應載入哪些最小 reference 的 evaluator-owned 正／反例。`validate_trigger_cases.py` 只檢查 fixture schema、正反例集合、ID／locale 與 reference 檔案的 self-consistency；它不呼叫 host、模型或 router，也不證明實際 activation/routing。
- `product_cases.json`：把八個非 landing／跨產品案例固定成 evaluator-owned machine-readable definitions，涵蓋 surface、audience/task、品牌證據邊界、mobile transformation、hidden acceptance focus 與 `zh-Hant`/`en` 分布。`validate_product_cases.py` 只驗 schema 與 coverage；fixture 不含執行結果、模型成績、browser evidence 或 WCAG 結論。
- `weak-model-showcase/`：`gpt-5.4-mini` 從普通繁中選物頁進行 hostile retrofit。保留分類、收藏與表單，並接受外部桌機／手機瀏覽器測試。
- `claude-haiku-showcase/`：Claude 弱模型固定 brief 與隔離輸出目錄。
- `claude-opus-showcase/`：Claude 強模型的相同固定 brief 與隔離輸出目錄。
- `claude-{haiku,opus}-product-dashboard/`：共用 `briefs/product-dashboard.md` 的非 landing 產品 UI 原始產物與 run manifest；兩者目前都未通過 strict acceptance。
- `claude-haiku-product-dashboard-remake/`：唯一一次 anti-slop remediation invocation 的拒絕紀錄；輸出政策在 publish 前熔斷，沒有可接受網站產物。
- `benchmark-matrix.md`：上述八案的人類可讀來源與 controlled-comparison 規則；`product_cases.json` 是其 definition-only fixture。兩者列出案例都不等於執行或通過。
- `capability-status.json`：公開 claim ledger。每項能力都要有現存 artifact 與明示 boundary；validator 只確保狀態結構與路徑未腐化，不替內容升級證據。
- `dashboard-playwright-acceptance.json`：嚴格 acceptance replay；4/4 viewport 失敗，命令 exit 1，沒有 DOM click fallback。
- `dashboard-playwright-replay.json`：同案 diagnostic replay；可在真實 click 失敗後用 DOM click 繼續蒐集其他觀察，但永遠不能轉成通過。

本輪可重現結果與限制見 [`RESULTS.md`](RESULTS.md)。

只驗 fixture 結構與 coverage：

```bash
python3 wow-frontend-design/scripts/validate_product_cases.py evals/product_cases.json
```

這個命令成功只代表八個固定案例、必要欄位與 locale 分布自洽，不得轉述為任何模型完成案例或取得分數。

Claude 兩案必須使用相同 brief、skill 版本、工具權限、viewports、互動路徑與獨立 reviewer。連線或 runtime 問題要記為 infrastructure failure，不得換算為設計分數。

若 host 拒絕完整 Skill context，可另跑 `prompt-only-compact.md`，但必須標成 `compact-adapter` cohort 並記錄 hash。它不得替代或和 `full-skill` cohort 直接比較；context-limit rejection 也不得換算為模型設計分數。

Runner 預設以 `CLAUDE_AUTH_MODE=official` 清除繼承的 Anthropic API key/token/base URL、自訂 model/alias，以及 Vertex、Bedrock、Foundry 與其常見 provider credential/config 環境變數；不清除 `CLAUDE_CODE_OAUTH_TOKEN` 或本機 Claude.ai 登入狀態。它再以 `--safe-mode` 隔離 plugins、hooks、MCP 與自訂設定。只有在刻意評測自訂 API 環境時，才設 `CLAUDE_AUTH_MODE=inherited`；兩模型必須使用相同模式並記錄 provenance。

本地模型可加入矩陣，但每次開始前都要揭露 runtime、精確 model/quantization、來源授權、下載與 RAM/VRAM/storage、命令、network 行為、可讀／可寫資料及清理方式，並取得使用者當次明確同意。未同意時只能準備 fixture/evaluator；不得下載、啟動或呼叫模型。雲端與本地結果分 cohort 報告，禁止 silent fallback。

Claude runner 只給固定 `Write` 工具，在暫存空目錄產出恰好三個模型檔案；沒有 `Read`、`Edit`、`Bash` 或 network tool。Haiku/Opus 都收到相同 `CONSTRAINED` lane、trusted Skill revision 與 untrusted brief 邊界。產物通過 allowlist、size、HTML/CSS/JS resource-sink 檢查後才複製到固定目標；protocol-relative URL、外連／local resource、`@import`、meta refresh、form action 與常見動態 network/navigation sink 會 fail closed。受控評測可先建立 repo 外、evaluator-owned 目錄並設 `CLAUDE_REJECTED_OUTPUT_DIR=/absolute/path`；拒絕輸出會以 `0600` 保存，另附 reason、bytes 與 SHA-256。未設定時仍 fail closed，但 raw rejected output 不保留；quarantine 不能位於 repository 內。

既有 showcase 呼叫維持 `run_claude_case.sh <haiku|opus> <固定 showcase 目錄>`；其他固定案例使用 `run_claude_case.sh <haiku|opus> --case product-dashboard`。單次 remediation case 只允許 Haiku。新式呼叫不接受 target 路徑，runner 只依 `model × case` allowlist 導出輸出目錄；不得改用任意或 traversal 路徑。

成功執行另由 evaluator 產生 `run-manifest.json`，記錄 `run_id`、固定 case ID/target、auth mode、Claude CLI path/version、請求的 model alias、runner/brief/trusted context/output hashes 與清除的環境變數名稱。Claude CLI 若未回報 alias 實際解析到的完整 model ID，manifest 會明確記為 `not_reported_by_cli`，不猜測 resolved exact model。

## 防作弊原則

- 實作模型不得修改 evaluator-owned tests、schema 或預期條件。
- 靜態訊號只能證明原始碼存在；功能必須用瀏覽器結果驗證。
- 視覺盲審只看 brief、程式、screenshots 與 raw evidence，不看產生模型的自評。
- 只有經選定、附 provenance 且仍符合 claim boundary 的 screenshots／summaries 進 repo；raw traces、暫存報告與 rejected quarantine 留在 evaluator-owned repo 外目錄。提交的截圖不得被誤當 regression baseline 或品質分數。

`weak-model-showcase/.wow-evidence.json` 若仍存在於本機 checkout，是已由 `.gitignore` 排除的 legacy v1 scratch ledger；它位於 implementation workspace、含舊式絕對路徑，因此不屬 release evidence，也不得交給目前 scorer 當可信 ledger。新評測一律使用 repo 外 evaluator root，讓 `ledger.json`、`policy.json`、`artifacts/` 與唯一 model-writable 的 `workspace/` 分離，並在每次 ledger `run` 明示 `--cwd <evaluator-root>/workspace`。
