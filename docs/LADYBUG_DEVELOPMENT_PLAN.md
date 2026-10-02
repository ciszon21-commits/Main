# Ladybug 完整功能開發計畫

更新日期：2026-10-02。正式版本 **0.8.7**。使用者優先順序是先完成原生 Ladybug，第一版保留目前 Rhino／Eto 框架；第二版大型視覺互動於主要功能完成並驗收後進行。總階段見 [ROADMAP](ROADMAP.md)。

## 目前完成數與單一功能狀態

實際安裝入口 122 個，含 119 原生元件和 3 ValueList；目錄全部已盤點。**8 項獨立接入、1 項僅後端使用、113 項待接入**，來源為 [catalog JSON](evidence/ladybug_feature_catalog.json)，逐項見 [功能表](LADYBUG_FEATURE_TABLE.md)／[HTML](LADYBUG_FEATURE_TABLE.html)。

獨立功能為 Incident Radiation、Import EPW、Construct Location、Import STAT、Import DDY、Analysis Period、Calculate HOY、HOY to DateTime。Cumulative Sky Matrix 用於已驗證日射後端；尚未完成獨立 Hub 流程。0.8.7 改善 UI，沒有增加功能完成數。L1 仍未完成。

## 功能里程碑

| 里程碑 | 狀態 | 範圍 | 出口條件 |
| --- | --- | --- | --- |
| L0 完整目錄 | 已完成盤點 | 122 入口、分類、參數、輸出、GUID、SHA 與狀態 | 本機全量目錄對齊；不宣告全功能已求解 |
| L1 氣象／時間／資料 | 進行中 | 已完成 7 項；解構、期間套用、資料型別／篩選／單位、剩餘氣象／設計日工具待接入 | 真實文件與原生輸出一致；時間索引、缺值、型別、單位及副作用保留 |
| L2 太陽／幾何 | 部分完成 | Incident Radiation 已獨立驗證；其餘 SunPath、Direct Sun Hours、Sky Mask、Solar Envelope、視域等 | 原生數值與幾何、模型單位、遮蔭、預覽及圖例一致 |
| L3 熱舒適 | 待開發 | PMV、Adaptive、UTCI、PET、MRT、Thermal Indices／參數 | 原生模型與適用條件；單位、數值、統計及錯誤路徑 |
| L4 圖表／呈現 | 待開發 | Psychrometric、Wind Rose／Profile、Hourly／Monthly、Sky／Radiation 等 | 原生資料與圖形一致，圖例、標籤、範圍與縮放可讀 |
| L5 工具／維護 | 待開發 | 資料建構／儲存、矩陣、網格、圖例、視圖、版本、預設選單 | 可重現操作、檔案／視圖／環境改變明示；三個 ValueList 驗項目與連接 |

里程碑按依賴組織，不與目錄的原生分類機械地一一對應。資料、圖例等基礎工具可為後續模組提前接入，但必須逐項更新狀態。

## L1 下一批待辦

| 批次 | 狀態／入口 | 依賴與交付 | 原生驗收重點 |
| --- | --- | --- | --- |
| B01 | 下一批；LB-003 Deconstruct Location | 以現有 Location 結果作輸入，建立原生轉換及解構結果，加入既有工具操作 | 一般／半小時／45 分鐘／負時區、經緯度與海拔；無效型別及失敗保留結果 |
| B02 | 待 B01 及資料契約；LB-015 Apply Analysis Period | 重用完成的分析期間與 EPW 原生集合；明確顯示來源、套用期間與輸出 | 年度、跨年、跨夜、次小時邊界；時間／數值／單位對齊；月資料不可誤作逐時 |
| B03 | 待基礎契約；LB-029 Deconstruct Data、LB-023 Construct Data | Header／DataCollection 可攜契約及原生重建；每個入口各自驗收 | 往返保留原生 Header、時間、值、單位與資料型別；空值／錯誤輸入依原生規則處理 |
| B04 | 待 B03；LB-024 Construct Data Type、LB-118 Unit Converter | DataType／單位工具；必要 Header 等依賴另列目錄入口，不能隱含宣告已完成 | 原生 SI／IP 與相容單位轉換、無效單位、精度；不能只換顯示標籤 |
| B05 | 待資料／地點契約；LB-002 Deconstruct Design Day、LB-008 Import Design Day、LB-005 EPW to DDY | 重用 DDY／STAT 原生物件；設計日明細、氣象集合與 DDY 檔案輸出 | 原生 JSON／IDF／逐時資料一致；不同氣候與缺失條件；寫入範圍及輸出來源 |
| B06 | 待依賴收斂；LB-004 Download Weather、LB-006 EPWmap 及剩餘 L1 資料入口 | 先界定下載／解壓／瀏覽器等副作用與資料操作，再逐項接入 | 成功／失敗、檔案範圍與返回路徑；不與純分析批次自動混跑 |

上述為待開發清單，未新增 adapter 或宣告已驗收。B06 的剩餘入口須由完整功能表逐項收斂；不以完成六個批次標題代替完成 L1。

## 每個功能的交付門檻

1. 核對原生 UserObject 名稱、ID、GUID、檔案 SHA、必填／選填、預設值、輸出及版本來源。119 個元件共用 GhPython ComponentGuid，不能用它作功能身分。
2. 建立型別化請求／結果與原生轉換；保留數值、單位、時間、Location／DataCollection 等真正的物件意義，不以任意字串或 UI slider 取代。
3. 用原生元件或原生輸出作參考，檢查正常、邊界與錯誤情境，以及 GH 文件隔離與釋放。不同物理模型明示自己的適用條件。
4. 在現有面板提供合理預設、清晰單位、Advanced、Validation、錯誤狀態與結果；保留前次結果，只清理 owned preview。依 [UI 標準](UI_UX_STANDARD.md) 檢查窄／寬版與相應操作。
5. 新版目錄建置、正式註冊、新 Rhino slot 載入與相關既有功能回歸。不可覆寫已載入組件；同步執行限制不得用假進度／取消掩蓋。
6. 更新 JSON／Markdown／HTML 的該入口狀態、目前狀態、驗收 evidence 與開發日誌。工具與預設選單用相應操作驗收，不虛構求解數值。

所有發布門檻與已知限制見 [PROJECT_STATUS](PROJECT_STATUS.md)。Ladybug 里程碑完成後才恢復 Eddy3D 等引擎工作；V2 詳細互動架構仍待規劃。
