namespace EnvironmentalHub.Core;

public sealed record RadiationSettings
{
    public int CpuCount { get; init; } = 1;
    public bool HighDensity { get; init; }
    public double GroundReflectance { get; init; } = 0.2;
    public double OffsetMetres { get; init; } = 0.1;
}

public sealed record RadiationAnalysisRequest
{
    public string SchemaVersion { get; init; } = "1.0";
    public Guid[] GeometryIds { get; init; } = [];
    public Guid[] ContextIds { get; init; } = [];
    public string WeatherFile { get; init; } = "";
    public string OutputDirectory { get; init; } = "";
    public double NorthDegrees { get; init; }
    public double GridMetres { get; init; } = 1;
    public int[] HoursOfYear { get; init; } = [];
    public string Quality { get; init; } = "Standard";
    public bool AcceptWarnings { get; init; }
    public RadiationSettings Settings { get; init; } = new();
}

public sealed record Diagnostic(string Severity, string Code, string Message);
public sealed record GeometryFact(Guid Id, bool Exists, bool Valid, bool Supported, double SizeMetres);
public sealed record EnvironmentFacts(double MetresPerUnit, bool UnitsDefined, GeometryFact[] Geometry,
    GeometryFact[] Context, bool ComponentsAvailable, bool SolverAvailable);
public sealed record PreflightReport(Diagnostic[] Diagnostics, string? Location)
{
    public bool CanRun => !Diagnostics.Any(d => d.Severity == "ERROR");
    public bool HasWarnings => Diagnostics.Any(d => d.Severity == "WARNING");
}
public sealed record MeshArtifact(double[][] Vertices, int[][] Faces, int[] VertexColorsArgb);
public sealed record LegendArtifact(string Units, double Minimum, double Maximum, int[] ColorsArgb);
public sealed record ResultStatistics(int Count, double Minimum, double Maximum, double Mean);
public sealed record AnalysisResult(string AnalysisType, Guid[] Geometry, MeshArtifact[] ResultMesh,
    double[] Values, double[][] Points, double[][] Vectors, string Units, LegendArtifact Legend,
    ResultStatistics Statistics, string Solver, string SolverVersion, string WorkflowVersion,
    RadiationAnalysisRequest InputParameters, Dictionary<string, string> Metadata,
    Diagnostic[] Warnings, Diagnostic[] Errors, double ExecutionTimeSeconds, DateTimeOffset Timestamp);

public interface IRadiationAdapter
{
    PreflightReport Preflight(RadiationAnalysisRequest request);
    AnalysisResult Execute(RadiationAnalysisRequest request);
}
