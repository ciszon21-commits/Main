# Architecture

## Current verified slice

Rhino object geometry snapshot → GH Brep parameter → LB Import EPW → LB Cumulative Sky Matrix (Radiance gendaymtx) → LB Incident Radiation (original Ladybug ray intersections) → values, colored mesh, legend → Rhino preview.

This phase proves the physics backend can execute. The three installed original Ladybug user objects are KEEP. The new definition is WRAP. The existing MCP transport is WRAP with bounded waits and explicit slot targeting. Other binary workflows are UNKNOWN until inspected separately.

The current GH panels are fixture inputs. There is no UI-to-slider coupling. They must not become the platform API.

## Next production boundary

Rhino Panel → RadiationAnalysisRequest → Preflight → RadiationAdapter → isolated GH definition → existing simulation libraries → AnalysisResult → Rhino result renderer.

Core contracts will not depend on Grasshopper types. The adapter owns Rhino/GH geometry conversion, named workflow interfaces, unit conversion, GH scheduling, and source-result translation. UI owns selection and status. It must not parse Ladybug-specific objects.

Radiation request: analysis/context object references, geometry snapshot/hash, EPW path/hash and location, north, analysis period, grid in metres, actual quality parameters, solver settings and workflow version.

Result: analysis type, geometry/result mesh/values/vectors, units, legend, min/max/mean, solver/version, workflow version, input parameters, warning/error codes, execution duration and timestamp. These contracts are design intent, not implemented or runtime verified in Phase 0.

Preflight errors block execution. Warnings require an explicit user decision. Cancellation/cache remain interface concerns until the minimum adapter works; no large job framework is introduced now.

Wind uses an existing verified Eddy3D workflow after radiation is stable. OpenFOAM availability remains UNVERIFIED. Energy/daylight/RiR/AI chat are outside this phase.

Company deployment needs dependency discovery, version compatibility checks, portable workflow bindings, and review of installed Ladybug licensing. No bundled/reimplemented solver is part of this repository.
