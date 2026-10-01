# 全部開發檢視 — 2026-10-01

0.6.0 後續更新：Import STAT／DDY 已完成三地全部原生 JSON／設計日 IDF 比對、五項錯誤測試與原生 Panel 按鈕驗證。最新目錄為五項獨立功能、一項輻射後端、116 項待接入；下一批為獨立時間工具。詳見 CLIMATE_FILE_MODULE.md 與 release_060_loaded.json。下方仍保留檢視當時基準，非最新完成數。

後續更新：本報告下方保留 0.4.0 檢視當時狀態。其時區顯示問題已於 0.5.0 修正並經原生 Panel 實測；Construct Location 已接入（六組原生比較、五項錯誤測試）。最新狀態為三項獨立功能、一項輻射後端、118 項待接入，詳見 LOCATION_MODULE.md 與 release_050_loaded.json。

檢視基準：本機來源程式、122 項功能目錄、測試 receipts、正式發布檔案 SHA-256 及 Git 狀態。基準提交 dc435d7、插件 0.4.0。本次沒有重新執行 Rhino 求解；以下執行結論引用已保存的實測證據，發布檔案雜湊則於本次重新核對通過。

## 整體狀態

目前是具備兩個可執行模組的開發版，尚未完成完整 Ladybug Hub 或公司部署驗收。

| 範圍 | 狀態 | 已有成果／未完成部分 |
| --- | --- | --- |
| L0 全功能目錄 | 完成 | 122 入口、119 原生分析元件及 3 預設選單；分類、參數、輸出、身分與狀態 |
| L1 氣象與時間 | 部分完成 | Import EPW 全部原生資料輸出、地點、HOY 篩選、時間與單位、缺值；STAT/DDY、獨立 Location／時間工具待開發 |
| L2 太陽與幾何 | 部分完成 | Incident Radiation 與其 Sky Matrix 後端；SunPath、Direct Sun Hours、Sky Mask、Solar Envelope 等待接入 |
| L3 熱舒適 | 未接入 | PMV、Adaptive、UTCI、PET、MRT 與相關指標／參數 |
| L4 圖表 | 未接入 | Psychrometric、Wind Rose、Hourly／Monthly 與其他原生圖表 |
| L5 工具與維護 | 未獨立接入 | 資料／矩陣／網格／圖例／視圖／版本工具與預設選單 |
| UI/UX | 功能實測、視覺验收待完成 | 兩個原生 Eto Panel、步驟與單位、前次結果、匯出與互相導覽；窄 Dock、主題、鍵盤、選取／檔案對話框仍待驗收 |
| Eddy3D CFD | 暫緩 | 僅既有 metadata 盤點，未求解驗證 |
| 整合與部署 | 部分基礎完成 | 版本化發布、設定與兩 Panel 導覽；統一分析入口、方案比較、跨機安裝／相容性驗收待完成 |

目錄狀態實際計數：2 項「已接入並實測」（Import EPW、Incident Radiation）、1 項「輻射後端已使用」（Cumulative Sky Matrix）、119 項「待接入 Hub」。2/119 約 1.7% 是原生分析元件獨立接入覆蓋率，不代表總工程工作量完成百分比。目錄覆蓋則為 122/122。

## 版本與架構

- 正式版本：0.4.0；EnvironmentalHub 開啟輻射、EnvironmentalWeather 開啟氣象。
- release_040_loaded.json 已記錄新 Rhino 工作階段的正式載入／登記路徑、版本與 Panel 執行；本次未即時巡查所有仍運行的 Rhino 程序。舊程序須重啟才能更換已載入組件。
- Core 保留型別化契約與 preflight；Adapters 建立隔離原生 GH definition；Plugin 使用 Rhino/Eto。沒有自行重寫物理求解器。
- 發布 manifest 中七個檔案雜湊重新核對全部一致。開始檢視時 Hub 工作區無未提交改動；本報告為本次新增文件。

## 已有實測證據

| 驗證 | 結果 | 證據 |
| --- | --- | --- |
| Radiation Core | 25 項檢查 | preflight_tests.json |
| 原生輻射比較與執行阻擋 | 3 組數值比較差異 0、5 項 gate | adapter_runtime_validation.json |
| 輻射可靠性 | 6 項：三種模型單位、82 格混合幾何與遮蔭、損壞元件清理、停用求解器 | radiation_reliability_validation.json |
| 輻射規模／來源失敗 | 4096 格單平面差異 0；求解後來源驗證失敗無成功 JSON | radiation_scale_validation.json |
| 原生 Weather | 8 項通過；全年／24 小時／跨年值、單位與時間一致；錯誤輸入／缺值通過 | weather_runtime_validation.json |
| 正式 0.4.0 Panel | 欄位切換、月資料、風向均值隱藏、非連續 HOY、失敗保留結果及輻射回測通過 | release_040_loaded.json |

上述為指定機器、原生元件與測試資料的驗證；4096 格單平面不能代表大型複雜建築性能。缺值案例只驗證指定測試 sentinel，不代表所有異常 EPW 都已覆蓋。氣象 fixture 使用 Seattle，不是正式案場分析。

## 本次來源檢視發現

1. **Weather 時區顯示需修正。** WeatherPanel.Execute 使用 TimeZone:+0;-0;0，將小數時區四捨五入為整數。例如 UTC+5.5 顯示為 +6。契約仍保留 double 原值；需要修正顯示並驗證正負半小時／45 分鐘時區。
2. **UI/UX 驗收尚未閉合。** 功能／控制項狀態驗證不能取代真正版面、主題、鍵盤及 native dialog 檢查。尚不宣告全部介面達到最終美學驗收。
3. **執行仍同步。** Rhino UI 執行期間可能暫停，沒有有效取消／進度；後续需設計符合 Rhino/GH 執行緒限制的任務機制。
4. **資料與相容性範圍有限。** Weather 限非閏年逐時 EPW；月地溫不隨逐時篩選改變。STAT/DDY、閏年、多氣候資料、跨機版本相容性仍待逐項驗證。
5. **Roadmap 部分文字落後。** 大型模型 gate 中已有 4096 格平面證據，整合基礎也已有 Panel 導覽；仍應保留複雜模型與完整整合部署待驗收的界線。

## 後續開發順序

1. 修正小數時區顯示，補對應驗證；同步整理版本／驗收狀態。
2. 完成 L1：STAT、DDY、Location、Analysis Period／HOY 與資料工具；每項建立型別、原生比較、Panel 與錯誤路徑。
3. L2：SunPath → Direct Sun Hours／Sky Mask → Solar Envelope／其他幾何功能；沿用真實幾何、單位與遮蔭比較。
4. L3 熱舒適 → L4 圖表 → L5 工具；工具副作用與檔案範圍明確呈現。
5. 各次發布都完成 UI/UX 與既有功能回測；Ladybug 功能里程碑完成後再接 Eddy3D。

詳細入口、輸入、輸出與狀態見 LADYBUG_FEATURE_TABLE.md／HTML。所有後續介面依 UI_UX_STANDARD.md；持續優先 MCP／SDK，不使用 Computer Use 作為日常開發手段。
