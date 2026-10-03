# 0.10.6 候選 · 停靠資料保留與正式匯出

2026-10-03。正式版本仍為 0.9.2；本輪是既有平台與日照流程的修正，不增加正式功能覆蓋。完整機器資訊、檔案 SHA、分項結果與失敗重試見 [acceptance.json](evidence/session_final_0106/acceptance.json)。

## 問題與結果

在自建隔離模型完成無遮蔭與遮蔭日照後，用公開 Rhino SDK 關閉平台並在另一容器開啟。0.10.5 的外框實例遭重建，模組回到首頁，日照結果為空、情境從 2 變成 0；模型與 owned preview 仍存在。失敗原證據 [dock_roundtrip.json](evidence/export_ui_0105/dock_roundtrip.json) 保留。

0.10.6 由每份 Rhino 文件的工作階段保存模組快取，新的已註冊外框重新掛接同一組控制項。一般離屏擷取外框保持獨立。IPanel shown／hidden／closing 及 Dispose 協調掛接與釋放；外框釋放前卸下模組，文件關閉及 Rhino 結束才釋放該份快取。沒有新增獨立 Dock，也沒有改寫求解器。

## 本輪最終建置與測試

| 項目 | 結果 | 範圍／證據 |
| --- | ---: | --- |
| Release 建置 | 0 錯誤／0 警告 | artifacts/home-build/0.10.6；兩個新非 adopted Rhino 實際載入版本與來源 |
| 既有原生回歸 | 161 通過 | 地點／氣候／時間 39、日射平台 21、SunPath 31＋1＋2、日照 45、重綁 7、八模組平台 15；[runtime](evidence/full_0106/runtime) |
| 資料保留／文件隔離 | 33 通過 | 實際停靠造成外框重建；草稿、完整結果與兩情境保存；普通擷取外框獨立；第二份 headless 文件隔離及 closing callback；[檢查](evidence/session_final_0106/session_checks.json) |
| 正式模型 picker | 2 通過 | 實際按鈕→Rhino GetObject 接受預選；結果與情境保留。滑鼠後選未驗收；[檢查](evidence/session_final_0106/picker_checks.json) |
| 正式匯出／取消 | 3 通過 | 結果按鈕→原生 SaveFileDialog→確認檔名→存檔→完整 JSON 一致；比較取消保留兩情境／解讀且未產生檔案；[檢查](evidence/session_final_0106/export_checks.json) |
| Core／MCP 工具 | 25／12 通過 | 使用隔離輸出建置 Core，再以真實 EPW 與測試輸出路徑執行；12 項 MCP 錯誤辨識測試 |

161＋38 共 199 個檢查含原生操作、狀態及文件生命週期邏輯；不是 199 個獨立模擬功能。第二文件使用 headless SDK 與 closing callback，不代表多視窗文件切換已驗收。前輪 0.10.5 的浮動寬度 7 項、44 張淺色離屏影像與 2 張視埠未重跑，不計入本輪。

## 真實結果與匯出

自建 8×8 m 平面、0.5 m 網格、0.1 m 取樣偏移，臺北、UTC+8、13 個逐時太陽取樣。原生 Ladybug Direct Sun Hours／Rhino 射線交會：256 點，無遮蔭平均 13 h；加入 3 m 高遮蔭後平均 9.57421875 h，最小 8 h、最大 13 h。平均是算術點平均，不是面積加權；含首尾的 13 個取樣不能混稱為 13 小時曆時長度，也不能稱為採光照度。

[正式對話框匯出的完整結果](../samples/session_final_0106/result_from_native_dialog.json) 與 API 完整 JSON 契約完全相等，保留輸入、模型／元件指紋、單位、時間約定、網格、數值與預覽設定。[檔案讀回](evidence/session_final_0106/export_result_readback.json) 保存 SHA。原生檔名設定回報逾時，但 accessibility 讀回已確認正確完整路徑；再由存檔鍵與磁碟資料建立成功證據。比較存檔對話框無法可靠讀取，成功存檔仍待驗收。

## 過程失敗與修正

- 首次 0.10.6 新程序自動載入已註冊的 0.10.5，被版本檢核拒絕；關閉空白程序、備份並更新單一 HKCU FileName，再以新程序確認 0.10.6。既有使用者程序沒有熱換版。
- 第一份資料保留測試把「暫時隱藏其他 Hub 預覽」也列為不變資料；該選項原本就會在切換模組時釋放。修正測試起始條件後 33 項通過，最終建置又在另一新程序完整複驗。
- 舊平台回歸要求關閉重開後外框仍為同一實例，與實際 Rhino 重建行為不符。只修改本輪重播測試，要求八個模組同一實例且完整快照一致；7 個已成功呼叫保留，後 2 呼叫通過。歷史測試不改寫。
- 初次清理用 ObjectTable.Count 比較活物件，計入已刪除物件而失敗；改用活物件迭代核對。首次 Core 指令路徑／參數錯誤與共用輸出鎖定均保留於過程說明；最終以隔離建置與完整參數通過 25 項。
- 匯出原生 modal 會阻住 MCP 回應；逾時 receipts 保留 UNVERIFIED，沒有改寫成成功。實際成功結果匯出使用獨立 UI／檔案證據驗收。

## 尚待完成

完整停靠窄／寬版面、原生深色、完整鍵盤、滑鼠後選、比較成功存檔、跨機無協助試用仍待驗收。V02 未正式交付；下一功能 V03 LB-067 Sky Mask，其後 LB-068 Solar Envelope。正式 9／1／112、候選 10／1／111；不把安裝、盤點或檢查數當作功能覆蓋。

## 知識與版本

本機目前狀態、索引、建置、計畫及開發檢視同步更新。Notion 沿用既有資料庫：詳細紀錄保留規格與證據，既有首頁呈現重點，固定 KB-003 視覺化頁呈現里程碑與流程。[視覺化精華](DEVELOPMENT_HIGHLIGHTS.md)、[Notion 維護與雙端 receipt](NOTION_KNOWLEDGE.md)。Git 僅地端提交；遠端驗證與上傳仍待處理。
