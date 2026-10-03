# Development log

## 2026-10-03｜0.10.3 API 單位重綁修正與候選回歸

- 本機實作檢查點 `4276444` 已提交，其他 Main 頂層項目 hash 保持相同；GitHub push 因本機 Git 無登入憑證未完成，未建立 PR，不能視為遠端備份。Notion 已同步並讀回 192 筆／192 唯一編號、正式 9／1／112。[Git 接續狀態](evidence/home_0103/git_checkpoint.json)。

- 真實重現 0.10.2 公開 SetGeometry 被舊單位綁定檢查阻擋；改為明確重選建立新文件／單位綁定，先準備完整陣列再更新狀態。舊求解保護與前次結果保留不變；Core／Adapter 求解源碼未改。
- Build 0 錯誤／0 警告，新非 adopted 專用 Rhino PID 30168 載入 0.10.3.0。既有 154＋新增 7＝161 項原生／平台通過；Core 25、MCP 工具 8、輸出回讀 3 項通過。44 張淺色離屏圖及 2 張真正視埠已檢視；122 Ladybug 入口 SHA 相符。
- 保留登錄路徑失配、測試程序中斷及啟動逾時的失敗 receipts，重建並核對身分後才重跑成功。SDK 載入後 HKCU FileName 回讀為 home-build 0.10.3，未執行正式升版腳本；正式發布仍為 0.9.2。
- 桌面擷取刷新重試仍逾時，完整 Dock／深色／鍵盤／原生對話框待驗收，V03 未啟動。更新本機知識與目錄三格式，Notion 本輪實際讀回見 [同步 receipt](evidence/notion_home_0103_sync_2026-10-03.json)；歷史 receipts 不改寫。[本輪驗證](HOME_VALIDATION_0103.md)。

## 2026-10-02｜L2 視覺化優先與同仁試用準備

- 使用者新方向：優先 SunPath／Direct Sun Hours／Sky Mask／Solar Envelope 與必要結果資訊，L1 依賴按需補齊；CFD 後續以 Eddy3D 為評估候選。
- 新增四來源索引，GitHub connector 核對三個官方 repo metadata；未更新本機原生套件。
- 製作 0.8.7 InternalPilot 包：正式二進位完全相同、使用者輸出目錄設定、中文上手與試用門檻、4×4 m 示範模型及環境檢查工具。
- 示範模型經 Rhino File3dm 寫入／讀回確認：1 Brep、16 m²、Metres，不改動測試文件。32 靜態檢查與輸出寫入探測通過；配置變更列 WARN、二進位被改動列 BLOCKED。
- 新電腦與無協助同仁上手仍待驗收。正式功能數及既有版本驗收不變；沒有新增 L2 已完成數，也未重新執行全部既有求解回歸。


## 2026-10-02｜0.8.7 單一工作平台

- UI audit：六個獨立 RegisterPanel 與 OpenPanel 路由造成面板分散。
- 改為一個 HubWorkspacePanel，沿用原首頁 Dock GUID；六個指令與首頁工具改為快取內部模組切換，移除重複導覽，資料轉移改讀平台中的已完成結果。
- 保留 Core／Adapter。0 錯誤／警告建置；正式註冊備份與讀回、新專用 Rhino 程序載入；60 既有原生檢查及 13 平台檢查通過，22 張 320／480 當前淺色原生離屏圖檢視。
- 功能維持 8 獨立、1 後端、113 待接入；進度、完整 Ladybug 對應與下一批順序已更新。版本證據：workspace_087_acceptance.json。


## 2026-10-02 — 0.8.6 Traditional Chinese interface

- KNOWLEDGE: Reused the existing Notion database; updated 7 current records and 9 verified function/backend version entries, added immutable VER-086-01 and REL-086, and preserved 0.8.5 records. Full readback confirms 178 unique records / 11 categories / 9 views and unchanged 8 / 1 / 113 function states. [Sync receipt](evidence/notion_chinese_086_sync_2026-10-02.json).
- DONE: All six existing Rhino/Eto panels use Traditional Chinese navigation, section names, buttons, hints, stale/current states, validation, statistics, criterion and comparison. HubText translates installed EPW/STAT/DDY output labels and common diagnostics, preserving codes and unfamiliar native messages. Command names, raw values and JSON contracts remain compatible.
- RELEASE: Versioned 0.8.6 package/manifest; backed up both existing registrations, updated/read back formal paths, and loaded the actual 0.8.6 assembly in the fresh owned aardvark slot. Prior loaded releases were preserved.
- TEST RESULT: Build 0 warnings/errors. 60 native cases (21 platform, 17 time, 11 location, 11 climate), weather selector/missing/monthly/custom-hour/failure checks, 5 overview buttons and 6 navigation routes pass. Radiation baseline remains 1233.3471168086037 kWh/m². All 22 native 320/480 px current-light-theme images inspected. Core/Adapter source and normalized compiled metadata/method bodies match 0.8.5; whole-file hashes differ.
- ROOT CAUSE/FIX: The first test replay still expected two English climate summaries; updated the new version's acceptance expectations and reran the full suite successfully. Earlier version scripts/receipts were preserved. Sandbox router initialization failed; authorized bounded MCP execution worked. No Computer Use.
- LIMITS/NEXT: Chinese UI adds no Ladybug functions: 8 independent / 1 backend / 113 pending. Native values, imported names and user scenario text remain original. Full Dock/dark-theme/keyboard/picker/dialog acceptance, reliable cancel/progress and B01 Deconstruct Location remain open.
- EVIDENCE: [Chinese release acceptance](evidence/chinese_086_acceptance.json), [actual load](evidence/release_086_loaded.json), [native UI](evidence/chinese_086_ui.json), [captures](evidence/ui_086/capture.json).

## 2026-10-02 — Stage plan and Notion knowledge database

- DONE: Consolidated current 0.8.5 status, staged roadmap, B01–B06 Ladybug batches, knowledge index and explicit decisions. Preserved the previous 0.4.0 review in history. Corrected the architecture's unsupported Eddy3D runtime claim to inventory-only scope.
- NOTION: Created the user-designated child database with 176 unique records: 122 Ladybug entries and 54 professional records, 11 categories and 9 table views. Added a parent-page portal with 10 native record mentions and preserved the database child. Fixed 47 Markdown source paths to inline code, preventing accidental domain links.
- VERIFICATION: Complete paginated database readback returned 176 unique IDs, 122 function entries with 8 tested standalone / 1 backend / 113 pending states, 54 professional records and 6 next-batch tasks. Read back portal structure, views, source-path formatting and sample native identities. Destination and record/page mapping are retained in [Notion maintenance](NOTION_KNOWLEDGE.md) and its sync receipt.
- SCOPE: Documentation and external knowledge capture only. No solver, source code, release package or registry changes; no new build or Rhino runtime claimed. Original versioned evidence remains unchanged. Cloud records contain source text and evidence metadata; local PNGs were not uploaded. No scheduled or automatic synchronization was created.
- NEXT: B01 Deconstruct Location in the existing Rhino/Eto framework; retain request → preflight → adapter → result and feature-specific native acceptance.

## 2026-10-01 — 0.6.0 original STAT and DDY imports

- DONE: Climate-file request/result, isolated original import adapter, native climate Panel and EnvironmentalClimate command, Weather navigation, full original output selection, JSON export, explicit unavailable outputs and previous-result state. Native to_dict preserves structural values; design days additionally retain to_idf to include details/schedules beyond the JSON schema.
- TEST RESULT: Build zero warnings/errors. Six comparisons across Seattle/New Delhi/Singapore and two import formats match every native JSON object and design-day IDF. Five invalid/malformed input cases block. Panel field/format switching, collection count/units, design-day summary and failure preservation pass; GH document count restores. Both native Eto import button events send the correct STAT/DDY request. Prior Location (11), UTC-format (8), Weather interactions and real radiation baseline pass again.
- ROOT CAUSE/FIX: The initial test-only Python serializer inherited Construct Location's string input hint; removed that hint in the disposable reference graph and reran successfully. Installed originals and production solver behavior were unchanged.
- RELEASE: Formal 0.6.0 package/manifest, backed-up registry update/readback, fresh armadillo process loaded the actual formal path/version. Evidence: release_060_loaded.json. No Computer Use.
- LIMITS/NEXT: Five standalone features, one radiation backend and 116 pending entries. STAT radiation is native modeled clear sky, not measured EPW. Plotting, sizing simulation, time filtering and full visual/theme/keyboard/dialog acceptance remain open. Next: independent Analysis Period/HOY, location deconstruction and data utilities; CFD deferred.

## 2026-10-01 — 0.5.0 Construct Location and fractional UTC labels

- DONE: Original LB Construct Location adapter, typed request/result, native Location Panel and EnvironmentalLocation command, Weather navigation, explicit/native-estimated UTC offset, JSON export and previous-result state. Shared invariant formatter preserves fractional offsets in Weather and Location.
- TEST RESULT: Build zero warnings/errors. Formal fresh Rhino runtime: six original Construct → Deconstruct comparisons match name/coordinates/time zone/elevation; five invalid requests block. Eight formatting checks across en-US/fr-FR pass. A real half-hour EPW fixture verifies Weather label text. Native Location Panel failures preserve the result; GH document count restores.
- RELEASE: Manifest/package 0.5.0; both existing registrations backed up and updated, readback passed. Actual fresh aardvark process loads the formal 0.5.0 path/version. Existing Weather interactions and radiation mean 1233.3471168086037 kWh/m2 pass again. Evidence: release_050_loaded.json.
- SCOPE: Three standalone features, one verified radiation backend and 118 pending catalog entries. Deconstruct Location is a reference in tests, not a standalone Hub feature. Original longitude-estimated time zone is explicitly warned; no weather is generated by location construction.
- LIMITS/NEXT: Full UI visual/theme/keyboard/dialog QA remains pending; no Computer Use. L1 STAT/DDY and independent time utilities are next; CFD remains deferred.

## 2026-10-01 — Phase 0 and original Ladybug radiation smoke

- DONE: Read actual environment; bounded explicit-slot Rhino MCP; runtime/plugin/component/solver/asset audits; stock radiation definition; Rhino-origin input snapshot, colored mesh, legend, 3dm fixture and viewport image.
- FILES CHANGED: New EnvironmentalSimulationHub directory only; existing projects unchanged.
- GH CHANGED: Added one new radiation_main.gh using three installed original Ladybug 1.10.0 user objects. New groups and fixture inputs; no existing user definition edited.
- TEST RESULT: RUNTIME VERIFIED. 16 finite radiation values, 16 mesh faces, 64 vertex colors, 3 legend items, no component error/warning, repeat max absolute difference 0. Viewport image inspected. Three persisted-evidence tests passed; filesystem scan returned 0 with no access errors after excluding temporary QA directories.
- ROOT CAUSE/FIX: Sandbox-only router SQLite write failed; authorized router execution worked. Default slot was stale; explicitly selected aardvark. New GH document was disabled; enabled the same document before solving. Incorrect LB Sky Matrix name was corrected to the live-discovered LB Cumulative Sky Matrix.
- KNOWN ISSUES: Seattle smoke weather only; native original-component repeatability is not independent scientific validation. No production request/result adapter, preflight, panel, reset or wind execution. Binary existing workflows remain UNKNOWN. OpenFOAM UNVERIFIED. Persisted fixture input is a snapshot rather than a live selection binding.
- GIT: Parent repository initially had no commits or configured human identity. Milestone uses a command-local Codex author identity and stages only the Hub folder; global Git settings remain unchanged. Commit completion must be verified separately.
- NEXT: Implement explicit radiation contracts and adapter/preflight, then perform stock-workflow numerical comparison before Eto UI.

## 2026-10-01 — C# adapter and minimal Eto panel

- DONE: .NET 8 Core contracts/preflight; Rhino/GH adapter using installed original LB components; actual gendaymtx path verification; geometry/weather hashes, typed mesh/result JSON; dockable panel and EnvironmentalHub command; mesh ownership/reset.
- FILES CHANGED: src/Core, src/Adapters, src/Plugin, runtime validation tooling/tests, configuration, documentation and evidence. Original radiation_main.gh/checkpoint unchanged.
- GH CHANGED: Adapter creates/disposes isolated definitions; no saved/active smoke workflow changes.
- TEST RESULT: Final RHP build 0 warnings/0 errors. 25 Core checks and 3 saved-evidence tests pass. Three stock/adapter comparisons (annual, shaded+rotated+24-hour, scaled geometry) have maximum per-value difference 0. Five invalid/warning execution cases block before output directory creation. Panel loaded/visible, request→adapter→mesh path, repeat and reset passed.
- ROOT CAUSE/FIX: Windows Forms implicit namespace imports conflicted with Eto; removed generated imports and qualified Font/Environment. Multi-project parallel MSBuild target evaluation failed without diagnostics; single-node build exposed compilation diagnostics and then passed. Already loaded DLLs are locked; separate development assembly names/output preserved the live Rhino session. No solver fallback.
- KNOWN ISSUES: Synchronous UI-thread execution; no progress/cancel. Picker/dialog clicks and visual panel QA pending. A later picker document-change guard fix is build verified in artifacts/next; the currently loaded runtime-v3 assembly remains locked and the guard needs a fresh Rhino session for runtime QA. Full failure injection/complex-geometry/runtime unit-change validation pending. Seattle fixtures only; wind and company deployment pending.
- NEXT: Strengthen execution failure handling, progress/cancel and reproducible project geometry fixtures, then inspect a real Eddy3D workflow.

## 2026-10-01 — 0.3.0 release and UI reliability

- DONE: Persisted UI/UX standard and MCP-first preference. Five-step Eto flow, displayed version, bounded viewport and numeric widths, prior-result state, JSON export, readable diagnostics, staged preview replacement and cleanup of GH construction failures.
- TEST RESULT: Release build 0 warnings / 0 errors. Native Eto runtime-v6: real Ladybug mean 1233.3471168086037 kWh/m2, repeat delta 0, invalid/null request preservation, partial replacement failure rollback and owned reset passed. API width checks at 320/480 passed; these do not replace visual QA.
- RELEASE: Formal artifacts/releases/0.3.0 package plus SHA-256 manifest. Updated the existing HKLM/HKCU plugin FileName values only, backed up their previous paths and verified readback.
- ROOT CAUSE/FIX: Rhino auto-loaded runtime-v3 / 0.2.0, so an attempted second plugin with the same GUID was rejected. Versioned release registration avoids that conflict in fresh sessions. Already running Rhino processes retain loaded assemblies until restart.
- KNOWN ISSUES: Full Dock visual/theme/keyboard/dialog QA pending; synchronous execution and no cancellation. Wind has not started. Formal release registration, loaded assembly, 0.3.0 subtitle, visible Dock Panel and true solve are verified in release_030_loaded.json. Old running processes retain 0.2.0 until restarted.
- NEXT: Close radiation reliability/UI acceptance gates before Eddy3D integration. Prefer MCP / documented APIs over Computer Use.

## 2026-10-01 — Extended radiation reliability acceptance

- DONE: Reproducible dedicated-document MCP harness for actual unit changes, mixed geometry, independent stock comparison and construction/disabled-solver failure paths. Preserved a real mixed-case result artifact.
- TEST RESULT: Six cases passed on the formal 0.3.0 adapter. Metres, centimetres and millimetres each give 16 values with mean 1233.3471168086037 and stock delta 0; mixed closed Brep / triangular Mesh / shading gives 82 values, mean 2.442391017648778 and stock delta 0. Corrupt local user-object fixtures fail construction without leaking GH documents. Disabled solver yields RAD-GH-001 and no output directory.
- CLEANUP: Original Centimeters units and modified state restored; zero active test objects remain; GH document count restored. Installed component files and user scene untouched. No Computer Use.
- ROOT CAUSE/FIX: The initial independent stock harness omitted its output-directory creation; added it, then reran all six cases successfully. No production adapter change was needed.
- VERSION: Production stays at verified 0.3.0. This milestone adds acceptance tooling, evidence and reference results; it does not replace the installed plugin binary.
- KNOWN ISSUES: Small deterministic fixtures only; large-model behavior and full external solver crash injection remain pending. UI theme/keyboard/dialog visual acceptance and wind integration are still open.
- NEXT: Complete the remaining bounded radiation/UI gates before Eddy3D adapter work.

## 2026-10-01 — Full Ladybug priority and feature catalog

- USER PRIORITY: Complete original Ladybug features first; provide the full feature table. Wind CFD adapter work is deferred.
- DONE: Read every installed Ladybug .ghuser through Rhino MCP. 122 entries instantiated: 119 components plus three preset value lists. Generated complete Markdown/HTML catalogs with original descriptions, required/optional inputs, outputs, GUIDs, versions and honest Hub state. Added phased Ladybug development plan.
- ROOT CAUSE/FIX: Three value-list archives have no component Message/Params properties; handled their actual ValueList fields instead of calling them failed analysis components. The 119 analysis objects share one GhPython ComponentGuid; corrected the catalog to use 122 distinct UserObject GUIDs, with base GUID and SHA-256 retained.
- VERIFIED SCOPE: Installed archive coverage and metadata only. Incident Radiation is integrated/tested; Import EPW and Cumulative Sky Matrix are used by that verified pipeline. Remaining catalog entries are explicitly pending Hub integration. HTML interaction is implemented; native visual QA is not claimed.
- OTHER COMPLETED WORK: 4096-cell radiation stock/adapter comparison delta 0; adapter duration 1.5166476 seconds on the tested machine. Post-solve provenance failure RAD-SOLVER-005 leaves no success JSON and restores GH document count. Single flat surface capacity, not full project certification. Preliminary Eddy metadata inventory retained without a CFD run.
- VERSION/NEXT: Production remains 0.3.0. Next implementation is L1 typed weather/time data and original-component adapter comparisons.

## 2026-10-01 — 0.4.0 original EPW weather module

- DONE: Typed location/time/data contracts, isolated original LB Import EPW adapter, native Weather Panel, reciprocal radiation navigation, annual/range/API custom hours, units/header metadata, raw missing values and mask, explicit JSON export, previous-result preservation.
- TEST RESULT: Build 0 warnings / 0 errors. Eight weather cases passed: annual, 24 hours and year boundary all have numerical delta 0 and identical original units/times; missing file, duplicate/out-of-range hours and null request blocked; missing sentinel values preserved and all-missing statistics null. GH document count restored.
- REFERENCE: Independent original LB Deconstruct Data/Header and Data DateTimes extract reference results. Python.NET cannot directly read IronPython dynamic collection attributes; reference harness uses these original GH components. EPW instantaneous fields follow native timestamp alignment; no manual shift is applied.
- RELEASE: Both existing plugin registrations updated with backup/hash/readback checks. Fresh bonobo Rhino loaded the formal 0.4.0 path and visible Weather Panel. Field selection, monthly summary, wind-direction mean suppression, noncontiguous hour preservation and failed-import result preservation passed. Existing radiation mean remains 1233.3471168086037 kWh/m2.
- LIMITS: L1 partial, not all 122 functions implemented. Non-leap hourly EPW only; monthly ground temperatures are not hourly filtered. Arithmetic statistics are not circular wind metrics. Theme/keyboard/dialog and actual visual QA remain pending. No Computer Use, solver reimplementation or CFD execution.
- NEXT: Original STAT/DDY, location and independent time-period utilities, with per-function original comparisons and catalog updates.


## 2026-10-01 — Original time tools and 0.8.3 building-performance UI

- DONE: Added typed original LB Analysis Period, Calculate HOY and HOY to DateTime adapters and native Time Panel. Seventeen native/reference/error checks pass, including cross-year, overnight, subhour and end-day normalization. Catalog now tracks eight independently integrated entries, one verified radiation backend and 113 pending entries out of 122.
- UI AUDIT / DESIGN: Audited native Eto/WPF panels and GH workflow; recorded findings in UI_AUDIT_2026-10-01.md. Shared header/navigation and ruled sections replace repeated card frames. The overview distinguishes an executable solar workflow, supporting environment tools and planned engine integrations. Human-readable climate labels retain original names/types in exported contracts.
- SOLAR FLOW: Six stages with fixed stage navigation; explicit completed EPW/hourly-period transfer; existing advanced CPU/sky/reflectance/offset defaults; typed preflight; KPI/range/exact mesh-color samples; optional inclusive project criterion; owned-preview viewport focus; uniquely named session scenarios and full-provenance comparison JSON. Changed inputs and failed runs preserve useful completed results.
- ROOT CAUSES / FIXES: Narrow shared table columns previously hid numeric inputs; wide hints now sit outside field grids. Native criterion controls round to one decimal, so the public boundary rejects unsupported precision instead of silently changing a threshold. Per-run unordered colors are not interpreted as a continuous palette. Geometry fingerprint differences are disclosed as records requiring model review, not proof of physical geometry changes.
- VERIFIED: Final build has 0 errors / 0 warnings. Twenty-five Core preflight checks, 21 native UI/result cases, five overview buttons and six shared routes passed. Fresh coati Rhino loaded the registered 0.8.3 assembly. Radiation baseline remains 1233.3471168086037 kWh/m2. The 96-cell three-dimensional fixture confirms native multi-color face mapping. Core and Adapter DLLs are byte-identical to pre-platform 0.7.2. Twenty-two production Eto/WPF offscreen renders at 320/480 px were visually inspected in the current theme. See platform_083_acceptance.json and release_083_loaded.json.
- LIMITS / NEXT: Current GH solve is synchronous; reliable percentage progress/cancel requires a separately verified runner. Full Dock/theme/keyboard/dialog acceptance, persistent scenario-library import and additional engines remain open. Continue the remaining L1 Ladybug location/data utilities, then broader solar/comfort/chart coverage. No Computer Use or CFD execution was used. Versioned package and registry backups preserve earlier releases; existing loaded Rhino processes need restart to use the new binary.


## 2026-10-01 — 0.8.5 native topic hierarchy and visual refinement

- DESIGN: Added muted semantic accents for model, environment, settings, run, results and compare; centralized light/dark tokens, quiet rules and native vector module/section icons. Full-width titles follow the compact brand/version row. Literal labels disable mnemonic parsing so ampersands remain visible; 0.8.4 captures revealed this and its loaded binary is preserved. No solver palette or numerical output is recolored.
- SCOPE: V1 remains in the current Rhino/Eto framework. V2 larger visual interaction is explicitly deferred until the major function milestones are accepted. This release adds no Ladybug adapters; catalog remains eight independently integrated, one backend-only and 113 pending entries out of 122.
- VERIFIED: 0 errors / 0 warnings. Fresh owned Rhino loaded registered 0.8.5; unchanged radiation benchmark 1233.3471168086037 kWh/m2. Native platform 21, time 17, location 11 and climate 11 cases passed, plus five overview buttons and six module routes. Core/Adapter source is unchanged. Whole-file hashes differ from 0.8.3 because the SDK embeds the current informational Git revision and build identity; all managed method bodies and metadata match after excluding only MVID and that revision. The comparison covers IL, locals, stack and exception regions; it is not byte identity. Actual host topic/secondary text colors are opaque and exceed 4.5:1 contrast; token math also checked white and #20242A. Twenty-two native production-control offscreen images at 320/480 px inspected. See topic_085_acceptance.json and binary_085_logic.json.
- LIMITS: Token math is not native dark-theme QA. Full Dock/theme switching, keyboard/picker/dialog checks, asynchronous progress/cancel and further engine integration remain open. No Computer Use. Existing loaded Rhino processes need restart to use the new assembly; versioned packages and registration backups retain earlier releases.

## 2026-10-02 · 0.9.0 SunPath 幾何第一批

新增原生 LB SunPath 契約／Adapter／中文內部模組，7 指令在同一 Dock；32 SunPath＋60 既有＋14 平台，共 106 原生數值／操作檢查；30 張當前淺色影像。9 獨立／1 後端／112 待接入。新增完整選項邊界，下一項 Direct Sun Hours。原生檔案未修改；Core／Adapter 新增檔案而非整個 DLL 不變。跨機／完整 UI 仍待驗收。

## 2026-10-02 · 0.9.2 文字尺度修正與最終交付

實際視埠 QA 發現 0.9.0 文字繼承文件註解尺度；0.9.1 單一數值 setter 未通過。使用官方 SetOverrideDimStyle／SetFieldOverride 明確覆寫各 owned 文字，在 100 倍父樣式驗證並保留文件設定；Core／Adapter 二進位與 0.9.0 相同。108 原生檢查、30 UI＋1 真正視埠已驗收；跨機與完整宿主品質仍待補。


## 2026-10-02 · 家用移轉交接

新增 LB-061 候選 Core／Adapter／中文內部模組與 UI-only preview owner。0.10.1 原生 154 項通過、44 UI＋2 3D 擷取；窄版圖例／數值欄位缺陷未驗收。0.10.2 修正／Build 0 錯誤 0 警告，尚未載入複驗。使用者要求先整理再安全移轉家用電腦，停止新增功能，專案快照保留未提交來源；無跨機通過宣稱。

## 2026-10-03 · 家用 0.10.2 接續與 MCP 確認

- 本機 SDK 8.0.425、Rhino 8.35.26251.13001／.NET 8.0.31。建置至新的 home-build/0.10.2，0 錯誤／0 警告，新專用 aardvark Rhino 載入 0.10.2.0；本輪產品 C# 來源未新增修改。
- 家用重播 154 原生／平台、25 Core、3 輸出回讀通過，日射基準與 13 組 SunHours stock 比較保持一致。44 張 320／480 px 淺色正式控制項影像與 2 張真正視埠已檢視，欄寬缺陷未重現。Ladybug 122 個入口 SHA 相符；Eddy3D 1.12.0.827 載入，CFD 未求解。
- MCP Router 在受限執行曾因 AppData listener 存取失敗；正式核准後初始化、32 工具探索與指定 Rhino 唯讀 Python 執行成功。修正 mcp_probe 對內層腳本錯誤／router 提前退出的誤判，8 項回歸通過。
- 實際桌面視窗擷取經重新選取及重試仍逾時；完整 Dock／原生深色／鍵盤／picker／file dialog 未驗收。正式維持 0.9.2／9、1、112，候選 10、1、111；尚未正式試用包／Notion 同步／Sky Mask。新版 evidence/home_0102 保留嘗試與成功紀錄，歷史 receipts 未改寫。
- 接續文件、功能表 JSON／Markdown／HTML 與 [本機驗證報告](HOME_VALIDATION_0102.md) 已更新，明確標示原生驗證通過及完整 UI 待辦。

## 2026-10-03 · 地端與 Notion 同步規則及候選補同步

依使用者要求，有實際進度時同步地端知識文件與原有 Notion 資料庫，再以繁體中文回報；候選／部分驗證也須記錄，無變化不通知、不改日期。更新 8 筆既有固定 ID、新增 `VER-HOME-0102-01`；191 筆唯一編號、122 功能入口與正式 9／1／112 已讀回。保留既有資料庫與歷史 receipts，候選同步不等同正式 UI／發布驗收。[同步紀錄](evidence/notion_home_0102_sync_2026-10-03.json)。
