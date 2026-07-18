# Agent Skills 相容性與腳本支援

本專案把「Skill package 相容性」和「repository 腳本可執行性」分開。模型品牌不是相容性維度；只要 host 正確實作 [Agent Skills specification](https://agentskills.io/specification)，就應依同一份 `SKILL.md` 與相對 references 載入。Host 的安裝路徑與操作介面差異另見 [`INSTALL.md`](INSTALL.md)，不維護逐模型支援表。

機器可讀的 runtime 快照位於 [`evals/platform-support.json`](evals/platform-support.json)，官方來源座標位於 [`platform-support-sources.json`](wow-frontend-design/references/platform-support-sources.json)。這是本版快照，沒有自動或預定的下次查核日期。

查詢未完成、失敗或明確不支援的 runtime cell：

```bash
python3 wow-frontend-design/scripts/validate_platform_support.py \
  evals/platform-support.json --repository-root . --report
```

## 1. Agent Skills package

- `SKILL.md` frontmatter、名稱、相對 references、scripts、license 與 UI metadata 由 installability／Skill validator 檢查。
- Package 合法不代表某個 host 已安裝或當次 session 已 discovery；這是 host 整合問題，不是模型支援問題。
- 不在 Skill 內依 `GPT`、`Claude`、`Gemini`、`mini`、`Haiku`、`Opus` 等名稱分支。模型路由只屬於外部 evaluator 的品質／成本策略。

## 2. 安裝後隨 Skill 提供的 Python scripts

Validator 會把 `wow-frontend-design/scripts/` 內所有非測試 Python entrypoint 和 matrix 做精確比對；新增 script 卻沒有聲明 runtime profile，CI 會失敗。目前共 21 個 entrypoints：

- 19 個 Python 3.9+ standard-library core scripts；primary CI 使用 Python 3.14.6。
- `validate_installability.py` 在 repository-aware 模式需要 `git`。
- `evidence_ledger.py` 只執行 caller 明示且 policy 允許的外部 command；該 command 自身的跨平台行為不由 Skill 保證。

目前完整 Python 測試在 Linux CI 通過；macOS 有本機開發證據但尚未形成等價 CI artifact。Ubuntu／macOS／Windows 的 portable contract smoke 已配置，macOS 與 Windows 在遠端 jobs 完成前維持 `not_run`。

## 3. Repository evaluator，不是 Skill runtime

`evals/` 的 generation／browser／evidence harness 是開發者評測工具，不隨一般 Skill 任務自動執行。舊 cohort validator 與 prompt fixture 保留在 `evals/archive/`，不再複製到每次 Skill 執行：

- 正式 `build:current` runner 依賴 POSIX process group／resource control、Python 3.9+、Codex CLI、Node.js 22、pinned `@google/design.md`、Playwright Chromium 與 Axe。
- 其他歷史 runner 另依賴 POSIX Bash；所有 evaluator 入口仍與安裝後的 Skill runtime 分離。
- Linux 有 CI 證據；macOS 為局部開發證據。
- Native Windows 完整 harness 本版明確不支援；portable Python scripts 不受這項限制。
- WSL 可能滿足 POSIX 前提，但本版沒有保存 end-to-end run，因此維持 `not_run`。

## 4. 主流 browser backend

- Pinned Playwright Chromium：已有 v6 browser／visual 證據。
- Branded Chrome／Edge channels、Playwright Firefox、Playwright WebKit：列入主流檢查範圍，但本版尚未實跑。
- Playwright WebKit 不等於實體 Safari；browser mobile emulation 也不等於實體 iOS／Android。實體裝置不列入本版支援承諾。

## 5. Remote／sandbox 行為

執行前只探測實際能力：可讀／可寫 root、Python、必要 command、network、browser 與 screenshot。缺 browser 或 network 時，安全的 static／implementation 工作可以繼續，但相關 rendered claim 必須標成 `UNVERIFIED`。

`scripts/capture_runtime_profile.py` 只記錄安全的 OS／Python 欄位與 caller declarations；不讀 hostname、username、home、IP、完整 environment，也不自行執行 command 或 network probe。Caller 宣告的 Node／browser／font profile 必須再綁定 setup log、lockfile 或 browser report，不能單獨升級成通過證據。

只重試可恢復錯誤。持續輸出可在 hard ceiling 內延長 inactivity deadline；permission、security、unsupported runtime 或 deterministic policy failure 必須先有明確修復方式。
