## 2026-10-03 · 0.10.6 停靠資料保留與正式匯出

0.10.6 修正 Rhino 停靠重建外框後遺失模組資料：依文件保存八個快取內部模組，保留草稿、日照結果與情境；外框釋放前卸下模組，文件關閉／Rhino 結束才釋放。建置零錯誤／零警告；本輪 161 項既有原生回歸、33 項狀態與文件隔離、2 項正式 picker 預選、3 項正式結果匯出／比較取消檢查通過，另 Core 25、MCP 工具 12。256 點日照無遮蔭平均 13 h、遮蔭 9.57421875 h；正式結果存檔 JSON 完全一致。比較成功存檔、完整 Dock 版面／深色／全鍵盤／滑鼠後選及跨機仍待驗收。正式 0.9.2／9、1、112，候選 10／1／111；V02 未正式交付，V03 未啟動。

[本輪詳細範圍](HOME_VALIDATION_0106.md) · [本輪 receipt](evidence/session_final_0106/acceptance.json) · [視覺化精華](DEVELOPMENT_HIGHLIGHTS.md)。Notion 依使用者要求分成詳細資料、重點整理與視覺化精華；只在有實際進度時更新，沿用既有資料庫與固定 ID。前輪 0.10.5 的浮動寬度 7 項與 44 張離屏圖未重跑，以下保留歷史證據。

## 2026-10-03 · 0.10.5 原生操作補驗與 MCP 修正

外掛維持 0.10.5。本輪修正 MCP 探測器漏判「正常輸出後附加執行例外」，**12 項工具測試通過**；另在新隔離空白 Rhino 通過 **7 項額外原生操作**（停靠保護 3、基本鍵盤 3、Eto 存檔取消 1）。原驗證程序已有 608 物件，未在其中操作。完整 168 項求解／平台回歸與 44 張圖屬前輪歷史，本輪未重跑。

唯讀檢查 161 份有回應的 transport，列出 21 個含錯誤的呼叫（包含已知失敗重試），歷史 receipts 不改寫。完整停靠版面、深色、全鍵盤／成功 picker 與正式匯出對話框仍待驗收，桌面影像擷取逾時；V02 未正式交付，V03 未啟動。正式 **0.9.2／9、1、112**，候選 10／1／111。

[本輪範圍](HOME_UI_VALIDATION_0105.md) · [補驗證據](evidence/native_ui_0105/acceptance.json)；以下保留前輪版本化範圍。

## 2026-10-03 · 目前候選 0.10.5

0.10.5 已修正工作平台首次開啟的浮動寬度：外框至少 500、實測內容 490；只處理 Rhino 已註冊的本平台實例。手動縮窄、關閉重開及模組切換保留使用者尺寸，較寬視窗不縮小；一般 Eto 視窗不被調整。168 項原生／平台（既有 161＋寬度 7）、Core 25、MCP 工具 8、輸出回讀 3 項通過，建置 0 錯誤／0 警告。

新版 44 張 320／480 淺色離屏圖與 2 張真正視埠已檢視，requested／actual width 全數相符。0.10.4 曾把測試用一般視窗加寬，窄版擷取失效；該候選保留失敗證據、不交付。完整原生 Dock、深色、鍵盤及 picker／檔案對話框仍待驗收；使用者原本開啟的 Rhino 仍載入 0.10.3，候選載入路徑已更新，新程序可使用 0.10.5。

正式仍為 **0.9.2／9、1、112**，候選 10／1／111；先完成 V02 UI 門檻，再交付及開始 V03 Sky Mask。此次 UI 修正不增加功能覆蓋數。 [驗證範圍](HOME_VALIDATION_0105.md) · [彙總 receipt](evidence/home_0105/acceptance.json) · [雙端同步 receipt](evidence/notion_home_0105_sync_2026-10-03.json)。

以下保留前一候選與正式歷史範圍。

## 家用開發優先讀此

目前候選 **0.10.3** 使用 `artifacts/home-build/0.10.3`；新專用程序實際載入 0.10.3.0，建置 0 錯誤／0 警告，161 項原生／平台與 Core／工具／輸出 25／8／3 項通過。SDK 載入後本機 HKCU FileName 回讀為候選路徑，未執行正式升版腳本；不等同正式部署。完整原生 UI 待驗收。新 calls 必須由當次非 adopted spawn 與 identity 產生，詳見 [0.10.3 重播與範圍](HOME_VALIDATION_0103.md)。以下 0.10.2 是前一檢查點，正式發布基準仍為 0.9.2。

依 [HOME_TRANSFER.md](HOME_TRANSFER.md) 做唯讀環境檢查、建置至新 home-build 資料夾。不要直接重播原機 *_calls.json、匯入 registry backup 或執行下文的原機升版腳本。2026-10-03 家用 0.10.2 已建置、新 Rhino 載入並完成 154 項原生／平台驗證；44 張淺色離屏 UI 已檢視，完整 Dock／主題／鍵盤／對話框待驗收。[目前證據與 MCP 重播方式](HOME_VALIDATION_0102.md)。新輸出為 `artifacts/home-build/0.10.2`，尚未正式發布。

# Build and run (0.9.2)

The current formal release is `artifacts/releases/0.9.2/EnvironmentalHub.Plugin.rhp`, with sibling Core/Adapter DLLs and `hub.config.json`. The portable package is `artifacts/EnvironmentalHub-0.9.2.zip`; its release manifest records SHA-256 hashes. Ladybug and Radiance remain external installed dependencies.

```powershell
dotnet build EnvironmentalSimulationHub/src/EnvironmentalHub.Plugin/EnvironmentalHub.Plugin.csproj -c Release -m:1 -p:CleanFile=Release092.FileListAbsolute.txt -o EnvironmentalSimulationHub/artifacts/releases/0.9.2
```

Do not rebuild over loaded release files. Preserve this versioned directory while Rhino references it. Later releases should use a new version and directory. Existing Rhino processes cannot replace an already-loaded .NET plugin; load a new version in a fresh process. The command `EnvironmentalHub` opens the single registered workspace. All six module commands open their cached view inside this same panel; navigation preserves inputs, results and session scenarios. Restart Rhino to replace an already-loaded previous version. Its subtitle displays the assembly version, currently 0.9.2.

The formal update is checked using Rhino MCP and RhinoCommon: plugin GUID, loaded assembly path/version, registered PathFromId, docked panel assembly/version, and a real Ladybug radiation fixture. See `docs/evidence/release_092_loaded.json` for the current release outcome, including Weather Panel and radiation regression. Only that receipt confirms the registered and loaded version; a build or reflected test form alone does not.

Configuration expands environment variables for the Ladybug user-object and Radiance directories. OutputDirectory is relative to the plugin directory unless absolute. Keep DLLs/configuration together. No solver is installed or reimplemented by this release.

Select Breps/Meshes, optional shading context, a complete hourly non-leap EPW, grid spacing in metres and north rotation. Check inputs, then run; warnings require explicit acceptance. Results contain actual colored mesh, min/max/mean/count, full JSON and provenance. Changed inputs mark prior results. A failed solve or staged preview replacement preserves the old result. Clear preview deletes only panel-owned mesh objects and keeps saved files.

Current UI defaults: annual, 1 CPU, Tregenza sky, 0.2 ground reflectance and 0.1 m offset. Advanced controls expose the existing typed settings. Explicitly use completed weather/time selections from supporting modules; fractional periods are rejected without rounding. Execution is synchronous; reliable cancel and percentage progress remain unavailable. Production unified workspace and Eto/WPF layouts are rendered at 320/480 px offscreen; full Dock/theme/keyboard/picker/dialog acceptance remains separate. Prefer MCP/API verification over Computer Use, following the user's preference. See PLATFORM_UI.md and platform_092_runtime.json for comparison, criterion and viewport-focus semantics.

Validation receipts: adapter_runtime_validation.json (three original-workflow comparisons and five execution gates), preflight_tests.json (25 checks), panel_v6_runtime_validation.json (native Eto execution, null/invalid requests, partial-preview rollback and reset), and release_030_loaded.json (formal plugin registration/dock load).

## Updating an existing registration
The audited local installation had both HKLM and HKCU entries pointing to runtime-v3. `tools/update_release_registration.ps1` validates release hashes/version, backs up the two existing FileName values, then updates only those values and checks readback. This requires registry write permission. It does not unload an assembly in an already running Rhino. Use a fresh Rhino process for the new version. See release_registration_updated_092.json for the update receipt.

## Extended radiation reliability checks
`tools/validate_radiation_reliability.py` requires a dedicated empty Rhino document and injected hub_root. Use the bounded MCP call fixture reliability_calls.json with its explicit current test slot; do not target a user document containing geometry. Receipt: `docs/evidence/radiation_reliability_validation.json`.

Six checks passed against the unchanged formal 0.3.0 adapter: three actual runtime unit systems, independently bound stock comparison for mixed closed Brep / triangular Mesh / context, failed user-object construction without a GH document leak, and the genuine disabled-solver guard with no solver output. Units and modified state are restored, all test geometry is removed, and GH document count returns to baseline. Generated solver work folders are ignored; the actual mixed-case JSON result is retained in samples/radiation_reliability.

## Weather module (0.4.0)
Run `EnvironmentalWeather` or use the panel navigation button. Import an EPW, select annual or a contiguous zero-based HOY range (0–8759), inspect individual fields and export the full typed JSON. API requests also accept noncontiguous hours. All original Import EPW outputs are retained: location, 15 hourly data collections and three monthly ground-temperature collections for the tested file. Monthly collections remain unchanged under hourly selection. See WEATHER_MODULE.md for semantics and verification. Eight weather runtime checks passed; the formal native panel preserves results on failure, retains custom hours, switches fields and suppresses arithmetic wind-direction means. Picker/dialog, themes and visual layout acceptance remain pending.

## Location module (0.5.0)
Run EnvironmentalLocation or open it from Weather. Original Construct Location supports explicit or native-estimated time zone and JSON export. See LOCATION_MODULE.md. Formal runtime evidence: release_050_loaded.json, with 11 location cases and eight culture/UTC formatter checks. Weather half-hour display is fixed, with real native Panel verification; weather and radiation regression pass.

STAT / DDY support introduced in 0.6.0 provides EnvironmentalClimate for original STAT / DDY imports. Three-city full native JSON and design-day IDF comparisons plus invalid-input and Panel checks passed; see docs/CLIMATE_FILE_MODULE.md (CLIMATE_FILE_MODULE.md from this docs directory) and release_060_loaded.json.

0.9.2 unified entry: EnvironmentalHub opens the overview; EnvironmentalRadiation opens radiation directly. EnvironmentalTime provides original period and date/HOY tools. All panels share navigation and styling; source/result state remains module-specific. See TIME_AND_HUB_MODULE.md in docs for native runtime and UI capture scope.

## Colleague internal pilot

The separate EnvironmentalHub-0.9.2-InternalPilot.zip includes identical verified binaries, a per-user OutputDirectory configuration, Chinese guides, a 4x4 m model and Test-HubReadiness.ps1. See QUICK_START.md and PILOT_ACCEPTANCE.md. Static package checks are not native/cross-machine acceptance. The original formal release and registration remain unchanged.

0.9.2: EnvironmentalSunPath uses original geometric SunPath in the seventh cached module; no separate Dock. Use -Version 0.9.2 -PreviousVersion 0.8.7 for registry updates. See SUNPATH_MODULE.md for supported options and native evidence.
