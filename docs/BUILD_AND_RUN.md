# Build and run (0.6.0)

The current formal release is `artifacts/releases/0.6.0/EnvironmentalHub.Plugin.rhp`, with sibling Core/Adapter DLLs and `hub.config.json`. The portable package is `artifacts/EnvironmentalHub-0.6.0.zip`; its release manifest records SHA-256 hashes. Ladybug and Radiance remain external installed dependencies.

```powershell
dotnet build EnvironmentalSimulationHub/src/EnvironmentalHub.Plugin/EnvironmentalHub.Plugin.csproj -c Release -m:1 -p:CleanFile=Release060.FileListAbsolute.txt -o EnvironmentalSimulationHub/artifacts/releases/0.6.0
```

Do not rebuild over loaded release files. Preserve this versioned directory while Rhino references it. Later releases should use a new version and directory. Existing Rhino processes cannot replace an already-loaded .NET plugin; load a new version in a fresh process. The command `EnvironmentalHub` opens the registered Dock Panel. Its subtitle displays the assembly version, currently 0.6.0.

The formal update is checked using Rhino MCP and RhinoCommon: plugin GUID, loaded assembly path/version, registered PathFromId, docked panel assembly/version, and a real Ladybug radiation fixture. See `docs/evidence/release_060_loaded.json` for the current release outcome, including Weather Panel and radiation regression. Only that receipt confirms the registered and loaded version; a build or reflected test form alone does not.

Configuration expands environment variables for the Ladybug user-object and Radiance directories. OutputDirectory is relative to the plugin directory unless absolute. Keep DLLs/configuration together. No solver is installed or reimplemented by this release.

Select Breps/Meshes, optional shading context, a complete hourly non-leap EPW, grid spacing in metres and north rotation. Check inputs, then run; warnings require explicit acceptance. Results contain actual colored mesh, min/max/mean/count, full JSON and provenance. Changed inputs mark prior results. A failed solve or staged preview replacement preserves the old result. Clear preview deletes only panel-owned mesh objects and keeps saved files.

Current UI defaults: annual, 1 CPU, Tregenza sky, 0.2 ground reflectance and 0.1 m offset. Backend requests also support selected hours. Execution is synchronous; cancellation is unavailable. Full theme, keyboard, picker/dialog and narrow-dock visual QA remain pending. Prefer MCP/API verification over Computer Use, following the user's preference.

Validation receipts: adapter_runtime_validation.json (three original-workflow comparisons and five execution gates), preflight_tests.json (25 checks), panel_v6_runtime_validation.json (native Eto execution, null/invalid requests, partial-preview rollback and reset), and release_030_loaded.json (formal plugin registration/dock load).

## Updating an existing registration
The audited local installation had both HKLM and HKCU entries pointing to runtime-v3. `tools/update_release_registration.ps1` validates release hashes/version, backs up the two existing FileName values, then updates only those values and checks readback. This requires registry write permission. It does not unload an assembly in an already running Rhino. Use a fresh Rhino process for the new version. See release_registration_updated.json for the update receipt.

## Extended radiation reliability checks
`tools/validate_radiation_reliability.py` requires a dedicated empty Rhino document and injected hub_root. Use the bounded MCP call fixture reliability_calls.json with its explicit current test slot; do not target a user document containing geometry. Receipt: `docs/evidence/radiation_reliability_validation.json`.

Six checks passed against the unchanged formal 0.3.0 adapter: three actual runtime unit systems, independently bound stock comparison for mixed closed Brep / triangular Mesh / context, failed user-object construction without a GH document leak, and the genuine disabled-solver guard with no solver output. Units and modified state are restored, all test geometry is removed, and GH document count returns to baseline. Generated solver work folders are ignored; the actual mixed-case JSON result is retained in samples/radiation_reliability.

## Weather module (0.4.0)
Run `EnvironmentalWeather` or use the panel navigation button. Import an EPW, select annual or a contiguous zero-based HOY range (0–8759), inspect individual fields and export the full typed JSON. API requests also accept noncontiguous hours. All original Import EPW outputs are retained: location, 15 hourly data collections and three monthly ground-temperature collections for the tested file. Monthly collections remain unchanged under hourly selection. See WEATHER_MODULE.md for semantics and verification. Eight weather runtime checks passed; the formal native panel preserves results on failure, retains custom hours, switches fields and suppresses arithmetic wind-direction means. Picker/dialog, themes and visual layout acceptance remain pending.

## Location module (0.5.0)
Run EnvironmentalLocation or open it from Weather. Original Construct Location supports explicit or native-estimated time zone and JSON export. See LOCATION_MODULE.md. Formal runtime evidence: release_050_loaded.json, with 11 location cases and eight culture/UTC formatter checks. Weather half-hour display is fixed, with real native Panel verification; weather and radiation regression pass.

Current 0.6.0 also provides EnvironmentalClimate for original STAT / DDY imports. Three-city full native JSON and design-day IDF comparisons plus invalid-input and Panel checks passed; see docs/CLIMATE_FILE_MODULE.md (CLIMATE_FILE_MODULE.md from this docs directory) and release_060_loaded.json.
