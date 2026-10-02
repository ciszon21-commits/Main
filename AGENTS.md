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

- Current user priority: complete the original Ladybug feature scope first. Keep all 122 installed entries in the feature catalog with per-function integration/verification states; defer wind CFD adapter work until the Ladybug milestones are addressed.

- Knowledge management: read docs/KNOWLEDGE_INDEX.md, PROJECT_STATUS.md and the relevant ROADMAP/Ladybug batch before new work. Keep current status, historical logs and versioned acceptance evidence distinct.
- On a feature delivery, update catalog JSON/Markdown/HTML, current status and evidence together. UI/documentation-only changes do not increase function coverage. Keep historical receipts unchanged.
- The user-designated Notion knowledge database is indexed in docs/NOTION_KNOWLEDGE.md. Use stable record IDs and the verified destination/schema; preserve the distinction between inventory, integration and acceptance. Do not create duplicate databases on later updates.
