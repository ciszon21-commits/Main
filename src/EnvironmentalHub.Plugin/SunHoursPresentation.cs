using EnvironmentalHub.Core;
using Eto.Drawing;
using Eto.Forms;

namespace EnvironmentalHub.Plugin;

internal static class SunHoursPresentation
{
    internal static Control Legend(SunHoursResult result)
    {
        var pairs = new List<(double Value, int Color)>(); int i = 0;
        foreach (var m in result.ResultMesh)
        foreach (var f in m.Faces)
        {
            if (i >= result.Values.Length || f.Length == 0 || f.Any(v => v < 0 || v >= m.VertexColorsArgb.Length) || f.Any(v => m.VertexColorsArgb[v] != m.VertexColorsArgb[f[0]]))
                return HubUi.Hint("無法對應原生面色樣 · 請檢視視埠網格，不推定插值色階。");
            pairs.Add((result.Values[i++], m.VertexColorsArgb[f[0]]));
        }
        if (i != result.Values.Length) return HubUi.Hint("無法對應原生面色樣");
        var sorted = pairs.Distinct().OrderBy(p => p.Value).ToArray(); var count = Math.Min(5, sorted.Length);
        var layout = new DynamicLayout { Spacing = new Size(8, 6) };
        layout.AddRow(HubUi.Hint($"結果範圍 · h\n{result.Statistics.Minimum:F3} – {result.Statistics.Maximum:F3}"));
        var rows = new DynamicLayout { Spacing = new Size(8, 6) };
        for (int n = 0; n < count; n++)
        {
            var p = sorted[(int)Math.Round(n * (sorted.Length - 1.0) / Math.Max(1, count - 1))]; var color = System.Drawing.Color.FromArgb(p.Color);
            rows.AddRow(new Panel { Size = new Size(24, 14), BackgroundColor = Color.FromArgb(color.R, color.G, color.B) }, new Label { Text = $"{p.Value:F3} h" });
        }
        layout.AddRow(rows);
        layout.AddRow(HubUi.Hint("色樣取自實際原生網格；各方案保留自己的色階，請比較數值。"));
        return layout;
    }
    internal static string Compare(string an, SunHoursResult a, string bn, SunHoursResult b)
    {
        var text = $"{an} → {bn}\n平均值 {a.Statistics.Mean:F3} h → {b.Statistics.Mean:F3} h\n取樣格數 {a.Statistics.Count:N0} → {b.Statistics.Count:N0}";
        if (a.Metadata["SunSourceSha256"] != b.Metadata["SunSourceSha256"] || a.Metadata["UserObjectSha256"] != b.Metadata["UserObjectSha256"] || a.Metadata["SunPathUserObjectSha256"] != b.Metadata["SunPathUserObjectSha256"])
            return text + "\n無法直接比較 · 太陽來源、期間、取樣頻率或原生版本不同，不顯示差值。";
        text += $"\nΔ 平均值 {b.Statistics.Mean - a.Statistics.Mean:+0.000;-0.000;0.000} h";
        var changes = new List<string>();
        if (a.Metadata["GeometrySha256"] != b.Metadata["GeometrySha256"]) changes.Add("模型／遮蔭識別摘要（請確認模型狀態）");
        if (a.InputParameters.GridMetres != b.InputParameters.GridMetres) changes.Add("網格間距");
        if (a.InputParameters.OffsetMetres != b.InputParameters.OffsetMetres || a.InputParameters.GeometryBlocks != b.InputParameters.GeometryBlocks) changes.Add("偏移／自遮蔭");
        return text + (changes.Count == 0 ? "\n已記錄條件一致" : "\n不同條件：" + string.Join("、", changes)) + "\n數值為格點算術平均，未按面積加權；差異不代表性能改善。";
    }
}
