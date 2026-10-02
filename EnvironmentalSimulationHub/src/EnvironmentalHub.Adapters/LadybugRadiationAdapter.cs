using System.Diagnostics;
using System.Drawing;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using EnvironmentalHub.Core;
using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Parameters;
using Grasshopper.Kernel.Types;
using Rhino;
using Rhino.Geometry;

namespace EnvironmentalHub.Adapters;

public sealed record RadiationAdapterConfiguration(string UserObjectDirectory, string RadianceBinDirectory);

public sealed class LadybugRadiationAdapter(RhinoDoc document, RadiationAdapterConfiguration configuration) : IRadiationAdapter
{
    private const string WorkflowVersion = "0.2.0";
    private static readonly string[] Components = ["LB Import EPW", "LB Cumulative Sky Matrix", "LB Incident Radiation"];
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true, WriteIndented = true };

    public static string RunJson(RhinoDoc document, string requestJson, string configurationJson) =>
        JsonSerializer.Serialize(new LadybugRadiationAdapter(document,
            JsonSerializer.Deserialize<RadiationAdapterConfiguration>(configurationJson, JsonOptions)!).Execute(
            JsonSerializer.Deserialize<RadiationAnalysisRequest>(requestJson, JsonOptions)!), JsonOptions);

    public static string PreflightJson(RhinoDoc document, string requestJson, string configurationJson) =>
        JsonSerializer.Serialize(new LadybugRadiationAdapter(document,
            JsonSerializer.Deserialize<RadiationAdapterConfiguration>(configurationJson, JsonOptions)!).Preflight(
            JsonSerializer.Deserialize<RadiationAnalysisRequest>(requestJson, JsonOptions)!), JsonOptions);

    public PreflightReport Preflight(RadiationAnalysisRequest request)
    {
        if (request is null)
            return new([new("ERROR", "RAD-CONTRACT-001", "Request cannot be null.")], null);
        if (request.GeometryIds is null || request.ContextIds is null || request.HoursOfYear is null || request.Settings is null)
            return new([new("ERROR", "RAD-CONTRACT-002", "Request collections and settings cannot be null.")], null);
        if (RhinoDoc.ActiveDoc?.RuntimeSerialNumber != document.RuntimeSerialNumber)
            return new([new("ERROR", "RAD-DOC-001", "Ladybug uses active Rhino units; the target document must be active.")], null);
        double scale = RhinoMath.UnitScale(document.ModelUnitSystem, UnitSystem.Meters);
        GeometryFact Fact(Guid id)
        {
            var obj = document.Objects.FindId(id);
            var geometry = obj?.Geometry;
            return new(id, obj is not null, geometry?.IsValid == true, geometry is Brep or Mesh,
                geometry is null ? 0 : geometry.GetBoundingBox(true).Diagonal.Length * scale);
        }
        return RadiationPreflight.Check(request, new(scale, document.ModelUnitSystem != UnitSystem.None,
            request.GeometryIds.Select(Fact).ToArray(), request.ContextIds.Select(Fact).ToArray(),
            Components.All(n => File.Exists(Path.Combine(configuration.UserObjectDirectory, n + ".ghuser"))),
            File.Exists(Path.Combine(configuration.RadianceBinDirectory, "gendaymtx.exe")) &&
            File.Exists(Path.Combine(configuration.RadianceBinDirectory, "rtrace.exe"))));
    }

    public AnalysisResult Execute(RadiationAnalysisRequest request)
    {
        if (RhinoApp.InvokeRequired) throw new InvalidOperationException("RAD-THREAD-001: Execute on the Rhino UI thread.");
        var preflight = Preflight(request);
        if (!preflight.CanRun) throw new InvalidOperationException(JsonSerializer.Serialize(preflight));
        if (preflight.HasWarnings && !request.AcceptWarnings)
            throw new InvalidOperationException("RAD-WARNING-001: Review and accept preflight warnings before execution.");
        if (!GH_Document.EnableSolutions) throw new InvalidOperationException("RAD-GH-001: Grasshopper solver globally disabled.");
        Directory.CreateDirectory(request.OutputDirectory);
        var timer = Stopwatch.StartNew();
        var modelScale = RhinoMath.UnitScale(UnitSystem.Meters, document.ModelUnitSystem);
        var snapshots = new Dictionary<Guid, GeometryBase>();
        using var definition = new GH_Document();
        definition.Enabled = false;
        try
        {
            foreach (var id in request.GeometryIds.Concat(request.ContextIds))
                snapshots.Add(id, document.Objects.FindId(id).Geometry.Duplicate());
            IGH_Component Stock(string name, int x)
            {
                var component = (IGH_Component)new GH_UserObject(Path.Combine(configuration.UserObjectDirectory, name + ".ghuser")).InstantiateObject();
                component.CreateAttributes(); component.Attributes.Pivot = new PointF(x, 100);
                definition.AddObject(component, false); return component;
            }
            var epw = Stock(Components[0], 350);
            var sky = Stock(Components[1], 650);
            var radiation = Stock(Components[2], 950);
            IGH_Param Input(IGH_Component c, string name) => c.Params.Input.Single(p => p.Name == name);
            IGH_Param Output(IGH_Component c, string name) => c.Params.Output.Single(p => p.Name == name);
            void Bind(IGH_Component target, string name, IEnumerable<object> values)
            {
                var parameter = new Param_GenericObject { Name = name, NickName = "HUB:" + name };
                parameter.CreateAttributes(); parameter.Attributes.Pivot = new PointF(50, 50 + definition.ObjectCount * 35);
                parameter.SetPersistentData(values.Select(v => new GH_ObjectWrapper(v)));
                definition.AddObject(parameter, false); Input(target, name).AddSource(parameter);
            }
            void One(IGH_Component c, string name, object value) => Bind(c, name, [value]);
            One(epw, "_epw_file", request.WeatherFile);
            Input(sky, "_location").AddSource(Output(epw, "location"));
            Input(sky, "_direct_rad").AddSource(Output(epw, "direct_normal_rad"));
            Input(sky, "_diffuse_rad").AddSource(Output(epw, "diffuse_horizontal_rad"));
            One(sky, "north_", request.NorthDegrees);
            if (request.HoursOfYear.Length > 0) Bind(sky, "_hoys_", request.HoursOfYear.Select(h => (object)h));
            One(sky, "high_density_", request.Settings.HighDensity);
            One(sky, "_ground_ref_", request.Settings.GroundReflectance);
            One(sky, "_folder_", request.OutputDirectory);
            Input(radiation, "_sky_mtx").AddSource(Output(sky, "sky_mtx"));
            Bind(radiation, "_geometry", request.GeometryIds.Select(id => (object)snapshots[id]));
            if (request.ContextIds.Length > 0) Bind(radiation, "context_", request.ContextIds.Select(id => (object)snapshots[id]));
            One(radiation, "_grid_size", request.GridMetres * modelScale);
            One(radiation, "_offset_dist_", request.Settings.OffsetMetres * modelScale);
            One(radiation, "irradiance_", false);
            One(radiation, "_cpu_count_", request.Settings.CpuCount);
            One(radiation, "_run", true);
            Instances.DocumentServer.AddDocument(definition);
            definition.Enabled = true;
            definition.NewSolution(false);
            var errors = new[] { epw, sky, radiation }.SelectMany(c => c.RuntimeMessages(GH_RuntimeMessageLevel.Error)
                .Select(m => new Diagnostic("ERROR", "RAD-SOLVER-002", c.Name + ": " + m))).ToArray();
            if (errors.Length > 0) throw new InvalidOperationException(JsonSerializer.Serialize(errors));
            // Verify the executable referenced by the actual stock SkyMatrix method,
            // rather than reporting a configured but unused Radiance installation.
            dynamic matrix = Output(sky, "sky_mtx").VolatileData.AllData(true).Single().ScriptVariable();
            string actualExecutable = (string)matrix._run_gendaymtx.__func__.__globals__["GENDAYMTX_EXE"];
            if (!Path.GetFullPath(actualExecutable).Equals(Path.GetFullPath(Path.Combine(configuration.RadianceBinDirectory, "gendaymtx.exe")), StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("RAD-SOLVER-005: Configured Radiance differs from Ladybug runtime executable.");
            object[] Data(string name) => Output(radiation, name).VolatileData.AllData(true).Select(v => v.ScriptVariable()).ToArray();
            var values = Data("results").Select(Convert.ToDouble).ToArray();
            var meshes = Data("mesh").Cast<Mesh>().ToArray();
            if (values.Length == 0 || values.Any(v => !double.IsFinite(v)) || meshes.Sum(m => m.Faces.Count) != values.Length)
                throw new InvalidOperationException("RAD-RESULT-001: Empty, non-finite or misaligned result.");
            if (Data("legend").Length == 0) throw new InvalidOperationException("RAD-RESULT-002: Legend missing.");
            var warnings = preflight.Diagnostics.Where(d => d.Severity == "WARNING").Concat(
                new[] { epw, sky, radiation }.SelectMany(c => c.RuntimeMessages(GH_RuntimeMessageLevel.Warning)
                    .Select(m => new Diagnostic("WARNING", "RAD-SOLVER-003", c.Name + ": " + m)))).ToArray();
            MeshArtifact Artifact(Mesh mesh) => new(mesh.Vertices.Select(v => new[] { (double)v.X, v.Y, v.Z }).ToArray(),
                mesh.Faces.Select(f => f.IsTriangle ? new[] { f.A, f.B, f.C } : new[] { f.A, f.B, f.C, f.D }).ToArray(),
                mesh.VertexColors.Select(c => c.ToArgb()).ToArray());
            var points = Data("points").Cast<Point3d>().Select(p => new[] { p.X, p.Y, p.Z }).ToArray();
            var stats = new ResultStatistics(values.Length, values.Min(), values.Max(), values.Average());
            var radianceVersion = RadianceVersion();
            var metadata = new Dictionary<string, string>
            {
                ["Location"] = preflight.Location ?? "", ["ModelUnits"] = document.ModelUnitSystem.ToString(),
                ["GridModelUnits"] = (request.GridMetres * modelScale).ToString("R", System.Globalization.CultureInfo.InvariantCulture),
                ["WeatherSha256"] = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(request.WeatherFile))),
                ["GeometrySha256"] = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(string.Join("\n",
                    snapshots.OrderBy(s => s.Key).Select(s => s.Key + ":" + s.Value.ToJSON(new Rhino.FileIO.SerializationOptions())))))),
                ["RadianceVersion"] = radianceVersion, ["ComponentVersions"] = string.Join(";", new[] { epw, sky, radiation }.Select(c => c.Name + "=" + c.Message)),
                ["RadianceBinDirectory"] = configuration.RadianceBinDirectory,
                ["ActualGendaymtxExecutable"] = actualExecutable,
                ["ScientificValidation"] = "Original Ladybug workflow comparison required for each fixture"
            };
            var result = new AnalysisResult("SolarRadiation", request.GeometryIds, meshes.Select(Artifact).ToArray(), values, points, [],
                "kWh/m2", new("kWh/m2", stats.Minimum, stats.Maximum, meshes.SelectMany(m => m.VertexColors.Select(c => c.ToArgb())).Distinct().ToArray()),
                stats, "Ladybug Incident Radiation + Radiance gendaymtx", metadata["ComponentVersions"] + ";" + radianceVersion,
                WorkflowVersion, request, metadata, warnings, [], timer.Elapsed.TotalSeconds, DateTimeOffset.UtcNow);
            File.WriteAllText(Path.Combine(request.OutputDirectory, "analysis_result.json"), JsonSerializer.Serialize(result, JsonOptions));
            return result;
        }
        finally
        {
            Instances.DocumentServer.RemoveDocument(definition);
            foreach (var geometry in snapshots.Values) geometry.Dispose();
        }
    }

    private string RadianceVersion()
    {
        using var process = Process.Start(new ProcessStartInfo(Path.Combine(configuration.RadianceBinDirectory, "rtrace.exe"), "-version")
        { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true })!;
        if (!process.WaitForExit(5000)) { process.Kill(); throw new InvalidOperationException("RAD-SOLVER-004: Version query timeout."); }
        if (process.ExitCode != 0) throw new InvalidOperationException("RAD-SOLVER-004: Version query failed.");
        return (process.StandardOutput.ReadToEnd() + process.StandardError.ReadToEnd()).Trim();
    }
}
