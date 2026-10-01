# Ladybug 完整功能開發計畫

使用者優先順序：先從完整 Ladybug 功能開發。真實安裝入口共 122 個，詳見 LADYBUG_FEATURE_TABLE.md；可搜尋的 HTML 版本包含完整輸入／輸出與預設選項。

## 覆蓋與接入原則
- 122 個入口均已逐一建立並盤點，含 119 個原生元件及 3 個 ValueList 預設選單。建立成功不等於求解通過。
- Hub 目前正式分析為 Incident Radiation；Import EPW、Cumulative Sky Matrix 用作已驗證後端。其餘項目逐一接入，不以「已安裝」冒充已完成。
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

下一個具體實作：L1 的氣象／時序型別及 Adapter，先擴展既有 Import EPW，提供完整氣象欄位、地點、時間篩選與原生結果比對。每次交付更新功能表狀態，避免以整組分類的完成度掩蓋未接入元件。

正式插件仍為已驗證的 0.3.0。本次目錄／計畫是功能覆蓋工作，未聲稱新增 119 個已完成分析。Eddy3D 僅保留唯讀盤點，CFD 暫緩。

辨識原則：122 個 UserObject GUID 各不相同；119 個分析元件共用 GhPython 的 ComponentGuid。後續 Adapter 依 UserObject 身分、檔案與 SHA-256 解析，不能以共用基底 GUID 選取功能。
