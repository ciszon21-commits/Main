# 家用進度同步到公司 · 2026-10-05

公司端已取得個人 GitHub `ciszon21-commits/Main` 的 `codex/home-0102-validation` 分支，來源提交 `d6c12af56ae034bd080e8990ba7b69b5c50ba1da`。來源包含週末 8 個專案提交，候選版本由 0.10.2 進展到 **0.10.7**。正式基準仍為 **0.9.2／9 獨立、1 後端、112 待接入**。

## 同步結果與安全範圍

- 公司同步前為 `a4a576bd3eda0c5c2944aa0fb643732be8be7c49`，保留分支 `codex/company-before-home-sync-20261005`。
- 公司是獨立專案根目錄，GitHub 是 Main 下的子目錄。已用 Git subtree 抽取專案，8 個提交的作者、提交者、日期及訊息逐一一致；前綴移除使 SHA 改變。
- 同步後專案提交 `f559e59b9841e55650a00f22793774780f96ada4`，共有 25 個專案提交；檔案樹 `66aa9c105003afdf68924b8e9e50fde9afefa27e` 完全等於家用提交的 EnvironmentalSimulationHub 子樹。
- 共 2,080 個專案檔案、1,057 個變更；2,120 個可達 blob 掃描未發現高可信度憑證特徵，沒有未追蹤／忽略檔案覆寫衝突。
- 原父儲存庫 HEAD `1b7a9d4` 保持原樣；未帶入 Main 其他資料，未更新 GitHub、全域 Git 設定或登入憑證。
- Git pack 曾遭 DNS／串流逾時；缺少物件改由 GitHub 官方 raw 網域的固定提交 URL 取得，每份資料以原 Git blob SHA 核對後才寫入隔離物件庫。

同步內容包含幾何與單位重新綁定、首次浮動面板寬度修正、依文件保存模組狀態、日照比較方案 JSON 匯入與新程序恢復，以及完整家用驗證／視覺優先計畫。家用原生測試是歷史證據，不能算作公司端重跑。

## 公司端實際檢查

| 檢查 | 2026-10-05 公司結果 | 邊界 |
| --- | --- | --- |
| Plugin／Core／Adapters 建置 | 0 錯誤、0 警告；RHP 組件 0.10.7.0 | SDK 10.0.400 建置 net8.0-windows；未更新宿主或第三方依賴 |
| Core 條件檢查 | 25 項通過 | 使用原安裝的 Seattle-Tacoma EPW，非 Rhino 求解 |
| SunHours 方案契約 | 42 項通過 | 使用家用 legacy_comparison.json 固定兩方案參考檔，完整結果往返與無效輸入 |
| 歷史證據完整性 | 3 項通過 | 只核對已存資料，未重新執行物理模擬 |
| 公司 Rhino 載入／原生／完整 UI | 尚未執行 | 不執行家用 calls、註冊脚本或接管既有文件 |

新的編譯輸出在 `artifacts/company-build/0.10.7/`，與歷史 releases 分開。新方案檢查專案缺少 assets 時，已以專案內離線來源還原，不下載新 NuGet 套件。最初兩次測試呼叫分別用了未核對的 EPW 路徑及六方案檔；修正為實際安裝的 EPW 與工具要求的兩方案 fixture 後通過。這些呼叫問題不是產品求解回歸失敗。

機器可讀範圍及提交對照見 [本次 receipt](evidence/company_sync_20261005/acceptance.json)；公司同步／知識紀錄保存在 `codex/company-sync-verification-20261005`。此分支的後續提交僅新增本次紀錄，沒有再修改家用功能程式。

## 接續開發

活動排程以 [視覺優先與流程瘦身計畫](OPTIMIZED_VISUAL_PLAN_2026-10-03.md) 為準：共用設定 → 模型結果 → 天空遮蔽解讀 → A／B 比較 → 精簡匯出。先完成 V02 剩餘原生／UI 門檻；Sky Mask、Solar Envelope 依新計畫推进，CFD 後排。

公司來源尚未於 Rhino 載入。下次部署使用新建專用程序與文件、版本化 calls 及載入 receipt；重新產生公司路徑與 slot，不重播家用機器的註冊／清理呼叫。

未來同步先核對工作樹與遠端分支。公司獨立專案不能直接 pull Main 根樹；應先抽取 EnvironmentalSimulationHub，驗證祖先與子樹，再 fast-forward 或審查合併。不用 reset 覆寫，也不把 Main 根目錄複製進本專案。
