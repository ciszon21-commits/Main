## 2026-10-03 · 目前候選 0.10.5

0.10.5 已修正工作平台首次開啟的浮動寬度：外框至少 500、實測內容 490；只處理 Rhino 已註冊的本平台實例。手動縮窄、關閉重開及模組切換保留使用者尺寸，較寬視窗不縮小；一般 Eto 視窗不被調整。168 項原生／平台（既有 161＋寬度 7）、Core 25、MCP 工具 8、輸出回讀 3 項通過，建置 0 錯誤／0 警告。

新版 44 張 320／480 淺色離屏圖與 2 張真正視埠已檢視，requested／actual width 全數相符。0.10.4 曾把測試用一般視窗加寬，窄版擷取失效；該候選保留失敗證據、不交付。完整原生 Dock、深色、鍵盤及 picker／檔案對話框仍待驗收；使用者原本開啟的 Rhino 仍載入 0.10.3，候選載入路徑已更新，新程序可使用 0.10.5。

正式仍為 **0.9.2／9、1、112**，候選 10／1／111；先完成 V02 UI 門檻，再交付及開始 V03 Sky Mask。此次 UI 修正不增加功能覆蓋數。 [驗證範圍](HOME_VALIDATION_0105.md) · [彙總 receipt](evidence/home_0105/acceptance.json) · [雙端同步 receipt](evidence/notion_home_0105_sync_2026-10-03.json)。

以下保留前一候選與正式歷史範圍。

# 家用電腦安全移轉與開發交接

## 接收後更新 · 2026-10-03

最新接續 **0.10.3**：日照時數 API 單位重綁已修正，161 原生／平台、25 Core、8 MCP 工具、3 輸出回讀通過；44 張新淺色離屏圖及 2 張視埠已檢視。MCP 呼叫成功，完整原生 UI 受桌面擷取逾時阻礙，正式維持 0.9.2。[最新證據](HOME_VALIDATION_0103.md)。下面 0.10.2 為上一家用檢查點，ZIP 仍是 2026-10-02 歷史快照。

已從 Git 在家用專案目錄接續；0.10.2 Build／新 Rhino 載入、154 項原生／平台及輸出回讀通過，44 張新離屏 UI 已檢視。MCP 已成功連線；完整 Dock／深色／鍵盤／對話框仍待驗收，正式維持 0.9.2。[本輪驗證與待辦](HOME_VALIDATION_0102.md)。下面 2026-10-02 的表格與 ZIP 步驟保留當時交接狀態，不能當作目前驗證結果。

日期：2026-10-02。這是完整開發快照，不是自動安裝程式。所有操作限定 EnvironmentalSimulationHub，原機資料保留；沒有傳送、刪除其他專案，沒有打包父目錄 Git 歷史、帳號憑證或整套 Rhino／Ladybug 安裝環境。

## 目前交接點

| 版本 | 已證實 | 尚未完成／用途 |
| --- | --- | --- |
| 0.9.2 | 原生 108 項，30 張 UI 擷取與 SunPath 視埠；既有正式基準 | 跨機、完整 Dock／深色／鍵盤／原生對話框仍待驗收；保留作回退基準 |
| 0.10.1 | 日照時數新增 45 項，全部原生／平台合計 154 項；44 張離屏擷取、2 張真正日照視埠 | 窄版色樣與數值欄位有排版缺陷，不能視為正式 UI 驗收完成 |
| 0.10.2 | 原始碼已修正欄位共用欄寬問題；Release 建置成功，0 錯誤／0 警告 | **只有 Build；尚未註冊／載入／重跑原生與 UI 驗證**。家用電腦從這裡接續 |

原機已登錄與測試程序載入 0.10.1；已開啟程序不會因 DLL 更新而自動換版。移轉不關閉 Rhino、不修改原機註冊。ZIP 產生時的父儲存庫 HEAD 為 `1b7a9d40f1426dd80342c2c32f76b23616980155`，當時未提交程式碼完整包含於快照，另附專案範圍 patch／status。之後已建立專案獨立 Git 並提交交接內容，個人 GitHub 方式見 [GIT_HOME_WORKFLOW.md](GIT_HOME_WORKFLOW.md)。**ZIP 是較早快照，不包含父儲存庫其他專案的歷史，也不是 Git clone。**

## 包含及排除內容

- 包含原始碼、專案規則、完整文件／122 入口功能表、工具、測試、GH workflow、專案範例、歷史驗證 JSON／PNG，以及 0.9.2／0.10.1／0.10.2 必要發布檔案。
- 不包含 `bin`、`obj`、Python cache、父 `.git`／`.codex`、其他專案、帳號連線資料、外部安裝軟體。其他歷史／暫存 artifacts 保留於原機；ZIP 的 TRANSFER_MANIFEST.json 逐項記錄排除內容。
- 原生 ghuser 與 Ladybug Python／Radiance／Rhino SDK 需於家用電腦合法安裝。檔案盤點與 SHA 不代表 Python imports／求解成功。
- Rhino 活動文件、Grasshopper 記憶體、內部模組草稿、session 比較方案與 MCP slot 不會跨電腦保留；範例與已匯出 JSON／圖片在包內。不要把範例當正式案場資料。

## 接收步驟

1. 將 `EnvironmentalHub-HomeDevelopment-20261002-r2.zip`、同名 `.sha256.json` 和 `safe_transfer.py` 一起複製到家用電腦。先保留原機快照；r2 已排除求解器測試暫存，解壓工具使用 Windows 長路徑 I/O，不改系統設定。
2. 用 Python 3 驗證 ZIP。驗證工具只用標準函式庫，不需要安裝 Python 套件：

```powershell
python .\safe_transfer.py verify .\EnvironmentalHub-HomeDevelopment-20261002-r2.zip
```

3. 解壓到**全新或空的專案資料夾**，資料夾最後一層必須為 EnvironmentalSimulationHub。下列 D 槽只是範例，改為自己的目標路徑：

```powershell
python .\safe_transfer.py extract .\EnvironmentalHub-HomeDevelopment-20261002-r2.zip D:\AEC\EnvironmentalSimulationHub
```

工具先檢查 ZIP 與全部檔案 SHA，再檢查路徑，不覆蓋既有工作、不允許路徑跳出專案或經過 junction／symlink。任何錯誤都會停止；若複製遇到磁碟錯誤，保留新資料夾供檢查，換另一個全新目的地重試，不覆蓋半套內容。SHA 是完整性校驗，請使用本次提供的同一份校驗檔。

4. 在家用電腦開啟解壓後的 EnvironmentalSimulationHub，先讀 `HOME_TRANSFER.md`、`HOME_CONTINUE_PROMPT.md`、`PROJECT_STATUS.md`、`AGENTS.md`。讓 Codex 的寫入範圍限定於此資料夾。
5. 執行唯讀環境檢查，不會安裝軟體、修改註冊或啟動 Rhino：

```powershell
.\tools\Test-HomeDevelopmentEnvironment.ps1
```

若 Rhino／Ladybug 安裝位置不同，使用腳本的 `-RhinoInstallDirectory`、`-LadybugUserObjectDirectory`、`-RadianceBinDirectory` 參數。查核 `.NET 8 SDK`、Rhino 8、Grasshopper、Eto、Ladybug Python imports；日射另外需要 Radiance。來源基準 RhinoCommon 為 8.35.26251.13001，版本差異要記錄並重新驗證。

6. 家用電腦建置使用**新輸出資料夾**，不要覆寫包內版本化證據／二進位：

```powershell
dotnet build .\src\EnvironmentalHub.Plugin\EnvironmentalHub.Plugin.csproj -c Release -o .\artifacts\home-build\0.10.2
```

可用 `-p:RhinoInstallDir="D:\Apps\Rhino 8"` 覆寫 SDK 路徑。原機 bin／obj 未搬入，首次建置需正常 restore；不要複製原機 NuGet cache 或使用者設定。

7. 外掛設定使用 `%ProgramFiles%`，但仍需確認實際 Ladybug 路徑。輸出資料設於家用專案內，避免沿用原機絕對路徑。若需調整，只改 `artifacts/home-build/0.10.2/hub.config.json`，保留包內 releases 原始 manifest 對應內容。
8. 用 Rhino 自身外掛管理員載入家用 build；先使用新空白測試文件。**不要在家用電腦直接執行 `update_release_registration.ps1`**，它是原機已存在 HKLM／HKCU 註冊的升版腳本；家用第一次安裝不符合前置條件。不匯入原機 registry backup。

## 回家後第一個開發任務

先完成 0.10.2 驗收，不直接開始 Sky Mask。確認結果色樣及 h 標籤、網格／感測點偏移／CPU／專案上下限／顯示偏移，在 320／480 px 都能讀取與操作；數值欄位不被說明文字擠出。保留原生網格色階；2 mm 顯示偏移只改預覽，不改感測點、原生結果或匯出座標。暫時隱藏其他 Hub 預覽必須在退出／清除時還原，使用者幾何不受影響。

原機測試 Python 會使用 `__rhino_doc__`，不可改以 Grasshopper 的 scriptcontext.doc 代替。所有 `*_calls.json` 是歷史機器路徑／slot 的證據，不可直接重播。重新配置專案 root、元件路徑、氣象路徑及新 MCP slot；新增家用版本化腳本與 receipts，不改寫舊證據。重跑順序：既有 release 載入／60 項回歸 → SunPath 31＋文字 2＋EPW 1 → SunHours 45 → workspace 15 → 新視覺 fixture → 44 張 UI 與 2 個實際 3D 視埠。這是原機 154 項的複驗目標，**尚未在家用機通過**。

0.10.2 通過後才完成正式發布、功能目錄交付狀態、InternalPilot、新 Notion 同步；再開始 L2 V03 Sky Mask、V04 Solar Envelope。Honeybee／採光／能耗／碳排及 Eddy3D／CFD 保留後續計畫，尚未交付。

## 知識管理與回報

Notion 最後完成同步仍是 190 筆、0.9.2；本輪候選版本及交接尚未同步，目的地與固定編號見 `NOTION_KNOWLEDGE.md`。重新連線自己的帳號，不搬移 token，保留原資料庫與歷史頁。

使用者手機操作時希望少詢問、定時簡短報告。30 分鐘 heartbeat 建立操作曾被取消，**目前沒有已啟用的本專案定時排程**。回家後需依實際可用排程設定；不可把這份說明當排程已建立。開發回報需區分 Build、原生求解、UI 擷取、實際檢視、跨機驗收，不報沒有證據的總完成百分比。

在家用機通過 Build、原生測試與 UI 檢視之前，保留原機原始資料及 0.9.2 回退版本。兩台電腦同一時段只讓一台繼續寫入，以免未提交程式碼分岔。ZIP 完整性驗證只證明資料已可安全接收，不能代替家用實際執行驗收。
