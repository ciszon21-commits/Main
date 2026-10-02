# 太陽路徑｜0.9.2

LB-057 SunPath 的第一批幾何功能已接入單一 HubWorkspacePanel。輸入 EnvironmentalSunPath 或在首頁選「開啟太陽路徑」。保留原生 Ladybug 元件，不自行重算太陽位置。

## 操作與結果

1. 確認 Rhino 模型單位；中心預設為原點，可在 Rhino 指定位置。更換文件或單位後，使用「綁定目前文件／重設中心」，中心會回到原點，前次結果仍保留。
2. 使用完成的地點或 EPW 地點，亦可手動輸入經緯度。預設臺北 25.033° N、121.5654° E、UTC+8、海拔 0 m；正式案場請核對。
3. 指定非閏年日期／時分，預設 6 月 21 日 12:00；或明確傳入時間模組完成的分析期間／日期。接受分鐘精度的次小時 HOY，不能把閏年日期混入。日期欄位改動會切回單一時刻。
4. 北向預設 0°，從 +Y 逆時針旋轉；90° = −X。半徑預設 20 m，原生 scale = 半徑 / 100，原生元件依模型單位換算。
5. 按「檢核並建立太陽路徑」。結果列出選取數、太陽位置數、地平線以下數、高度角範圍；選時刻檢視原生高度角、方位角與向地面的日照向量。
6. 定位整體預覽或選取太陽，匯出完整 JSON；清除只移除本模組建立的預覽，完成結果仍可檢視／匯出。替換預覽及失敗會保留使用者模型。

進階設定包含 UTC 時差、海拔、模型單位中心 XYZ、真太陽時，以及原生 3D／Orthographic／Stereographic／Equidistant／Equisolid 投影。全年 analemma／每月日弧為預設，亦可只顯示選取日期日弧。真太陽時不等同鐘錶時間；2D 投影只改變圖形，向量與日照方向線保持物理 3D。

圖形分類：日弧為低飽和赭色、analemma 為灰藍、羅盤與原生文字為灰、太陽點為橙色。日照方向線由物理太陽方向指向中心。這些是幾何識別色，沒有氣象數值色階或 Pass／Fail。尚未計算遮蔭、直射日照時數、照度或輻射能量。

## 支援邊界

本批完成地點、HOY、角度／向量、曲線、原生文字、北向、尺度、中心、日弧模式與四種投影。未接入 data_ 氣象著色、statement_ 條件篩選、legend_par_、dl_saving_ 夏令時間、向量式 north_ 或 vis_set 介面。原生全量參數仍留在目錄，不能將「已接入並實測」解讀為所有選項已完成。下一批 Direct Sun Hours 要另驗證向量取樣與時間步長契約。

求解同步在 Rhino UI 執行緒執行，沒有百分比或取消。大量分鐘取樣與密集預覽尚未完成效能驗收。工作階段結果未提供匯入／持久化方案比較，請先匯出再關閉 Rhino。

## 驗收證據

- sunpath_092_runtime.json：31 項。12 組獨立原生 GH 定義比對位置／向量、曲線取樣點及文字；臺北日夜、北向、太陽時、日弧、次小時、南半球、極夜、平移與四投影。毫米尺度、9 組非法輸入、失敗／停用 GH 保留、owned preview 替換／清除、定位、單位變動拒絕、完成地點／期間／日期及真實按鈕、GH 文件清理。
- sunpath_092_transfer.json：1 項，完成 EPW 地點傳入保留前次完成結果。
- release_092_loaded.json、platform_092_runtime.json：既有原生流程 60 項；日射基準平均 1233.3471168086037 kWh/m²。
- workspace_092_runtime.json：14 項；7 個指令／路由、6 個首頁入口、草稿／完成結果／比較保留及關閉重開。原生數值／操作共 108 項。
- ui_092/capture.json：30 張目前淺色主題、320／480 px 的正式控制項離屏影像；新增 SunPath 輸入、進階、結果、失敗與既有模組。完整 Dock、深色切換、鍵盤、原生對話框與跨機同仁試用仍待驗收。

參考：[Ladybug 官方 SunPath 說明](https://docs.ladybug.tools/ladybug-primer/components/2_visualizedata/sunpath)。本機安裝的 ghuser SHA 才是這次運算基準；文件網頁版本與本機可能不同。原生程式碼在 sunpath_native_audit.json 保留稽核副本，未修改上游原件。

0.9.2 修正視埠文字縮放：17 個原生文字各自明確覆寫 DimensionScale=1，保留文件樣式與 ModelSpaceAnnotationScalingEnabled。另有 sunpath_092_text.json 兩項 100 倍父樣式驗證及真正視埠影像 ui_092/sunpath_viewport.png。0.9.0 的實際文字顯示問題保留為歷史；0.9.1 測試候選未通過。技術依據為 [Rhino AnnotationBase.SetOverrideDimStyle 官方文件](https://mcneel.github.io/rhinocommon-api-docs/api/RhinoCommon/html/M_Rhino_Geometry_AnnotationBase_SetOverrideDimStyle.htm)。
