# 0.10.3 幾何重綁修正與家用回歸 · 2026-10-03

目前為 **NATIVE_VERIFIED_FULL_UI_PENDING**。0.10.3 修正日照時數的公開 `SetGeometry`：更換模型單位後，明確重新選取可建立新的文件／單位綁定，接著使用原生 Ladybug 求解。正式基準仍為 **0.9.2／9 獨立、1 後端、112 待接入**；候選 10／1／111，尚未正式交付 V02 或啟動 Sky Mask。

[彙總 receipt](evidence/home_0103/acceptance.json) · [目前狀態](PROJECT_STATUS.md) · [Notion 本輪同步狀態](evidence/notion_home_0103_sync_2026-10-03.json)

## 問題、修正及邊界

0.10.2 中 `SetGeometry` 先執行舊綁定檢查；單位改變後，檢查提示「重新選取幾何」，但重新選取 API 自身也被 `SUNH-DOC-002` 阻擋。這是公開 SDK／MCP 選取恢復的缺陷，不能推論原生 picker 同樣失效。[修正前重現](evidence/home_0103/selection_rebind_before.json) 保留真實 0.10.2.0 失敗。

本次明確重新選取改用活動文件重新綁定；兩個陣列都成功複製後才更新選取，避免無效 context 造成半套狀態。舊綁定仍阻擋求解，前次完成結果仍保留並標示過期。只修改 `SunHoursPanel.cs` 與組件版本，Core／Adapter 求解原始碼未變。

## 真正通過的範圍

| 檢查 | 本輪結果 | 證據 |
| --- | --- | --- |
| 建置與載入 | 0 錯誤／0 警告；Rhino 8.35、.NET 8.0.31，新專用 PID 30168、slot aardvark、文件 268435457 載入 0.10.3.0 | [manifest](evidence/home_0103/build_manifest.json)、[identity](evidence/home_0103/identity.json) |
| 既有地點／氣候／時間 | 39 項 | [原生回歸](evidence/home_0103/runtime/release_0101_loaded.json) |
| 日射 | 21 項；基準平均 1233.3471168086037 kWh/m² | [平台](evidence/home_0103/runtime/platform_0101_runtime.json) |
| SunPath | 31＋文字 2＋EPW 轉移 1 項 | [原生](evidence/home_0103/runtime/sunpath_0101_runtime.json) |
| 日照時數 | 45 項，含 13 組獨立 stock 比較 | [日照](evidence/home_0103/runtime/sunhours_0101_runtime.json) |
| 單位重綁 | 7 項：初始原生求解、過期綁定阻擋／保留結果、明確重選、按新單位求解、無效重選不改綁定、回復單位再求解、清理還原 | [新增回歸](evidence/home_0103/selection_rebind_checks.json) |
| 八模組 workspace | 15 項 | [平台整合](evidence/home_0103/runtime/workspace_0101_runtime.json) |
| Core／MCP 工具／輸出 | 分別 25／8／3 項 | [Core](evidence/home_0103/core_checks.json)、[通訊](evidence/home_0103/mcp_probe_checks.json)、[回讀](evidence/home_0103/export_roundtrip.json) |
| 正式控制項離屏版面 | 44 張、320／480 px 淺色；11 張原像素 contact sheets 已檢視，日照數值及 h 色樣欄寬缺陷未重現 | [擷取](evidence/home_0103/runtime/ui_0101/capture.json)、[檢視範圍](evidence/home_0103/ui_review.json) |
| 真正 3D 視埠 | 2 張；臺北測試 256 格、7–13 h、平均 9.08203125 h | [視埠](evidence/home_0103/runtime/ui_0101/viewport_capture.json) |
| Ladybug 安裝盤點 | 122 個入口 SHA 相符；不是 122 項功能驗收 | [彙總](evidence/home_0103/acceptance.json) |

原生／平台合計 **161 項**；Core、通訊、輸出另列。部分輸出名稱保留 `0101`／`0102` 以追溯來源，`home_0103` 本輪版本欄位及載入身分都為 0.10.3。測試模型不是正式案場或法規判定。Eddy3D 組件載入不代表 CFD 求解可用。

## 連線、載入與待完成門檻

第一次回歸因註冊路徑與明確載入候選不同而中止；之後測試程序已不在執行，另一次啟動 60 秒逾時。保留 `native_regression_registration_attempt.json`、`native_regression_interrupted_transport.json` 及 `spawn_timeout_transport.json`。沒有證據判定程序消失原因，不將它宣稱為已確認 Rhino 崩潰。最後重新建立 **非 adopted** 專用槽位，鎖定 PID／文件／實際組件路徑後，9 個原生呼叫及 3 個補充呼叫成功。

使用 `PlugIn.LoadPlugIn` 明確載入測試候選，未執行正式升版註冊腳本。SDK 本次載入後 `PathFromId` 及 HKCU `PlugIn/FileName` 均回讀為 home-build 0.10.3 路徑；這是本機候選登錄，不能視為正式部署驗收。[登錄回讀](evidence/home_0103/registration_readback.json)。

新程序桌面擷取刷新視窗後仍為 `window capture timed out: timed out waiting on channel`。完整 Dock 窄／寬、原生深色切換、鍵盤、幾何 picker 及檔案對話框未驗收；離屏圖與 SDK 選取測試不能代替這些項目。

使用者另回報 **面板預設開啟很窄，須手動拉寬（UI-WIDTH-0103）**，尚未修復。需先區分停靠分頁與浮動容器，再取得實際初始寬度。2026-01-20 [McNeel 開發者答覆](https://discourse.mcneel.com/t/change-panel-width-programmatically/214758) 說明 Rhino 8／9 尚無公開 API 可設定面板外框寬度；Eto Size／MinimumSize 不能作為宿主自動拉寬的完成證據。[官方 WindowLayout](https://docs.mcneel.com/rhino/8/help/en-us/commands/macros.htm) 可保存容器寬高；需確認使用者目前排列，再評估只處理本面板的配置方案，不能直接重設全部 Rhino 工作區。本問題保留在完整 UI 出口門檻。

[Computer Use SKILL.md](C:/Users/ciszo/.codex/plugins/cache/openai-bundled/computer-use/26.930.21537/skills/computer-use/SKILL.md) 引用的 [guidance.md](C:/Users/ciszo/.codex/plugins/cache/openai-bundled/computer-use/26.930.21537/docs/guidance.md:256) 要求："Refresh the app/window selection and retry once; report the exact error if recovery fails." 本次已刷新重試，依要求停止使用失效畫面的座標。待桌面恢復可擷取，再完成 UI、正式交付及內部試用；之後接續 V03 Sky Mask。

## 下次重播

新建專用 slot 後先執行 `tools/home_0103/prepare_load.py`，執行其 load calls；成功取得 identity 後才執行 `prepare_validation.py`。產生的 `native_regression_calls.json` 與 `presentation_export_calls.json` 鎖定該次身分，不能直接重播已結束程序的呼叫。Router 存取 AppData 使用正式執行核准；不覆寫已載入版本二進位及歷史 receipts。

本輪知識同步沿用既有 Notion 資料庫與固定 ID，新的版本化驗證編號為 `VER-HOME-0103-01`；實際完成／讀回狀態以日期化同步 receipt 為準。有實際進度才更新雙端並回報，無變化保持安靜。
