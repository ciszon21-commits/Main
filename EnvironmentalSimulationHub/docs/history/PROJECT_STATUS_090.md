# 專案目前狀態

更新日期：2026-10-02。正式版本 **0.9.0**；本輪加入 SunPath 幾何功能並在新 Rhino 程序驗收，來源與範圍見版本化證據。

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
| LB-063 · LB Incident Radiation | EnvironmentalRadiation；幾何、遮蔭、原生日射與結果 | release_090_loaded.json、platform_090_runtime.json |
| LB-009 · LB Import EPW | EnvironmentalWeather；原生氣象集合、時間篩選與缺值 | release_090_loaded.json、weather_runtime_validation.json |
| LB-001 · LB Construct Location | EnvironmentalLocation；座標、小數時區及海拔 | release_090_loaded.json |
| LB-011 · LB Import STAT | EnvironmentalClimate；氣候與設計條件 | release_090_loaded.json |
| LB-007 · LB Import DDY | EnvironmentalClimate；設計日與地點 | release_090_loaded.json |
| LB-013 · LB Analysis Period | EnvironmentalTime；原生分析期間 | release_090_loaded.json |
| LB-020 · LB Calculate HOY | EnvironmentalTime；日期轉 HOY | release_090_loaded.json |
| LB-033 · LB HOY to DateTime | EnvironmentalTime；HOY 轉日期 | release_090_loaded.json |
| LB-057 · LB SunPath | EnvironmentalSunPath；位置、向量、曲線、文字與四投影；[支援邊界](SUNPATH_MODULE.md) | sunpath_090_runtime.json、sunpath_090_transfer.json |

九項功能位於同一工作平台的內部模組，不代表九種完整模擬引擎。LB-049 Cumulative Sky Matrix 僅供日射後端使用，尚未提供獨立完成流程。[完整功能表](LADYBUG_FEATURE_TABLE.md)／[可搜尋目錄](LADYBUG_FEATURE_TABLE.html)／[原始狀態資料](evidence/ladybug_feature_catalog.json)。

## 0.9.0 太陽路徑與單一工作平台

- SunPath 沿用六階段、中文、主題色與向量圖示；一般地點／日期／北向／半徑，進階時區／中心／投影／真太陽時。地點、EPW 與時間資料只能由完成結果明確傳入。
- 原生曲線、羅盤文字、太陽點與日照方向線；結果顯示高度角、方位角、地平線以下時刻、模型單位與時間制。定位或清除只處理本模組預覽。
- 只註冊 HubWorkspacePanel，七個內部模組／七個指令均導向同一面板，切換保留草稿、完成結果及比較方案。
- 新增 Core 契約與 Adapter；既有 Core／Adapter 求解檔案未修改。不能稱為全部 DLL 未變或完整 SunPath 選項完成。

| 驗證 | 結果 | 證據 |
| --- | --- | --- |
| 建置／正式載入 | 0 錯誤、0 警告；新專用 Rhino 程序載入 0.9.0，註冊路徑更新 | [載入](evidence/release_090_loaded.json)、[發布 manifest](evidence/release_090_manifest.json) |
| SunPath 原生／操作 | 31＋1 項；12 組原生角度、向量、曲線與文字比較，四投影／單位／失敗／資料轉移／owned preview | [模組驗證](evidence/sunpath_090_runtime.json)、[EPW 地點](evidence/sunpath_090_transfer.json) |
| 七模組整合 | 14 項；七指令、路由、六首頁入口、狀態保留、關閉重開 | [平台驗證](evidence/workspace_090_runtime.json) |
| 既有數值／流程 | 60 項，合計 106 項原生數值／操作；日射平均 1233.3471168086037 kWh/m² | [載入／數值](evidence/release_090_loaded.json)、[日射平台](evidence/platform_090_runtime.json) |
| 版面 | 30 張 320／480 px，當前淺色原生控制項離屏呈現 | [擷取範圍](evidence/ui_090/capture.json)、[SunPath 結果](evidence/ui_090/sunpath_results_320.png) |

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

可準備 0.9.0 小範圍內部試用，已配置環境可使用現有氣象／時間／日射流程；跨機安裝、首次求解與一般同仁無協助操作未驗收。已新增中文 [快速上手](QUICK_START.md)、[試用驗收](PILOT_ACCEPTANCE.md)、示範模型與靜態環境檢查工具，另有 InternalPilot ZIP。新版試用包與正式版二進位相同，試用包輸出改用使用者目錄。L2 視覺化優先序見 [L2_VISUAL_PLAN.md](L2_VISUAL_PLAN.md)；CFD 後續優先評估 Eddy3D。參考來源見 [REFERENCE_INDEX.md](REFERENCE_INDEX.md)。

歷史補記：實際視埠發現原生文字繼承文件註解尺度而過大，最終修正及驗收見 0.9.2。0.9.1 為未通過文字尺度驗收的測試候選。
