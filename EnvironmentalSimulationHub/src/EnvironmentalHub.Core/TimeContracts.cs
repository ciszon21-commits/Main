using System.Text.Json;
namespace EnvironmentalHub.Core;

public sealed record PeriodRequest
{
    public string SchemaVersion { get; init; } = "1.0";
    public int StartMonth { get; init; } = 1;
    public int StartDay { get; init; } = 1;
    public int StartHour { get; init; }
    public int EndMonth { get; init; } = 12;
    public int EndDay { get; init; } = 31;
    public int EndHour { get; init; } = 23;
    public int TimeStep { get; init; } = 1;
}
public sealed record PeriodResult(PeriodRequest InputParameters, JsonElement Period, double[] HoursOfYear,
    WeatherTime[] Times, Dictionary<string,string> Metadata);
public sealed record CalendarRequest
{
    public string SchemaVersion { get; init; } = "1.0";
    public string Mode { get; init; } = "Calculate";
    public int Month { get; init; } = 1;
    public int Day { get; init; } = 1;
    public int Hour { get; init; }
    public int Minute { get; init; }
    public double HourOfYear { get; init; }
}
public sealed record CalendarResult(CalendarRequest InputParameters, WeatherTime Time, int DayOfYear,
    Dictionary<string,string> Metadata);
