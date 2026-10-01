# Development log

## 2026-10-01 — Phase 0 and original Ladybug radiation smoke

- DONE: Read actual environment; bounded explicit-slot Rhino MCP; runtime/plugin/component/solver/asset audits; stock radiation definition; Rhino-origin input snapshot, colored mesh, legend, 3dm fixture and viewport image.
- FILES CHANGED: New EnvironmentalSimulationHub directory only; existing projects unchanged.
- GH CHANGED: Added one new radiation_main.gh using three installed original Ladybug 1.10.0 user objects. New groups and fixture inputs; no existing user definition edited.
- TEST RESULT: RUNTIME VERIFIED. 16 finite radiation values, 16 mesh faces, 64 vertex colors, 3 legend items, no component error/warning, repeat max absolute difference 0. Viewport image inspected. Three persisted-evidence tests passed; filesystem scan returned 0 with no access errors after excluding temporary QA directories.
- ROOT CAUSE/FIX: Sandbox-only router SQLite write failed; authorized router execution worked. Default slot was stale; explicitly selected aardvark. New GH document was disabled; enabled the same document before solving. Incorrect LB Sky Matrix name was corrected to the live-discovered LB Cumulative Sky Matrix.
- KNOWN ISSUES: Seattle smoke weather only; native original-component repeatability is not independent scientific validation. No production request/result adapter, preflight, panel, reset or wind execution. Binary existing workflows remain UNKNOWN. OpenFOAM UNVERIFIED. Persisted fixture input is a snapshot rather than a live selection binding.
- GIT: Parent repository initially had no commits or configured human identity. Milestone uses a command-local Codex author identity and stages only the Hub folder; global Git settings remain unchanged. Commit completion must be verified separately.
- NEXT: Implement explicit radiation contracts and adapter/preflight, then perform stock-workflow numerical comparison before Eto UI.

## 2026-10-01 — C# adapter and minimal Eto panel

- DONE: .NET 8 Core contracts/preflight; Rhino/GH adapter using installed original LB components; actual gendaymtx path verification; geometry/weather hashes, typed mesh/result JSON; dockable panel and EnvironmentalHub command; mesh ownership/reset.
- FILES CHANGED: src/Core, src/Adapters, src/Plugin, runtime validation tooling/tests, configuration, documentation and evidence. Original radiation_main.gh/checkpoint unchanged.
- GH CHANGED: Adapter creates/disposes isolated definitions; no saved/active smoke workflow changes.
- TEST RESULT: Final RHP build 0 warnings/0 errors. 25 Core checks and 3 saved-evidence tests pass. Three stock/adapter comparisons (annual, shaded+rotated+24-hour, scaled geometry) have maximum per-value difference 0. Five invalid/warning execution cases block before output directory creation. Panel loaded/visible, request→adapter→mesh path, repeat and reset passed.
- ROOT CAUSE/FIX: Windows Forms implicit namespace imports conflicted with Eto; removed generated imports and qualified Font/Environment. Multi-project parallel MSBuild target evaluation failed without diagnostics; single-node build exposed compilation diagnostics and then passed. Already loaded DLLs are locked; separate development assembly names/output preserved the live Rhino session. No solver fallback.
- KNOWN ISSUES: Synchronous UI-thread execution; no progress/cancel. Picker/dialog clicks and visual panel QA pending. A later picker document-change guard fix is build verified in artifacts/next; the currently loaded runtime-v3 assembly remains locked and the guard needs a fresh Rhino session for runtime QA. Full failure injection/complex-geometry/runtime unit-change validation pending. Seattle fixtures only; wind and company deployment pending.
- NEXT: Strengthen execution failure handling, progress/cancel and reproducible project geometry fixtures, then inspect a real Eddy3D workflow.
