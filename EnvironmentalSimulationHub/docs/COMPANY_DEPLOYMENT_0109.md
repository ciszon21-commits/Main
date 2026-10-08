# 公司部署 0.10.9｜2026-10-05

公司 Rhino 已實際載入 **0.10.9.0**；兩筆既有 Environmental Hub 註冊路徑一致指向 `artifacts/releases/0.10.9/EnvironmentalHub.Plugin.rhp`。外掛 GUID 保持 `bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f`，沒有改動其他外掛或專案。

此為候選版本的公司部署與日照回歸，不等於全部功能正式驗收。正式功能基準仍是 **0.9.2／9 獨立、1 後端、112 待接入**；候選仍是 **10／1／111**。

## 使用

正常開啟 Rhino 8，執行 `EnvironmentalHub` 開啟單一中文工作平台，或 `EnvironmentalSunHours` 直接進入日照。完成分析後，按「匯出圖像摘要 HTML…」取得新版報告式成果頁，再以瀏覽器開啟。結果頁包含主 KPI、分布圖、必要條件、完整區間數據、來源、專案區間及已有比較摘要。

Eto 原生外框與求解路徑保留；內嵌 WebView 仍由試驗 gate 預設關閉。本版的新版大型視覺成果頁透過離線 HTML 使用，尚未宣告全面內嵌視覺介面交付。勿在已載入舊版的程序內再次載入不同路徑的同 GUID `.rhp`；更新後應重新開啟 Rhino。

## 已驗證

- 發布檔案四項 SHA-256 與已建置 0.10.9 一致。
- 新專用空白 Rhino 8.35.26251.13001／.NET 8.0.30，實際組件版本、載入路徑及 SDK 註冊路徑一致。
- **15 項原生檢查**：正式指令／單一工作區、摘要惰性初始化、兩次新日照求解、A/B 比較、新版 HTML 匯出 API、完整結果不變、失敗保留前次結果、模組切換、WebView gate、實際 Dock／浮動與模型 CRC 保護。
- 256 點無遮蔭平均 **13 h**；新增遮蔭 **8–13 h／平均 9.57421875 h**，與基準一致。算術格點平均不代表面積加權。
- 實際 SDK 停靠至已有容器後切回浮動，結果與兩個方案保持。
- 本輪方案契約 **42**、MCP 工具 **15** 通過。前輪 Build 0 錯誤／0 警告、18 呈現契約及 10 組 320–1280 CSS 淺深色檢查保留原範圍，非本輪重跑。
- 清理只處理本輪模型 GUID 及本模組擁有標記的預覽；有效物件為零、測試面板已關閉。Rhino 物件表的刪除歷史保留。

## 問題與修正

初次只更新 HKCU 路徑，另一筆 HKLM 仍指向 0.10.1；新程序採用舊版，驗證腳本再呼叫檔案載入，觸發使用者截圖的 **ID already in use**。已備份並更新兩筆既有 `PlugIn/FileName`，不新增 ID；驗證改為先 Find，必要時依既有 GUID 載入。

第二次 MCP 連線回傳 `rhino_closed`，但程序仍在，原生腳本繼續完成並保存 15 項檢查。保留該 transport 失敗紀錄；後續獨立讀回同一 PID 的 0.10.9 路徑與版本確認。沒有以 transport 回應冒充成功。

原生 320／480 擷取未通過：浮動面板 ParentWindow 不符合 `Eto.Forms.Form` 假設，未調整主視窗，也未取得合格圖片。清理初稿誤以 `Objects.Count` 作有效物件數；改用 SDK 的有效物件枚舉後確認零物件。兩次失敗均有原始紀錄，產品核心未因測試而改動。

完整 Dock 窄／寬版面、原生深色／DPI、完整鍵盤、HTML 檔案對話框與 WebView 非同步失敗復原仍待驗收。沒有本輪 CFD／日射／所有模組新求解或跨機同仁無協助操作驗收。

## 備份與回復

本機使用 `tools/deploy_0109/Set-Deployment.ps1`；實際修正由 `Repair-Registration.ps1` 執行。兩者拒絕在 Rhino 執行中更動註冊，拒絕覆寫不符預期的路徑或既有第一份備份。

回復前正常關閉所有 Rhino，再執行 `tools/deploy_0109/Set-Deployment.ps1 -Rollback`。腳本核對兩筆目前路徑與舊版 SHA，僅回復本外掛至 0.10.1；不刪除候選、模型或其他註冊。本輪未執行回復，不將腳本存在宣稱為實際回復驗收。

原始 HKCU 單筆嘗試 `registration_before/after.json` 保留為歷史；有效備份為 `registration_pair_before.json`，修正讀回為 `registration_repaired.json`，最終證據為 `deployment_verified.json`。新版二進位目前仍為 0.10.9，部署工具修正不改變組件版本。

[原生檢查](evidence/deploy_0109/native_checks.json) · [真實新求解摘要](evidence/deploy_0109/current-summary.html) · [清理證據](evidence/deploy_0109/cleanup.json) · [前輪視覺範圍](VISUAL_RESULT_PAGE_0109.md)。部署包在本機專案目錄；本輪沒有推送 GitHub。

下一步依多功能視覺 MVP 推進指定時刻陰影、風花圖與常用圖表；Eddy3D 先完成引擎及基準關卡。完整宿主 UI 門檻持續追蹤，尚未解除 WebView gate。
