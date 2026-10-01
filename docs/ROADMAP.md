# Staged development plan

Status is based on acceptance evidence, not lines of code or an estimated overall percentage. Current priority is the complete original Ladybug scope. The live inventory covers 122 entries; this is not a claim that 122 Hub adapters have been implemented.

| Stage | Status | Acceptance / next gate |
| --- | --- | --- |
| 1. Runtime and component audit | Complete for documented scope | Installed Rhino/GH/Ladybug/Radiance inspected; stock radiation smoke executed. Binary assets and OpenFOAM remain unverified. |
| 2. Radiation contracts and adapter | Complete | Real stock components, preflight, normalized result/provenance and export. |
| 3. Radiation reliability validation | In progress | Three stock comparisons have delta 0; 25 Core checks and five execution gates passed. Null request and partial-preview rollback verified in native Eto. Additional real runtime checks passed: metre/centimetre/millimetre invariance, 82-cell closed Brep + triangular Mesh + shading comparison (delta 0), corrupt stock-archive cleanup, and disabled-solver blocking. Larger models and full external solver crash injection remain pending. |
| 4. Panel / UI UX | In progress | Five-step hierarchy, units, prior-result state, export and owned reset implemented. 0.3 native Eto execution and formal release registration / Dock loading passed. Theme, keyboard, dialogs and final narrow-dock visual QA pending. |
| 5. Wind / Eddy3D | Deferred by user priority | Preliminary metadata audit exists; actual CFD solver execution remains unverified. Resume after the Ladybug milestones. |
| 6. Integrated hub and deployment | In progress | Versioned packages and three-panel navigation exist. Unified operation modes, comparison, dependency/version compatibility and cross-machine deployment validation remain pending. |

Next sequence: finish the Ladybug module coverage in LADYBUG_DEVELOPMENT_PLAN.md, preserving the radiation reliability/UI gates, then return to Eddy3D. Each stage needs a build, real runtime evidence and explicit remaining limits before closure. No wind result or company deployment readiness is claimed. Radiation fixtures use Seattle weather, not a project-specific site study.

Current release: 0.6.0. L1 weather/time is in progress: original Import EPW, Construct Location, Import STAT and Import DDY are runtime verified. STAT/DDY full native outputs and design-day IDF match original three-city GH references. Half/quarter-hour UTC labels are fixed and verified. Independent time utilities and remaining L1 entries are pending. The package and loaded/registered-path evidence are described in BUILD_AND_RUN.md. A 4096-cell flat-surface radiation comparison has delta 0; complex-project capacity remains unverified. All future interfaces follow UI_UX_STANDARD.md. Prefer Rhino MCP and SDK APIs; minimize Computer Use.
