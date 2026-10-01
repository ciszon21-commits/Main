# Weather module — 0.4.0

Rhino command `EnvironmentalWeather` opens the native Eto panel. Select an EPW, annual or an hourly range, import, select a field, and export the actual full JSON if needed. `EnvironmentalHub` opens radiation; both panels have navigation buttons.

The adapter executes the installed original `LB Import EPW` in an isolated GH document. It preserves every original data output rather than claiming every raw EPW column is exposed by that component. The tested Seattle EPW produces a location and 18 collections: 15 hourly fields and three monthly ground-temperature collections. Ground collection counts/depths follow the input file; header metadata is retained.

| Original output | Unit | Frequency |
| --- | --- | --- |
| dry_bulb_temperature | C | Hourly |
| dew_point_temperature | C | Hourly |
| relative_humidity | % | Hourly |
| wind_speed | m/s | Hourly |
| wind_direction | degrees | Hourly |
| direct_normal_rad | Wh/m2 | Hourly |
| diffuse_horizontal_rad | Wh/m2 | Hourly |
| global_horizontal_rad | Wh/m2 | Hourly |
| horizontal_infrared_rad | W/m2 | Hourly |
| direct_normal_ill | lux | Hourly |
| diffuse_horizontal_ill | lux | Hourly |
| global_horizontal_ill | lux | Hourly |
| total_sky_cover | tenths | Hourly |
| barometric_pressure | Pa | Hourly |
| model_year | yr | Hourly |
| ground_temperature (each depth) | C | Monthly |

## Time, missing values and statistics

`WeatherRequest.HoursOfYear` is an array of unique zero-based integer hours, 0–8759. Empty selects annual. Zero is January 1 at 00:00 local standard time, with no daylight-saving conversion. The adapter uses the native collection's `filter_by_hoys`; native instantaneous/radiation alignment is preserved. API custom/noncontiguous hours survive panel import; editing the range replaces the custom selection.

Monthly ground-temperature collections remain unchanged under hourly selection, with an explicit warning. Their time entries retain month, with HourOfYear -1 and day/hour/minute zero. This release rejects leap-year or incomplete hourly collections.

Known EPW missing sentinels remain in `Values`, with a parallel `Missing` mask. Statistics exclude marked entries; all-missing statistics are null. No interpolation or invented replacement value is applied. The panel suppresses arithmetic means for wind direction and model year; exported generic statistics are arithmetic, not a circular wind metric. Source EPW/user-object hashes, executed component version, units and header metadata accompany the result.

Imports validate the request and source file and restore GH document ownership on failure. A failed import retains the previous usable result. Execution is synchronous on Rhino's UI thread; native picker/export dialogs and complete theme/keyboard/narrow-dock visual acceptance remain pending.

## Verified acceptance

- [Weather runtime receipt](evidence/weather_runtime_validation.json): eight cases passed. Annual, 24-hour and year-boundary values have maximum difference 0 against independently deconstructed original GH outputs; units/times match. Four invalid inputs blocked, and missing-value masking/all-missing statistics passed. GH document count restored.
- [Formal release receipt](evidence/release_040_loaded.json): actual registered/loaded 0.4.0 assembly, visible Weather Panel, field/monthly selection, suppressed wind mean, custom hours and failure preservation passed. Radiation regression mean remains 1233.3471168086037 kWh/m2.
- [Real selected-hour result](../samples/weather/selected_24h.json): typed values and provenance from bundled Seattle weather. This fixture is not a project-specific climate study.

L1 remains in progress. STAT/DDY, independent Location and Analysis Period/HOY tools are next; reference GH deconstructor components used in tests are not claimed as standalone Hub features.
