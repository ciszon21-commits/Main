# Phase 0 environment audit

2026-10-01, Asia/Taipei. Evidence is in `evidence/`; physical result is in `../samples/radiation_smoke/`.

## Runtime baseline

- Rhino and Grasshopper: 8.35.26251.13001; Rhino process uses .NET 8.0.30.
- Installed .NET SDKs: 8.0.424 and 10.0.400 (terminal `dotnet --info`).
- Explicit MCP target: aardvark, PID 37272, port 10501. Default armadillo was stale and pruned by the router.
- Initial Rhino document: unnamed, no path, Centimeters, tolerance 0.01, 0 objects, 6 visible layers.
- Initial GH canvas closed; no active document, components, connections, groups, or clusters.
- Router requires its external SQLite state database to be writable; sandbox-only initialization failed. Authorized execution responded.

## Plugin and solver audit

| Stack | Verified version | Availability evidence |
| --- | --- | --- |
| Ladybug | core 0.44.56; radiation components 1.10.0 | Live library and actual radiation run |
| Honeybee | core 1.64.65 | Live HB component search; energy/daylight execution pending |
| Dragonfly | core 1.77.1 | Live DF component search; execution pending |
| Eddy3D | package 1.15.0-beta.827; loaded provisioning 1.15.0.827 | Live library search; wind execution pending |
| OpenStudio | 3.11.0+241b8abb4d | Version command exit 0; full energy run pending |
| EnergyPlus | EnergyPlus, Version 25.2.0-cf7368216c | Version command exit 0; full energy run pending |
| Radiance | RADIANCE 5.4 2023-11-05 LBNL (5.4.4ee32974b1) | Version exit 0; gendaymtx used by Ladybug sky matrix |
| OpenFOAM | UNVERIFIED | No confirmed executable/version; do not infer from Eddy3D presence |

Actual LBT installation root is `C:/Program Files/ladybug_tools`, not `C:/ladybug_tools`.

## Assets and MVP decision

Indexed 348 existing source/model/workflow/weather files; by extension: {'.py': 166, '.gh': 45, '.3dm': 52, '.cs': 69, '.ghx': 16}.
GHX component names were inspected. Binary GH files are UNKNOWN until individually read and runtime tested.
No working local radiation definition was established by this audit. There was no active definition to wrap.
Use the installed original LB Import EPW, LB Cumulative Sky Matrix, and LB Incident Radiation user objects to form the smallest slice.
Existing unrelated CAD, cinema, structural, and Revit assets remain UNKNOWN or outside this MVP; no changes were made to them.
The asset JSON records exclusions and any search access errors; this is not a claim to have executed every existing binary workflow.

## Verified vertical slice

Rhino 4m × 4m horizontal Brep snapshot → GH parameter → original Ladybug → Radiance sky matrix → 16 results → colored mesh and legend in Rhino.
Seattle-Tacoma bundled TMYx 2004–2018 EPW, annual period, north 0°, 1m grid (100cm), 1 CPU, Tregenza sky.
Mean/min/max: 1233.3471168086037 kWh/m². Repeat run per-value maximum difference: 0.
Mesh has 16 faces and 64 vertex colors. Viewport screenshot visually inspected.
This is a smoke fixture, not Taipei weather, a production adapter, or full scientific validation.

First solve produced no outputs because the new GH document was disabled. Enabled the same document and re-ran; no solver replacement.
Initial failure and successful transport receipts are retained.

## Git baseline

Parent repository exists on branch master but initially has no commits; all prior project folders are untracked.
No global safe.directory setting was changed; commands use a one-command safe.directory override.
Human author identity was not configured. Only this new Hub folder belongs to the milestone scope.
