using EnvironmentalHub.Core;
using System.Text.Json;

if (args.Length != 2) throw new ArgumentException("Pass a real EPW and a test output directory.");
var id = Guid.NewGuid();
var request = new RadiationAnalysisRequest { GeometryIds = [id], WeatherFile = args[0], OutputDirectory = Path.GetFullPath(args[1]) };
var facts = new EnvironmentFacts(0.01, true, [new(id, true, true, true, 4)], [], true, true);
List<string> passed = [];
void Test(string name, RadiationAnalysisRequest r, EnvironmentFacts f, string? error = null)
{
    var result = RadiationPreflight.Check(r, f);
    if (error is null ? !result.CanRun : result.CanRun || !result.Diagnostics.Any(d => d.Code == error && d.Severity == "ERROR"))
        throw new Exception(name + " failed: " + JsonSerializer.Serialize(result));
    passed.Add(name);
}
Test("valid real EPW", request, facts);
Test("missing geometry", request with { GeometryIds = [] }, facts, "RAD-INPUT-001");
Test("overlapping context", request with { ContextIds = [id] }, facts, "RAD-INPUT-004");
Test("missing Rhino object", request, facts with { Geometry = [new(id, false, false, false, 0)] }, "RAD-INPUT-002");
Test("invalid geometry", request, facts with { Geometry = [new(id, true, false, true, 4)] }, "RAD-INPUT-003");
Test("unsupported curve", request, facts with { Geometry = [new(id, true, true, false, 4)] }, "RAD-INPUT-003");
Test("undefined units", request, facts with { UnitsDefined = false }, "RAD-UNIT-001");
Test("bad conversion", request, facts with { MetresPerUnit = double.NaN }, "RAD-UNIT-001");
Test("zero scale", request, facts with { Geometry = [new(id, true, true, true, 0)] }, "RAD-SCALE-001");
Test("millimetres", request, facts with { MetresPerUnit = 0.001 });
Test("missing EPW", request with { WeatherFile = "missing.epw" }, facts, "CLIMATE-EPW-003");
Test("missing plugin", request, facts with { ComponentsAvailable = false }, "RAD-PLUGIN-001");
Test("missing solver", request, facts with { SolverAvailable = false }, "RAD-SOLVER-001");
Test("zero grid", request with { GridMetres = 0 }, facts, "RAD-PARAM-001");
Test("infinite grid", request with { GridMetres = double.PositiveInfinity }, facts, "RAD-PARAM-001");
Test("invalid north", request with { NorthDegrees = 361 }, facts, "RAD-PARAM-002");
Test("out of year", request with { HoursOfYear = [8760] }, facts, "RAD-PERIOD-001");
Test("duplicate hour", request with { HoursOfYear = [1, 1] }, facts, "RAD-PERIOD-001");
Test("bad offset", request with { Settings = new() { OffsetMetres = 0 } }, facts, "RAD-PARAM-003");
Test("invalid reflectance", request with { Settings = new() { GroundReflectance = 2 } }, facts, "RAD-PARAM-003");
Test("invalid cpu", request with { Settings = new() { CpuCount = 0 } }, facts, "RAD-PARAM-003");
Test("relative output", request with { OutputDirectory = "relative" }, facts, "RAD-OUTPUT-001");
Test("unknown schema", request with { SchemaVersion = "2" }, facts, "RAD-CONTRACT-001");
Test("null contract", request with { Settings = null! }, facts, "RAD-CONTRACT-002");
Directory.CreateDirectory(args[1]);
var badWeather = Path.Combine(args[1], "invalid.epw");
File.WriteAllText(badWeather, "not an EPW");
Test("malformed EPW", request with { WeatherFile = badWeather }, facts, "CLIMATE-EPW-003");
var warning = RadiationPreflight.Check(request, facts);
if (!warning.HasWarnings || !warning.CanRun) throw new Exception("No-context warning must not become an error.");
Console.WriteLine(JsonSerializer.Serialize(new { Passed = passed.Count, Cases = passed }, new JsonSerializerOptions { WriteIndented = true }));
