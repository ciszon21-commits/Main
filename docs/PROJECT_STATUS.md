# 專案目前狀態

更新日期：2026-10-02。正式版本 **0.8.6**；本輪繁體中文介面已建置並在新 Rhino 程序驗收，來源與範圍見版本化證據。

## 完成範圍

| 指標 | 目前狀態 | 判讀方式 |
| --- | --- | --- |
| Ladybug 安裝目錄 | 122／122 已盤點 | 119 個元件、3 個 ValueList；盤點不代表求解或整合完成 |
| 獨立 Hub 功能 | 8 項已接入並實測 | 逐項見下表與功能目錄 |
| 僅作後端使用 | 1 項 | Cumulative Sky Matrix；未宣告獨立操作流程完成 |
| 待接入 | 113 項 | 不包含額外 Honeybee、Eddy3D 或能耗引擎 |
| 平台介面 | 6 個原生面板 | 首頁、氣象、地點、STAT／DDY、時間、日射 |
| 第一版 UI | 基礎、主題階層與中文化已交付；完整驗收未閉合 | 繁體中文、主題色、向量圖示、六階段流程；保留 Rhino／Eto |
| 第二版 UI | 規劃中 | 主要功能完成並驗收後進行大型視覺互動介面 |

功能覆蓋與工程工作量不同；不提供沒有驗收依據的總完成百分比。

| 已接入功能 | 現有入口／用途 | 驗證來源 |
| --- | --- | --- |
| LB Incident Radiation | EnvironmentalRadiation；幾何、遮蔭、原生日射與結果 | release_086_loaded.json、platform_086_runtime.json |
| LB Import EPW | EnvironmentalWeather；原生氣象集合、時間篩選與缺值 | release_086_loaded.json、weather_runtime_validation.json |
| LB Construct Location | EnvironmentalLocation；座標、小數時區及海拔 | release_086_loaded.json |
| LB Import STAT | EnvironmentalClimate；氣候與設計條件 | release_086_loaded.json |
| LB Import DDY | EnvironmentalClimate；設計日與地點 | release_086_loaded.json |
| LB Analysis Period | EnvironmentalTime；原生分析期間 | release_086_loaded.json |
| LB Calculate HOY | EnvironmentalTime；日期轉 HOY | release_086_loaded.json |
| LB HOY to DateTime | EnvironmentalTime；HOY 轉日期 | release_086_loaded.json |

獨立功能共用面板，因此不是八個畫面或八種完整模擬引擎。[完整功能表](LADYBUG_FEATURE_TABLE.md)／[可搜尋目錄](LADYBUG_FEATURE_TABLE.html)／[原始狀態資料](evidence/ladybug_feature_catalog.json)。

## 0.8.6 驗證摘要

| 驗證 | 結果 | 證據 |
| --- | --- | --- |
| 建置 | 0 錯誤、0 警告 | [發布驗收](evidence/chinese_086_acceptance.json) |
| 正式註冊與新程序載入 | 路徑及版本一致；測試 slot 為 aardvark | [正式載入紀錄](evidence/release_086_loaded.json) |
| 原生操作／數值 | 平台 21、時間 17、地點 11、STAT／DDY 11，共 60 項 | [驗收摘要](evidence/chinese_086_acceptance.json)、[平台流程](evidence/platform_086_runtime.json) |
| 導覽 | 首頁 5 個按鈕、共用 6 條路由；保留氣象結果 | [中文介面核對](evidence/chinese_086_ui.json) |
| 日射回歸 | 1233.3471168086037 kWh/m²，與基準一致 | [正式載入紀錄](evidence/release_086_loaded.json) |
| 版面 | 22 張 320／480 px 原生控制項影像已檢視；當前淺色主題、離屏呈現 | [影像範圍](evidence/ui_086/capture.json)、[首頁預覽](evidence/ui_086/overview_480.png) |
| 中文操作／欄位 | 六面板操作、欄位與導覽中文；診斷編號及未知原始訊息保留 | [中文介面核對](evidence/chinese_086_ui.json)、[驗收範圍](evidence/chinese_086_acceptance.json) |
| 核心保留 | Core／Adapter 原始碼未變；全部方法內容與排除建置 MVID／資訊 Git 版本後的中繼資料一致 | [編譯內容比較](evidence/binary_086_logic.json) |

DLL 整檔雜湊不同，不能稱為位元組一致。深色 token 的對比計算不代表原生深色切換驗收。先前的 25 項 Core preflight、單位不變性、82 格混合幾何與遮蔭、4096 格平面測試是歷史證據，未在本次中文化重新執行。

## 已知限制與未完成門檻

- L1 仍未全部完成；下一批是 Location 解構、Apply Analysis Period 與資料契約／工具。
- GH 求解同步執行於 Rhino UI 執行緒；沒有可靠百分比進度或取消。非閏年逐時 EPW 為目前支援邊界。
- 完整 Dock、深色切換、鍵盤、原生選取／檔案對話框，以及複雜大型模型與外部求解器崩潰注入仍待驗收。
- 方案快照限當次工作階段，可匯出；未實作持久方案庫匯入。結果平均為算術格點平均，不是面積加權。
- Pass／Fail 是使用者自訂包含邊界的專案區間，不是法規合規判定。圖例取自原生網格色彩，不對不同方案強行共用色階。
- Eddy3D／OpenFOAM 僅有前期盤點，未完成 CFD 求解驗證。Honeybee 採光、能耗、碳排等引擎仍是後續整合範圍。
- 跨機安裝與公司部署未驗收；現有測試使用 Seattle 等參考資料，不代表正式案場成果。

下一步見 [階段計畫](ROADMAP.md) 與 [Ladybug 批次計畫](LADYBUG_DEVELOPMENT_PLAN.md)。
