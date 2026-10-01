# Environmental Simulation Hub development rules

User direction: every subsequent interface must have high-quality UI/UX, clear logic and considered visual presentation.

- Follow docs/UI_UX_STANDARD.md for new panels and interface changes.
- Keep real Rhino/Eto interactions on the request → preflight → adapter → result path. Preserve original solver behavior; never fabricate simulation values.
- Present model, climate, settings, validation and results in a clear sequence with explicit units, concise labels and restrained hierarchy.
- Show actual execution state, actionable diagnostics and honest limitations. Never imply unavailable cancellation or percentage progress.
- Distinguish previous results from current inputs. Preserve useful results after validation or solver failure; delete only panel-owned preview objects.
- Build changed code and record verification scope. Build success is not native UI or solver runtime verification.
- Inspect actual Rhino layout at narrow/wide dock widths and supported themes before declaring visual QA complete.

- User preference: minimize Computer Use. Prefer Rhino MCP, documented SDK APIs and file-based verification. Use native UI automation only when necessary to resolve a specific interaction/visual issue.

- Current user priority: complete the original Ladybug feature scope first. Keep all 122 installed entries in the feature catalog with per-function integration/verification states; defer wind CFD adapter work until the Ladybug milestones are addressed.
