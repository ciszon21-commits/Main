# Architecture

## Current platform — 0.8.5

EnvironmentalHub opens the overview. EnvironmentalRadiation, EnvironmentalWeather, EnvironmentalLocation, EnvironmentalClimate and EnvironmentalTime open five workflows in six native Eto panels. Weather/location/climate/time adapters also use typed Core contracts and isolated original components. Shared HubUi/HubVisuals own presentation; result comparison and viewport actions retain normalized provenance and owned-preview scope. Current state and limits: [PROJECT_STATUS](PROJECT_STATUS.md); decisions: [DECISIONS](DECISIONS.md).

## Original verified radiation slice

Rhino object geometry snapshot → GH Brep parameter → LB Import EPW → LB Cumulative Sky Matrix (Radiance gendaymtx) → LB Incident Radiation (original Ladybug ray intersections) → values, colored mesh, legend → Rhino preview.

This phase proves the physics backend can execute. The three installed original Ladybug user objects are KEEP. The new definition is WRAP. The existing MCP transport is WRAP with bounded waits and explicit slot targeting. Other binary workflows are UNKNOWN until inspected separately.

The current GH panels are fixture inputs. There is no UI-to-slider coupling. They must not become the platform API.

## Implemented request/adapter boundary (0.2.0)

Rhino Panel → RadiationAnalysisRequest → Preflight → RadiationAdapter → isolated GH definition → existing simulation libraries → AnalysisResult → Rhino result renderer.

Core contracts will not depend on Grasshopper types. The adapter owns Rhino/GH geometry conversion, named workflow interfaces, unit conversion, GH scheduling, and source-result translation. UI owns selection and status. It must not parse Ladybug-specific objects.

`src/EnvironmentalHub.Core` implements RadiationAnalysisRequest, RadiationSettings, PreflightReport, AnalysisResult and IRadiationAdapter. The request carries analysis/context object IDs, EPW path, north, explicit hours (empty = annual), grid in metres, settings, output directory and warning acceptance. Geometry/weather hashes and EPW location are recorded in result metadata after snapshotting.

Result includes source geometry IDs, portable mesh vertex/face/color arrays, values, sample points, empty radiation vectors, units, legend range/colors, statistics, solver/version, workflow version, input parameters, metadata, warnings/errors, duration and UTC timestamp. Mesh/point coordinates use the recorded Rhino model units.

`src/EnvironmentalHub.Adapters` snapshots valid Rhino Breps/Meshes and binds named typed GH parameters. It uses original installed Ladybug user objects, isolates and disposes its GH document, verifies actual SkyMatrix gendaymtx executable provenance, and serializes the normalized result. It requires the target Rhino document to be active because Ladybug unit conversion uses active-document state. Execution runs on the Rhino UI thread.

`src/EnvironmentalHub.Plugin` registers EnvironmentalHub for the overview and EnvironmentalRadiation for the Eto dockable RadiationPanel, plus supporting environment commands. UI selects object IDs and calls the typed adapter; it does not locate sliders or parse native Ladybug data. It renders portable result meshes and owns the IDs needed for reset.

Preflight errors block execution. Warnings require an explicit user decision; an unattended caller must explicitly set AcceptWarnings. Current EPW validation supports 8760 non-leap hourly records; leap/subhourly files are rejected. Output write failures may still arise at execution time. Cancellation/cache remain future concerns; no large job framework is introduced now.

Wind/Eddy3D has preliminary metadata inspection only; no CFD solve is verified. It is deferred until the Ladybug milestones. OpenFOAM availability remains UNVERIFIED. Daylight, energy and carbon are planned additional engines, not completed Ladybug workflows. V1 retains Rhino/Eto; V2 larger visual interaction follows major functional acceptance.

Company deployment needs dependency discovery, version compatibility checks, portable workflow bindings, and review of installed Ladybug licensing. No bundled/reimplemented solver is part of this repository.
