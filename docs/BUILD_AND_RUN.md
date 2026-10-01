# Build and run (development 0.2.0)

Requires the audited Rhino 8 SDK assemblies and .NET 8-compatible SDK. No new NuGet package or physics solver was installed for this milestone.

From the parent workspace:

```powershell
dotnet build EnvironmentalSimulationHub/src/EnvironmentalHub.Plugin/EnvironmentalHub.Plugin.csproj -c Release -m:1 -p:AdapterAssemblyName=EnvironmentalHub.Adapters.RuntimeV3 -p:CoreAssemblyName=EnvironmentalHub.Core.RuntimeV3 -p:CleanFile=RuntimeV3.FileListAbsolute.txt -o EnvironmentalSimulationHub/artifacts/runtime-v3
```

`RhinoInstallDir` is configurable with an MSBuild property; its default is the Program Files Rhino 8 installation. `-m:1` resolved the local multi-project MSBuild evaluation failure. Final build: 0 warnings, 0 errors. Older assemblies already loaded in Rhino are locked; close that Rhino before rebuilding this exact loaded version. Development assembly suffixes allowed validation without restarting the user's existing session.

The live runtime-v3 panel passed the functional tests. A subsequent selection guard fix clears selection when changing documents and catches picker exceptions; it is build verified in `artifacts/next/EnvironmentalHub.Plugin.rhp`, with cross-document picker interaction still pending runtime QA. Loading this updated RHP requires a fresh Rhino session because the existing plugin assembly is already loaded. Keep its sibling DLLs/configuration together when changing the registered plugin path.

Load `artifacts/runtime-v3/EnvironmentalHub.Plugin.rhp` through Rhino's plugin manager, or the verified RhinoCommon LoadPlugIn API. Rhino remembers the loaded path between sessions. This local build was loaded successfully; no system installer was used. Core/adapter DLLs and `hub.config.json` must remain beside the RHP.

`hub.config.json` configures installed Ladybug user-object and Radiance bin directories, expanding environment variables. `OutputDirectory` is relative to the plugin folder unless absolute. The solver configuration must match Ladybug's actual configured executable, which the adapter verifies. Output contains `analysis_result.json` and genuine Radiance WEA files.

Rhino command: `EnvironmentalHub`.

1. Select valid Breps/Meshes for analysis, optionally select shading context.
2. Select a complete non-leap hourly EPW; location comes from its header.
3. Set grid in metres and north in Ladybug's counterclockwise convention from +Y.
4. Preflight; errors prevent a run, warnings require Yes in the UI.
5. Run; inspect colored mesh and min/max/mean/count in the panel.
6. Reset removes only meshes created by that panel; input geometry remains.

The UI currently analyzes the full year with 1 CPU, Tregenza sky, 0.2 ground reflectance and 0.1m offset. The backend request additionally supports explicit hour subsets/settings. Quality labels do not silently alter numerical settings.

Validation evidence: `docs/evidence/adapter_runtime_validation.json`, `panel_runtime_validation.json`, and `preflight_tests.json`. Comparisons used identical original Ladybug settings, every value, and summary statistics. Panel verification used the same ExecuteRequest path as the Run button; picker and file-dialog interactions were not manually clicked in this audit.

Known limits: synchronous execution blocks Rhino during solving; progress/cancel/cache absent. No wind adapter. No Taipei-specific study. Scene preview from an already-open unrelated GH definition remains under the user's control. Preview meshes are actual Rhino document objects managed by the panel; reset ownership is instance-local and is not persisted across Rhino restarts.
