using System.Security.Cryptography;
using System.Text.Json;
using EnvironmentalHub.Core;
using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Parameters;
using Grasshopper.Kernel.Types;
using Rhino;

namespace EnvironmentalHub.Adapters;

public sealed class LadybugLocationAdapter(string userObjectDirectory)
{
    public static string RunJson(string json, string folder) => JsonSerializer.Serialize(
        new LadybugLocationAdapter(folder).Execute(JsonSerializer.Deserialize<LocationRequest>(json)!));
    public LocationResult Execute(LocationRequest request)
    {
        if (RhinoApp.InvokeRequired) throw new InvalidOperationException("CLIMATE-THREAD-001: Execute on Rhino UI thread.");
        if (request is null || request.SchemaVersion != "1.0" || request.Name is null)
            throw new InvalidOperationException("CLIMATE-CONTRACT-001: Invalid location request.");
        if (!double.IsFinite(request.Latitude) || Math.Abs(request.Latitude) > 90 ||
            !double.IsFinite(request.Longitude) || Math.Abs(request.Longitude) > 180 ||
            !double.IsFinite(request.ElevationMetres) ||
            request.TimeZone is double zone && (!double.IsFinite(zone) || Math.Abs(zone) > 12))
            throw new InvalidOperationException("CLIMATE-LOCATION-001: Latitude -90..90, longitude -180..180, time zone -12..12 and finite elevation required.");
        if (!GH_Document.EnableSolutions) throw new InvalidOperationException("CLIMATE-GH-001: Grasshopper solver disabled.");
        var path = Path.Combine(userObjectDirectory, "LB Construct Location.ghuser");
        if (!File.Exists(path)) throw new InvalidOperationException("CLIMATE-PLUGIN-001: LB Construct Location missing.");
        var hash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)));
        using var definition = new GH_Document(); definition.Enabled = false;
        try
        {
            var component = (IGH_Component)new GH_UserObject(path).InstantiateObject();
            component.CreateAttributes(); definition.AddObject(component, false);
            void Bind(string name, object? value)
            {
                if (value is null) return;
                var input = new Param_GenericObject(); input.CreateAttributes(); input.SetPersistentData(new GH_ObjectWrapper(value));
                definition.AddObject(input, false); component.Params.Input.Single(p => p.Name == name).AddSource(input);
            }
            Bind("_name_", request.Name); Bind("_latitude_", request.Latitude); Bind("_longitude_", request.Longitude);
            Bind("_time_zone_", request.TimeZone); Bind("_elevation_", request.ElevationMetres);
            Instances.DocumentServer.AddDocument(definition); definition.Enabled = true; definition.NewSolution(false);
            var errors = component.RuntimeMessages(GH_RuntimeMessageLevel.Error);
            if (errors.Count > 0) throw new InvalidOperationException("CLIMATE-SOLVER-001: " + string.Join("\n", errors));
            dynamic native = component.Params.Output.Single(p => p.Name == "location").VolatileData.AllData(true).Single().ScriptVariable();
            var place = new WeatherLocation((string)native.city, (string)native.country, (double)native.latitude,
                (double)native.longitude, (double)native.time_zone, (double)native.elevation,
                Convert.ToString(native.station_id) ?? "", Convert.ToString(native.source) ?? "");
            if (hash != Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))))
                throw new InvalidOperationException("CLIMATE-INPUT-001: Component changed during execution.");
            var warnings = component.RuntimeMessages(GH_RuntimeMessageLevel.Warning).Select(m => new Diagnostic("WARNING", "CLIMATE-SOLVER-002", m)).ToList();
            if (request.TimeZone is null) warnings.Add(new("WARNING", "CLIMATE-LOCATION-002", "Time zone estimated by original Ladybug from longitude; verify the civil time zone before analysis."));
            return new("1.0", place, request, new() { ["Source"] = path, ["UserObjectSha256"] = hash,
                ["ComponentVersion"] = component.Message }, warnings.ToArray());
        }
        finally { Instances.DocumentServer.RemoveDocument(definition); }
    }
}
