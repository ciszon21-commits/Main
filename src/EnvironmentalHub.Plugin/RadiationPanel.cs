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
    private readonly Label geometryLabel = new() { Text = "No geometry selected", Wrap = WrapMode.Word };
    private readonly TextBox weather = new() { PlaceholderText = "Select EPW" };
    private readonly NumericStepper grid = new() { MinValue = 0.01, MaxValue = 1000, Value = 1, DecimalPlaces = 2, Width = 100 };
    private readonly NumericStepper north = new() { MinValue = -360, MaxValue = 360, Value = 0, Width = 100 };
    private readonly Label status = new() { Text = "Select analysis geometry and an EPW weather file.", Wrap = WrapMode.Word };
    private readonly Label resultLabel = new() { Text = "No result yet", Wrap = WrapMode.Word };
    private readonly Button run = new() { Text = "Run radiation analysis", Enabled = false };
    private readonly Label resultState = new() { Text = "Awaiting analysis", Wrap = WrapMode.Word };
    private readonly Button export = new() { Text = "Export result JSON…", Enabled = false };
    private readonly Button reset = new() { Text = "Clear preview", Enabled = false };
    private AnalysisResult? lastResult;
    private bool busy;
    private bool updatingInputs;
    private readonly List<(uint Document, Guid Object)> rendered = [];
    private Guid[] selected = [];
    private Guid[] context = [];
    private uint selectedDocument;
    public string ProductVersion => typeof(RadiationPanel).Assembly.GetName().Version!.ToString(3);
    public string StatusText => status.Text;
    public string ResultText => resultLabel.Text;
    public string ResultStateText => resultState.Text;
    public int RenderedObjectCount => rendered.Count;

    public RadiationPanel()
    {
        BackgroundColor = SystemColors.ControlBackground;
        Size = new Size(360, 640);
        MinimumSize = new Size(300, 200);
        var select = new Button { Text = "Select analysis geometry…" };
        var selectContext = new Button { Text = "Select shading context…" };
        var clearContext = new Button { Text = "Clear context" };
        var browse = new Button { Text = "Browse EPW…" };
        var preflight = new Button { Text = "Check inputs" };
        select.Click += (_, _) => Guard(() => SelectGeometry(false));
        selectContext.Click += (_, _) => Guard(() => SelectGeometry(true));
        clearContext.Click += (_, _) => { context = []; RefreshGeometry(); InputsChanged(); };
        browse.Click += (_, _) =>
        {
            var dialog = new OpenFileDialog();
            dialog.Filters.Add(new FileFilter("EPW weather", ".epw"));
            if (dialog.ShowDialog(this) == DialogResult.Ok) weather.Text = dialog.FileName;
        };
        weather.TextChanged += (_, _) => { weather.ToolTip = weather.Text; InputsChanged(); };
        grid.ValueChanged += (_, _) => InputsChanged();
        north.ValueChanged += (_, _) => InputsChanged();
        preflight.Click += (_, _) => Guard(() => status.Text = FormatPreflight(Adapter(RequireDocument()).Preflight(Request(false))));
        run.Click += (_, _) => Guard(() =>
        {
            var request = Request(false);
            var report = Adapter(RequireDocument()).Preflight(request);
            status.Text = FormatPreflight(report);
            if (!report.CanRun) return;
            if (report.HasWarnings && MessageBox.Show(this, string.Join("\n", report.Diagnostics.Where(d => d.Severity == "WARNING").Select(d => d.Message)),
                "Continue with these warnings?", MessageBoxButtons.YesNo, MessageBoxType.Warning) != DialogResult.Yes) return;
            ExecuteRequest(request with { AcceptWarnings = true });
        });
        reset.Click += (_, _) => ResetResult();
        export.Click += (_, _) => Guard(() =>
        {
            if (lastResult is null) return;
            var dialog = new SaveFileDialog { FileName = "radiation_result.json" };
            dialog.Filters.Add(new FileFilter("Analysis JSON", ".json"));
            if (dialog.ShowDialog(this) == DialogResult.Ok)
                File.WriteAllText(dialog.FileName, JsonSerializer.Serialize(lastResult, new JsonSerializerOptions { WriteIndented = true }));
        });
        var model = Section("01  Model", select, geometryLabel, selectContext, clearContext,
            Hint("Brep or mesh • Shading context is optional"));
        var climate = Section("02  Weather", weather, browse,
            Hint("EPW file • Annual simulation, 8,760 hours"));
        var settings = new DynamicLayout { Padding = 10, Spacing = new Size(8, 8) };
        settings.AddRow(new Label { Text = "Grid spacing (m)" }, grid);
        settings.AddRow(new Label { Text = "North rotation (°)" }, north);
        settings.AddRow(Hint("Standard • 1 CPU • Original Ladybug solver"));
        var execution = Section("04  Validate & run", preflight, run, status,
            Hint("Rhino may pause while the synchronous solver runs. Cancellation is not available yet."));
        var results = Section("05  Results", resultState, resultLabel, export, reset);
        var layout = new DynamicLayout { Padding = 14, Spacing = new Size(8, 12) };
        layout.AddRow(new Label { Text = "Solar radiation", Font = new Eto.Drawing.Font(SystemFont.Bold, 16) });
        layout.AddRow(Hint("Environmental Simulation Hub • " + ProductVersion));
        layout.AddRow(model); layout.AddRow(climate);
        layout.AddRow(new GroupBox { Text = "03  Analysis settings", Content = settings });
        layout.AddRow(execution); layout.AddRow(results); layout.Add(null);
        var scroll = new Scrollable { Content = layout, ExpandContentWidth = true };
        // WPF scroll viewers measure content at infinite width. Bound the layout
        // to its viewport so long paths cannot push button captions offscreen.
        scroll.SizeChanged += (_, _) => layout.Width = Math.Max(120, scroll.ClientSize.Width - 20);
        Content = scroll;
    }

    private static Label Hint(string text) => new() { Text = text, Wrap = WrapMode.Word, TextColor = SystemColors.DisabledText };
    private static GroupBox Section(string title, params Control[] controls)
    {
        var layout = new DynamicLayout { Padding = 10, Spacing = new Size(8, 8) };
        foreach (var control in controls) layout.AddRow(control);
        return new GroupBox { Text = title, Content = layout };
    }
    private void RefreshGeometry() => geometryLabel.Text = $"{selected.Length} analysis objects • {context.Length} context objects";
    private void InputsChanged()
    {
        if (updatingInputs || busy) return;
        run.Enabled = selected.Length > 0 && !string.IsNullOrWhiteSpace(weather.Text);
        status.Text = "Inputs changed • Check inputs before running.";
        if (lastResult is not null) resultState.Text = "Previous result • Inputs changed; run again to update.";
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
        if (picker.CommandResult() != Rhino.Commands.Result.Success)
        {
            RefreshGeometry(); InputsChanged(); return;
        }
        var ids = picker.Objects().Select(o => o.ObjectId).ToArray();
        if (isContext) context = ids; else selected = ids;
        selectedDocument = currentDocument.RuntimeSerialNumber;
        RefreshGeometry();
        InputsChanged();
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
    private static string FormatPreflight(PreflightReport report) => report.Diagnostics.Length == 0 ? "Inputs verified • Ready to run" :
        (report.CanRun ? "Ready with warnings\n" : "Fix the following inputs\n") + string.Join("\n", report.Diagnostics.Select(d => $"{d.Severity} {d.Code}: {d.Message}"));
    private void Guard(Action action)
    {
        try { action(); } catch (Exception e) { status.Text = "Analysis could not complete\n" + e.Message; }
    }

    // The button and integration test share this same UI → request → adapter path.
    public string ExecuteJson(string requestJson) => ExecuteRequest(JsonSerializer.Deserialize<RadiationAnalysisRequest>(requestJson)!);

    public string ExecuteRequest(RadiationAnalysisRequest request)
    {
        var doc = RequireDocument();
        // Reject malformed requests before updating controls or touching a preview.
        var report = Adapter(doc).Preflight(request);
        if (!report.CanRun)
        {
            status.Text = FormatPreflight(report);
            if (lastResult is not null) resultState.Text = "Previous result • New request rejected";
            throw new InvalidOperationException(status.Text);
        }
        selected = request.GeometryIds; context = request.ContextIds; selectedDocument = doc.RuntimeSerialNumber;
        updatingInputs = true;
        try { RefreshGeometry(); weather.Text = request.WeatherFile; grid.Value = request.GridMetres; north.Value = request.NorthDegrees; }
        finally { updatingInputs = false; }
        busy = true; run.Enabled = false; export.Enabled = false; reset.Enabled = false;
        status.Text = "Running original Ladybug radiation…";
        if (lastResult is not null) resultState.Text = "Previous result • New analysis pending";
        try
        {
            var result = Adapter(doc).Execute(request);
            ReplacePreview(doc, result);
            lastResult = result;
            resultState.Text = result.InputParameters.HoursOfYear.Length == 0
                ? "Current result • Annual incident radiation"
                : $"Current result • {result.InputParameters.HoursOfYear.Length} selected hours";
            resultLabel.Text = $"Average {result.Statistics.Mean:F3}\nMin {result.Statistics.Minimum:F3} • Max {result.Statistics.Maximum:F3}\n{result.Statistics.Count} cells • {result.Units}";
            status.Text = "Complete • " + result.Metadata["Location"];
            doc.Views.Redraw();
            return JsonSerializer.Serialize(result);
        }
        catch (Exception e)
        {
            status.Text = "Analysis could not complete\n" + ErrorMessage(e);
            if (lastResult is not null) resultState.Text = "Previous result • New analysis failed";
            throw;
        }
        finally { busy = false; run.Enabled = selected.Length > 0 && !string.IsNullOrWhiteSpace(weather.Text); export.Enabled = lastResult is not null; reset.Enabled = rendered.Count > 0; }
    }

    private void ReplacePreview(RhinoDoc doc, AnalysisResult result)
    {
        // Stage the entire replacement before removing the existing preview.
        var replacement = new List<(uint Document, Guid Object)>();
        try
        {
            foreach (var artifact in result.ResultMesh)
            {
                using var mesh = new Mesh();
                foreach (var v in artifact.Vertices) mesh.Vertices.Add(v[0], v[1], v[2]);
                foreach (var f in artifact.Faces)
                    if (f.Length == 3) mesh.Faces.AddFace(f[0], f[1], f[2]); else mesh.Faces.AddFace(f[0], f[1], f[2], f[3]);
                foreach (var color in artifact.VertexColorsArgb) mesh.VertexColors.Add(System.Drawing.Color.FromArgb(color));
                if (!mesh.IsValid || mesh.Faces.Count == 0)
                    throw new InvalidOperationException("RAD-VIEW-002: Invalid result mesh; previous preview preserved.");
                var attributes = new ObjectAttributes { Name = "EnvironmentalHub / SolarRadiation / kWh per m2" };
                var id = doc.Objects.AddMesh(mesh, attributes);
                if (id == Guid.Empty) throw new InvalidOperationException("RAD-VIEW-001: Result mesh display failed; previous preview preserved.");
                replacement.Add((doc.RuntimeSerialNumber, id));
            }
            if (replacement.Count == 0) throw new InvalidOperationException("RAD-VIEW-002: Empty preview; previous preview preserved.");
        }
        catch
        {
            foreach (var item in replacement) doc.Objects.Delete(item.Object, true);
            doc.Views.Redraw();
            throw;
        }
        DeleteOwnedPreview();
        rendered.AddRange(replacement);
    }

    private static string ErrorMessage(Exception error)
    {
        try
        {
            using var json = JsonDocument.Parse(error.Message);
            var diagnostics = json.RootElement.ValueKind == JsonValueKind.Array
                ? json.RootElement : json.RootElement.GetProperty("Diagnostics");
            return string.Join("\n", diagnostics.EnumerateArray().Select(d =>
                $"{d.GetProperty("Code").GetString()}: {d.GetProperty("Message").GetString()}"));
        }
        catch (Exception) { return error.Message; }
    }

    private void DeleteOwnedPreview()
    {
        foreach (var owned in rendered)
        {
            var doc = RhinoDoc.FromRuntimeSerialNumber(owned.Document);
            doc?.Objects.Delete(owned.Object, true); doc?.Views.Redraw();
        }
        rendered.Clear();
    }

    public void ResetResult()
    {
        DeleteOwnedPreview(); lastResult = null; export.Enabled = false; reset.Enabled = false;
        resultLabel.Text = "No result yet"; resultState.Text = "Awaiting analysis";
        status.Text = "Preview cleared • Saved analysis files remain available.";
    }
}
