namespace EnvironmentalHub.Core;

public sealed record SunHoursRequest
{
    public string SchemaVersion { get; init; } = "1.0";
    public Guid[] GeometryIds { get; init; } = [];
    public Guid[] ContextIds { get; init; } = [];
    public SunPathRequest? SunSource { get; init; }
    public int TimeStepsPerHour { get; init; } = 1;
    public double GridMetres { get; init; } = 1;
    public double OffsetMetres { get; init; } = 0.1;
    public bool GeometryBlocks { get; init; } = true;
    public int CpuCount { get; init; } = 1;
    public bool AcceptWarnings { get; init; }
}

public sealed record SunHoursResult(string SchemaVersion, SunHoursRequest InputParameters,
    MeshArtifact[] ResultMesh, double[] Values, double[][] Points, double[][] SunlightVectors,
    double[] SunUpHoursOfYear, string Units, ResultStatistics Statistics,
    Dictionary<string, string> Metadata, Diagnostic[] Warnings, double ExecutionTimeSeconds, DateTimeOffset Timestamp);

// The full requested sequence defines sampling; night-time filtering must not change its rate.
public static class SunHoursSampling
{
    public static readonly int[] SupportedRates = [1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60];
    public static int Infer(double[] hours)
    {
        ValidateHours(hours);
        if (hours.Length == 1) return 1; // A single sample needs an explicit declared rate; UI defaults to one.
        var delta = Enumerable.Range(1, hours.Length - 1).Select(i => (hours[i] - hours[i - 1] + 8760) % 8760).Min();
        var rate = (int)Math.Round(1 / delta);
        Check(hours, rate);
        return rate;
    }
    public static void Check(double[] hours, int rate)
    {
        ValidateHours(hours);
        if (!SupportedRates.Contains(rate)) throw new ArgumentException("SUNH-TIME-001: Unsupported timesteps per hour.");
        if (hours.Length == 1) return;
        var deltas = Enumerable.Range(1, hours.Length - 1).Select(i => (hours[i] - hours[i - 1] + 8760) % 8760).ToArray();
        if (Math.Abs(deltas.Min() * rate - 1) > 1e-7 || deltas.Any(d => Math.Abs(d * rate - Math.Round(d * rate)) > 1e-7))
            throw new ArgumentException("SUNH-TIME-001: Requested HOY sequence must match a regular sampling rate; unsupported sparse or irregular sampling.");
    }
    private static void ValidateHours(double[] hours)
    {
        if (hours is null || hours.Length == 0 || hours.Any(h => !double.IsFinite(h) || h < 0 || h >= 8760 || Math.Abs(h * 60 - Math.Round(h * 60)) > 1e-7) || hours.Distinct().Count() != hours.Length)
            throw new ArgumentException("SUNH-TIME-001: Unique non-leap HOYs at minute precision required.");
    }
}
