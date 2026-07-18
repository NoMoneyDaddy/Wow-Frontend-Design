# Model evaluation fixtures

這些案例用來評測 `wow-frontend-design` 在不同模型上的行為，不是品質宣傳素材。Fixture validator 只證明資料結構與內部參照一致；只有實際 host/model integration run 才能證明 Skill activation 或 reference routing。

## 現行 fresh-build 入口

一般新專案只使用單一 current runner；v4–v7 名稱的檔案是歷史 cohort 或 evaluator research，不是需要選擇的 Skill 版本。

```bash
npm run build:current -- \
  --brief /absolute/path/brief.md \
  --target /absolute/empty-target \
  --log-dir /absolute/private-log-directory
```

Runner 以目前 `wow-frontend-design` snapshot 生成 caller 宣告的 exact product outputs，依序通過 pinned `DESIGN.md`、fresh desktop/mobile Playwright 與 Axe gate；可修 finding 最多自修兩輪，每輪完整重驗。只有 clean candidate 會原子發布。Target 另含 runner-owned `run-manifest.json`，不屬於 model 可寫的 product output set，也是成功發布的 terminal receipt。私有 execution receipt 在原子替換前固定為 `publication_pending`；若最後的 target identity check／replace 失敗，另寫 `current-skill-build.publication-failure.json`，不覆寫先前 provenance。Trace、stderr、完整 gate rejection 與 quarantine 留在 `--log-dir`。Target 與 log directory 必須是既存、真實、互不包含的絕對路徑，target 起始為空。

## 歷史發布的 v6 自修復 cohort

固定只使用 `gpt-5.4-mini`，涵蓋 8 個互相錯開的產品、12 routes 與 4 個裝置 profiles。這是 development/regression closure，不是 held-out validation：同一 cohort 曾參與 Skill／evaluator 修正與候選選擇。初始 generation 最終 8/8 完成；最新 Skill 再依繁中排版、hierarchy、locale 與 layout 診斷修正全部 8 案。後續三輪 Darwin 候選共產生 192 張截圖，但最終仍有 6 案 findings，因劣於基準而未晉級。修正 evaluator 公開契約後，人工檢閱再找到兩個中文標題孤字，補上逐行 gate 並完成兩輪全矩陣。官方 `DESIGN.md` verifier 8/8 clean，最終 64/64 PNG 通過尺寸、DPR、hash、auditor 與 inventory 完整性檢查；deterministic visual、runtime、network、body-flow、heading-flow、layout-flow 與 locale-flow findings 都是 0。

- `product-flow-v6-repaired-v2-generation-results.json`：8 repairs／0 promotions 的最終 target、latest-Skill provenance、attempt 與 manifest path。
- `product-flow-v6-latest-skill-repair.md`：8 案修復、外部研究落實與限制。
- `product-flow-v6-repaired-v2-design-md-results.json`：pinned `@google/design.md@0.3.0` 的 8/8 clean 結果。
- `product-flow-v6-visual-results.json`：64 張 screenshot 的 route、state、裝置訊號、hash 與 browser findings。
- `product-flow-v6-repaired-v2-targets/`：最終網站與 `DESIGN.md`。
- `../assets/product-flow-v6/`：發布的完整 screenshot inventory。
- `../wow-frontend-design/scripts/validate_product_flow_v6_evidence.py`：拒絕 stale／額外／缺少圖片、model drift、錯誤 viewport、body／heading-flow finding 與 auditor drift。

Mobile profile 使用 Android Chromium UA、touch、`isMobile=true`、DPR 3 與 mobile viewport/screen；這是 browser device emulation，不是實體 iOS／Android 認證，也不是所有瀏覽器或正式 WCAG conformance。

## 目前保留的 v5 mini raw artifacts

固定 cohort 只使用 `gpt-5.4-mini`，涵蓋列車改簽、訂閱稽核、多人翻譯審校與低資訊量三頁陶藝祭。生成 4/4 完成、5 attempts、1 case 自動重試；官方 DESIGN lint 4/4 clean。四個原始 target 都留下 repair-required finding，現行 Skill 已吸收但未倒改原始產物。所有舊 screenshot 與 screenshot-bound manifest 已於 2026-07-15 清空，不再作發布證據。

- `product-flow-v5-mini-generation-results.json`：凍結 Skill／brief、attempt history、exact model selector 與 manifest。
- `product-flow-v5-mini-design-md-results.json`：更新 lockfile 後以 pinned `@google/design.md@0.3.0` 重驗的結果。
- `product-flow-v5-mini-targets/`：四組原始 HTML、DESIGN 與 manifest。

這批只保留為優化來源，不代表現行 Skill 通過。現行證據是上方 v6 自修復 cohort。

## 歷史 v4 證據

歷史固定 Codex cohort 共 9 個 target：三個 v4 主題 × `gpt-5.4-mini`、`gpt-5.4`、`gpt-5.5`。生成 9/9 完成、13 attempts、3 個 case 重試；官方 DESIGN lint 9/9 clean。舊 screenshot 與 visual report 已清空。

- `product-flow-v4-generation-results.json`：固定 Skill／brief、attempt history、target 與 manifest。
- `product-flow-v4-design-md-results.json`：pinned `@google/design.md@0.2.0` 結果。
- `product-flow-v4-targets/`：9 組原始 HTML、DESIGN 與 manifest。

生成使用凍結的 pre-optimization Skill；現行 Skill 的新完整重跑結果見上方 v6 cohort。

## 題型與後續政策

- 換掉 v4 三個主題；測不同產品功能、互動路徑與測試面向，不把舊案換皮重跑。
- 執行前先研究現代網頁的設計感、字體編排、層級、材質、動效節制與響應式呈現，再把來源轉成可驗證規則。第一個方法論案例是 [Design Skill Comparison Lab](https://designskill.qiaomu.ai/)；只採用其題型分離、實際互動與雙軌評估思路，不照搬作者分數。
- 本輪依使用者指定只跑 `gpt-5.4-mini`；其他模型未進入此 cohort。Codex 與 Claude 若日後加入，仍分 provider cohort 報告，不混成直接排名。
- 新截圖只用於 README 的功能／成果展示；測試報告仍分開列出 repair history 與 boundary，不能以好看的截圖取代 acceptance。
- 舊 screenshot 已清空；v6 發布依 [`TEST_PLAN.md`](TEST_PLAN.md) 建立獨立 cohort，不沿用舊 hash。

`playwright_dashboard_audit.cjs` 會重播固定 dashboard 的桌機／手機行為矩陣，不修改模型產物。以 repo 根目錄的 `package-lock.json` 安裝固定 Playwright 版本；使用系統瀏覽器時設定 `CHROME_EXECUTABLE_PATH`，再傳入 Haiku 與 Opus 的本機 URL。預設是 acceptance mode：任何互動失敗會非零退出，禁止 DOM click fallback。`--diagnostic` 才允許 fallback 以繼續觀察，但 verdict 永遠是 `diagnostic_only`。輸出的 JSON 是互動證據，不是視覺品質分數。

```bash
npm ci --ignore-scripts
CHROME_EXECUTABLE_PATH=/absolute/path/to/chrome npm run audit:dashboards -- \
  http://127.0.0.1:4178/ http://127.0.0.1:4179/
```

## v6 截圖與 hash 證據

v6 report 把 screenshot、route、state、viewport、DPR、browser、source、auditor 與 dependency lock 互相以 SHA-256 綁定。Evidence validator 會拒絕 stale byte、缺圖、額外圖片、錯誤尺寸、model drift、body-flow finding 或 auditor drift；不可手改 hash 讓 validator 變綠。完整規格、執行紀錄與尚未執行的 v7 分階段單一候選／獨立供應鏈計畫見 [`TEST_PLAN.md`](TEST_PLAN.md)。v7 沒有 repository-owned 預設 evidence；無參數驗證必須 fail closed。CI 只以 `npm run check:evidence-v7-cli` 檢查入口，實際驗證需明示 evaluator-owned artifacts：

```bash
npm run validate:evidence-v7 -- \
  --manifest evals/v7-pilot-manifest-20260717-tools.json \
  --ledger "$RUN_ROOT/ledger.json" \
  --result-dir "$RUN_ROOT/results" \
  --screenshot-dir "$RUN_ROOT/screenshots" \
  --repository-root . \
  --gate full
```

驗證成功後，可把同一組 Playwright evidence 編譯成 evaluator-owned、不可覆寫的 bounded repair packet。它只保留 issue code、case/state/profile、受限量測、artifact hash 與最小重測矩陣，不轉送原始頁面文字、console body、URL 或完整報告；輸出必須位於 repository 外。`a1_target_contract_unresolved` 與未知 schema 會中止編譯，避免把 evaluator defect 誤導成產品修正：

```bash
npm run eval:v7-repair-packet -- \
  --manifest evals/v7-pilot-manifest-20260717-tools.json \
  --ledger "$RUN_ROOT/ledger.json" \
  --result-dir "$RUN_ROOT/results" \
  --screenshot-dir "$RUN_ROOT/screenshots" \
  --output "$RUN_ROOT/repair-packet.json" \
  --repository-root . \
  --gate full
```

P1 repair cycle 只重生 packet 中的 `variant × case_id`，再以 issue class、source/repaired output receipt 與凍結支援矩陣選取 affected rows。`index.html` 有變時，CSS、token、layout、文字與互動都保守擴大為該 target 的完整 15-row matrix；`index.html` 未變時仍重跑原 failure rows；分類未知或 target isolation 無法機械證明時回退完整 cohort。每輪只有 evaluator-owned deterministic vector 嚴格改善才成為 best artifact；新 interaction/runtime regression 不可被較少 composition findings、較小輸出或 hash 抵銷。所有選擇、rank、fuse 與 promotion 都保存 append-only receipt：

```bash
npm run eval:v7-repair-cycle -- \
  --manifest evals/v7-pilot-manifest-20260718-form-outcome-v23.json \
  --hidden-matrix "$RUN_ROOT/hidden-matrix.json" \
  --split development \
  --packet "$RUN_ROOT/repair-packet.json" \
  --source-ledger "$RUN_ROOT/ledger.json" \
  --source-result-dir "$RUN_ROOT/results" \
  --source-screenshot-dir "$RUN_ROOT/screenshots" \
  --brief-map "$RUN_ROOT/brief-map.json" \
  --candidate-reference wow-frontend-design/references/typographic-layout.md \
  --work-root "$REPAIR_ROOT" \
  --log-dir "$REPAIR_LOGS" \
  --output "$REPAIR_ROOT/cycle-ledger.json" \
  --max-total-generations 9 \
  --max-wall-seconds 1800 \
  --repository-root .
```

`brief-map.json` 必須逐一綁定 development full matrix 的 evaluator-owned absolute brief path 與 SHA-256。Packet 是可執行回饋接口，不是修正成功證據；affected receipt 只能證明其 SHA-256 綁定 rows，不能替代 release/full-support matrix。Runner 啟動前會凍結 packet target hash、全 cohort `max-total-generations` 與 monotonic wall deadline；每個 generation、affected capture、full verification 和 promotion 前都會檢查預算。觸頂只可留下 `PARTIALLY VERIFIED` 的 `cohort_budget_fuse`，保留目前 staged best artifact 與尚未 narrow 的 inflight artifact，不能繼續後續 browser/model 呼叫或 promotion；receipt 明示 staged artifact 只屬 `pre_promotion_only`，不宣稱已通過 full matrix。Wall deadline 是步驟間的保險絲，不會取代各 delegated operation 自己的 timeout。計數與 elapsed 只代表 evaluator 工作量，不參與品質 rank；沒有官方 usage receipt 時 token／cost 明示 unavailable，不做估算。這個 runner 已通過 synthetic contract tests，但尚未執行 live model/browser repair cycle，因此自動修正能力仍是 `PARTIALLY VERIFIED`。

P7 paired decision compiler 把 promotion ratchet 固定為唯讀、無 promotion 權限的四態 receipt。它只接受 frozen manifest 與 evaluator-owned hash-bound bundle；accepted package 與 evaluator toolchain digest 必須由 manifest baseline／toolchain／evaluator records 重算，development、validation summary、每組 pair 與 sealed-test 兩個 arm 也各自以不可重用的 evaluator receipt 綁定對應 payload。每個 arm 另須列出 generation manifest、output inventory、visual ledger、visual result inventory 與 attempt history SHA；pair 內的 brief／input／execution contract 必須相同，run-specific sources 必須跨 arm／pair 唯一。Sealed test 沿用 execution contract，但不得重用 validation 的 brief、input、run source 或 receipt。Development 有預指定 deterministic family 嚴格改善且無較高優先 regression，才可 `READY_FOR_SEALED`。Sealed validation 必須是三組未重用 evidence、同時包含兩種呈現順序的 eligible pairs；hard gate、material craft loss、budget exceeded 或 untouched sealed test failure 都是 `REJECTED_STOP`，缺資料／`not_run`／hash drift 則是 `UNAVAILABLE`。全數成立也只能輸出 `ELIGIBLE_FOR_EVALUATOR_ACCEPTANCE`，不能自行 promotion。Receipt compiler 不重新解析 hidden brief、raw screenshot 或 browser ledger 內容；它只套用已通過 schema、source binding 與 hash 驗證的 evaluator receipts。`REJECTED_STOP` 只停止目前 frozen candidate，不宣稱已有跨 candidate history；「連續兩候選無增益」仍需另一份 hash-bound history receipt。現行 manifest 仍是 `pilot_ready`，因此以下命令會誠實輸出 `candidate_not_frozen`；它不會啟動 model、browser、network 或額外截圖：

```bash
npm run eval:v7-paired-decision -- \
  --manifest evals/v7-pilot-manifest-20260718-form-outcome-v23.json \
  --output "$DECISION_ROOT/v7-paired-decision.json" \
  --repository-root .
```

P2 在每個 repair target 的生成前、affected Playwright matrix 後執行一個 hash-pinned `source_layout_audit.py` supporting probe。它只投影 `global_emergency_breaking`、`prose_wrap_disabled`、`fixed_text_clipping` 三種高可信 source-risk code，去除原始 evidence、confirmation、selector、HTML 與產品文字，依 `probe × code × path` 去重並限制最多三筆。Sidecar 以 target SHA-256、probe contract、script 與 dependency 綁定；未知 schema/code、truncated coverage、tool drift、timeout 或 unavailable 都留下明確 receipt，不得被解讀成 clean。這些 advisory 只有與已驗證 browser finding 共用根因時才可協助定位，不改變 failure key、best-artifact rank、promotion 或 release gate；Playwright 仍是 rendered behavior 的權威。Pretext 暫不接入自修正閉環，因目前缺少穩定 CLI／versioned result schema 與 bounded computed-style provenance。

P3a `eval:v7-breakpoints` 是獨立、零截圖的 Chromium supporting-discovery sidecar。它不接受模型自報的 breakpoint；先量固定 11 個 coarse widths，只有相鄰 categorical layout signature 不同時才二分到 1 CSS px，單一 route/state 最多 48 samples、8 transitions、depth 11。Signature 只保留 hidden spec ID、display/position/writing-mode/flex 類別、可見數、child row/column topology、viewport clipping、overflow 與 assertion 結果，不輸出 selector、產品文字或連續 rect。相同寬度的兩次 animation-frame sample 必須穩定；route/spec/manifest/contract/script 漂移、字型、互動、runtime、外部 request 或 budget 問題都明示 unavailable。只有兩個 fresh context 都重現的 horizontal overflow／required assertion failure 才列 finding；mode transition 本身只是 advisory。它不產生 screenshot/trace/video，也不被 repair packet、failure key、rank 或 promotion 讀取。第一版只宣稱 bounded Chromium width observation；cross-engine、touch、height、zoom、motion、physical-device 與視覺品質仍未驗證。

P3b `eval:v7-motion` 是另一個獨立 sidecar，只在 390／1024px 的 `no-preference` fresh context 透過標準 `document.getAnimations()` 觀測到 CSS Animation、CSS Transition 或 Web Animation 時，才建立對應 `reduce` context；不注入全域極短 duration CSS。它以 kind × duration bucket × finite/infinite 的 bounded categories 比較 computed behavior，並重跑 hidden assertions、overflow 與 categorical layout signature。只有 normal 通過但 reduce 連續兩組 fresh-context pair 失敗，才列 `reduced_motion_task_regression`／`reduced_motion_horizontal_overflow`；動畫數量或 normal/reduce 類別相同本身只可成 advisory。無 motion 是 `not_applicable`，超過 64 animations／12 samples、preference emulation、provenance、font、runtime 或外部 request 問題都是 explicit unavailable。它同樣不產生 screenshot/trace/video，也不進 repair authority。這遵循 [Media Queries Level 5 `prefers-reduced-motion`](https://www.w3.org/TR/mediaqueries-5/#prefers-reduced-motion) 的 preference 語意，並使用 [MDN `Document.getAnimations()`](https://developer.mozilla.org/en-US/docs/Web/API/Document/getAnimations) 所述會涵蓋 CSS Animations、CSS Transitions 與 Web Animations 的介面；sidecar 不等同 WCAG、視覺品質或 physical-device 證據。

P9 focus-obscuration repair gate 使用 hidden spec v2 明示最多八個 task control；v1 spec 與 result schema 保持原契約。每個 v2 control 先重播其 preceding steps，再於兩個 fresh Playwright context 各自執行 `scrollIntoViewIfNeeded()`、`focus()` 與兩個 animation frame，只有兩次都以 bounded partition 證明同一 simple opaque author-created fixed/sticky rectangle coverage 時，才產生 `focused_control_obscured` repair finding。partial／behind 為 clear；透明、blend、transform／clip／mask／filter、複雜 ancestor paint、外部 request、字型、DOM／partition budget或兩次幾何不穩定一律 unavailable。Unavailable 會明示阻斷 clean，repair packet 也會拒絕把 evaluator evidence gap 投影成產品修正。它不增加 screenshot、trace 或 video；repair packet 只帶 evaluator target ID 與 bounded geometry，不帶 selector。這個 gate 以 [Playwright locator focus API](https://playwright.dev/docs/api/class-locator#locator-focus) 與 [W3C WCAG 2.4.11 Focus Not Obscured (Minimum)](https://www.w3.org/TR/WCAG22/#focus-not-obscured-minimum) 建立反例，但只宣稱 named browser/profile/state 的 programmatic focus；不宣稱 keyboard、virtual keyboard、assistive technology 或 WCAG conformance。

P10 修補 P9 在 required `click` 被完整遮住時先撞上 Playwright actionability timeout、因而遺失 repair evidence 的消費端缺口。Auditor 先取得 P9 的兩次 fresh-context full-obscuration 證據；只有 coverage complete、confirmed control 與 hidden click step 三者精確綁定時，才輸出 outcome-specific result schema v3。它不執行也不 force blocked click：前置 step 誠實記 completed，blocked step 與相依後續 step 各以固定 reason 記 incomplete，assertions 全標示未評估；focused evidence 只新增 evaluator step ID，不帶 selector、value、產品文字或 raw Playwright error。沒有這個精確反例時仍輸出原 v1/v2 exact contract。v3 仍只保留原本一張 screenshot，repair packet 只投影既有 focus finding；這遵循 [Playwright actionability](https://playwright.dev/docs/actionability) 對 click 必須 Receives Events 的官方邊界，不把一般 timeout 或 selector defect猜成產品修正。

P11 在既有 A1 typography evaluator 補上 required product heading／prose 的直接裁切反例。它只檢查 target 自身的 client box，先以 scroll/client delta 超過 line-height-derived tolerance 判定候選，再以每個 grapheme 的 `Range.getClientRects()` 證明文字 fragment 確實落在 box 外；只接受 `text-overflow: ellipsis`、直接 inline `clip`、`line-clamp` 與直接 block `hidden/clip` 四種 bounded mechanism。具備命名、可聚焦 region 的 scroll container 記為 accessible，其他 scroll container 只 advisory；transform、zoom、pseudo content、複雜 clip/mask/filter、未知 `text-overflow`、非 product intent 與超過預算都 fail closed。它不掃 ancestor、不新增 screenshot，也不宣稱 cross-engine、assistive technology、全文語意或整體排版品質；repair packet 只投影 bounded geometry/enums，要求保留完整 copy 並移除直接裁切或重組 text track。此反例依 [CSS Overflow Level 3 `text-overflow`](https://www.w3.org/TR/css-overflow-3/#text-overflow) 與 [CSS Overflow Level 4 `line-clamp`](https://www.w3.org/TR/css-overflow-4/#line-clamp) 的規範語意建立。

P12 以 input schema v3／result schema v4 驗證一個 evaluator-declared stale completion：主頁與一個 fresh context 都只攔截同源 exact method/path 的第一筆 request，確認 pending predicate 後執行唯一 identity-changing interruption，再以固定 response `fulfill`、`response.finished()`、兩個 animation frame 與 750ms post-release quiescence window 檢查 identity／success／content freshness及延遲重複 request。兩次都 stale 才產生 `stale_async_completion`；任一 phase unavailable 或兩次不一致只會阻斷 clean，不得成為產品修正。Result 與 repair packet 只留 evaluator IDs／fixed enums，不帶 selector、path、value、body、copy 或 raw error；v1/v2 input 與 v1–v3 result exact contract不變，每個 matrix item仍只有原本一張 screenshot。這遵循 [Playwright Network API](https://playwright.dev/docs/network) 與 [`Route.fulfill()`](https://playwright.dev/docs/api/class-route#route-fulfill)；claim 只涵蓋兩次 declared controlled replay 與明示 window，不外推到所有 backend race、timer、WebSocket 或 async UX。

P13 以 input schema v4／result schema v5 驗證 evaluator-declared native task control 的 accessible name。每個宣告都一對一綁定既有 form-control step，只接受 bounded native text/search/email/tel/url/number `input`、`textarea`、`select` 與 `textbox`、`searchbox`、`spinbutton`、`combobox`、`listbox` role；password、color、file、date 類型及 custom composite 不在此 probe 範圍。兩個 fresh Playwright context 重播 preceding steps，確認 target 唯一、可見且 native role 相符，再用 exact `getByRole(role, { name })` 驗證同一 DOM node。兩次都 mismatch 才產生 `declared_control_accessible_name_mismatch`；unsupported control、重複 role/name、字型／runtime／external request 或兩次狀態漂移只會阻斷 clean。Result 與 repair packet 只留 evaluator ID、role 與 fixed enums，不帶 expected name、selector、copy 或 raw error；v1–v4 result exact contract不變，每個 matrix item仍只有原本一張 screenshot。此 bounded gate 依 [Playwright role locators](https://playwright.dev/docs/locators#locate-by-role) 與 [WAI form labels](https://www.w3.org/WAI/tutorials/forms/labels/) 建立反例，不宣稱全頁 WCAG、assistive technology、custom widget 或 Label in Name conformance。

P14 以 input schema v5／result schema v6 驗證 evaluator-declared modal dialog focus lifecycle。每筆 declaration 只綁既有 click/press open-close steps、唯一且可見的 `role=dialog`／`aria-modal=true` 容器、開啟後 descendant focus target 與關閉後 workflow return target；兩個 fresh context 重播相同 prefix/middle steps，在各 phase 兩個 animation frame 後比較 `document.activeElement`。普通非 focusable declaration 會 unavailable，明示 `tabindex=-1` 的合法 programmatic target可驗證；open Shadow DOM target暫時 fail closed。兩次都一致 mismatch 才產生 `declared_dialog_focus_lifecycle_mismatch`；role/modal/visibility/descendant/count、字型/runtime/external request 或 replay drift 只會阻斷 clean。Result 與 repair packet 只留 evaluator ID、open/return boolean 與 fixed enums，不帶 selector、copy 或 raw error；v1–v5 result exact contract不變，每個 matrix item仍只有原本一張 screenshot。此 gate 依 [WAI-ARIA APG Modal Dialog Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) 與 [Playwright focus assertion](https://playwright.dev/docs/api/class-locatorassertions#locator-assertions-to-be-focused) 建立 bounded counterexample，不宣稱完整 focus trap、Escape、背景 inert、screen reader、APG 或 WCAG conformance。

P15 以 input schema v6／result schema v7 驗證 evaluator-declared invalid-feedback linkage。每筆 declaration 只綁既有 fill/select control step、其後 click/press invalidation step、唯一且可見的原生文字輸入／`textarea`／`select` 與可見錯誤節點；兩個 fresh context 重播到 invalid state，要求 `aria-invalid="true"`，再確認錯誤節點的唯一 stable ID 是否出現在 control 的 `aria-describedby` IDREF list，或精確等於單一 `aria-errormessage` ID reference。兩次都穩定 missing 才產生 `declared_invalid_feedback_unlinked`；unsupported control、hidden/empty/duplicate-ID feedback、`aria-hidden`／`inert` subtree、multi-ID `aria-errormessage`、Shadow DOM、字型/runtime/external request 或 replay drift 只會阻斷 clean。Result 與 repair packet 只留 evaluator ID、fixed relation enum，不帶 selector、IDREF、copy、value 或 raw error；v1–v6 result exact contract不變，每個 matrix item仍只有原本一張 screenshot。此 gate 依 [WAI Forms User Notifications](https://www.w3.org/WAI/tutorials/forms/notifications/)、[WAI ARIA21](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA21.html) 與 [WAI-ARIA `aria-errormessage`](https://www.w3.org/TR/wai-aria/#aria-errormessage) 建立 bounded counterexample，不宣稱全表單、screen reader、assistive technology 或 WCAG conformance。

P16 以 input schema v7／result schema v8 驗證 evaluator-declared invalid-input preservation。每筆 declaration 只綁相鄰的既有 fill/select control step 與 click/press invalidation step，且必須明示 `normalization:"none"`；control step 只接受 `eval-preserve-*` bounded evaluator-owned synthetic token，不接受真實或敏感輸入；兩個 fresh context 先在 control step 後以 Playwright `locator.inputValue()` 擷取 evaluator 內部 baseline，再執行 invalidation，要求唯一、可見、light-DOM 原生文字輸入／`textarea`／single `select` 初態未 invalid、之後為 `aria-invalid="true"` 且 current value 精確保留。兩次都穩定 lost 才產生 `declared_invalid_input_lost`；unsupported/hidden/duplicate/Shadow DOM control、multiple select、字型/runtime/external request 或 replay drift 只會阻斷 clean。Result 與 repair packet 只留 evaluator ID、native-kind 與 retained boolean，不帶 selector、baseline、輸入值、copy 或 raw error；v1–v7 result exact contract不變，每個 matrix item仍只有原本一張 screenshot。此 gate 依 [Playwright `locator.inputValue()`](https://playwright.dev/docs/api/class-locator#locator-input-value) 與 Skill 既有 retained-input recovery contract 建立 bounded counterexample；有 formatter/normalizer、明示 reset 或非 invalid recovery 的流程不得宣告此 no-normalization exact-preservation contract。

P17 以 input schema v8／result schema v9 驗證 evaluator-declared disclosure state synchronization。每筆 declaration 只綁既有 click 或 Enter/Space press step、`settling:"reduced-motion-static"`、唯一可見且 enabled 的 light-DOM native `<button>`（實際 role 仍為 button）與唯一 light-DOM panel；兩個 fresh context 在 action 前要求 `aria-expanded="false"` 且 panel 不可感知，action 後兩個 animation frame 要求沒有 pending/running panel animation、`aria-expanded="true"` 且 panel 可感知。可感知 probe會拒絕 `aria-hidden`、`inert`、`content-visibility:hidden`、effective opacity 0，並支援 `display:contents` 的可見 descendant。兩次都穩定 XOR mismatch 才產生 `declared_disclosure_state_mismatch`；no-op、動畫未收斂、初態契約、disabled/unsupported/shadow target、字型/runtime/external request 或 replay drift 只會阻斷 clean。P17 structural record 與 repair packet 只留 evaluator ID 與 expanded/panelVisible boolean，不帶 selector、copy 或 raw error；v1–v8 result exact contract不變，每個 matrix item仍只有原本一張 screenshot。此 gate 依 [WAI-ARIA APG Disclosure Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/) 與 Playwright role/action semantics 建立 bounded counterexample；不要求 optional `aria-controls`，也不宣稱 animated disclosure、二次收合、全頁鍵盤、focus、APG 或 WCAG conformance。

涉及 ancestor animation 或非預設 `filter`、`clip-path`、`mask-image`、`mix-blend-mode` 的 panel 會 fail closed；P17 不以簡化幾何推論完整 paint/compositing visibility。

P18 以 input schema v9／result schema v10 驗證 evaluator-declared valid→success→invalid 視覺結果互斥。每筆 declaration 只綁四個相鄰且不跨 target 重用的既有 steps、同一 light-DOM native control、`normalization:"none"` 與 `settling:"reduced-motion-static"`；`custom-aria` 要求 invalid state 的 `aria-invalid=true` 與可感知非空 error，`native-constraint` 則要求 `willValidate=true` 並以 `validity.valid` 驗證成功／失敗 checkpoint，不讀瀏覽器原生錯誤文案。兩個 fresh context 都必須先見到可感知、具 bounded rendered text 的 success，再確認 invalid value 精確保留；invalid 後相同 rendered success message 仍可見，才產生 `stale_success_after_invalid`，內容已改寫則不誤判為 stale。空 outcome、hidden-only content、complex subtree paint、native validity 不成立、value 被清除、動畫／request／font／runtime 或 replay drift 都 fail closed。Result 與 repair packet 只留 evaluator ID 與 stale boolean，不帶 selector、value、copy、validity message 或 raw error；v1–v9 result exact contract不變，每個 matrix item仍只有原本一張 screenshot。Live-region／accessibility-tree precedence 在獨立反例連續失敗後已熔斷並排除於 repair authority；P18 不宣稱 screen reader、assistive technology、全表單或 WCAG conformance。

## 目前案例

- `trigger_cases.json`：Skill 是否應啟用，以及啟用後應載入哪些最小 reference 的 evaluator-owned 正／反例。`validate_trigger_cases.py` 只檢查 fixture schema、正反例集合、ID／locale 與 reference 檔案的 self-consistency；它不呼叫 host、模型或 router，也不證明實際 activation/routing。
- `product_cases.json`：把八個非 landing／跨產品案例固定成 evaluator-owned machine-readable definitions，涵蓋 surface、audience/task、品牌證據邊界、mobile transformation、hidden acceptance focus 與 `zh-Hant`/`en` 分布。`validate_product_cases.py` 只驗 schema 與 coverage；fixture 不含執行結果、模型成績、browser evidence 或 WCAG 結論。
- `weak-model-showcase/`：`gpt-5.4-mini` 從普通繁中選物頁進行 hostile retrofit。保留分類、收藏與表單，並接受外部桌機／手機瀏覽器測試。
- `briefs/showcase.md` 與 `claude-{haiku,opus}-showcase/`：兩個隔離輸出共用同一份 canonical fixed brief，不在 target 內維護重複副本。
- `claude-{haiku,opus}-product-dashboard/`：共用 `briefs/product-dashboard.md` 的非 landing 產品 UI 原始產物與 run manifest；兩者目前都未通過 strict acceptance。
- `briefs/{rail-rebooking,subscription-audit,community-translation,ceramics-festival-one-line}-v5.md`：交通恢復、高密度資料操作、多語審校與低資訊多頁 editorial 四個互相錯開的方向；hash 固定在 generation ledger。
- `briefs/*-v6.md`、`product-flow-v6-repaired-v2-targets/`、`product-flow-v6-visual-results.json` 與 `../assets/product-flow-v6/`：目前 8 案自修復 cohort 的 brief、最終網站、browser report 與 64 張發布截圖。
- `claude-haiku-product-dashboard-remake/`：唯一一次 anti-slop remediation invocation 的拒絕紀錄；輸出政策在 publish 前熔斷，沒有可接受網站產物。
- `capability-status.json`：公開 claim ledger。每項能力都要有現存 artifact 與明示 boundary；validator 只確保狀態結構與路徑未腐化，不替內容升級證據。
- `platform-support.json`：本版一次性 script runtime 快照。Agent Skills package 依標準驗證，不按模型品牌分格；12 格只追蹤 23 個 installed Python entrypoints、CI／POSIX evaluator 與 Chromium、Chrome／Edge、Firefox、WebKit backend。沒有下次查核日期，未跑過的格子維持 `not_run`。
- `../wow-frontend-design/scripts/capture_runtime_profile.py`：只輸出 privacy-bounded OS／Python 與 caller declarations，不讀 hostname／user／home／IP／完整 environment，也不執行 command 或 network probe。跨 OS CI smoke 會執行它與 portable contract tests，但新 cell 必須等 workflow 真正完成才可升級。
- `../wow-frontend-design/scripts/model_profile.example.json`、`route_model.py`：由 evaluator 依 task／locale／surface／risk 與精確環境 revision 決定起始 lane；模型不能自報強弱。
- `../wow-frontend-design/scripts/runtime_events.example.json`、`runtime_downgrade.py`：把真實 schema／工具／repair／timeout／權限結果轉成單向降級；不允許同一 run 自動升級。
- `../wow-frontend-design/scripts/{site_manifest,wireframe_plan}.example.json`：有效的 IA／wireflow 契約範例；`validate_site_plan.py` 會連同本機 XML sitemap 驗證 route、權限、狀態、手機轉換、證據引用與 canonical 集合。通過不等於使用者研究、視覺品質、可用性或索引結果。
- `dashboard-playwright-acceptance.json`：嚴格 acceptance replay；4/4 viewport 失敗，命令 exit 1，沒有 DOM click fallback。
- `dashboard-playwright-replay.json`：同案 diagnostic replay；可在真實 click 失敗後用 DOM click 繼續蒐集其他觀察，但永遠不能轉成通過。

本輪可重現結果與限制見 [`RESULTS.md`](RESULTS.md)。

只驗 fixture 結構與 coverage：

```bash
python3 wow-frontend-design/scripts/validate_product_cases.py evals/product_cases.json
python3 wow-frontend-design/scripts/validate_platform_support.py \
  evals/platform-support.json --repository-root . --report
python3 wow-frontend-design/scripts/validate_site_plan.py \
  wow-frontend-design/scripts/site_manifest.example.json \
  wow-frontend-design/scripts/wireframe_plan.example.json \
  --sitemap wow-frontend-design/scripts/sitemap.example.xml
python3 wow-frontend-design/scripts/validate_product_flow_v6_evidence.py \
  evals/product-flow-v6-visual-results.json --repository-root .
```

這個命令成功只代表八個固定案例、必要欄位與 locale 分布自洽，不得轉述為任何模型完成案例或取得分數。

Claude 兩案必須使用相同 brief、skill 版本、工具權限、viewports、互動路徑與獨立 reviewer。連線或 runtime 問題要記為 infrastructure failure，不得換算為設計分數。

若 host 拒絕完整 Skill context，可另跑 `prompt-only-compact.md`，但必須標成 `compact-adapter` cohort 並記錄 hash。它不得替代或和 `full-skill` cohort 直接比較；context-limit rejection 也不得換算為模型設計分數。

Codex runner 不再對每案固定嵌入全部 reference。核心檔固定，caller 指定的 `model × case` 再加入 weak-model、元件、字型或色彩 reference；manifest 記錄實際選取清單。這是外部決策與 progressive routing，不是要求模型自報能力。v6 mini 的固定 prompt context 由 190,732 bytes 降至 145,024–161,274 bytes；尚未用新路由重跑 generation，因此不得轉述為已驗證的速度或品質提升。

Model profile 不可只寫 `strong`／`weak` 或由模型自填。schema v2 綁定 Skill、adapter、toolchain、evaluator revision，並分開 `eligible_runs` 與 `infrastructure_failures`。執行中由外層 evaluator 追加 runtime event；一般 repair 先重試，持續輸出則延長 inactivity timeout，同錯三次才停止盲修並保留最佳產物。

Runner 預設以 `CLAUDE_AUTH_MODE=official` 清除繼承的 Anthropic API key/token/base URL、自訂 model/alias，以及 Vertex、Bedrock、Foundry 與其常見 provider credential/config 環境變數；不清除 `CLAUDE_CODE_OAUTH_TOKEN` 或本機 Claude.ai 登入狀態。它再以 `--safe-mode` 隔離 plugins、hooks、MCP 與自訂設定。只有在刻意評測自訂 API 環境時，才設 `CLAUDE_AUTH_MODE=inherited`；兩模型必須使用相同模式並記錄 provenance。

本地模型可加入矩陣，但每次開始前都要揭露 runtime、精確 model/quantization、來源授權、下載與 RAM/VRAM/storage、命令、network 行為、可讀／可寫資料及清理方式，並取得使用者當次明確同意。未同意時只能準備 fixture/evaluator；不得下載、啟動或呼叫模型。雲端與本地結果分 cohort 報告，禁止 silent fallback。

Claude runner 只給固定 `Write` 工具，在暫存空目錄產出 case allowlist 指定檔案；沒有 `Read`、`Edit`、`Bash` 或 network tool。Haiku/Sonnet/Opus 都收到相同 trusted Skill revision 與 untrusted brief 邊界。產物通過 allowlist、size 與視覺網站輸出檢查後才複製到固定目標。受控評測可先建立 repo 外、evaluator-owned 目錄並設 `CLAUDE_REJECTED_OUTPUT_DIR=/absolute/path`；拒絕輸出會以 `0600` 保存，另附 reason、bytes 與 SHA-256。未設定時仍 fail closed，但 raw rejected output 不保留；quarantine 不能位於 repository 內。

受控矩陣以 `CLAUDE_CODE_EFFORT_LEVEL=auto` 使用各 Claude 模型預設 effort，並以 `CLAUDE_CODE_DISABLE_THINKING=1` 強制關閉 extended thinking。Codex cohort 忽略個人 `model_reasoning_effort`，使用模型預設 effort，並固定 `model_reasoning_summary="none"`；Codex 這些模型沒有可驗證的 zero-reasoning 模式，因此只宣稱關閉 summary，不宣稱停用內部 reasoning。

OpenAI cohort 使用已登入 ChatGPT 的 Codex CLI，v5 mini 精確請求 `gpt-5.4-mini`，忽略個人 config/rules，採 `workspace-write` sandbox、ephemeral session、無 web search／OSS local provider，並停用 implementation builder 的 multi-agent、browser 與 computer-use capability；瀏覽器與截圖只由外層 evaluator 擁有。Runner 只把 `auth.json` 複製進權限 `0600` 的臨時 `CODEX_HOME`，同時換掉 `HOME`、淨化 `PATH`；完成後會掃描 JSONL log，若發現主機使用者 Skill、原始 Codex Skill、repo `node_modules`、套件管理器、網路命令、git、MCP/web-search 或工作區外暫存路徑，就拒絕發布該次輸出。官方 `DESIGN.md` lint 只由外層 pinned evaluator 執行。CLI 接受 requested identifier 不代表回報 backend snapshot；manifest 不猜解析版本。

既有 showcase 呼叫維持 `run_claude_case.sh <haiku|sonnet|opus> <固定 showcase 目錄>`；v5 使用 `run_claude_case.sh <haiku|sonnet> --case <fixed-v5-case>`。Codex 對應使用 `run_codex_case.sh <gpt-5.4-mini|gpt-5.4> --case <fixed-v5-case>`。新式呼叫不接受任意 target 路徑，runner 只依 `model × case` allowlist 導出輸出目錄。

## 後續完整矩陣

後續正式執行一律使用 `run_product_flow_evaluation.py`，並為每一輪提供全新 evaluator-owned `--target-root`。單一命令依序完成 Codex generation、pinned `DESIGN.md` clean gate、Playwright audit 與 screenshot inventory：

```bash
RUN_ROOT=/absolute/evaluator-owned/product-flow-run
npm run eval:product-flow -- \
  --provider codex \
  --model gpt-5.4-mini \
  --target-root "$RUN_ROOT/targets" \
  --generation-output "$RUN_ROOT/generation.json" \
  --design-output "$RUN_ROOT/design-md.json" \
  --visual-output "$RUN_ROOT/visual.json" \
  --screenshot-dir "$RUN_ROOT/screenshots"
```

每個 generation case 預設最多嘗試三次；只有 inactivity timeout 與一般 generation failure 會把前次 bounded diagnostic 交給 fresh attempt。Hard-runtime、output-limit、contract/security policy rejection、model resolution、本機設定與不可恢復 infrastructure failure 不盲目重試，需先分類與明示 remediation。只要 runner output 持續推進，inactivity deadline 就延後且不消耗失敗 streak，另有 hard ceiling。`DESIGN.md` lint 與 screenshot capture 也各有自己的 bounded retry policy；若 DESIGN.md 有 findings，外層 evaluator 會封存當輪證據，只重生受影響 case，將官方訊息以 bounded feedback 傳回，直到 lint clean 或 fuse。缺少固定 verifier 時，實際 Skill 先依 lockfile／精確版本安全安裝到 project/evaluator cache；不得 global install 或改產品 runtime dependency。Mobile 使用 `390×844` CSS viewport、Android Chromium UA、touch、`isMobile=true` 與 DPR 3，不只是改變視窗大小。每次 attempt 都保留在 generation ledger；全部 case、clean DESIGN 與完整 PNG inventory 才回報 execution complete。repair-required visual issue 會保留網站與截圖、輸出結構化診斷並讓 benchmark 非零；一般 Skill 使用則自動回送 AI 修復。修復後以相同路徑加 `--resume`，舊 attempt 不覆蓋。

成功執行另由 evaluator 產生 `run-manifest.json`，記錄 `run_id`、固定 case ID/target、auth mode、Claude CLI path/version、請求的 model alias、runner/brief/trusted context/output hashes 與清除的環境變數名稱。Claude CLI 若未回報 alias 實際解析到的完整 model ID，manifest 會明確記為 `not_reported_by_cli`，不猜測 resolved exact model。

## 防作弊原則

- 實作模型不得修改 evaluator-owned tests、schema 或預期條件。
- 靜態訊號只能證明原始碼存在；功能必須用瀏覽器結果驗證。
- 視覺盲審只看 brief、程式、screenshots 與 raw evidence，不看產生模型的自評。
- 只有經選定、附 provenance 且仍符合 claim boundary 的 screenshots／summaries 進 repo；raw traces、暫存報告與 rejected quarantine 留在 evaluator-owned repo 外目錄。提交的截圖不得被誤當 regression baseline 或品質分數。

`weak-model-showcase/.wow-evidence.json` 若仍存在於本機 checkout，是已由 `.gitignore` 排除的 legacy v1 scratch ledger；它位於 implementation workspace、含舊式絕對路徑，因此不屬 release evidence，也不得交給目前 scorer 當可信 ledger。新評測一律使用 repo 外 evaluator root，讓 `ledger.json`、`policy.json`、`artifacts/` 與唯一 model-writable 的 `workspace/` 分離，並在每次 ledger `run` 明示 `--cwd <evaluator-root>/workspace`。
