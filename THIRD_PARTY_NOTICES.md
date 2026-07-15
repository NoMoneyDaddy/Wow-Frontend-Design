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

本輪中文排版規則另參考 [PixelCake 中文排版小技巧](https://pixelcake.com.tw/posts/chinese-typography-tips/)，並以 [W3C 中文排版需求](https://www.w3.org/TR/clreq/) 與 [CSS Text Module Level 3](https://www.w3.org/TR/css-text-3/) 交叉檢查。採用的方向是語意段落、全形標點、接近正常的內文 tracking 與較寬鬆行高；沒有照搬「所有中文一律左對齊」或全域 `word-break: keep-all`。本專案沒有重製該站文章、程式或圖像。

本輪亦檢閱 [夜月七境：中文網頁排版優化](https://piv.ink/chinese-layout-optimization/)、[我是鐵：舒適的中文文章 CSS 排版](https://www.iamtie.com/2020/09/cssarticlesetting.html?m=1)、[BFA：十項中文長文原則](https://www.bfa.com.tw/blog/ten-rules-that-make-articles-better-understood)、[白湯四物：中文網頁排版設計建議](https://www.fournoas.com/posts/chinese-web-typesetting-design-suggestions/)、[Apple 中文排版細節](https://pudge1996.medium.com/apple-awsome-typographic-details-a5705d31417) 與 [探索 Web 字元換行規則](https://pudge1996.medium.com/wrap-rule-on-web-56a375c11043)。這些 2015–2022 的文章是實務觀察，不是現行瀏覽器標準；只採納段落模式、長字串 QA、標點與標題光學檢查等可驗證方向。未採用全域 `break-all`、每字插入空白／`wbr`、DOM 改寫、絕對定位活標點、固定 `300` 內文字重或單一行高配方。技術邊界以 2026-07-03 版 [W3C CLReq Group Note Draft](https://www.w3.org/TR/clreq/) 及 [CSS Text Level 4 Working Draft](https://www.w3.org/TR/css-text-4/) 為主；兩者仍是草案，不描述成 W3C Recommendation 或跨瀏覽器實作保證。本專案沒有重製文章文字、程式或圖片。

注音／ruby 規則另參考 [CMEX 數位排版中注音調號定位方式](https://www.cmex.org.tw/page.jsp?SN=&ID=33&la=0)、鎖定 revision `f86d793b7995c276bd30a2b7146e9b6dfb34d1fc` 的 [Bopomofo on Web](https://github.com/cmex-30/Bopomofo_on_Web/tree/f86d793b7995c276bd30a2b7146e9b6dfb34d1fc)、其 2019 中英文 PDF、[W3C Ruby Markup](https://www.w3.org/International/articles/ruby/) 與 [Ruby Styling](https://www.w3.org/International/articles/ruby/styling.en)。PDF 只規範注音字串內的碼位、調號／韻尾相對位置與 OpenType shaping，不涵蓋 ruby 相對漢字的位置或視覺品質；封面公布日期仍為空白，因此本專案不把該檔案描述成可直接主張現行法定效力的 CNS。範例字型明示採 SIL OFL 1.1，但 repository 沒有可確認涵蓋所有文件、範例碼與圖片的 root license；本專案因此只轉述技術邊界，沒有複製或散布其字型、程式、PDF、圖片或文章。

合法開放閱讀材料另包含 [Introduction to Human-Computer Interaction](https://introductiontohci.org/)、[Flexible Typesetting](https://flexibletypesetting.com/)、[Designing for the Web](https://designingfortheweb.co.uk/)、[政府網站營運交流平台：以使用者為中心的設計](https://www.webguide.nat.gov.tw/guidelines/442/show) 與 [智慧財產局 UI/UX 設計指引](https://tiponet.tipo.gov.tw/TIPO_UIUX/)。它們只作閱讀、交叉檢查與有限轉述；各自的 CC、網站或政府資料條款不會被本專案的 MIT 授權取代，也沒有把禁止改作或未確認授權的內容併入 repository。

另檢閱 r/UXDesign 的 [AI 工作流程](https://www.reddit.com/r/UXDesign/comments/1tf2yea/actual_ai_design_workflows_in_2026/)、[企業設計系統整合](https://www.reddit.com/r/UXDesign/comments/1tsy4sh/has_anyone_successfully_integrated_ai_into_a/) 與 [case study 長度](https://www.reddit.com/r/UXDesign/comments/1uwdqj5/can_we_please_talk_about_case_study_length/) 討論。這些是自選樣本的社群訊號，不是代表性研究；本專案沒有複製貼文內容。

## Evaluator 開發依賴

根目錄 `package-lock.json` 固定瀏覽器 evaluator 的開發依賴；它們不會被 `gh skill install` 複製進 `wow-frontend-design/`：

| Package | Version | License | Purpose |
| --- | --- | --- | --- |
| `@google/design.md` | 0.3.0 | Apache-2.0 | 官方 `DESIGN.md` 格式檢查 |
| `playwright` | 1.61.1 | Apache-2.0 | 瀏覽器擷取與互動重播 |
| `playwright-core` | 1.61.1 | Apache-2.0 | Playwright 核心 runtime |
| `fsevents` | 2.3.2 | MIT | npm 的 macOS optional dependency |

實際安裝內容與授權以 `package-lock.json`、各 package 內附 LICENSE 及其官方發行內容為準。
