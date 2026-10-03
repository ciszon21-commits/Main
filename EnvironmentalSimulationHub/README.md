## 2026-10-03 · 0.10.5 原生操作補驗與 MCP 修正

外掛維持 0.10.5。本輪修正 MCP 探測器漏判「正常輸出後附加執行例外」，**12 項工具測試通過**；另在新隔離空白 Rhino 通過 **7 項額外原生操作**（停靠保護 3、基本鍵盤 3、Eto 存檔取消 1）。原驗證程序已有 608 物件，未在其中操作。完整 168 項求解／平台回歸與 44 張圖屬前輪歷史，本輪未重跑。

唯讀檢查 161 份有回應的 transport，列出 21 個含錯誤的呼叫（包含已知失敗重試），歷史 receipts 不改寫。完整停靠版面、深色、全鍵盤／成功 picker 與正式匯出對話框仍待驗收，桌面影像擷取逾時；V02 未正式交付，V03 未啟動。正式 **0.9.2／9、1、112**，候選 10／1／111。

[本輪範圍](docs/HOME_UI_VALIDATION_0105.md) · [補驗證據](docs/evidence/native_ui_0105/acceptance.json)；以下保留前輪版本化範圍。

## 2026-10-03 · 目前候選 0.10.5

0.10.5 已修正工作平台首次開啟的浮動寬度：外框至少 500、實測內容 490；只處理 Rhino 已註冊的本平台實例。手動縮窄、關閉重開及模組切換保留使用者尺寸，較寬視窗不縮小；一般 Eto 視窗不被調整。168 項原生／平台（既有 161＋寬度 7）、Core 25、MCP 工具 8、輸出回讀 3 項通過，建置 0 錯誤／0 警告。

新版 44 張 320／480 淺色離屏圖與 2 張真正視埠已檢視，requested／actual width 全數相符。0.10.4 曾把測試用一般視窗加寬，窄版擷取失效；該候選保留失敗證據、不交付。完整原生 Dock、深色、鍵盤及 picker／檔案對話框仍待驗收；使用者原本開啟的 Rhino 仍載入 0.10.3，候選載入路徑已更新，新程序可使用 0.10.5。

正式仍為 **0.9.2／9、1、112**，候選 10／1／111；先完成 V02 UI 門檻，再交付及開始 V03 Sky Mask。此次 UI 修正不增加功能覆蓋數。 [驗證範圍](docs/HOME_VALIDATION_0105.md) · [彙總 receipt](docs/evidence/home_0105/acceptance.json) · [雙端同步 receipt](docs/evidence/notion_home_0105_sync_2026-10-03.json)。

以下保留前一候選與正式歷史範圍。

# 目前候選 0.10.3 · 2026-10-03

已修正日照時數 API 的模型單位重綁；建置 0 錯誤／0 警告，新專用 Rhino 載入 0.10.3.0，161 項原生／平台、25 Core、8 MCP 工具與 3 輸出回讀通過。44 張淺色離屏 UI、2 張真正視埠已檢視；完整 Dock／深色／鍵盤／原生對話框待驗收，桌面擷取仍逾時。正式基準 0.9.2／9、1、112。[本輪驗證](docs/HOME_VALIDATION_0103.md) · [雙端知識同步狀態](docs/evidence/notion_home_0103_sync_2026-10-03.json)。

## 歷史家用檢查點 0.10.2 · 2026-10-03

0.10.2 已在家用機完成建置及新 Rhino 載入，154 項原生／平台、25 項 Core、8 項 MCP 錯誤處理及 3 項輸出回讀通過。44 張 320／480 px 淺色控制項影像與 2 張真正視埠已檢視；完整 Dock／深色／鍵盤／對話框仍待驗收。MCP 唯讀請求成功，視窗擷取服務仍逾時。正式基準維持 0.9.2／9 獨立、1 後端、112 待接入。[本機驗收與下一步](docs/HOME_VALIDATION_0102.md)。

## 歷史交接 · 2026-10-02

先讀 [安全移轉](docs/HOME_TRANSFER.md) 與 [接續指令](docs/HOME_CONTINUE_PROMPT.md)。來源目前為 0.10.2，僅建置通過；0.10.1 原生 154 項通過但 UI 未完成驗收。正式基準仍是下文 0.9.2。快照包含未提交新程式碼，沒有父儲存庫其他專案的 Git 歷史、憑證或 Rhino 安裝環境。

# Environmental Simulation Hub

Knowledge entry: [current status](docs/PROJECT_STATUS.md), [knowledge index](docs/KNOWLEDGE_INDEX.md), [stage plan](docs/ROADMAP.md), and [Ladybug batches](docs/LADYBUG_DEVELOPMENT_PLAN.md). The user-designated [Notion database](https://app.notion.com/p/27b5fd42055b410ea1d58fbbf60fd31e) contains 190 classified records; see [destination and maintenance](docs/NOTION_KNOWLEDGE.md). The current 0.9.2 release adds the first geometric SunPath workflow; coverage is 9 standalone / 1 backend / 112 pending.

Original Ladybug radiation and EPW weather backends, typed C# adapters and Rhino dockable panels — **RUNTIME VERIFIED** on Rhino 8.35 / .NET 8.0.30.

Run `EnvironmentalHub` for the building-performance overview or `EnvironmentalRadiation` for the six-stage analysis workflow. Select geometry/context, choose EPW and time, set basic or advanced parameters, validate and run. Results include native mesh-color samples, numerical KPIs, project target evaluation and viewport focus. Compare named session scenarios and export full provenance. Reset removes only panel-owned previews and preserves saved scenarios. See [platform UI and limits](docs/PLATFORM_UI.md) and [UI audit](docs/UI_AUDIT_2026-10-01.md).

The local plugin is `artifacts/releases/0.9.2/EnvironmentalHub.Plugin.rhp`. Build and loading instructions are in `docs/BUILD_AND_RUN.md`. Release 0.9.2 has been registered and loaded in a fresh Rhino process. Run `EnvironmentalWeather` for climate fields and hourly selection; `EnvironmentalRadiation` opens radiation. Execution is synchronous. Existing Rhino processes retain their loaded version until restarted.

V1 retains the current Rhino/Eto framework. Topic colors and native vector icons distinguish model, environment, settings, run, results and comparison without changing simulation palettes. Shared titles, spacing and ruled sections follow [UI standards](docs/UI_UX_STANDARD.md). Larger visual interaction is planned for V2 after the major function milestones are accepted; see [release strategy](docs/ROADMAP.md). SunPath joins the same cached workspace; its optional weather coloring, conditional filtering, DST, legend and visualization-set UI remain pending.

Open `workflows/radiation/radiation_main.gh` in the inspected Rhino installation to see the original Ladybug workflow. The saved input is a 4m × 4m Brep snapshot from a Rhino object. The fixture uses bundled Seattle-Tacoma EPW data, annual cumulative radiation, north 0°, and 1m grid. It is not a Taipei project result.

The active Rhino session displays the result mesh and Ladybug legend. `samples/radiation_smoke/radiation_smoke.3dm` contains the input Brep and colored result mesh; its legend remains in the GH definition, not baked into that sample model. `runtime_result.json` stores all 16 physical values and their provenance. `rhino_preview.png` records the display.

Read `docs/ENVIRONMENT_AUDIT.md`, `docs/COMPONENT_INVENTORY.md`, and `docs/ROADMAP.md` before extending the workflow. Raw MCP evidence is retained in `docs/evidence/`.

The tools directory contains audit/fixture tooling; compiled code lives in `src/`. Core contracts have no Rhino/GH dependencies. The adapter constructs an isolated definition from installed original user objects, never modifies the smoke canvas, and verifies the actual gendaymtx executable used by Ladybug. Existing solver source files remain unchanged. New SunPath contracts and an adapter are additive, so this is not a whole-DLL identity claim against 0.8.7. The older `docs/evidence/binary_086_logic.json` applies only to its original 0.8.6 scope. This release provides Traditional Chinese (zh-TW) navigation, controls, field names, diagnostics and result summaries. Native values, technical identifiers, command names and JSON contracts retain their original forms. Reliable cancellation/percentage progress and wind workflows remain future milestones.

Paths passed in `tools/*_calls.json` are captured environment-specific replay inputs. Configure them for another machine. Executable scripts receive their project/weather/component roots from the caller; no source copy of the Ladybug solver is maintained here.

To regenerate the audit from captured evidence, run `python tools/write_audit.py` in the verified environment. The original LBT components remain separately installed dependencies; their license notices and terms apply to company deployment.

Full original Ladybug scope: [122-entry feature table](docs/LADYBUG_FEATURE_TABLE.md) and searchable [HTML catalog](docs/LADYBUG_FEATURE_TABLE.html). Nine standalone functions are integrated and tested, one function is used by the radiation backend, and 112 entries await integration. See [current status and verification scope](docs/PROJECT_STATUS.md) and [weather semantics](docs/WEATHER_MODULE.md).

Run EnvironmentalLocation for the original Ladybug location tool; half/quarter-hour UTC display is preserved in both location and weather panels. See docs/LOCATION_MODULE.md.

STAT / DDY support introduced in 0.6.0 provides EnvironmentalClimate for original STAT / DDY imports. Three-city full native JSON and design-day IDF comparisons plus invalid-input and Panel checks passed; see docs/CLIMATE_FILE_MODULE.md (CLIMATE_FILE_MODULE.md from this docs directory) and release_060_loaded.json.

0.9.2 unified entry: EnvironmentalHub opens the overview; EnvironmentalRadiation opens radiation directly. EnvironmentalTime provides original period and date/HOY tools. All panels share navigation and styling; source/result state remains module-specific. See TIME_AND_HUB_MODULE.md in docs for native runtime and UI capture scope.

新版介面整合：EnvironmentalHub 與五個模組指令均開啟同一 Rhino 工作平台，以頂部中文選單切換內部模組，保留草稿與完成結果。已載入舊版的 Rhino 需儲存工作後重新啟動以載入 0.9.2。

0.9.2 adds EnvironmentalSunPath within the same workspace: original geometric SunPath, positions/vectors, four projections and safe owned preview. See docs/SUNPATH_MODULE.md for supported/deferred options and 108 native checks. Coverage: 9 standalone, 1 backend, 112 pending.
