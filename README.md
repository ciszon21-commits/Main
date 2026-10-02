# Environmental Simulation Hub

Knowledge entry: [current status](docs/PROJECT_STATUS.md), [knowledge index](docs/KNOWLEDGE_INDEX.md), [stage plan](docs/ROADMAP.md), and [Ladybug batches](docs/LADYBUG_DEVELOPMENT_PLAN.md). The user-designated [Notion database](https://app.notion.com/p/27b5fd42055b410ea1d58fbbf60fd31e) contains 178 classified records; see [destination and maintenance](docs/NOTION_KNOWLEDGE.md). The October 2 Chinese UI release changes presentation; function coverage remains 8 standalone / 1 backend / 113 pending.

Original Ladybug radiation and EPW weather backends, typed C# adapters and Rhino dockable panels — **RUNTIME VERIFIED** on Rhino 8.35 / .NET 8.0.30.

Run `EnvironmentalHub` for the building-performance overview or `EnvironmentalRadiation` for the six-stage analysis workflow. Select geometry/context, choose EPW and time, set basic or advanced parameters, validate and run. Results include native mesh-color samples, numerical KPIs, project target evaluation and viewport focus. Compare named session scenarios and export full provenance. Reset removes only panel-owned previews and preserves saved scenarios. See [platform UI and limits](docs/PLATFORM_UI.md) and [UI audit](docs/UI_AUDIT_2026-10-01.md).

The local plugin is `artifacts/releases/0.8.7/EnvironmentalHub.Plugin.rhp`. Build and loading instructions are in `docs/BUILD_AND_RUN.md`. Release 0.8.7 has been registered and loaded in a fresh Rhino process. Run `EnvironmentalWeather` for climate fields and hourly selection; `EnvironmentalRadiation` opens radiation. Execution is synchronous. Existing Rhino processes retain their loaded version until restarted.

V1 retains the current Rhino/Eto framework. Topic colors and native vector icons distinguish model, environment, settings, run, results and comparison without changing simulation palettes. Shared titles, spacing and ruled sections follow [UI standards](docs/UI_UX_STANDARD.md). Larger visual interaction is planned for V2 after the major function milestones are accepted; see [release strategy](docs/ROADMAP.md). This presentation release does not add Ladybug functions.

Open `workflows/radiation/radiation_main.gh` in the inspected Rhino installation to see the original Ladybug workflow. The saved input is a 4m × 4m Brep snapshot from a Rhino object. The fixture uses bundled Seattle-Tacoma EPW data, annual cumulative radiation, north 0°, and 1m grid. It is not a Taipei project result.

The active Rhino session displays the result mesh and Ladybug legend. `samples/radiation_smoke/radiation_smoke.3dm` contains the input Brep and colored result mesh; its legend remains in the GH definition, not baked into that sample model. `runtime_result.json` stores all 16 physical values and their provenance. `rhino_preview.png` records the display.

Read `docs/ENVIRONMENT_AUDIT.md`, `docs/COMPONENT_INVENTORY.md`, and `docs/ROADMAP.md` before extending the workflow. Raw MCP evidence is retained in `docs/evidence/`.

The tools directory contains audit/fixture tooling; compiled code lives in `src/`. Core contracts have no Rhino/GH dependencies. The adapter constructs an isolated definition from installed original user objects, never modifies the smoke canvas, and verifies the actual gendaymtx executable used by Ladybug. Core and adapter source is unchanged in 0.8.7. Compiled method bodies and managed metadata match 0.8.5, excluding only build MVID and the informational Git revision; whole-file hashes differ. See `docs/evidence/binary_086_logic.json`. This release provides Traditional Chinese (zh-TW) navigation, controls, field names, diagnostics and result summaries. Native values, technical identifiers, command names and JSON contracts retain their original forms. Reliable cancellation/percentage progress and wind workflows remain future milestones.

Paths passed in `tools/*_calls.json` are captured environment-specific replay inputs. Configure them for another machine. Executable scripts receive their project/weather/component roots from the caller; no source copy of the Ladybug solver is maintained here.

To regenerate the audit from captured evidence, run `python tools/write_audit.py` in the verified environment. The original LBT components remain separately installed dependencies; their license notices and terms apply to company deployment.

Full original Ladybug scope: [122-entry feature table](docs/LADYBUG_FEATURE_TABLE.md) and searchable [HTML catalog](docs/LADYBUG_FEATURE_TABLE.html). Eight standalone functions are integrated and tested, one function is used by the radiation backend, and 113 entries await integration. See [current status and verification scope](docs/PROJECT_STATUS.md) and [weather semantics](docs/WEATHER_MODULE.md).

Run EnvironmentalLocation for the original Ladybug location tool; half/quarter-hour UTC display is preserved in both location and weather panels. See docs/LOCATION_MODULE.md.

STAT / DDY support introduced in 0.6.0 provides EnvironmentalClimate for original STAT / DDY imports. Three-city full native JSON and design-day IDF comparisons plus invalid-input and Panel checks passed; see docs/CLIMATE_FILE_MODULE.md (CLIMATE_FILE_MODULE.md from this docs directory) and release_060_loaded.json.

0.8.7 unified entry: EnvironmentalHub opens the overview; EnvironmentalRadiation opens radiation directly. EnvironmentalTime provides original period and date/HOY tools. All panels share navigation and styling; source/result state remains module-specific. See TIME_AND_HUB_MODULE.md in docs for native runtime and UI capture scope.

新版介面整合：EnvironmentalHub 與五個模組指令均開啟同一 Rhino 工作平台，以頂部中文選單切換內部模組，保留草稿與完成結果。已載入舊版的 Rhino 需儲存工作後重新啟動以載入 0.8.7。
