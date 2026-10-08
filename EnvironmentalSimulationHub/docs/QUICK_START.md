公司本機更新（2026-10-05）：已部署候選 **0.10.9**，可執行 `EnvironmentalHub`／`EnvironmentalSunHours`，完成日照後使用「匯出圖像摘要 HTML…」。[新版操作與回復](COMPANY_DEPLOYMENT_0109.md)。下方保留 0.9.2 跨機內部試用包說明，未將本機載入視為同仁跨機驗收。

# 同仁快速上手｜0.9.2 內部試用

本版適合小範圍內部試用。操作不需要理解 Grasshopper 電池；首次安裝與依賴設定由負責同仁協助。另一台同仁電腦的安裝、首次求解與無協助操作尚未驗收，不能視為公司正式部署版。

## 安裝前準備

- Windows、Rhino 8／Grasshopper，Rhino 使用 .NET 8。已實測基準為 Rhino 8.35.26251.13001；其他組合須另驗。
- 安裝 Ladybug Tools 與 Radiance，並完成其 Rhino／Grasshopper Python 環境設定。包內不包含這些外部依賴，也不需要安裝 Rhino MCP 或 Codex 才能使用介面。
- 將 InternalPilot ZIP 完整解壓到固定的使用者目錄，例如 Documents/EnvironmentalHub/0.9.2。保留 plugin、guide、tools、examples 的相對位置。
- plugin/hub.config.json 的 UserObjectDirectory 與 RadianceBinDirectory 必須符合本機安裝。預設是 Program Files/ladybug_tools；位置不同時請負責同仁修改。
- 試用包將求解輸出設在 %LOCALAPPDATA%/EnvironmentalSimulationHub/runs，避免寫入 Program Files。這是試用包設定，正式發布的原始檔不變。

## 首次環境確認

由負責同仁在 PowerShell 執行工具，不須管理員權限或網路下載：

```powershell
& .\tools\Test-HubReadiness.ps1 -ProbeWriteAccess
```

如公司限制 PowerShell 腳本，依公司允許的方式執行或由負責同仁協助，不需變更整台電腦的執行原則。

FAIL 表示缺檔、非配置檔雜湊不符或輸出不可寫；WARN 表示配置改動或版本／原生元件與已測基準不同，需先審核。READY_FOR_NATIVE_TRIAL 表示可進行 Rhino 實測，仍須完成 PILOT_ACCEPTANCE.md；不是求解已通過。設定被修改後，配置檔雜湊將與包內 manifest 不同，請記錄差異並由負責同仁核對。

在 Rhino 的「工具 → 選項 → 外掛程式 → 安裝」選取 plugin/EnvironmentalHub.Plugin.rhp，保留 DLL 與 config 在同一資料夾。舊版已載入時，先儲存模型並重新啟動 Rhino。於命令列輸入 EnvironmentalHub，確認首頁版本 0.9.2。安裝方式參考 [Rhino 官方說明](https://docs.mcneel.com/rhino/8/help/en-us/options/plug-ins.htm)。

## 第一個可視覺化結果

1. 在新文件開啟 examples/SolarPlate_4x4m.3dm：公尺模型、4×4 m 水平分析面，僅一個 Brep。
2. 輸入 EnvironmentalHub，選「EPW 氣象」。以瀏覽按鈕選擇 Ladybug 安裝中 resources/weather 的 Seattle-Tacoma 參考 EPW，保持全年，按「匯入氣象」。參考資料僅供上手；正式案場另選適當 EPW。
3. 切到「日射分析 → 幾何／模型」，按「選取分析模型」，選示範分析面，Enter 結束選取；本例不選遮蔭。
4. 在「環境／氣象」按「套用已匯入的氣象選取」，確認全年 8,760 小時。設定網格 1.00 m、北向 0°，保持預設進階值。
5. 按「檢核輸入」，先處理錯誤；警告依實際提示確認。按「執行日射分析」。求解同步執行，Rhino 期間可能無法操作，目前沒有可靠取消或百分比。
6. 在「分析結果」讀取 kWh/m²、Min／Max／Average、網格數及圖例，再按「在 Rhino 中定位結果」。本機既有同條件基準為 16 格、平均約 1233.347 kWh/m²；新電腦須實際比對，不能僅憑這個數字宣告成功。
7. 在「比較／匯出」儲存完成結果為「基準方案」，另用 0.50 m 網格執行、儲存為「比較方案」，檢視網格差異與比較條件。網格細化不代表性能改善。
8. 匯出結果／比較 JSON。切換模組保留草稿與結果；關閉 Rhino 前須匯出，現階段方案限同一次工作階段。

## 目前可用內容與邊界

可用：地點、EPW、STAT／DDY、分析期間、日期／HOY 換算、入射日射、原生網格色樣、KPI、定位、方案比較及 JSON 匯出。功能與證據見 PROJECT_STATUS.md。

尚未可用：SunPath、Direct Sun Hours、Sky Mask、Solar Envelope、完整熱舒適、CFD、採光、能耗與碳排的 Hub 工作流程。後续优先 L2 視覺化，不需等待所有 L1 工具完成。

正式分析需確認模型／遮蔭、北向、EPW 地點及時段。評估區間是自訂專案條件，平均是格點算術平均；目前未提供法規合規判定或面積加權平均。

## 遇到問題時提供什麼

記錄版本、環境檢查 JSON、錯誤代碼與完整訊息、EPW 來源、網格／北向／期間，以及可重現步驟。失敗會保留前次結果，先確認畫面標示是否為舊結果。其他電腦路徑不同時由負責同仁調整；不直接沿用開發者絕對路徑。

## 先快速檢視太陽路徑

輸入 EnvironmentalSunPath，在同一面板確認版本 0.9.2。設定所在地點／UTC 時區；亦可使用已完成的 EPW 地點。預設日期 6/21 12:00、半徑 20 m、北向 0°，按「檢核並建立太陽路徑」，在結果選時刻、檢視角度並定位預覽。先讀 SUNPATH_MODULE.md 的時間制、北向與支援邊界；此流程不需要 Radiance 求解，但仍需要原生 Ladybug／GH Python 環境。更換文件或單位後用「綁定目前文件／重設中心」。
