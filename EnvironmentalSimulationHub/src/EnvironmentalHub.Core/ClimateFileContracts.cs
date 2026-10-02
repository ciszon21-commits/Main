using System.Text.Json;

namespace EnvironmentalHub.Core;

public sealed record ClimateFileRequest
{
    public string SchemaVersion { get; init; } = "1.0";
    public string Format { get; init; } = "STAT";
    public string FilePath { get; init; } = "";
}
// Data is the original Ladybug to_dict schema, not a textual object representation.
public sealed record ClimateObject(string Output, int Index, string Kind, JsonElement Data, string? EnergyPlusIdf = null);
public sealed record ClimateFileResult(string SchemaVersion, ClimateFileRequest InputParameters,
    ClimateObject[] Outputs, Dictionary<string, string> Metadata, Diagnostic[] Warnings);
