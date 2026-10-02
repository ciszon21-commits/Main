using System.Runtime.InteropServices;
using System.Text.Json;
using EnvironmentalHub.Core;
using EnvironmentalHub.Adapters;
using Eto.Forms;
using Eto.Drawing;
using Panels = Rhino.UI.Panels;

namespace EnvironmentalHub.Plugin;

[Guid("5f78d8d4-e9a1-4713-bb04-d08466339735")]
public sealed class LocationPanel : Panel
{
    private readonly TextBox name = new() { Text = "地點" };
    private readonly NumericStepper latitude = Number(-90, 90);
    private readonly NumericStepper longitude = Number(-180, 180);
    private readonly NumericStepper zone = Number(-12, 12);
    private readonly NumericStepper elevation = Number(-100000, 100000);
    private readonly CheckBox estimate = new() { Text = "依經度估算時區", Checked = false };
    private readonly Label status = new() { Text = "設定地點資料，使用原生 Ladybug 建立地點。", Wrap = WrapMode.Word };
    private readonly Label summary = new() { Wrap = WrapMode.Word };
    private readonly Button run = new() { Text = "建立地點" };
    private readonly Button export = new() { Text = "匯出地點 JSON…", Enabled = false };
    private LocationResult? result;
    private bool updating;
    public string SummaryText => summary.Text;
    public string StatusText => status.Text;
    private static NumericStepper Number(double min, double max) => new() { MinValue = min, MaxValue = max, DecimalPlaces = 4, Increment = 0.25, Width = 100 };
    public LocationPanel()
    {
        MinimumSize = new Size(300, 200); Size = new Size(360, 640); BackgroundColor = SystemColors.ControlBackground;
        void Changed() { if (!updating) status.Text = result is null ? "可建立地點" : "前次結果 · 重新建立以更新"; }
        name.TextChanged += (_, _) => Changed();
        foreach (var n in new[] { latitude, longitude, zone, elevation }) n.ValueChanged += (_, _) => Changed();
        estimate.CheckedChanged += (_, _) => { zone.Enabled = estimate.Checked != true; Changed(); };
        run.Click += (_, _) => Guard(() => Execute(new() { Name = name.Text, Latitude = latitude.Value, Longitude = longitude.Value,
            TimeZone = estimate.Checked == true ? null : zone.Value, ElevationMetres = elevation.Value }));
        export.Click += (_, _) => Guard(() =>
        {
            if (result is null) return;
            var dialog = new SaveFileDialog { FileName = "location_result.json" };
            dialog.Filters.Add(new FileFilter("地點 JSON", ".json"));
            if (dialog.ShowDialog(this) == DialogResult.Ok) File.WriteAllText(dialog.FileName, JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }));
        });
        var inputs = new DynamicLayout { Padding = 12, Spacing = new Size(8, 8) };
        var inputFields = new DynamicLayout { Spacing = new Size(8, 8) };
        inputFields.AddRow(new Label { Text = "名稱" }, name); inputFields.AddRow(new Label { Text = "緯度 (°)" }, latitude);
        inputFields.AddRow(new Label { Text = "經度 (°)" }, longitude); inputFields.AddRow(new Label { Text = "UTC 時差 (h)" }, zone);
        inputFields.AddRow(new Label { Text = "海拔 (m)" }, elevation);
        inputs.AddRow(inputFields); inputs.AddRow(estimate);
        var actions = new DynamicLayout { Padding = 12, Spacing = new Size(8, 8) }; actions.AddRow(run); actions.AddRow(status);
        var output = new DynamicLayout { Padding = 12, Spacing = new Size(8, 8) }; output.AddRow(summary); output.AddRow(export);
        var layout = new DynamicLayout { Padding = 16, Spacing = new Size(8, 14) };
        layout.AddRow(HubUi.Header("地點", "建立座標與時區，作為環境分析的地點條件。",typeof(LocationPanel)));
        layout.AddRow(HubUi.Navigation(typeof(LocationPanel))); layout.AddRow(HubUi.Section("01  地點輸入",HubTopic.Environment, inputs));
        layout.AddRow(HubUi.Section("02  建立地點",HubTopic.Run, actions)); layout.AddRow(HubUi.Section("03  分析結果",HubTopic.Results, output));
        layout.AddRow(new Label { Text = "使用原生 LB Construct Location；不產生氣象資料。採同步執行。", Wrap = WrapMode.Word }); layout.Add(null);
        var scroll = new Scrollable { Content = layout, ExpandContentWidth = true };
        scroll.SizeChanged += (_, _) => layout.Width = Math.Max(120, scroll.ClientSize.Width - 20); Content = scroll;
    }
    private void Guard(Action action) { try { action(); } catch (Exception e) { status.Text = (result is null ? "執行失敗\n" : "執行失敗 · 已保留前次結果\n") + HubText.Error(e); } }
    public string ExecuteJson(string json) => Execute(JsonSerializer.Deserialize<LocationRequest>(json)!);
    private string Execute(LocationRequest request)
    {
        run.Enabled = false;
        try
        {
            using var config = JsonDocument.Parse(File.ReadAllText(Path.Combine(Path.GetDirectoryName(GetType().Assembly.Location)!, "hub.config.json")));
            var imported = new LadybugLocationAdapter(System.Environment.ExpandEnvironmentVariables(config.RootElement.GetProperty("UserObjectDirectory").GetString()!)).Execute(request);
            updating = true;
            try { name.Text = request.Name; latitude.Value = request.Latitude; longitude.Value = request.Longitude;
                estimate.Checked = request.TimeZone is null; zone.Value = request.TimeZone ?? imported.Location.TimeZone; elevation.Value = request.ElevationMetres; }
            finally { updating = false; }
            result = imported;
            var p = result.Location;
            summary.Text = $"{p.City}\n緯度 {p.Latitude:F4}° • 經度 {p.Longitude:F4}°\n{ClimateDisplay.UtcOffset(p.TimeZone)} • 海拔 {p.Elevation:F2} m";
            status.Text = "地點已建立" + (result.Warnings.Length == 0 ? "" : "\n" + string.Join("\n", result.Warnings.Select(HubText.Diagnostic)));
            export.Enabled = true; return JsonSerializer.Serialize(result);
        }
        catch (Exception e) { status.Text = (result is null ? "執行失敗\n" : "執行失敗 · 已保留前次結果\n") + HubText.Error(e); throw; }
        finally { run.Enabled = true; }
    }
}
