# UI / UX standard

## Intent and hierarchy
A professional Rhino analysis tool must make the next action clear without hiding technical meaning. Retain the existing Eto panel, Rhino MCP integration and verified original Ladybug execution path.

Use a short title, quiet subtitle and six numbered analysis stages: Geometry / Model, Environment / Weather, Simulation settings, Validate / Run, Results, Compare / Export. Validation precedes execution even when visually combined. Supporting climate utilities may use shorter task-specific sequences. Put units next to numeric inputs and statistics. Shared tokens: 8 px inner spacing, 14 px section spacing, 16 px panel padding; existing compact field bodies may use 12 px inset. Titles use host bold 18 pt, section labels bold 11 pt, KPI summary bold 13 pt, brand/version 10 pt, other controls the native font. Keep one primary execution action.

Use open ruled sections rather than outlined cards. Professional, minimal, scientific, architectural and technical presentation takes precedence over a web-dashboard appearance. No gradients, decorative animation, excessive rounding, shadows or saturated navigation colors. System colors follow the host theme; simulation colors appear only in actual results. The overview distinguishes available workflows, environment utilities and explicitly planned integrations.

Use HubUi.Header / Navigation for consistent module hierarchy and a compact selector instead of multiple stacked navigation buttons. EnvironmentalHub is the overview; module state stays in its registered Panel. Keep wide hints and checkbox rows outside multi-column field grids: single cells in a shared DynamicLayout can push numeric fields offscreen. Calendar conversion uses vertical labeled fields; time period start/end inputs use a separate compact grid.

Use Eto system background and text colors to follow the host theme. Wrap explanations and diagnostics. Keep full file paths selectable and available as tooltips. Scroll vertically when docked narrowly. Never rely on color alone for errors, warnings, completion or stale results.

## Interaction and state
Enable Run when geometry and a weather path are supplied; preflight remains the authority on validity. Label results as previous when inputs change. Preserve previous numerical results after unsuccessful runs. Warnings require an explicit continue decision. Errors show an actionable message and diagnostic code. Export the actual full result contract, including provenance, parameters and units. Clear preview deletes only owned meshes and leaves saved files available.

The current GH solve is synchronous on Rhino's UI thread. State that Rhino may pause and cancellation is unavailable. Do not present fabricated percentages or ineffective cancel controls. A future asynchronous runner must preserve GH/Rhino threading requirements and pass runtime verification.

## Verification gates
Build against the installed SDK. Recheck request → adapter → colored mesh, reset ownership, repeatability and failure behavior in a fresh Rhino session when assemblies are locked. Inspect the actual panel at 320 / 480 px dock widths, supported light/dark themes, long paths and multiline errors. Check keyboard/tab order and native picker/file dialogs. Record build, solver, interaction and visual checks separately.

## Current scope
0.8.3 applies shared ruled sections to all six modules, an architectural workflow overview, stage navigation and the full six-stage radiation flow. Existing solver defaults remain 1 CPU, standard sky, ground reflectance 0.20, sensor offset 0.10 m; advanced controls are collapsed by default. API-supplied analysis hours and advanced settings must survive the next button request. Controls that assess a project criterion change presentation only and must not mark simulation inputs stale.

Result color samples must come from actual uniform-colored mesh faces aligned to their native cell values. Never infer a continuous palette from the unordered Legend.ColorsArgb array or recolor a result. Label samples and per-run scales clearly. If mapping cannot be established, disclose that and defer to the viewport. Range, average, min/max, cell count and units must describe the same result. Optional pass/fail is an inclusive user-defined project range, not regulatory compliance.

Scenario comparison stores named completed-result snapshots (including geometry/weather hashes and settings); exports retain full provenance. Report deltas only for matching weather hash, time period, analysis type and units. Disclose differing geometry/context fingerprints (review model state), grid, north, advanced settings or solver versions. A fingerprint alone is not an independent geometric change detector. Arithmetic cell means are not area-weighted and differences alone do not establish improvement. Do not let failed runs or clearing the current preview remove saved scenarios. Session snapshots are not persistent until exported. User criterion bounds use explicit 0.1 kWh/m² precision; reject unsupported precision rather than silently rounding it.

Build, native solver/control tests and visual captures are independent gates. Current evidence lives in release_083_loaded.json, platform_ui_runtime.json and ui_083/capture.json once those checks complete. Offscreen production-panel rendering verifies current-theme layout; full dock, light/dark switching, keyboard and file-dialog QA remain separate requirements.
