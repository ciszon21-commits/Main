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
    private readonly TextBox file = new() { PlaceholderText = "Select EPW weather file" };
    private readonly CheckBox annual = new() { Text = "Full year", Checked = true };
    private readonly NumericStepper start = new() { MinValue = 0, MaxValue = 8759, Value = 0, Width = 100 };
    private readonly NumericStepper end = new() { MinValue = 0, MaxValue = 8759, Value = 23, Width = 100 };
    private readonly DropDown fields = new();
    private readonly Label status = new() { Text = "Select an EPW to import original Ladybug weather data.", Wrap = WrapMode.Word };
    private readonly Label location = new() { Text = "No weather imported", Wrap = WrapMode.Word };
    private readonly Label summary = new() { Wrap = WrapMode.Word };
    private readonly Button import = new() { Text = "Import weather", Enabled = false };
    private readonly Button export = new() { Text = "Export full result JSON…", Enabled = false };
    private WeatherResult? result;
    private bool updating;
    private int[]? customHours;
    private readonly Label periodNote = new() { Text = "0 = Jan 1 00:00 • Local standard time", Wrap = WrapMode.Word };
    public string StatusText => status.Text;
    public string SummaryText => summary.Text;
    public string ProductVersion => GetType().Assembly.GetName().Version!.ToString(3);
    public string? CompletedSelectionJson => result is null ? null : JsonSerializer.Serialize(result.InputParameters);

    public WeatherPanel()
    {
        Size = new Size(360, 640); MinimumSize = new Size(300, 200);
        BackgroundColor = SystemColors.ControlBackground;
        var browse = new Button { Text = "Browse EPW…" };
        browse.Click += (_, _) =>
        {
            var dialog = new OpenFileDialog(); dialog.Filters.Add(new FileFilter("EPW weather", ".epw"));
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
            dialog.Filters.Add(new FileFilter("Weather JSON", ".json"));
            if (dialog.ShowDialog(this) == DialogResult.Ok)
                File.WriteAllText(dialog.FileName, JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }));
        });
        var period = new DynamicLayout { Spacing = new Size(8, 8) };
        var periodFields = new DynamicLayout { Spacing = new Size(8, 8) };
        periodFields.AddRow(new Label { Text = "Start HOY" }, start); periodFields.AddRow(new Label { Text = "End HOY" }, end);
        period.AddRow(annual); period.AddRow(periodFields);
        period.AddRow(periodNote);
        var layout = new DynamicLayout { Padding = 16, Spacing = new Size(8, 14) };
        layout.AddRow(HubUi.Header("EPW weather", "Import climate fields, choose a time range and inspect the original data."));
        layout.AddRow(HubUi.Navigation(typeof(WeatherPanel)));
        layout.AddRow(Section("01  Weather source", file, browse, Hint("Original LB Import EPW • Non-leap hourly EPW")));
        layout.AddRow(HubUi.Section("02  Time selection", period));
        layout.AddRow(Section("03  Import", import, status));
        layout.AddRow(Section("04  Weather data", location, fields, summary, export)); layout.Add(null);
        var scroll = new Scrollable { Content = layout, ExpandContentWidth = true };
        scroll.SizeChanged += (_, _) => layout.Width = Math.Max(120, scroll.ClientSize.Width - 20);
        Content = scroll;
    }
    private static Label Hint(string text) => new() { Text = text, Wrap = WrapMode.Word, TextColor = SystemColors.ControlText };
    private static Control Section(string title, params Control[] controls) => HubUi.Section(title, controls);
    private void PeriodChanged()
    {
        if (updating) return;
        customHours = null;
        periodNote.Text = "0 = Jan 1 00:00 • Local standard time";
        Changed();
    }
    private void Changed()
    {
        if (updating) return;
        import.Enabled = !string.IsNullOrWhiteSpace(file.Text);
        status.Text = result is null ? "Inputs changed • Ready to import" : "Previous result • Import again to update";
    }
    private void Guard(Action action)
    {
        try { action(); } catch (Exception e) { status.Text = (result is null ? "Import failed\n" : "Import failed • Previous result retained\n") + e.Message; }
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
                periodNote.Text = customHours is null ? "0 = Jan 1 00:00 • Local standard time"
                    : $"Custom {customHours.Length} hours • Editing range replaces selection";
            }
            finally { updating = false; }
            result = imported;
            fields.Items.Clear();
            foreach (var s in result.Series) fields.Items.Add($"{s.DataType}" +
                (result.Series.Count(other => other.Output == s.Output) > 1 ? $" · Collection {s.CollectionIndex + 1}" : "") + $" • {s.Units}");
            fields.SelectedIndex = 0; ShowSeries();
            location.Text = $"{result.Location.City}, {result.Location.Country}\nLatitude {result.Location.Latitude:F3} • Longitude {result.Location.Longitude:F3} • {ClimateDisplay.UtcOffset(result.Location.TimeZone)}";
            status.Text = $"Imported • {result.Series.Length} data collections" + (result.Warnings.Length == 0 ? "" : "\n" + string.Join("\n", result.Warnings.Select(w => w.Message)));
            export.Enabled = true;
            return JsonSerializer.Serialize(result);
        }
        catch (Exception e) { status.Text = (result is null ? "Import failed\n" : "Import failed • Previous result retained\n") + e.Message; throw; }
        finally { import.Enabled = !string.IsNullOrWhiteSpace(file.Text); }
    }
    private void ShowSeries()
    {
        if (result is null || fields.SelectedIndex < 0) return;
        var s = result.Series[fields.SelectedIndex];
        var stats = s.Statistics;
        summary.Text = $"{s.DataType} • {s.Units}\n{s.Values.Length} {s.Frequency.ToLowerInvariant()} values • {s.Missing.Count(v => v)} missing";
        if (stats is not null)
        {
            summary.Text += $"\nMin {stats.Minimum:F3} • Max {stats.Maximum:F3}";
            if (s.Output != "wind_direction" && s.Output != "model_year") summary.Text += $" • Mean {stats.Mean:F3}";
        }
        if (s.Metadata.Count > 0) summary.Text += "\n" + string.Join(" • ", s.Metadata.Select(p => p.Key + ": " + p.Value));
    }
}
