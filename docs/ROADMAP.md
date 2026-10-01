# Roadmap

1. Phase 0 — verified runtime environment, 239 deduplicated component search results, asset index, original Ladybug radiation smoke workflow, Rhino preview, repeat run with exact value match. Done for the documented scope; binary asset execution and OpenFOAM remain unverified.
2. Radiation adapter — C#/.NET 8 standard request/result contracts, geometry/context object IDs, weather/north/period/grid/settings, isolated stock GH execution, actual solver-path verification and JSON result export. Runtime verified.
3. Radiation validation — annual, shaded/rotated 24-hour and scaled-geometry cases compare every value and min/max/mean against an independent stock definition, all differences 0. Five execution gates and 25 Core checks pass. Full solver-failure injection, runtime unit-system changes, complex meshes and larger models remain pending.
4. Minimal Eto dockable panel — geometry/context/EPW selection, Grid, North, Preflight, Run, status/statistics and Reset. Plugin load, visible panel, shared UI execution path, repeat and owned-mesh reset runtime verified. Interactive picker/dialog clicking and full visual UI QA remain pending.
5. Wind — inspect and wrap a working Eddy3D definition, verify the actual installed solver and compare stock/adapter output. Pending.
6. Quick/Standard/Expert modes, comparison/export and additional analysis adapters. Future.

The present validation weather is Seattle. Choose and verify project weather/location before any site-specific analysis. Execution is synchronous; cancellation and progress are pending. No general scientific certification or company deployment readiness is claimed.
