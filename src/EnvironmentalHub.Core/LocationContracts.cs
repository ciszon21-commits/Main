using System.Globalization;

namespace EnvironmentalHub.Core;

public static class ClimateDisplay
{
    public static string UtcOffset(double hours) => "UTC" + hours.ToString("+0.##;-0.##;0", CultureInfo.InvariantCulture);
}
public sealed record LocationRequest
{
    public string SchemaVersion { get; init; } = "1.0";
    public string Name { get; init; } = "-";
    public double Latitude { get; init; }
    public double Longitude { get; init; }
    public double? TimeZone { get; init; }
    public double ElevationMetres { get; init; }
}
public sealed record LocationResult(string SchemaVersion, WeatherLocation Location, LocationRequest InputParameters,
    Dictionary<string, string> Metadata, Diagnostic[] Warnings);
