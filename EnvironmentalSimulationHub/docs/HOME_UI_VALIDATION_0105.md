# 0.10.5 原生操作補驗與 MCP 失敗判定修正

日期：2026-10-03。外掛二進位維持 0.10.5，本輪修改 Python MCP 探測器與驗收工具，未重新建置 .NET 外掛或重跑先前完整 168 項求解／平台回歸。正式仍為 0.9.2／9 獨立、1 後端、112 待接入；候選 10／1／111。完整 V02 UI 仍未閉合，V03 未啟動。

[本輪操作／工具證據](evidence/native_ui_0105/acceptance.json) · [原生停靠保護](evidence/native_ui_0105/dock_guard.json) · [鍵盤／對話框觀察](evidence/native_ui_0105/keyboard_dialog_observations.json)

## 失敗判定修正

Rhino 的 run_python 回應可能先印正常 JSON，再附加 Rhino.Runtime.Code.Execution.ExecuteException 或 Python Traceback。舊 tools/mcp_probe.py 只比對整段字串開頭，會將這種回應標記為 MCP_RESPONDED 且無 error。本輪實際停靠測試在 finally 誤對 Rhino 主視窗包裝器設定 Size，得到 NotImplementedException；舊工具漏判，實際驗收檔也未產生，因此未接受該次測試。

新版逐行辨識診斷行的開頭，正常輸出之後的例外也會拒絕；未包裝的文字回應同樣檢查。一般成功 JSON 中引用例外名稱不被誤判。12 項工具測試通過：既有 8 項＋stdout 後 Rhino 例外、stdout 後 Python traceback、未包裝錯誤、成功資料引用診斷名稱。以真實失敗 receipt 重讀確認被拒絕。

唯讀掃描 161 份 MCP_RESPONDED transport，21 個呼叫含錯誤（包含已知失敗重試，並非 21 次新缺陷）。清單記於本輪 acceptance；原 transport 不改寫。0.10.5 原完整驗收的成功 transport 未被新檢查器拒絕；通訊回應不能代替執行成功或驗收檔。

## 隔離與本輪通過範圍

原驗證 PID 21244 的物件已變為 608，與先前 fixture 不符，只唯讀檢查，不在其中操作。另開非 adopted slot capybara／PID 27524／文件 268435457，實際載入 0.10.5.0，從 0 物件、未修改文件開始；指令鎖定 PID、文件與組件版本，每次操作前要求 0 物件。

| 本輪新增操作 | 已確認範圍 |
| --- | --- |
| 原生停靠保護 3 項 | OpenPanelAsSibling 回傳 false，改用公開 OpenPanel(dockbar, panel, true) 進入已有容器；實際 ParentWindow 是 Rhino 主視窗，平台 300 × 542；初始浮動加寬策略不改主視窗尺寸、初始化標記不被設為完成；文件 0 物件／mm 不變 |
| 原生鍵盤 3 項 | SDK 設模組選單初始焦點；Computer Use 發送 Tab 到首頁按鈕、Shift+Tab／End 選日照時數、Tab／Space 回首頁，SDK 讀回 Eto HasFocus 與 ActiveModule 證明操作結果 |
| 原生存檔取消 1 項 | 實際 Windows 另存新檔對話框被觀察，Escape 關閉；Eto 回傳 Cancel，沒有建立檔案。是同型 Eto 對話框的取消測試，未經正式結果匯出按鈕 |

總計 **7 項額外原生操作**，另有 **12 項工具測試**。不將它們包裝成重跑全部 175 項。先前 168 原生、Core 25、44 張淺色離屏圖與 2 張視埠的版本化歷史證據保持原範圍。

## 部分進度與仍待驗收

真正日照面板的選取按鈕經 SDK PerformClick 啟動，觀察到「選取日照時數分析面」原生提示，送出 Escape，後續讀回仍為空輸入／0 物件；成功選取及完整 picker 流程仍待驗收。modal／picker 期間 MCP 等待可能逾時，但 UI 已開啟；保留逾時 receipt，以原生觀察及完成結果另行判定，不能把排程成功當作動作完成。

兩次影像擷取仍為 FrameArrived／window capture timed out。鍵盤 UIA 的 focused_element 有時停留在指令歷史，故模組／焦點由公開 Eto HasFocus 及原生狀態讀回核對；不使用舊 UIA index 猜測點擊。

完整 320／480 停靠版面、深色切換、全模組 Tab 順序、成功幾何 picker、正式匯出存檔／取消及同仁試用仍待驗收。FloatPanel 在此輪未使面板離開主視窗，保留該限制；finally 排除 MainWindowHandle，避免設定唯讀主視窗包裝器。不宣稱已恢復浮動或完成 Dock 視覺驗收。新測試文件最終 0 物件、mm、無完成結果；未操作使用者原模型或修改第三方套件。

## 下一步與知識維護

先恢復可用桌面影像擷取、完成上述 V02 原生 UI 門檻，再正式交付及 V03 Sky Mask。每次有進度同步地端與原有 Notion；本輪新增固定驗證編號 VER-HOME-0105-UI-01，歷史 VER-HOME-0105-01 及更早 receipts 保持原範圍。本輪同步證據另存 evidence/notion_native_ui_0105_sync_2026-10-03.json。
