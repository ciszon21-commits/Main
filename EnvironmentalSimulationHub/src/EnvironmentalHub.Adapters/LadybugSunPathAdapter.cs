using System.Security.Cryptography;
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

public sealed class LadybugSunPathAdapter(string folder)
{
    public static string RunJson(string json, string folder) => JsonSerializer.Serialize(
        new LadybugSunPathAdapter(folder).Execute(JsonSerializer.Deserialize<SunPathRequest>(json)!));

    public SunPathResult Execute(SunPathRequest r)
    {
        if (RhinoApp.InvokeRequired) throw new InvalidOperationException("CLIMATE-THREAD-001: Execute on Rhino UI thread.");
        if (r is null || r.SchemaVersion != "1.0" || r.Location is null || r.Center is null || r.Center.Length != 3 || r.Center.Any(v => !double.IsFinite(v)))
            throw new InvalidOperationException("SUN-CONTRACT-001: Valid schema 1.0, location and XYZ centre required.");
        if (r.HoursOfYear is null || r.HoursOfYear.Length == 0 || r.HoursOfYear.Length > 525600 ||
            r.HoursOfYear.Any(h => !double.IsFinite(h) || h < 0 || h >= 8760 || Math.Abs(h * 60 - Math.Round(h * 60)) > 1e-7) ||
            r.HoursOfYear.Distinct().Count() != r.HoursOfYear.Length)
            throw new InvalidOperationException("SUN-TIME-001: Unique non-leap HOYs 0..<8760 at minute precision required.");
        if (!double.IsFinite(r.NorthDegrees) || Math.Abs(r.NorthDegrees) > 360 || !double.IsFinite(r.RadiusMetres) || r.RadiusMetres <= 0 || r.RadiusMetres > 1000000 ||
            r.Projection is not ("3D" or "Orthographic" or "Stereographic" or "Equidistant" or "Equisolid"))
            throw new InvalidOperationException("SUN-PARAM-001: North -360..360, radius >0..1000000 m and supported projection required.");
        var doc = RhinoDoc.ActiveDoc ?? throw new InvalidOperationException("SUN-DOC-001: Active Rhino document required.");
        if (doc.ModelUnitSystem is UnitSystem.None or UnitSystem.CustomUnits || !double.IsFinite(RhinoMath.UnitScale(doc.ModelUnitSystem, UnitSystem.Meters)))
            throw new InvalidOperationException("SUN-UNIT-001: Explicit supported model units required.");
        // Validate the location through the existing original-component adapter before binding it.
        var location = new LadybugLocationAdapter(folder).Execute(r.Location);
        if (!GH_Document.EnableSolutions) throw new InvalidOperationException("CLIMATE-GH-001: Grasshopper solver disabled.");
        var paths = new[] { "LB Construct Location", "LB SunPath" }.Select(n => Path.Combine(folder, n + ".ghuser")).ToArray();
        if (paths.Any(p => !File.Exists(p))) throw new InvalidOperationException("CLIMATE-PLUGIN-001: Original SunPath component missing.");
        var hashes = paths.Select(Hash).ToArray();
        using var d = new GH_Document(); d.Enabled = false;
        try
        {
            IGH_Component Make(string path)
            {
                var c = (IGH_Component)new GH_UserObject(path).InstantiateObject(); c.CreateAttributes(); d.AddObject(c, false); return c;
            }
            void Bind(IGH_Component c, string name, params object[] values)
            {
                var p = new Param_GenericObject(); p.CreateAttributes();
                foreach (var value in values) p.PersistentData.Append(new GH_ObjectWrapper(value), new GH_Path(0));
                d.AddObject(p, false); c.Params.Input.Single(i => i.Name == name).AddSource(p);
            }
            var loc = Make(paths[0]); var sun = Make(paths[1]);
            Bind(loc, "_name_", r.Location.Name); Bind(loc, "_latitude_", r.Location.Latitude); Bind(loc, "_longitude_", r.Location.Longitude);
            Bind(loc, "_time_zone_", location.Location.TimeZone); Bind(loc, "_elevation_", r.Location.ElevationMetres);
            sun.Params.Input.Single(i => i.Name == "_location").AddSource(loc.Params.Output.Single(o => o.Name == "location"));
            Bind(sun, "hoys_", r.HoursOfYear.Cast<object>().ToArray()); Bind(sun, "north_", r.NorthDegrees); Bind(sun, "solar_time_", r.SolarTime);
            Bind(sun, "_center_pt_", new Point3d(r.Center[0], r.Center[1], r.Center[2])); Bind(sun, "_scale_", r.RadiusMetres / 100);
            Bind(sun, "daily_", r.Daily); if (r.Projection != "3D") Bind(sun, "projection_", r.Projection);
            Instances.DocumentServer.AddDocument(d); d.Enabled = true; d.NewSolution(false);
            var errors = loc.RuntimeMessages(GH_RuntimeMessageLevel.Error).Concat(sun.RuntimeMessages(GH_RuntimeMessageLevel.Error)).ToArray();
            if (errors.Length > 0) throw new InvalidOperationException("SUN-SOLVER-001: " + string.Join("\n", errors));
            object[] Values(string name) => sun.Params.Output.Single(o => o.Name == name).VolatileData.AllData(true).Select(v => v.ScriptVariable()).ToArray();
            var hoys = Values("hoys").Select(Convert.ToDouble).ToArray(); var alts = Values("altitudes").Select(Convert.ToDouble).ToArray();
            var azis = Values("azimuths").Select(Convert.ToDouble).ToArray(); var points = Values("sun_pts").Cast<Point3d>().ToArray(); var vectors = Values("vectors").Cast<Vector3d>().ToArray();
            if (new[] { alts.Length, azis.Length, points.Length, vectors.Length }.Any(n => n != hoys.Length) || hoys.Any(h => !double.IsFinite(h)) ||
                alts.Any(a => !double.IsFinite(a) || a < 0 || a > 90) || azis.Any(a => !double.IsFinite(a)) || points.Any(p => !p.IsValid) || vectors.Any(v => !v.IsValid || Math.Abs(v.Length - 1) > 1e-8))
                throw new InvalidOperationException("SUN-RESULT-001: Native output alignment or values invalid.");
            var curves = new List<SunPathCurve>(); var texts = new List<SunPathText>();
            foreach (var output in new[] { "analemma", "daily", "compass", "title" })
                foreach (var value in Values(output))
                {
                    Curve? curve = value switch { Curve c => c, Arc a => new ArcCurve(a), Circle c => c.ToNurbsCurve(), _ => null };
                    if (curve is not null)
                    {
                        if (!curve.IsValid) throw new InvalidOperationException("SUN-RESULT-001: Invalid native curve.");
                        curves.Add(new(output, curve.ToJSON(new Rhino.FileIO.SerializationOptions())));
                    }
                    else
                    {
                        dynamic goo = value; Rhino.Display.Text3d t = goo.m_value;
                        texts.Add(new(output, t.Text, XYZ(t.TextPlane.Origin), XYZ(t.TextPlane.XAxis), XYZ(t.TextPlane.YAxis), t.Height, t.FontFace, (int)t.HorizontalAlignment, (int)t.VerticalAlignment));
                    }
                }
            if (curves.Count == 0 || hashes.Where((h, i) => h != Hash(paths[i])).Any()) throw new InvalidOperationException("CLIMATE-INPUT-001: Missing geometry or changed original component.");
            var warnings = location.Warnings.Concat(sun.RuntimeMessages(GH_RuntimeMessageLevel.Warning).Select(m => new Diagnostic("WARNING", "SUN-SOLVER-002", m))).ToArray();
            return new("1.0", r, location.Location, hoys.Select((h, i) => new SunPosition(h, alts[i], azis[i], XYZ(points[i]), XYZ(vectors[i]))).ToArray(),
                curves.ToArray(), texts.ToArray(), doc.ModelUnitSystem.ToString(), RhinoMath.UnitScale(doc.ModelUnitSystem, UnitSystem.Meters),
                new() { ["Source"] = paths[1], ["UserObjectSha256"] = hashes[1], ["LocationUserObjectSha256"] = hashes[0], ["ComponentVersion"] = sun.Message,
                    ["Convention"] = "Non-leap minute HOY; no DST; azimuth native; north CCW from +Y; sunlight vectors towards ground",
                    ["Scope"] = "Original geometric SunPath, all four native projections, annual/daily; data/statement/legend/DST/vis_set not exposed" }, warnings);
        }
        finally { Instances.DocumentServer.RemoveDocument(d); }
    }
    private static string Hash(string path) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)));
    private static double[] XYZ(Point3d p) => [p.X, p.Y, p.Z];
    private static double[] XYZ(Vector3d p) => [p.X, p.Y, p.Z];
}
