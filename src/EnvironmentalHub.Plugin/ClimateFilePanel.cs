using System.Runtime.InteropServices;
using System.Text.Json;
using EnvironmentalHub.Core;
using EnvironmentalHub.Adapters;
using Eto.Forms;
using Eto.Drawing;
using Panels = Rhino.UI.Panels;

namespace EnvironmentalHub.Plugin;

[Guid("499a99e8-8e73-4a6b-8208-fc879e413d36")]
public sealed class ClimateFilePanel : Panel
{
    private readonly DropDown format = new();
    private readonly TextBox file = new() { PlaceholderText = "選擇 STAT 或 DDY 檔案" };
    private readonly DropDown outputs = new();
    private readonly Label summary = new() { Wrap = WrapMode.Word };
    private readonly Label status = new() { Text = "選擇來源格式與氣候檔案。", Wrap = WrapMode.Word };
    private readonly Button import = new() { Text = "匯入氣候檔案", Enabled = false };
    private readonly Button export = new() { Text = "匯出完整結果 JSON…", Enabled = false };
    private ClimateFileResult? result;
    private bool updating;
    public string StatusText => status.Text;
    public string SummaryText => summary.Text;
    public ClimateFilePanel()
    {
        MinimumSize = new Size(300, 200); Size = new Size(360, 640); BackgroundColor = SystemColors.ControlBackground;
        format.Items.Add("STAT"); format.Items.Add("DDY"); format.SelectedIndex = 0;
        void Changed() { if (updating) return; import.Enabled = !string.IsNullOrWhiteSpace(file.Text);
            status.Text = result is null ? "可匯入" : "前次結果 · 重新匯入以更新"; }
        file.TextChanged += (_, _) => { file.ToolTip = file.Text; Changed(); }; format.SelectedIndexChanged += (_, _) => Changed();
        var browse = new Button { Text = "瀏覽氣候檔案…" };
        browse.Click += (_, _) => { var dialog = new OpenFileDialog(); dialog.Filters.Add(new FileFilter("氣候檔案", "." + format.SelectedValue!.ToString()!.ToLowerInvariant()));
            if (dialog.ShowDialog(this) == DialogResult.Ok) file.Text = dialog.FileName; };
        import.Click += (_, _) => Guard(() => Execute(new() { Format = format.SelectedValue!.ToString()!, FilePath = file.Text }));
        outputs.SelectedIndexChanged += (_, _) => ShowOutput();
        export.Click += (_, _) => Guard(() => { if (result is null) return; var dialog = new SaveFileDialog { FileName = "climate_result.json" };
            dialog.Filters.Add(new FileFilter("氣候結果 JSON", ".json")); if (dialog.ShowDialog(this) == DialogResult.Ok)
                File.WriteAllText(dialog.FileName, JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true })); });
        var layout = new DynamicLayout { Padding = 16, Spacing = new Size(8, 14) };
        layout.AddRow(HubUi.Header("氣候與設計日", "讀取氣候分區、典型週與原生設計日條件。",typeof(ClimateFilePanel)));
        layout.AddRow(Section("01  資料來源",HubTopic.Environment, format, file, browse)); layout.AddRow(Section("02  匯入",HubTopic.Run, import, status));
        layout.AddRow(Section("03  氣候條件",HubTopic.Results, outputs, summary, export));
        layout.AddRow(new Label { Text = "使用原生 LB Import STAT / DDY，同步執行。STAT 晴空輻射為模型估算，與 EPW 實測輻射不同。", Wrap = WrapMode.Word }); layout.Add(null);
        var scroll = new Scrollable { Content = layout, ExpandContentWidth = true }; scroll.SizeChanged += (_, _) => layout.Width = Math.Max(120, scroll.ClientSize.Width - 20); Content = scroll;
    }
    private static Control Section(string title, HubTopic topic, params Control[] controls) => HubUi.Section(title, topic, controls);
    private void Guard(Action action) { try { action(); } catch (Exception e) { status.Text = (result is null ? "匯入失敗\n" : "匯入失敗 · 已保留前次結果\n") + HubText.Error(e); } }
    public string ExecuteJson(string json) => Execute(JsonSerializer.Deserialize<ClimateFileRequest>(json)!);
    private string Execute(ClimateFileRequest request)
    {
        import.Enabled = false;
        try
        {
            using var config = JsonDocument.Parse(File.ReadAllText(Path.Combine(Path.GetDirectoryName(GetType().Assembly.Location)!, "hub.config.json")));
            var imported = new LadybugClimateFileAdapter(System.Environment.ExpandEnvironmentVariables(config.RootElement.GetProperty("UserObjectDirectory").GetString()!)).Execute(request);
            updating = true; try { file.Text = request.FilePath; format.SelectedIndex = request.Format == "STAT" ? 0 : 1; } finally { updating = false; }
            result = imported; outputs.Items.Clear(); foreach (var o in result.Outputs) outputs.Items.Add(HubUi.FieldTitle(o.Output) +
                (result.Outputs.Count(other => other.Output == o.Output) > 1 && o.Index >= 0 ? $" · {o.Index + 1}" : ""));
            outputs.SelectedIndex = 0; ShowOutput(); export.Enabled = true;
            status.Text = $"匯入完成 · {result.Outputs.Count(o => o.Index >= 0)} 個原生物件" + (result.Warnings.Length == 0 ? "" : "\n" + string.Join("\n", result.Warnings.Select(HubText.Diagnostic)));
            return JsonSerializer.Serialize(result);
        }
        catch (Exception e) { status.Text = (result is null ? "匯入失敗\n" : "匯入失敗 · 已保留前次結果\n") + HubText.Error(e); throw; }
        finally { import.Enabled = !string.IsNullOrWhiteSpace(file.Text); }
    }
    private void ShowOutput()
    {
        if (result is null || outputs.SelectedIndex < 0) return;
        var o = result.Outputs[outputs.SelectedIndex]; var data = o.Data;
        if (data.ValueKind == JsonValueKind.Object && data.TryGetProperty("values", out var values))
            summary.Text = $"{HubUi.FieldTitle(o.Output)}\n{values.GetArrayLength()} 筆數值 · {data.GetProperty("header").GetProperty("unit").GetString()}\n匯出包含原始資料標頭、期間與全部數值。";
        else if (o.Kind == "DesignDay")
            summary.Text = $"{data.GetProperty("name").GetString()}\n{HubText.DayType(data.GetProperty("day_type").GetString())}\n最高乾球溫度 {data.GetProperty("dry_bulb_condition").GetProperty("dry_bulb_max").GetDouble():F2} °C\n匯出包含濕度、風、天空與地點條件。";
        else if (o.Kind == "Location")
            summary.Text = $"{data.GetProperty("city").GetString()}\n緯度 {data.GetProperty("latitude").GetDouble():F4}° • 經度 {data.GetProperty("longitude").GetDouble():F4}°\n{ClimateDisplay.UtcOffset(data.GetProperty("time_zone").GetDouble())} • 海拔 {data.GetProperty("elevation").GetDouble():F1} m";
        else if (o.Kind == "AnalysisPeriod")
            summary.Text = $"起始 {data.GetProperty("st_month").GetInt32():00}/{data.GetProperty("st_day").GetInt32():00} {data.GetProperty("st_hour").GetInt32():00}:00\n結束 {data.GetProperty("end_month").GetInt32():00}/{data.GetProperty("end_day").GetInt32():00} {data.GetProperty("end_hour").GetInt32():00}:00\n{data.GetProperty("timestep").GetInt32()} 步／小時 · 當地標準時間";
        else if (data.ValueKind == JsonValueKind.String) summary.Text = data.GetString();
        else summary.Text = o.Kind == "Unavailable" || data.ValueKind == JsonValueKind.Null ? "原始資料未提供" : "完整匯出包含其他原始欄位。";
    }
}
