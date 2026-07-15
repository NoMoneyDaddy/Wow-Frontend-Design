# Model evaluation fixtures

這些案例用來評測 `wow-frontend-design` 在不同模型上的行為，不是品質宣傳素材。Fixture validator 只證明資料結構與內部參照一致；只有實際 host/model integration run 才能證明 Skill activation 或 reference routing。

## 最近發布的 v4 證據

最近一次固定 Codex cohort 共 9 個 target：三個 v4 主題 × `gpt-5.4-mini`、`gpt-5.4`、`gpt-5.5`。生成 9/9 完成、13 attempts、3 個 case 重試；官方 DESIGN lint 9/9 clean；Playwright 保留 30 張完整 PNG。更新後 auditor 對相同 HTML 的結果為 2/9 無 blocker、7/9 有觀察到的 blocker。

- `product-flow-v4-generation-results.json`：固定 Skill／brief、attempt history、target 與 manifest。
- `product-flow-v4-design-md-results.json`：pinned `@google/design.md@0.2.0` 結果。
- `product-flow-v4-visual-results.json`：viewport、auditor、runtime 與 visual findings。
- `product-flow-v4-targets/`：9 組原始 HTML、DESIGN 與 manifest。
- `../assets/product-flow-v4/`：README 展示用 30 張桌機／手機截圖；展示不等於 acceptance pass。

```bash
python3 wow-frontend-design/scripts/validate_product_flow_evidence.py \
  evals/product-flow-v4-visual-results.json --repository-root .
```

驗證器會拒絕被隱藏的 retry、stale manifest／DESIGN／PNG hash、錯誤尺寸、遺失或額外截圖，以及被改寫的 visual blocker。生成使用凍結的 pre-optimization Skill；現行 Skill 雖已吸收發現，尚未以相同 cohort 重跑。

## 本輪題型與後續政策

- 換掉 v4 三個主題；測不同產品功能、互動路徑與測試面向，不把舊案換皮重跑。
- 執行前先研究現代網頁的設計感、字體編排、層級、材質、動效節制與響應式呈現，再把來源轉成可驗證規則。第一個方法論案例是 [Design Skill Comparison Lab](https://designskill.qiaomu.ai/)；只採用其題型分離、實際互動與雙軌評估思路，不照搬作者分數。
- 第一批只跑 `gpt-5.4-mini`、`gpt-5.4` 與 Claude Haiku；Codex 與 Claude 分 provider cohort 執行、分開報告，不混成直接排名。
- 截圖用於 README 的功能／成果展示；測試報告仍分開列出 blocker，不能以好看的截圖取代 acceptance。
- 新一輪完成後才替換 README 的「最近一次」結果與圖；舊報告保留其凍結 Skill 與 evaluator provenance。

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
- `briefs/{harbor-cold-chain,island-sound-archive,plant-swap-one-line}-v4.md`：高密度操作、editorial archive 與低資訊多頁社區三個互相錯開的測試方向；hash 固定在新一輪 generation ledger。
- `claude-haiku-product-dashboard-remake/`：唯一一次 anti-slop remediation invocation 的拒絕紀錄；輸出政策在 publish 前熔斷，沒有可接受網站產物。
- `benchmark-matrix.md`：上述八案的人類可讀來源與 controlled-comparison 規則；`product_cases.json` 是其 definition-only fixture。兩者列出案例都不等於執行或通過。
- `capability-status.json`：公開 claim ledger。每項能力都要有現存 artifact 與明示 boundary；validator 只確保狀態結構與路徑未腐化，不替內容升級證據。
- `../wow-frontend-design/scripts/{site_manifest,wireframe_plan}.example.json`：有效的 IA／wireflow 契約範例；`validate_site_plan.py` 會連同本機 XML sitemap 驗證 route、權限、狀態、手機轉換、證據引用與 canonical 集合。通過不等於使用者研究、視覺品質、可用性或索引結果。
- `dashboard-playwright-acceptance.json`：嚴格 acceptance replay；4/4 viewport 失敗，命令 exit 1，沒有 DOM click fallback。
- `dashboard-playwright-replay.json`：同案 diagnostic replay；可在真實 click 失敗後用 DOM click 繼續蒐集其他觀察，但永遠不能轉成通過。

本輪可重現結果與限制見 [`RESULTS.md`](RESULTS.md)。

只驗 fixture 結構與 coverage：

```bash
python3 wow-frontend-design/scripts/validate_product_cases.py evals/product_cases.json
python3 wow-frontend-design/scripts/validate_site_plan.py \
  wow-frontend-design/scripts/site_manifest.example.json \
  wow-frontend-design/scripts/wireframe_plan.example.json \
  --sitemap wow-frontend-design/scripts/sitemap.example.xml
```

這個命令成功只代表八個固定案例、必要欄位與 locale 分布自洽，不得轉述為任何模型完成案例或取得分數。

Claude 兩案必須使用相同 brief、skill 版本、工具權限、viewports、互動路徑與獨立 reviewer。連線或 runtime 問題要記為 infrastructure failure，不得換算為設計分數。

若 host 拒絕完整 Skill context，可另跑 `prompt-only-compact.md`，但必須標成 `compact-adapter` cohort 並記錄 hash。它不得替代或和 `full-skill` cohort 直接比較；context-limit rejection 也不得換算為模型設計分數。

Runner 預設以 `CLAUDE_AUTH_MODE=official` 清除繼承的 Anthropic API key/token/base URL、自訂 model/alias，以及 Vertex、Bedrock、Foundry 與其常見 provider credential/config 環境變數；不清除 `CLAUDE_CODE_OAUTH_TOKEN` 或本機 Claude.ai 登入狀態。它再以 `--safe-mode` 隔離 plugins、hooks、MCP 與自訂設定。只有在刻意評測自訂 API 環境時，才設 `CLAUDE_AUTH_MODE=inherited`；兩模型必須使用相同模式並記錄 provenance。

本地模型可加入矩陣，但每次開始前都要揭露 runtime、精確 model/quantization、來源授權、下載與 RAM/VRAM/storage、命令、network 行為、可讀／可寫資料及清理方式，並取得使用者當次明確同意。未同意時只能準備 fixture/evaluator；不得下載、啟動或呼叫模型。雲端與本地結果分 cohort 報告，禁止 silent fallback。

Claude runner 只給固定 `Write` 工具，在暫存空目錄產出 case allowlist 指定檔案；沒有 `Read`、`Edit`、`Bash` 或 network tool。Haiku/Sonnet/Opus 都收到相同 trusted Skill revision 與 untrusted brief 邊界。產物通過 allowlist、size 與視覺網站輸出檢查後才複製到固定目標。受控評測可先建立 repo 外、evaluator-owned 目錄並設 `CLAUDE_REJECTED_OUTPUT_DIR=/absolute/path`；拒絕輸出會以 `0600` 保存，另附 reason、bytes 與 SHA-256。未設定時仍 fail closed，但 raw rejected output 不保留；quarantine 不能位於 repository 內。

受控矩陣以 `CLAUDE_CODE_EFFORT_LEVEL=auto` 使用各 Claude 模型預設 effort，並以 `CLAUDE_CODE_DISABLE_THINKING=1` 強制關閉 extended thinking。Codex cohort 忽略個人 `model_reasoning_effort`，使用模型預設 effort，並固定 `model_reasoning_summary="none"`；Codex 這些模型沒有可驗證的 zero-reasoning 模式，因此只宣稱關閉 summary，不宣稱停用內部 reasoning。

OpenAI cohort 使用已登入 ChatGPT 的 Codex CLI，精確請求 `gpt-5.4-mini`、`gpt-5.4`、`gpt-5.5`，忽略個人 config/rules，採 `workspace-write` sandbox、ephemeral session、無 web search／OSS local provider，並顯式啟用內建 multi-agent、browser 與 computer-use capability。Runner 只把 `auth.json` 複製進權限 `0600` 的臨時 `CODEX_HOME`，同時換掉 `HOME`、淨化 `PATH`；完成後會掃描 JSONL log，若發現主機使用者 Skill、原始 Codex Skill、repo `node_modules`、套件管理器、網路命令、git、MCP/web-search 或工作區外暫存路徑，就拒絕發布該次輸出。官方 `DESIGN.md` lint 只由外層 pinned evaluator 執行，implementation model 不得自行用 `npx` 取得工具。CLI 接受 requested identifier 不代表回報 backend snapshot；manifest 不會猜解析版本。Claude 與 Codex CLI 的工具面不同，因此跨 provider 只作分 cohort 觀察；同 provider 內才是工具面一致比較。

既有 showcase 呼叫維持 `run_claude_case.sh <haiku|sonnet|opus> <固定 showcase 目錄>`；v4 使用 `run_claude_case.sh <haiku|sonnet|opus> --case <fixed-v4-case>`。Codex 對應使用 `run_codex_case.sh <gpt-5.4-mini|gpt-5.4|gpt-5.5> --case <fixed-v4-case>`。新式呼叫不接受任意 target 路徑，runner 只依 `model × case` allowlist 導出輸出目錄。

## 後續完整矩陣

後續正式執行一律使用 `run_product_flow_evaluation.py`，並為每一輪提供全新 evaluator-owned `--target-root`。單一命令依序完成 Codex generation、pinned `DESIGN.md` clean gate、Playwright audit 與 screenshot inventory：

```bash
RUN_ROOT=/absolute/evaluator-owned/product-flow-run
npm run eval:product-flow -- \
  --provider codex \
  --target-root "$RUN_ROOT/targets" \
  --generation-output "$RUN_ROOT/generation.json" \
  --design-output "$RUN_ROOT/design-md.json" \
  --visual-output "$RUN_ROOT/visual.json" \
  --screenshot-dir "$RUN_ROOT/screenshots"
```

每個 generation case 預設最多嘗試三次；timeout 與 generation failure 會重試，model resolution、輸出政策與本機設定錯誤不會盲目重試。`DESIGN.md` lint 與 screenshot capture 也各最多三次。Mobile 使用 `390×844` CSS viewport、Android Chromium UA、touch、`isMobile=true` 與 DPR 3，不只是改變視窗大小。每次 attempt 都保留在 generation ledger；只有全部 case 完成、所有 `DESIGN.md` 零 error／warning、且每個 page/viewport 都有完整解碼、尺寸與 SHA-256 相符的 PNG，才回報 execution complete。任何 blocking visual issue 會另外回報 acceptance failed 並回傳非零；有截圖不等於通過。修復外部服務或設定後，以相同路徑加 `--resume`；若 generation 已用完原上限，明確提高 `--max-attempts` 後續跑，舊 attempt 不得覆蓋。

成功執行另由 evaluator 產生 `run-manifest.json`，記錄 `run_id`、固定 case ID/target、auth mode、Claude CLI path/version、請求的 model alias、runner/brief/trusted context/output hashes 與清除的環境變數名稱。Claude CLI 若未回報 alias 實際解析到的完整 model ID，manifest 會明確記為 `not_reported_by_cli`，不猜測 resolved exact model。

## 防作弊原則

- 實作模型不得修改 evaluator-owned tests、schema 或預期條件。
- 靜態訊號只能證明原始碼存在；功能必須用瀏覽器結果驗證。
- 視覺盲審只看 brief、程式、screenshots 與 raw evidence，不看產生模型的自評。
- 只有經選定、附 provenance 且仍符合 claim boundary 的 screenshots／summaries 進 repo；raw traces、暫存報告與 rejected quarantine 留在 evaluator-owned repo 外目錄。提交的截圖不得被誤當 regression baseline 或品質分數。

`weak-model-showcase/.wow-evidence.json` 若仍存在於本機 checkout，是已由 `.gitignore` 排除的 legacy v1 scratch ledger；它位於 implementation workspace、含舊式絕對路徑，因此不屬 release evidence，也不得交給目前 scorer 當可信 ledger。新評測一律使用 repo 外 evaluator root，讓 `ledger.json`、`policy.json`、`artifacts/` 與唯一 model-writable 的 `workspace/` 分離，並在每次 ledger `run` 明示 `--cwd <evaluator-root>/workspace`。
