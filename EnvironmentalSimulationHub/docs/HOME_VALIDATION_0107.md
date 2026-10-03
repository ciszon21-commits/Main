# 0.10.7 候選 · 日照方案匯入與跨程序恢復

日期：2026-10-03。接續 0.10.6，依 ROADMAP X1 補齊日照方案檔案恢復；V02 完整宿主驗收尚未閉合，V03 未啟動。正式 **0.9.2／9 獨立、1 後端、112 待接入**，候選 **10／1／111**；本輪不增加原生元件覆蓋。

## 交付行為

- 第六階段新增「匯入方案比較 JSON…」，單一方案即可匯出，最多 20 個方案、檔案 64 MiB。完整原生結果與選擇可在新 Rhino 程序恢復。
- Core 先檢核整批結構、名稱、容量、取樣、時數／統計、網格及來源欄位。錯誤或重複名稱整批拒絕，既有資料保留。
- 匯入只讀歷史比較資料，不綁定舊物件 UUID、不重建模型／預覽、不重跑求解、不改目前輸入或完成結果。
- 比較核對實際太陽條件及原有摘要；檔內 Interpretation 不採信，重新產生文字；匯入方案明示歷史來源與未核對目前模型。

[使用方法與契約](SUNHOURS_SCENARIO_ARCHIVE.md)。產品 Core／Plugin 有變更，Adapter 原生求解路徑保持既有實作。

## 本輪驗證

| 層級 | 完成範圍 | 證據 |
| --- | --- | --- |
| 建置 | Plugin、Core Checks、Archive Checks：0 錯誤、0 警告；Rhino 8.35／.NET 8.0.31 載入 0.10.7 | `evidence/archive_0107/identity.json`、`evidence/full_0107/identity.json` |
| 方案契約 | 42 項，使用 0.10.6 真實匯出資料及損壞／衝突變體；完整結果 roundtrip、來源變更、格式與容量 | `evidence/archive_0107/core_archive_checks.json` |
| Rhino 匯入 | 17 項，歷史結果完整保留、選擇恢復、不改模型、晚段錯誤整批拒絕、北向變更不顯示差值 | `evidence/archive_0107/archive_checks.json` |
| 狀態／文件 | 32 項，八模組導覽、六方案／完成結果保留、停靠移動、關閉重開、獨立 capture shell、headless 文件隔離 | `evidence/archive_0107/session_checks.json` |
| 新程序恢復 | 13 項；六個完整 NativeResult、中文名稱、索引與重新匯出讀回完全一致；模型為空、未修改 | `evidence/archive_resume_0107/restore_checks.json` |
| 既有原生回歸 | 161 項；氣象／地點／時間 39、日射 21、SunPath 31＋1＋2、日照 45、重綁 7、平台 15 | `evidence/full_0107/native_regression_final_transport.json`、`runtime` |
| Core／工具 | 原有 Core 25、MCP 工具 12 | `evidence/full_0107/core_checks.json`、`mcp_probe_checks.txt` |
| 視覺 | 新版比較／匯入區：320／480 淺色離屏 4 張，含目前求解與恢復歷史兩種狀態；actual width 相符，已檢視 | `evidence/full_0107/runtime/ui_0101`、`evidence/archive_resume_0107/runtime/ui_0101` |

全平台回歸位於隔離 PID 18536；方案操作 PID 28280；重開恢復 PID 20924。首個 PID 28756 在載入前已退出，未操作原有使用者 Rhino 21244。不同測試模型結果分開記錄，不把檢查數當成已接入功能數。

## 真實案例與檔案回讀

8×8 m 分析面、0.5 m 網格、0.1 m 感測偏移、臺北 06/21 06:00–18:00 共 13 個逐時取樣；256 個點，無遮蔭平均 13 h、新增部分遮蔭平均 9.57421875 h（最小 8、最大 13）。是原生格點算術平均，非面積加權；13 個含首尾取樣不等於 13 小時曆時。

`samples/archive_0107/comparison_export_api.json` 保存四個匯入方案與兩個本輪求解方案，SHA-256 `dcb5713fcb3c220f113a97ff4b671f1f685fea58165f99ff797947a08533f50c`。來源為正式 ExportComparisonJson 契約，從測試 fixture 回讀寫入磁碟；不是原生 SaveFileDialog 成功存檔。新程序從檔案經正式 ImportScenariosJson 恢復，全部 NativeResult 完全相等；再次匯出 `comparison_after_restart.json` 讀回一致。

## 失敗與限制

- 首次 load retry 測試仍引用舊 spawn receipt，PID 守衛阻止操作；全回歸準備的錯誤呼叫檔名同樣未執行 Rhino 腳本，保留失敗 transport。
- 狀態測試原先假設主機必定重建外框；本次持久佈局重用外框，已改為記錄實際 identity 並檢查資料保留。本輪沒有重新證明新外框重建；0.10.6 的真正重建證據保留。
- 比較對話框測試的背景 Timer 使用了不存在的 `RhinoApp.AsyncInvoke`，未處理 PythonException 導致測試 PID 28280 結束。Windows .NET Runtime 堆疊已保存於 `test_callback_crash.txt`；產品程式未使用該 API。測試工具改回 Eto `Application.Instance.AsyncInvoke` 並移除 Timer，不計為產品匯出通過。
- 正式匯入按鈕已開啟 OpenFileDialog；MCP 於模態期間逾時，accessibility 經重試仍不可讀。取消後模型／方案仍空白，API 恢復成功；原生檔案選取成功仍待驗收。
- 比較原生成功存檔、完整 Dock 窄／寬版面、深色、全鍵盤、滑鼠後選、多視窗文件 UI、跨機無協助試用未通過。四張離屏圖不代替以上門檻。

候選載入路徑為 `artifacts/home-build/0.10.7/EnvironmentalHub.Plugin.rhp`，已備份與讀回；原有已開啟 Rhino 不會自動更新已載入組件。正式發布與遠端上傳未完成。

本機目前狀態、索引、建置與計畫及 Notion 三層知識依實際進度更新；詳細結果、重點與視覺化精華互相連結，歷史 evidence 不改寫。
