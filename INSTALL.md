# 安裝與發現

`wow-frontend-design/` 本身就是符合 Agent Skills 格式的 skill 目錄。安裝只代表 host 能發現 metadata；不代表特定模型、工具、框架或品質已通過實測。

Package 相容性以 [Agent Skills specification](https://agentskills.io/specification) 為準，不按模型品牌維護不同版本。Host 安裝路徑、scope 與 discovery UI 仍可能不同；installer 能放置檔案不等於當次 session 已載入。Python、OS、POSIX evaluator 與主流 browser backend 的實測邊界見 [`PLATFORM_SUPPORT.md`](PLATFORM_SUPPORT.md)與 [`evals/platform-support.json`](evals/platform-support.json)。

## 自動辨識不等於未授權安裝

- 安裝完成後，支援 Agent Skills implicit invocation 的 host 可依 `SKILL.md` 的 `name`／`description` 自動辨識任務並啟用；Codex metadata 已設定 `allow_implicit_invocation: true`。不支援的 host 仍須用 `$wow-frontend-design`、`/wow-frontend-design` 或 wrapper 明確載入。
- 尚未安裝時，模型不能憑空知道可信來源。使用者、host registry 或 caller 必須提供 repository／catalogue 座標與允許的 scope；AI 才能代辦 preview、固定 revision、安裝與 discovery smoke。不得自行搜尋同名套件後安裝，也不得覆寫既有 Skill。
- Skill 執行時可自動辨識缺少的「驗證用工具」，沿用 lockfile；沒有 pin 才解析最新穩定相容版、固定精確版本，安裝到專案或授權的 evaluator cache 並續跑。這不授權 global install、產品 runtime dependency、框架遷移、lockfile family 變更或 lifecycle scripts。

## 5 分鐘成功路徑

先取得目前 `main` 的完整 commit SHA；預覽後才把同一 SHA 安裝到指定 host。正式環境應改用團隊已審查的 SHA。此 repo 目前沒有 GitHub Release，因此不要把浮動 `main` 當成 production pin。

```bash
PIN="$(gh api repos/NoMoneyDaddy/Wow-Frontend-Design/commits/main --jq .sha)"
printf '%s\n' "$PIN"
gh skill preview NoMoneyDaddy/Wow-Frontend-Design "wow-frontend-design/SKILL.md@$PIN"
gh skill install NoMoneyDaddy/Wow-Frontend-Design wow-frontend-design/SKILL.md \
  --agent codex --scope user --pin "$PIN"
gh skill list --json skillName,sourceURL,scope,version,pinned,path
```

重新開啟一個 session，做不修改檔案的 discovery smoke：

```text
Use $wow-frontend-design to audit this repository read-only. Report the detected
project type, mutation boundary, available verification capabilities, and exact
evidence ceiling. Do not edit files or install tools.
```

成功條件不是只看 `gh skill list`：host 必須真的觸發 Skill，並回報 `AUDIT`、專案類型、能力與不誇大的 evidence ceiling。Claude Code 把 `--agent codex --scope user` 改為 `--agent claude-code --scope project`，然後以 `/wow-frontend-design` 執行同一 smoke。

需要留下可比較的 host provenance 時，用不執行外部 probe 的 helper，把 stdout 重新導向 evaluator-owned artifact；`node`／browser／font 值是 caller declaration，仍須綁定 setup log 或 browser report：

```bash
python3 wow-frontend-design/scripts/capture_runtime_profile.py \
  --environment-kind local --shell-name zsh \
  --node-version v22.18.0 --network available
```

> Claude Code remote：本機 `~/.claude/skills/` 不會自動同步到 remote sandbox。最可靠做法是在 remote 內安裝到專案 `.claude/skills/wow-frontend-design/`。Remote 的 home 可能是暫時性或不可寫；沒有 browser／vision 時，Skill 應交付網站與靜態證據，但把 rendered claims 標為 `UNVERIFIED`。

## AI 直接安裝（Codex）

在 Codex 對話貼上：

```text
Use GitHub CLI to preview and install wow-frontend-design from
NoMoneyDaddy/Wow-Frontend-Design at commit <FULL_COMMIT_SHA> for Codex user scope.
Do not overwrite an existing skill or execute bundled scripts during installation.
Report the installed path, source URL, revision, scope, and host.
```

也可直接請 `$skill-installer` 安裝同一個完整 commit 的 `wow-frontend-design` 子目錄；目的目錄已存在時必須中止，不覆寫同名 skill。安裝後若未出現，重新啟動 Codex。

## 官方 GitHub CLI：先預覽，再一行安裝

`gh skill` 自 GitHub CLI 2.90.0 起內建，目前仍是可能變動的 preview；支援 Codex、Claude Code、GitHub Copilot、Gemini CLI 與多個其他 agent host。先用 `gh --version` 確認版本，再唯讀預覽完整 skill tree：

```bash
gh skill preview NoMoneyDaddy/Wow-Frontend-Design wow-frontend-design/SKILL.md
```

再指定 host 與 scope；以下安裝到 Codex 使用者範圍：

```bash
gh skill install NoMoneyDaddy/Wow-Frontend-Design wow-frontend-design/SKILL.md --agent codex --scope user
```

正式部署加上完整 commit；未來有已審查 release tag 時也可固定該 tag：

```bash
gh skill install NoMoneyDaddy/Wow-Frontend-Design wow-frontend-design/SKILL.md --agent codex --scope user --pin <release-tag-or-full-sha>
```

把 `--agent` 改為 `claude-code`、`github-copilot` 或 `gemini-cli` 即可導向該 host；用 `gh skill list --json skillName,sourceURL,scope,version,pinned,path` 驗證來源與安裝位置，再跑上方 discovery smoke。preview 命令、參數或 metadata 可能隨 GitHub CLI 版本改變；正式流程固定 CLI 版本與 skill commit。

## Host 原生方式

| Host | 使用者範圍 | 專案範圍 | 安裝／發現驗證 |
| --- | --- | --- | --- |
| Codex | `~/.agents/skills/wow-frontend-design/` | `.agents/skills/wow-frontend-design/` | 輸入 `$wow-frontend-design`，或以 `/skills` 查找 |
| Claude Code | `~/.claude/skills/wow-frontend-design/` | `.claude/skills/wow-frontend-design/` | 輸入 `/wow-frontend-design`；新建頂層 skills 目錄後必要時重啟 |
| GitHub Copilot | `~/.copilot/skills/` 或 `~/.agents/skills/` | `.github/skills/`、`.claude/skills/` 或 `.agents/skills/` | 用 Copilot／`gh skill` 列出後，以符合 description 的請求驗證 |
| Gemini CLI | `~/.gemini/skills/` 或 `~/.agents/skills/` | `.gemini/skills/` 或 `.agents/skills/` | `/skills list`、`/skills reload`；也可用下方官方 CLI |

Gemini CLI 可從 remote skill URL 安裝；workspace scope 不污染使用者全域：

```bash
gemini skills install https://github.com/NoMoneyDaddy/Wow-Frontend-Design/tree/main/wow-frontend-design --scope workspace
```

若已 clone repo，可用無 Node、無 telemetry 的本機複製：

```bash
mkdir -p .agents/skills
cp -R wow-frontend-design .agents/skills/
```

也可用 GitHub CLI 從目前 checkout 安裝；local 模式用 skill name，不用 remote 的 `.../SKILL.md` 路徑語法：

```bash
gh skill install . wow-frontend-design --from-local --agent codex --scope project
```

目的目錄已存在時不要直接覆寫。先比較版本與 diff，再改名備份或由使用者明示升級策略。複製後保留 skill 內的 `LICENSE`。

## Claude.ai 與 API

Claude.ai custom skills、Claude API workspace skills、Claude Code filesystem skills彼此不自動同步。Claude.ai 需上傳 skill zip；Claude API 需先建立 custom skill/version 再以 `skill_id` 掛載；兩者的資料保留、code execution、network 與 package 限制不同。不要把 Claude Code 安裝成功轉述成 API 或 claude.ai 已安裝。

## 不原生支援 Agent Skills 的模型

模型本身不負責發現 skill；agent host／wrapper 必須：

1. 掃描 `SKILL.md` frontmatter 的 `name` 與 `description`；
2. 任務匹配時載入完整 `SKILL.md`；
3. 依路由按需讀取相對 `references/`；
4. 只在授權工具存在時執行 `scripts/`；
5. 把缺 browser、vision、command、write 或 context 能力轉成明示 evidence ceiling。

若 wrapper 會跨模型編排，不要把 `MODEL_TIER=strong` 交給模型自行解讀。由 wrapper 建立 evaluator-owned schema-v2 capability profile，先以 `scripts/route_model.py` 選 lane；再把真實執行事件交給 `scripts/runtime_downgrade.py` 單向降級。Skill 本身不切換模型，也不允許同一 run 自行升級。

單純把整個 skill 塞進 system prompt 是 prompt adapter，不是原生安裝；必須另標 cohort，不能宣稱與 Codex、Claude Code、Copilot 或 Gemini CLI 的 discovery 行為相同。

## 版本、完整性與卸載

- production pin release tag、完整 commit 或已審查 skill version；不要浮動追蹤 `main`。`gh skill` 安裝會注入來源 metadata，供 `gh skill update --dry-run` 核對。
- 部署前驗證 `SKILL.md` frontmatter、每份 Markdown reference／adapter 都可由核心直接到達、單元測試與來源 lock。
- 記錄安裝來源、revision、hash、host/version、scope 與安裝時間。
- 停用優先於刪除；Codex 在 `~/.codex/config.toml` 使用精確絕對路徑：

  ```toml
  [[skills.config]]
  path = "/absolute/path/to/wow-frontend-design/SKILL.md"
  enabled = false
  ```

  Gemini 可用 `/skills disable wow-frontend-design`。
- 卸載只刪除使用者明確指定的那個 scope 與精確 skill 目錄；不要遞迴清除整個 `skills/`。
