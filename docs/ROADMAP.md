# Staged development plan

Status is based on acceptance evidence, not lines of code or an estimated overall percentage. Two of six stages have completed their bounded acceptance scope; two are in progress and two have not started.

| Stage | Status | Acceptance / next gate |
| --- | --- | --- |
| 1. Runtime and component audit | Complete for documented scope | Installed Rhino/GH/Ladybug/Radiance inspected; stock radiation smoke executed. Binary assets and OpenFOAM remain unverified. |
| 2. Radiation contracts and adapter | Complete | Real stock components, preflight, normalized result/provenance and export. |
| 3. Radiation reliability validation | In progress | Three stock comparisons have delta 0; 25 Core checks and five execution gates passed. Null request and partial-preview rollback verified in native Eto. Additional real runtime checks passed: metre/centimetre/millimetre invariance, 82-cell closed Brep + triangular Mesh + shading comparison (delta 0), corrupt stock-archive cleanup, and disabled-solver blocking. Larger models and full external solver crash injection remain pending. |
| 4. Panel / UI UX | In progress | Five-step hierarchy, units, prior-result state, export and owned reset implemented. 0.3 native Eto execution and formal release registration / Dock loading passed. Theme, keyboard, dialogs and final narrow-dock visual QA pending. |
| 5. Wind / Eddy3D | Not started | Inspect a working definition and actual solver first; wrap only after stock execution succeeds; compare all outputs. |
| 6. Integrated hub and deployment | Not started | Operation modes, comparison, additional analyses, dependency/version compatibility and deployment validation. |

Next sequence: close stages 3 and 4, then inspect/wrap Eddy3D, then extend the hub. Each stage needs a build, real runtime evidence and explicit remaining limits before closure. No wind result or company deployment readiness is claimed. Radiation fixtures use Seattle weather, not a project-specific site study.

Current release: 0.3.0. The package and loaded/registered-path evidence are described in BUILD_AND_RUN.md. All future interfaces follow UI_UX_STANDARD.md. Prefer Rhino MCP and SDK APIs; minimize Computer Use.
