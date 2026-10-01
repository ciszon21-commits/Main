# Building-performance workspace

The native Eto/Rhino UI is organized as a performance-analysis platform. There is no replacement web frontend or simulation-core rewrite. The overview separates executable solar radiation, environment utilities and planned engines. Daylight, thermal comfort, energy, carbon and CFD are shown as planned; their engines are not executable Hub workflows yet.

`EnvironmentalHub` opens the overview. `EnvironmentalRadiation` opens the solar analysis. Its fixed stage selector provides direct access to:

1. Geometry / Model: select Breps/Meshes and optional shading context.
2. Environment / Weather: select a non-leap hourly EPW, explicitly use a completed EPW selection or completed analysis period from the environment tools, or reset to annual. Fractional periods and calendar conversions are rejected without changing the established selection.
3. Simulation settings: 1 m grid and 0° north initially; collapsed advanced CPU, sky density, reflectance and sensor-offset controls use the existing solver defaults.
4. Validate / Run: the existing typed preflight rejects invalid inputs; warnings require review. Actual errors keep previous results and previews.
5. Results: average/min/max/count/units, exact sampled cell colors, execution duration/location/warnings and conditions, optional project target range and viewport focus.
6. Compare / Export: named completed-result snapshots, baseline/candidate selection, scientific comparability notes and full-provenance JSON.

Result colors come from actual uniform-colored native mesh faces aligned with their values. No smooth scale is fabricated from the unordered color array. Each result retains its original palette; numerical comparisons avoid cross-run scale confusion. Viewport focus zooms to owned preview bounds in the originating document and does not delete or select user geometry.

The project target is inclusive, entered at 0.1 kWh/m² precision, and measures the fraction of cells within the range. It is not a legal/regulatory compliance assessment or area-weighted performance metric. Invalid bounds and unsupported precision are rejected before changing an established criterion. The comparison export records the configured criterion and interpretation.

Comparison requires matching weather SHA-256, analysis type, units and selected hours before reporting mean deltas. Differences in recorded geometry/context fingerprints, grid spacing, north, advanced settings and solver/workflow are disclosed. A fingerprint difference requires reviewing model state; no independent geometric change detection is claimed. A cell mean is arithmetic, not area-weighted; a smaller or larger number alone does not establish improved architectural performance. Store up to 20 uniquely named snapshots per session. Clearing the current preview preserves snapshots; export before closing Rhino. No persistent scenario-library import is implemented. The exported criterion assessment describes the current completed result, as identified by its basis; snapshots retain their full values for further evaluation.

The original synchronous Grasshopper solve requires Rhino's UI thread. Rhino may pause; no reliable percentage or cancel action is exposed. An asynchronous runner with verified process cancellation is a separate development milestone. This UI release does not change the original radiation adapter or pretend that cancellation works.

Acceptance evidence is recorded separately for build, typed preflight, original numerical regression, native controls and production Eto/WPF layouts. MCP and SDK APIs are used without Computer Use. Offscreen 320/480 px renders establish layout in the current host theme, not full dock, theme-switching, keyboard or native file-dialog acceptance.
