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
        layout.AddRow(HubUi.Hint($"RESULT RANGE  ·  {result.Units}\n{result.Statistics.Minimum:F3} – {result.Statistics.Maximum:F3}"));
        var pairs = new List<(double Value, int Color)>();
        int index = 0;
        foreach (var mesh in result.ResultMesh)
        foreach (var face in mesh.Faces)
        {
            if (index >= result.Values.Length || face.Length == 0 || face.Any(v => v < 0 || v >= mesh.VertexColorsArgb.Length))
                return HubUi.Hint("Color samples unavailable · Inspect the native viewport mesh.");
            var color = mesh.VertexColorsArgb[face[0]];
            if (face.Any(v => mesh.VertexColorsArgb[v] != color))
                return HubUi.Hint("Interpolated mesh colors · Inspect the native viewport legend; no face-color scale inferred.");
            pairs.Add((result.Values[index++], color));
        }
        if (index != result.Values.Length || pairs.Count == 0) return HubUi.Hint("Color samples unavailable");
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
        layout.AddRow(HubUi.Hint("Sampled cell colors from the actual mesh. Each run uses its original scale; compare numbers across scenarios."));
        return layout;
    }

    internal static string Assessment(AnalysisResult result, double minimum, double maximum)
    {
        int passed = result.Values.Count(v => v >= minimum && v <= maximum);
        return $"Project target {minimum:g} – {maximum:g} {result.Units}\nPASS {passed:N0} · FAIL {result.Values.Length - passed:N0} cells\n{100.0 * passed / result.Values.Length:F1}% within range · Inclusive bounds";
    }

    internal static string Compare(string aName, AnalysisResult a, string bName, AnalysisResult b)
    {
        var text = $"{aName} → {bName}\nAverage {a.Statistics.Mean:F3} {a.Units} → {b.Statistics.Mean:F3} {b.Units}\nCells {a.Statistics.Count:N0} → {b.Statistics.Count:N0}";
        if (a.Units != b.Units || a.AnalysisType != b.AnalysisType ||
            !a.Metadata.TryGetValue("WeatherSha256", out var weatherA) || !b.Metadata.TryGetValue("WeatherSha256", out var weatherB) || weatherA != weatherB ||
            !a.InputParameters.HoursOfYear.Order().SequenceEqual(b.InputParameters.HoursOfYear.Order()))
            return text + "\nNot comparable · Weather, analysis type, units or time period differ. No delta reported.";
        var delta = b.Statistics.Mean - a.Statistics.Mean;
        text += $"\nΔ average {delta:+0.000;-0.000;0.000} {a.Units}";
        if (a.Statistics.Mean != 0) text += $" ({100 * delta / a.Statistics.Mean:+0.0;-0.0;0.0}%)";
        var changes = new List<string>();
        if (a.InputParameters.GridMetres != b.InputParameters.GridMetres) changes.Add("grid spacing");
        if (a.InputParameters.NorthDegrees != b.InputParameters.NorthDegrees) changes.Add("north rotation");
        if (a.InputParameters.Settings != b.InputParameters.Settings) changes.Add("advanced settings");
        if (a.SolverVersion != b.SolverVersion || a.WorkflowVersion != b.WorkflowVersion) changes.Add("solver / workflow version");
        if (a.Metadata.GetValueOrDefault("GeometrySha256") != b.Metadata.GetValueOrDefault("GeometrySha256")) changes.Add("geometry / context fingerprint (review model state)");
        return text + (changes.Count == 0 ? "\nMatching recorded conditions" : "\nDifferent records: " + string.Join(", ", changes)) +
            "\nArithmetic cell mean; not area-weighted. Changes do not imply improved performance.";
    }
}
