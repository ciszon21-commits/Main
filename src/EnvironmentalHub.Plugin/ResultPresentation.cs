using EnvironmentalHub.Core;
using Eto.Drawing;
using Eto.Forms;

namespace EnvironmentalHub.Plugin;

// Presentation only: never recolor meshes, interpolate a solver scale or modify results.
internal static class ResultPresentation
{
    internal static Control Legend(AnalysisResult result)
    {
        var layout = new DynamicLayout { Spacing = new Size(8, 6) };
        layout.AddRow(HubUi.Hint($"結果範圍 · {result.Units}\n{result.Statistics.Minimum:F3} – {result.Statistics.Maximum:F3}"));
        var pairs = new List<(double Value, int Color)>();
        int index = 0;
        foreach (var mesh in result.ResultMesh)
        foreach (var face in mesh.Faces)
        {
            if (index >= result.Values.Length || face.Length == 0 || face.Any(v => v < 0 || v >= mesh.VertexColorsArgb.Length))
                return HubUi.Hint("無法取得色樣 · 請檢視原生視埠網格。");
            var color = mesh.VertexColorsArgb[face[0]];
            if (face.Any(v => mesh.VertexColorsArgb[v] != color))
                return HubUi.Hint("網格使用插值色彩 · 請檢視原生視埠圖例；此處不推定面色階。");
            pairs.Add((result.Values[index++], color));
        }
        if (index != result.Values.Length || pairs.Count == 0) return HubUi.Hint("無法取得色樣");
        var sorted = pairs.Distinct().OrderBy(p => p.Value).ToArray();
        var samples = Enumerable.Range(0, Math.Min(5, sorted.Length))
            .Select(i => sorted[(int)Math.Round(i * (sorted.Length - 1.0) / Math.Max(1, Math.Min(5, sorted.Length) - 1))]).Distinct();
        var rows = new DynamicLayout { Spacing = new Size(8, 6) };
        foreach (var pair in samples)
        {
            var rgb = System.Drawing.Color.FromArgb(pair.Color);
            rows.AddRow(new Panel { Size = new Size(24, 14), BackgroundColor = Color.FromArgb(rgb.R, rgb.G, rgb.B) },
                new Label { Text = $"{pair.Value:F3} {result.Units}" });
        }
        layout.AddRow(rows);
        layout.AddRow(HubUi.Hint("色樣取自實際網格。各次分析保留原始色階；不同方案請比較數值。"));
        return layout;
    }

    internal static string Assessment(AnalysisResult result, double minimum, double maximum)
    {
        int passed = result.Values.Count(v => v >= minimum && v <= maximum);
        return $"專案目標 {minimum:g} – {maximum:g} {result.Units}\n符合 {passed:N0} · 未符合 {result.Values.Length - passed:N0} 格網格\n{100.0 * passed / result.Values.Length:F1}% 位於目標區間 · 包含上下限";
    }

    internal static string Compare(string aName, AnalysisResult a, string bName, AnalysisResult b)
    {
        var text = $"{aName} → {bName}\n平均值 {a.Statistics.Mean:F3} {a.Units} → {b.Statistics.Mean:F3} {b.Units}\n網格數 {a.Statistics.Count:N0} → {b.Statistics.Count:N0}";
        if (a.Units != b.Units || a.AnalysisType != b.AnalysisType ||
            !a.Metadata.TryGetValue("WeatherSha256", out var weatherA) || !b.Metadata.TryGetValue("WeatherSha256", out var weatherB) || weatherA != weatherB ||
            !a.InputParameters.HoursOfYear.Order().SequenceEqual(b.InputParameters.HoursOfYear.Order()))
            return text + "\n無法直接比較 · 氣象、分析類型、單位或期間不同，因此不顯示差值。";
        var delta = b.Statistics.Mean - a.Statistics.Mean;
        text += $"\nΔ 平均值 {delta:+0.000;-0.000;0.000} {a.Units}";
        if (a.Statistics.Mean != 0) text += $" ({100 * delta / a.Statistics.Mean:+0.0;-0.0;0.0}%)";
        var changes = new List<string>();
        if (a.InputParameters.GridMetres != b.InputParameters.GridMetres) changes.Add("網格間距");
        if (a.InputParameters.NorthDegrees != b.InputParameters.NorthDegrees) changes.Add("北向旋轉");
        if (a.InputParameters.Settings != b.InputParameters.Settings) changes.Add("進階設定");
        if (a.SolverVersion != b.SolverVersion || a.WorkflowVersion != b.WorkflowVersion) changes.Add("求解器／流程版本");
        if (a.Metadata.GetValueOrDefault("GeometrySha256") != b.Metadata.GetValueOrDefault("GeometrySha256")) changes.Add("模型／遮蔭識別摘要（請確認模型狀態）");
        return text + (changes.Count == 0 ? "\n已記錄條件一致" : "\n不同的條件：" + string.Join(", ", changes)) +
            "\n數值為網格算術平均，未依面積加權；差異不代表性能改善。";
    }
}
