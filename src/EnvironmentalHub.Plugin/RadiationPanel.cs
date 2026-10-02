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
    private readonly Label geometryLabel = new() { Text = "尚未選取模型", Wrap = WrapMode.Word };
    private readonly TextBox weather = new() { PlaceholderText = "選擇 EPW 檔案" };
    private readonly NumericStepper grid = new() { MinValue = 0.01, MaxValue = 1000, Value = 1, DecimalPlaces = 2, Width = 100 };
    private readonly NumericStepper north = new() { MinValue = -360, MaxValue = 360, Value = 0, Width = 100 };
    private readonly Label status = new() { Text = "選取分析模型與 EPW 氣象檔案。", Wrap = WrapMode.Word };
    private readonly Label resultLabel = new() { Text = "尚無分析結果", Wrap = WrapMode.Word };
    private readonly Button run = new() { Text = "執行日射分析", Enabled = false };
    private readonly Label resultState = new() { Text = "等待分析", Wrap = WrapMode.Word };
    private readonly Button export = new() { Text = "匯出結果 JSON…", Enabled = false };
    private readonly Button reset = new() { Text = "清除預覽", Enabled = false };
    private readonly NumericStepper cpu = new() { MinValue = 1, MaxValue = System.Environment.ProcessorCount, Value = 1, Width = 100 };
    private readonly NumericStepper reflectance = new() { MinValue = 0, MaxValue = 1, Value = 0.2, DecimalPlaces = 2, Increment = 0.05, Width = 100 };
    private readonly NumericStepper offset = new() { MinValue = 0.001, MaxValue = 1000, Value = 0.1, DecimalPlaces = 3, Increment = 0.01, Width = 100 };
    private readonly CheckBox density = new() { Text = "高密度天空", Checked = false };
    private readonly Label periodSummary = HubUi.Hint("全年 · 8,760 小時");
    private readonly Label resultDetail = HubUi.Hint("結果包含氣象、模型與求解器來源資訊。");
    private readonly Panel legend = new();
    private readonly CheckBox targetEnabled = new() { Text = "評估專案目標區間", Checked = false };
    private readonly NumericStepper targetMin = new() { MinValue = 0, MaxValue = 1e9, Value = 0, DecimalPlaces = 1, Width = 100 };
    private readonly NumericStepper targetMax = new() { MinValue = 0, MaxValue = 1e9, Value = 1500, DecimalPlaces = 1, Width = 100 };
    private readonly Label assessment = HubUi.Hint("尚未設定專案評估區間。");
    private readonly Button locate = new() { Text = "在 Rhino 中定位結果", Enabled = false };
    private readonly Button saveScenario = new() { Text = "儲存完成結果為方案", Enabled = false };
    private readonly TextBox scenarioName = new() { Text = "方案 1" };
    private readonly DropDown baseline = new(), candidate = new();
    private readonly Label comparison = HubUi.Hint("儲存至少兩個已完成方案，即可進行比較。");
    private readonly Button exportComparison = new() { Text = "匯出比較 JSON…", Enabled = false };
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
        var select = new Button { Text = "選取分析模型…" };
        var selectContext = new Button { Text = "選取遮蔭環境…" };
        var clearContext = new Button { Text = "清除遮蔭環境" };
        var browse = new Button { Text = "瀏覽 EPW 檔案…" };
        var preflight = new Button { Text = "檢核輸入" };
        select.Click += (_, _) => Guard(() => SelectGeometry(false));
        selectContext.Click += (_, _) => Guard(() => SelectGeometry(true));
        clearContext.Click += (_, _) => { context = []; RefreshGeometry(); InputsChanged(); };
        browse.Click += (_, _) =>
        {
            var dialog = new OpenFileDialog();
            dialog.Filters.Add(new FileFilter("EPW 氣象", ".epw"));
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
            if (report.HasWarnings && MessageBox.Show(this, string.Join("\n", report.Diagnostics.Where(d => d.Severity == "WARNING").Select(HubText.Diagnostic)),
                "仍有以下警告，是否繼續執行？", MessageBoxButtons.YesNo, MessageBoxType.Warning) != DialogResult.Yes) return;
            ExecuteRequest(request with { AcceptWarnings = true });
        });
        reset.Click += (_, _) => ResetResult();
        export.Click += (_, _) => Guard(() =>
        {
            if (lastResult is null) return;
            var dialog = new SaveFileDialog { FileName = "radiation_result.json" };
            dialog.Filters.Add(new FileFilter("分析結果 JSON", ".json"));
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
            dialog.Filters.Add(new FileFilter("方案比較 JSON", ".json"));
            if (dialog.ShowDialog(this) == DialogResult.Ok) File.WriteAllText(dialog.FileName, ExportComparisonJson());
        });
        var annual = new Button { Text = "使用全年氣象" };
        annual.Click += (_, _) => { hours = []; periodSummary.Text = "全年 · 8,760 小時"; InputsChanged(); };
        var importedWeather = new Button { Text = "套用已匯入的氣象選取" };
        importedWeather.Click += (_, _) => Guard(UseImportedWeather);
        var importedPeriod = new Button { Text = "套用已建立的分析期間" };
        importedPeriod.Click += (_, _) => Guard(UseCompletedPeriod);
        var model = HubUi.Section("01  幾何／模型",HubTopic.Model, select, geometryLabel, selectContext, clearContext,
            Hint("支援 Brep 或網格；遮蔭環境為選填。"));
        var climate = HubUi.Section("02  環境／氣象",HubTopic.Environment, weather, browse, importedWeather, periodSummary, importedPeriod, annual,
            Hint("先於環境工具匯入 EPW 或建立期間，再於此套用完成的選取。僅支援整數小時；次小時值不會自動四捨五入。"));
        var settings = new DynamicLayout { Spacing = new Size(8, 8) };
        var settingsFields = new DynamicLayout { Spacing = new Size(8, 8) };
        settingsFields.AddRow(new Label { Text = "網格間距 (m)" }, grid);
        settingsFields.AddRow(new Label { Text = "北向旋轉 (°)" }, north);
        settings.AddRow(settingsFields);
        settings.AddRow(Hint("入射太陽能量 · kWh/m²。網格間距與感測點偏移均使用公尺，不受模型單位影響。"));
        var advancedFields = new DynamicLayout { Spacing = new Size(8, 8) };
        advancedFields.AddRow(new Label { Text = "CPU 數量" }, cpu);
        advancedFields.AddRow(new Label { Text = "地表反射率 (0–1)" }, reflectance);
        advancedFields.AddRow(new Label { Text = "感測點偏移 (m)" }, offset);
        var advanced = new DynamicLayout { Spacing = new Size(8, 8), Visible = false };
        advanced.AddRow(advancedFields); advanced.AddRow(density);
        advanced.AddRow(Hint("預設：1 CPU、反射率 0.20、偏移 0.10 m、標準天空。高密度天空會提高解析度與計算時間。"));
        var reveal = new CheckBox { Text = "進階設定", Checked = false };
        reveal.CheckedChanged += (_, _) => advanced.Visible = reveal.Checked == true;
        settings.AddRow(reveal); settings.AddRow(advanced);
        var execution = HubUi.Section("04  檢核／執行",HubTopic.Run, preflight, run, status,
            Hint("求解採同步執行，期間 Rhino 可能暫時無法操作；目前尚不支援取消。"));
        var targetFields = new DynamicLayout { Spacing = new Size(8, 8) };
        targetFields.AddRow(new Label { Text = "區間下限 (kWh/m²)" }, targetMin);
        targetFields.AddRow(new Label { Text = "區間上限 (kWh/m²)" }, targetMax);
        var targetBody = new DynamicLayout { Spacing = new Size(8, 8), Visible = false };
        targetBody.AddRow(targetFields); targetBody.AddRow(Hint("包含區間上下限；精度 0.1 kWh/m²。僅作專案評估，不代表法規合規判定。"));
        targetEnabled.CheckedChanged += (_, _) => targetBody.Visible = targetEnabled.Checked == true;
        var results = HubUi.Section("05  分析結果",HubTopic.Results, resultState, resultLabel, legend, resultDetail, targetEnabled, targetBody, assessment, locate, reset);
        var choices = new DynamicLayout { Spacing = new Size(8, 8) };
        choices.AddRow(new Label { Text = "基準方案" }, baseline); choices.AddRow(new Label { Text = "比較方案" }, candidate);
        var compareExport = HubUi.Section("06  比較／匯出",HubTopic.Compare, scenarioName, saveScenario, choices, comparison, exportComparison, export,
            Hint("方案於當次工作階段保留完成結果與輸入來源；關閉 Rhino 前請匯出比較資料。"));
        var layout = new DynamicLayout { Padding = 16, Spacing = new Size(8, 14) };
        layout.AddRow(HubUi.Header("日射分析", "分析建築表面的入射太陽能量。模型 → 氣象 → 設定 → 檢核 → 結果。",typeof(RadiationPanel)));
        layout.AddRow(HubUi.Navigation(typeof(RadiationPanel)));
        foreach (var label in new[] { "01  幾何／模型", "02  環境／氣象", "03  模擬設定", "04  檢核／執行", "05  分析結果", "06  比較／匯出" }) stage.Items.Add(label);
        stage.SelectedIndex = 0;
        var jump = new Button { Text = "前往階段" }; jump.Click += (_, _) => ShowStage(stage.SelectedIndex);
        var stageNavigation = new DynamicLayout { Spacing = new Size(8, 8) }; stageNavigation.AddRow(stage, jump);
        layout.AddRow(model); layout.AddRow(climate);
        var simulation = HubUi.Section("03  模擬設定",HubTopic.Settings, settings);
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
    private void RefreshGeometry() => geometryLabel.Text = $"{selected.Length} 個分析物件 · {context.Length} 個遮蔽物件";
    private void InputsChanged()
    {
        if (updatingInputs || busy) return;
        run.Enabled = selected.Length > 0 && !string.IsNullOrWhiteSpace(weather.Text);
        status.Text = "輸入已變更 · 執行前請重新檢核。";
        if (lastResult is not null) resultState.Text = "前次結果 · 輸入已變更，重新執行以更新。";
    }

    private void SelectGeometry(bool isContext)
    {
        var currentDocument = RhinoDoc.ActiveDoc ?? throw new InvalidOperationException("RAD-DOC-001: No active document.");
        if (selectedDocument != 0 && selectedDocument != currentDocument.RuntimeSerialNumber)
        {
            selected = []; context = [];
        }
        using var picker = new GetObject();
        picker.SetCommandPrompt(isContext ? "選取遮蔭環境" : "選取日射分析模型");
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
    private static string FormatPreflight(PreflightReport report) => report.Diagnostics.Length == 0 ? "輸入檢核通過 · 可執行" :
        (report.CanRun ? "可執行，但仍有警告\n" : "請修正以下輸入\n") + string.Join("\n", report.Diagnostics.Select(HubText.Diagnostic));
    private void Guard(Action action)
    {
        try { action(); } catch (Exception e) { status.Text = "分析未完成\n" + HubText.Error(e); }
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
            if (lastResult is not null) resultState.Text = "前次結果 · 新輸入未通過檢核";
            throw new InvalidOperationException(status.Text);
        }
        selected = request.GeometryIds; context = request.ContextIds; selectedDocument = doc.RuntimeSerialNumber;
        updatingInputs = true;
        try
        {
            RefreshGeometry(); weather.Text = request.WeatherFile; grid.Value = request.GridMetres; north.Value = request.NorthDegrees;
            cpu.Value = request.Settings.CpuCount; reflectance.Value = request.Settings.GroundReflectance; offset.Value = request.Settings.OffsetMetres;
            density.Checked = request.Settings.HighDensity; hours = request.HoursOfYear.ToArray(); quality = request.Quality;
            periodSummary.Text = hours.Length == 0 ? "全年 · 8,760 小時" : $"{hours.Length:N0} 個已選小時 · 保留原始輸入";
        }
        finally { updatingInputs = false; }
        busy = true; run.Enabled = false; export.Enabled = false; reset.Enabled = false; locate.Enabled = false; saveScenario.Enabled = false;
        status.Text = "正在執行原生 Ladybug 日射分析…";
        if (lastResult is not null) resultState.Text = "前次結果 · 新分析執行中";
        try
        {
            var result = Adapter(doc).Execute(request);
            ReplacePreview(doc, result);
            lastResult = result;
            resultState.Text = result.InputParameters.HoursOfYear.Length == 0
                ? "目前結果 · 全年入射太陽能量"
                : $"目前結果 · {result.InputParameters.HoursOfYear.Length} 個已選小時";
            resultLabel.Text = $"平均值 {result.Statistics.Mean:F3}\n最小值 {result.Statistics.Minimum:F3} • 最大值 {result.Statistics.Maximum:F3}\n{result.Statistics.Count} 格網格 · {result.Units}";
            resultLabel.Font = new Eto.Drawing.Font(SystemFont.Bold, 13);
            legend.Content = ResultPresentation.Legend(result);
            resultDetail.Text = $"{result.Metadata["Location"]} · {result.Timestamp.ToLocalTime():yyyy-MM-dd HH:mm}\n{result.ExecutionTimeSeconds:F1} s · {result.Warnings.Length} 則警告\n{result.InputParameters.GridMetres:g} m 網格 · 北向 {result.InputParameters.NorthDegrees:g}°\n{result.Solver}";
            UpdateAssessment();
            status.Text = "分析完成 · " + result.Metadata["Location"];
            doc.Views.Redraw();
            ShowStage(4);
            return JsonSerializer.Serialize(result);
        }
        catch (Exception e)
        {
            status.Text = "分析未完成\n" + ErrorMessage(e);
            if (lastResult is not null) resultState.Text = "前次結果 · 新分析失敗";
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

    private static string ErrorMessage(Exception error) => HubText.Error(error);

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
        resultLabel.Text = "尚無分析結果"; resultState.Text = "等待分析";
        legend.Content = null; resultDetail.Text = "結果包含氣象、模型與求解器來源資訊。"; UpdateAssessment();
        status.Text = "預覽已清除 · 已儲存的分析檔案仍保留。";
    }

    private void UpdateAssessment()
    {
        assessment.Text = lastResult is null ? "等待分析" : targetEnabled.Checked != true ? "尚未設定專案評估區間。" :
            targetMin.Value > targetMax.Value ? "評估區間無效 · 下限不得高於上限。" :
            ResultPresentation.Assessment(lastResult, targetMin.Value, targetMax.Value);
    }

    public void UseImportedWeather()
    {
        var panel = Rhino.UI.Panels.GetPanel<WeatherPanel>(RequireDocument());
        var json = panel?.CompletedSelectionJson ?? throw new InvalidOperationException("請先在 EPW 氣象模組匯入資料。");
        var selection = JsonSerializer.Deserialize<WeatherRequest>(json)!;
        updatingInputs = true;
        try { weather.Text = selection.WeatherFile; hours = selection.HoursOfYear.ToArray(); RefreshPeriod(); }
        finally { updatingInputs = false; }
        InputsChanged();
    }

    public void UseCompletedPeriod()
    {
        var panel = Rhino.UI.Panels.GetPanel<TimePanel>(RequireDocument());
        var json = panel?.CompletedResultJson ?? throw new InvalidOperationException("請先在時間與分析期間模組建立期間。");
        using var result = JsonDocument.Parse(json);
        if (!result.RootElement.TryGetProperty("HoursOfYear", out var values))
            throw new InvalidOperationException("請建立分析期間；日期換算結果不能用作期間。");
        var supplied = values.EnumerateArray().Select(v => v.GetDouble()).ToArray();
        if (supplied.Length == 0 || supplied.Any(h => !double.IsFinite(h) || h != Math.Truncate(h) || h < 0 || h >= 8760) || supplied.Distinct().Count() != supplied.Length)
            throw new InvalidOperationException("日射分析僅接受不重複的整數年時數 0–8759。請使用每小時 1 步；次小時值不會自動四捨五入。");
        hours = supplied.Select(h => (int)h).ToArray(); RefreshPeriod(); InputsChanged();
    }

    private void RefreshPeriod() => periodSummary.Text = hours.Length == 0 ? "全年 · 8,760 小時" : $"{hours.Length:N0} 個已選小時 · 保留完成的選取";

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
            throw new ArgumentException("目標區間須為有限值，且介於 0 至 1,000,000,000；包含上下限。");
        if (minimum != Math.Round(minimum, 1) || maximum != Math.Round(maximum, 1))
            throw new ArgumentException("目標區間精度為 0.1 kWh/m²，請明確調整輸入上下限。");
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
        if (busy || lastResult is null) throw new InvalidOperationException("請先完成分析，再儲存方案。");
        name = name.Trim(); if (name.Length == 0 || name.Length > 80) throw new ArgumentException("方案名稱須為 1–80 個字元。");
        if (scenarios.Any(s => s.Name.Equals(name, StringComparison.OrdinalIgnoreCase))) throw new ArgumentException("請使用不重複的方案名稱。");
        if (scenarios.Count >= 20) throw new InvalidOperationException("本次工作階段已達 20 個方案上限；請先匯出，再建立新的工作階段。");
        scenarios.Add((name, lastResult)); baseline.Items.Add(name); candidate.Items.Add(name);
        if (baseline.SelectedIndex < 0) baseline.SelectedIndex = 0;
        candidate.SelectedIndex = scenarios.Count - 1; scenarioName.Text = "方案 " + (scenarios.Count + 1);
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
        comparison.Text = baseline.SelectedIndex == candidate.SelectedIndex ? "請選取兩個不同的方案。" :
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
