using EnvironmentalHub.Core;
using EnvironmentalHub.Plugin;
using System.Text.Json;
using System.Globalization;

if (args.Length != 2) throw new ArgumentException("Pass verified archive and output folder.");
var archive = SunHoursArchive.Parse(File.ReadAllText(args[0]), []);
var result = archive.Scenarios[1].Result;
var original = JsonSerializer.Serialize(result);
var checks = new List<string>();
void Check(string name, bool condition) { if (!condition) throw new Exception(name); checks.Add(name); }
string Render(SunHoursResult r, bool dark = false) => SunHoursResultPage.Render(r, "歷史驗證資料 · 未核對目前模型", "歷史方案；未重新求解。", "尚未設定專案目標。", "", dark);
var bins = SunHoursResultPage.Distribution(result);
Check("native fixture histogram conserves all points", bins.Sum(b => b.Count) == result.Values.Length);
var edgeValues = Enumerable.Range(0, 9).Select(i => (double)i).ToArray();
var edge = result with { Values = edgeValues, Statistics = new(9, 0, 8, 4) };
var boundaryBins = SunHoursResultPage.Distribution(edge);
Check("boundary points included once; maximum in final bin", boundaryBins.Take(7).All(b => b.Count == 1) && boundaryBins[^1].Count == 2);
var constant = archive.Scenarios[0].Result;
Check("uniform native result uses one bin", SunHoursResultPage.Distribution(constant) is { Length: 1 } uniform && uniform[0].Count == constant.Values.Length);
foreach (var invalid in new[] { result with { Units = "kWh/m2" }, result with { Values = [] }, result with { Values = [double.NaN] }, result with { Statistics = result.Statistics with { Count = 0 } } })
{
    bool rejected = false; try { Render(invalid); } catch (ArgumentException) { rejected = true; }
    Check("invalid presentation data rejected " + checks.Count, rejected);
}
var samples = SunHoursResultPage.NativeSamples(result)!;
Check("legend samples come from actual native face colors", samples.Length > 0 && samples.All(p => result.Values.Contains(p.Value) && result.ResultMesh.Any(m => m.VertexColorsArgb.Contains(p.Color))));
var malformed = result with { ResultMesh = [result.ResultMesh[0] with { VertexColorsArgb = [] }] };
Check("unmappable colors disclose fallback", Render(malformed).Contains("不推定插值色階") && SunHoursResultPage.NativeSamples(malformed) is null);
var attack = "</p><script>alert('x')</script><img src=https://example.com/x>";
var malicious = result with { Metadata = new(result.Metadata) { ["Location"] = attack } };
var html = SunHoursResultPage.Render(malicious, attack, attack, attack, attack, false);
Check("all caller text encoded; no active script or image", !html.Contains("<script") && !html.Contains("<img") && html.Contains("&lt;script&gt;"));
Check("offline CSP denies scripts network forms and base URLs", html.Contains("default-src 'none'") && html.Contains("form-action 'none'") && html.Contains("base-uri 'none'"));
var dataUri = SunHoursResultPage.DataUri(html);
Check("installed Eto exact generated data URI allowed", SunHoursResultPage.AllowedNavigation(new(dataUri), dataUri));
Check("external and other data payloads denied", !SunHoursResultPage.AllowedNavigation(new("https://example.com"), dataUri) && !SunHoursResultPage.AllowedNavigation(new(SunHoursResultPage.DataUri("<script>attack</script>")), dataUri) && !SunHoursResultPage.AllowedNavigation(new("file:///C:/secret.txt"), dataUri));
Check("source conditions and units visible", html.Contains("時間取樣") && html.Contains("太陽來源摘要") && html.Contains("格點算術平均"));
var wrapped = result with { InputParameters = result.InputParameters with { SunSource = result.InputParameters.SunSource! with { HoursOfYear = [8759, 0] } } };
Check("sample endpoints preserve year-wrap sequence; not sorted or duration", Render(wrapped).Contains("12/31 23:00 → 01/01 00:00（2 點）") && Render(wrapped).Contains("不代表連續涵蓋期間"));
var march = result with { InputParameters = result.InputParameters with { SunSource = result.InputParameters.SunSource! with { HoursOfYear = [1416] } } };
Check("HOY calendar display follows native non-leap convention", Render(march).Contains("03/01 00:00 → 03/01 00:00（1 點）"));
var culture = CultureInfo.CurrentCulture;
try { CultureInfo.CurrentCulture = new("fr-FR"); Check("numeric SVG independent of locale", Render(result) == RenderUnderInvariant(result)); }
finally { CultureInfo.CurrentCulture = culture; }
string RenderUnderInvariant(SunHoursResult r) { var previous = CultureInfo.CurrentCulture; try { CultureInfo.CurrentCulture = CultureInfo.InvariantCulture; return Render(r); } finally { CultureInfo.CurrentCulture = previous; } }
Check("renderer does not mutate native result", original == JsonSerializer.Serialize(result));
Directory.CreateDirectory(args[1]);
foreach (bool dark in new[] { false, true }) File.WriteAllText(Path.Combine(args[1], dark ? "summary-dark.html" : "summary-light.html"), Render(result, dark));
File.WriteAllText(Path.Combine(args[1], "presentation_checks.json"), JsonSerializer.Serialize(new { Passed = checks.Count, Cases = checks, Fixture = args[0], Source = "Historical native export; no current solver run", Bins = bins }, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine(JsonSerializer.Serialize(new { Passed = checks.Count, Cases = checks }));
