# Build and run (0.8.7)

The current formal release is `artifacts/releases/0.8.7/EnvironmentalHub.Plugin.rhp`, with sibling Core/Adapter DLLs and `hub.config.json`. The portable package is `artifacts/EnvironmentalHub-0.8.7.zip`; its release manifest records SHA-256 hashes. Ladybug and Radiance remain external installed dependencies.

```powershell
dotnet build EnvironmentalSimulationHub/src/EnvironmentalHub.Plugin/EnvironmentalHub.Plugin.csproj -c Release -m:1 -p:CleanFile=Release087.FileListAbsolute.txt -o EnvironmentalSimulationHub/artifacts/releases/0.8.7
```

Do not rebuild over loaded release files. Preserve this versioned directory while Rhino references it. Later releases should use a new version and directory. Existing Rhino processes cannot replace an already-loaded .NET plugin; load a new version in a fresh process. The command `EnvironmentalHub` opens the single registered workspace. All five module commands open their cached view inside this same panel; navigation preserves inputs, results and session scenarios. Restart Rhino to replace an already-loaded previous version. Its subtitle displays the assembly version, currently 0.8.7.

The formal update is checked using Rhino MCP and RhinoCommon: plugin GUID, loaded assembly path/version, registered PathFromId, docked panel assembly/version, and a real Ladybug radiation fixture. See `docs/evidence/release_087_loaded.json` for the current release outcome, including Weather Panel and radiation regression. Only that receipt confirms the registered and loaded version; a build or reflected test form alone does not.

Configuration expands environment variables for the Ladybug user-object and Radiance directories. OutputDirectory is relative to the plugin directory unless absolute. Keep DLLs/configuration together. No solver is installed or reimplemented by this release.

Select Breps/Meshes, optional shading context, a complete hourly non-leap EPW, grid spacing in metres and north rotation. Check inputs, then run; warnings require explicit acceptance. Results contain actual colored mesh, min/max/mean/count, full JSON and provenance. Changed inputs mark prior results. A failed solve or staged preview replacement preserves the old result. Clear preview deletes only panel-owned mesh objects and keeps saved files.

Current UI defaults: annual, 1 CPU, Tregenza sky, 0.2 ground reflectance and 0.1 m offset. Advanced controls expose the existing typed settings. Explicitly use completed weather/time selections from supporting modules; fractional periods are rejected without rounding. Execution is synchronous; reliable cancel and percentage progress remain unavailable. Production unified workspace and Eto/WPF layouts are rendered at 320/480 px offscreen; full Dock/theme/keyboard/picker/dialog acceptance remains separate. Prefer MCP/API verification over Computer Use, following the user's preference. See PLATFORM_UI.md and platform_087_runtime.json for comparison, criterion and viewport-focus semantics.

Validation receipts: adapter_runtime_validation.json (three original-workflow comparisons and five execution gates), preflight_tests.json (25 checks), panel_v6_runtime_validation.json (native Eto execution, null/invalid requests, partial-preview rollback and reset), and release_030_loaded.json (formal plugin registration/dock load).

## Updating an existing registration
The audited local installation had both HKLM and HKCU entries pointing to runtime-v3. `tools/update_release_registration.ps1` validates release hashes/version, backs up the two existing FileName values, then updates only those values and checks readback. This requires registry write permission. It does not unload an assembly in an already running Rhino. Use a fresh Rhino process for the new version. See release_registration_updated_086.json for the update receipt.

## Extended radiation reliability checks
`tools/validate_radiation_reliability.py` requires a dedicated empty Rhino document and injected hub_root. Use the bounded MCP call fixture reliability_calls.json with its explicit current test slot; do not target a user document containing geometry. Receipt: `docs/evidence/radiation_reliability_validation.json`.

Six checks passed against the unchanged formal 0.3.0 adapter: three actual runtime unit systems, independently bound stock comparison for mixed closed Brep / triangular Mesh / context, failed user-object construction without a GH document leak, and the genuine disabled-solver guard with no solver output. Units and modified state are restored, all test geometry is removed, and GH document count returns to baseline. Generated solver work folders are ignored; the actual mixed-case JSON result is retained in samples/radiation_reliability.

## Weather module (0.4.0)
Run `EnvironmentalWeather` or use the panel navigation button. Import an EPW, select annual or a contiguous zero-based HOY range (0–8759), inspect individual fields and export the full typed JSON. API requests also accept noncontiguous hours. All original Import EPW outputs are retained: location, 15 hourly data collections and three monthly ground-temperature collections for the tested file. Monthly collections remain unchanged under hourly selection. See WEATHER_MODULE.md for semantics and verification. Eight weather runtime checks passed; the formal native panel preserves results on failure, retains custom hours, switches fields and suppresses arithmetic wind-direction means. Picker/dialog, themes and visual layout acceptance remain pending.

## Location module (0.5.0)
Run EnvironmentalLocation or open it from Weather. Original Construct Location supports explicit or native-estimated time zone and JSON export. See LOCATION_MODULE.md. Formal runtime evidence: release_050_loaded.json, with 11 location cases and eight culture/UTC formatter checks. Weather half-hour display is fixed, with real native Panel verification; weather and radiation regression pass.

STAT / DDY support introduced in 0.6.0 provides EnvironmentalClimate for original STAT / DDY imports. Three-city full native JSON and design-day IDF comparisons plus invalid-input and Panel checks passed; see docs/CLIMATE_FILE_MODULE.md (CLIMATE_FILE_MODULE.md from this docs directory) and release_060_loaded.json.

0.8.7 unified entry: EnvironmentalHub opens the overview; EnvironmentalRadiation opens radiation directly. EnvironmentalTime provides original period and date/HOY tools. All panels share navigation and styling; source/result state remains module-specific. See TIME_AND_HUB_MODULE.md in docs for native runtime and UI capture scope.
