namespace EnvironmentalHub.Core;

public sealed record WeatherRequest
{
    public string SchemaVersion { get; init; } = "1.0";
    public string WeatherFile { get; init; } = "";
    // Zero-based Ladybug HOY: 0 = Jan 1 00:00. Empty = annual.
    public int[] HoursOfYear { get; init; } = [];
}
public sealed record WeatherLocation(string City, string Country, double Latitude, double Longitude,
    double TimeZone, double Elevation, string StationId, string Source);
public sealed record WeatherTime(int Month, int Day, int Hour, int Minute, double HourOfYear);
public sealed record WeatherSeries(string Output, int CollectionIndex, string DataType, string Units,
    string Frequency, Dictionary<string, string> Metadata, double[] Values, bool[] Missing, WeatherTime[] Times, ResultStatistics? Statistics);
public sealed record WeatherResult(string SchemaVersion, WeatherLocation Location, WeatherSeries[] Series,
    WeatherRequest InputParameters, Dictionary<string, string> Metadata, Diagnostic[] Warnings,
    double ExecutionTimeSeconds, DateTimeOffset Timestamp);
public interface IWeatherAdapter
{
    WeatherResult Execute(WeatherRequest request);
}
