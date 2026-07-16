# Product flow v6 latest-Skill repair notes

日期：2026-07-15

## 範圍與設計論點

- 對象與情境：保留 8 個既有測試站、12 routes、資料、互動與各自視覺語法；只修正排版、locale、空間配置與可操作流程。
- 核心概念：繁中介面先讓「任務、內容、動作」形成連續閱讀序列。正文使用完整對齊欄與瀏覽器自動換行；只有展示標題、引句或真的語意停頓能強制斷行。
- 內容優先序：主標與主要任務 > 狀態與選項 > 摘要 > 裝飾。留白表達群組關係，不是固定百分比，也不是把正文壓窄後留下無意義右側空洞。
- 標題規則：避免用 `ch` 把繁中標題預設壓成狹長柱；先讓容器、語意片語、`line-break`、`word-break: auto-phrase` 與 `text-wrap` 決定自然換行。
- 語系規則：繁中 UI 保留必要術語，但首次出現要有中文語境；無功能的單獨英文標語、`modal`、`shortlist`、`fallback`、`Step` 等改為中文或中文加括號術語。
- 手機規則：Android Chromium mobile-device emulation 同時設定 mobile UA、touch、screen、visual viewport 與 DPR；不是只縮小 viewport。實體手機、Safari/Firefox 與 OS 輔助科技仍未認證。
- 色彩與元件：不重配既有色票，不替所有元件加特效。框線、文字、表面、動態與特殊效果維持語意角色、現有設計系統及實測狀態。

## 8 案最新修復

| 案例 | 最新 Skill 修復 |
| --- | --- |
| 風場維修派工 | 主標改用嚴格 CJK 換行與字型相對寬度，避免 Latin `ch` 造成錯誤斷行；關閉瀏覽器原生英文驗證泡泡，保留頁內繁中錯誤、焦點回復與 `aria-invalid`。 |
| 繁中字體樣張 | 解除主標狹窄上限，正文使用完整欄；`fallback` 改為「備援字型／備援版面」，保留術語語境與直書返回橫書流程。 |
| 修繕咖啡館 | 主標回到同一閱讀層級，解除說明欄偏右與過窄限制，讓正文與表單自然對齊。 |
| 夜市過敏原 | 把繁中說明 measure 改為字型相對 `em` 上限，避免 `ch` 造成不必要右側空白。 |
| 版稅報表 | hero 重新對齊主標與摘要；正文使用可讀欄，`tabular figures` 以「等寬數字」說明。 |
| 循環包材配置器 | 由三個狹窄欄改為目的／操作兩欄，摘要跨欄；移除沒有資訊功能的 CSS 模切圖，取消遮擋式 sticky，翻譯頁首與步驟文字。 |
| 口述歷史典藏 | 三頁解除 `11ch–18ch` 正文／標題限制，特色內容使用完整欄與自然換行，`media fallback` 改為「媒體替代說明」。 |
| 補助審查台 | 解除主標與說明狹窄限制，只有「整理出」保留語意片語；`shortlist`、`modal` 改為「候選」、「對話框」。 |

所有案例相對上一個已發布 repair root 都有至少一個輸出變更；manifest 記錄來源 manifest、before hash、changed output、Skill、研究筆記與最終視覺報告 SHA-256。

## 研究落實與邊界

- 中文排版：W3C CLREQ、W3C ruby、CMEX 注音排版與 `Bopomofo_on_Web` 用來校正換行、直排、ruby／注音、標點與跨引擎邊界；實際字型、瀏覽器與內容仍須 render 驗證。
- 網頁正文：Pixelcake、Piv、Four Noas、IAMTIE、BFA 與相關繁中實務文章提供段落、留白、行長與內容層級的問題樣本；採用關係原則，不把文章中的固定數字升格為 release gate。
- Layout 與 hierarchy：Figma layout／visual hierarchy、YoungDay、BFA 與 UXPilot 支持依任務選 grid、split、asymmetry、editorial、gallery 等模式；F/Z、三分法、固定字級比與固定欄數只作假設，不作注視或轉換率證明。
- 字型與色彩：Figma 字型／色彩文章只作 discovery。繁中仍依實際 glyph、fallback、font loading、locale、gamut、語意角色與 rendered contrast 決策；OKLCH 可進 `DESIGN.md` 與 CSS，但須 sRGB fallback、工具鏈與實際像素驗證。
- 字級與字型來源：GogoShark、PixelCake 與 Apple `DESIGN.md` 樣本支持比較角色字級、標題／內文對比、繁中字型 coverage 與 responsive display ladder；固定 px／pt、負字距、SF Pro 替代、字型排行榜與二手授權摘要不升格為 gate。MindStudio 的品牌分類只作候選方向，Notion／Claude／Stripe／Uber README 實為外站 redirect，且外站預覽於 Chrome 擷取時全部失敗；`getdesign@0.6.24` 抓取的六份樣本全部未通過官方 clean gate，且三份與 repo revision 不同；`design-ai` 也只作 prompt catalogue。這些來源都不能取代官方 alpha schema、來源證據、lint 與實際 render。
- Webfont：`elvisdragonmao/emfont` 於 2026-07-15 重查 HEAD，仍是已鎖定的 `85158ad`。動態 client 仍會讀取目標節點 `textContent`、input／textarea value 與 placeholder 並 POST 字元；敏感／登入範圍維持禁止預設啟用，優先採 versioned self-hosted subset 與完整 fallback。
- Motion／icon／3D：Lordicon、Lottie Web、LottieFiles 與相關 motion/3D Skills 用來建立「目的、最小充分技術層、靜態語意幀、reduced result、失敗 fallback、cleanup」流程；不自動把動畫或特效套到所有元件。`greensock/gsap-skills@aed9cfd` 另補入 timeline、ScrollTrigger、React scope/cleanup 與頁面敘事路由；其 `refreshPriority` 矛盾、Nuxt mount cleanup 錯誤、`duration: 0` 簡化與效能過度宣稱不採用。
- Skill 生態：`copyleftdev/sk1llz@a988a7559b4d758706e622be18eed68a18a88c0c` 的 manifest、分類與 contribution checklist 可取；persona 權威、可變 `master` 安裝、未驗證路徑及大量隱形 Unicode 不匯入。
- Material：`material-components/material-web@b4de401eb665ec63474f39319a4ba8f2145974cc` 是 `@material/web` 的官方實作證據。它目前為 maintenance mode，`tokens/versions` 可能在 minor/patch 破壞相容；Skill 只在專案已使用它時依 lockfile 與實際元件 API 路由，不把 Material 值當通用視覺預設。
- 來源鎖：完整 GitHub revision、license 與選定 paths 位於 `wow-frontend-design/references/external-sources.lock.json`。未明確授權內容只研究與獨立摘要，不複製表述、程式或資產。

## 最終驗證契約

- 模型固定為 `gpt-5.4-mini`；8 products、12 routes、4 device profiles。
- 每案桌機／手機互動狀態，加上每 route 的 desktop／tablet／mobile／compact-mobile base state，共 64 張 PNG。
- evaluator 檢查 layout overflow、裁切、碰撞、obstruction、窄欄、touch target、reading rhythm、forced break、non-wrapping／underfilled prose、四行以上過度壓縮與一字末行 heading flow、DOM order、intro displacement、未翻譯 UI、reduced motion、console、network 與跨頁 token drift。
- 同一錯誤修正三次仍不通過才熔斷；持續輸出會延長 inactivity timeout。三輪 Darwin 候選共產生 192 張截圖，最終仍有 6 案 findings，因劣於基準而未晉級。
- 基準產物依最終 evidence 修正包材 sticky 遮擋、口述歷史寬卡窄文、補助審查公開 hook／dialog title track 與字體樣張 mobile title step；最終 post-orphan-gate 完整重驗 64/64，8/8 targets 無觀察到上述 deterministic 問題。
- `DESIGN.md` 另由 pinned `@google/design.md@0.3.0` 正式 lint；乾淨格式仍不等於 runtime conformance，兩者都保留證據。

## 模型路由補強

- Agent Skills 規格沒有 portable `model` selector；模型選擇、版本解析與起始 lane 屬於 caller／orchestrator，不由 Skill body 問模型自報。
- capability profile 改為 task × locale × surface × risk 的 schema v2 cell，另綁定 Skill、adapter、toolchain 與 evaluator revision；只有 eligible independent runs 可升到 `STANDARD`，infrastructure failure 分開記錄。
- 執行期採單向自動降級：進度持續就延長 timeout；一般 repair finding 先自修正；同一錯誤三次才熔斷並保留最佳產物；缺 browser／visual 只把該 gate 標為 `UNVERIFIED`；缺 mutation／權限才停止修改。
- 不用一次 generic probe 推論全域能力，也不在同一 run 自動升級。新的較高 lane 必須由外部以新 profile 與獨立證據開新 run。
- Codex benchmark 由 caller 的 `model × case` 選 reference：mini 才加入 weak-model，互動型案例加入元件，字體／典藏加入 webfonts，狀態色重案例加入 color。v6 mini 的 embedded context 由固定 190,732 bytes 降為 145,024–161,274 bytes；這只是輸入量證據，新路由尚未另跑 generation，不宣稱已變快或變好。
