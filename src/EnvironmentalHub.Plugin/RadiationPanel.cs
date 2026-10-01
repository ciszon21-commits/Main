using System.Globalization;
using System.Runtime.InteropServices;
using System.Text.Json;
using EnvironmentalHub.Adapters;
using EnvironmentalHub.Core;
using Eto.Drawing;
using Eto.Forms;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Input.Custom;

namespace EnvironmentalHub.Plugin;

[Guid("c62382ce-7709-4fcd-9dfb-447d1d8a08c0")]
public sealed class RadiationPanel : Panel
{
    private readonly Label geometryLabel = new() { Text = "No geometry selected" };
    private readonly TextBox weather = new() { PlaceholderText = "Select EPW" };
    private readonly NumericStepper grid = new() { MinValue = 0.01, MaxValue = 1000, Value = 1, DecimalPlaces = 2 };
    private readonly NumericStepper north = new() { MinValue = -360, MaxValue = 360, Value = 0 };
    private readonly Label status = new() { Text = "Ready" };
    private readonly Label resultLabel = new() { Text = "No result" };
    private readonly Button run = new() { Text = "RUN ANALYSIS" };
    private readonly List<(uint Document, Guid Object)> rendered = [];
    private Guid[] selected = [];
    private Guid[] context = [];
    private uint selectedDocument;
    public string StatusText => status.Text;
    public string ResultText => resultLabel.Text;
    public int RenderedObjectCount => rendered.Count;

    public RadiationPanel()
    {
        BackgroundColor = Colors.White;
        var select = new Button { Text = "SELECT GEOMETRY" };
        var selectContext = new Button { Text = "SELECT CONTEXT (optional)" };
        var browse = new Button { Text = "SELECT EPW" };
        var preflight = new Button { Text = "PREFLIGHT" };
        var reset = new Button { Text = "RESET RESULT" };
        select.Click += (_, _) => Guard(() => SelectGeometry(false));
        selectContext.Click += (_, _) => Guard(() => SelectGeometry(true));
        browse.Click += (_, _) =>
        {
            var dialog = new OpenFileDialog();
            dialog.Filters.Add(new FileFilter("EPW weather", ".epw"));
            if (dialog.ShowDialog(this) == DialogResult.Ok) weather.Text = dialog.FileName;
        };
        preflight.Click += (_, _) => Guard(() =>
        {
            var doc = RequireDocument();
            var report = Adapter(doc).Preflight(Request(false));
            status.Text = FormatPreflight(report);
        });
        run.Click += (_, _) => Guard(() =>
        {
            var doc = RequireDocument();
            var request = Request(false);
            var report = Adapter(doc).Preflight(request);
            status.Text = FormatPreflight(report);
            if (!report.CanRun) return;
            if (report.HasWarnings && MessageBox.Show(this, string.Join("\n", report.Diagnostics.Select(d => d.Message)),
                "Preflight warning", MessageBoxButtons.YesNo, MessageBoxType.Warning) != DialogResult.Yes) return;
            ExecuteRequest(request with { AcceptWarnings = true });
        });
        reset.Click += (_, _) => ResetResult();
        var layout = new DynamicLayout { Padding = 12, Spacing = new Size(6, 8) };
        layout.AddRow(new Label { Text = "SOLAR RADIATION", Font = new Eto.Drawing.Font(SystemFont.Bold, 12), TextColor = Color.FromArgb(30, 90, 180) });
        layout.AddRow(select); layout.AddRow(geometryLabel); layout.AddRow(selectContext);
        layout.AddRow(weather); layout.AddRow(browse);
        layout.AddRow(new Label { Text = "Grid (m)" }, grid);
        layout.AddRow(new Label { Text = "North (degrees)" }, north);
        layout.AddRow(new Label { Text = "Annual • Standard • 1 CPU" });
        layout.AddRow(preflight); layout.AddRow(run); layout.AddRow(status);
        layout.AddRow(new Label { Text = "RESULT / kWh/m²" }); layout.AddRow(resultLabel); layout.AddRow(reset);
        layout.Add(null);
        Content = new Scrollable { Content = layout };
    }

    private void SelectGeometry(bool isContext)
    {
        var currentDocument = RhinoDoc.ActiveDoc ?? throw new InvalidOperationException("RAD-DOC-001: No active document.");
        if (selectedDocument != 0 && selectedDocument != currentDocument.RuntimeSerialNumber)
        {
            selected = []; context = [];
        }
        using var picker = new GetObject();
        picker.SetCommandPrompt(isContext ? "Select shading context" : "Select radiation analysis geometry");
        picker.GeometryFilter = ObjectType.Surface | ObjectType.Brep | ObjectType.Mesh;
        picker.GetMultiple(1, 0);
        if (picker.CommandResult() != Rhino.Commands.Result.Success) return;
        var ids = picker.Objects().Select(o => o.ObjectId).ToArray();
        if (isContext) context = ids; else selected = ids;
        selectedDocument = currentDocument.RuntimeSerialNumber;
        geometryLabel.Text = $"Analysis {selected.Length} • Context {context.Length}";
    }

    private RadiationAnalysisRequest Request(bool acceptWarnings) => new()
    {
        GeometryIds = selected, ContextIds = context, WeatherFile = weather.Text,
        GridMetres = grid.Value, NorthDegrees = north.Value, AcceptWarnings = acceptWarnings,
        OutputDirectory = Path.Combine(OutputRoot(), DateTimeOffset.UtcNow.ToString("yyyyMMdd_HHmmss") + "_" + Guid.NewGuid().ToString("N"))
    };

    private static string AssemblyDirectory => Path.GetDirectoryName(typeof(RadiationPanel).Assembly.Location)!;
    private static JsonElement Configuration() => JsonDocument.Parse(File.ReadAllText(Path.Combine(AssemblyDirectory, "hub.config.json"))).RootElement.Clone();
    private static string Expand(string path) => System.Environment.ExpandEnvironmentVariables(path);
    private static string OutputRoot()
    {
        var path = Expand(Configuration().GetProperty("OutputDirectory").GetString()!);
        return Path.IsPathFullyQualified(path) ? path : Path.GetFullPath(Path.Combine(AssemblyDirectory, path));
    }
    private static LadybugRadiationAdapter Adapter(RhinoDoc doc)
    {
        var config = Configuration();
        return new(doc, new(Expand(config.GetProperty("UserObjectDirectory").GetString()!), Expand(config.GetProperty("RadianceBinDirectory").GetString()!)));
    }
    private RhinoDoc RequireDocument()
    {
        var doc = RhinoDoc.ActiveDoc ?? throw new InvalidOperationException("RAD-DOC-001: No active document.");
        if (selectedDocument != 0 && selectedDocument != doc.RuntimeSerialNumber)
            throw new InvalidOperationException("RAD-DOC-002: Document changed; select geometry again.");
        return doc;
    }
    private static string FormatPreflight(PreflightReport report) => report.Diagnostics.Length == 0 ? "PASS" :
        string.Join("\n", report.Diagnostics.Select(d => $"{d.Severity} {d.Code}: {d.Message}"));
    private void Guard(Action action)
    {
        try { action(); } catch (Exception e) { status.Text = e.Message; resultLabel.Text = "Analysis failed"; }
    }

    // The button and integration test share this same UI → request → adapter path.
    public string ExecuteJson(string requestJson) => ExecuteRequest(JsonSerializer.Deserialize<RadiationAnalysisRequest>(requestJson)!);

    public string ExecuteRequest(RadiationAnalysisRequest request)
    {
        var doc = RequireDocument();
        selected = request.GeometryIds; context = request.ContextIds; selectedDocument = doc.RuntimeSerialNumber;
        geometryLabel.Text = $"Analysis {selected.Length} • Context {context.Length}";
        weather.Text = request.WeatherFile; grid.Value = request.GridMetres; north.Value = request.NorthDegrees;
        run.Enabled = false; status.Text = "Running Ladybug radiation…"; resultLabel.Text = "Pending";
        try
        {
            var result = Adapter(doc).Execute(request);
            ResetResult();
            foreach (var artifact in result.ResultMesh)
            {
                using var mesh = new Mesh();
                foreach (var v in artifact.Vertices) mesh.Vertices.Add(v[0], v[1], v[2]);
                foreach (var f in artifact.Faces)
                    if (f.Length == 3) mesh.Faces.AddFace(f[0], f[1], f[2]); else mesh.Faces.AddFace(f[0], f[1], f[2], f[3]);
                foreach (var color in artifact.VertexColorsArgb) mesh.VertexColors.Add(System.Drawing.Color.FromArgb(color));
                var attributes = new ObjectAttributes { Name = "EnvironmentalHub / SolarRadiation / kWh per m2" };
                var objectId = doc.Objects.AddMesh(mesh, attributes);
                if (objectId == Guid.Empty) throw new InvalidOperationException("RAD-VIEW-001: Result mesh display failed.");
                rendered.Add((doc.RuntimeSerialNumber, objectId));
            }
            resultLabel.Text = $"Average {result.Statistics.Mean:F3}\nMin {result.Statistics.Minimum:F3} • Max {result.Statistics.Maximum:F3}\n{result.Statistics.Count} cells • {result.Units}";
            status.Text = "Complete • " + result.Metadata["Location"];
            doc.Views.Redraw();
            return JsonSerializer.Serialize(result);
        }
        catch (Exception e) { status.Text = e.Message; resultLabel.Text = "Analysis failed"; throw; }
        finally { run.Enabled = true; }
    }

    public void ResetResult()
    {
        foreach (var owned in rendered)
        {
            var doc = RhinoDoc.FromRuntimeSerialNumber(owned.Document);
            doc?.Objects.Delete(owned.Object, true); doc?.Views.Redraw();
        }
        rendered.Clear(); resultLabel.Text = "No result"; status.Text = "Ready";
    }
}
