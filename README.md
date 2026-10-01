# Environmental Simulation Hub

Phase 0 audit and first radiation vertical slice — **RUNTIME VERIFIED** on Rhino 8.35 / .NET 8.0.30.

Open `workflows/radiation/radiation_main.gh` in the inspected Rhino installation to see the original Ladybug workflow. The saved input is a 4m × 4m Brep snapshot from a Rhino object. The fixture uses bundled Seattle-Tacoma EPW data, annual cumulative radiation, north 0°, and 1m grid. It is not a Taipei project result.

The active Rhino session displays the result mesh and Ladybug legend. `samples/radiation_smoke/radiation_smoke.3dm` contains the input Brep and colored result mesh; its legend remains in the GH definition, not baked into that sample model. `runtime_result.json` stores all 16 physical values and their provenance. `rhino_preview.png` records the display.

Read `docs/ENVIRONMENT_AUDIT.md`, `docs/COMPONENT_INVENTORY.md`, and `docs/ROADMAP.md` before extending the workflow. Raw MCP evidence is retained in `docs/evidence/`.

The tools here are audit/fixture tooling. There is no production Rhino panel, AnalysisRequest adapter, cancellation service, or validated wind pipeline yet. UI work follows input validation and comparison fixtures.

Paths passed in `tools/*_calls.json` are captured environment-specific replay inputs. Configure them for another machine. Executable scripts receive their project/weather/component roots from the caller; no source copy of the Ladybug solver is maintained here.

To regenerate the audit from captured evidence, run `python tools/write_audit.py` in the verified environment. The original LBT components remain separately installed dependencies; their license notices and terms apply to company deployment.
