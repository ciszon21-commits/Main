# 私人 GitHub 與兩台電腦接續開發

2026-10-02。指定帳號：`ciszon21-commits`。預定專案名稱 EnvironmentalSimulationHub；實際 GitHub 目的地與私人可見性需由遠端查核後才推送。帳號早先提到的 `ciszon` 已更正，不作發布目的地。

## 本機已完成

專案本身已建立獨立 `.git`，不再依賴父目錄 RHINO_Deve 的 Git。只從父儲存庫 HEAD 匯入 EnvironmentalSimulationHub 的 15 個歷史提交；每個歷史樹與原專案子樹完全相同，作者／提交者／日期／訊息保留。移除頂層資料夾前綴，因此提交 SHA 會改變；對照在 `evidence/standalone_git_import_20261002.json`。原父儲存庫 HEAD 保持 `1b7a9d4`，異常的 Codex checkpoint refs 沒有匯入，也沒有修理或刪除父儲存庫。

本輪日照時數候選、0.10.2 排版修正、完整交接文件與驗證資料加入專案提交。**0.10.2 仍僅 Build 通過，不因提交 Git 而成為原生／UI 驗收完成。** 既有 0.10.1 原生 154 項與缺陷說明保留。

`.gitignore` 排除 `transfer/`、`artifacts/`、bin／obj、Python cache、暫存、憑證及本機工具設定。已校驗 ZIP 保留原狀，作為前一個時間點的備份；其 SHA 不代表本輪新增 Git 整理之後的工作樹。Git bundle 另存於 `transfer/`，包含已提交歷史，不包含排除的發布二進位或記憶體中的 Rhino／GH 狀態。

## 目的地與登入

GitHub 連接器已驗證登入 `ciszon21-commits`，目前列出的 Main、REVIT_MCP_study、Rhino_Study 都是 public，沒有上傳本專案。連接器提供 Git 物件／檔案操作，但沒有建立儲存庫工具。本機 Git Credential Manager 沒有已登入帳號；內建瀏覽器目前停在 GitHub 登入入口。因此建立新 Private 儲存庫仍需由已登入的使用者操作，或提供已存在且可存取的私人目的地。不要把公開 repo 當臨時傳輸入口，也不要貼密碼／token 到對話。

建立 `EnvironmentalSimulationHub` 時選 **Private**，先不初始化 README／license／gitignore；再提供完整 repo URL。只有完成遠端權限及 private 查核、提交／檔案掃描後才傳送。本機整理完成不代表 GitHub 已上傳。

## 回家接續

私人目的地建立並上傳後，使用自己的 GitHub 登入在家用電腦 clone。地址以下以預定名稱為例，實際使用經查核的遠端：

```powershell
git clone https://github.com/ciszon21-commits/EnvironmentalSimulationHub.git
cd EnvironmentalSimulationHub
git status
```

先讀 `AGENTS.md`、`docs/HOME_TRANSFER.md`、`docs/HOME_CONTINUE_PROMPT.md`，執行唯讀 `tools/Test-HomeDevelopmentEnvironment.ps1`。外部 Rhino／Ladybug／Radiance 安裝、帳號憑證和发布二進位不由 Git clone 自動提供。

家用與公司每次開始工作先確認乾淨工作樹，再 `git pull --ff-only`。每個可核對的階段提交並 push；未完成的工作也能作清楚標示的 checkpoint，但不能宣稱驗收完成。兩台電腦同一時段由一台修改同一分支；若已有本地修改，不直接覆寫或 reset，先保存並檢查差異。

若遠端尚未就緒，專案限定的 Git bundle 可作離線 clone／核對；另外的 ZIP 提供 0.9.2／0.10.1／0.10.2 候選發布檔案。保留兩者直到家用機原生與 UI 驗收完成。
