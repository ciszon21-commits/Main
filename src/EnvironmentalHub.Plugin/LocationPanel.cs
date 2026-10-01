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
    private readonly TextBox name = new() { Text = "Location" };
    private readonly NumericStepper latitude = Number(-90, 90);
    private readonly NumericStepper longitude = Number(-180, 180);
    private readonly NumericStepper zone = Number(-12, 12);
    private readonly NumericStepper elevation = Number(-100000, 100000);
    private readonly CheckBox estimate = new() { Text = "Estimate time zone from longitude", Checked = false };
    private readonly Label status = new() { Text = "Set location and construct using original Ladybug.", Wrap = WrapMode.Word };
    private readonly Label summary = new() { Wrap = WrapMode.Word };
    private readonly Button run = new() { Text = "Construct location" };
    private readonly Button export = new() { Text = "Export location JSON…", Enabled = false };
    private LocationResult? result;
    private bool updating;
    public string SummaryText => summary.Text;
    public string StatusText => status.Text;
    private static NumericStepper Number(double min, double max) => new() { MinValue = min, MaxValue = max, DecimalPlaces = 4, Increment = 0.25, Width = 120 };
    public LocationPanel()
    {
        MinimumSize = new Size(300, 200); Size = new Size(360, 640); BackgroundColor = SystemColors.ControlBackground;
        void Changed() { if (!updating) status.Text = result is null ? "Ready to construct" : "Previous result • Construct again to update"; }
        name.TextChanged += (_, _) => Changed();
        foreach (var n in new[] { latitude, longitude, zone, elevation }) n.ValueChanged += (_, _) => Changed();
        estimate.CheckedChanged += (_, _) => { zone.Enabled = estimate.Checked != true; Changed(); };
        run.Click += (_, _) => Guard(() => Execute(new() { Name = name.Text, Latitude = latitude.Value, Longitude = longitude.Value,
            TimeZone = estimate.Checked == true ? null : zone.Value, ElevationMetres = elevation.Value }));
        export.Click += (_, _) => Guard(() =>
        {
            if (result is null) return;
            var dialog = new SaveFileDialog { FileName = "location_result.json" };
            dialog.Filters.Add(new FileFilter("Location JSON", ".json"));
            if (dialog.ShowDialog(this) == DialogResult.Ok) File.WriteAllText(dialog.FileName, JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }));
        });
        var weather = new Button { Text = "Weather & climate…" }; weather.Click += (_, _) => Panels.OpenPanel(typeof(WeatherPanel));
        var inputs = new DynamicLayout { Padding = 10, Spacing = new Size(8, 8) };
        inputs.AddRow(new Label { Text = "Name" }, name); inputs.AddRow(new Label { Text = "Latitude (°)" }, latitude);
        inputs.AddRow(new Label { Text = "Longitude (°)" }, longitude); inputs.AddRow(new Label { Text = "UTC offset (hours)" }, zone);
        inputs.AddRow(estimate); inputs.AddRow(new Label { Text = "Elevation (m)" }, elevation);
        var actions = new DynamicLayout { Padding = 10, Spacing = new Size(8, 8) }; actions.AddRow(run); actions.AddRow(status);
        var output = new DynamicLayout { Padding = 10, Spacing = new Size(8, 8) }; output.AddRow(summary); output.AddRow(export);
        var layout = new DynamicLayout { Padding = 14, Spacing = new Size(8, 12) };
        layout.AddRow(new Label { Text = "Construct location", Font = new Eto.Drawing.Font(SystemFont.Bold, 16) });
        layout.AddRow(new Label { Text = "Environmental Simulation Hub • " + GetType().Assembly.GetName().Version!.ToString(3) });
        layout.AddRow(weather); layout.AddRow(new GroupBox { Text = "01  Location inputs", Content = inputs });
        layout.AddRow(new GroupBox { Text = "02  Construct", Content = actions }); layout.AddRow(new GroupBox { Text = "03  Result", Content = output });
        layout.AddRow(new Label { Text = "Original LB Construct Location • No weather data generated. Execution is synchronous.", Wrap = WrapMode.Word }); layout.Add(null);
        var scroll = new Scrollable { Content = layout, ExpandContentWidth = true };
        scroll.SizeChanged += (_, _) => layout.Width = Math.Max(120, scroll.ClientSize.Width - 20); Content = scroll;
    }
    private void Guard(Action action) { try { action(); } catch (Exception e) { status.Text = (result is null ? "Failed\n" : "Failed • Previous result retained\n") + e.Message; } }
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
            summary.Text = $"{p.City}\nLatitude {p.Latitude:F4}° • Longitude {p.Longitude:F4}°\n{ClimateDisplay.UtcOffset(p.TimeZone)} • Elevation {p.Elevation:F2} m";
            status.Text = "Constructed" + (result.Warnings.Length == 0 ? "" : "\n" + string.Join("\n", result.Warnings.Select(w => w.Message)));
            export.Enabled = true; return JsonSerializer.Serialize(result);
        }
        catch (Exception e) { status.Text = (result is null ? "Failed\n" : "Failed • Previous result retained\n") + e.Message; throw; }
        finally { run.Enabled = true; }
    }
}
