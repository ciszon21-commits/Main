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
