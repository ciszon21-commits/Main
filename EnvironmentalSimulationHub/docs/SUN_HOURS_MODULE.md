## 2026-10-03 · 目前候選 0.10.5

0.10.5 已修正工作平台首次開啟的浮動寬度：外框至少 500、實測內容 490；只處理 Rhino 已註冊的本平台實例。手動縮窄、關閉重開及模組切換保留使用者尺寸，較寬視窗不縮小；一般 Eto 視窗不被調整。168 項原生／平台（既有 161＋寬度 7）、Core 25、MCP 工具 8、輸出回讀 3 項通過，建置 0 錯誤／0 警告。

新版 44 張 320／480 淺色離屏圖與 2 張真正視埠已檢視，requested／actual width 全數相符。0.10.4 曾把測試用一般視窗加寬，窄版擷取失效；該候選保留失敗證據、不交付。完整原生 Dock、深色、鍵盤及 picker／檔案對話框仍待驗收；使用者原本開啟的 Rhino 仍載入 0.10.3，候選載入路徑已更新，新程序可使用 0.10.5。

正式仍為 **0.9.2／9、1、112**，候選 10／1／111；先完成 V02 UI 門檻，再交付及開始 V03 Sky Mask。此次 UI 修正不增加功能覆蓋數。 [驗證範圍](HOME_VALIDATION_0105.md) · [彙總 receipt](evidence/home_0105/acceptance.json) · [雙端同步 receipt](evidence/notion_home_0105_sync_2026-10-03.json)。

以下保留前一候選與正式歷史範圍。

# 日照時數 · LB-061 候選開發紀錄

## 最新候選 0.10.3 · 2026-10-03

修正公開 `SetGeometry` 在模型單位改變後無法重新綁定的缺陷：重選建立新綁定，舊綁定仍拒絕求解；前次結果保留並標示過期，無效重選不更新部分狀態。45 項日照＋7 項重綁、全平台 161 項通過；新版 44 張淺色離屏圖與 2 張視埠已檢視。Core／Adapter 原生求解源碼未變，完整原生 UI 待驗收。[本輪報告](HOME_VALIDATION_0103.md) · [修正前重現](evidence/home_0103/selection_rebind_before.json) · [修正後原生測試](evidence/home_0103/selection_rebind_checks.json)。以下保留歷史開發範圍。

2026-10-02。0.10.1 原生驗證通過，窄版 UI 尚未交付；0.10.2 排版修正只有 Build。家用接續見 [HOME_TRANSFER.md](HOME_TRANSFER.md)。

## 已接入範圍

原生 LB Direct Sun Hours 1.10.0，透過原生 SunPath 重算完成的地點／HOY／北向／時間制；不由外部任意向量取代。分析 Brep／Mesh、外部遮蔭、網格 m、感測點偏移 m、自遮蔭、CPU 及每小時步數。輸入檢核、夜間／錯誤處理、前次結果保留、原生面色樣、h 的最小／最大／平均／格點數、專案目標、session 方案、比較與 JSON 匯出。僅註冊既有 HubWorkspacePanel，第八個內部模組與 EnvironmentalSunHours 指令。

每小時步數支援 1、2、3、4、5、6、10、12、15、20、30、60；先檢查完整非閏年分鐘 HOY 序列，再由原生 SunPath 排除夜間。單一樣本依明確步數加權，期間端點作取樣樣本計數，不把端點數冒充曆時長度；不支援不相容的稀疏或不規則序列。Brep 依間距網格化；Mesh 依既有面取樣，不細分。全夜間來源拒絕，不能編造零時數。

## 數據與視埠

保留原生 mesh colors、values、points；預覽沿法線 0.002 m 顯示偏移避免共面閃爍，匯出保留未位移原生網格及獨立 Presentation 設定。顯示網格開關、只暫時隱藏帶有 Hub owner userstring 的其他預覽；退出／清除還原。使用者同名物件不視為 Hub 預覽，不隱藏或刪除。更換文件／單位會阻止不相容請求。

比較只有相同 SunSource SHA、原生 SunPath／SunHours 元件 SHA 才顯示平均差值；其他方案顯示條件不一致。格點平均不是面積加權，不等於性能改善。最多 20 個不重名 session 方案；關閉 Rhino 前須匯出。目標區間是包含邊界的使用者設定，不是日照法規合規。

## 家用 0.10.2 複驗 · 2026-10-03

45 項日照時數檢查已在新專用 Rhino 通過，與既有模組合計 154 原生／平台項目；13 組 stock 比較保留原生值、points、faces 及色彩。新的 44 張 320／480 px 淺色離屏控制項與 2 張真正視埠已檢視，色樣／h／進階數值欄位缺陷未重現。結果／比較 JSON 與 mm 模型輸出回讀通過。完整 Dock／深色／鍵盤／原生 picker／file dialog 待驗收，仍屬候選。[本機報告](HOME_VALIDATION_0102.md) · [彙總](evidence/home_0102/acceptance.json)。

## 歷史驗證與移轉前待辦 · 2026-10-02

- 0.10.1：13 組獨立 stock 比較＋15 類無效輸入＋17 項 UI／owned preview 操作，共 45 項；與其他模組合計 154。
- 原生比較含全遮蔭、局部遮蔭、夜間過濾、半小時／單一四分之一小時、北向、真太陽時、南半球、Mesh 面朝向及 mm／m 單位。
- 44 張原生控制項離屏擷取並不等於全部 UI 通過：結果色樣、h 標籤與數值欄位窄版有缺陷。0.10.2 已用巢狀獨立欄位列修正，尚待新機重新擷取／檢視。
- 2 張真正 3D 視埠已檢視。臺北 06–18 時範例 256 格，7–13 h，平均 9.08203125 h；第二張暫時隱藏 canopy 供 QA，並非新增使用者模型可見性控制。不是正式案場或法規成果。

證據：`evidence/sunhours_0101_runtime.json`、`evidence/ui_0101/capture.json`、`evidence/ui_0101/viewport_capture.json`、`evidence/release_0102_build_manifest.json`。新機 receipts 必須新增，不覆寫歷史。

## 未完成

完整原生 int_mtx、自訂 legend/title 介面、持久方案匯入、可靠取消／百分比進度，以及完整 Dock／深色／鍵盤／原生對話框／跨機驗收。求解仍同步於 Rhino UI，先用短期間和粗網格試算。Direct Sun Hours 不需要 Radiance；日射模組仍需 Radiance。原生 ghuser 不打包也不修改。
