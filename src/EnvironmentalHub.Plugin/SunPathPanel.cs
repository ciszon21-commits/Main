using System.Text.Json;
using EnvironmentalHub.Adapters;
using EnvironmentalHub.Core;
using Eto.Drawing;
using Eto.Forms;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;
using Color = System.Drawing.Color;

namespace EnvironmentalHub.Plugin;

public sealed class SunPathPanel : Panel
{
    private readonly TextBox name = new() { Text = "臺北" };
    private readonly NumericStepper latitude = Number(-90, 90, 25.033, 4);
    private readonly NumericStepper longitude = Number(-180, 180, 121.5654, 4);
    private readonly NumericStepper zone = Number(-12, 12, 8, 2);
    private readonly NumericStepper elevation = Number(-100000, 100000, 0, 2);
    private readonly NumericStepper month = Number(1, 12, 6);
    private readonly NumericStepper day = Number(1, 31, 21);
    private readonly NumericStepper hour = Number(0, 23, 12);
    private readonly NumericStepper minute = Number(0, 59, 0);
    private readonly NumericStepper north = Number(-360, 360, 0, 2);
    private readonly NumericStepper radius = Number(0.01, 1000000, 20, 2);
    private readonly NumericStepper x = Number(-1e9, 1e9, 0, 4);
    private readonly NumericStepper y = Number(-1e9, 1e9, 0, 4);
    private readonly NumericStepper z = Number(-1e9, 1e9, 0, 4);
    private readonly DropDown projection = new();
    private readonly CheckBox solarTime = new() { Text = "以真太陽時解讀輸入時刻", Checked = false };
    private readonly CheckBox daily = new() { Text = "只顯示選取日期的日弧", Checked = false };
    private readonly CheckBox reveal = new() { Text = "進階設定", Checked = false };
    private readonly Label timeNote = HubUi.Hint("指定日期 · 當地標準時間（不含夏令時間）");
    private readonly Label status = new() { Text = "確認地點、日期與模型單位後，建立太陽路徑。", Wrap = WrapMode.Word };
    private readonly Label summary = new() { Text = "尚無分析結果", Wrap = WrapMode.Word, Font = new Eto.Drawing.Font(SystemFont.Bold, 13) };
    private readonly Label detail = new() { Wrap = WrapMode.Word };
    private readonly DropDown positions = new() { Enabled = false };
    private readonly Button run = new() { Text = "檢核並建立太陽路徑" };
    private readonly Button locate = new() { Text = "定位整體預覽", Enabled = false };
    private readonly Button locateSun = new() { Text = "定位選取太陽", Enabled = false };
    private readonly Button clear = new() { Text = "清除本模組預覽", Enabled = false };
    private readonly Button export = new() { Text = "匯出結果 JSON…", Enabled = false };
    private SunPathResult? result;
    private double[]? importedHours;
    private double? importedRadius;
    private readonly List<(uint Document, Guid Object)> owned = [];
    private readonly List<Guid> sunObjects = [];
    private uint? inputDocument;
    private string? inputUnits;
    private bool updating;
    public string? CompletedResultJson => result is null ? null : JsonSerializer.Serialize(result);
    public string StatusText => status.Text;
    public string SummaryText => summary.Text;
    private static NumericStepper Number(double min, double max, double value, int decimals = 0) => new() { MinValue = min, MaxValue = max, Value = value, DecimalPlaces = decimals, Width = 100, Increment = decimals == 0 ? 1 : 0.1 };

    public SunPathPanel()
    {
        foreach (var label in new[] { "3D 半球", "正投影 Orthographic", "立體投影 Stereographic", "等距 Equidistant", "等立體角 Equisolid" }) projection.Items.Add(label); projection.SelectedIndex = 0;
        void Changed() { if (!updating) status.Text = result is null ? "條件已更新 · 執行時先檢核" : "前次結果 · 條件已變更，重新執行以更新"; }
        name.TextChanged += (_, _) => Changed();
        foreach (var control in new[] { latitude, longitude, zone, elevation, north, x, y, z }) control.ValueChanged += (_, _) => Changed();
        radius.ValueChanged += (_, _) => { if (!updating) importedRadius = null; Changed(); };
        foreach (var control in new[] { month, day, hour, minute }) control.ValueChanged += (_, _) => { if (!updating) { importedHours = null; RefreshTime(); Changed(); } };
        solarTime.CheckedChanged += (_, _) => { RefreshTime(); Changed(); }; daily.CheckedChanged += (_, _) => Changed(); projection.SelectedIndexChanged += (_, _) => Changed();
        var advanced = new DynamicLayout { Spacing = new Size(8, 8), Visible = false };
        advanced.AddRow(Fields(("UTC 時差 (h)", zone), ("海拔 (m)", elevation), ("中心 X · 模型單位", x), ("中心 Y · 模型單位", y), ("中心 Z · 模型單位", z)));
        advanced.AddRow(new Label { Text = "顯示投影" }); advanced.AddRow(projection); advanced.AddRow(solarTime);
        advanced.AddRow(HubUi.Hint("投影只改變圖形，日照向量仍為原生 3D 方向。此版未接入夏令時間、氣象著色及條件篩選。"));
        reveal.CheckedChanged += (_, _) => advanced.Visible = reveal.Checked == true;
        var useLocation = new Button { Text = "使用已建立地點" }; useLocation.Click += (_, _) => Guard(UseCompletedLocation);
        var useWeather = new Button { Text = "使用 EPW 地點" }; useWeather.Click += (_, _) => Guard(UseImportedWeather);
        var usePeriod = new Button { Text = "使用時間模組的完成結果" }; usePeriod.Click += (_, _) => Guard(UseCompletedTime);
        var rebind = new Button { Text = "綁定目前文件／重設中心" }; rebind.Click += (_, _) => Guard(RebindCurrentDocument);
        var pick = new Button { Text = "在 Rhino 指定中心…" }; pick.Click += (_, _) => Guard(() =>
        {
            var doc = RequireDocument(); using var get = new Rhino.Input.Custom.GetPoint(); get.SetCommandPrompt("指定太陽路徑中心");
            if (get.Get() != Rhino.Input.GetResult.Point) return; var pt = get.Point();
            updating = true; try { x.Value = pt.X; y.Value = pt.Y; z.Value = pt.Z; } finally { updating = false; }
            inputDocument = doc.RuntimeSerialNumber; inputUnits = doc.ModelUnitSystem.ToString(); Changed();
        });
        run.Click += (_, _) => Guard(() => ExecuteJson(JsonSerializer.Serialize(Request())));
        locate.Click += (_, _) => Guard(LocateResult); locateSun.Click += (_, _) => Guard(LocateSun);
        clear.Click += (_, _) => Guard(() => { DeletePreview(); locate.Enabled = locateSun.Enabled = clear.Enabled = false; status.Text = "預覽已清除 · 完成結果仍可匯出或檢視。"; });
        positions.SelectedIndexChanged += (_, _) => ShowPosition();
        export.Click += (_, _) => Guard(() =>
        {
            if (result is null) return; var dialog = new SaveFileDialog { FileName = "sunpath_result.json" }; dialog.Filters.Add(new FileFilter("太陽路徑 JSON", ".json"));
            if (dialog.ShowDialog(this) == DialogResult.Ok) File.WriteAllText(dialog.FileName, JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }));
        });
        var layout = new DynamicLayout { Padding = 16, Spacing = new Size(8, 14) };
        layout.AddRow(HubUi.Header("太陽路徑", "檢視太陽位置、全年日弧與日照方向，輔助量體及遮陽設計。", typeof(SunPathPanel)));
        layout.AddRow(HubUi.Section("01  幾何／模型", HubTopic.Model, pick, rebind, HubUi.Hint("中心預設為模型原點；半徑以公尺輸入，依文件單位自動換算。預覽不會更動分析模型。")));
        var location = new DynamicLayout { Spacing = new Size(8, 8) }; location.AddRow(useLocation); location.AddRow(useWeather); location.AddRow(new Label { Text = "地點名稱" }); location.AddRow(name);
        location.AddRow(Fields(("緯度 (°)", latitude), ("經度 (°)", longitude)));
        layout.AddRow(HubUi.Section("02  環境／地點", HubTopic.Environment, location, HubUi.Hint("預設臺北 / UTC+8；實際時區與海拔可在進階設定調整。")));
        var settings = new DynamicLayout { Spacing = new Size(8, 8) }; settings.AddRow(usePeriod); settings.AddRow(Fields(("月", month), ("日", day), ("時 (0–23)", hour), ("分", minute))); settings.AddRow(timeNote);
        settings.AddRow(Fields(("北向旋轉 (°)", north), ("路徑半徑 (m)", radius))); settings.AddRow(HubUi.Hint("北向從 +Y 逆時針旋轉：0° = +Y、90° = −X。")); settings.AddRow(daily); settings.AddRow(reveal); settings.AddRow(advanced);
        layout.AddRow(HubUi.Section("03  模擬設定", HubTopic.Settings, settings));
        layout.AddRow(HubUi.Section("04  檢核／執行", HubTopic.Run, run, status, HubUi.Hint("原生 Ladybug 同步運算；Rhino 可能暫停回應，目前不提供取消。")));
        layout.AddRow(HubUi.Section("05  分析結果", HubTopic.Results, summary, positions, detail, locateSun, locate));
        layout.AddRow(HubUi.Section("06  匯出／預覽管理", HubTopic.Compare, export, clear, HubUi.Hint("路徑線為幾何分類，非輻射色階；太陽點為橙色、日照方向線由太陽指向中心。沒有遮蔭、輻射或日照時數計算。")));
        layout.Add(null); HubUi.Mount(this, layout);
    }
    private static Control Fields(params (string Label, Control Input)[] values)
    {
        var layout = new DynamicLayout { Spacing = new Size(8, 8) }; foreach (var v in values) layout.AddRow(new Label { Text = v.Label, Wrap = WrapMode.Word }, v.Input); return layout;
    }
    private void RefreshTime() => timeNote.Text = (importedHours is null ? "指定日期" : $"已傳入 {importedHours.Length:N0} 個時刻 · 修改日期會切回單一時刻") +
        (solarTime.Checked == true ? "\n真太陽時 · 不等同鐘錶時間" : "\n當地標準時間 · 不含夏令時間");
    private void Guard(Action action) { try { action(); } catch (Exception e) { status.Text = (result is null ? "執行失敗\n" : "執行失敗 · 已保留前次結果\n") + HubText.Error(e); } }
    private RhinoDoc RequireDocument()
    {
        var doc = RhinoDoc.ActiveDoc ?? throw new InvalidOperationException("SUN-DOC-001: Active document required.");
        if (inputDocument.HasValue && (inputDocument != doc.RuntimeSerialNumber || inputUnits != doc.ModelUnitSystem.ToString()))
            throw new InvalidOperationException("SUN-DOC-002: Input document or model units changed; create inputs in the target document.");
        return doc;
    }
    public void RebindCurrentDocument()
    {
        var doc = RhinoDoc.ActiveDoc ?? throw new InvalidOperationException("SUN-DOC-001: Active document required.");
        updating = true; try { x.Value = y.Value = z.Value = 0; } finally { updating = false; }
        inputDocument = doc.RuntimeSerialNumber; inputUnits = doc.ModelUnitSystem.ToString();
        status.Text = result is null ? "已綁定目前文件 · 中心重設為原點" : "前次結果 · 已綁定目前文件並重設中心，重新執行以更新";
    }
    private SunPathRequest Request()
    {
        var doc = RequireDocument();
        double[] hours = importedHours ?? [new LadybugTimeAdapter(Folder()).Calendar(new() { Month = (int)month.Value, Day = (int)day.Value, Hour = (int)hour.Value, Minute = (int)minute.Value }).Time.HourOfYear];
        return new()
        {
            Location = new() { Name = name.Text, Latitude = latitude.Value, Longitude = longitude.Value, TimeZone = zone.Value, ElevationMetres = elevation.Value },
            HoursOfYear = hours,
            NorthDegrees = north.Value,
            RadiusMetres = importedRadius ?? radius.Value,
            Center = [x.Value, y.Value, z.Value],
            SolarTime = solarTime.Checked == true,
            Daily = daily.Checked == true,
            Projection = Projection()
        };
    }
    private string Projection() => new[] { "3D", "Orthographic", "Stereographic", "Equidistant", "Equisolid" }[projection.SelectedIndex];
    private string Folder()
    {
        using var config = JsonDocument.Parse(File.ReadAllText(Path.Combine(Path.GetDirectoryName(GetType().Assembly.Location)!, "hub.config.json")));
        return System.Environment.ExpandEnvironmentVariables(config.RootElement.GetProperty("UserObjectDirectory").GetString()!);
    }
    public string ExecuteJson(string json)
    {
        run.Enabled = false; status.Text = "檢核並執行原生太陽路徑…";
        try
        {
            var doc = RequireDocument(); var request = JsonSerializer.Deserialize<SunPathRequest>(json)!;
            var completed = new LadybugSunPathAdapter(Folder()).Execute(request); ReplacePreview(doc, completed);
            updating = true;
            try
            {
                name.Text = request.Location.Name; latitude.Value = request.Location.Latitude; longitude.Value = request.Location.Longitude; zone.Value = completed.Location.TimeZone; elevation.Value = request.Location.ElevationMetres;
                north.Value = request.NorthDegrees; radius.Value = request.RadiusMetres; importedRadius = request.RadiusMetres; x.Value = request.Center[0]; y.Value = request.Center[1]; z.Value = request.Center[2];
                solarTime.Checked = request.SolarTime; daily.Checked = request.Daily; projection.SelectedIndex = Array.IndexOf(new[] { "3D", "Orthographic", "Stereographic", "Equidistant", "Equisolid" }, request.Projection);
                importedHours = request.HoursOfYear.ToArray(); RefreshTime(); result = completed; positions.Items.Clear();
                foreach (var p in completed.Positions) positions.Items.Add($"{Date(p.HourOfYear)} · HOY {p.HourOfYear:0.####}");
                positions.Enabled = completed.Positions.Length > 0; positions.SelectedIndex = completed.Positions.Length > 0 ? 0 : -1;
            }
            finally { updating = false; }
            inputDocument = doc.RuntimeSerialNumber; inputUnits = doc.ModelUnitSystem.ToString();
            summary.Text = $"{completed.Location.City} · {completed.Positions.Length:N0} 個太陽位置\n選取 {request.HoursOfYear.Length:N0} · 地平線以下 {request.HoursOfYear.Length - completed.Positions.Length:N0}" +
                (completed.Positions.Length > 0 ? $"\n高度角 {completed.Positions.Min(p => p.AltitudeDegrees):F2}°–{completed.Positions.Max(p => p.AltitudeDegrees):F2}°" : "\n所選時刻沒有地平線以上的太陽");
            ShowPosition(); status.Text = "完成 · 原生太陽路徑" + (completed.Warnings.Length == 0 ? "" : "\n" + string.Join("\n", completed.Warnings.Select(HubText.Diagnostic)));
            export.Enabled = locate.Enabled = clear.Enabled = true; locateSun.Enabled = completed.Positions.Length > 0; doc.Views.Redraw(); return JsonSerializer.Serialize(completed);
        }
        catch (Exception e) { status.Text = (result is null ? "執行失敗\n" : "執行失敗 · 已保留前次結果\n") + HubText.Error(e); throw; }
        finally { run.Enabled = true; }
    }
    private static string Date(double hoy) => new DateTime(2001, 1, 1).AddMinutes(Math.Round(hoy * 60)).ToString("MM/dd HH:mm");
    private void ShowPosition()
    {
        if (result is null) return; var prefix = $"{ClimateDisplay.UtcOffset(result.Location.TimeZone)} · {(result.InputParameters.SolarTime ? "真太陽時" : "當地標準時間")}\n{result.InputParameters.Projection} · 半徑 {result.InputParameters.RadiusMetres:G} m\n模型單位 {result.ModelUnits}";
        var index = positions.SelectedIndex;
        detail.Text = index < 0 || index >= result.Positions.Length ? prefix : prefix + $"\n高度角 {result.Positions[index].AltitudeDegrees:F2}° · 方位角 {result.Positions[index].AzimuthDegrees:F2}°\n日照方向向量 ({string.Join(", ", result.Positions[index].SunlightVector.Select(v => v.ToString("F4")))})";
    }
    private void ReplacePreview(RhinoDoc doc, SunPathResult next)
    {
        var replacement = new List<(uint Document, Guid Object)>(); var points = new List<Guid>();
        void Add(Guid id) { if (id == Guid.Empty) throw new InvalidOperationException("SUN-VIEW-001: Failed preview; previous retained."); replacement.Add((doc.RuntimeSerialNumber, id)); }
        ObjectAttributes Attributes(string role, Color color) => new() { Name = "EnvironmentalHub / SunPath / " + role, ColorSource = ObjectColorSource.ColorFromObject, ObjectColor = color };
        try
        {
            foreach (var c in next.Curves)
            {
                using var geometry = GeometryBase.FromJSON(c.GeometryJson); if (geometry is not Curve curve || !curve.IsValid) throw new InvalidOperationException("SUN-VIEW-001: Invalid curve.");
                Add(doc.Objects.AddCurve(curve, Attributes(c.Output, c.Output == "compass" ? Color.FromArgb(90, 105, 116) : c.Output == "daily" ? Color.FromArgb(164, 125, 62) : Color.FromArgb(91, 111, 133))));
            }
            foreach (var t in next.Texts)
            {
                var plane = new Plane(Pt(t.Origin), Vec(t.XAxis), Vec(t.YAxis)); using var text = new Rhino.Display.Text3d(t.Text, plane, t.Height) { FontFace = t.Font, HorizontalAlignment = (TextHorizontalAlignment)t.HorizontalAlignment, VerticalAlignment = (TextVerticalAlignment)t.VerticalAlignment };
                var id = doc.Objects.AddText(text, Attributes(t.Output, Color.FromArgb(90, 105, 116))); Add(id);
                // Native GH Text3d preview uses model height directly. Override only this
                // owned annotation: the document's annotation-scale setting stays intact.
                using var entity = doc.Objects.FindId(id)?.Geometry.Duplicate() as TextEntity
                    ?? throw new InvalidOperationException("SUN-VIEW-001: Native text preview unavailable.");
                var parentStyle = doc.DimStyles.FindId(entity.DimensionStyleId);
                using var overrideStyle = entity.GetDimensionStyle(parentStyle).Duplicate();
                overrideStyle.Id = Guid.Empty; overrideStyle.ParentId = entity.DimensionStyleId;
                overrideStyle.DimensionScale = 1; overrideStyle.SetFieldOverride(DimensionStyle.Field.DimensionScale);
                if (!entity.SetOverrideDimStyle(overrideStyle) || !doc.Objects.Replace(id, entity))
                    throw new InvalidOperationException("SUN-VIEW-001: Text scale override failed.");
            }
            foreach (var p in next.Positions)
            {
                var id = doc.Objects.AddPoint(Pt(p.SunPoint), Attributes($"sun / HOY {p.HourOfYear:R}", Color.FromArgb(210, 139, 45))); Add(id); points.Add(id);
                // Use the actual physical 3D vector even with a flattened projected sun point.
                var start = Pt(next.InputParameters.Center) - Vec(p.SunlightVector) * (next.InputParameters.RadiusMetres / next.MetresPerModelUnit);
                Add(doc.Objects.AddLine(start, Pt(next.InputParameters.Center), Attributes("sunlight / towards centre", Color.FromArgb(183, 160, 120))));
            }
        }
        catch { foreach (var item in replacement) doc.Objects.Delete(item.Object, true); throw; }
        DeletePreview(); owned.AddRange(replacement); sunObjects.AddRange(points);
    }
    private static Point3d Pt(double[] p) => new(p[0], p[1], p[2]);
    private static Vector3d Vec(double[] p) => new(p[0], p[1], p[2]);
    public void DeletePreview()
    {
        foreach (var item in owned) { var doc = RhinoDoc.FromRuntimeSerialNumber(item.Document); doc?.Objects.Delete(item.Object, true); doc?.Views.Redraw(); }
        owned.Clear(); sunObjects.Clear();
        locate.Enabled = locateSun.Enabled = clear.Enabled = false;
    }
    public void LocateResult()
    {
        var doc = RequireDocument(); var bounds = BoundingBox.Empty;
        if (owned.Count == 0 || owned.Any(o => o.Document != doc.RuntimeSerialNumber)) throw new InvalidOperationException("SUN-VIEW-002: No preview in the active result document.");
        foreach (var o in owned) { var obj = doc.Objects.FindId(o.Object); if (obj is not null) bounds.Union(obj.Geometry.GetBoundingBox(true)); }
        if (!bounds.IsValid || doc.Views.ActiveView is null) throw new InvalidOperationException("SUN-VIEW-002: Preview or viewport unavailable."); doc.Views.ActiveView.ActiveViewport.ZoomBoundingBox(bounds); doc.Views.Redraw();
    }
    public void LocateSun()
    {
        var doc = RequireDocument(); var index = positions.SelectedIndex;
        if (result is null || index < 0 || index >= sunObjects.Count || doc.Objects.FindId(sunObjects[index]) is null || doc.Views.ActiveView is null) throw new InvalidOperationException("SUN-VIEW-002: Sun preview unavailable.");
        var point = Pt(result.Positions[index].SunPoint); var span = result.InputParameters.RadiusMetres / result.MetresPerModelUnit * .08;
        doc.Objects.Select(sunObjects[index]); doc.Views.ActiveView.ActiveViewport.ZoomBoundingBox(new BoundingBox(point - new Vector3d(span, span, span), point + new Vector3d(span, span, span))); doc.Views.Redraw();
    }
    public void UseCompletedLocation()
    {
        var doc = RequireDocument(); var panel = Rhino.UI.Panels.GetPanel<HubWorkspacePanel>(doc)?.GetModule<LocationPanel>();
        var completed = JsonSerializer.Deserialize<LocationResult>(panel?.CompletedResultJson ?? throw new InvalidOperationException("請先完成地點建立。"))!; SetLocation(completed.Location);
    }
    public void UseImportedWeather()
    {
        var doc = RequireDocument(); var panel = Rhino.UI.Panels.GetPanel<HubWorkspacePanel>(doc)?.GetModule<WeatherPanel>();
        var completed = JsonSerializer.Deserialize<WeatherResult>(panel?.CompletedResultJson ?? throw new InvalidOperationException("請先完成 EPW 匯入。"))!; SetLocation(completed.Location);
    }
    private void SetLocation(WeatherLocation location)
    {
        updating = true; try { name.Text = location.City; latitude.Value = location.Latitude; longitude.Value = location.Longitude; zone.Value = location.TimeZone; elevation.Value = location.Elevation; } finally { updating = false; }
        status.Text = result is null ? "已傳入完成的地點 · 請確認後執行" : "前次結果 · 地點已變更";
    }
    public void UseCompletedTime()
    {
        var doc = RequireDocument(); var panel = Rhino.UI.Panels.GetPanel<HubWorkspacePanel>(doc)?.GetModule<TimePanel>();
        using var json = JsonDocument.Parse(panel?.CompletedResultJson ?? throw new InvalidOperationException("請先在時間模組建立日期或分析期間。"));
        importedHours = json.RootElement.TryGetProperty("HoursOfYear", out var hours) ? hours.EnumerateArray().Select(v => v.GetDouble()).ToArray() : [json.RootElement.GetProperty("Time").GetProperty("HourOfYear").GetDouble()];
        RefreshTime(); status.Text = result is null ? "已傳入完成的時刻 · 請確認時間制後執行" : "前次結果 · 時刻已變更";
    }
}
