using System.Globalization;

namespace EnvironmentalHub.Core;

public static class RadiationPreflight
{
    public static PreflightReport Check(RadiationAnalysisRequest request, EnvironmentFacts facts)
    {
        List<Diagnostic> diagnostics = [];
        void Error(string code, string message) => diagnostics.Add(new("ERROR", code, message));
        if (request.GeometryIds is null || request.ContextIds is null || request.HoursOfYear is null || request.Settings is null)
            return new([new("ERROR", "RAD-CONTRACT-002", "Geometry/context/hour arrays and settings cannot be null.")], null);
        if (request.SchemaVersion != "1.0") Error("RAD-CONTRACT-001", "Unsupported request schema.");
        if (request.GeometryIds.Length == 0) Error("RAD-INPUT-001", "Analysis geometry missing.");
        var allIds = request.GeometryIds.Concat(request.ContextIds).ToArray();
        if (allIds.Distinct().Count() != allIds.Length)
            Error("RAD-INPUT-004", "Geometry IDs must be unique and analysis/context must not overlap.");
        foreach (var geometry in facts.Geometry.Concat(facts.Context))
        {
            if (!geometry.Exists) Error("RAD-INPUT-002", $"Object {geometry.Id} not found.");
            else if (!geometry.Valid || !geometry.Supported)
                Error("RAD-INPUT-003", $"Object {geometry.Id} must be a valid Brep or Mesh.");
            else if (!double.IsFinite(geometry.SizeMetres) || geometry.SizeMetres <= 0)
                Error("RAD-SCALE-001", $"Object {geometry.Id} has invalid scale.");
        }
        if (!facts.UnitsDefined || !double.IsFinite(facts.MetresPerUnit) || facts.MetresPerUnit <= 0)
            Error("RAD-UNIT-001", "Document units must be defined and convertible to metres.");
        if (!double.IsFinite(request.GridMetres) || request.GridMetres <= 0)
            Error("RAD-PARAM-001", "Grid must be finite and positive.");
        if (!double.IsFinite(request.NorthDegrees) || Math.Abs(request.NorthDegrees) > 360)
            Error("RAD-PARAM-002", "North must be between -360 and 360 degrees.");
        if (request.HoursOfYear.Any(h => h < 0 || h >= 8760) || request.HoursOfYear.Distinct().Count() != request.HoursOfYear.Length)
            Error("RAD-PERIOD-001", "Hours must be unique integers in 0..8759; empty means annual.");
        if (request.Quality is not ("Quick" or "Standard" or "Detailed"))
            Error("RAD-PRESET-001", "Unknown quality label; actual settings are always recorded.");
        var settings = request.Settings;
        if (settings.CpuCount < 1 || settings.CpuCount > Environment.ProcessorCount ||
            !double.IsFinite(settings.OffsetMetres) || settings.OffsetMetres <= 0 ||
            !double.IsFinite(settings.GroundReflectance) || settings.GroundReflectance < 0 || settings.GroundReflectance > 1)
            Error("RAD-PARAM-003", "CPU, offset or ground reflectance invalid.");
        if (!facts.ComponentsAvailable) Error("RAD-PLUGIN-001", "Required installed Ladybug user objects missing.");
        if (!facts.SolverAvailable) Error("RAD-SOLVER-001", "Radiance gendaymtx or rtrace executable missing.");
        if (!Path.IsPathFullyQualified(request.OutputDirectory)) Error("RAD-OUTPUT-001", "Absolute output directory required.");
        else
        {
            // Check an existing ancestor without creating files during preflight.
            var ancestor = request.OutputDirectory;
            while (!Directory.Exists(ancestor) && Path.GetDirectoryName(ancestor) is { } parent) ancestor = parent;
            if (!Directory.Exists(ancestor) || File.Exists(request.OutputDirectory))
                Error("RAD-OUTPUT-001", "Output path is not a directory location.");
        }
        string? location = null;
        try { location = ValidateEpw(request.WeatherFile); }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or FormatException or OverflowException)
        { Error("CLIMATE-EPW-003", e.Message); }
        if (request.ContextIds.Length == 0)
            diagnostics.Add(new("WARNING", "RAD-CONTEXT-001", "No context: analysis assumes no external shading."));
        if (facts.Geometry.Any(g => g.Valid && g.SizeMetres > 0 && request.GridMetres >= g.SizeMetres))
            diagnostics.Add(new("WARNING", "RAD-GRID-001", "Grid is coarse relative to the analysis geometry."));
        return new(diagnostics.ToArray(), location);
    }

    private static string ValidateEpw(string path)
    {
        if (!File.Exists(path)) throw new FileNotFoundException("Weather file missing.");
        using var reader = new StreamReader(path);
        var header = (reader.ReadLine() ?? "").Split(',');
        if (header.Length < 10 || header[0] != "LOCATION") throw new FormatException("Invalid EPW LOCATION header.");
        for (int i = 0; i < 7; i++) if (reader.ReadLine() is null) throw new FormatException("Incomplete EPW header.");
        int count = 0;
        HashSet<string> times = [];
        while (reader.ReadLine() is { } line)
        {
            if (string.IsNullOrWhiteSpace(line)) continue;
            var cells = line.Split(',');
            if (cells.Length < 35) throw new FormatException("EPW row needs 35 fields.");
            int month = int.Parse(cells[1], CultureInfo.InvariantCulture);
            int day = int.Parse(cells[2], CultureInfo.InvariantCulture);
            int hour = int.Parse(cells[3], CultureInfo.InvariantCulture);
            if (month < 1 || month > 12 || day < 1 || day > DateTime.DaysInMonth(2001, month) || hour < 1 || hour > 24)
                throw new FormatException("Unsupported EPW date/hour; non-leap hourly weather required.");
            if (!times.Add($"{month}:{day}:{hour}")) throw new FormatException("Duplicate EPW hour.");
            foreach (var field in new[] { 14, 15 })
            {
                var radiation = double.Parse(cells[field], CultureInfo.InvariantCulture);
                if (!double.IsFinite(radiation) || radiation < 0 || radiation >= 9999)
                    throw new FormatException("Missing/invalid direct or diffuse EPW radiation.");
            }
            count++;
        }
        if (count != 8760) throw new FormatException("Expected 8760 hourly EPW records.");
        return header[1];
    }
}
