using System.Runtime.InteropServices;
using System.Text.Json;
using EnvironmentalHub.Adapters;
using EnvironmentalHub.Core;
using Eto.Drawing;
using Eto.Forms;
using Panels = Rhino.UI.Panels;

namespace EnvironmentalHub.Plugin;

[Guid("1c0c5ac3-b820-42f2-9aaa-1e0f50356d1a")]
public sealed class WeatherPanel : Panel
{
    private readonly TextBox file = new() { PlaceholderText = "選擇 EPW 氣象檔案" };
    private readonly CheckBox annual = new() { Text = "全年", Checked = true };
    private readonly NumericStepper start = new() { MinValue = 0, MaxValue = 8759, Value = 0, Width = 100 };
    private readonly NumericStepper end = new() { MinValue = 0, MaxValue = 8759, Value = 23, Width = 100 };
    private readonly DropDown fields = new();
    private readonly Label status = new() { Text = "選擇 EPW 檔案，匯入 Ladybug 原生氣象資料。", Wrap = WrapMode.Word };
    private readonly Label location = new() { Text = "尚未匯入氣象資料", Wrap = WrapMode.Word };
    private readonly Label summary = new() { Wrap = WrapMode.Word };
    private readonly Button import = new() { Text = "匯入氣象", Enabled = false };
    private readonly Button export = new() { Text = "匯出完整結果 JSON…", Enabled = false };
    private WeatherResult? result;
    private bool updating;
    private int[]? customHours;
    private readonly Label periodNote = new() { Text = "HOY 0 = 1 月 1 日 00:00 · 當地標準時間", Wrap = WrapMode.Word };
    public string StatusText => status.Text;
    public string SummaryText => summary.Text;
    public string ProductVersion => GetType().Assembly.GetName().Version!.ToString(3);
    public string? CompletedSelectionJson => result is null ? null : JsonSerializer.Serialize(result.InputParameters);

    public WeatherPanel()
    {
        Size = new Size(360, 640); MinimumSize = new Size(300, 200);
        BackgroundColor = SystemColors.ControlBackground;
        var browse = new Button { Text = "瀏覽 EPW 檔案…" };
        browse.Click += (_, _) =>
        {
            var dialog = new OpenFileDialog(); dialog.Filters.Add(new FileFilter("EPW 氣象", ".epw"));
            if (dialog.ShowDialog(this) == DialogResult.Ok) file.Text = dialog.FileName;
        };
        file.TextChanged += (_, _) => { file.ToolTip = file.Text; Changed(); };
        annual.CheckedChanged += (_, _) => { start.Enabled = end.Enabled = annual.Checked != true; PeriodChanged(); };
        start.ValueChanged += (_, _) => PeriodChanged(); end.ValueChanged += (_, _) => PeriodChanged();
        start.Enabled = end.Enabled = false;
        import.Click += (_, _) => Guard(() => Execute(new WeatherRequest { WeatherFile = file.Text,
            HoursOfYear = annual.Checked == true ? [] : customHours is not null ? customHours : end.Value < start.Value
                ? throw new InvalidOperationException("CLIMATE-PERIOD-001: End hour must be at or after start.")
                : Enumerable.Range((int)start.Value, (int)(end.Value - start.Value + 1)).ToArray() }));
        fields.SelectedIndexChanged += (_, _) => ShowSeries();
        export.Click += (_, _) => Guard(() =>
        {
            if (result is null) return;
            var dialog = new SaveFileDialog { FileName = "weather_result.json" };
            dialog.Filters.Add(new FileFilter("氣象結果 JSON", ".json"));
            if (dialog.ShowDialog(this) == DialogResult.Ok)
                File.WriteAllText(dialog.FileName, JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }));
        });
        var period = new DynamicLayout { Spacing = new Size(8, 8) };
        var periodFields = new DynamicLayout { Spacing = new Size(8, 8) };
        periodFields.AddRow(new Label { Text = "起始年時數" }, start); periodFields.AddRow(new Label { Text = "結束年時數" }, end);
        period.AddRow(annual); period.AddRow(periodFields);
        period.AddRow(periodNote);
        var layout = new DynamicLayout { Padding = 16, Spacing = new Size(8, 14) };
        layout.AddRow(HubUi.Header("EPW 氣象", "匯入氣象欄位、選擇時間範圍並檢視原始資料。",typeof(WeatherPanel)));
        layout.AddRow(Section("01  氣象來源",HubTopic.Environment, file, browse, Hint("原生 LB Import EPW · 非閏年逐時 EPW")));
        layout.AddRow(HubUi.Section("02  時間選取",HubTopic.Settings, period));
        layout.AddRow(Section("03  匯入",HubTopic.Run, import, status));
        layout.AddRow(Section("04  氣象資料",HubTopic.Results, location, fields, summary, export)); layout.Add(null);
        var scroll = new Scrollable { Content = layout, ExpandContentWidth = true };
        scroll.SizeChanged += (_, _) => layout.Width = Math.Max(120, scroll.ClientSize.Width - 20);
        Content = scroll;
    }
    private static Label Hint(string text) => new() { Text = text, Wrap = WrapMode.Word, TextColor = SystemColors.ControlText };
    private static Control Section(string title, HubTopic topic, params Control[] controls) => HubUi.Section(title, topic, controls);
    private void PeriodChanged()
    {
        if (updating) return;
        customHours = null;
        periodNote.Text = "HOY 0 = 1 月 1 日 00:00 · 當地標準時間";
        Changed();
    }
    private void Changed()
    {
        if (updating) return;
        import.Enabled = !string.IsNullOrWhiteSpace(file.Text);
        status.Text = result is null ? "輸入已變更 · 可匯入" : "前次結果 · 重新匯入以更新";
    }
    private void Guard(Action action)
    {
        try { action(); } catch (Exception e) { status.Text = (result is null ? "匯入失敗\n" : "匯入失敗 · 已保留前次結果\n") + HubText.Error(e); }
    }
    public string ExecuteJson(string json) => Execute(JsonSerializer.Deserialize<WeatherRequest>(json)!);
    private string Execute(WeatherRequest request)
    {
        import.Enabled = false;
        try
        {
            var path = Path.Combine(Path.GetDirectoryName(GetType().Assembly.Location)!, "hub.config.json");
            using var config = JsonDocument.Parse(File.ReadAllText(path));
            var directory = System.Environment.ExpandEnvironmentVariables(config.RootElement.GetProperty("UserObjectDirectory").GetString()!);
            var imported = new LadybugWeatherAdapter(directory).Execute(request);
            updating = true;
            try
            {
                file.Text = request.WeatherFile; annual.Checked = request.HoursOfYear.Length == 0;
                customHours = null;
                if (request.HoursOfYear.Length > 0)
                {
                    start.Value = request.HoursOfYear.Min(); end.Value = request.HoursOfYear.Max();
                    if (!request.HoursOfYear.SequenceEqual(Enumerable.Range((int)start.Value, (int)(end.Value - start.Value + 1))))
                        customHours = request.HoursOfYear.ToArray();
                }
                periodNote.Text = customHours is null ? "HOY 0 = 1 月 1 日 00:00 · 當地標準時間"
                    : $"自訂 {customHours.Length} 小時 · 修改範圍將取代此選取";
            }
            finally { updating = false; }
            result = imported;
            fields.Items.Clear();
            foreach (var s in result.Series) fields.Items.Add($"{HubText.Field(s.Output)}" +
                (result.Series.Count(other => other.Output == s.Output) > 1 ? $" · 資料組 {s.CollectionIndex + 1}" : "") + $" • {s.Units}");
            fields.SelectedIndex = 0; ShowSeries();
            location.Text = $"{result.Location.City}, {result.Location.Country}\n緯度 {result.Location.Latitude:F3} • 經度 {result.Location.Longitude:F3} • {ClimateDisplay.UtcOffset(result.Location.TimeZone)}";
            status.Text = $"匯入完成 · {result.Series.Length} 組資料" + (result.Warnings.Length == 0 ? "" : "\n" + string.Join("\n", result.Warnings.Select(HubText.Diagnostic)));
            export.Enabled = true;
            return JsonSerializer.Serialize(result);
        }
        catch (Exception e) { status.Text = (result is null ? "匯入失敗\n" : "匯入失敗 · 已保留前次結果\n") + HubText.Error(e); throw; }
        finally { import.Enabled = !string.IsNullOrWhiteSpace(file.Text); }
    }
    private void ShowSeries()
    {
        if (result is null || fields.SelectedIndex < 0) return;
        var s = result.Series[fields.SelectedIndex];
        var stats = s.Statistics;
        summary.Text = $"{HubText.Field(s.Output)} • {s.Units}\n{s.Values.Length} {HubText.Frequency(s.Frequency)}資料 • {s.Missing.Count(v => v)} 筆缺值";
        if (stats is not null)
        {
            summary.Text += $"\n最小值 {stats.Minimum:F3} • 最大值 {stats.Maximum:F3}";
            if (s.Output != "wind_direction" && s.Output != "model_year") summary.Text += $" • 平均值 {stats.Mean:F3}";
        }
        if (s.Metadata.Count > 0) summary.Text += "\n" + string.Join(" • ", s.Metadata.Select(p => HubText.Field(p.Key) + "：" + p.Value));
    }
}
