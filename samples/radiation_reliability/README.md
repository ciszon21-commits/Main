# Radiation reliability fixture

`mixed_brep_mesh_result.json` contains real Ladybug outputs for a 4×4×3 m closed Brep, a sloping two-triangle Mesh and a shading wall. The Seattle EPW, north 35°, grid 1 m and hours 4000..4023 produce 82 cells. Every value matches the independently bound original GH definition (maximum absolute difference 0).

Source GUIDs are temporary and were deleted after testing. Recreate the geometry and requests with `tools/validate_radiation_reliability.py` in a dedicated empty Rhino document; do not assume the recorded GUIDs still exist. The test restores document units and removes only its owned geometry. This is a small deterministic reference, not a project site analysis or large-model certification.
