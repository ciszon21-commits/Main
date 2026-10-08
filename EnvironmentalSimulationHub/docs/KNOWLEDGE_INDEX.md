## 2026-10-08 · 圖像知識與 Git 交接

補附 0.10.9 日照 HTML 成果與 0.9.2 Rhino SunPath 兩張實際圖片到固定 Notion KB-003；各自標明原始日期、來源與驗證範圍，已讀回圖片區塊。專案卡片與 KB-001 同步知識入口，MCP AI 首頁維持多專案導航。Git 交接使用 `codex/company-0109-knowledge-20261008`；只替換遠端 `EnvironmentalSimulationHub/`，成功以遠端子樹核對與本機具名回執為準。

[本輪知識與家用接續](KNOWLEDGE_GIT_UPDATE_2026-10-08.md) · [圖片上傳／讀回回執](evidence/knowledge_20261008/notion_image_receipt.json)。沒有新增 Build、求解、部署或覆蓋變更：正式 0.9.2／9、1、112；已部署候選 0.10.9／10、1、111。主線仍為指定時刻陰影、風花圖／常用圖表、MRT 與提前 Eddy3D 引擎關卡。

## 2026-10-05 · MCP AI 首頁清理與舊環境資料歸檔

依使用者要求，MCP AI 首頁保持多專案卡片導航。外部 Environmental Hub 舊版本、部署、計畫、技術評估及舊知識入口已完整收進 [專案卡片](https://app.notion.com/p/3f01956a9b0e81f0a52fc11e84c1d86c) 的「08｜首頁歷史紀錄」下：[歷史子頁](https://app.notion.com/p/3f01956a9b0e8139adf2f98050403812)。已先保存並讀回，再移除首頁長文；其他專案入口及既有資料庫保留。

[歷史地端副本](NOTION_HOME_ENVIRONMENTAL_HISTORY.md) · [12 項歸檔／首頁／卡片 readback](evidence/notion_home_cleanup_2026-10-05/receipt.json)。後續更新以專案卡片、固定紀錄及原有知識資料庫為入口，不再將本專案長篇報告加回 MCP AI 首頁。本輪只整理知識，沒有新求解或功能覆蓋變更。

## 2026-10-05 · Notion 專案卡片入口

依使用者指定，將 [Environmental Simulation Hub｜Rhino 環境模擬專案卡片](https://app.notion.com/p/3f01956a9b0e81f0a52fc11e84c1d86c) 整理為目前狀態、快速入口、同仁操作、主要功能、接續開發、待驗收／部署及詳細資料庫七層。綠色呈現已部署、藍色功能／計畫、橙色待驗收；詳細修正與回復可展開。原有子資料庫、固定紀錄 ID 與歷史證據保留，沒有新建或搬移資料庫。

[本機卡片內容](NOTION_PROJECT_CARD.md) · [八項結構／屬性 readback](evidence/notion_card_2026-10-05/receipt.json)。本輪只整理知識介面；未執行新 Build／求解／部署或增加功能覆蓋。

## 2026-10-05 · 公司已部署 0.10.9／重複 ID 修正

公司新專用 Rhino 已實際載入 **0.10.9.0**。修正 HKLM／HKCU 兩筆既有外掛路徑，消除舊 0.10.1 覆蓋與再次載入同 ID 的觸發原因；保留 GUID、舊版及第一份備份。15 項原生檢查通過，包含兩次新日照求解（256 點無遮蔭 13 h、遮蔭 8–13 h／平均 9.57421875 h）、A/B、新版 HTML、失敗保留、模組切換與實際停靠／浮動狀態。另有本輪 42 方案、15 MCP 工具檢查。

新版報告頁由「匯出圖像摘要 HTML…」使用，WebView 預設 gate 保留。原生窄版擷取未通過宿主型別假設，完整 Dock 版面／主題／DPI／鍵盤與檔案對話框仍待驗收；MCP 曾提前斷線，後續同程序版本及原生紀錄已讀回。有效測試物件清空，面板已關閉；未強制結束工作階段。

[部署、操作與回復](COMPANY_DEPLOYMENT_0109.md) · [最終證據](evidence/deploy_0109/deployment_verified.json) · [本輪真實日照摘要](evidence/deploy_0109/current-summary.html)。正式功能基準 **0.9.2／9、1、112**；已部署候選 **0.10.9／10、1、111**，不增加功能覆蓋。本輪沒有 GitHub 推送或跨機試用驗收。下一步維持指定時刻陰影、風花圖／常用圖表及提前 Eddy3D 引擎關卡。

## 2026-10-05 · 0.10.9 日照成果頁視覺優化

候選來源 **0.10.9** 採建築成果報告版面：大型平均日照、分布圖與條件分欄、主題色／線條圖示、可展開數據與來源、首尾取樣日期。320–1280px 淺深色共 10 組尺寸／展開檢查通過；18 項呈現契約與 Release Build 0 錯誤／0 警告。已人工檢視 10 張收合及 2 張展開圖；資料為歷史原生結果，本輪沒有新求解。

[成果頁與 Audit／驗證範圍](VISUAL_RESULT_PAGE_0109.md) · [淺色預覽](evidence/visual_0109/summary-light.html) · [證據](evidence/visual_0109/acceptance.json)。Core／Adapters／Grasshopper 與單一工作區保持原行為。WebView 預設試驗 gate 保留；完整 Rhino Dock／原生主題、鍵盤與失敗復原待驗收，未部署。正式 0.9.2／9、1、112，候選 10、1、111，不增加功能覆蓋。

## 2026-10-05 · 0.10.8 日照圖像摘要與 WebView 探查

候選來源 0.10.8 新增中文日照分布圖、原生色樣、KPI／來源／目標／比較摘要與離線 HTML 匯出。只讀 WebView 在同一內部視圖惰性載入，預設由試驗 gate 阻擋初始化；C# 權威狀態與求解核心保留。

最終 Build 0 錯誤／0 警告；呈現契約 16、原有方案契約 42、隔離 Rhino 呈現／狀態 9 項通過，修正版 WebView 中文 DOM 已讀回。真正 320／480 CSS viewport 淺／深色四張已檢視，無水平溢出。這是歷史原生結果的呈現驗證，沒有本輪新求解。

原生 SDK 擷取、完整 Dock／原生深色／DPI／鍵盤／檔案及非同步失敗復原待驗收；MV-U0 部分完成。公司自建 Rhino 自動載入舊 0.10.1，探查改用獨立組件名稱，未替換公司註冊或正式部署。正式仍 0.9.2／9、1、112；候選 10、1、111，UI 工作不增加功能覆蓋。

[詳細驗證與下一步](WEBVIEW_RESULT_PROBE_0108.md) · [證據](evidence/webview_0108/acceptance.json) · [離線摘要](evidence/webview_0108/summary-light.html)。本輪失敗與限制另存；其他專案未修改，GitHub 未推送。

## 2026-10-05 · 目前採用：多功能視覺化 MVP

依使用者最新指示，主線改為 **日照／日射 → 指定時刻陰影 → 風花圖與常用圖表 → 熱輻射 MRT**；Eddy3D 單風向風模擬提前做引擎／基準探查，PASS 後插入風場實作，不再等待完整 Ladybug。先交付多種可解讀、可比較、可匯出的最小流程；細部數值工具、全參數、Solar Envelope 與全量獨立頁後排，必要資料／單位與原生數值驗證仍保留。

[多功能 MVP 活動計畫](MULTI_VISUAL_MVP_PLAN_2026-10-05.md)取代前版日照單線排序及其近期工期。核心 MVP 含風引擎探查、不含風場實作：48–85 人日；含通過探查後的風場實作：63–113 人日，皆只加一次 25% 預備量，單人＋AI 全時工程假設，非交付日期。未通過風場關卡的釋出須明示風場未交付。

本輪只調整計畫與知識文件。正式 0.9.2／9、1、112、候選 0.10.7／10、1、111 不變；公司 Rhino 載入／完整 UI 待驗收，沒有新增求解或功能覆蓋。前版規劃與驗證保留原範圍。

參考「Rhino MCP UIUX」後，加入 [Eto 外框＋WebView 圖表／成果探查](WEBVIEW_UI_STRATEGY_2026-10-05.md)：先只讀圖表／圖例／比較頁，保留 C# 狀態、原生選取與既有求解。公司 SDK 有 WebView API／組件，宿主初始化／Dock 尚未驗證；MV-U0 條件式探查 2–4 原始人日，含一次 25% 為 3–5 人日，不含全介面遷移。

## 歷史計畫 · 2026-10-03 視覺優先與日照流程瘦身

交付改為完整日照設計流程：共用設定→模型結果→天空遮蔽解讀→A／B比較→精簡匯出。先A日照視覺MVP23–40人日／5–8工作週，再B Solar Envelope13–23人日／3–5工作週；A＋B統一加25%為35–63人日。單人＋AI全時工程假設；122能力保留待辦，CFD／全量獨立頁面／大框架重寫後排。正式0.9.2／候選0.10.7，未新增求解驗證。

[2026-10-03 日照計畫](OPTIMIZED_VISUAL_PLAN_2026-10-03.md)保留為歷史範圍；目前活動排序與工期以本文最上方 2026-10-05 多功能 MVP 計畫為準。

## 2026-10-03 · 技術、難點與工期完整評估

新增 [完整技術評估](TECHNICAL_ASSESSMENT_2026-10-03.md)：目前 C#／.NET 8、Rhino／Eto／GH／Ladybug／Radiance 架構、已解與未解難點、後續功能依賴、人力假設及逐入口工期。附 [可重算模型](evidence/technical_assessment_20261003/estimate_model.json)；112 待補入口＝候選 111＋天空矩陣後端轉獨立流程，日照收尾另計一次。

基準為一位工程人員、AI 輔助、全時投入：近期 L2 第一批 38–70 人日／8–14 工作週；完整 Ladybug V1 309–677 人日／約16–34規劃月。這是初步估算，不是驗收成果或交付日期；程式維持正式0.9.2／候選0.10.7。另納入 .NET 8於2026-11-10結束支援的相容性探查。地端主文件、Notion詳細評估、首頁重點與固定KB-003相互連結；本輪同步receipt另存，不改舊版本證據。

## 2026-10-03 · 0.10.7 日照方案匯入與恢復

0.10.7 新增日照方案比較 JSON 匯入與跨程序恢復：整批檢核後追加，保留完整原生結果、名稱及選擇；不綁定舊模型、不求解、不改目前輸入或結果。42 項方案契約、17 項原生匯入、32 項狀態／文件隔離、13 項新程序恢復及 161 項全平台原生回歸通過；Core 25、MCP 工具 12，建置零錯誤／零警告。4 張 320／480 淺色離屏圖已檢視。原生匯入檔案選取、比較存檔、完整 Dock／深色／全鍵盤／滑鼠後選及跨機仍待驗收。測試 Timer 錯誤造成自建程序退出，堆疊與修正保留；產品未使用該 API。正式 0.9.2／9、1、112，候選 10／1／111；V02 未正式交付，V03 未啟動。

[方案操作與契約](SUNHOURS_SCENARIO_ARCHIVE.md) · [本輪詳細驗證](HOME_VALIDATION_0107.md) · [本輪 receipt](evidence/archive_0107/acceptance.json) · [視覺化精華](DEVELOPMENT_HIGHLIGHTS.md)。原有歷史紀錄保留；本輪沿用 Notion 詳細紀錄／重點／固定 KB-003 三層，實際進度才同步。

## 2026-10-03 · 0.10.6 停靠資料保留與正式匯出

0.10.6 修正 Rhino 停靠重建外框後遺失模組資料：依文件保存八個快取內部模組，保留草稿、日照結果與情境；外框釋放前卸下模組，文件關閉／Rhino 結束才釋放。建置零錯誤／零警告；本輪 161 項既有原生回歸、33 項狀態與文件隔離、2 項正式 picker 預選、3 項正式結果匯出／比較取消檢查通過，另 Core 25、MCP 工具 12。256 點日照無遮蔭平均 13 h、遮蔭 9.57421875 h；正式結果存檔 JSON 完全一致。比較成功存檔、完整 Dock 版面／深色／全鍵盤／滑鼠後選及跨機仍待驗收。正式 0.9.2／9、1、112，候選 10／1／111；V02 未正式交付，V03 未啟動。

[本輪詳細範圍](HOME_VALIDATION_0106.md) · [本輪 receipt](evidence/session_final_0106/acceptance.json) · [視覺化精華](DEVELOPMENT_HIGHLIGHTS.md)。Notion 依使用者要求分成詳細資料、重點整理與視覺化精華；只在有實際進度時更新，沿用既有資料庫與固定 ID。前輪 0.10.5 的浮動寬度 7 項與 44 張離屏圖未重跑，以下保留歷史證據。

## 2026-10-03 · 0.10.5 原生操作補驗與 MCP 修正

外掛維持 0.10.5。本輪修正 MCP 探測器漏判「正常輸出後附加執行例外」，**12 項工具測試通過**；另在新隔離空白 Rhino 通過 **7 項額外原生操作**（停靠保護 3、基本鍵盤 3、Eto 存檔取消 1）。原驗證程序已有 608 物件，未在其中操作。完整 168 項求解／平台回歸與 44 張圖屬前輪歷史，本輪未重跑。

唯讀檢查 161 份有回應的 transport，列出 21 個含錯誤的呼叫（包含已知失敗重試），歷史 receipts 不改寫。完整停靠版面、深色、全鍵盤／成功 picker 與正式匯出對話框仍待驗收，桌面影像擷取逾時；V02 未正式交付，V03 未啟動。正式 **0.9.2／9、1、112**，候選 10／1／111。

[本輪範圍](HOME_UI_VALIDATION_0105.md) · [補驗證據](evidence/native_ui_0105/acceptance.json)；以下保留前輪版本化範圍。

## 2026-10-03 · 目前候選 0.10.5

0.10.5 已修正工作平台首次開啟的浮動寬度：外框至少 500、實測內容 490；只處理 Rhino 已註冊的本平台實例。手動縮窄、關閉重開及模組切換保留使用者尺寸，較寬視窗不縮小；一般 Eto 視窗不被調整。168 項原生／平台（既有 161＋寬度 7）、Core 25、MCP 工具 8、輸出回讀 3 項通過，建置 0 錯誤／0 警告。

新版 44 張 320／480 淺色離屏圖與 2 張真正視埠已檢視，requested／actual width 全數相符。0.10.4 曾把測試用一般視窗加寬，窄版擷取失效；該候選保留失敗證據、不交付。完整原生 Dock、深色、鍵盤及 picker／檔案對話框仍待驗收；使用者原本開啟的 Rhino 仍載入 0.10.3，候選載入路徑已更新，新程序可使用 0.10.5。

正式仍為 **0.9.2／9、1、112**，候選 10／1／111；先完成 V02 UI 門檻，再交付及開始 V03 Sky Mask。此次 UI 修正不增加功能覆蓋數。 [驗證範圍](HOME_VALIDATION_0105.md) · [彙總 receipt](evidence/home_0105/acceptance.json) · [雙端同步 receipt](evidence/notion_home_0105_sync_2026-10-03.json)。

以下保留前一候選與正式歷史範圍。

## 目前接續入口 · 0.10.3／2026-10-03

先讀 [HOME_VALIDATION_0103.md](HOME_VALIDATION_0103.md)：日照時數公開 API 單位重綁修正、161 項原生／平台、25 Core、8 MCP 工具、3 輸出回讀通過；44 張淺色離屏圖及 2 張視埠已檢視，完整原生 UI 待驗收。正式仍為 0.9.2／9、1、112。新證據置於 `evidence/home_0103`，0.10.2 及更早 receipts 保持原範圍。

有實際進度即同步地端與既有 Notion 固定 ID；本輪新驗證編號 `VER-HOME-0103-01`，同步與讀回結果以 [本輪日期化 receipt](evidence/notion_home_0103_sync_2026-10-03.json) 為準。無變化不改日期或重複回報。

## 歷史接續入口 · 0.10.2／2026-10-03

使用者更新規則：每次有實際開發進度，同步維護地端知識文件與既有 Notion 紀錄，再用繁體中文回報。候選進度、測試證據及待驗收門檻也須同步，保持正式／候選的區分；Notion 同步失敗時明確記錄待補，不宣稱雙端完成。沒有變化時不重複回報或改日期。

本輪已更新 Notion 8 筆既有紀錄、新增 `VER-HOME-0102-01`，191 筆唯一編號與正式 9／1／112 已讀回。[日期化同步 receipt](evidence/notion_home_0102_sync_2026-10-03.json) 保留頁面對照、來源 SHA 與驗證範圍；後續重用此對照，不建立重複紀錄。

[HOME_VALIDATION_0102.md](HOME_VALIDATION_0102.md) 記錄家用機 0.10.2：154 原生／平台、25 Core、8 MCP 工具回歸、3 輸出回讀通過；44 張淺色離屏 UI 與 2 張視埠已檢視。完整原生 UI 待驗收，正式版本仍為 0.9.2。以下保留移轉前索引及正式基準；本輪狀態以新驗收文件與 PROJECT_STATUS 為準。

## 歷史交接入口 · 2026-10-02

[HOME_TRANSFER.md](HOME_TRANSFER.md) 是家用安全接收與版本狀態入口；[HOME_CONTINUE_PROMPT.md](HOME_CONTINUE_PROMPT.md) 可交給家用 Codex。[SUN_HOURS_MODULE.md](SUN_HOURS_MODULE.md) 記錄候選日照時數範圍。0.10.2 僅建置，原生 154 項屬 0.10.1；以下歷史索引不能視為新版本已驗收。

# 專案知識索引

更新日期：2026-10-02。這是專案內知識管理入口；目前已驗證版本為 0.9.2。歷史文件、測試樣本與新版狀態分開管理。

使用者指定的 [Notion 開發與知識資料庫](https://app.notion.com/p/27b5fd42055b410ea1d58fbbf60fd31e) 已建立：190 筆紀錄、11 分類、9 檢視。目的地、固定編號、同步邊界與維護流程見 [NOTION_KNOWLEDGE.md](NOTION_KNOWLEDGE.md)。本次為人工授權同步，未建立背景自動同步。

## 從哪裡開始

| 要回答的問題 | 主要文件 | 維護責任 |
| --- | --- | --- |
| 現在完成什麼、還缺什麼？ | [PROJECT_STATUS.md](PROJECT_STATUS.md) | 每次驗收後更新；引用版本化證據 |
| 下一階段與先後依賴？ | [ROADMAP.md](ROADMAP.md)、[LADYBUG_DEVELOPMENT_PLAN.md](LADYBUG_DEVELOPMENT_PLAN.md) | 功能批次或優先序改變時更新 |
| 為什麼保留框架、先做 Ladybug？ | [DECISIONS.md](DECISIONS.md) | 記錄使用者決策及實作規則；保留變更理由 |
| 全部原生功能與接入狀態？ | [Markdown 功能表](LADYBUG_FEATURE_TABLE.md)、[HTML 目錄](LADYBUG_FEATURE_TABLE.html)、[JSON 狀態資料](evidence/ladybug_feature_catalog.json) | 三者逐項對齊；目錄盤點與求解驗收分開 |
| UI 與操作流程如何統一？ | [UI_UX_STANDARD.md](UI_UX_STANDARD.md)、[PLATFORM_UI.md](PLATFORM_UI.md)、[UI audit](UI_AUDIT_2026-10-01.md) | 新面板、參數、圖例及互動均沿用 |
| 架構、型別及 GH 如何銜接？ | [ARCHITECTURE.md](ARCHITECTURE.md)、[GH_MODULE_STANDARD.md](GH_MODULE_STANDARD.md) | 保留 request → preflight → adapter → result 邊界 |
| 如何建置、更新與確認真實版本？ | [BUILD_AND_RUN.md](BUILD_AND_RUN.md) | 使用版本化目錄、新 Rhino 程序與載入 receipt |
| 某次交付做了什麼？ | [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) | 只新增歷史紀錄，不把舊結果改寫成新版驗收 |
| 全部開發檢視？ | [DEVELOPMENT_REVIEW_2026-10-01.md](DEVELOPMENT_REVIEW_2026-10-01.md) | 最新評估與歷史檢視分開 |

## 新優先序與同仁交付

- [L2_VISUAL_PLAN.md](L2_VISUAL_PLAN.md)：SunPath 幾何第一批已完成 → Direct Sun Hours → Sky Mask → Solar Envelope；L1 依賴按需補齊。
- [QUICK_START.md](QUICK_START.md)／[PILOT_ACCEPTANCE.md](PILOT_ACCEPTANCE.md)：同仁內部試用、環境與首次分析步驟；跨機與無協助上手仍待驗收。
- [REFERENCE_INDEX.md](REFERENCE_INDEX.md)：使用者提供的 GitHub／Ladybug 官網／論壇／Eddy3D 官網及版本使用規則。

## 模組知識

| 模組 | 文件 | 重要邊界 |
| --- | --- | --- |
| EPW | [WEATHER_MODULE.md](WEATHER_MODULE.md) | 8760 非閏年逐時；月地溫不跟逐時篩選；風向不作算術均值 |
| Location | [LOCATION_MODULE.md](LOCATION_MODULE.md) | 半／四分之一小時 UTC 時區保留；輸入錯誤保留前次結果 |
| STAT／DDY | [CLIMATE_FILE_MODULE.md](CLIMATE_FILE_MODULE.md) | 原生 JSON／IDF；不可用假數值補缺失輸出 |
| 時間及平台 | [TIME_AND_HUB_MODULE.md](TIME_AND_HUB_MODULE.md) | 原生跨年、跨夜與次小時規則；日射的逐時邊界另行驗證 |
| 日射、結果及比較 | [PLATFORM_UI.md](PLATFORM_UI.md) | 原生網格色、明確單位、比較條件、owned preview、session snapshots |
| 太陽路徑 | [SUNPATH_MODULE.md](SUNPATH_MODULE.md) | 原生幾何第一批；位置／向量／投影，完整選項待補；日照時數是下一批 |
| 安裝／元件盤點 | [ENVIRONMENT_AUDIT.md](ENVIRONMENT_AUDIT.md)、[COMPONENT_INVENTORY.md](COMPONENT_INVENTORY.md) | 機器快照；安裝、建立、求解、部署是不同狀態 |

模組文件可能描述功能首次交付時的版本。當前產品狀態以 PROJECT_STATUS 與版本化驗收為準；不要把舊文件的版本號當作最新載入版本。

## 證據層級與可追溯性

1. **原生盤點**：`evidence/ladybug_feature_catalog.json` 提供 122 入口身分、參數與狀態；3 個 ValueList 不是求解器。UserObject GUID／SHA 與共用 GhPython ComponentGuid 不可混用。
2. **建置／包裝**：`release_092_manifest.json` 記錄發布檔案 SHA；建置成功不能證明 Rhino 已載入。
3. **正式載入**：`release_092_loaded.json` 確認目標 slot、Assembly 路徑與版本、PathFromId 及原生操作。
4. **功能／流程**：`platform_092_runtime.json` 與載入 receipt；保留數值、失敗路徑、預覽歸屬及 GH 清理檢查。
5. **視覺／對比**：`ui_092/capture.json`、PNG；配色沿用 0.8.5 的 `topic_085_palette.json`；當前淺色離屏控制項；Dock 識別與關閉重開另有 14 項原生檢查。
6. **彙整驗收**：`sunpath_092_acceptance.json` 引用以上範圍及來源雜湊；既有求解檔案未改，新增 SunPath 契約與 adapter；不能稱整個 DLL 相同。

Transport 的 `MCP_RESPONDED` 只代表通訊有回應；仍須檢查內層 payload／error 及實際驗收檔。`samples/` 是測試輸出，不能單憑「有檔案」宣告測試通過。多數 replay paths 是本機路徑，移機前需重新配置。

## 開發與交付時如何更新

開始工作先讀 AGENTS、目前狀態、相關批次與模組文件。每項新功能記錄原生名稱／ID、型別契約、預設值、單位、原生參考、錯誤處理與 UI 驗收，再更新 JSON／Markdown／HTML 目錄及 PROJECT_STATUS。純介面或文件交付不增加功能完成數。

每次發布使用新版本／目錄，不覆寫 Rhino 已載入的組件。保留前版、manifest、註冊備份和獨立載入紀錄。測試必須鎖定自己的 Rhino slot／文件；使用 `__rhino_doc__` 取得 MCP 的目標文件，不操作使用者未授權的文件。清理只移除模組 owned preview；原生 GH definition 要隔離並釋放。

知識更新保留三種狀態：已實作、指定範圍已驗證、尚未驗收。不以截圖代替物理數值、不以配色 token 計算代替深色操作、不以 4096 格單平面代替複雜專案容量，也不把歷史測試寫成本次重跑。

歷史檢視存於 [history/](history/DEVELOPMENT_REVIEW_040.md)；版本化 evidence 保留原始結果。Notion 與本機引用同一套狀態與證據，後續使用固定編號更新同一筆紀錄，避免另建矛盾的進度來源。

SunPath 操作、第一批支援邊界及驗證來源：[SUNPATH_MODULE.md](SUNPATH_MODULE.md)。新版接受證據：[sunpath_092_acceptance.json](evidence/sunpath_092_acceptance.json)。歷史版本文件與 receipts 不更動。
