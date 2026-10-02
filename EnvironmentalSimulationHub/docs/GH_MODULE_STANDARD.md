# Grasshopper module standard

One independent definition per analysis. Planned stages are 00_INPUT, 10_PREPROCESS, 20_GEOMETRY, 30_ANALYSIS, 40_SOLVER, 50_POSTPROCESS, 60_RESULT, 70_VISUALIZATION, and 80_EXPORT.

The Phase 0 smoke definition contains 00_INPUT, 10_PREPROCESS, and 40_SOLVER groups only. Result and visualization currently use the stock component outputs. Expand stages only when responsibilities are implemented.

Use verified input/output names and real component GUIDs from COMPONENT_INVENTORY.md. Never rely on canvas positions or slider indices. Production adapter endpoints must be explicit and versioned.

Preserve original Ladybug components. Geometry snapshots carry document units; grid metre values are converted before reaching Ladybug. North convention is the Ladybug counterclockwise angle from +Y. Record actual sky density, CPU count, period, offset and ground reflectance rather than a quality label alone.

Create a definition with solving disabled while wiring; enable the document explicitly before requesting a solution. UI parameter edits do not implicitly run heavy simulations. Execution is an explicit action on the intended document and Rhino slot.

Before any change to a verified definition, save a checkpoint. The Phase 0 checkpoint is `docs/evidence/radiation_verified_checkpoint.gh`. Do not replace user documents or silently open/solve unrelated workflows.

Verify finite values, mesh-to-value alignment, legend output, error messages and numerical comparisons. A successful viewport screenshot alone is insufficient scientific validation.
