using System.Globalization;
using System.Net;
using System.Text;
using EnvironmentalHub.Core;

namespace EnvironmentalHub.Plugin;

// Pure presentation: no Rhino calls, geometry serialization, JavaScript or solver state.
internal static class SunHoursResultPage
{
    internal sealed record Bin(double Lower, double Upper, int Count, bool Last);
    internal static Bin[] Distribution(SunHoursResult result)
    {
        var values = result.Values;
        if (result.Units != "h" || values.Length == 0 || values.Length != result.Statistics.Count || values.Any(v => !double.IsFinite(v) || v < 0))
            throw new ArgumentException("結果單位或格點資料無法呈現。");
        var min = values.Min(); var max = values.Max();
        if (min == max) return [new(min, max, values.Length, true)];
        const int count = 8;
        var totals = new int[count];
        foreach (var value in values) totals[Math.Min(count - 1, (int)((value - min) / (max - min) * count))]++;
        return Enumerable.Range(0, count).Select(i => new Bin(min + (max - min) * i / count, min + (max - min) * (i + 1) / count, totals[i], i == count - 1)).ToArray();
    }
    internal static (double Value, int Color)[]? NativeSamples(SunHoursResult result)
    {
        var pairs = new List<(double Value, int Color)>(); int i = 0;
        foreach (var mesh in result.ResultMesh)
        foreach (var face in mesh.Faces)
        {
            if (i >= result.Values.Length || face.Length == 0 || face.Any(v => v < 0 || v >= mesh.VertexColorsArgb.Length) || face.Any(v => mesh.VertexColorsArgb[v] != mesh.VertexColorsArgb[face[0]])) return null;
            pairs.Add((result.Values[i++], mesh.VertexColorsArgb[face[0]]));
        }
        if (i != result.Values.Length) return null;
        var sorted = pairs.Distinct().OrderBy(p => p.Value).ToArray(); int count = Math.Min(5, sorted.Length);
        return Enumerable.Range(0, count).Select(n => sorted[(int)Math.Round(n * (sorted.Length - 1.0) / Math.Max(1, count - 1))]).ToArray();
    }
    internal static string DataUri(string html) => "data:text/html;charset=utf-8;base64," + Convert.ToBase64String(Encoding.UTF8.GetBytes(html));
    internal static bool AllowedNavigation(Uri? uri, string? currentDataUri) => uri is not null && (uri.AbsoluteUri == "about:blank" || (currentDataUri is not null && uri.AbsoluteUri == currentDataUri));
    internal static string Render(SunHoursResult result, string state, string comparison, string assessment, string diagnostics, bool dark) =>
        SunHoursReportLayout.Render(result, state, comparison, assessment, diagnostics, dark);
}