# 現行評測與受控建置

本目錄只支援一份規範性標準：`wow-frontend-design/SKILL.md`。`build:current` 是唯一受控建置入口；它不維護平行 Skill 版本，也不把舊產物或舊截圖當成新證據。

`evals/` 是 repository evaluator，不屬於安裝後自動執行的 Skill runtime。一般 Skill package 仍可只靠 `SKILL.md`、按需 references、scripts 與 assets 使用。

## 受控建置

```bash
npm run build:current -- \
  --brief /absolute/path/brief.md \
  --target /absolute/path/output \
  --log-dir /absolute/path/logs \
  --output index.html
```

預設執行模型是 `gpt-5.6-sol`，reasoning effort 是 `high`。可用 `--model` 與 `--reasoning-effort low|medium|high|xhigh` 明示覆寫；receipt 只記錄請求值，不把它當成服務端已履行或品質已通過的證明。

Runner 會：

1. 把現行 Skill 複製成唯讀 snapshot，並記錄來源 hash。
2. 要求 Codex 只產生 caller 明列的相對輸出。
3. 以 process group、hard deadline、inactivity deadline、輸出 byte budget 與 exact-output inventory 約束執行。
4. 驗證 Codex log policy、輸出路徑與 `DESIGN.md` clean contract。
5. 對 HTML 以 fresh Playwright Chromium context 執行可見內容、console、resource、網路邊界、root overflow 與 Axe smoke。
6. 將 deterministic failure 壓成 bounded repair packet，讓同一模型與 reasoning effort 做最小修正；每輪只重驗受影響面。
7. 只有全部 release gates clean 時，才以原子 rename 發布 staged artifact，並寫入 runner-owned `run-manifest.json` 與 evaluator receipt。若 repair fuse 觸頂，則把最後一個已驗證 checkpoint 移到 evaluator-owned quarantine、保持 target 空白並回傳失敗 receipt；quarantine 不是可發布成品。

若獨立 Playwright evaluator 不可用，Skill 可以繼續交付 runnable artifact，但相關 rendered claim 必須是 `UNVERIFIED`。模型自己的截圖、分數或完成宣告不能取代 evaluator receipt。

Current runner 的 `status: completed` 只表示 exact-output、`DESIGN.md` clean 與 deterministic HTML/Chromium/Axe smoke 通過；它不等於 screenshot acceptance、novel discovery、獨立 craft review、完整 release matrix 或商業上線核准。需要這些 claim 時，caller 必須提供獨立的 fresh Playwright evidence plane，否則維持 `UNVERIFIED`。

## 現行檔案邊界

- `run_current_skill_build.py`：公開 CLI、repair loop、原子發布與 receipt。
- `codex_isolated_build_core.py`：受控 Codex 執行、snapshot、資源限制與 log policy。
- `current_skill_repair.py`：finding 正規化、root-cause 去重、repair packet 與收斂判定。
- `validate_design_md_clean.py`：pinned `@google/design.md` clean 驗證包裝。
- `playwright_html_smoke.cjs`：fresh Chromium/Axe acceptance smoke。
- `playwright_browser_runtime.cjs`：共用 Playwright network、popup、Service Worker 與 lifecycle policy。
- `validate_codex_log_policy.py`：bounded stdout/stderr 與敏感輸出政策。
- `product_cases.json`、`trigger_cases.json`：通用產品與 trigger fixtures，不是已發布成果。
- `platform-support.json`：現行 package、script、runner 與 browser 的 evidence-bounded 支援快照。

## 基準與 Darwin 迭代

產品交付與 Skill 優化是兩個迴路：

- 產品交付預設使用現行 production runner 設定。
- Darwin／回歸評測主要以 `gpt-5.4-mini` 明示覆寫，讓較受限模型暴露指令、排版、互動與自修正缺口。
- accepted 與 candidate 必須使用同一 brief、模型、reasoning effort、工具鎖、輸出契約與 evaluator；較強模型不得悄悄進入其中一個 arm。
- 模型名稱是 evaluator 參數，不是另一份 Skill 版本或規則集。
- 只有 held-out 改善、現行 hard gates 乾淨且獨立 rendered review 支持時，才接受 Skill 改動。

最小 benchmark invocation：

```bash
npm run build:current -- \
  --brief /absolute/path/held-out.md \
  --target /absolute/path/run \
  --log-dir /absolute/path/logs \
  --model gpt-5.4-mini \
  --reasoning-effort high \
  --output index.html
```

不要把同一批輸出反覆加入規則後再稱為 held-out。不要保存舊 screenshot cohort 來替代 fresh replay；只有最新 source/build、fresh context、明示 viewport/state 與當次 receipt 能支持當次 claim。

## 驗證

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 wow-frontend-design/scripts/validate_installability.py wow-frontend-design --repository-root .
python3 wow-frontend-design/scripts/validate_platform_support.py evals/platform-support.json --repository-root .
python3 wow-frontend-design/scripts/validate_trigger_cases.py evals/trigger_cases.json --references wow-frontend-design/references
python3 wow-frontend-design/scripts/validate_product_cases.py evals/product_cases.json
```

`npm run audit:html -- <path>` 是可選的 pinned Nu HTML Checker；它只提供 markup conformance signal，不證明視覺、互動、可及性或商業品質。
