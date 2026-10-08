## 2026-10-08 · 圖像知識與 Git 交接

補附 0.10.9 日照 HTML 成果與 0.9.2 Rhino SunPath 兩張實際圖片到固定 Notion KB-003；各自標明原始日期、來源與驗證範圍，已讀回圖片區塊。專案卡片與 KB-001 同步知識入口，MCP AI 首頁維持多專案導航。Git 交接使用 `codex/company-0109-knowledge-20261008`；只替換遠端 `EnvironmentalSimulationHub/`，成功以遠端子樹核對與本機具名回執為準。

[本輪知識與家用接續](KNOWLEDGE_GIT_UPDATE_2026-10-08.md) · [圖片上傳／讀回回執](evidence/knowledge_20261008/notion_image_receipt.json)。沒有新增 Build、求解、部署或覆蓋變更：正式 0.9.2／9、1、112；已部署候選 0.10.9／10、1、111。主線仍為指定時刻陰影、風花圖／常用圖表、MRT 與提前 Eddy3D 引擎關卡。

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

## 2026-10-05 · 家用進度已同步到公司

已從 GitHub 家用分支取回 8 個專案提交，完整來源樹一致；公司候選來源為 **0.10.7**。公司 Build 0 錯誤／0 警告、25 項 Core、42 項方案契約與 3 項歷史證據完整性檢查通過。**尚未於公司 Rhino 載入或完成原生／完整 UI 驗收**；正式基準維持 0.9.2／9、1、112，家用原生結果保留原範圍。[同步範圍、備份與接續方式](COMPANY_SYNC_2026-10-05.md)。

## 歷史計畫 · 2026-10-03 視覺優先與日照流程瘦身

交付改為完整日照設計流程：共用設定→模型結果→天空遮蔽解讀→A／B比較→精簡匯出。先A日照視覺MVP23–40人日／5–8工作週，再B Solar Envelope13–23人日／3–5工作週；A＋B統一加25%為35–63人日。單人＋AI全時工程假設；122能力保留待辦，CFD／全量獨立頁面／大框架重寫後排。正式0.9.2／候選0.10.7，未新增求解驗證。

[2026-10-03 日照計畫](OPTIMIZED_VISUAL_PLAN_2026-10-03.md)保留為歷史範圍；目前活動排序與工期以本文最上方 2026-10-05 多功能 MVP 計畫為準。

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

## 2026-10-03 · 目前候選 0.10.3

**0.10.3 已修正日照時數 API 的單位重綁，161 項原生／平台回歸通過，完整 UI 待驗收。** 建置 0 錯誤／0 警告；新專用 Rhino 載入 0.10.3.0，既有 154 項＋新增 7 項重綁測試通過。Core 25、MCP 工具 8、輸出回讀 3 項另列。新版 44 張 320／480 px 淺色離屏圖與 2 張真正視埠已檢視，Ladybug 122 入口 SHA 相符。

變更單位後舊綁定仍阻擋求解；明確重選可恢復並保留前次結果，無效重選不改舊綁定。MCP 已恢復並完成本輪呼叫；完整 Dock／深色／鍵盤／原生對話框仍受桌面擷取逾時阻礙。正式 **0.9.2／9、1、112**，候選 10／1／111；先完成 V02 UI 再正式交付與 V03 Sky Mask。[0.10.3 範圍與下一步](HOME_VALIDATION_0103.md) · [彙總 receipt](evidence/home_0103/acceptance.json) · [本輪 Notion 同步狀態](evidence/notion_home_0103_sync_2026-10-03.json)。

使用者新增 UI-WIDTH-0103：面板初始外框太窄，需要手動拉寬，尚未修復。Rhino 8 容器寬度無公開設定 API，正確認停靠／浮動模式及實際尺寸；此項加入 V02 UI 出口門檻。

## 2026-10-03 · 歷史家用檢查點 0.10.2

**0.10.2 已完成本機原生驗證，完整 UI 待驗收。** .NET SDK 8.0.425、Rhino 8.35／.NET 8.0.31；Build 0 錯誤／0 警告，新專用 Rhino 載入 0.10.2.0。154 項原生／平台、25 項 Core、8 項 MCP 錯誤處理與 3 項輸出回讀通過，Ladybug 122 入口檔案 SHA 相符。44 張 320／480 px 淺色離屏版面已檢視，日照時數欄位／色樣缺陷未重現，另檢視 2 張真正視埠。

MCP 通訊與指定 Rhino 唯讀執行成功；實際桌面視窗擷取仍逾時。完整 Dock、原生深色／鍵盤／picker／file dialog 待驗收，尚未正式升版或開始 Sky Mask。正式 **0.9.2／9 獨立、1 後端、112 待接入**；候選 10／1／111。Eddy3D 載入不代表 CFD 求解可用；Notion 候選檢查點已同步並讀回，更新 8 筆、新增 1 筆驗證，總計 191 筆，正式功能數不變。[完整範圍](HOME_VALIDATION_0102.md) · [彙總 receipt](evidence/home_0102/acceptance.json) · [同步 receipt](evidence/notion_home_0102_sync_2026-10-03.json)。

## 歷史交接 · 2026-10-02

正式已交付基準仍為 **0.9.2（9 獨立／1 後端／112 待正式接入）**。日照時數 LB-061 已加入第八個內部模組；0.10.1 候選的 45 項新功能及 109 項其他原生／平台檢查合計 **154 項通過**，候選接入數為 10／1／111。44 張離屏 UI 與 2 張真正 3D 圖已擷取，但窄版色樣／數值欄位排版缺陷尚未正式驗收。

**目前程式碼為 0.10.2**：已分離圖例、參數與說明的欄寬，Build 0 錯誤／0 警告；**尚未註冊、載入或完成原生與 UI 複驗**。因使用者要求安全轉回家用電腦，停止新增功能，先整理並打包。0.10.1 的結果不能代替 0.10.2 或家用機驗收。

[安全移轉／交接](HOME_TRANSFER.md) · [回家後接續指令](HOME_CONTINUE_PROMPT.md) · [日照時數候選範圍](SUN_HOURS_MODULE.md) · [交接證據](evidence/handoff_20261002_status.json)

Notion 最後已同步仍為 190 筆／0.9.2；本輪候選及交接待同步。定時回報建立曾取消，尚無本專案已啟用 heartbeat。以下 0.9.2 表格保留正式基準與原驗收範圍。

# 專案目前狀態

更新日期：2026-10-02。正式版本 **0.9.2**；本輪加入 SunPath 幾何功能並在新 Rhino 程序驗收，來源與範圍見版本化證據。

## 完成範圍

| 指標 | 目前狀態 | 判讀方式 |
| --- | --- | --- |
| Ladybug 安裝目錄 | 122／122 已盤點 | 119 個元件、3 個 ValueList；盤點不代表求解或整合完成 |
| 獨立 Hub 功能 | 9 項已接入並實測 | 逐項見下表與功能目錄 |
| 僅作後端使用 | 1 項 | Cumulative Sky Matrix；未宣告獨立操作流程完成 |
| 待接入 | 112 項 | 不包含額外 Honeybee、Eddy3D 或能耗引擎 |
| 平台介面 | 1 個原生面板、7 個內部模組 | 首頁、氣象、地點、STAT／DDY、時間、日射、太陽路徑 |
| 第一版 UI | 基礎、中文化與單一平台整合已交付；完整驗收未閉合 | 繁體中文、主題色、向量圖示、六階段流程；保留 Rhino／Eto |
| 第二版 UI | 規劃中 | 主要功能完成並驗收後進行大型視覺互動介面 |

功能覆蓋與工程工作量不同；不提供沒有驗收依據的總完成百分比。

| 已接入功能 | 現有入口／用途 | 驗證來源 |
| --- | --- | --- |
| LB-063 · LB Incident Radiation | EnvironmentalRadiation；幾何、遮蔭、原生日射與結果 | release_092_loaded.json、platform_092_runtime.json |
| LB-009 · LB Import EPW | EnvironmentalWeather；原生氣象集合、時間篩選與缺值 | release_092_loaded.json、weather_runtime_validation.json |
| LB-001 · LB Construct Location | EnvironmentalLocation；座標、小數時區及海拔 | release_092_loaded.json |
| LB-011 · LB Import STAT | EnvironmentalClimate；氣候與設計條件 | release_092_loaded.json |
| LB-007 · LB Import DDY | EnvironmentalClimate；設計日與地點 | release_092_loaded.json |
| LB-013 · LB Analysis Period | EnvironmentalTime；原生分析期間 | release_092_loaded.json |
| LB-020 · LB Calculate HOY | EnvironmentalTime；日期轉 HOY | release_092_loaded.json |
| LB-033 · LB HOY to DateTime | EnvironmentalTime；HOY 轉日期 | release_092_loaded.json |
| LB-057 · LB SunPath | EnvironmentalSunPath；位置、向量、曲線、文字與四投影；[支援邊界](SUNPATH_MODULE.md) | sunpath_092_runtime.json、sunpath_092_transfer.json |

九項功能位於同一工作平台的內部模組，不代表九種完整模擬引擎。LB-049 Cumulative Sky Matrix 僅供日射後端使用，尚未提供獨立完成流程。[完整功能表](LADYBUG_FEATURE_TABLE.md)／[可搜尋目錄](LADYBUG_FEATURE_TABLE.html)／[原始狀態資料](evidence/ladybug_feature_catalog.json)。

## 0.9.2 太陽路徑與單一工作平台

- SunPath 沿用六階段、中文、主題色與向量圖示；一般地點／日期／北向／半徑，進階時區／中心／投影／真太陽時。地點、EPW 與時間資料只能由完成結果明確傳入。
- 原生曲線、羅盤文字、太陽點與日照方向線；結果顯示高度角、方位角、地平線以下時刻、模型單位與時間制。定位或清除只處理本模組預覽。
- 只註冊 HubWorkspacePanel，七個內部模組／七個指令均導向同一面板，切換保留草稿、完成結果及比較方案。
- 新增 Core 契約與 Adapter；既有 Core／Adapter 求解檔案未修改。不能稱為全部 DLL 未變或完整 SunPath 選項完成。

| 驗證 | 結果 | 證據 |
| --- | --- | --- |
| 建置／正式載入 | 0 錯誤、0 警告；新專用 Rhino 程序載入 0.9.2，註冊路徑更新 | [載入](evidence/release_092_loaded.json)、[發布 manifest](evidence/release_092_manifest.json) |
| SunPath 原生／操作 | 31＋1＋2 項；12 組原生角度、向量、曲線與文字比較，四投影／單位／失敗／資料轉移／owned preview | [模組驗證](evidence/sunpath_092_runtime.json)、[EPW 地點](evidence/sunpath_092_transfer.json)、[文字尺度](evidence/sunpath_092_text.json) |
| 七模組整合 | 14 項；七指令、路由、六首頁入口、狀態保留、關閉重開 | [平台驗證](evidence/workspace_092_runtime.json) |
| 既有數值／流程 | 60 項，合計 108 項原生數值／操作；日射平均 1233.3471168086037 kWh/m² | [載入／數值](evidence/release_092_loaded.json)、[日射平台](evidence/platform_092_runtime.json) |
| 版面 | 30 張 320／480 px，當前淺色原生控制項離屏呈現 | [擷取範圍](evidence/ui_092/capture.json)、[SunPath 結果](evidence/ui_092/sunpath_results_320.png) |

完整 Dock、深色切換、鍵盤、原生 picker／file dialog、不同文件切換與大型分鐘取樣預覽效能仍需完整驗收。單一平台的 Dock 識別及關閉重開已實測；影像是離屏正式控制項，不能視為完整宿主驗收。歷史大型模型與全部舊單位案例未重跑。[0.8.7 快照](history/PROJECT_STATUS_087.md) 保留以前的驗收界線。

## 已知限制與未完成門檻

- L1 仍未全部完成；SunPath 幾何第一批已完成，下一優先 Direct Sun Hours → Sky Mask → Solar Envelope；SunPath 選項按依賴補齊，必要 L1 資料／單位依賴按需補齊。
- GH 求解同步執行於 Rhino UI 執行緒；沒有可靠百分比進度或取消。非閏年逐時 EPW 為目前支援邊界。
- 完整 Dock、深色切換、鍵盤、原生選取／檔案對話框，以及複雜大型模型與外部求解器崩潰注入仍待驗收。
- 方案快照限當次工作階段，可匯出；未實作持久方案庫匯入。結果平均為算術格點平均，不是面積加權。
- Pass／Fail 是使用者自訂包含邊界的專案區間，不是法規合規判定。圖例取自原生網格色彩，不對不同方案強行共用色階。
- Eddy3D／OpenFOAM 僅有前期盤點，未完成 CFD 求解驗證。Honeybee 採光、能耗、碳排等引擎仍是後續整合範圍。
- 跨機安裝與公司部署未驗收；現有測試使用 Seattle 等參考資料，不代表正式案場成果。

下一步見 [階段計畫](ROADMAP.md) 與 [Ladybug 批次計畫](LADYBUG_DEVELOPMENT_PLAN.md)。

## 同仁使用與新優先序

可準備 0.9.2 小範圍內部試用，已配置環境可使用現有氣象／時間／日射流程；跨機安裝、首次求解與一般同仁無協助操作未驗收。已新增中文 [快速上手](QUICK_START.md)、[試用驗收](PILOT_ACCEPTANCE.md)、示範模型與靜態環境檢查工具，另有 InternalPilot ZIP。新版試用包與正式版二進位相同，試用包輸出改用使用者目錄。L2 視覺化優先序見 [L2_VISUAL_PLAN.md](L2_VISUAL_PLAN.md)；CFD 後續優先評估 Eddy3D。參考來源見 [REFERENCE_INDEX.md](REFERENCE_INDEX.md)。

已檢視 [真正 SunPath 視埠](evidence/ui_092/sunpath_viewport.png)；原生文字依單一物件覆寫尺度，不更動文件樣式。0.9.0 首次實際視埠曾發現文字過大，0.9.1 是未通過該驗收的測試候選，最終正式版本為 0.9.2。
