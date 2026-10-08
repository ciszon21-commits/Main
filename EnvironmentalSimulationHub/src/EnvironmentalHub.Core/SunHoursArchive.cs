using System.Globalization;
using System.Text;
using System.Text.Json;

namespace EnvironmentalHub.Core;

public sealed record SunHoursScenario(string Name, SunHoursResult Result, bool Imported = false);
public sealed record SunHoursArchive(int BaselineIndex, int CandidateIndex, SunHoursScenario[] Scenarios)
{
    public const int MaximumScenarios = 20;
    public const int MaximumBytes = 64 * 1024 * 1024;

    // Historical results are data only: never bind their IDs or geometry to the active document.
    public static SunHoursArchive Parse(string json, IEnumerable<string> existingNames)
    {
        if (Encoding.UTF8.GetByteCount(json) > MaximumBytes) throw Invalid("檔案超過 64 MiB，請縮小方案資料。");
        try
        {
            using var document = JsonDocument.Parse(json);
            var root = document.RootElement;
            RejectDuplicateProperties(root);
            Required(root, "SchemaVersion", "BaselineIndex", "CandidateIndex", "Metric", "Scenarios");
            if (root.GetProperty("SchemaVersion").GetString() != "1.0" || root.GetProperty("Metric").GetString() != "Arithmetic point mean, not area weighted")
                throw Invalid("僅支援本平台 1.0 日照方案比較 JSON（格點算術平均）。");
            var entries = root.GetProperty("Scenarios");
            var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            int existingCount = 0;
            foreach (var name in existingNames) { names.Add(name); existingCount++; }
            if (entries.ValueKind != JsonValueKind.Array || entries.GetArrayLength() == 0 || entries.GetArrayLength() + existingCount > MaximumScenarios)
                throw Invalid("匯入後須為 1–20 個方案；請使用較小的方案檔或新的工作階段。");
            var scenarios = new List<SunHoursScenario>();
            foreach (var entry in entries.EnumerateArray())
            {
                Required(entry, "Name", "Result");
                var name = entry.GetProperty("Name").GetString();
                if (name is null || name.Length is < 1 or > 80 || name != name.Trim() || name.Any(char.IsControl) || !names.Add(name))
                    throw Invalid("方案名稱須為 1–80 字元、不含首尾空白或控制字元，且不得與既有方案重複。");
                var raw = entry.GetProperty("Result");
                Required(raw, "SchemaVersion", "InputParameters", "ResultMesh", "Values", "Points", "SunlightVectors", "SunUpHoursOfYear", "Units", "Statistics", "Metadata", "Warnings", "ExecutionTimeSeconds", "Timestamp");
                Required(raw.GetProperty("InputParameters"), "SchemaVersion", "GeometryIds", "ContextIds", "SunSource", "TimeStepsPerHour", "GridMetres", "OffsetMetres", "GeometryBlocks", "CpuCount", "AcceptWarnings");
                Required(raw.GetProperty("InputParameters").GetProperty("SunSource"), "SchemaVersion", "Location", "HoursOfYear", "NorthDegrees", "SolarTime", "Center", "RadiusMetres", "Daily", "Projection");
                var location = raw.GetProperty("InputParameters").GetProperty("SunSource").GetProperty("Location");
                Required(location, "SchemaVersion", "Name", "Latitude", "Longitude", "ElevationMetres");
                if (!location.TryGetProperty("TimeZone", out _)) throw Invalid("缺少地點時區欄位。");
                Required(raw.GetProperty("Statistics"), "Count", "Minimum", "Maximum", "Mean");
                var result = raw.Deserialize<SunHoursResult>() ?? throw Invalid("缺少完成結果。");
                Validate(result);
                scenarios.Add(new(name, result, true));
            }
            int baseline = root.GetProperty("BaselineIndex").GetInt32(), candidate = root.GetProperty("CandidateIndex").GetInt32();
            if (baseline < 0 || candidate < 0 || baseline >= scenarios.Count || candidate >= scenarios.Count)
                throw Invalid("基準／比較方案索引不在檔案範圍內。");
            return new(baseline, candidate, scenarios.ToArray());
        }
        catch (Exception e) when (e is JsonException or InvalidOperationException or FormatException or OverflowException or ArgumentException)
        {
            if (e is ArgumentException && e.Message.StartsWith("SUNH-IMPORT-001:")) throw;
            throw Invalid("JSON 格式或日照資料無效，請選取本平台匯出的方案比較檔。", e);
        }
    }

    private static void Validate(SunHoursResult r)
    {
        var request = r.InputParameters;
        var sun = request.SunSource;
        if (r.SchemaVersion != "1.0" || request.SchemaVersion != "1.0" || sun?.SchemaVersion != "1.0" || sun.Location?.SchemaVersion != "1.0" || r.Units != "h")
            throw Invalid("結果契約、太陽來源或單位不符（須為 1.0、h）。");
        var location = sun.Location;
        if (string.IsNullOrWhiteSpace(location.Name) || !double.IsFinite(location.Latitude) || Math.Abs(location.Latitude) > 90 || !double.IsFinite(location.Longitude) || Math.Abs(location.Longitude) > 180 || (location.TimeZone is { } zone && (!double.IsFinite(zone) || Math.Abs(zone) > 14)) || !double.IsFinite(location.ElevationMetres) || !double.IsFinite(sun.NorthDegrees) || Math.Abs(sun.NorthDegrees) > 360 || !Vector(sun.Center) || !double.IsFinite(sun.RadiusMetres) || sun.RadiusMetres is <= 0 or > 1000000 || sun.Projection is not ("3D" or "Orthographic" or "Stereographic" or "Equidistant" or "Equisolid"))
            throw Invalid("太陽來源的地點、時間制或幾何參數無效。");
        SunHoursSampling.Check(sun.HoursOfYear, request.TimeStepsPerHour);
        if (request.GeometryIds is null || request.ContextIds is null || request.GeometryIds.Length == 0 || request.GeometryIds.Concat(request.ContextIds).Any(id => id == Guid.Empty) || request.GeometryIds.Concat(request.ContextIds).Distinct().Count() != request.GeometryIds.Length + request.ContextIds.Length || !double.IsFinite(request.GridMetres) || request.GridMetres is < .01 or > 1000000 || !double.IsFinite(request.OffsetMetres) || request.OffsetMetres is < 0 or > 1000000 || request.CpuCount is < 1 or > 128)
            throw Invalid("結果輸入的模型識別碼或模擬參數無效。");
        if (r.Values is null || r.Values.Length == 0 || r.Points is null || r.Points.Length != r.Values.Length || r.Points.Any(p => !Vector(p)) || r.SunlightVectors is null || r.SunlightVectors.Length == 0 || r.SunlightVectors.Any(v => !Vector(v) || !Close(v.Sum(x => x * x), 1)) || r.SunUpHoursOfYear is null || r.SunUpHoursOfYear.Length != r.SunlightVectors.Length || r.SunUpHoursOfYear.Distinct().Count() != r.SunUpHoursOfYear.Length || r.SunUpHoursOfYear.Except(sun.HoursOfYear).Any())
            throw Invalid("數值、格點或太陽向量資料不完整／不對齊。");
        double maximum = r.SunlightVectors.Length / (double)request.TimeStepsPerHour;
        if (r.Values.Any(v => !double.IsFinite(v) || v < 0 || v > maximum + 1e-8 || !Close(v * request.TimeStepsPerHour, Math.Round(v * request.TimeStepsPerHour))) || r.Statistics is null || r.Statistics.Count != r.Values.Length || !Close(r.Statistics.Minimum, r.Values.Min()) || !Close(r.Statistics.Maximum, r.Values.Max()) || !Close(r.Statistics.Mean, r.Values.Average()))
            throw Invalid("日照時數超出取樣權重，或統計與完整數值不一致。");
        if (r.ResultMesh is null || r.ResultMesh.Length == 0 || r.ResultMesh.Any(m => m is null || m.Vertices is null || m.Faces is null || m.VertexColorsArgb is null || m.Vertices.Length == 0 || m.VertexColorsArgb.Length != m.Vertices.Length || m.Vertices.Any(v => !Vector(v)) || m.Faces.Any(f => f is null || f.Length is not (3 or 4) || f.Distinct().Count() != f.Length || f.Any(i => i < 0 || i >= m.Vertices.Length))) || r.ResultMesh.Sum(m => (long)m.Faces.Length) != r.Values.Length)
            throw Invalid("原生網格、面索引、色彩或格點數不一致。");
        string[] hashes = ["SunSourceSha256", "UserObjectSha256", "SunPathUserObjectSha256", "GeometrySha256"];
        string[] metadata = ["Location", "ModelUnits", "MetresPerModelUnit", "ComponentVersion", "Solver", "WorkflowVersion", "TimeConvention", "Scope"];
        if (r.Metadata is null || hashes.Any(key => !r.Metadata.TryGetValue(key, out var value) || value is null || value.Length != 64 || !value.All(Uri.IsHexDigit)) || metadata.Any(key => !r.Metadata.TryGetValue(key, out var value) || string.IsNullOrWhiteSpace(value)) || !double.TryParse(r.Metadata["MetresPerModelUnit"], NumberStyles.Float, CultureInfo.InvariantCulture, out var scale) || !double.IsFinite(scale) || scale <= 0 || r.Metadata["WorkflowVersion"] != "1.0" || r.Metadata["Solver"] != "Original Ladybug Direct Sun Hours / Rhino CAD ray intersections" || r.Warnings is null || r.Warnings.Any(w => w is null || w.Severity is null || w.Code is null || w.Message is null) || !double.IsFinite(r.ExecutionTimeSeconds) || r.ExecutionTimeSeconds < 0 || r.Timestamp == default)
            throw Invalid("結果缺少可追溯的原生求解來源、時間或單位資訊。");
    }

    public static bool SameSunConditions(SunHoursResult a, SunHoursResult b)
    {
        var sa = a.InputParameters.SunSource!; var sb = b.InputParameters.SunSource!;
        return a.Units == b.Units && a.Metadata["Solver"] == b.Metadata["Solver"] && a.Metadata["WorkflowVersion"] == b.Metadata["WorkflowVersion"] && a.InputParameters.TimeStepsPerHour == b.InputParameters.TimeStepsPerHour && sa.NorthDegrees == sb.NorthDegrees && sa.SolarTime == sb.SolarTime && sa.Location.Latitude == sb.Location.Latitude && sa.Location.Longitude == sb.Location.Longitude && sa.Location.TimeZone == sb.Location.TimeZone && sa.Location.ElevationMetres == sb.Location.ElevationMetres && sa.HoursOfYear.SequenceEqual(sb.HoursOfYear) && a.SunUpHoursOfYear.SequenceEqual(b.SunUpHoursOfYear) && a.SunlightVectors.Length == b.SunlightVectors.Length && a.SunlightVectors.Zip(b.SunlightVectors).All(pair => pair.First.SequenceEqual(pair.Second));
    }
    private static bool Vector(double[]? v) => v is { Length: 3 } && v.All(double.IsFinite);
    private static bool Close(double a, double b) => double.IsFinite(a) && double.IsFinite(b) && Math.Abs(a - b) <= 1e-8 * Math.Max(1, Math.Abs(b));
    private static void Required(JsonElement node, params string[] properties) { if (node.ValueKind != JsonValueKind.Object || properties.Any(p => !node.TryGetProperty(p, out var value) || value.ValueKind == JsonValueKind.Null)) throw Invalid("缺少必要的 JSON 欄位。"); }
    private static void RejectDuplicateProperties(JsonElement node)
    {
        if (node.ValueKind == JsonValueKind.Object) { var names = new HashSet<string>(StringComparer.Ordinal); foreach (var p in node.EnumerateObject()) { if (!names.Add(p.Name)) throw Invalid("JSON 含有重複欄位。"); RejectDuplicateProperties(p.Value); } }
        else if (node.ValueKind == JsonValueKind.Array) foreach (var item in node.EnumerateArray()) RejectDuplicateProperties(item);
    }
    private static ArgumentException Invalid(string message, Exception? inner = null) => new("SUNH-IMPORT-001: " + message, inner);
}
