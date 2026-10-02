# Location — 0.5.0

Run `EnvironmentalLocation`, or choose Construct location from the Weather Panel. Enter name, latitude/longitude in degrees, UTC offset in hours and elevation in metres; construct and export the actual JSON result. Inputs changing mark the result as previous; failures preserve it.

The isolated adapter executes the installed original `LB Construct Location`. A null TimeZone leaves the native input unbound, allowing Ladybug to estimate it from longitude. The result warns that this estimate must be checked against the civil time zone. Country/state/source are native defaults, not inferred geographical metadata. This tool creates a location; it does not generate weather or replace the radiation EPW input.

Current contract: schema 1.0, latitude -90..90, longitude -180..180, optional time zone -12..12 and finite elevation. The UI elevation input is bounded to -100000..100000 m. Explicit half/quarter-hour offsets are retained. UTC labels use invariant decimal hours (UTC+5.5 = UTC+5:30; UTC+5.75 = UTC+5:45), including negative offsets. Weather Panel shares this formatter.

Acceptance in evidence/release_050_loaded.json:

- Six independent original Construct Location → Deconstruct Location comparisons: Taipei, positive/negative half-hour, quarter-hour, native estimate and defaults. All names/coordinates/time zones/elevations match.
- Five invalid requests blocked: latitude, longitude, time zone, null and schema.
- Eight UTC formatting checks in en-US/fr-FR pass. Real EPW half-hour fixture renders correctly in Weather Panel.
- Formal Location Panel loaded and visible; a failed construct preserves the previous result. GH document count restores.
- Weather field/custom-hour/failure behavior and true radiation regression pass on 0.5.0.

Build: zero warnings/errors. Registered and loaded paths point to the formal 0.5.0 package. This is native functional/API verification; theme, keyboard, dialogs and narrow-Dock visual acceptance remain open. Original Deconstruct Location is used for test reference only; its standalone Hub feature remains pending. L1 STAT/DDY and independent time utilities are next.
