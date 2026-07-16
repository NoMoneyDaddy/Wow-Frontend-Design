# 平台與執行環境支援

在宣稱可攜性、安裝到新 host、進入 CI／remote sandbox，或選擇 browser／device 證據前，先查這份文件。

本 repository 將這一版的固定支援快照收在 [`evals/platform-support.json`](evals/platform-support.json)，官方來源座標則綁定於 [`platform-support-sources.json`](wow-frontend-design/references/platform-support-sources.json)。快照不含後續查核排程，只描述目前版本；若未來版本選擇重做研究，必須產生新的已審查快照，不能把會變動的上游網頁默認成永久事實。

查詢目前尚未完成或曾失敗的 cell：

```bash
python3 wow-frontend-design/scripts/validate_platform_support.py \
  evals/platform-support.json --repository-root . --report
```

## 證據階段要逐字解讀

- `official_status` 只表示上游官方文件怎麼寫，不是本 repository 的測試證據。
- `repository_status` 只描述這個專案版本內已簽入的證據。
- `checks` 分開 install、discovery、invocation、implementation、browser 與 visual；前一階段通過，不能自動升級後一階段。
- `historic_only`、`partial`、`not_run`、`failed` 必須保留，不能壓成一個「支援」。
- Artifact 存在且 schema 合法，不代表內容語意為真。Validator 只防止 inventory、來源綁定與路徑腐化。

## 依 host 能力路由，不依品牌名稱猜測

1. 偵測實際可用的 host、安裝 scope、可寫 root、runtime、shell、network、package manager、browser／screenshot 與 model provenance。
2. 只安裝到 caller 授權的 project、user Skill 目錄或 evaluator cache。除非 host 明示會同步，remote session 不會繼承本機 Skill。
3. 宣稱 host 已載入 Skill 前，先跑 read-only discovery smoke。複製目錄或 installer 成功只能算 install 結果。
4. Host 無法載入完整 Skill 時，prompt-only adapter 必須標成降級 cohort，不能把 prompt injection 說成原生 discovery。
5. 不讓模型自行推論平台支援或能力 tier。外部編排選起始 profile；實際 runtime 事件只能維持或降級。

## 作業系統與 harness 邊界

封裝的指引與 Python validators 比完整 evaluator 更容易攜帶。目前已發布的完整 generation／evidence harness 假設 POSIX Bash、process group、POSIX resource control、Node.js 22 與固定的 Playwright／Chromium evaluator。Native Windows 完整 harness 尚未驗證；WSL 或 Git Bash 的官方說明也不等於本 repo 測試。既有已發布 CI 證據仍只有 Ubuntu、Python 3.12 與 Node.js 22；workflow 已新增 macOS／Windows 的 Python 3.12 portable contract smoke，但在遠端 jobs 實際完成前不升級這兩格。

新增 OS 證據前，先把 host OS／version、architecture、shell、Python、Node、package manager、browser revision、locale、timezone 與相關 fonts 寫進 checked-in 或 immutable evaluator artifact，再分別執行 install → discovery → invocation → implementation → browser → visual。

`scripts/capture_runtime_profile.py` 可記錄安全的 OS／Python 與 caller declarations，不會讀取 hostname、username、home、IP、完整 environment，也不會自行執行 command 或 network probe。宣告的 Node／browser／font profile 仍需和 setup log、lockfile 或 browser report 綁定，不能單獨當成通過證據。

## Browser 與 mobile 邊界

- Chromium 證據只適用於固定的 Chromium revision 與已發布 cohort 的精確 routes／states。
- Playwright 提供 Firefox／WebKit，不代表本 repository 已測過。Patched WebKit 不是實體 Safari；Android Chromium emulation 也不是實體 Android 手機。
- 只改 viewport 寬度不能當 mobile 證據。可用 emulation 時，要記錄 viewport、screen、DPR、user agent、touch、`isMobile`、orientation、visual viewport 與 safe-area 假設。
- 實體 iOS Safari、實體 Android Chrome、assistive technology 與 OS font rendering，在指定目標實跑前都維持 `UNVERIFIED`。

## Remote 與受限環境

使用 workspace-local 或 evaluator-cache 工具、精確 pin，安裝時關閉 lifecycle scripts。若 home 唯讀、沒有 network、browser 無法啟動或 package 不能安裝，保留 implementation 並執行最強的可用 static checks。無法取得的 rendered claim 要標成 `UNVERIFIED`，不能把缺工具轉成 visual pass。

只重試可恢復錯誤。持續輸出可在 hard ceiling 內延後 inactivity deadline；permission、security、model resolution、unsupported runtime 與 deterministic policy failure 必須先有明確 remediation，不能盲目重試。

## Model provenance

記錄 provider、requested identifier、host 有回報時的 resolved identifier、host／version、Skill revision、adapter、toolchain 與 evaluator revision。Host 接受 model flag 不代表已證明實際 resolved backend；不得把單一 model、alias 或 cohort 推廣到同 host 的所有模型。
