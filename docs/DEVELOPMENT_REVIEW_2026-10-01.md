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
