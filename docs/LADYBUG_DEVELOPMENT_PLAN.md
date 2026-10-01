# Ladybug 完整功能開發計畫

使用者優先順序：先從完整 Ladybug 功能開發。真實安裝入口共 122 個，詳見 LADYBUG_FEATURE_TABLE.md；可搜尋的 HTML 版本包含完整輸入／輸出與預設選項。

## 覆蓋與接入原則
- 122 個入口均已逐一建立並盤點，含 119 個原生元件及 3 個 ValueList 預設選單。建立成功不等於求解通過。
- Hub 目前正式功能為 Incident Radiation、Import EPW、Construct Location、Import STAT、Import DDY、Analysis Period、Calculate HOY 與 HOY to DateTime；Cumulative Sky Matrix 用作已驗證輻射後端。其餘項目逐一接入，不以「已安裝」冒充已完成。
- 每個入口保留原生名稱、GUID、必填／選填參數、輸出與版本。統一請求／結果邊界；UI 不操作 GH slider。
- Data Collection、Location、Sky Matrix、VisualizationSet 等需明確的型別轉換。不能用任意字串化取代真實數值、單位或物理物件。
- 下載、檔案開啟、Rhino Sun／View 變更及版本同步等入口標示副作用；不跟純分析批次一起自動執行。

## 開發順序與驗收
| 里程碑 | 功能範圍 | 完成條件 |
| --- | --- | --- |
| L0 完整目錄 | 122 個入口、分類搜尋、逐項輸入／輸出及狀態 | 本機全量盤點對齊；已完成 |
| L1 氣象與時間資料 | EPW／STAT／DDY、Location、Analysis Period、HOY、資料篩選與單位 | 以真實文件比較原生輸出；保留時間索引、單位及缺值 |
| L2 太陽與幾何 | SunPath、Sky Mask、Direct Sun Hours、Solar Envelope、輻射、視域 | 原生數值逐項比較；單位、幾何與遮蔭測試；結果預覽與圖例 |
| L3 熱舒適 | PMV、Adaptive、UTCI、PET、MRT、Thermal Indices 與相關參數 | 採用原生模型與單位；明示適用條件；數值與統計比對 |
| L4 圖表與呈現 | Psychrometric、Wind Rose／Profile、Hourly／Monthly、Sky／Radiation 圖表 | 原生資料一致；清晰圖例、標籤與縮放；UI/UX 驗收 |
| L5 工具與維護 | 資料建構／儲存、矩陣、網格、圖例、視圖、版本與預設選單 | 可重現操作、明確副作用與檔案範圍；逐項狀態可追蹤 |

L1 已完成 EPW 的原生資料輸出／HOY 篩選／缺值遮罩、Construct Location 及 STAT／DDY 匯入與原生比對。三項獨立時間功能已實測接入；下一批為 Location 解構及資料工具。每次交付更新功能表狀態，避免以整組分類的完成度掩蓋未接入元件。

正式插件更新為 0.8.3。122 項目錄完成；八項功能已獨立接入、一項輻射後端使用、113 項待接入。新增 Analysis Period、Calculate HOY、HOY to DateTime，17 項原生比對／錯誤測試通過。統一首頁與共用導覽整合五種工作流程；版面驗收與實測 scope 分開記錄。接下來為 Location 解構、Apply Analysis Period 與資料工具；L1 尚未全部完成。Eddy3D 僅保留唯讀盤點，CFD 暫緩。

辨識原則：122 個 UserObject GUID 各不相同；119 個分析元件共用 GhPython 的 ComponentGuid。後續 Adapter 依 UserObject 身分、檔案與 SHA-256 解析，不能以共用基底 GUID 選取功能。
