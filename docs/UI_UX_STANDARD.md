# UI / UX standard

## Intent and hierarchy
A professional Rhino analysis tool must make the next action clear without hiding technical meaning. Retain the existing Eto panel, Rhino MCP integration and verified original Ladybug execution path.

Use a short title, quiet subtitle and six numbered analysis stages: Geometry / Model, Environment / Weather, Simulation settings, Validate / Run, Results, Compare / Export. Validation precedes execution even when visually combined. Supporting climate utilities may use shorter task-specific sequences. Put units next to numeric inputs and statistics. Shared tokens: 8 px inner spacing, 14 px section spacing, 16 px panel padding; existing compact field bodies may use 12 px inset. Titles use host bold 18 pt, section labels bold 11 pt, KPI summary bold 13 pt, brand/version 10 pt, other controls the native font. Keep one primary execution action.

Use open ruled sections rather than outlined cards. Professional, minimal, scientific, architectural and technical presentation takes precedence over a web-dashboard appearance. No gradients, decorative animation, excessive rounding, shadows or saturated navigation colors. System colors follow the host theme. Restrained categorical accents identify interface topics; solver palettes remain exclusive to actual results. The overview distinguishes available workflows, environment utilities and explicitly planned integrations.

Use HubUi.Header for module hierarchy. Only HubWorkspacePanel is registered with Rhino; it owns one fixed module selector and cached internal views. EnvironmentalHub opens the overview inside that workspace. Remove per-view navigation and route all commands/actions internally, retaining inputs, completed results and session snapshots. Never register a new independent Dock panel for each feature. Keep wide hints and checkbox rows outside multi-column field grids: single cells in a shared DynamicLayout can push numeric fields offscreen. Calendar conversion uses vertical labeled fields; time period start/end inputs use a separate compact grid.

Use Eto system background and text colors to follow the host theme. Wrap explanations and diagnostics. Keep full file paths selectable and available as tooltips. Scroll vertically when docked narrowly. Never rely on color alone for errors, warnings, completion or stale results.


## Topic colors and icons — V1

Keep the current Rhino/Eto framework throughout V1. HubVisuals centralizes theme-aware accents and native vector glyphs; HubUi applies them to module identity, section headings, rules and workflow labels. Titles, units, input values, diagnostics and result numbers retain their ordinary readable hierarchy. Pair color with text and icons; color alone never conveys execution or validation state. Icons use 1.5-unit strokes on a 24-unit grid, without emoji, external fonts or raster assets.

| Topic | Light accent | Dark accent | Meaning / glyph |
| --- | --- | --- | --- |
| Model | #3E5D72 | #AAC2D2 | Geometry / cube |
| Environment | #226B61 | #8ECBBF | Weather and site / cloud or location pin |
| Settings | #58528B | #BBB1E0 | Parameters and time / sliders or clock |
| Run | #8A652E | #D4B778 | Validation and execution / play or sun |
| Results | #48585A | #B5C7C9 | Statistics / bars |
| Compare | #73506E | #D2B0CA | Scenarios and export / split frame |
| Overview | #4B5865 | #B8C5D0 | Platform identity / grid |

The small brand glyph/version row precedes a full-width title, allowing long architectural titles to wrap naturally. Muted section rules derive from the background and topic color. Assess heading/secondary-text contrast separately from intentionally subtle rules. This palette never recolors simulation meshes, legends or saved data. Dark tokens are defined; native dark-theme switching remains a separate acceptance gate.

## Interaction and state
Enable Run when geometry and a weather path are supplied; preflight remains the authority on validity. Label results as previous when inputs change. Preserve previous numerical results after unsuccessful runs. Warnings require an explicit continue decision. Errors show an actionable message and diagnostic code. Export the actual full result contract, including provenance, parameters and units. Clear preview deletes only owned meshes and leaves saved files available.

The current GH solve is synchronous on Rhino's UI thread. State that Rhino may pause and cancellation is unavailable. Do not present fabricated percentages or ineffective cancel controls. A future asynchronous runner must preserve GH/Rhino threading requirements and pass runtime verification.

## Verification gates
Build against the installed SDK. Recheck request → adapter → colored mesh, reset ownership, repeatability and failure behavior in a fresh Rhino session when assemblies are locked. Inspect the actual panel at 320 / 480 px dock widths, supported light/dark themes, long paths and multiline errors. Check keyboard/tab order and native picker/file dialogs. Record build, solver, interaction and visual checks separately.

## Current scope
0.8.5 adds restrained topic colors, native vector icons and full-width titles to the existing shared sections across all six modules. The architectural workflow overview, stage navigation and full six-stage radiation flow retain the current Rhino/Eto framework. Existing solver defaults remain 1 CPU, standard sky, ground reflectance 0.20, sensor offset 0.10 m; advanced controls are collapsed by default. API-supplied analysis hours and advanced settings must survive the next button request. Controls that assess a project criterion change presentation only and must not mark simulation inputs stale.

Result color samples must come from actual uniform-colored mesh faces aligned to their native cell values. Never infer a continuous palette from the unordered Legend.ColorsArgb array or recolor a result. Label samples and per-run scales clearly. If mapping cannot be established, disclose that and defer to the viewport. Range, average, min/max, cell count and units must describe the same result. Optional pass/fail is an inclusive user-defined project range, not regulatory compliance.

Scenario comparison stores named completed-result snapshots (including geometry/weather hashes and settings); exports retain full provenance. Report deltas only for matching weather hash, time period, analysis type and units. Disclose differing geometry/context fingerprints (review model state), grid, north, advanced settings or solver versions. A fingerprint alone is not an independent geometric change detector. Arithmetic cell means are not area-weighted and differences alone do not establish improvement. Do not let failed runs or clearing the current preview remove saved scenarios. Session snapshots are not persistent until exported. User criterion bounds use explicit 0.1 kWh/m² precision; reject unsupported precision rather than silently rounding it.

Build, native solver/control tests and visual captures are independent gates. Current evidence lives in release_086_loaded.json, platform_086_runtime.json, chinese_086_ui.json and ui_086/capture.json. Offscreen production-panel rendering verifies current-theme layout; full dock, light/dark switching, keyboard and file-dialog QA remain separate requirements.

## Traditional Chinese — 0.8.6

The user-facing platform language is Traditional Chinese (zh-TW). Use the six stages「幾何／模型 → 環境／氣象 → 模擬設定 → 檢核／執行 → 分析結果 → 比較／匯出」. Use「進階設定」「前次結果」「基準方案」「比較方案」「符合／未符合」consistently. Field labels, status, validation and summaries must not expose raw English data-type keys as their primary labels.

HubText supplies native weather/climate field names, frequency, design-day type and diagnostic presentation. Preserve native keys, values, scientific acronyms, units, user-entered names, file paths, command names and JSON contracts. Unknown native messages include the original diagnostic; do not guess a physical interpretation. Keep identifiers available for troubleshooting.

Host default fonts supply native CJK fallback. Review glyphs and line wrap at 320/480 px; keep actions compact and long explanation text outside numeric field grids. UI language does not imply a translated Rhino or operating-system interface. Full Dock, native picker/file dialogs, keyboard and light/dark switching remain distinct acceptance gates.

## Unified workspace — 0.8.7

The workspace retains the original overview Dock GUID. Modules are lazily cached and detached/re-attached without disposal when navigating; the existing solver and document guards remain in each view. Weather/period transfer reads completed data from the same workspace. Six legacy commands select internal views in one Rhino panel. Session data persists across view switching and Windows Dock close/reopen, not application restarts; export before closing Rhino.

Native evidence: workspace_087_runtime.json (13 checks), release_087_loaded.json and platform_087_runtime.json (60 existing checks), ui_087/capture.json (22 current-theme offscreen images including the shell). Dock identity and close/reopen are verified, while full dock sizing, themes, keyboard and native dialogs remain separate gates.

## 2026-10-02 更新 · 0.9.0

目前為 9 獨立功能、1 後端、112 待接入；SunPath 幾何第一批透過新增契約與原生 Adapter 接入第七個內部模組。原有求解檔案保留。32＋60＋14 共 106 項原生檢查；30 張目前淺色 320／480 px 離屏影像。SunPath 未含氣象著色／條件／夏令時間／圖例等完整選項，見 [SUNPATH_MODULE.md](SUNPATH_MODULE.md)。下一項 Direct Sun Hours；跨機、完整 Dock／theme／keyboard／dialogs 驗收未閉合。本文前段版本記錄保留原驗收範圍，最新狀態以 PROJECT_STATUS.md 為準。

0.9.2 最新修正：SunPath 文字以明確的 DimensionStyle 欄位覆寫固定物件尺度，文件樣式不變。108 原生檢查、30 張淺色 UI 影像及 1 張真正視埠已檢視；9／1／112 不變。0.9.0／0.9.1 過程證據保留，最新正式狀態以 PROJECT_STATUS.md 為準。
