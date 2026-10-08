# 個人 GitHub 與兩台電腦接續開發

最新公司 0.10.9 與知識交接分支為 `codex/company-0109-knowledge-20261008`，操作與安全核對見 [2026-10-08 交接](KNOWLEDGE_GIT_UPDATE_2026-10-08.md)。下方 0.10.2 與首次發布紀錄保留原日期／範圍，不代表目前版本。

2026-10-02。使用者指定個人帳號 `ciszon21-commits`、目的地 `https://github.com/ciszon21-commits/Main.git`，並明確允許 public。「私人」在此指個人帳號，不是要求 private 可見性。Main 已有其他內容，本專案放入 `EnvironmentalSimulationHub/`，使用 `codex/environmentalhub-home-development` 分支與 PR；不直接更新 main、不 force push。

## 本機已完成

專案本身已建立獨立 `.git`，不再依賴父目錄 RHINO_Deve 的 Git。只從父儲存庫 HEAD 匯入 EnvironmentalSimulationHub 的 15 個歷史提交；每個歷史樹與原專案子樹完全相同，作者／提交者／日期／訊息保留。移除頂層資料夾前綴，因此提交 SHA 會改變；對照在 `evidence/standalone_git_import_20261002.json`。原父儲存庫 HEAD 保持 `1b7a9d4`，異常的 Codex checkpoint refs 沒有匯入，也沒有修理或刪除父儲存庫。

本輪日照時數候選、0.10.2 排版修正、完整交接文件與驗證資料加入專案提交。**0.10.2 仍僅 Build 通過，不因提交 Git 而成為原生／UI 驗收完成。** 既有 0.10.1 原生 154 項與缺陷說明保留。

`.gitignore` 排除 `transfer/`、`artifacts/`、bin／obj、Python cache、暫存、憑證及本機工具設定。已校驗 ZIP 保留原狀，作為前一個時間點的備份；其 SHA 不代表本輪新增 Git 整理之後的工作樹。Git bundle 另存於 `transfer/`，包含已提交歷史，不包含排除的發布二進位或記憶體中的 Rhino／GH 狀態。

## 目的地、安全與登入

GitHub 連接器已驗證登入 `ciszon21-commits`，Main 的 public 可見性及 push 權限已查核。本機 Git 尚無登入憑證。只使用 GitHub 官方 HTTPS 目的地及正常登入授權，不讀取連接器內部憑證、不要求密碼／token 貼到對話。若需本次裝置授權，token 只保留在傳輸程序及必要子程序的記憶體／環境，不保存到磁碟、全域 Git 設定或 Windows 憑證庫；傳輸結束撤銷本次 token。拒絕登入不同帳號或對錯誤目的地推送。

發布前掃描來源 HEAD 全部可達歷史物件及 index，拒絕憑證特徵、超大 blob、排除的路徑或二進位。此掃描不能代替人工判斷；既有測試模型、圖像與文件属于使用者授權發布的專案範圍。發布分支使用 Main 的 main 與獨立專案來源 HEAD 作兩個父提交，保留來源提交歷史。新樹必須保留 Main 所有既有項目的原始雜湊，專案子樹必須與來源根樹完全相同。

本文件記錄發布方式；實際成功以 GitHub 分支／PR 及本機 `transfer/github_publish_receipt.json` 的遠端核對為準。沒有成功 receipt 時，不宣稱已上傳。

## 回家接續

發布成功而 PR 尚未合併時，指定交接分支 clone。可先只取本專案工作樹；Git 根目錄為 Main，禁止將其其他資料當作本專案修改範圍：

```powershell
git clone --filter=blob:none --sparse --branch codex/environmentalhub-home-development https://github.com/ciszon21-commits/Main.git
cd Main
git sparse-checkout set EnvironmentalSimulationHub
cd EnvironmentalSimulationHub
git status
```

先讀 `AGENTS.md`、`docs/HOME_TRANSFER.md`、`docs/HOME_CONTINUE_PROMPT.md`，執行唯讀 `tools/Test-HomeDevelopmentEnvironment.ps1`。外部 Rhino／Ladybug／Radiance 安裝、帳號憑證及發布二進位不由 Git clone 自動提供。`TRANSFER_MANIFEST.json` 僅適用 ZIP，Git 接續使用 commit、tree 與乾淨工作樹核對。

家用與公司每次開始工作先確認乾淨工作樹，再 `git pull --ff-only`。每個可核對的階段提交並 push；未完成的工作也能作清楚標示的 checkpoint，但不能宣稱驗收完成。兩台電腦同一時段由一台修改同一分支；若已有本地修改，不直接覆寫或 reset，先保存並檢查差異。

PR 合併後先確認遠端分支狀態，再安排後續分支；不要假設 main 已含交接內容。專案限定的 Git bundle 可作離線 clone／核對；R2 ZIP 提供 0.9.2／0.10.1／0.10.2 候選發布檔案。兩者是明確時間點的備份，不代表後續工作樹。保留備份直到家用機原生與 UI 驗收完成。
