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
    private readonly TextBox file = new() { PlaceholderText = "Select a STAT or DDY file" };
    private readonly DropDown outputs = new();
    private readonly Label summary = new() { Wrap = WrapMode.Word };
    private readonly Label status = new() { Text = "Select source format and climate file.", Wrap = WrapMode.Word };
    private readonly Button import = new() { Text = "Import climate file", Enabled = false };
    private readonly Button export = new() { Text = "Export full result JSON…", Enabled = false };
    private ClimateFileResult? result;
    private bool updating;
    public string StatusText => status.Text;
    public string SummaryText => summary.Text;
    public ClimateFilePanel()
    {
        MinimumSize = new Size(300, 200); Size = new Size(360, 640); BackgroundColor = SystemColors.ControlBackground;
        format.Items.Add("STAT"); format.Items.Add("DDY"); format.SelectedIndex = 0;
        void Changed() { if (updating) return; import.Enabled = !string.IsNullOrWhiteSpace(file.Text);
            status.Text = result is null ? "Ready to import" : "Previous result • Import again to update"; }
        file.TextChanged += (_, _) => { file.ToolTip = file.Text; Changed(); }; format.SelectedIndexChanged += (_, _) => Changed();
        var browse = new Button { Text = "Browse climate file…" };
        browse.Click += (_, _) => { var dialog = new OpenFileDialog(); dialog.Filters.Add(new FileFilter("Climate file", "." + format.SelectedValue!.ToString()!.ToLowerInvariant()));
            if (dialog.ShowDialog(this) == DialogResult.Ok) file.Text = dialog.FileName; };
        import.Click += (_, _) => Guard(() => Execute(new() { Format = format.SelectedValue!.ToString()!, FilePath = file.Text }));
        outputs.SelectedIndexChanged += (_, _) => ShowOutput();
        export.Click += (_, _) => Guard(() => { if (result is null) return; var dialog = new SaveFileDialog { FileName = "climate_result.json" };
            dialog.Filters.Add(new FileFilter("Climate JSON", ".json")); if (dialog.ShowDialog(this) == DialogResult.Ok)
                File.WriteAllText(dialog.FileName, JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true })); });
        var layout = new DynamicLayout { Padding = 16, Spacing = new Size(8, 14) };
        layout.AddRow(HubUi.Header("Climate & design days", "Read climate zones, typical weeks and original design-day conditions."));
        layout.AddRow(HubUi.Navigation(typeof(ClimateFilePanel)));
        layout.AddRow(Section("01  Source", format, file, browse)); layout.AddRow(Section("02  Import", import, status));
        layout.AddRow(Section("03  Climate conditions", outputs, summary, export));
        layout.AddRow(new Label { Text = "Original LB Import STAT / DDY • Synchronous execution. STAT clear-sky radiation is modeled, not measured EPW radiation.", Wrap = WrapMode.Word }); layout.Add(null);
        var scroll = new Scrollable { Content = layout, ExpandContentWidth = true }; scroll.SizeChanged += (_, _) => layout.Width = Math.Max(120, scroll.ClientSize.Width - 20); Content = scroll;
    }
    private static Control Section(string title, params Control[] controls) => HubUi.Section(title, controls);
    private void Guard(Action action) { try { action(); } catch (Exception e) { status.Text = (result is null ? "Import failed\n" : "Import failed • Previous result retained\n") + e.Message; } }
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
            status.Text = $"Imported • {result.Outputs.Count(o => o.Index >= 0)} original objects" + (result.Warnings.Length == 0 ? "" : "\n" + string.Join("\n", result.Warnings.Select(w => w.Message)));
            return JsonSerializer.Serialize(result);
        }
        catch (Exception e) { status.Text = (result is null ? "Import failed\n" : "Import failed • Previous result retained\n") + e.Message; throw; }
        finally { import.Enabled = !string.IsNullOrWhiteSpace(file.Text); }
    }
    private void ShowOutput()
    {
        if (result is null || outputs.SelectedIndex < 0) return;
        var o = result.Outputs[outputs.SelectedIndex]; var data = o.Data;
        if (data.ValueKind == JsonValueKind.Object && data.TryGetProperty("values", out var values))
            summary.Text = $"{HubUi.FieldTitle(o.Output)}\n{values.GetArrayLength()} values • {data.GetProperty("header").GetProperty("unit").GetString()}\nOriginal header, time period and all values included in export.";
        else if (o.Kind == "DesignDay")
            summary.Text = $"{data.GetProperty("name").GetString()}\n{data.GetProperty("day_type").GetString()}\nDry bulb max {data.GetProperty("dry_bulb_condition").GetProperty("dry_bulb_max").GetDouble():F2} °C\nHumidity, wind, sky and location conditions included in export.";
        else if (o.Kind == "Location")
            summary.Text = $"{data.GetProperty("city").GetString()}\nLatitude {data.GetProperty("latitude").GetDouble():F4}° • Longitude {data.GetProperty("longitude").GetDouble():F4}°\n{ClimateDisplay.UtcOffset(data.GetProperty("time_zone").GetDouble())} • Elevation {data.GetProperty("elevation").GetDouble():F1} m";
        else if (o.Kind == "AnalysisPeriod")
            summary.Text = $"Start {data.GetProperty("st_month").GetInt32():00}/{data.GetProperty("st_day").GetInt32():00} {data.GetProperty("st_hour").GetInt32():00}:00\nEnd {data.GetProperty("end_month").GetInt32():00}/{data.GetProperty("end_day").GetInt32():00} {data.GetProperty("end_hour").GetInt32():00}:00\n{data.GetProperty("timestep").GetInt32()} steps / hour • Local standard time";
        else if (data.ValueKind == JsonValueKind.String) summary.Text = data.GetString();
        else summary.Text = o.Kind == "Unavailable" || data.ValueKind == JsonValueKind.Null ? "Unavailable in original source" : "Additional original fields included in full export.";
    }
}
