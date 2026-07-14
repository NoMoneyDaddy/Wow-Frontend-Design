# Third-party notices

本專案程式、文件與自製展示資產採 [MIT](LICENSE)。下列資訊用來區分研究來源、開發依賴與實際再散布內容，不是法律意見。

## 研究來源

`wow-frontend-design/references/external-sources.lock.json` 以完整 Git revision 記錄本輪直接研究的 GitHub repository、檔案路徑與當時辨識到的授權。這些來源用來比較方法、找反例並獨立重寫規則；本專案沒有直接複製其 Skill 文字、程式或視覺資產。

- `MIT`、`Apache-2.0` 等值只描述鎖定來源在研究時辨識到的授權，不會自動延伸到同一作者的其他 repo、branch、目錄或資產。
- `NOASSERTION` 代表沒有足夠證據確認可重用授權。此類來源只可作事實研究與方法比較；禁止複製其受著作權保護內容。
- 真正要引入上游程式、字體、圖片、SVG、Lottie、影片或文案時，必須重新檢查精確版本、檔案層級授權、notice、商標與再散布條件，並新增對應 provenance。
- 論文、標準與官方技術文件的連結是引用依據，不是把其全文納入 MIT 授權。

本輪 Sitemap／Wireframe 規則另外參考下列網路來源；只採用可交叉驗證的方法與邊界，沒有重製其文章文字或圖像：

- [W3C WAI Page Structure](https://www.w3.org/WAI/tutorials/page-structure/) 與 [Information Design curriculum](https://www.w3.org/WAI/curricula/designer-modules/information-design/)：頁面區域、標題、命名、分組與替代表現。
- [GOV.UK Making prototypes](https://www.gov.uk/service-manual/design/making-prototypes)：原型保真度、測試與可丟棄邊界。
- [Nielsen Norman Group Wireflows](https://www.nngroup.com/articles/wireflows/)、[Card sorting](https://www.nngroup.com/articles/card-sorting-definition/) 與 [Tree testing](https://www.nngroup.com/articles/tree-testing/)：流程表示與資訊架構研究選型。
- [Google Search Central Build and submit a sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap) 與 [sitemaps.org protocol](https://www.sitemaps.org/protocol.html)：XML Sitemap 語法、數量／大小與 crawl hint 邊界。
- [DayDayDing Wireframe 技巧](https://daydayding.com/wireframe-skills-tools-for-new-uiuxdesigners/#Wireframe_%E6%8A%80%E5%B7%A7_4%E7%95%99%E6%84%8F%E8%B3%87%E8%A8%8A%E5%B1%A4%E7%B4%9A)：實務提示來源。未採用缺少可靠依據的「負向流程出現頻率為正向流程三至十倍」數字，也不把其工具盤點視為現行官方比較。

## Evaluator 開發依賴

根目錄 `package-lock.json` 固定瀏覽器 evaluator 的開發依賴；它們不會被 `gh skill install` 複製進 `wow-frontend-design/`：

| Package | Version | License | Purpose |
| --- | --- | --- | --- |
| `playwright` | 1.61.1 | Apache-2.0 | 瀏覽器擷取與互動重播 |
| `playwright-core` | 1.61.1 | Apache-2.0 | Playwright 核心 runtime |
| `fsevents` | 2.3.2 | MIT | npm 的 macOS optional dependency |

實際安裝內容與授權以 `package-lock.json`、各 package 內附 LICENSE 及其官方發行內容為準。
