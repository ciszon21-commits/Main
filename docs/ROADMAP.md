# Staged development plan

Status is based on acceptance evidence, not lines of code or an estimated overall percentage. Current priority is the complete original Ladybug scope. The live inventory covers 122 entries; this is not a claim that 122 Hub adapters have been implemented.

| Stage | Status | Acceptance / next gate |
| --- | --- | --- |
| 1. Runtime and component audit | Complete for documented scope | Installed Rhino/GH/Ladybug/Radiance inspected; stock radiation smoke executed. Binary assets and OpenFOAM remain unverified. |
| 2. Radiation contracts and adapter | Complete | Real stock components, preflight, normalized result/provenance and export. |
| 3. Radiation reliability validation | In progress | Three stock comparisons have delta 0; 25 Core checks and five execution gates passed. Null request and partial-preview rollback verified in native Eto. Additional real runtime checks passed: metre/centimetre/millimetre invariance, 82-cell closed Brep + triangular Mesh + shading comparison (delta 0), corrupt stock-archive cleanup, and disabled-solver blocking. Larger models and full external solver crash injection remain pending. |
| 4. Panel / UI UX | In progress | Six-stage solar workflow, shared ruled design system across six panels, advanced settings, KPIs, exact color samples, criteria and viewport focus implemented. Current-theme 320/480 native offscreen rendering is recorded separately. Full Dock/theme/keyboard/dialog acceptance and verified async progress/cancel remain pending. |
| 5. Wind / Eddy3D | Deferred by user priority | Preliminary metadata audit exists; actual CFD solver execution remains unverified. Resume after the Ladybug milestones. |
| 6. Integrated hub and deployment | In progress | Six-panel overview/navigation, explicit completed-weather/time transfer, named session comparison and provenance export implemented. Persistent scenario-library import, additional simulation engines, dependency compatibility and cross-machine deployment remain pending. |

Next sequence: finish the Ladybug module coverage in LADYBUG_DEVELOPMENT_PLAN.md, preserving the radiation reliability/UI gates, then return to Eddy3D. Each stage needs a build, real runtime evidence and explicit remaining limits before closure. No wind result or company deployment readiness is claimed. Radiation fixtures use Seattle weather, not a project-specific site study.

Current release: 0.8.5. Original EPW, Construct Location, STAT/DDY and three time utilities are runtime verified. The Hub overview and shared navigation integrate five workflows, with module-specific state preserved. Native time comparisons cover annual, cross-year, overnight, subhour and date conversion. Production Eto layouts are captured at 320/480 offscreen viewports; full host Dock/theme/keyboard/dialog acceptance remains separate. Remaining L1 location/data utilities are next. A 4096-cell flat-surface radiation comparison has delta 0; complex-project capacity remains unverified. All interfaces follow UI_UX_STANDARD.md. Prefer Rhino MCP and SDK APIs; minimize Computer Use.

## Interface release strategy

- V1: retain the current native Rhino/Eto panel framework while completing the Ladybug function milestones. Improve information hierarchy, theme colors, vector icons, spacing, validation, result presentation and consistent navigation within that framework. Version 0.8.5 is a presentation refinement; coverage remains eight independently integrated entries, one backend-only entry and 113 pending entries out of 122.
- V2: after the major function milestones are complete and accepted, plan the larger visual and interactive interface, including broader viewport interaction, scenario exploration and richer result navigation. This is a future design/development phase, not an implemented screen or a reason to replace the V1 framework now. Preserve the original solver and contract boundaries when it starts.
