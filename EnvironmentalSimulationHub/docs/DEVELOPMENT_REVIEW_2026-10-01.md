## 2026-10-03 · 0.10.7 日照方案匯入與恢復

0.10.7 新增日照方案比較 JSON 匯入與跨程序恢復：整批檢核後追加，保留完整原生結果、名稱及選擇；不綁定舊模型、不求解、不改目前輸入或結果。42 項方案契約、17 項原生匯入、32 項狀態／文件隔離、13 項新程序恢復及 161 項全平台原生回歸通過；Core 25、MCP 工具 12，建置零錯誤／零警告。4 張 320／480 淺色離屏圖已檢視。原生匯入檔案選取、比較存檔、完整 Dock／深色／全鍵盤／滑鼠後選及跨機仍待驗收。測試 Timer 錯誤造成自建程序退出，堆疊與修正保留；產品未使用該 API。正式 0.9.2／9、1、112，候選 10／1／111；V02 未正式交付，V03 未啟動。

[方案操作與契約](SUNHOURS_SCENARIO_ARCHIVE.md) · [本輪詳細驗證](HOME_VALIDATION_0107.md) · [本輪 receipt](evidence/archive_0107/acceptance.json) · [視覺化精華](DEVELOPMENT_HIGHLIGHTS.md)。原有歷史紀錄保留；本輪沿用 Notion 詳細紀錄／重點／固定 KB-003 三層，實際進度才同步。

## 2026-10-03 · 0.10.6 停靠資料保留與正式匯出

0.10.6 修正 Rhino 停靠重建外框後遺失模組資料：依文件保存八個快取內部模組，保留草稿、日照結果與情境；外框釋放前卸下模組，文件關閉／Rhino 結束才釋放。建置零錯誤／零警告；本輪 161 項既有原生回歸、33 項狀態與文件隔離、2 項正式 picker 預選、3 項正式結果匯出／比較取消檢查通過，另 Core 25、MCP 工具 12。256 點日照無遮蔭平均 13 h、遮蔭 9.57421875 h；正式結果存檔 JSON 完全一致。比較成功存檔、完整 Dock 版面／深色／全鍵盤／滑鼠後選及跨機仍待驗收。正式 0.9.2／9、1、112，候選 10／1／111；V02 未正式交付，V03 未啟動。

[本輪詳細範圍](HOME_VALIDATION_0106.md) · [本輪 receipt](evidence/session_final_0106/acceptance.json) · [視覺化精華](DEVELOPMENT_HIGHLIGHTS.md)。Notion 依使用者要求分成詳細資料、重點整理與視覺化精華；只在有實際進度時更新，沿用既有資料庫與固定 ID。前輪 0.10.5 的浮動寬度 7 項與 44 張離屏圖未重跑，以下保留歷史證據。

# 全部開發檢視｜0.8.7

更新日期：2026-10-02。已完成單一 Rhino 工作平台整合；功能數維持 8 獨立、1 後端、113 待接入。

## 已完成與目標

- 介面：一個 Dock、六個內部模組、中文導覽、主題圖示、六階段日射流程、KPI／圖例／比較／匯出。切換與關閉重開保留草稿及結果。
- Ladybug：LB-001 地點、LB-007 DDY、LB-009 EPW、LB-011 STAT、LB-013 分析期間、LB-020 Calculate HOY、LB-033 HOY to DateTime、LB-063 Incident Radiation 已實测；LB-049 天空矩陣僅用作後端。
- 驗證：建置零錯誤／警告；60 既有原生檢查及 13 平台整合檢查通過；22 張當前淺色 320／480 原生影像已檢視。Core／Adapter 保留。
- 近期目標：優先 L2 SunPath → Direct Sun Hours → Sky Mask → Solar Envelope，提供可視幾何及解讀必要資訊；L1 按依賴補齊，不要求全部完成才啟動 L2。
- 中期目標：L2 太陽／幾何 → L3 熱舒適 → L4 圖表 → L5 工具／維護。每項完成須有原生數值、操作、錯誤及狀態保留證據。
- 後續目標：Ladybug 主要功能與第一版驗收後，再整合 Honeybee／Eddy3D／OpenStudio／EnergyPlus，展開第二版大型互動 UI。

完整對應與限制見 [目前狀態](PROJECT_STATUS.md)、[全部 122 項功能](LADYBUG_FEATURE_TABLE.md)、[階段計畫](ROADMAP.md)、[批次計畫](LADYBUG_DEVELOPMENT_PLAN.md)。0.8.7 證據見 [發布驗收](evidence/workspace_087_acceptance.json)。前一版完整檢視保留於 [0.8.6 歷史快照](history/DEVELOPMENT_REVIEW_086.md)。

## 未完成門檻

同步求解尚無取消或可靠百分比；跨次 Rhino 工作階段方案庫尚未完成；完整 Dock 調整、深色、鍵盤、原生 picker／dialog、複雜大型模型與跨機部署仍須獨立驗收。採光、熱舒適、CFD、能耗與碳排尚未提供已驗證 Hub 流程。不能將安裝、目錄盤點或介面頁面視為功能完成。

同仁可準備小範圍內部試用，跨機與無協助操作仍待驗收；見 QUICK_START.md／PILOT_ACCEPTANCE.md。CFD 後續優先評估 Eddy3D，未宣告真實 CFD 求解完成。

## 2026-10-02 更新 · 0.9.0

目前為 9 獨立功能、1 後端、112 待接入；SunPath 幾何第一批透過新增契約與原生 Adapter 接入第七個內部模組。原有求解檔案保留。32＋60＋14 共 106 項原生檢查；30 張目前淺色 320／480 px 離屏影像。SunPath 未含氣象著色／條件／夏令時間／圖例等完整選項，見 [SUNPATH_MODULE.md](SUNPATH_MODULE.md)。下一項 Direct Sun Hours；跨機、完整 Dock／theme／keyboard／dialogs 驗收未閉合。本文前段版本記錄保留原驗收範圍，最新狀態以 PROJECT_STATUS.md 為準。

0.9.2 最新修正：SunPath 文字以明確的 DimensionStyle 欄位覆寫固定物件尺度，文件樣式不變。108 原生檢查、30 張淺色 UI 影像及 1 張真正視埠已檢視；9／1／112 不變。0.9.0／0.9.1 過程證據保留，最新正式狀態以 PROJECT_STATUS.md 為準。
