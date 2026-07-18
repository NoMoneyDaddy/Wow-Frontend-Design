# Agent Skills 相容性與腳本支援

本專案只維護一份規範性 Skill：`wow-frontend-design/SKILL.md`。模型品牌不是相容性維度；host 只要正確實作 [Agent Skills specification](https://agentskills.io/specification)，就應載入同一份 package。Host 安裝與 discovery 差異見 [`INSTALL.md`](INSTALL.md)。

機器可讀快照位於 [`evals/platform-support.json`](evals/platform-support.json)，官方來源座標位於 [`platform-support-sources.json`](wow-frontend-design/references/platform-support-sources.json)。查詢未完成或不支援的 cell：

```bash
python3 wow-frontend-design/scripts/validate_platform_support.py \
  evals/platform-support.json --repository-root . --report
```

## Package

- `SKILL.md` frontmatter、相對 references、scripts、license 與 UI metadata 由 installability validator 檢查。
- Package 合法不代表某個 host 已 discovery，也不代表某個模型已完成產品任務。
- 不在 Skill 內依模型品牌或大小分叉規則；模型只屬外部 evaluator 參數。

## 安裝後 scripts

現行 package 有 18 個非測試 Python entrypoints：

- 16 個 Python 3.9+ standard-library core scripts；primary CI 使用 Python 3.14.6。
- `validate_installability.py` 的 repository-aware 模式需要 `git`。
- `evidence_ledger.py` 只執行 caller 明示且 policy 允許的 command；command 自身的可攜性與副作用不由 Skill 保證。

現行完整 Python suite 已在本機 macOS checkout 通過。Ubuntu、macOS、Windows portable smoke 已配置，但本 revision 尚未保存完成的遠端 job，因此三個 CI cell 都維持 `not_run`。

## 現行 evaluator

`evals/` 不隨一般 Skill 任務自動執行。唯一受控建置入口是 `npm run build:current`，其依賴：

- POSIX process groups 與 resource controls；
- Python 3.9+、Node.js 22、authenticated Codex CLI；
- pinned `@google/design.md`、Playwright Chromium 與 Axe。

Runner 以 exact-output staging、fresh Playwright context、deterministic finding、bounded repair packet、收斂 fuse 與原子發布維持證據邊界。現行 unit 與 browser smoke 在本機 macOS 通過；Linux 遠端 job 尚未保存，native Windows 完整 runner 明確不支援，但 portable Skill scripts 不受這項限制。

## Browser

Pinned Playwright Chromium 已有本機 macOS 的現行 runtime、network、visible-content、root-overflow 與 Axe smoke evidence。`visual` 維持 `not_run`：這不是 screenshot acceptance、獨立美感審查、完整 WCAG conformance、branded Chrome／Edge、Firefox、WebKit、實體 Safari 或實體手機證據。

每次完成宣告必須來自最新 source/build 與 fresh context。缺 browser 或 network 時，安全的 static／implementation 工作可以繼續，但受影響的 rendered claim 必須標為 `UNVERIFIED`。

`capture_runtime_profile.py` 只記錄 bounded OS／Python 欄位與 caller declarations；不讀 hostname、username、home、IP 或完整 environment，也不自行執行 command／network probe。Caller 宣告的 Node、browser 或 font profile 必須再綁定 setup log、lockfile 或 browser receipt。
