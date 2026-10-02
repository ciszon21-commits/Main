# 專案目前狀態

更新日期：2026-10-02。正式版本 **0.8.7**；本輪單一工作平台已建置並在新 Rhino 程序驗收，來源與範圍見版本化證據。

## 完成範圍

| 指標 | 目前狀態 | 判讀方式 |
| --- | --- | --- |
| Ladybug 安裝目錄 | 122／122 已盤點 | 119 個元件、3 個 ValueList；盤點不代表求解或整合完成 |
| 獨立 Hub 功能 | 8 項已接入並實測 | 逐項見下表與功能目錄 |
| 僅作後端使用 | 1 項 | Cumulative Sky Matrix；未宣告獨立操作流程完成 |
| 待接入 | 113 項 | 不包含額外 Honeybee、Eddy3D 或能耗引擎 |
| 平台介面 | 1 個原生面板、6 個內部模組 | 首頁、氣象、地點、STAT／DDY、時間、日射 |
| 第一版 UI | 基礎、中文化與單一平台整合已交付；完整驗收未閉合 | 繁體中文、主題色、向量圖示、六階段流程；保留 Rhino／Eto |
| 第二版 UI | 規劃中 | 主要功能完成並驗收後進行大型視覺互動介面 |

功能覆蓋與工程工作量不同；不提供沒有驗收依據的總完成百分比。

| 已接入功能 | 現有入口／用途 | 驗證來源 |
| --- | --- | --- |
| LB-063 · LB Incident Radiation | EnvironmentalRadiation；幾何、遮蔭、原生日射與結果 | release_087_loaded.json、platform_087_runtime.json |
| LB-009 · LB Import EPW | EnvironmentalWeather；原生氣象集合、時間篩選與缺值 | release_087_loaded.json、weather_runtime_validation.json |
| LB-001 · LB Construct Location | EnvironmentalLocation；座標、小數時區及海拔 | release_087_loaded.json |
| LB-011 · LB Import STAT | EnvironmentalClimate；氣候與設計條件 | release_087_loaded.json |
| LB-007 · LB Import DDY | EnvironmentalClimate；設計日與地點 | release_087_loaded.json |
| LB-013 · LB Analysis Period | EnvironmentalTime；原生分析期間 | release_087_loaded.json |
| LB-020 · LB Calculate HOY | EnvironmentalTime；日期轉 HOY | release_087_loaded.json |
| LB-033 · LB HOY to DateTime | EnvironmentalTime；HOY 轉日期 | release_087_loaded.json |

八項功能位於同一工作平台的內部模組，不代表八種完整模擬引擎。LB-049 Cumulative Sky Matrix 僅供日射後端使用，尚未提供獨立完成流程。[完整功能表](LADYBUG_FEATURE_TABLE.md)／[可搜尋目錄](LADYBUG_FEATURE_TABLE.html)／[原始狀態資料](evidence/ladybug_feature_catalog.json)。

## 0.8.7 單一工作平台

- 僅註冊 HubWorkspacePanel；沿用原首頁 Dock GUID，保留 Rhino 的面板位置識別。
- 固定頂部模組選單與首頁入口。內部切換首頁、氣象、地點、氣候／設計日、時間與日射；不新增獨立 Dock 面板。
- 六個原指令保留，全部導向同一平台。模組按需建立並保留實例；切換保留未完成輸入、已完成結果、日射預覽與工作階段方案。
- 氣象與期間資料從同一平台已完成的模組轉移；不因切換重新計算或自動套用未完成輸入。
- 日射仍沿用模型 → 氣象 → 設定 → 檢核／執行 → 結果 → 比較／匯出。主題色／圖示、原生圖例、明確單位與進階設定保持一致。

| 驗證 | 結果 | 證據 |
| --- | --- | --- |
| 建置／正式載入 | 0 錯誤、0 警告；新專用 Rhino 程序載入 0.8.7 | [發布驗收](evidence/workspace_087_acceptance.json)、[實際載入](evidence/release_087_loaded.json) |
| 單一平台操作 | 13 項：六指令、六路由、五首頁入口、未完成輸入與結果保留、關閉重開、未知模組拒絕 | [平台驗證](evidence/workspace_087_runtime.json) |
| 原生數值／既有流程 | 平台 21、時間 17、地點 11、STAT／DDY 11，共 60 項；合計 73 項 | [載入／數值](evidence/release_087_loaded.json)、[日射與資料轉移](evidence/platform_087_runtime.json) |
| 日射回歸 | 1233.3471168086037 kWh/m²，與基準一致 | [數值紀錄](evidence/release_087_loaded.json) |
| 版面 | 22 張單一平台＋內部模組影像，320／480 px，當前淺色主題；已檢視 | [擷取範圍](evidence/ui_087/capture.json)、[首頁](evidence/ui_087/overview_480.png) |
| 核心保留 | Core／Adapter 原始碼未變；全部方法與中繼資料排除建置識別後一致 | [編譯內容比較](evidence/binary_087_logic.json) |

Dock 識別、可見性與關閉重開已實測。22 張影像是離屏原生控制項呈現，不代表完整 Dock 調整、深色切換、鍵盤與原生對話框驗收。DLL 整檔雜湊不同，不能稱為位元組一致。歷史大型模型與單位測試未在本輪全部重跑。[0.8.6 快照](history/PROJECT_STATUS_086.md) 保留原驗收範圍。

## 已知限制與未完成門檻

- L1 仍未全部完成；現在優先 L2 SunPath → Direct Sun Hours → Sky Mask → Solar Envelope，必要 L1 資料／單位依賴按需補齊。
- GH 求解同步執行於 Rhino UI 執行緒；沒有可靠百分比進度或取消。非閏年逐時 EPW 為目前支援邊界。
- 完整 Dock、深色切換、鍵盤、原生選取／檔案對話框，以及複雜大型模型與外部求解器崩潰注入仍待驗收。
- 方案快照限當次工作階段，可匯出；未實作持久方案庫匯入。結果平均為算術格點平均，不是面積加權。
- Pass／Fail 是使用者自訂包含邊界的專案區間，不是法規合規判定。圖例取自原生網格色彩，不對不同方案強行共用色階。
- Eddy3D／OpenFOAM 僅有前期盤點，未完成 CFD 求解驗證。Honeybee 採光、能耗、碳排等引擎仍是後續整合範圍。
- 跨機安裝與公司部署未驗收；現有測試使用 Seattle 等參考資料，不代表正式案場成果。

下一步見 [階段計畫](ROADMAP.md) 與 [Ladybug 批次計畫](LADYBUG_DEVELOPMENT_PLAN.md)。

## 同仁使用與新優先序

可準備 0.8.7 小範圍內部試用，已配置環境可使用現有氣象／時間／日射流程；跨機安裝、首次求解與一般同仁無協助操作未驗收。已新增中文 [快速上手](QUICK_START.md)、[試用驗收](PILOT_ACCEPTANCE.md)、示範模型與靜態環境檢查工具，另有 InternalPilot ZIP。正式二進位未變，試用包輸出改用使用者目錄。L2 視覺化優先序見 [L2_VISUAL_PLAN.md](L2_VISUAL_PLAN.md)；CFD 後續優先評估 Eddy3D。參考來源見 [REFERENCE_INDEX.md](REFERENCE_INDEX.md)。
