# 0.10.8｜日照圖像摘要與 WebView 探查

日期：2026-10-05（臺北）。MV-U0 **部分完成**；候選來源 0.10.8，正式基準仍 0.9.2。此次 UI／呈現工作不增加 Ladybug 功能覆蓋：正式 9／1／112，候選 10／1／111。

## 已實作

- 日照完成結果的中文離線 HTML 摘要：平均／最小／最大／格點數、八等分分布圖及完整區間表、原生模型色樣、條件與來源摘要、專案目標與既有方案比較文字。
- 主題沿用既有 Results／Environment／Compare／Run 色彩。統計柱色與模型色階分開；不推定原生色階插值。320／480 CSS 寬度可換行，數字採等寬數字特性，圖表內容亦以表格呈現。
- 日照原生面板新增「匯出圖像摘要 HTML…」。HTML 是匯出時的只讀快照，完整資料與跨程序方案恢復仍用 JSON。變更輸入／失敗保留、目標與比較文字由 C# 更新。
- 同一日照內部視圖提供可收合的 WebView 試驗區，未新增註冊 Dock。初始化採惰性載入；明確試驗開關 `ENVIRONMENTALHUB_WEBVIEW_PROBE=1` 才建立瀏覽器。**預設不初始化 WebView**；未閉合非同步失敗／Dock 門檻前不當正式功能。
- 無 CDN、外部字型、網路資源、JavaScript、訊息橋或瀏覽器儲存求解狀態。文字 HTML 編碼，CSP 阻擋網路／script／form。導覽僅允許 about:blank 與本次產生的完整 HTML data URI；新視窗取消。

Core、Adapters、Grasshopper、HubWorkspacePanel 與既有求解路徑未修改。原生 Eto／HTML 共用實際面色樣映射；沒有產生新物理數值或重繪模型色階。

## 本輪驗證與限制

| 層級 | 證據 | 結果／實際界線 |
| --- | --- | --- |
| 正常候選及隔離探查 Build | 0.10.8、WebViewProbe2；公司 SDK 10.0.400 | 最終 0 錯誤／0 警告，net8.0-windows |
| 呈現契約 | presentation_checks.json | 16 項通過：分箱總數與邊界、單一值、錯誤資料、原生色樣、安全文字、精確導覽限制、locale、原始結果不變 |
| 原有方案契約 | 本輪 dotnet console 輸出 | 42 項通過；同一 legacy_comparison.json，Core 未修改 |
| Rhino 控制項／狀態 | fixed/native_start.json | 9 項通過；空白隔離文件、歷史 fixture、組件方式載入；不是正式外掛部署或新的求解 |
| WebView 實際內容 | fixed/pump.json | WebView2 標題及中文 DOM、八列區間表成功讀回；Rhino 8.35、.NET 8.0.30 |
| 瀏覽器 HTML 排版 | browser-verified/verification.json、4 PNG | 真正 320／480 CSS viewport、淺／深色各一；DOM／PNG 寬度及無水平溢出通過，四張已檢視 |
| 完整宿主 UI | Native CapturePreviewAsync、Dock／主題／DPI／鍵盤／檔案 | **未通過／待驗收**；測試 Form 隱藏、原生擷取未完成。HTML 深色不等於 Rhino 深色驗收 |

圖像與數值來自 `samples/archive_0107/legacy_comparison.json` 的歷史原生結果：遮蔭情境 256 點、8–13 h、算術平均 9.57421875 h。所有探查頁標示歷史資料，未核對目前模型，不算本輪求解。

公司自建 Rhino 自動載入既有 0.10.1 外掛，導致普通組件名稱衝突；因此探查用獨立 AssemblyName，**未使用 PlugIn.LoadPlugIn／RegisterPanel 更新註冊**。測試比較註冊根值前後一致；不宣告整個 registry 已全面稽核。正常 0.10.8 輸出仍為 `artifacts/company-build/0.10.8/EnvironmentalHub.Plugin.rhp`，本輪未替換公司註冊。

WebView 測試 profile 位於本專案 artifacts。最終控制項已釋放，文件物件維持零個；close_slot 回報 adopted 保護，未強制關閉或繞過保護。其他使用者 Rhino 未操作；保留此關閉限制於 receipt。

## 失敗證據保留

1. MCP 沙箱 SQLite readonly；獲准重試後回應正常。
2. 驗證腳本 Registry 命名空間／Python.NET AddReference 參數錯誤、普通組件名稱衝突；修正探查方式後通過，未改產品核心。
3. 初版只允許 about:blank，擋到安裝版 Eto 的 data URI，產生空白影像；修正為精確比對當次產生的 URI。官方 develop 實作不能代替本機版本查核。
4. 第一個 Rhino 工作階段後來不存在，原因未確定；新建 PID／文件證據另存 fixed。一次準備步驟在 spawn 尚未結束前執行，失敗後等待完成再重新綁定；不重播舊身分。
5. 原生 SDK 擷取仍待回應；測試 Form 為隱藏狀態，重新顯示用錯 Show overload，未把它列為通過。
6. headless Edge 初次因沙箱 IPC 失敗；CLI 的 320 圖實際裁切較寬 viewport，這四張不列窄版驗收。改用 CDP 官方 viewport API，確認實際寬度後產生 browser-verified 四張。
7. Core console 曾漏傳 EPW／輸出參數而失敗；本輪不計 Core 25 重跑通過。前輪公司 Core 25 僅保留歷史範圍。

## 使用與下一步

候選外掛載入後，完成日照分析 → 比較／匯出 →「匯出圖像摘要 HTML…」。頁面離線可讀，留有條件、時間、單位與警告；不是可恢復完整方案的檔案。WebView 試驗開關只給隔離驗證，不能當正式部署設定。

MV-U0 下一門檻：實際已註冊工作平台的窄寬／浮動／Dock 重建、中文與焦點、DPI／原生深色、載入失敗與瀏覽器中止、文件切換及正式 HTML SaveFileDialog 成功／取消。通過才解除預設 gate。

多功能 MVP 主線仍按活動計畫推進指定時刻陰影、風花圖與常用圖表；Eddy3D 引擎／基準探查提前進行。WebView 宿主問題不阻塞其他原生視覺功能。

官方依據：[Eto Handler](https://github.com/picoe/Eto/blob/develop/src/Eto.Wpf/Forms/Controls/WebView2Handler.cs)、[WebView2 CapturePreviewAsync](https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2.capturepreviewasync)、[CDP Emulation](https://chromedevtools.github.io/devtools-protocol/tot/Emulation/)、[CDP Page](https://chromedevtools.github.io/devtools-protocol/tot/Page/)。本機 DLL／實際回應優先，develop 不等於已安裝版。

[彙總證據](evidence/webview_0108/acceptance.json) · [淺色摘要](evidence/webview_0108/summary-light.html) · [320 淺色](evidence/webview_0108/browser-verified/320-light.png) · [480 深色](evidence/webview_0108/browser-verified/480-dark.png)。
