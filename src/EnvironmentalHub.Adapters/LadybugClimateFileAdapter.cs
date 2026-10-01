using System.Collections;
using System.Security.Cryptography;
using System.Text.Json;
using EnvironmentalHub.Core;
using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Parameters;
using Grasshopper.Kernel.Types;
using Rhino;

namespace EnvironmentalHub.Adapters;

public sealed class LadybugClimateFileAdapter(string userObjectDirectory)
{
    public static string RunJson(string json, string folder) => JsonSerializer.Serialize(
        new LadybugClimateFileAdapter(folder).Execute(JsonSerializer.Deserialize<ClimateFileRequest>(json)!));
    private static string Hash(string path) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)));
    private static object? Normalize(object? value)
    {
        if (value is null || value is string || value is bool || value is int || value is long) return value;
        if (value is double number && double.IsFinite(number)) return number;
        if (value is IDictionary dict)
        {
            var result = new Dictionary<string, object?>();
            foreach (DictionaryEntry item in dict)
            {
                if (item.Key is not string key) throw new InvalidOperationException("CLIMATE-RESULT-001: Nonstring native dictionary key.");
                result[key] = Normalize(item.Value);
            }
            return result;
        }
        if (value is IEnumerable list) return list.Cast<object?>().Select(Normalize).ToArray();
        throw new InvalidOperationException("CLIMATE-RESULT-001: Unsupported native value type " + value.GetType().FullName);
    }
    public ClimateFileResult Execute(ClimateFileRequest request)
    {
        if (RhinoApp.InvokeRequired) throw new InvalidOperationException("CLIMATE-THREAD-001: Execute on Rhino UI thread.");
        if (request is null || request.SchemaVersion != "1.0" || request.Format is not ("STAT" or "DDY"))
            throw new InvalidOperationException("CLIMATE-CONTRACT-001: STAT or DDY schema 1.0 required.");
        if (!File.Exists(request.FilePath) || !string.Equals(Path.GetExtension(request.FilePath), "." + request.Format, StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("CLIMATE-FILE-001: Select an existing file with the matching STAT/DDY extension.");
        if (!GH_Document.EnableSolutions) throw new InvalidOperationException("CLIMATE-GH-001: Grasshopper solver disabled.");
        var path = Path.Combine(userObjectDirectory, "LB Import " + request.Format + ".ghuser");
        if (!File.Exists(path)) throw new InvalidOperationException("CLIMATE-PLUGIN-001: Original import component missing.");
        var fileHash = Hash(request.FilePath); var componentHash = Hash(path);
        using var definition = new GH_Document(); definition.Enabled = false;
        try
        {
            var component = (IGH_Component)new GH_UserObject(path).InstantiateObject();
            component.CreateAttributes(); definition.AddObject(component, false);
            var input = new Param_GenericObject(); input.CreateAttributes(); input.SetPersistentData(new GH_ObjectWrapper(request.FilePath));
            definition.AddObject(input, false); component.Params.Input.Single(p => p.Name == "_" + request.Format.ToLowerInvariant() + "_file").AddSource(input);
            Instances.DocumentServer.AddDocument(definition); definition.Enabled = true; definition.NewSolution(false);
            var errors = component.RuntimeMessages(GH_RuntimeMessageLevel.Error);
            if (errors.Count > 0) throw new InvalidOperationException("CLIMATE-SOLVER-001: " + string.Join("\n", errors));
            List<ClimateObject> outputs = [];
            foreach (var output in component.Params.Output)
            {
                var index = 0;
                foreach (var goo in output.VolatileData.AllData(true))
                {
                    object? value = goo.ScriptVariable();
                    JsonElement data;
                    if (value is null || value is string || value is bool || value is int || value is double)
                        data = JsonSerializer.SerializeToElement(Normalize(value));
                    else { dynamic native = value; data = JsonSerializer.SerializeToElement(Normalize((object)native.to_dict())); }
                    var kind = data.ValueKind == JsonValueKind.Object ? data.GetProperty("type").GetString()! : data.ValueKind.ToString();
                    string? idf = null;
                    if (kind == "DesignDay") { dynamic native = value!; idf = (string)native.to_idf(); }
                    outputs.Add(new(output.Name, index++, kind, data, idf));
                }
                // Empty native outputs are explicit; no fabricated design day or period.
                if (index == 0) outputs.Add(new(output.Name, -1, "Unavailable", JsonSerializer.SerializeToElement<object?>(null)));
            }
            if (!outputs.Any(o => o.Output == "location" && o.Kind == "Location"))
                throw new InvalidOperationException("CLIMATE-RESULT-001: Native location missing.");
            if (fileHash != Hash(request.FilePath) || componentHash != Hash(path))
                throw new InvalidOperationException("CLIMATE-INPUT-001: Source changed during import.");
            var warnings = component.RuntimeMessages(GH_RuntimeMessageLevel.Warning).Select(m => new Diagnostic("WARNING", "CLIMATE-SOLVER-002", m)).ToList();
            if (outputs.Any(o => o.Kind is "Unavailable" or "Null")) warnings.Add(new("WARNING", "CLIMATE-DATA-001", "Some original outputs are unavailable; no replacement values generated."));
            return new("1.0", request, outputs.ToArray(), new() { ["FileSha256"] = fileHash, ["UserObjectSha256"] = componentHash,
                ["Source"] = path, ["ComponentVersion"] = component.Message, ["DataConvention"] = "Original Ladybug to_dict schema; collection units and analysis_period retained; design-day units follow Ladybug SI conventions" }, warnings.ToArray());
        }
        finally { Instances.DocumentServer.RemoveDocument(definition); }
    }
}
