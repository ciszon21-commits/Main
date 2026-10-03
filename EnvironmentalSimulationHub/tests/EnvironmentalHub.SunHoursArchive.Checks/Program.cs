using EnvironmentalHub.Core;
using System.Text.Json;
using System.Text.Json.Nodes;

if (args.Length != 1) { Console.Error.WriteLine("Pass a real exported SunHours comparison JSON."); return 2; }
List<string> passed = [];
var original = JsonNode.Parse(File.ReadAllText(args[0]))!;
SunHoursArchive Read(JsonNode node, string[]? names = null) => SunHoursArchive.Parse(node.ToJsonString(), names ?? []);
void Check(string name, Action test) { test(); passed.Add(name); }
void Reject(string name, Action<JsonNode> mutate, string[]? names = null)
{
    Check(name, () => { var node = original.DeepClone(); mutate(node); try { Read(node, names); } catch (ArgumentException e) when (e.Message.StartsWith("SUNH-IMPORT-001:")) { return; } throw new Exception("Invalid archive accepted: " + name); });
}
JsonNode Result(JsonNode node) => node["Scenarios"]![0]!["Result"]!;
var archive = Read(original);
Check("real two-scenario archive accepted", () => { if (archive.Scenarios.Length != 2 || archive.BaselineIndex != 0 || archive.CandidateIndex != 1 || archive.Scenarios.Any(s => !s.Imported)) throw new Exception(); });
Check("full native result roundtrip", () => { for (int i = 0; i < 2; i++) if (!JsonNode.DeepEquals(original["Scenarios"]![i]!["Result"], JsonSerializer.SerializeToNode(archive.Scenarios[i].Result))) throw new Exception(); });
Check("one scenario can be restored", () => { var node = original.DeepClone(); node["Scenarios"]!.AsArray().RemoveAt(1); node["CandidateIndex"] = 0; if (Read(node).Scenarios.Length != 1) throw new Exception(); });
Check("native nullable inferred time zone supported", () => { var node = original.DeepClone(); Result(node)["InputParameters"]!["SunSource"]!["Location"]!["TimeZone"] = null; Read(node); });
Check("all native projections supported", () => { foreach (var projection in new[] { "3D", "Orthographic", "Stereographic", "Equidistant", "Equisolid" }) { var node = original.DeepClone(); Result(node)["InputParameters"]!["SunSource"]!["Projection"] = projection; Read(node); } });
Reject("unknown envelope schema", n => n["SchemaVersion"] = "2.0");
Reject("wrong comparison metric", n => n["Metric"] = "Area weighted");
Reject("empty archive", n => n["Scenarios"] = new JsonArray());
Reject("negative selection", n => n["BaselineIndex"] = -1);
Reject("selection outside archive", n => n["CandidateIndex"] = 2);
Reject("duplicate incoming names", n => n["Scenarios"]![1]!["Name"] = n["Scenarios"]![0]!["Name"]!.GetValue<string>());
Reject("existing name collision case insensitive", _ => { }, [archive.Scenarios[0].Name.ToUpperInvariant()]);
Reject("scenario limit includes existing", _ => { }, Enumerable.Range(0, 19).Select(i => "Existing " + i).ToArray());
Reject("empty name", n => n["Scenarios"]![0]!["Name"] = "");
Reject("oversized name", n => n["Scenarios"]![0]!["Name"] = new string('a', 81));
Reject("control characters in name", n => n["Scenarios"]![0]!["Name"] = "a\nb");
Reject("trim ambiguity rejected", n => n["Scenarios"]![0]!["Name"] = " a");
Reject("missing result", n => n["Scenarios"]![0]!["Result"] = null);
Reject("missing request field cannot use defaults", n => Result(n)["InputParameters"]!.AsObject().Remove("TimeStepsPerHour"));
Reject("missing statistic cannot use defaults", n => Result(n)["Statistics"]!.AsObject().Remove("Minimum"));
Reject("wrong result units", n => Result(n)["Units"] = "kWh/m2");
Reject("invalid timestep", n => Result(n)["InputParameters"]!["TimeStepsPerHour"] = 7);
Reject("invalid location", n => Result(n)["InputParameters"]!["SunSource"]!["Location"]!["Latitude"] = 100);
Reject("invalid geometry IDs", n => Result(n)["InputParameters"]!["GeometryIds"]![0] = Guid.Empty.ToString());
Reject("invalid grid", n => Result(n)["InputParameters"]!["GridMetres"] = 0);
Reject("mismatched points", n => Result(n)["Points"]!.AsArray().RemoveAt(0));
Reject("negative hours", n => Result(n)["Values"]![0] = -1);
Reject("hours exceed possible samples", n => Result(n)["Values"]![0] = 1000);
Reject("statistic differs from full values", n => Result(n)["Statistics"]!["Mean"] = 999);
Reject("nonunit sun vector", n => Result(n)["SunlightVectors"]![0] = new JsonArray(0, 0, 0));
Reject("sun-up time not in source", n => Result(n)["SunUpHoursOfYear"]![0] = 100);
Reject("mesh face outside vertices", n => Result(n)["ResultMesh"]![0]!["Faces"]![0]![0] = 999999);
Reject("mesh color misalignment", n => Result(n)["ResultMesh"]![0]!["VertexColorsArgb"]!.AsArray().RemoveAt(0));
Reject("missing provenance hash", n => Result(n)["Metadata"]!.AsObject().Remove("GeometrySha256"));
Reject("invalid provenance hash", n => Result(n)["Metadata"]!["SunSourceSha256"] = new string('Z', 64));
Reject("invalid unit scale", n => Result(n)["Metadata"]!["MetresPerModelUnit"] = "0");
Reject("missing timestamp", n => Result(n).AsObject().Remove("Timestamp"));
Check("duplicate JSON property rejected", () => { try { SunHoursArchive.Parse(original.ToJsonString().Replace("\"SchemaVersion\":\"1.0\"", "\"SchemaVersion\":\"1.0\",\"SchemaVersion\":\"1.0\""), []); } catch (ArgumentException) { return; } throw new Exception(); });
Check("malformed JSON rejected", () => { try { SunHoursArchive.Parse("{", []); } catch (ArgumentException) { return; } throw new Exception(); });
Check("oversized UTF8 rejected", () => { try { SunHoursArchive.Parse(new string('a', SunHoursArchive.MaximumBytes + 1), []); } catch (ArgumentException) { return; } throw new Exception(); });
Check("metadata cannot hide changed north", () => { var a = archive.Scenarios[0].Result; var b = a with { InputParameters = a.InputParameters with { SunSource = a.InputParameters.SunSource! with { NorthDegrees = 90 } } }; if (SunHoursArchive.SameSunConditions(a, b)) throw new Exception(); });
Check("metadata cannot hide changed vectors", () => { var a = archive.Scenarios[0].Result; var vectors = a.SunlightVectors.Select(v => v.ToArray()).ToArray(); vectors[0][0] += .001; if (SunHoursArchive.SameSunConditions(a, a with { SunlightVectors = vectors })) throw new Exception(); });
Console.WriteLine(JsonSerializer.Serialize(new { Passed = passed.Count, Cases = passed }, new JsonSerializerOptions { WriteIndented = true }));
return 0;
