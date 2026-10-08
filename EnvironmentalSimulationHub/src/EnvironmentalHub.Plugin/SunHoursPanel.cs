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

public sealed class SunHoursPanel : Panel
{
    private Guid[] selected = [], context = [];
    private uint inputDocument; private string? inputUnits;
    private SunPathRequest? source; private SunHoursResult? result; private bool updating, busy;
    private readonly List<(uint Document, Guid Object)> owned = [], hiddenOther = [];
    private readonly NumericStepper displayOffset = Number(0, 1, .002, 3);
    private readonly CheckBox visible = new() { Text = "顯示結果網格", Checked = true }, solo = new() { Text = "暫時隱藏其他 Hub 預覽", Checked = true };
    private readonly List<SunHoursScenario> scenarios = [];
    private readonly Label archiveStatus = HubUi.Hint("匯入歷史方案只恢復比較資料，不會套用模型或重新求解。");
    private readonly Button importScenarios = new() { Text = "匯入方案比較 JSON…" };
    private readonly NumericStepper grid = Number(.01, 1000000, 1, 2), offset = Number(0, 1000000, .1, 3), cpu = Number(1, 128, 1);
    private readonly NumericStepper targetMin = Number(0, 525600, 2, 2), targetMax = Number(0, 525600, 6, 2);
    private readonly DropDown rate = new(), baseline = new(), candidate = new(), stage = new();
    private readonly CheckBox blocks = new() { Text = "分析模型參與自遮蔭", Checked = true }, reveal = new() { Text = "進階設定", Checked = false }, target = new() { Text = "評估專案目標區間", Checked = false };
    private readonly Label geometry = HubUi.Hint("尚未選取分析面"), sunSummary = HubUi.Hint("先完成太陽路徑，再傳入來源。"), status = Text("等待輸入"), state = HubUi.Hint("尚無完成結果"), detail = HubUi.Hint(""), assessment = HubUi.Hint("尚未設定專案目標。"), comparison = HubUi.Hint("儲存兩個完成結果以比較。"), kpi = Text("尚無分析結果");
    private readonly Panel legend = new();
    private readonly Button showSummary = new() { Text = "展開圖像摘要（試驗）", Enabled = false }, exportSummary = new() { Text = "匯出圖像摘要 HTML…", Enabled = false };
    private readonly Panel summaryHost = new() { Visible = false };
    private SunHoursWebSummary? webSummary;
    private readonly Button run = new() { Text = "執行日照時數分析", Enabled = false }, locate = new() { Text = "定位結果網格", Enabled = false }, clear = new() { Text = "清除本模組預覽", Enabled = false }, export = new() { Text = "匯出完整結果 JSON…", Enabled = false }, save = new() { Text = "儲存完成結果為方案", Enabled = false }, exportCompare = new() { Text = "匯出比較 JSON…", Enabled = false };
    private readonly TextBox scenarioName = new() { Text = "方案 1" };
    private readonly Control[] sections; private readonly Scrollable scroll;
    public string? CompletedResultJson => result is null ? null : JsonSerializer.Serialize(result);
    public string SummaryText => kpi.Text;
    public string StatusText => status.Text;
    public string ComparisonText => comparison.Text;
    public string AssessmentText => assessment.Text;
    public int ScenarioCount => scenarios.Count;
    private static NumericStepper Number(double min, double max, double value, int places = 0) => new() { MinValue = min, MaxValue = max, Value = value, DecimalPlaces = places, Increment = Math.Pow(10, -places) };
    private static Label Text(string value) => new() { Text = value, UseMnemonic = false, Wrap = WrapMode.Word };
    public SunHoursPanel()
    {
        foreach (var r in SunHoursSampling.SupportedRates) rate.Items.Add($"{r} 步／小時 · {60.0 / r:G} 分鐘／步"); rate.SelectedIndex = 0;
        var select = new Button { Text = "選取分析面／模型…" }; select.Click += (_, _) => Guard(() => Select(false));
        var shade = new Button { Text = "選取遮蔭環境…" }; shade.Click += (_, _) => Guard(() => Select(true));
        var noShade = new Button { Text = "清除遮蔭選取" }; noShade.Click += (_, _) => { context = []; Changed(); RefreshGeometry(); };
        var region = new Button { Text = "定位分析區域" }; region.Click += (_, _) => Guard(LocateGeometry);
        var transfer = new Button { Text = "使用太陽路徑的完成結果" }; transfer.Click += (_, _) => Guard(UseCompletedSunPath);
        var openSun = new Button { Text = "前往太陽路徑" }; openSun.Click += (_, _) => HubUi.OpenModule(this, typeof(SunPathPanel));
        var validate = new Button { Text = "檢核輸入" }; validate.Click += (_, _) => Guard(() => status.Text = Format(Adapter(RequireDocument()).Preflight(Request())));
        run.Click += (_, _) => Guard(() => { var r = Request(); var report = Adapter(RequireDocument()).Preflight(r); status.Text = Format(report); if (!report.CanRun) return; if (report.HasWarnings && MessageBox.Show(this, string.Join("\n", report.Diagnostics.Select(HubText.Diagnostic)), "警告仍存在，是否繼續？", MessageBoxButtons.YesNo, MessageBoxType.Warning) != DialogResult.Yes) return; ExecuteRequest(r with { AcceptWarnings = true }); });
        foreach (var n in new[] { grid, offset, cpu }) n.ValueChanged += (_, _) => Changed(); blocks.CheckedChanged += (_, _) => Changed(); rate.SelectedIndexChanged += (_, _) => { RefreshSource(); Changed(); };
        locate.Click += (_, _) => Guard(LocateResult); clear.Click += (_, _) => DeletePreview(); export.Click += (_, _) => Guard(() => SaveJson("sun_hours_result.json", ExportResultJson()));
        save.Click += (_, _) => Guard(() => SaveScenario(scenarioName.Text)); baseline.SelectedIndexChanged += (_, _) => RefreshComparison(); candidate.SelectedIndexChanged += (_, _) => RefreshComparison(); exportCompare.Click += (_, _) => Guard(() => SaveJson("sun_hours_comparison.json", ExportComparisonJson()));
        importScenarios.Click += (_, _) => ImportFile();
        showSummary.Click += (_, _) => Guard(() => { summaryHost.Visible = !summaryHost.Visible; showSummary.Text = summaryHost.Visible ? "收合圖像摘要" : "展開圖像摘要（試驗）"; RefreshSummary(); });
        exportSummary.Click += (_, _) => Guard(() => { using var dialog = new SaveFileDialog { Title = "匯出完成結果圖像摘要", FileName = "sun_hours_summary.html" }; dialog.Filters.Add(new FileFilter("離線圖像摘要 HTML", ".html")); if (dialog.ShowDialog(this) == DialogResult.Ok) File.WriteAllText(dialog.FileName, ExportSummaryHtml(), System.Text.Encoding.UTF8); });
        visible.CheckedChanged += (_, _) => Guard(ApplyVisibility); solo.CheckedChanged += (_, _) => Guard(ApplyOtherVisibility);
        displayOffset.ValueChanged += (_, _) => Guard(() => { if (result is not null && !busy) { ReplacePreview(RequireDocument(), result); ApplyVisibility(); } });
        target.CheckedChanged += (_, _) => UpdateAssessment(); targetMin.ValueChanged += (_, _) => UpdateAssessment(); targetMax.ValueChanged += (_, _) => UpdateAssessment();
        var advanced = new DynamicLayout { Spacing = new Size(8, 8), Visible = false };
        var advancedFields = new DynamicLayout { Spacing = new Size(8, 8) };
        advancedFields.AddRow(new Label { Text = "感測點偏移 (m)" }, offset); advancedFields.AddRow(new Label { Text = "CPU 數量" }, cpu);
        advanced.AddRow(advancedFields); advanced.AddRow(blocks); advanced.AddRow(HubUi.Hint("預設 0.10 m、1 CPU、啟用自遮蔭。關閉自遮蔭會忽略分析面的朝向與阻擋，僅檢查外部遮蔭。"));
        reveal.CheckedChanged += (_, _) => advanced.Visible = reveal.Checked == true;
        var settingsFields = new DynamicLayout { Spacing = new Size(8, 8) }; settingsFields.AddRow(new Label { Text = "網格間距 (m)" }, grid);
        var settings = new DynamicLayout { Spacing = new Size(8, 8) }; settings.AddRow(settingsFields); settings.AddRow(HubUi.Hint("Brep 依網格間距細分；輸入 Mesh 依既有網格面取樣，不再細分。")); settings.AddRow(reveal); settings.AddRow(advanced);
        var targetFields = new DynamicLayout { Spacing = new Size(8, 8) }; targetFields.AddRow(new Label { Text = "下限 (h)" }, targetMin); targetFields.AddRow(new Label { Text = "上限 (h)" }, targetMax);
        var targetBody = new DynamicLayout { Spacing = new Size(8, 8), Visible = false }; targetBody.AddRow(targetFields); targetBody.AddRow(HubUi.Hint("包含上下限，精度 0.01 h；只作使用者專案評估，不代表法規合規。")); target.CheckedChanged += (_, _) => targetBody.Visible = target.Checked == true;
        var displayFields = new DynamicLayout { Spacing = new Size(8, 8) }; displayFields.AddRow(new Label { Text = "顯示偏移 (m)" }, displayOffset);
        var viewSettings = new DynamicLayout { Spacing = new Size(8, 8) }; viewSettings.AddRow(displayFields); viewSettings.AddRow(HubUi.Hint("預設沿網格法線偏移 0.002 m，避免與原模型共面閃爍。只改顯示，不改感測點或原生數值；匯出保留原生網格座標。")); viewSettings.AddRow(visible); viewSettings.AddRow(solo);
        var choices = new DynamicLayout { Spacing = new Size(8, 8) }; choices.AddRow(new Label { Text = "基準方案" }, baseline); choices.AddRow(new Label { Text = "比較方案" }, candidate);
        kpi.Font = new Eto.Drawing.Font(SystemFont.Bold, 13);
        sections = [HubUi.Section("01  幾何／模型", HubTopic.Model, select, geometry, shade, noShade, region),
            HubUi.Section("02  環境／太陽來源", HubTopic.Environment, openSun, transfer, sunSummary, new Label { Text = "每小時步數" }, rate, HubUi.Hint("沿用完成的地點、北向、HOY 與時間制；不需要 EPW。先傳入完整取樣序列，再由原生 SunPath 過濾夜間。單一時刻預設 1 步／小時，可明確指定權重。")),
            HubUi.Section("03  模擬設定", HubTopic.Settings, settings),
            HubUi.Section("04  檢核／執行", HubTopic.Run, validate, run, status, HubUi.Hint("同步執行原生 Rhino 射線交會；Rhino 可能暫停回應，尚無取消或百分比進度。請先以短期間及粗網格試算。")),
            HubUi.Section("05  分析結果", HubTopic.Results, state, kpi, legend, detail, target, targetBody, assessment, showSummary, summaryHost, viewSettings, locate, clear),
            HubUi.Section("06  比較／匯出", HubTopic.Compare, scenarioName, save, choices, comparison, exportCompare, importScenarios, archiveStatus, export, exportSummary, HubUi.Hint("HTML 為匯出時的只讀摘要；完整資料與方案恢復請使用 JSON。方案保留於本次工作階段；關閉 Rhino 前請匯出比較 JSON，可於下次匯入。匯入後合計上限 20 個方案、檔案上限 64 MiB；同名方案請先改名再匯出。此結果是直射日照時數 h，並非照度、日射能量或日照法規判定。"))];
        var layout = new DynamicLayout { Padding = 16, Spacing = new Size(8, 14) }; layout.AddRow(HubUi.Header("日照時數", "檢視建築表面與地面的直射日照，核對遮蔭與時間取樣。", typeof(SunHoursPanel))); foreach (var s in sections) layout.AddRow(s);
        scroll = new Scrollable { Content = layout, ExpandContentWidth = true }; scroll.SizeChanged += (_, _) => layout.Width = Math.Max(120, scroll.ClientSize.Width - 20);
        foreach (var s in new[] { "01  幾何／模型", "02  太陽來源", "03  模擬設定", "04  檢核／執行", "05  分析結果", "06  比較／匯出" }) stage.Items.Add(s); stage.SelectedIndex = 0;
        var jump = new Button { Text = "前往階段" }; jump.Click += (_, _) => ShowStage(stage.SelectedIndex); var nav = new DynamicLayout { Padding = new Padding(16, 8), Spacing = new Size(8, 8) }; nav.AddRow(stage, jump);
        var body = new DynamicLayout(); body.AddRow(nav); body.Add(scroll, yscale: true); Content = body; MinimumSize = new Size(300, 200); Size = new Size(360, 680); BackgroundColor = SystemColors.ControlBackground;
    }
    private static string Folder() { using var c = JsonDocument.Parse(File.ReadAllText(Path.Combine(Path.GetDirectoryName(typeof(SunHoursPanel).Assembly.Location)!, "hub.config.json"))); return System.Environment.ExpandEnvironmentVariables(c.RootElement.GetProperty("UserObjectDirectory").GetString()!); }
    private static LadybugSunHoursAdapter Adapter(RhinoDoc doc) => new(doc, Folder());
    private RhinoDoc RequireDocument() { var d = RhinoDoc.ActiveDoc ?? throw new InvalidOperationException("SUNH-DOC-001: Active document required."); if (inputDocument != 0 && (inputDocument != d.RuntimeSerialNumber || inputUnits != d.ModelUnitSystem.ToString())) throw new InvalidOperationException("SUNH-DOC-002: Document/units changed; select geometry again."); return d; }
    private void Changed() { if (updating || busy) return; run.Enabled = selected.Length > 0 && source is not null; status.Text = "輸入已變更 · 執行前請重新檢核"; if (result is not null) state.Text = "前次結果 · 輸入已變更"; RefreshSummary(); }
    public string ExportSummaryHtml() => result is null ? throw new InvalidOperationException("尚無完成結果可呈現。") : SunHoursResultPage.Render(result, state.Text, comparison.Text, assessment.Text, string.Join("\n", result.Warnings.Select(HubText.Diagnostic)), HubVisuals.Dark);
    private void RefreshSummary()
    {
        showSummary.Enabled = exportSummary.Enabled = result is not null && !busy;
        if (result is null || busy || !summaryHost.Visible) return;
        try { if (webSummary is null) { webSummary = new SunHoursWebSummary(); summaryHost.Content = webSummary; } webSummary.ShowHtml(ExportSummaryHtml()); }
        catch (Exception e) { summaryHost.Content = HubUi.Hint("圖像摘要未能建立 · 原生結果保留。\n" + HubText.Error(e)); webSummary?.Dispose(); webSummary = null; }
    }
    private void Guard(Action action) { try { action(); } catch (Exception e) { status.Text = "分析未完成" + (result is null ? "" : " · 已保留前次結果") + "\n" + HubText.Error(e); } }
    private static string Format(PreflightReport r) => r.Diagnostics.Length == 0 ? "輸入檢核通過" : (r.CanRun ? "可執行，仍有警告\n" : "請修正以下輸入\n") + string.Join("\n", r.Diagnostics.Select(HubText.Diagnostic));
    private void Select(bool shade)
    {
        var d = RhinoDoc.ActiveDoc ?? throw new InvalidOperationException("SUNH-DOC-001: Active document required."); using var picker = new GetObject(); picker.SetCommandPrompt(shade ? "選取遮蔭環境" : "選取日照時數分析面"); picker.GeometryFilter = ObjectType.Surface | ObjectType.Brep | ObjectType.Mesh; picker.GetMultiple(1, 0); if (picker.CommandResult() != Rhino.Commands.Result.Success) return;
        if (inputDocument != d.RuntimeSerialNumber || inputUnits != d.ModelUnitSystem.ToString()) { selected = []; context = []; }
        if (shade) context = picker.Objects().Select(o => o.ObjectId).ToArray(); else selected = picker.Objects().Select(o => o.ObjectId).ToArray(); inputDocument = d.RuntimeSerialNumber; inputUnits = d.ModelUnitSystem.ToString(); RefreshGeometry(); Changed();
    }
    public void SetGeometry(Guid[] geometryIds, Guid[] contextIds)
    {
        // Explicit reselection establishes a new document/unit binding, as the native picker does.
        var d = RhinoDoc.ActiveDoc ?? throw new InvalidOperationException("SUNH-DOC-001: Active document required.");
        var nextSelected = geometryIds.ToArray();
        var nextContext = contextIds.ToArray();
        selected = nextSelected; context = nextContext;
        inputDocument = d.RuntimeSerialNumber; inputUnits = d.ModelUnitSystem.ToString();
        RefreshGeometry(); Changed();
    }
    private void RefreshGeometry() => geometry.Text = $"{selected.Length} 個分析物件 · {context.Length} 個遮蔽物件";
    public void UseCompletedSunPath()
    {
        var d = RequireDocument(); var panel = Rhino.UI.Panels.GetPanel<HubWorkspacePanel>(d)?.GetModule<SunPathPanel>(); var completed = JsonSerializer.Deserialize<SunPathResult>(panel?.CompletedResultJson ?? throw new InvalidOperationException("請先完成太陽路徑建立。"))!; SetSunSource(completed.InputParameters);
    }
    public void SetSunSource(SunPathRequest input)
    {
        var inferred = SunHoursSampling.Infer(input.HoursOfYear); source = JsonSerializer.Deserialize<SunPathRequest>(JsonSerializer.Serialize(input)); updating = true; try { rate.SelectedIndex = Array.IndexOf(SunHoursSampling.SupportedRates, inferred); } finally { updating = false; } RefreshSource(); Changed();
    }
    private void RefreshSource() { if (source is null) return; sunSummary.Text = $"{source.Location.Name} · 北向 {source.NorthDegrees:G}°\n{source.HoursOfYear.Length:N0} 個選取時刻 · 每小時 {Steps()} 步\n{(source.SolarTime ? "真太陽時" : "當地標準時間")} · 非閏年／不含夏令時間\n{new DateTime(2001, 1, 1).AddHours(source.HoursOfYear[0]):MM/dd HH:mm} → {new DateTime(2001, 1, 1).AddHours(source.HoursOfYear[^1]):MM/dd HH:mm}"; }
    private int Steps() => SunHoursSampling.SupportedRates[Math.Max(0, rate.SelectedIndex)];
    private SunHoursRequest Request() => new() { GeometryIds = selected.ToArray(), ContextIds = context.ToArray(), SunSource = source, TimeStepsPerHour = Steps(), GridMetres = grid.Value, OffsetMetres = offset.Value, GeometryBlocks = blocks.Checked == true, CpuCount = (int)cpu.Value };
    public string ExecuteJson(string json) => ExecuteRequest(JsonSerializer.Deserialize<SunHoursRequest>(json)!);
    public string ExecuteRequest(SunHoursRequest r)
    {
        var d = RequireDocument(); var report = Adapter(d).Preflight(r); if (!report.CanRun) { status.Text = Format(report); if (result is not null) state.Text = "前次結果 · 新輸入未通過檢核"; RefreshSummary(); throw new InvalidOperationException(status.Text); }
        busy = true; run.Enabled = false; status.Text = "正在執行原生日照時數分析…";
        try
        {
            r = JsonSerializer.Deserialize<SunHoursRequest>(JsonSerializer.Serialize(r))!; var completed = Adapter(d).Execute(r); ReplacePreview(d, completed);
            updating = true; try { selected = r.GeometryIds.ToArray(); context = r.ContextIds.ToArray(); source = r.SunSource; grid.Value = r.GridMetres; offset.Value = r.OffsetMetres; cpu.Value = r.CpuCount; blocks.Checked = r.GeometryBlocks; rate.SelectedIndex = Array.IndexOf(SunHoursSampling.SupportedRates, r.TimeStepsPerHour); inputDocument = d.RuntimeSerialNumber; inputUnits = d.ModelUnitSystem.ToString(); RefreshGeometry(); RefreshSource(); } finally { updating = false; }
            result = completed; state.Text = "目前完成結果 · 直射日照時數"; kpi.Text = $"平均值 {completed.Statistics.Mean:F3} h\n最小值 {completed.Statistics.Minimum:F3} · 最大值 {completed.Statistics.Maximum:F3}\n{completed.Statistics.Count:N0} 個分析格點"; legend.Content = SunHoursPresentation.Legend(completed);
            detail.Text = $"{completed.Metadata["Location"]} · {completed.Timestamp.ToLocalTime():yyyy-MM-dd HH:mm}\n{completed.SunlightVectors.Length:N0} 個太陽向量／{r.SunSource!.HoursOfYear.Length:N0} 個選取時刻\n{r.TimeStepsPerHour} 步／小時 · 每向量 {1.0 / r.TimeStepsPerHour:G4} h\n可用向量權重上限 {completed.SunlightVectors.Length / (double)r.TimeStepsPerHour:F3} h\n首尾均為取樣點，上限不等於曆時長度。\n{r.GridMetres:G} m 網格 · {r.OffsetMetres:G} m 偏移\n模型單位 {completed.Metadata["ModelUnits"]} · 自遮蔭 {(r.GeometryBlocks ? "開啟" : "關閉")}\n原生 Rhino 射線交會 · {completed.ExecutionTimeSeconds:F1} s";
            status.Text = "分析完成" + (completed.Warnings.Length == 0 ? "" : "\n" + string.Join("\n", completed.Warnings.Select(HubText.Diagnostic))); export.Enabled = save.Enabled = locate.Enabled = clear.Enabled = true; UpdateAssessment(); ApplyVisibility(); ApplyOtherVisibility(); ShowStage(4); d.Views.Redraw(); return CompletedResultJson!;
        }
        catch (Exception e) { status.Text = "分析未完成" + (result is null ? "" : " · 已保留前次結果") + "\n" + HubText.Error(e); if (result is not null) state.Text = "前次結果 · 新分析失敗"; throw; }
        finally { busy = false; run.Enabled = selected.Length > 0 && source is not null; RefreshSummary(); }
    }
    private void ReplacePreview(RhinoDoc d, SunHoursResult r)
    {
        var replacement = new List<(uint Document, Guid Object)>();
        try { foreach (var a in r.ResultMesh) { using var m = new Mesh(); foreach (var v in a.Vertices) m.Vertices.Add(v[0], v[1], v[2]); foreach (var f in a.Faces) { if (f.Length == 3) m.Faces.AddFace(f[0], f[1], f[2]); else m.Faces.AddFace(f[0], f[1], f[2], f[3]); } foreach (var c in a.VertexColorsArgb) m.VertexColors.Add(System.Drawing.Color.FromArgb(c)); if (!m.IsValid) throw new InvalidOperationException("SUNH-VIEW-001: Invalid preview mesh."); m.Normals.ComputeNormals(); if (m.Normals.Count != m.Vertices.Count) throw new InvalidOperationException("SUNH-VIEW-001: Preview normals unavailable."); var displayScale = RhinoMath.UnitScale(UnitSystem.Meters, d.ModelUnitSystem); for (int i = 0; i < m.Vertices.Count; i++) { var n = m.Normals[i]; m.Vertices.SetVertex(i, new Point3d(m.Vertices[i]) + new Vector3d(n.X, n.Y, n.Z) * (displayOffset.Value * displayScale)); }
            var id = d.Objects.AddMesh(m, HubPreviewTag.Mark(new ObjectAttributes { Name = "EnvironmentalHub / DirectSunHours / h" }, "SunHours")); if (id == Guid.Empty) throw new InvalidOperationException("SUNH-VIEW-001: Failed preview mesh."); replacement.Add((d.RuntimeSerialNumber, id)); } }
        catch { foreach (var o in replacement) d.Objects.Delete(o.Object, true); throw; }
        RemoveOwnedOnly(); owned.AddRange(replacement); locate.Enabled = clear.Enabled = true; ApplyVisibility();
    }
    private void RemoveOwnedOnly() { foreach (var o in owned) { var d = RhinoDoc.FromRuntimeSerialNumber(o.Document); d?.Objects.Delete(o.Object, true); d?.Views.Redraw(); } owned.Clear(); locate.Enabled = clear.Enabled = false; }
    public void DeletePreview() { RemoveOwnedOnly(); ReleaseFocusVisibility(); }
    public void ReleaseFocusVisibility() { solo.Checked = false; RestoreOtherVisibility(); }
    private void RestoreOtherVisibility() { foreach (var o in hiddenOther) { var d = RhinoDoc.FromRuntimeSerialNumber(o.Document); var obj = d?.Objects.FindId(o.Object); if (obj?.Attributes.GetUserString(HubPreviewTag.Key)?.StartsWith(HubPreviewTag.Prefix) == true) d!.Objects.Show(o.Object, true); d?.Views.Redraw(); } hiddenOther.Clear(); }
    private void ApplyOtherVisibility()
    {
        if (solo.Checked != true) { RestoreOtherVisibility(); return; }
        if (owned.Count == 0) return; var d = RequireDocument();
        foreach (var o in d.Objects) if (!o.IsHidden && o.Attributes.GetUserString(HubPreviewTag.Key) is { } tag && tag.StartsWith(HubPreviewTag.Prefix) && tag != HubPreviewTag.Prefix + "SunHours" && d.Objects.Hide(o.Id, true)) hiddenOther.Add((d.RuntimeSerialNumber, o.Id));
        d.Views.Redraw();
    }
    private void ApplyVisibility() { foreach (var o in owned) { var d = RhinoDoc.FromRuntimeSerialNumber(o.Document); if (visible.Checked == true) d?.Objects.Show(o.Object, true); else d?.Objects.Hide(o.Object, true); d?.Views.Redraw(); } }
    public void SetDisplayOffset(double metres) { if (!double.IsFinite(metres) || metres < 0 || metres > 1 || Math.Round(metres, 3) != metres) throw new ArgumentException("顯示偏移須為 0–1 m，精度 0.001 m。"); displayOffset.Value = metres; }
    public string ExportResultJson() => JsonSerializer.Serialize(new { SchemaVersion = "1.0", NativeResult = result, Presentation = new { DisplayOffsetMetres = displayOffset.Value, MeshCoordinates = "Native unshifted coordinates; display offset is preview only", Visible = visible.Checked == true } }, new JsonSerializerOptions { WriteIndented = true });
    private void Zoom(IEnumerable<Guid> ids) { var d = RequireDocument(); var bounds = BoundingBox.Empty; foreach (var id in ids) if (d.Objects.FindId(id) is { } o) bounds.Union(o.Geometry.GetBoundingBox(true)); if (!bounds.IsValid || d.Views.ActiveView is null) throw new InvalidOperationException("SUNH-VIEW-002: Geometry or viewport unavailable."); d.Views.ActiveView.ActiveViewport.ZoomBoundingBox(bounds); d.Views.Redraw(); }
    public void LocateGeometry() => Zoom(selected);
    public void LocateResult() { var d = RequireDocument(); if (owned.Count == 0 || owned.Any(o => o.Document != d.RuntimeSerialNumber)) throw new InvalidOperationException("SUNH-VIEW-002: No preview in active document."); Zoom(owned.Select(o => o.Object)); }
    public void ShowStage(int i) { if (i < 0 || i >= sections.Length) throw new ArgumentOutOfRangeException(nameof(i)); stage.SelectedIndex = i; var origin = scroll.Content.PointToScreen(PointF.Empty); var p = sections[i].PointToScreen(PointF.Empty); scroll.ScrollPosition = new Eto.Drawing.Point(0, Math.Max(0, (int)(p.Y - origin.Y))); }
    private void UpdateAssessment() { if (result is null || target.Checked != true) assessment.Text = "尚未設定完成結果的專案評估區間。"; else if (targetMin.Value > targetMax.Value) assessment.Text = "區間下限不得高於上限。"; else { var pass = result.Values.Count(v => v >= targetMin.Value && v <= targetMax.Value); assessment.Text = $"專案目標 {targetMin.Value:G}–{targetMax.Value:G} h\n符合 {pass:N0} · 未符合 {result.Values.Length - pass:N0}\n{100.0 * pass / result.Values.Length:F1}% · 包含上下限"; } RefreshSummary(); }
    public void SetTargetRange(double min, double max) { if (!double.IsFinite(min) || !double.IsFinite(max) || min < 0 || max > 525600 || min > max || Math.Round(min, 2) != min || Math.Round(max, 2) != max) throw new ArgumentException("專案區間須為 0–525600 h，精度 0.01 h，且下限不超過上限。"); targetMin.Value = min; targetMax.Value = max; target.Checked = true; UpdateAssessment(); }
    public string SaveScenario(string name) { if (result is null || busy) throw new InvalidOperationException("請先完成分析。"); name = name.Trim(); if (name.Length == 0 || name.Length > 80 || name.Any(char.IsControl) || scenarios.Any(s => s.Name.Equals(name, StringComparison.OrdinalIgnoreCase)) || scenarios.Count >= SunHoursArchive.MaximumScenarios) throw new ArgumentException("方案名稱須為 1–80 字元、不含控制字元、不重複；本次工作階段上限 20 個方案。"); scenarios.Add(new(name, result)); baseline.Items.Add(name); candidate.Items.Add(name); if (baseline.SelectedIndex < 0) baseline.SelectedIndex = 0; candidate.SelectedIndex = scenarios.Count - 1; exportCompare.Enabled = scenarios.Count > 0; scenarioName.Text = "方案 " + (scenarios.Count + 1); RefreshComparison(); return JsonSerializer.Serialize(new { Name = name, Result = result }); }
    private void RefreshComparison() { if (updating || baseline.SelectedIndex < 0 || candidate.SelectedIndex < 0 || baseline.SelectedIndex >= scenarios.Count || candidate.SelectedIndex >= scenarios.Count) return; var a = scenarios[baseline.SelectedIndex]; var b = scenarios[candidate.SelectedIndex]; comparison.Text = baseline.SelectedIndex == candidate.SelectedIndex ? "請選取兩個不同方案。" : SunHoursPresentation.Compare(a.Name, a.Result, b.Name, b.Result); if (a.Imported || b.Imported) comparison.Text += "\n含匯入歷史結果 · 未重新求解、未核對目前模型；請確認檔案來源。"; RefreshSummary(); }
    public string CompareScenarios(int a, int b) { if (a < 0 || b < 0 || a >= scenarios.Count || b >= scenarios.Count) throw new ArgumentOutOfRangeException(nameof(a)); baseline.SelectedIndex = a; candidate.SelectedIndex = b; RefreshComparison(); return comparison.Text; }
    public string ExportComparisonJson() => JsonSerializer.Serialize(new { SchemaVersion = "1.0", BaselineIndex = baseline.SelectedIndex, CandidateIndex = candidate.SelectedIndex, Interpretation = comparison.Text, Metric = "Arithmetic point mean, not area weighted", Scenarios = scenarios }, new JsonSerializerOptions { WriteIndented = true });
    public int ImportScenariosJson(string json)
    {
        if (busy) throw new InvalidOperationException("分析執行中，請完成後再匯入方案。");
        var archive = SunHoursArchive.Parse(json, scenarios.Select(s => s.Name));
        int first = scenarios.Count;
        updating = true;
        try
        {
            scenarios.AddRange(archive.Scenarios);
            foreach (var s in archive.Scenarios) { baseline.Items.Add(s.Name); candidate.Items.Add(s.Name); }
            baseline.SelectedIndex = first + archive.BaselineIndex; candidate.SelectedIndex = first + archive.CandidateIndex;
            exportCompare.Enabled = true; scenarioName.Text = "方案 " + (scenarios.Count + 1);
        }
        finally { updating = false; }
        RefreshComparison(); archiveStatus.Text = $"已匯入 {archive.Scenarios.Length} 個歷史方案 · 合計 {scenarios.Count} 個。\n目前模型、輸入與完成結果保留；歷史識別碼不會綁定目前文件。";
        return archive.Scenarios.Length;
    }
    private void ImportFile()
    {
        try
        {
            using var dialog = new OpenFileDialog { Title = "匯入日照方案比較 JSON" };
            dialog.Filters.Add(new FileFilter("日照方案比較 JSON", ".json"));
            if (dialog.ShowDialog(this) != DialogResult.Ok) return;
            using var stream = File.OpenRead(dialog.FileName);
            if (stream.Length > SunHoursArchive.MaximumBytes) throw new ArgumentException("SUNH-IMPORT-001: 檔案超過 64 MiB。");
            using var reader = new StreamReader(stream, System.Text.Encoding.UTF8, true);
            ImportScenariosJson(reader.ReadToEnd());
        }
        catch (Exception e) { archiveStatus.Text = "匯入未完成 · 已保留既有方案、模型與結果\n" + HubText.Error(e); }
    }
    private void SaveJson(string name, string? json) { if (json is null) throw new InvalidOperationException("尚無可匯出的結果。"); var dialog = new SaveFileDialog { FileName = name }; dialog.Filters.Add(new FileFilter("分析資料 JSON", ".json")); if (dialog.ShowDialog(this) == DialogResult.Ok) File.WriteAllText(dialog.FileName, json); }
}
