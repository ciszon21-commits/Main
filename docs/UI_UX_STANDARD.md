# UI / UX standard

## Intent and hierarchy
A professional Rhino analysis tool must make the next action clear without hiding technical meaning. Retain the existing Eto panel, Rhino MCP integration and verified original Ladybug execution path.

Use a short title, quiet subtitle and numbered sections: Model, Weather, Analysis settings, Validate & run, Results. Put units next to numeric inputs and statistics. Use 8 px inner spacing, 10 px group padding, 12 px section spacing and 14 px panel padding. Keep one primary execution action. Avoid decorative dashboards and invented metrics.

Use Eto system background and text colors to follow the host theme. Wrap explanations and diagnostics. Keep full file paths selectable and available as tooltips. Scroll vertically when docked narrowly. Never rely on color alone for errors, warnings, completion or stale results.

## Interaction and state
Enable Run when geometry and a weather path are supplied; preflight remains the authority on validity. Label results as previous when inputs change. Preserve previous numerical results after unsuccessful runs. Warnings require an explicit continue decision. Errors show an actionable message and diagnostic code. Export the actual full result contract, including provenance, parameters and units. Clear preview deletes only owned meshes and leaves saved files available.

The current GH solve is synchronous on Rhino's UI thread. State that Rhino may pause and cancellation is unavailable. Do not present fabricated percentages or ineffective cancel controls. A future asynchronous runner must preserve GH/Rhino threading requirements and pass runtime verification.

## Verification gates
Build against the installed SDK. Recheck request → adapter → colored mesh, reset ownership, repeatability and failure behavior in a fresh Rhino session when assemblies are locked. Inspect the actual panel at 320 / 480 px dock widths, supported light/dark themes, long paths and multiline errors. Check keyboard/tab order and native picker/file dialogs. Record build, solver, interaction and visual checks separately.

## Current scope
0.3.0 adds five numbered groups, host theme colors, bounded viewport width, explicit numeric input widths, a displayed version, readable diagnostics, input readiness, prior-result state, full JSON export and honest execution limitations. Native Eto runtime checks cover real solve/repeat/reset, invalid/null request preservation and partial replacement rollback. Formal Dock registration/load is recorded separately in release_030_loaded.json. Full visual/theme/keyboard/dialog QA remains pending; API width measurements alone are not visual acceptance.
