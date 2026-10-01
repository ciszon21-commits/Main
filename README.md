# Environmental Simulation Hub

Original Ladybug radiation and EPW weather backends, typed C# adapters and Rhino dockable panels — **RUNTIME VERIFIED** on Rhino 8.35 / .NET 8.0.30.

Run Rhino command `EnvironmentalHub` to open the loaded panel. Select analysis geometry, optional context and an EPW; set grid/north; run Preflight, review warnings, and Run. Results appear as colored Rhino mesh plus numerical statistics in the panel. Reset removes only objects created by that panel instance.

The local plugin is `artifacts/releases/0.5.0/EnvironmentalHub.Plugin.rhp`. Build and loading instructions are in `docs/BUILD_AND_RUN.md`. Release 0.5.0 has been registered and loaded in a fresh Rhino process. Run `EnvironmentalWeather` for climate fields and hourly selection; `EnvironmentalHub` opens radiation. Execution is synchronous. Existing Rhino processes retain their loaded version until restarted.

Open `workflows/radiation/radiation_main.gh` in the inspected Rhino installation to see the original Ladybug workflow. The saved input is a 4m × 4m Brep snapshot from a Rhino object. The fixture uses bundled Seattle-Tacoma EPW data, annual cumulative radiation, north 0°, and 1m grid. It is not a Taipei project result.

The active Rhino session displays the result mesh and Ladybug legend. `samples/radiation_smoke/radiation_smoke.3dm` contains the input Brep and colored result mesh; its legend remains in the GH definition, not baked into that sample model. `runtime_result.json` stores all 16 physical values and their provenance. `rhino_preview.png` records the display.

Read `docs/ENVIRONMENT_AUDIT.md`, `docs/COMPONENT_INVENTORY.md`, and `docs/ROADMAP.md` before extending the workflow. Raw MCP evidence is retained in `docs/evidence/`.

The tools directory contains audit/fixture tooling; compiled code lives in `src/`. Core contracts have no Rhino/GH dependencies. The adapter constructs an isolated definition from installed original user objects, never modifies the smoke canvas, and verifies the actual gendaymtx executable used by Ladybug. Cancellation/progress and wind are not implemented yet.

Paths passed in `tools/*_calls.json` are captured environment-specific replay inputs. Configure them for another machine. Executable scripts receive their project/weather/component roots from the caller; no source copy of the Ladybug solver is maintained here.

To regenerate the audit from captured evidence, run `python tools/write_audit.py` in the verified environment. The original LBT components remain separately installed dependencies; their license notices and terms apply to company deployment.

Full original Ladybug scope: [122-entry feature table](docs/LADYBUG_FEATURE_TABLE.md) and searchable [HTML catalog](docs/LADYBUG_FEATURE_TABLE.html). Standalone radiation, EPW weather and Construct Location are verified; the remaining functions are tracked individually. [Weather semantics and evidence](docs/WEATHER_MODULE.md).

Run EnvironmentalLocation for the original Ladybug location tool; half/quarter-hour UTC display is preserved in both location and weather panels. See docs/LOCATION_MODULE.md.
