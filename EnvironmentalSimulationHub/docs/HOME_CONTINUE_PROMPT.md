# 回家後交給 Codex 的接續指令

請在目前 EnvironmentalSimulationHub 資料夾接續開發。先讀 AGENTS.md、docs/HOME_TRANSFER.md、docs/PROJECT_STATUS.md、docs/KNOWLEDGE_INDEX.md 與 docs/L2_VISUAL_PLAN.md。只修改本專案，不動其他專案、使用者模型、全域設定或原機 registry backup。優先使用 MCP、RhinoCommon／Grasshopper SDK、檔案工具，盡量不用 Computer Use；降低非必要詢問，操作需升權時仍用正式核准工具。

若從 ZIP 接收，先核對 TRANSFER_MANIFEST.json 與接收校驗；若由 Git 接續，先讀 docs/GIT_HOME_WORKFLOW.md，核對遠端分支、commit 與乾淨工作樹。GitHub 目的地為個人公開 ciszon21-commits/Main，專案在 Main/EnvironmentalSimulationHub/；只修改此子目錄，不動 Main 其他資料。再執行 tools/Test-HomeDevelopmentEnvironment.ps1。原機正式基準 0.9.2；0.10.1 原生 154 項通過但窄版 UI 有缺陷。來源已完成 0.10.2 欄位／圖例排版修正、建置 0 錯誤／0 警告；尚未載入或完成原生與 UI 複驗。父儲存庫歷史基準 1b7a9d4；專案已建立獨立 Git 歷史並提交新程式碼。ZIP 是較早快照，不代表最新 Git 工作樹。

先完成家用環境接入及 0.10.2 驗收：使用 artifacts/home-build 的新輸出，不覆寫歷史 releases。不要直接執行原機升版註冊腳本或 *_calls.json；為家用 root、元件、氣象、MCP slot 產生新 calls／版本化 receipts。只操作新建專用測試文件，不接管不明 Rhino session。家用環境不符合時先整理具體缺口，不自動更新／覆寫第三方套件。

重點修正已在 SunHoursPanel.cs / SunHoursPresentation.cs：說明與輸入欄位分離，圖例使用獨立色樣列，避免 DynamicLayout 共用欄寬擠出數值。驗證 320／480 px、進階設定、h 色樣數字、目標上下限、顯示偏移；保留原生色階及數據。沿法線 2 mm 顯示偏移僅修改預覽；標記的 Hub 預覽可暫時隱藏並還原，使用者幾何不能因清理／切換被隱藏或刪除。

保留原有核心與單一 HubWorkspacePanel。日照時數對應 LB-061 原生 Direct Sun Hours 1.10.0，透過原生 SunPath 重新產生來源，不接收任意外部向量替代。原機 13 組 stock 比較、15 類無效輸入、17 UI／owned-preview 操作共 45 項；既有回歸 60、SunPath 31＋2＋1、workspace 15，合計 154。家用需重新取得證據，Build 成功不能代替原生驗證，44 張舊 UI 圖片不能證明新排版已通過。

完成 0.10.2 原生及視覺驗收後，更新正式功能表 JSON／Markdown／HTML、目前狀態、內部試用包和既有 Notion 資料庫，保留 190 筆歷史紀錄與固定 ID，不重建資料庫。候選功能有 10 項接入，正式已交付仍 9；未完成 UI 驗收不能增加正式完成數。下一項為 L2 V03 Sky Mask；CFD 後續優先 Eddy3D，Honeybee／能耗等仍為後續整合。

用繁體中文簡短回報已完成、實際 Build/Test 結果、下一步與阻礙。使用者希望少詢問；原機 heartbeat 建立曾被取消，目前沒有已啟用定時排程。若需恢復定時回報，核對可用排程與現在的環境，不宣稱移轉包已包含帳號或排程設定。
