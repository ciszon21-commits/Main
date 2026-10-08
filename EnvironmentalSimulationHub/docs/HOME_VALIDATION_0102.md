# 0.10.2 家用接續驗證 · 2026-10-03

目前狀態為 **NATIVE_VERIFIED_FULL_UI_PENDING**：家用機已載入 0.10.2，完成原生求解、回歸、輸出與部分視覺檢查；完整原生操作驗收仍待完成。正式交付維持 **0.9.2／9 獨立、1 後端、112 待接入**；候選為 10／1／111。下一功能 Sky Mask 在本輪 UI 驗收後接續。

[彙總 receipt](evidence/home_0102/acceptance.json) · [目前狀態](PROJECT_STATUS.md) · [功能目錄](LADYBUG_FEATURE_TABLE.md)

## 本機與載入

- 開發目錄：`I:\中興工程-工作區\00.DEVE-HOME\GIT-Base\Main\EnvironmentalSimulationHub`。本機工作分支 `codex/home-0102-validation`，來源 HEAD `e7744cea946fd5afe062c02c9a2dada0fa9c2b9f`。
- .NET SDK 8.0.425；實際 Rhino 執行階段 .NET 8.0.31；Rhino 8.35.26251.13001。
- 新建專用 Rhino MCP slot `aardvark`，PID 29180、文件 RuntimeSerialNumber 268435457、連線埠 10500。重播檢查固定程序與文件，不接管其他活動模型。
- Release 輸出 `artifacts/home-build/0.10.2`，0 錯誤／0 警告；新 Rhino 載入版本 0.10.2.0。產品 C# 原始碼沒有本輪新增變更，沿用已交接的欄寬修正。
- Ladybug 122 個安裝入口檔案 SHA 全部與來源盤點相符；這是檔案一致性，並非 122 項求解驗收。Radiance 執行檔已找到。
- Eddy3D 已安裝，Rhino 載入 MetaFOAM、Provisioning.Engines、Eddy3D.Provisioning 1.12.0.827；CFD／OpenFOAM 求解未測試。

## 實際通過範圍

| 檢查 | 本輪結果 | 證據 |
| --- | --- | --- |
| 建置／載入 | 0 錯誤、0 警告；版本與路徑已確認 | [Build](evidence/home_0102/build_manifest.json)、[載入](evidence/home_0102/runtime/release_0101_loaded.json) |
| 既有地點／氣候／時間 | 39 項 | [原生回歸](evidence/home_0102/runtime/release_0101_loaded.json) |
| 日射平台 | 21 項；平均 1233.3471168086037 kWh/m² 與來源相同 | [平台](evidence/home_0102/runtime/platform_0101_runtime.json) |
| SunPath | 31＋文字 2＋EPW 轉移 1 項 | [原生](evidence/home_0102/runtime/sunpath_0101_runtime.json)、[文字](evidence/home_0102/runtime/sunpath_0101_text.json)、[轉移](evidence/home_0102/runtime/sunpath_0101_transfer.json) |
| Direct Sun Hours | 45 項：13 組 stock 比較、15 類無效輸入、17 項操作／owned preview | [日照時數](evidence/home_0102/runtime/sunhours_0101_runtime.json) |
| 八模組 workspace | 15 項 | [工作平台](evidence/home_0102/runtime/workspace_0101_runtime.json) |
| Core preflight | 25 項 | [Core](evidence/home_0102/core_checks.json) |
| MCP 錯誤處理 | 8 項；JSON-RPC、isError、內層腳本錯誤與 traceback 不再被誤判成功 | [工具回歸](evidence/home_0102/mcp_probe_checks.json) |
| 輸出回讀 | 3 項：結果 JSON、比較 JSON、3 物件 mm 模型 | [輸出](evidence/home_0102/export_roundtrip.json) |
| 淺色控制項版面 | 44 張正式 Eto/WPF 離屏影像，320／480 px；欄位與 h 色樣缺陷未重現 | [擷取](evidence/home_0102/runtime/ui_0101/capture.json)、[視覺檢視](evidence/home_0102/ui_review.json) |
| 真正 3D 視埠 | 2 張；臺北範例 256 格，7–13 h、平均 9.08203125 h | [視埠](evidence/home_0102/runtime/ui_0101/viewport_capture.json) |

原生／平台合計 **154 項**。Core、通訊及輸出回讀另列，避免混作原生功能數。範例為測試資料，並非正式案場成果或法規判定。新的 receipts 檔名部分保留 `0101`，用於追溯來源測試套件；位於 `home_0102` 的本轮載入與執行版本為 0.10.2，舊機 receipts 未改寫。

## MCP 通訊與視窗擷取

Router 的 stdio MCP 初始化與工具探索成功，取得 32 個工具；`run_python` 在指定 Rhino 文件成功執行，HTTP 回應 200、IsError=False。[本次唯讀連線證據](evidence/home_0102/host_api_transport.json)。

先前 `0xe0434352` Router 錯誤來自受限執行環境無法建立 AppData listener 目錄；正式核准執行後通訊成功。MCP 能執行 SDK 指令，與桌面截圖服務能否擷取視窗是不同檢查。

實際視窗擷取在啟用視窗、重新列出並選取後仍失敗：`FrameArrived timed out: timed out waiting on channel`、`window capture timed out: timed out waiting on channel`。因此 44 張離屏圖與 2 張原生視埠圖不能代替完整 Dock 驗收；待桌面解鎖並還原 Rhino 後，再取得新的實際 UI 狀態。

使用的 [Computer Use 技能](C:/Users/ciszo/.codex/plugins/cache/openai-bundled/computer-use/26.930.21537/skills/computer-use/SKILL.md) 所附 [guidance.md](C:/Users/ciszo/.codex/plugins/cache/openai-bundled/computer-use/26.930.21537/docs/guidance.md:256) 要求："Refresh the app/window selection and retry once; report the exact error if recovery fails." 本輪已依此刷新及重試；擷取失敗時不能以舊座標完成原生操作驗收。這是桌面擷取的實際阻礙，MCP 仍可正常執行唯讀 SDK 請求。

## 重播與下一步

`tools/home_0102/prepare_replay.py` 為新 root、slot、版本及輸出路徑產生呼叫，修正來源單位負測試的環境假設；[重播 provenance](evidence/home_0102/replay_provenance.json) 保留來源與生成檔案 SHA。不要直接執行原機 `*_calls.json` 或升版 registry 腳本。

唯讀 MCP 檢查（Router 存取 AppData 需要正式執行核准）：

```powershell
python .\tools\mcp_probe.py 'C:\Users\ciszo\AppData\Roaming\McNeel\Rhinoceros\ai\bin\rhino-mcp-router.exe' --timeout 60 --calls .\tools\home_0102\inspect_host_calls.json --output .\docs\evidence\home_0102\host_api_transport.json
```

更新彙總：`python .\tools\home_0102\record_validation.py`；工具回歸：`python .\tests\mcp_probe_checks.py`。專用程序已關閉或文件已變更時，舊 calls 的 guard 應拒絕执行；先建立新的專用測試實例再產生 calls。

待完成：完整 Dock 的窄／寬版、原生主題切換、鍵盤、幾何 picker 與檔案對話框。通過後才能正式交付日照時數、產生內部試用包及啟動 V03 Sky Mask。依使用者要求，部分驗證與候選進度也同步 Notion；此輪已更新 8 筆既有頁、新增 1 筆家用驗證，191 筆唯一編號與正式 9／1／112 讀回相符。[同步 receipt](evidence/notion_home_0102_sync_2026-10-03.json)。這次知識同步沒有宣告完整 UI 或正式發布完成。
