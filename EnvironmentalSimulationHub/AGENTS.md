# Environmental Simulation Hub development rules

User direction: every subsequent interface must have high-quality UI/UX, clear logic and considered visual presentation.

- User-facing UI is Traditional Chinese (zh-TW). Use Chinese navigation, controls, status, validation and summaries; HubText maps native field labels and diagnostic presentation. Preserve command names, native identifiers, scientific units, raw values and JSON contract keys. Retain unknown original diagnostics rather than guessing their meaning.

- Follow docs/UI_UX_STANDARD.md for new panels and interface changes.
- Keep real Rhino/Eto interactions on the request → preflight → adapter → result path. Preserve original solver behavior; never fabricate simulation values.
- Present model, climate, settings, validation and results in a clear sequence with explicit units, concise labels and restrained hierarchy.
- Show actual execution state, actionable diagnostics and honest limitations. Never imply unavailable cancellation or percentage progress.
- Distinguish previous results from current inputs. Preserve useful results after validation or solver failure; delete only panel-owned preview objects.
- Build changed code and record verification scope. Build success is not native UI or solver runtime verification.
- Inspect actual Rhino layout at narrow/wide dock widths and supported themes before declaring visual QA complete.

- User preference: minimize Computer Use. Prefer Rhino MCP, documented SDK APIs and file-based verification. Use native UI automation only when necessary to resolve a specific interaction/visual issue.

- Current user priority (2026-10-05): follow docs/MULTI_VISUAL_MVP_PLAN_2026-10-05.md. Prioritize a multi-function visual MVP: solar hours/radiation, time-specific shadows, wind rose, hourly/monthly charts and outdoor radiant-temperature interpretation. Bring the Eddy3D engine/baseline feasibility gate forward; after it passes, implement a single-direction visual wind workflow without waiting for all Ladybug milestones. Defer detailed numerical utility pages, exhaustive options and Solar Envelope; retain necessary typed data, units, provenance and native validation. Keep all 122 Ladybug entries and honest per-function states; weather wind statistics are not CFD, solar radiation is not surface temperature or MRT.

- Knowledge management: read docs/KNOWLEDGE_INDEX.md, PROJECT_STATUS.md and the relevant ROADMAP/Ladybug batch before new work. Keep current status, historical logs and versioned acceptance evidence distinct.
- User reporting preference (2026-10-03): update stage results, development progress and knowledge records when there is actual progress, and report in Traditional Chinese. Without a meaningful change, do not send routine reports or change document dates. On milestone completion, new test evidence or a changed blocker, record the evidence and next step.
- Keep local knowledge documents and the existing Notion knowledge database updated together when progress occurs. Candidate progress and open validation gates must also be recorded in Notion without promoting formal acceptance. Reuse stable IDs, fetch before edits, verify readback and save a dated local synchronization receipt; report any failed or pending synchronization explicitly.
- Notion presentation (2026-10-03): maintain three linked layers: detailed records in the existing database, key progress and next steps on the existing hub page, and a stable visual highlights record with milestone/process diagrams. Keep local counterparts updated; reuse KB-003 for visual highlights, preserve historical evidence, and do not duplicate databases or create routine updates without meaningful progress.
- On a feature delivery, update catalog JSON/Markdown/HTML, current status and evidence together. UI/documentation-only changes do not increase function coverage. Keep historical receipts unchanged.
- The user-designated Notion knowledge database is indexed in docs/NOTION_KNOWLEDGE.md. Use stable record IDs and the verified destination/schema; preserve the distinction between inventory, integration and acceptance. Do not create duplicate databases on later updates.

- Notion homepage direction (2026-10-05): keep MCP AI開發 as clean multi-project card navigation. Environmental Hub reports belong in the existing project card `3f01956a-9b0e-81f0-a52f-c11e84c1d86c` and its existing knowledge database/records, not as long updates on the shared homepage. Its migrated homepage history is the child page `3f01956a-9b0e-8139-adf2-f98050403812`; preserve that archive and other projects' cards. Update the project summary and linked records when actual progress occurs.

- Register only HubWorkspacePanel with Rhino. New features belong to cached internal views; route commands/navigation inside the same workspace. Preserve draft inputs, completed results and scenarios during navigation; do not create independent Dock panels per module.

- UI exploration (2026-10-05): consider the hybrid Eto shell plus Eto.Forms.WebView strategy in docs/WEBVIEW_UI_STRATEGY_2026-10-05.md. Start with a bounded read-only chart/result proof of concept using local assets; preserve native selection, C# state authority and the existing solver path. WebView API presence is not runtime/Dock acceptance; do not migrate the whole UI or claim Mac compatibility before the corresponding gates pass.

- CFD: evaluate Eddy3D as the preferred candidate in the early MVP feasibility gate; verify actual deployment, engine, boundary conditions, convergence, baseline results and visual output before declaring CFD available. Do not make unverified wind fields or let a failed engine gate erase the other accepted MVP workflows. Reference sources are indexed in docs/REFERENCE_INDEX.md.
