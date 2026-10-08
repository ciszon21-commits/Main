# Environmental Simulation Hub｜Rhino 環境模擬・專案卡片

<callout icon="☀️" color="green_bg">
	**建築環境分析，集中在同一個 Rhino 工作平台。**
	以中文流程串接模型、環境條件、分析與視覺成果；保留 RhinoCommon／Grasshopper 與原生模擬邏輯。
	**2026-10-05｜公司已部署候選 0.10.9.0；專案持續開發中。**
</callout>
## 01｜目前狀態 {color="green"}
<columns>
	<column ratio="50">
		<callout icon="✅" color="green_bg">
			**已部署與可使用**
			單一中文工作平台、日照分析、A／B 方案比較及新版離線 HTML 成果頁。
			重複外掛 ID 的舊版註冊衝突已修正，舊版與回復備份保留。
		</callout>
	</column>
	<column ratio="50">
		<callout icon="🧪" color="gray_bg">
			**驗證範圍**
			本輪 **15 項原生檢查**、**42 項方案契約**、**15 項 MCP 工具檢查**通過。
			真實日照求解、結果保留及實際停靠／浮動切換已驗證；完整宿主 UI 仍待驗收。
		</callout>
	</column>
</columns>
**Ladybug 122 個入口已盤點。** 正式功能基準 **0.9.2：9 獨立／1 後端／112 待接入**；已部署候選 **0.10.9：10／1／111**。盤點、部署與正式功能驗收分別記錄，本次整理不增加功能覆蓋。
## 02｜快速入口 {color="blue"}
<columns>
	<column ratio="34">
		<callout icon="📍" color="gray_bg">
			**專案狀態**
			版本、驗證範圍與限制。
			<mention-page url="https://app.notion.com/p/3ec1956a9b0e81aca858fefd1fae1c4c"/>
		</callout>
	</column>
	<column ratio="33">
		<callout icon="📐" color="gray_bg">
			**視覺化精華**
			里程碑、流程與真實案例。
			<mention-page url="https://app.notion.com/p/3ee1956a9b0e8157996cd7e88c4d2cf3"/>
		</callout>
	</column>
	<column ratio="33">
		<callout icon="🗺️" color="gray_bg">
			**活動開發計畫**
			多功能視覺 MVP 與引擎關卡。
			<mention-page url="https://app.notion.com/p/3ee1956a9b0e811188bacca59252fbcb"/>
		</callout>
	</column>
</columns>
## 03｜同仁操作 {color="blue"}
1. 在已配置依賴的 Rhino 8，執行 `EnvironmentalHub` 開啟平台；`EnvironmentalSunHours` 可直接進入日照。
2. 依序確認 **模型 → 環境／氣象 → 模擬設定 → 驗證／執行 → 成果 → 比較／匯出**。
3. 完成日照後，按 **「匯出圖像摘要 HTML…」**，以瀏覽器查看 KPI、分布圖、條件、完整區間數據、來源與比較摘要。
新版報告頁目前透過離線 HTML 使用；內嵌 WebView 預設關閉。其他同仁電腦的安裝、首次求解與無協助操作尚未驗收。
## 04｜目前功能 {color="blue"}
<table fit-page-width="true" header-row="true">
	<tr>
		<td>主題</td>
		<td>已有功能／成果</td>
		<td>狀態</td>
	</tr>
	<tr>
		<td>模型與日射</td>
		<td>Incident Radiation：模型、遮蔭、原生日射與結果</td>
		<td>正式基準已實測</td>
	</tr>
	<tr>
		<td>氣象與地點</td>
		<td>Import EPW／STAT／DDY、Construct Location</td>
		<td>正式基準已實測</td>
	</tr>
	<tr>
		<td>時間條件</td>
		<td>Analysis Period、Calculate HOY、HOY to DateTime</td>
		<td>正式基準已實測</td>
	</tr>
	<tr>
		<td>太陽路徑</td>
		<td>SunPath 幾何第一批：位置、向量、曲線及文字</td>
		<td>正式基準已實測；全選項未完成</td>
	</tr>
	<tr>
		<td>日照與方案</td>
		<td>Direct Sun Hours、預覽、目標區間、A／B 比較、方案匯入／恢復及 HTML 摘要</td>
		<td>候選已部署並完成本輪日照回歸；完整 UI 待驗收</td>
	</tr>
	<tr>
		<td>天空矩陣</td>
		<td>Cumulative Sky Matrix 供日射後端使用</td>
		<td>後端已使用；獨立流程待完成</td>
	</tr>
</table>
完整 122 入口及逐項狀態，見下方既有開發與知識資料庫；本表為主要操作入口摘要。
## 05｜接續開發 {color="blue"}
**目前主線：日照／日射 → 指定時刻陰影 → 風花圖與常用圖表 → 熱輻射 MRT；風場另以 Eddy3D 引擎關卡驗證。**
- **日照／日射收尾**：完成宿主 UI 與同仁操作驗收，沿用統一成果閱讀層級。
- **指定時刻陰影**：優先交付模型中的時間、遮蔭與視覺判讀。
- **風花圖／常用圖表**：先做氣象風向風速及逐時／逐月視覺成果。
- **熱輻射 MRT**：保留必要單位、來源及物理意義；日射不能直接當作表面溫度或 MRT。
- **Eddy3D 提前並行關卡**：確認部署、引擎、邊界條件、收斂、基準結果與視覺輸出，通過後才接入單風向 3D 風場。氣象風統計不代表 CFD。
細部數值工具、全參數及 Solar Envelope 後排；必要輸入、科學單位、來源與原生數值驗證仍保留。V1 沿用現有框架；大型視覺互動介面屬 V2 方向。
## 06｜待驗收與部署紀錄 {color="orange"}
<callout icon="⚠️" color="orange_bg">
	**目前仍待驗收**
	完整 Dock 窄／寬版面、原生深色／DPI、完整鍵盤、HTML 檔案對話框及 WebView 非同步失敗復原。
	CFD 尚未完成求解驗證；Honeybee 採光、能耗、碳排與其他引擎屬後續整合範圍。
</callout>
<details>
<summary>展開｜本輪日照驗證、ID 衝突修正與回復</summary>
	新專用 Rhino 8.35.26251.13001／.NET 8.0.30 已讀回組件 **0.10.9.0**、載入路徑及註冊路徑一致。256 點無遮蔭平均 **13 h**；新增遮蔭 **8–13 h／平均 9.57421875 h**，與基準一致。平均為算術格點平均，不是面積加權。
	舊 HKLM／HKCU 註冊指向 0.10.1，造成新版被覆蓋及再次載入同 GUID 的錯誤；已備份並同步修正兩筆既有路徑，外掛 GUID 保持不變。有效測試物件已清空。
	MCP 曾提前斷線，但原生檢查完成，後續同程序讀回確認；320／480 原生擷取未通過宿主型別假設，因此不宣告完整原生版面驗收。
	回復前正常關閉所有 Rhino，執行本機 `tools/deploy_0109/Set-Deployment.ps1 -Rollback`。腳本只回復本外掛既有路徑至 0.10.1；回復腳本已備妥，本輪未執行回復驗收。
	本機來源：`docs/COMPANY_DEPLOYMENT_0109.md`；證據：`docs/evidence/deploy_0109/deployment_verified.json`；Git 提交 `99c3442`。本輪部署未推送 GitHub。上述路徑供追溯，並非雲端下載連結。
</details>
## 07｜詳細開發與知識資料庫 {color="gray"}
依分類查看功能目錄、階段計畫、UI／UX、架構、設計決策、驗證與發布紀錄；沿用原有資料庫及歷史證據。
<database url="https://app.notion.com/p/27b5fd42055b410ea1d58fbbf60fd31e" inline="false" data-source-url="collection://1c84aeb9-764d-4165-a569-b8628e8c2a2d">Environmental Simulation Hub｜開發與知識紀錄</database>
## 08｜首頁歷史紀錄 {color="gray"}
原 MCP AI 首頁的版本、部署、計畫、技術評估與舊導航已移入下方子頁，保留原始內容及日期。最新狀態看上方總覽；舊版工期與資料庫筆數僅供追溯。
<page url="https://app.notion.com/p/3f01956a9b0e8139adf2f98050403812">首頁歷史紀錄｜Environmental Hub</page>
