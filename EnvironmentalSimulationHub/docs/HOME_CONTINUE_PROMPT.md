## 2026-10-03 · 目前候選 0.10.5

0.10.5 已修正工作平台首次開啟的浮動寬度：外框至少 500、實測內容 490；只處理 Rhino 已註冊的本平台實例。手動縮窄、關閉重開及模組切換保留使用者尺寸，較寬視窗不縮小；一般 Eto 視窗不被調整。168 項原生／平台（既有 161＋寬度 7）、Core 25、MCP 工具 8、輸出回讀 3 項通過，建置 0 錯誤／0 警告。

新版 44 張 320／480 淺色離屏圖與 2 張真正視埠已檢視，requested／actual width 全數相符。0.10.4 曾把測試用一般視窗加寬，窄版擷取失效；該候選保留失敗證據、不交付。完整原生 Dock、深色、鍵盤及 picker／檔案對話框仍待驗收；使用者原本開啟的 Rhino 仍載入 0.10.3，候選載入路徑已更新，新程序可使用 0.10.5。

正式仍為 **0.9.2／9、1、112**，候選 10／1／111；先完成 V02 UI 門檻，再交付及開始 V03 Sky Mask。此次 UI 修正不增加功能覆蓋數。 [驗證範圍](HOME_VALIDATION_0105.md) · [彙總 receipt](evidence/home_0105/acceptance.json) · [雙端同步 receipt](evidence/notion_home_0105_sync_2026-10-03.json)。

以下保留前一候選與正式歷史範圍。

# 回家後交給 Codex 的接續指令

## 目前檢查點 · 2026-10-03

目前優先讀 [HOME_VALIDATION_0103.md](HOME_VALIDATION_0103.md)，原始碼版本 **0.10.3**。已修正公開 API 單位重綁，161 原生／平台、25 Core、8 MCP 工具、3 輸出回讀通過；44 張淺色離屏 UI 與 2 張視埠已檢視。完整 Dock／深色／鍵盤／picker／file dialog 未驗收，實際桌面擷取仍逾時。舊測試程序曾結束，不重用舊 PID；新的 calls 從當次非 adopted spawn、identity 產生。候選同步地端與 Notion，正式仍為 0.9.2。工作分支沿用 `codex/home-0102-validation`；新證據在 `home_0103`，下文 0.10.2 步驟與測試保留前一檢查點範圍。

先讀 [HOME_VALIDATION_0102.md](HOME_VALIDATION_0102.md)。家用接入、0.10.2 建置／新 Rhino 載入、154 原生／平台、25 Core、8 MCP 工具回歸、3 輸出回讀已通過。44 張新的淺色離屏 UI 與 2 張視埠已檢視；完整原生 Dock、主題、鍵盤與 picker／file dialog 未完成。MCP 指令成功，實際視窗擷取逾時；待恢復桌面後接續 UI。正式 0.9.2／9、1、112 維持；持續同步地端與 Notion 候選進度，但不要先宣告正式交付或開始 Sky Mask。工作分支 `codex/home-0102-validation`；新證據在 `docs/evidence/home_0102`。以下保留原移轉指令與安全界線，已完成步驟不必重做。

請在目前 EnvironmentalSimulationHub 資料夾接續開發。先讀 AGENTS.md、docs/HOME_TRANSFER.md、docs/PROJECT_STATUS.md、docs/KNOWLEDGE_INDEX.md 與 docs/L2_VISUAL_PLAN.md。只修改本專案，不動其他專案、使用者模型、全域設定或原機 registry backup。優先使用 MCP、RhinoCommon／Grasshopper SDK、檔案工具，盡量不用 Computer Use；降低非必要詢問，操作需升權時仍用正式核准工具。

若從 ZIP 接收，先核對 TRANSFER_MANIFEST.json 與接收校驗；若由 Git 接續，先讀 docs/GIT_HOME_WORKFLOW.md，核對遠端分支、commit 與乾淨工作樹。GitHub 目的地為個人公開 ciszon21-commits/Main，專案在 Main/EnvironmentalSimulationHub/；只修改此子目錄，不動 Main 其他資料。再執行 tools/Test-HomeDevelopmentEnvironment.ps1。原機正式基準 0.9.2；0.10.1 原生 154 項通過但窄版 UI 有缺陷。來源已完成 0.10.2 欄位／圖例排版修正、建置 0 錯誤／0 警告；尚未載入或完成原生與 UI 複驗。父儲存庫歷史基準 1b7a9d4；專案已建立獨立 Git 歷史並提交新程式碼。ZIP 是較早快照，不代表最新 Git 工作樹。

先完成家用環境接入及 0.10.2 驗收：使用 artifacts/home-build 的新輸出，不覆寫歷史 releases。不要直接執行原機升版註冊腳本或 *_calls.json；為家用 root、元件、氣象、MCP slot 產生新 calls／版本化 receipts。只操作新建專用測試文件，不接管不明 Rhino session。家用環境不符合時先整理具體缺口，不自動更新／覆寫第三方套件。

重點修正已在 SunHoursPanel.cs / SunHoursPresentation.cs：說明與輸入欄位分離，圖例使用獨立色樣列，避免 DynamicLayout 共用欄寬擠出數值。驗證 320／480 px、進階設定、h 色樣數字、目標上下限、顯示偏移；保留原生色階及數據。沿法線 2 mm 顯示偏移僅修改預覽；標記的 Hub 預覽可暫時隱藏並還原，使用者幾何不能因清理／切換被隱藏或刪除。

保留原有核心與單一 HubWorkspacePanel。日照時數對應 LB-061 原生 Direct Sun Hours 1.10.0，透過原生 SunPath 重新產生來源，不接收任意外部向量替代。原機 13 組 stock 比較、15 類無效輸入、17 UI／owned-preview 操作共 45 項；既有回歸 60、SunPath 31＋2＋1、workspace 15，合計 154。家用需重新取得證據，Build 成功不能代替原生驗證，44 張舊 UI 圖片不能證明新排版已通過。

每次有實際進度，同步地端文件與既有 Notion 固定 ID，再用繁體中文回報；候選／部分驗證也須記錄，無變化不通知、不改日期。家用檢查點已更新 8 筆既有頁、新增 `VER-HOME-0102-01`，191 筆唯一編號與正式 9／1／112 已讀回，對照見 `docs/evidence/notion_home_0102_sync_2026-10-03.json`。不重建資料庫或覆寫歷史。完成完整 UI 後才更新正式交付狀態及內部試用包；候選功能 10 項，正式已交付仍 9。下一項為 L2 V03 Sky Mask；CFD 後續優先 Eddy3D，Honeybee／能耗等仍為後續整合。

用繁體中文簡短回報已完成、實際 Build/Test 結果、下一步與阻礙。使用者希望少詢問；原機 heartbeat 曾被取消；家用機目前已啟用每日 09:00 的同對話檢查，只有實際新進度才更新地端與 Notion 並通知。排程不屬移轉包內的帳號／環境內容。
