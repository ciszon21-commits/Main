using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using EnvironmentalHub.Core;
using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Parameters;
using Grasshopper.Kernel.Types;
using Rhino;
using Rhino.Geometry;

namespace EnvironmentalHub.Adapters;

public sealed class LadybugSunHoursAdapter(RhinoDoc document, string folder)
{
    public static string RunJson(RhinoDoc doc, string json, string folder) => JsonSerializer.Serialize(new LadybugSunHoursAdapter(doc, folder).Execute(JsonSerializer.Deserialize<SunHoursRequest>(json)!));
    public PreflightReport Preflight(SunHoursRequest r)
    {
        var diagnostics = new List<Diagnostic>();
        void Error(string code, string message) => diagnostics.Add(new("ERROR", code, message));
        if (r is null || r.SchemaVersion != "1.0" || r.GeometryIds is null || r.ContextIds is null || r.SunSource is null)
            return new([new("ERROR", "SUNH-CONTRACT-001", "Schema 1.0, geometry collections and sun source required.")], null);
        if (RhinoDoc.ActiveDoc?.RuntimeSerialNumber != document.RuntimeSerialNumber) Error("SUNH-DOC-001", "Target document must be active.");
        if (document.ModelUnitSystem is UnitSystem.None or UnitSystem.CustomUnits) Error("SUNH-UNIT-001", "Explicit supported model units required.");
        if (r.GeometryIds.Length == 0 || r.GeometryIds.Concat(r.ContextIds).Distinct().Count() != r.GeometryIds.Length + r.ContextIds.Length)
            Error("SUNH-GEO-001", "Select analysis geometry; geometry/context IDs must be unique and disjoint.");
        foreach (var id in r.GeometryIds.Concat(r.ContextIds))
            if (document.Objects.FindId(id)?.Geometry is not (Brep or Mesh) || document.Objects.FindId(id)?.Geometry.IsValid != true)
                Error("SUNH-GEO-001", "Geometry must exist and be valid Brep/Mesh: " + id);
        if (!double.IsFinite(r.GridMetres) || r.GridMetres < .01 || r.GridMetres > 1000000 || !double.IsFinite(r.OffsetMetres) || r.OffsetMetres < 0 || r.OffsetMetres > 1000000 || r.CpuCount < 1 || r.CpuCount > 128)
            Error("SUNH-PARAM-001", "Grid 0.01..1000000 m, offset 0..1000000 m and CPU 1..128 required.");
        try { SunHoursSampling.Check(r.SunSource.HoursOfYear, r.TimeStepsPerHour); }
        catch (ArgumentException e) { Error("SUNH-TIME-001", e.Message); }
        if (!File.Exists(Path.Combine(folder, "LB Direct Sun Hours.ghuser"))) Error("SUNH-PLUGIN-001", "Original Direct Sun Hours component unavailable.");
        if (r.GeometryBlocks && r.OffsetMetres == 0) diagnostics.Add(new("WARNING", "SUNH-OFFSET-001", "Zero offset with self-blocking may intersect the analysis surface; verify normals and offset."));
        if (r.SunSource.HoursOfYear?.Length > 10000) diagnostics.Add(new("WARNING", "SUNH-CAPACITY-001", "Large sample count; synchronous CAD ray intersection has no cancellation. Begin with a short period."));
        return new(diagnostics.ToArray(), r.SunSource.Location?.Name);
    }
    public SunHoursResult Execute(SunHoursRequest r)
    {
        if (RhinoApp.InvokeRequired) throw new InvalidOperationException("SUNH-THREAD-001: Execute on Rhino UI thread.");
        var preflight = Preflight(r);
        if (!preflight.CanRun) throw new InvalidOperationException(JsonSerializer.Serialize(preflight));
        if (preflight.HasWarnings && !r.AcceptWarnings) throw new InvalidOperationException("SUNH-WARNING-001: Review and accept preflight warnings.");
        if (!GH_Document.EnableSolutions) throw new InvalidOperationException("SUNH-GH-001: Grasshopper solver disabled.");
        var watch = Stopwatch.StartNew();
        // Recompute using the unchanged stock SunPath adapter; never trust user-supplied vectors.
        var sun = new LadybugSunPathAdapter(folder).Execute(r.SunSource!);
        if (sun.Positions.Length == 0) throw new InvalidOperationException("SUNH-NIGHT-001: No sun-up vectors; select a daytime period. No synthetic zero result produced.");
        var path = Path.Combine(folder, "LB Direct Sun Hours.ghuser"); var hash = Hash(File.ReadAllBytes(path));
        var snapshots = new Dictionary<Guid, GeometryBase>();
        using var d = new GH_Document(); d.Enabled = false;
        try
        {
            foreach (var id in r.GeometryIds.Concat(r.ContextIds)) snapshots.Add(id, document.Objects.FindId(id).Geometry.Duplicate());
            var c = (IGH_Component)new GH_UserObject(path).InstantiateObject(); c.CreateAttributes(); d.AddObject(c, false);
            void Bind(string name, params object[] values)
            {
                var p = new Param_GenericObject(); p.CreateAttributes();
                foreach (var v in values) p.PersistentData.Append(new GH_ObjectWrapper(v), new GH_Path(0));
                d.AddObject(p, false); c.Params.Input.Single(i => i.Name == name).AddSource(p);
            }
            var scale = RhinoMath.UnitScale(UnitSystem.Meters, document.ModelUnitSystem);
            Bind("_vectors", sun.Positions.Select(p => (object)new Vector3d(p.SunlightVector[0], p.SunlightVector[1], p.SunlightVector[2])).ToArray());
            Bind("_timestep_", r.TimeStepsPerHour); Bind("_geometry", r.GeometryIds.Select(id => (object)snapshots[id]).ToArray());
            if (r.ContextIds.Length > 0) Bind("context_", r.ContextIds.Select(id => (object)snapshots[id]).ToArray());
            Bind("_grid_size", r.GridMetres * scale); Bind("_offset_dist_", r.OffsetMetres * scale); Bind("geo_block_", r.GeometryBlocks); Bind("_cpu_count_", r.CpuCount); Bind("_run", true);
            Instances.DocumentServer.AddDocument(d); d.Enabled = true; d.NewSolution(false);
            var errors = c.RuntimeMessages(GH_RuntimeMessageLevel.Error).ToArray();
            if (errors.Length > 0) throw new InvalidOperationException("SUNH-SOLVER-001: " + string.Join("\n", errors));
            object[] Data(string name) => c.Params.Output.Single(o => o.Name == name).VolatileData.AllData(true).Select(v => v.ScriptVariable()).ToArray();
            var values = Data("results").Select(Convert.ToDouble).ToArray(); var points = Data("points").Cast<Point3d>().ToArray(); var meshes = Data("mesh").Cast<Mesh>().ToArray();
            var maximum = sun.Positions.Length / (double)r.TimeStepsPerHour;
            if (values.Length == 0 || points.Length != values.Length || meshes.Sum(m => m.Faces.Count) != values.Length || points.Any(p => !p.IsValid) || values.Any(v => !double.IsFinite(v) || v < 0 || v > maximum + 1e-8) || meshes.Any(m => !m.IsValid || m.VertexColors.Count != m.Vertices.Count))
                throw new InvalidOperationException("SUNH-RESULT-001: Native values/points/mesh alignment invalid.");
            if (hash != Hash(File.ReadAllBytes(path))) throw new InvalidOperationException("SUNH-PLUGIN-001: Original component changed during solve.");
            var artifacts = meshes.Select(m => new MeshArtifact(m.Vertices.Select(v => new[] { (double)v.X, v.Y, v.Z }).ToArray(), m.Faces.Select(f => f.IsTriangle ? new[] { f.A, f.B, f.C } : new[] { f.A, f.B, f.C, f.D }).ToArray(), m.VertexColors.Select(v => v.ToArgb()).ToArray())).ToArray();
            var canonicalSun = new { sun.Location, r.SunSource!.HoursOfYear, r.SunSource.NorthDegrees, r.SunSource.SolarTime, r.TimeStepsPerHour, Vectors = sun.Positions.Select(p => p.SunlightVector) };
            var metadata = new Dictionary<string, string>
            {
                ["Location"] = sun.Location.City, ["ModelUnits"] = document.ModelUnitSystem.ToString(), ["MetresPerModelUnit"] = (1 / scale).ToString("R", System.Globalization.CultureInfo.InvariantCulture),
                ["UserObjectSha256"] = hash, ["SunPathUserObjectSha256"] = sun.Metadata["UserObjectSha256"], ["ComponentVersion"] = c.Message,
                ["SunSourceSha256"] = Hash(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(canonicalSun))),
                ["GeometrySha256"] = Hash(Encoding.UTF8.GetBytes(string.Join("\n", snapshots.OrderBy(s => s.Key).Select(s => s.Key + ":" + s.Value.ToJSON(new Rhino.FileIO.SerializationOptions()))))),
                ["Solver"] = "Original Ladybug Direct Sun Hours / Rhino CAD ray intersections", ["WorkflowVersion"] = "1.0",
                ["TimeConvention"] = "Non-leap, no DST. Each selected sun-up vector represents 1/timestep hours; endpoints are included samples, not elapsed calendar duration.",
                ["Scope"] = "Stock points/results/colored mesh; native default legend palette. Custom legend/title/intersection-matrix UI deferred. Mesh inputs retain native per-face sampling; Breps use grid size."
            };
            return new("1.0", r, artifacts, values, points.Select(p => new[] { p.X, p.Y, p.Z }).ToArray(), sun.Positions.Select(p => p.SunlightVector).ToArray(), sun.Positions.Select(p => p.HourOfYear).ToArray(), "h",
                new(values.Length, values.Min(), values.Max(), values.Average()), metadata, preflight.Diagnostics.Where(d => d.Severity == "WARNING").Concat(sun.Warnings).Concat(c.RuntimeMessages(GH_RuntimeMessageLevel.Warning).Select(m => new Diagnostic("WARNING", "SUNH-SOLVER-002", m))).ToArray(), watch.Elapsed.TotalSeconds, DateTimeOffset.UtcNow);
        }
        finally { Instances.DocumentServer.RemoveDocument(d); foreach (var g in snapshots.Values) g.Dispose(); }
    }
    private static string Hash(byte[] data) => Convert.ToHexString(SHA256.HashData(data));
}
