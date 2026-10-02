using System.Collections;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Text.Json;
using EnvironmentalHub.Core;
using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Parameters;
using Grasshopper.Kernel.Types;
using Rhino;

namespace EnvironmentalHub.Adapters;

public sealed class LadybugWeatherAdapter(string userObjectDirectory) : IWeatherAdapter
{
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true, WriteIndented = true };
    private static readonly Dictionary<string, double> MissingSentinels = new()
    {
        ["dry_bulb_temperature"] = 99.9, ["dew_point_temperature"] = 99.9,
        ["relative_humidity"] = 999, ["wind_speed"] = 999, ["wind_direction"] = 999,
        ["direct_normal_rad"] = 9999, ["diffuse_horizontal_rad"] = 9999,
        ["global_horizontal_rad"] = 9999, ["horizontal_infrared_rad"] = 9999,
        ["direct_normal_ill"] = 999999, ["diffuse_horizontal_ill"] = 999999,
        ["global_horizontal_ill"] = 999999, ["total_sky_cover"] = 99, ["barometric_pressure"] = 999999
    };
    public static string RunJson(string requestJson, string userObjectDirectory) => JsonSerializer.Serialize(
        new LadybugWeatherAdapter(userObjectDirectory).Execute(JsonSerializer.Deserialize<WeatherRequest>(requestJson, JsonOptions)!), JsonOptions);

    public WeatherResult Execute(WeatherRequest request)
    {
        if (RhinoApp.InvokeRequired) throw new InvalidOperationException("CLIMATE-THREAD-001: Execute on Rhino UI thread.");
        if (request is null || request.SchemaVersion != "1.0" || request.HoursOfYear is null)
            throw new InvalidOperationException("CLIMATE-CONTRACT-001: Invalid weather request.");
        if (!File.Exists(request.WeatherFile)) throw new InvalidOperationException("CLIMATE-EPW-003: Weather file missing.");
        if (request.HoursOfYear.Any(h => h < 0 || h >= 8760) || request.HoursOfYear.Distinct().Count() != request.HoursOfYear.Length)
            throw new InvalidOperationException("CLIMATE-PERIOD-001: Unique zero-based hours in 0..8759 required.");
        if (!GH_Document.EnableSolutions) throw new InvalidOperationException("CLIMATE-GH-001: Grasshopper solver disabled.");
        var path = Path.Combine(userObjectDirectory, "LB Import EPW.ghuser");
        if (!File.Exists(path)) throw new InvalidOperationException("CLIMATE-PLUGIN-001: LB Import EPW missing.");
        var timer = Stopwatch.StartNew();
        var weatherHash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(request.WeatherFile)));
        using var definition = new GH_Document();
        definition.Enabled = false;
        try
        {
            var component = (IGH_Component)new GH_UserObject(path).InstantiateObject();
            component.CreateAttributes(); definition.AddObject(component, false);
            var input = new Param_GenericObject(); input.CreateAttributes();
            input.SetPersistentData(new GH_ObjectWrapper(request.WeatherFile));
            definition.AddObject(input, false);
            component.Params.Input.Single(p => p.Name == "_epw_file").AddSource(input);
            Instances.DocumentServer.AddDocument(definition); definition.Enabled = true; definition.NewSolution(false);
            var errors = component.RuntimeMessages(GH_RuntimeMessageLevel.Error);
            if (errors.Count > 0) throw new InvalidOperationException("CLIMATE-SOLVER-001: " + string.Join("\n", errors));
            dynamic location = component.Params.Output.Single(p => p.Name == "location").VolatileData.AllData(true).Single().ScriptVariable();
            var place = new WeatherLocation((string)location.city, (string)location.country, (double)location.latitude,
                (double)location.longitude, (double)location.time_zone, (double)location.elevation,
                Convert.ToString(location.station_id) ?? "", Convert.ToString(location.source) ?? "");
            List<WeatherSeries> series = [];
            foreach (var output in component.Params.Output.Where(p => p.Name != "location"))
            {
                var index = 0;
                foreach (var goo in output.VolatileData.AllData(true))
                {
                    dynamic collection = goo.ScriptVariable();
                    var hourly = output.Name != "ground_temperature";
                    if (hourly && (bool)collection.header.analysis_period.is_leap_year)
                        throw new InvalidOperationException("CLIMATE-PERIOD-002: Leap EPW is not supported in this version.");
                    if (hourly && request.HoursOfYear.Length > 0)
                        collection = collection.filter_by_hoys(request.HoursOfYear);
                    double[] values = ((IEnumerable)collection.values).Cast<object>().Select(Convert.ToDouble).ToArray();
                    WeatherTime[] times = ((IEnumerable)collection.datetimes).Cast<dynamic>().Select(t =>
                        hourly ? new WeatherTime((int)t.month, (int)t.day, (int)t.hour, (int)t.minute, (double)t.hoy)
                               : new WeatherTime(Convert.ToInt32(t), 0, 0, 0, -1)).ToArray();
                    if (values.Length != times.Length || values.Any(v => !double.IsFinite(v)))
                        throw new InvalidOperationException("CLIMATE-RESULT-001: Invalid or unaligned weather values.");
                    if (hourly && request.HoursOfYear.Length == 0 && values.Length != 8760)
                        throw new InvalidOperationException("CLIMATE-PERIOD-002: Only 8760-hour non-leap EPW supported in this version.");
                    bool[] missing = values.Select(v => MissingSentinels.TryGetValue(output.Name, out var sentinel) && v == sentinel).ToArray();
                    var valid = values.Where((v, i) => !missing[i]).ToArray();
                    var stats = valid.Length == 0 ? null : new ResultStatistics(valid.Length, valid.Min(), valid.Max(), valid.Average());
                    var metadata = new Dictionary<string, string>();
                    foreach (DictionaryEntry entry in (IDictionary)collection.header.metadata)
                        metadata[Convert.ToString(entry.Key)!] = Convert.ToString(entry.Value, System.Globalization.CultureInfo.InvariantCulture) ?? "";
                    series.Add(new(output.Name, index++, (string)collection.header.data_type.name,
                        (string)collection.header.unit, hourly ? "Hourly" : "Monthly", metadata, values, missing, times, stats));
                }
            }
            if (!series.Any(s => s.Output == "dry_bulb_temperature")) throw new InvalidOperationException("CLIMATE-RESULT-001: Weather result empty.");
            var warnings = component.RuntimeMessages(GH_RuntimeMessageLevel.Warning).Select(m => new Diagnostic("WARNING", "CLIMATE-SOLVER-002", m)).ToList();
            if (request.HoursOfYear.Length > 0 && series.Any(s => s.Frequency == "Monthly"))
                warnings.Add(new("WARNING", "CLIMATE-MONTHLY-001", "Hourly selection leaves monthly ground-temperature collections unchanged."));
            if (series.Any(s => s.Missing.Any(m => m))) warnings.Add(new("WARNING", "CLIMATE-MISSING-001", "Missing EPW values retained with explicit masks; statistics exclude marked values."));
            if (weatherHash != Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(request.WeatherFile))))
                throw new InvalidOperationException("CLIMATE-INPUT-001: Weather file changed during import.");
            return new("1.0", place, series.ToArray(), request, new()
            {
                ["WeatherSha256"] = weatherHash, ["UserObjectSha256"] = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))),
                ["ComponentVersion"] = component.Message, ["Source"] = path,
                ["HourConvention"] = "Zero-based Ladybug HOY; monthly entries use month with HourOfYear=-1",
                ["StatisticConvention"] = "Arithmetic statistics over nonmissing values; wind direction is not a circular mean"
            }, warnings.ToArray(), timer.Elapsed.TotalSeconds, DateTimeOffset.UtcNow);
        }
        finally { Instances.DocumentServer.RemoveDocument(definition); }
    }
}
