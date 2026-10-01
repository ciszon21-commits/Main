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
    private readonly NumericStepper cpu = new() { MinValue = 1, MaxValue = System.Environment.ProcessorCount, Value = 1, Width = 100 };
    private readonly NumericStepper reflectance = new() { MinValue = 0, MaxValue = 1, Value = 0.2, DecimalPlaces = 2, Increment = 0.05, Width = 100 };
    private readonly NumericStepper offset = new() { MinValue = 0.001, MaxValue = 1000, Value = 0.1, DecimalPlaces = 3, Increment = 0.01, Width = 100 };
    private readonly CheckBox density = new() { Text = "High-density sky", Checked = false };
    private readonly Label periodSummary = HubUi.Hint("Annual · 8,760 hours");
    private readonly Label resultDetail = HubUi.Hint("Results include the weather, geometry and solver provenance.");
    private readonly Panel legend = new();
    private readonly CheckBox targetEnabled = new() { Text = "Evaluate project target range", Checked = false };
    private readonly NumericStepper targetMin = new() { MinValue = 0, MaxValue = 1e9, Value = 0, DecimalPlaces = 1, Width = 100 };
    private readonly NumericStepper targetMax = new() { MinValue = 0, MaxValue = 1e9, Value = 1500, DecimalPlaces = 1, Width = 100 };
    private readonly Label assessment = HubUi.Hint("No project criterion configured.");
    private readonly Button locate = new() { Text = "Locate result in Rhino", Enabled = false };
    private readonly Button saveScenario = new() { Text = "Save completed result as scenario", Enabled = false };
    private readonly TextBox scenarioName = new() { Text = "Scenario 1" };
    private readonly DropDown baseline = new(), candidate = new();
    private readonly Label comparison = HubUi.Hint("Save at least two completed results to compare.");
    private readonly Button exportComparison = new() { Text = "Export comparison JSON…", Enabled = false };
    private readonly List<(string Name, AnalysisResult Result)> scenarios = [];
    private readonly DropDown stage = new();
    private readonly Scrollable scroll;
    private readonly Control[] stages;
    private int[] hours = [];
    private string quality = "Standard";
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
    public int ScenarioCount => scenarios.Count;
    public string ComparisonText => comparison.Text;
    public string AssessmentText => assessment.Text;

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
        foreach (var number in new[] { cpu, reflectance, offset }) number.ValueChanged += (_, _) => InputsChanged();
        density.CheckedChanged += (_, _) => InputsChanged();
        targetEnabled.CheckedChanged += (_, _) => UpdateAssessment();
        targetMin.ValueChanged += (_, _) => UpdateAssessment(); targetMax.ValueChanged += (_, _) => UpdateAssessment();
        locate.Click += (_, _) => Guard(LocateResult);
        saveScenario.Click += (_, _) => Guard(() => SaveScenario(scenarioName.Text));
        baseline.SelectedIndexChanged += (_, _) => RefreshComparison(); candidate.SelectedIndexChanged += (_, _) => RefreshComparison();
        exportComparison.Click += (_, _) => Guard(() =>
        {
            var dialog = new SaveFileDialog { FileName = "radiation_comparison.json" };
            dialog.Filters.Add(new FileFilter("Comparison JSON", ".json"));
            if (dialog.ShowDialog(this) == DialogResult.Ok) File.WriteAllText(dialog.FileName, ExportComparisonJson());
        });
        var annual = new Button { Text = "Use annual weather" };
        annual.Click += (_, _) => { hours = []; periodSummary.Text = "Annual · 8,760 hours"; InputsChanged(); };
        var importedWeather = new Button { Text = "Use imported EPW selection" };
        importedWeather.Click += (_, _) => Guard(UseImportedWeather);
        var importedPeriod = new Button { Text = "Use completed analysis period" };
        importedPeriod.Click += (_, _) => Guard(UseCompletedPeriod);
        var model = HubUi.Section("01  Geometry / Model",HubTopic.Model, select, geometryLabel, selectContext, clearContext,
            Hint("Brep or mesh • Shading context is optional"));
        var climate = HubUi.Section("02  Environment / Weather",HubTopic.Environment, weather, browse, importedWeather, periodSummary, importedPeriod, annual,
            Hint("Import EPW or build a period in Environment tools, then explicitly use the completed selection here. Hourly periods only; subhour values are never rounded."));
        var settings = new DynamicLayout { Spacing = new Size(8, 8) };
        var settingsFields = new DynamicLayout { Spacing = new Size(8, 8) };
        settingsFields.AddRow(new Label { Text = "Grid spacing (m)" }, grid);
        settingsFields.AddRow(new Label { Text = "North rotation (°)" }, north);
        settings.AddRow(settingsFields);
        settings.AddRow(Hint("Incident energy · kWh/m² · Grid and sensor offset use metres, regardless of model units."));
        var advancedFields = new DynamicLayout { Spacing = new Size(8, 8) };
        advancedFields.AddRow(new Label { Text = "CPU count" }, cpu);
        advancedFields.AddRow(new Label { Text = "Ground reflectance (0–1)" }, reflectance);
        advancedFields.AddRow(new Label { Text = "Sensor offset (m)" }, offset);
        var advanced = new DynamicLayout { Spacing = new Size(8, 8), Visible = false };
        advanced.AddRow(advancedFields); advanced.AddRow(density);
        advanced.AddRow(Hint("Defaults: 1 CPU · 0.20 reflectance · 0.10 m offset · standard sky. High density increases sky resolution and computation time."));
        var reveal = new CheckBox { Text = "Advanced settings", Checked = false };
        reveal.CheckedChanged += (_, _) => advanced.Visible = reveal.Checked == true;
        settings.AddRow(reveal); settings.AddRow(advanced);
        var execution = HubUi.Section("04  Validate / Run",HubTopic.Run, preflight, run, status,
            Hint("Rhino may pause while the synchronous solver runs. Cancellation is not available yet."));
        var targetFields = new DynamicLayout { Spacing = new Size(8, 8) };
        targetFields.AddRow(new Label { Text = "Minimum (kWh/m²)" }, targetMin);
        targetFields.AddRow(new Label { Text = "Maximum (kWh/m²)" }, targetMax);
        var targetBody = new DynamicLayout { Spacing = new Size(8, 8), Visible = false };
        targetBody.AddRow(targetFields); targetBody.AddRow(Hint("Inclusive bounds · 0.1 kWh/m² precision · Project criterion only; no regulatory compliance claim."));
        targetEnabled.CheckedChanged += (_, _) => targetBody.Visible = targetEnabled.Checked == true;
        var results = HubUi.Section("05  Results",HubTopic.Results, resultState, resultLabel, legend, resultDetail, targetEnabled, targetBody, assessment, locate, reset);
        var choices = new DynamicLayout { Spacing = new Size(8, 8) };
        choices.AddRow(new Label { Text = "Baseline" }, baseline); choices.AddRow(new Label { Text = "Candidate" }, candidate);
        var compareExport = HubUi.Section("06  Compare / Export",HubTopic.Compare, scenarioName, saveScenario, choices, comparison, exportComparison, export,
            Hint("Session scenarios retain completed results and input provenance. Save a comparison export before closing Rhino."));
        var layout = new DynamicLayout { Padding = 16, Spacing = new Size(8, 14) };
        layout.AddRow(HubUi.Header("Solar radiation", "Incident solar energy on building surfaces. Model → weather → settings → validate → results.",typeof(RadiationPanel)));
        layout.AddRow(HubUi.Navigation(typeof(RadiationPanel)));
        foreach (var label in new[] { "01  Geometry / Model", "02  Environment / Weather", "03  Simulation settings", "04  Validate / Run", "05  Results", "06  Compare / Export" }) stage.Items.Add(label);
        stage.SelectedIndex = 0;
        var jump = new Button { Text = "Go to stage" }; jump.Click += (_, _) => ShowStage(stage.SelectedIndex);
        var stageNavigation = new DynamicLayout { Spacing = new Size(8, 8) }; stageNavigation.AddRow(stage, jump);
        layout.AddRow(model); layout.AddRow(climate);
        var simulation = HubUi.Section("03  Simulation settings",HubTopic.Settings, settings);
        stages = [model, climate, simulation, execution, results, compareExport];
        layout.AddRow(simulation);
        layout.AddRow(execution); layout.AddRow(results); layout.AddRow(compareExport); layout.Add(null);
        scroll = new Scrollable { Content = layout, ExpandContentWidth = true };
        // WPF scroll viewers measure content at infinite width. Bound the layout
        // to its viewport so long paths cannot push button captions offscreen.
        scroll.SizeChanged += (_, _) => layout.Width = Math.Max(120, scroll.ClientSize.Width - 20);
        var host = new DynamicLayout { Spacing = new Size(8, 8) };
        host.AddRow(new Panel { Padding = new Padding(16, 8), Content = stageNavigation });
        host.Add(scroll, yscale: true);
        Content = host;
    }

    private static Label Hint(string text) => new() { Text = text, Wrap = WrapMode.Word, TextColor = SystemColors.ControlText };
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
        HoursOfYear = hours, Quality = quality,
        Settings = new() { CpuCount = (int)cpu.Value, GroundReflectance = reflectance.Value, OffsetMetres = offset.Value, HighDensity = density.Checked == true },
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
        try
        {
            RefreshGeometry(); weather.Text = request.WeatherFile; grid.Value = request.GridMetres; north.Value = request.NorthDegrees;
            cpu.Value = request.Settings.CpuCount; reflectance.Value = request.Settings.GroundReflectance; offset.Value = request.Settings.OffsetMetres;
            density.Checked = request.Settings.HighDensity; hours = request.HoursOfYear.ToArray(); quality = request.Quality;
            periodSummary.Text = hours.Length == 0 ? "Annual · 8,760 hours" : $"{hours.Length:N0} selected hours · Original request retained";
        }
        finally { updatingInputs = false; }
        busy = true; run.Enabled = false; export.Enabled = false; reset.Enabled = false; locate.Enabled = false; saveScenario.Enabled = false;
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
            resultLabel.Font = new Eto.Drawing.Font(SystemFont.Bold, 13);
            legend.Content = ResultPresentation.Legend(result);
            resultDetail.Text = $"{result.Metadata["Location"]} · {result.Timestamp.ToLocalTime():yyyy-MM-dd HH:mm}\n{result.ExecutionTimeSeconds:F1} s · {result.Warnings.Length} warnings\n{result.InputParameters.GridMetres:g} m grid · North {result.InputParameters.NorthDegrees:g}°\n{result.Solver}";
            UpdateAssessment();
            status.Text = "Complete • " + result.Metadata["Location"];
            doc.Views.Redraw();
            ShowStage(4);
            return JsonSerializer.Serialize(result);
        }
        catch (Exception e)
        {
            status.Text = "Analysis could not complete\n" + ErrorMessage(e);
            if (lastResult is not null) resultState.Text = "Previous result • New analysis failed";
            throw;
        }
        finally { busy = false; run.Enabled = selected.Length > 0 && !string.IsNullOrWhiteSpace(weather.Text); export.Enabled = saveScenario.Enabled = lastResult is not null; reset.Enabled = locate.Enabled = rendered.Count > 0; }
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
        DeleteOwnedPreview(); lastResult = null; export.Enabled = saveScenario.Enabled = false; reset.Enabled = locate.Enabled = false;
        resultLabel.Text = "No result yet"; resultState.Text = "Awaiting analysis";
        legend.Content = null; resultDetail.Text = "Results include the weather, geometry and solver provenance."; UpdateAssessment();
        status.Text = "Preview cleared • Saved analysis files remain available.";
    }

    private void UpdateAssessment()
    {
        assessment.Text = lastResult is null ? "Awaiting analysis" : targetEnabled.Checked != true ? "No project criterion configured." :
            targetMin.Value > targetMax.Value ? "Invalid criterion · Minimum must not exceed maximum." :
            ResultPresentation.Assessment(lastResult, targetMin.Value, targetMax.Value);
    }

    public void UseImportedWeather()
    {
        var panel = Rhino.UI.Panels.GetPanel<WeatherPanel>(RequireDocument());
        var json = panel?.CompletedSelectionJson ?? throw new InvalidOperationException("Import weather in the EPW weather module first.");
        var selection = JsonSerializer.Deserialize<WeatherRequest>(json)!;
        updatingInputs = true;
        try { weather.Text = selection.WeatherFile; hours = selection.HoursOfYear.ToArray(); RefreshPeriod(); }
        finally { updatingInputs = false; }
        InputsChanged();
    }

    public void UseCompletedPeriod()
    {
        var panel = Rhino.UI.Panels.GetPanel<TimePanel>(RequireDocument());
        var json = panel?.CompletedResultJson ?? throw new InvalidOperationException("Build an analysis period in Time & periods first.");
        using var result = JsonDocument.Parse(json);
        if (!result.RootElement.TryGetProperty("HoursOfYear", out var values))
            throw new InvalidOperationException("Build an analysis period; a date conversion is not a period.");
        var supplied = values.EnumerateArray().Select(v => v.GetDouble()).ToArray();
        if (supplied.Length == 0 || supplied.Any(h => !double.IsFinite(h) || h != Math.Truncate(h) || h < 0 || h >= 8760) || supplied.Distinct().Count() != supplied.Length)
            throw new InvalidOperationException("Radiation accepts unique hourly indices 0–8759. Use 1 step/hour; subhour values are not rounded.");
        hours = supplied.Select(h => (int)h).ToArray(); RefreshPeriod(); InputsChanged();
    }

    private void RefreshPeriod() => periodSummary.Text = hours.Length == 0 ? "Annual · 8,760 hours" : $"{hours.Length:N0} selected hours · Completed selection retained";

    public void ShowStage(int index)
    {
        if (index < 0 || index >= stages.Length) throw new ArgumentOutOfRangeException(nameof(index));
        stage.SelectedIndex = index;
        var origin = scroll.Content.PointToScreen(PointF.Empty);
        var target = stages[index].PointToScreen(PointF.Empty);
        scroll.ScrollPosition = new Eto.Drawing.Point(0, Math.Max(0, (int)(target.Y - origin.Y)));
    }

    public void SetTargetRange(double minimum, double maximum)
    {
        if (!double.IsFinite(minimum) || !double.IsFinite(maximum) || minimum < 0 || maximum > 1e9 || minimum > maximum)
            throw new ArgumentException("Target range must be finite, inclusive and between 0 and 1,000,000,000.");
        if (minimum != Math.Round(minimum, 1) || maximum != Math.Round(maximum, 1))
            throw new ArgumentException("Target range uses 0.1 kWh/m² precision; round the requested bounds explicitly.");
        targetMin.Value = minimum; targetMax.Value = maximum; targetEnabled.Checked = true; UpdateAssessment();
    }

    public void LocateResult()
    {
        var doc = RequireDocument();
        if (rendered.Count == 0 || rendered.Any(x => x.Document != doc.RuntimeSerialNumber))
            throw new InvalidOperationException("RAD-VIEW-003: Open the result document before locating the preview.");
        var bounds = BoundingBox.Empty;
        foreach (var owned in rendered)
        {
            var obj = doc.Objects.FindId(owned.Object);
            if (obj is not null) bounds.Union(obj.Geometry.GetBoundingBox(true));
        }
        if (!bounds.IsValid || doc.Views.ActiveView is null) throw new InvalidOperationException("RAD-VIEW-004: No preview or active viewport.");
        doc.Views.ActiveView.ActiveViewport.ZoomBoundingBox(bounds); doc.Views.Redraw();
    }

    public string SaveScenario(string name)
    {
        if (busy || lastResult is null) throw new InvalidOperationException("Complete an analysis before saving a scenario.");
        name = name.Trim(); if (name.Length == 0 || name.Length > 80) throw new ArgumentException("Scenario name must contain 1–80 characters.");
        if (scenarios.Any(s => s.Name.Equals(name, StringComparison.OrdinalIgnoreCase))) throw new ArgumentException("Choose a unique scenario name.");
        if (scenarios.Count >= 20) throw new InvalidOperationException("Session limit of 20 scenarios reached; export before starting a new session.");
        scenarios.Add((name, lastResult)); baseline.Items.Add(name); candidate.Items.Add(name);
        if (baseline.SelectedIndex < 0) baseline.SelectedIndex = 0;
        candidate.SelectedIndex = scenarios.Count - 1; scenarioName.Text = "Scenario " + (scenarios.Count + 1);
        exportComparison.Enabled = scenarios.Count >= 2; RefreshComparison();
        return JsonSerializer.Serialize(new { Name = name, Result = lastResult });
    }

    public string CompareScenarios(int baselineIndex, int candidateIndex)
    {
        if (baselineIndex < 0 || candidateIndex < 0 || baselineIndex >= scenarios.Count || candidateIndex >= scenarios.Count)
            throw new ArgumentOutOfRangeException(nameof(baselineIndex));
        baseline.SelectedIndex = baselineIndex; candidate.SelectedIndex = candidateIndex; RefreshComparison(); return comparison.Text;
    }

    private void RefreshComparison()
    {
        if (baseline.SelectedIndex < 0 || candidate.SelectedIndex < 0 || baseline.SelectedIndex >= scenarios.Count || candidate.SelectedIndex >= scenarios.Count) return;
        comparison.Text = baseline.SelectedIndex == candidate.SelectedIndex ? "Select two different scenarios." :
            ResultPresentation.Compare(scenarios[baseline.SelectedIndex].Name, scenarios[baseline.SelectedIndex].Result,
                scenarios[candidate.SelectedIndex].Name, scenarios[candidate.SelectedIndex].Result);
    }

    public string ExportComparisonJson() => JsonSerializer.Serialize(new
    {
        SchemaVersion = "1.0", BaselineIndex = baseline.SelectedIndex, CandidateIndex = candidate.SelectedIndex,
        Interpretation = comparison.Text, Metric = "Arithmetic mean per analysis cell; not area-weighted",
        ProjectCriterion = targetEnabled.Checked == true && targetMin.Value <= targetMax.Value
            ? new { Minimum = targetMin.Value, Maximum = targetMax.Value, Units = "kWh/m2", Assessment = assessment.Text, Basis = "Current completed result; inclusive cell values; not regulatory compliance" } : null,
        Scenarios = scenarios.Select(s => new { s.Name, s.Result })
    }, new JsonSerializerOptions { WriteIndented = true });
}
