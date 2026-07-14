# Third-party notices

本專案程式、文件與自製展示資產採 [MIT](LICENSE)。下列資訊用來區分研究來源、開發依賴與實際再散布內容，不是法律意見。

## 研究來源

`wow-frontend-design/references/external-sources.lock.json` 以完整 Git revision 記錄本輪直接研究的 GitHub repository、檔案路徑與當時辨識到的授權。這些來源用來比較方法、找反例並獨立重寫規則；本專案沒有直接複製其 Skill 文字、程式或視覺資產。

- `MIT`、`Apache-2.0` 等值只描述鎖定來源在研究時辨識到的授權，不會自動延伸到同一作者的其他 repo、branch、目錄或資產。
- `NOASSERTION` 代表沒有足夠證據確認可重用授權。此類來源只可作事實研究與方法比較；禁止複製其受著作權保護內容。
- 真正要引入上游程式、字體、圖片、SVG、Lottie、影片或文案時，必須重新檢查精確版本、檔案層級授權、notice、商標與再散布條件，並新增對應 provenance。
- 論文、標準與官方技術文件的連結是引用依據，不是把其全文納入 MIT 授權。

## Evaluator 開發依賴

根目錄 `package-lock.json` 固定瀏覽器 evaluator 的開發依賴；它們不會被 `gh skill install` 複製進 `wow-frontend-design/`：

| Package | Version | License | Purpose |
| --- | --- | --- | --- |
| `playwright` | 1.61.1 | Apache-2.0 | 瀏覽器擷取與互動重播 |
| `playwright-core` | 1.61.1 | Apache-2.0 | Playwright 核心 runtime |
| `fsevents` | 2.3.2 | MIT | npm 的 macOS optional dependency |

實際安裝內容與授權以 `package-lock.json`、各 package 內附 LICENSE 及其官方發行內容為準。
