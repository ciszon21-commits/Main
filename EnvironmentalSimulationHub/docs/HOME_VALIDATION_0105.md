# 0.10.5 浮動面板初始寬度修正 · 2026-10-03

目前為 **NATIVE_VERIFIED_FULL_UI_PENDING**。工作平台的首次浮動開啟寬度已修正；正式基準仍為 **0.9.2／9 獨立、1 後端、112 待接入**，候選 10／1／111。完整 V02 UI 出口尚未閉合，V03 Sky Mask 尚未啟動。

[彙總證據](evidence/home_0105/acceptance.json) · [寬度檢查](evidence/home_0105/floating_width_checks.json) · [本輪 Notion 同步](evidence/notion_home_0105_sync_2026-10-03.json)

## 問題與實作

使用者回報面板預設開啟很窄、需要手動拉寬。唯讀 MCP 在使用者原 Rhino PID 12004 確認 0.10.3.0；平台位於真正的 Eto 浮動視窗，外框 436 × 619、內容 426 × 591。儲存的 containers.xml 同樣記錄浮動 436 × 619，僅讀取，未直接修改。公開 `Eto.Forms.Control.ParentWindow`／`Window.Size` 試驗成功將外框改為 500、內容 490，位置／高度／物件／模組不變，試驗後還原。[宿主讀回](evidence/ui_width_0103/host_retry.json)、[公開 API 試驗](evidence/ui_width_0103/width_probe.json)。

`HubWorkspacePanel` 只在首次開啟本平台的真正註冊實例時，將自己的可調整浮動外框補足至 500 個 Eto 邏輯單位，並以螢幕工作區寬度為上限。已較寬時保留；使用者手動縮窄後，切換模組與關閉重開不再強制加寬。停靠到 Rhino 主視窗、共用已開啟其他面板的容器、一般 Eto 視窗／離屏實例皆排除；沒有修改 solver、模型單位或重設 Rhino 工作區。

RhinoCommon 沒有公開的通用 Dock 寬度設定 API；本修正使用實測宿主所提供的公開 Eto Form 屬性，範圍限浮動視窗，不能推論所有停靠／平台版本均完成。[McNeel 面板尺寸說明](https://discourse.mcneel.com/t/eto-forms-panel-ipanel-size-does-not-work/203108)、[Eto 視窗實作](https://github.com/picoe/Eto/blob/develop/src/Eto.Wpf/Forms/WpfWindow.cs)。

## 中間候選保留

0.10.4 原生／平台 167 項、Core 25、MCP 工具 8、輸出 3 項通過，但新版加寬策略也套用測試用一般 Eto Form；要求 320 的 22 張擷取实际寬度 484，被裁切至 320。因此本批不能驗收窄版，0.10.4 沒有交付。[拒絕範圍](evidence/home_0104/candidate_disposition.json)。0.10.5 增加真正註冊實例限制及一般視窗排除測試，重新建置、另開 Rhino、重跑及擷取，不用中間候選結果替代新版驗證。

0.10.4 嘗試 `OpenPanelAsSibling` 搬移到 Layers 容器時回傳 false，[失敗 receipt](evidence/home_0104/floating_width_attempt1.json) 保留；0.10.5 未將此算作停靠驗收。

## 本輪真正通過的範圍

| 檢查 | 結果 |
| --- | --- |
| 建置／載入 | SDK 8.0.425；0 錯誤／0 警告；Rhino 8.35／.NET 8.0.31，非 adopted 專用 PID 21244、slot bonobo、文件 268435457，載入 0.10.5.0 |
| 原生／平台 | 168 項：地點／氣候／時間 39、日射 21、SunPath 31＋文字 2＋EPW 1、日照 45、八模組平台 15、單位重綁 7、浮動寬度 7 |
| 新增寬度 | 首次 500／內容 490、手動 320 後切換及重開保留、640 不缩小、300 初始補足並保留位置／高度、物件與單位不變、未註冊的一般視窗實例不調整 |
| Core／工具／輸出 | 分別 25／8／3 項；真實 EPW、MCP 內層錯誤、結果／比較 JSON 與三物件 mm 3dm 回讀 |
| 版面 | 新版 44 張淺色離屏正式控制項；320／480 要求值與 actual width 全數相符；11 張原像素 contact sheets 已檢視 |
| 真正視埠 | 2 張；臺北 256 格、7–13 h、平均 9.08203125 h；日射回歸平均 1233.3471168086037 kWh/m² |
| 安裝盤點 | Ladybug 122 入口 SHA 全數相符；不是 122 功能驗收；Eddy3D 載入不代表 CFD 求解可用 |

來源見 [manifest](evidence/home_0105/build_manifest.json)、[identity](evidence/home_0105/identity.json)、[原生回歸](evidence/home_0105/native_regression_transport.json)、[版面檢視](evidence/home_0105/ui_review.json)。部分輸出檔名保留 0101／0102 以追溯測試來源，版本欄位與執行身分屬於本輪 0.10.5。

## 載入、回退及下一步

先前新 Rhino 恢復已儲存面板時預載舊候選，再載入新版會出現「外掛 ID 已被使用」。本輪先備份並只更新本平台 HKCU `PlugIn/FileName` 至版本化 home-build，保留 [原值](evidence/home_0105/candidate_registration_before.json) 及 [讀回](evidence/home_0105/candidate_registration_after.json)；沒有修改 HKLM、其他外掛或正式覆蓋數。載入腳本先檢查已載入組件，版本不符直接拒絕，避免再次觸發重複載入對話框。失敗啟動／載入 receipts 保留，不能稱為新版通過。

使用者原先開啟的 Rhino 仍載入 0.10.3；已開啟程序不會自動換版。新 Rhino 會使用候選 0.10.5 路徑，專用驗證程序可檢視本輪成果。回退只需將本平台單一 FileName 還原至相应備份，再於新程序核對真正組件；不覆寫已載入二進位。

桌面影像擷取仍逾時，但原生控制項文字可讀。**完整原生 Dock 窄／寬、深色切換、鍵盤、picker／檔案對話框與同仁無協助試用仍待驗收**；44 張離屏影像、SDK 操作與視埠不能替代這些門檻。先完成 V02 UI，再正式交付與 V03；本輪不宣稱已推送 Git 遠端。

重播須使用新非 adopted spawn receipt → `tools/home_0105/prepare_load.py` → 載入 identity → `prepare_validation.py`，不能直接重用已結束程序的 calls。知識同步沿用 8 筆固定頁面與新 `VER-HOME-0105-01`，以本輪同步 receipt 為準；0.10.3 及以前歷史 receipts 不覆寫。
