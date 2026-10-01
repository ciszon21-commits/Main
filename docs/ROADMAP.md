# Roadmap

1. Phase 0 — verified runtime environment, 239 deduplicated component search results, asset index, original Ladybug radiation smoke workflow, Rhino preview, repeat run with exact value match. Done for the documented scope; binary asset execution and OpenFOAM remain unverified.
2. Radiation adapter — standard request/result contracts, named geometry/context/weather/period inputs, portable dependency discovery, preflight with error codes, deterministic execution and result export. Pending.
3. Radiation validation — compare adapter against original workflow using identical inputs, every value and min/max/mean; add shaded and rotated fixtures, missing/invalid geometry/weather/dependencies/parameters, units and scale, solver failures, repeated runs and reset. Pending.
4. Minimal Eto dockable panel — SELECT geometry, SELECT EPW, Grid, Preflight, Run, Status and Result; only after adapter validation. Pending.
5. Wind — inspect and wrap a working Eddy3D definition, verify the actual installed solver and compare stock/adapter output. Pending.
6. Quick/Standard/Expert modes, comparison/export and additional analysis adapters. Future.

The present result is a Seattle smoke test. Choose and verify project weather/location before any site-specific analysis. No production usability or broader scientific validation is claimed.
