namespace EnvironmentalHub.Core;

public sealed record SunPathRequest
{
    public string SchemaVersion { get; init; } = "1.0";
    public LocationRequest Location { get; init; } = new() { Name = "臺北", Latitude = 25.033, Longitude = 121.5654, TimeZone = 8 };
    public double[] HoursOfYear { get; init; } = [4116];
    public double NorthDegrees { get; init; }
    public bool SolarTime { get; init; }
    public double[] Center { get; init; } = [0, 0, 0];
    public double RadiusMetres { get; init; } = 20;
    public bool Daily { get; init; }
    public string Projection { get; init; } = "3D";
}
public sealed record SunPosition(double HourOfYear, double AltitudeDegrees, double AzimuthDegrees,
    double[] SunPoint, double[] SunlightVector);
public sealed record SunPathCurve(string Output, string GeometryJson);
public sealed record SunPathText(string Output, string Text, double[] Origin, double[] XAxis, double[] YAxis,
    double Height, string Font, int HorizontalAlignment, int VerticalAlignment);
public sealed record SunPathResult(string SchemaVersion, SunPathRequest InputParameters, WeatherLocation Location,
    SunPosition[] Positions, SunPathCurve[] Curves, SunPathText[] Texts, string ModelUnits,
    double MetresPerModelUnit, Dictionary<string, string> Metadata, Diagnostic[] Warnings);
