using System.Globalization;
using System.Net;
using System.Text;
using EnvironmentalHub.Core;

namespace EnvironmentalHub.Plugin;

// Offline report composition only. Native result values, colors and caller state remain authoritative.
internal static class SunHoursReportLayout
{
    private static string E(string? text) => WebUtility.HtmlEncode(text ?? "");
    private static string N(double value) => value.ToString("0.###", CultureInfo.InvariantCulture);
    private static string SampleTime(double hoy) => new DateTime(2021, 1, 1).AddMinutes(Math.Round(hoy * 60)).ToString("MM/dd HH:mm", CultureInfo.InvariantCulture);
    private const string Styles = """
        *{box-sizing:border-box}html{color-scheme:var(--scheme)}
        body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.65 'Segoe UI','Microsoft JhengHei',sans-serif}
        main{max-width:1180px;margin:0 auto;padding:32px 40px 24px;background:var(--paper)}
        p{margin:0;overflow-wrap:anywhere}h1,h2,h3{margin:0;font-weight:600}h1{font-size:36px;line-height:1.25;letter-spacing:.025em}h2{font-size:18px;line-height:1.4}h3{font-size:13px}
        .masthead{display:flex;justify-content:space-between;align-items:center;gap:12px;padding-bottom:17px;border-bottom:1px solid var(--fg)}
        .brand{display:flex;align-items:center;gap:10px;font-size:11px;font-weight:600;letter-spacing:.12em}.mark{width:28px;height:28px;color:var(--run)}
        .edition,.eyebrow,.index,.label{font-size:11px;color:var(--muted)}.edition{white-space:nowrap}.eyebrow{letter-spacing:.1em;font-weight:600}
        .title-row{display:flex;justify-content:space-between;align-items:end;gap:24px;margin:30px 0 22px}.title-row h1{margin-top:8px}.subtitle{color:var(--muted);margin-top:10px;font-size:13px}.location{display:flex;align-items:center;gap:6px;color:var(--environment);font-size:13px;overflow-wrap:anywhere}
        .icon{width:20px;height:20px;flex:none;fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}
        .state{display:flex;align-items:start;gap:10px;border-left:3px solid var(--run);padding:10px 14px;background:var(--state-bg);color:var(--state-fg);font-size:12px}.state .icon{width:17px;height:17px;margin-top:2px}.text{white-space:pre-wrap;overflow-wrap:anywhere;min-width:0}
        .metrics{display:grid;grid-template-columns:2fr repeat(3,1fr);margin:28px 0 12px;font-variant-numeric:tabular-nums}.metric{border-left:1px solid var(--rule);padding:8px 24px}.metric:first-child{border:0;padding-left:0}.metric dt{color:var(--muted);font-size:12px;margin-bottom:7px}.metric dd{margin:0;font-size:32px;line-height:1.15;letter-spacing:-.035em}.metric.primary dd{font-size:56px}.metric.primary dt{color:var(--result)}.unit{font-size:14px;color:var(--muted);letter-spacing:0;margin-left:5px;font-weight:400}
        .note{color:var(--muted);font-size:12px;line-height:1.7}.metric-note{max-width:660px;margin-bottom:28px}
        .report-grid{display:grid;grid-template-columns:minmax(0,1.85fr) minmax(0,1fr);border-top:1px solid var(--fg)}.visual{min-width:0;padding:24px 30px 24px 0}.context{min-width:0;padding:24px 0 24px 28px;border-left:1px solid var(--rule)}
        .section-head{display:flex;align-items:center;gap:10px;margin-bottom:15px;color:var(--result)}.section-head .index{font-variant-numeric:tabular-nums;color:inherit;font-size:12px}.section-head h2{color:var(--fg)}.section-head .icon{margin-left:auto;color:inherit}.environment{color:var(--environment)}.compare{color:var(--compare)}.settings{color:var(--settings)}
        figure{margin:18px 0 14px}.chart{display:block;width:100%;height:auto;overflow:visible;color:var(--result);font-variant-numeric:tabular-nums}.chart .grid{stroke:var(--rule);stroke-width:1}.chart text{fill:var(--muted);font-family:'Segoe UI','Microsoft JhengHei',sans-serif;font-size:11px}.chart .count{fill:var(--fg);font-size:12px}.chart .bar{fill:var(--result)}
        figcaption{display:flex;justify-content:space-between;gap:12px;padding:7px 0 0;font-size:11px;color:var(--muted)}
        details{margin-top:18px;border-top:1px solid var(--rule)}summary{cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 0;font-size:12px;font-weight:600;color:var(--fg)}summary::-webkit-details-marker{display:none}summary::after{content:'＋';font-size:18px;font-weight:400;color:var(--muted)}details[open]>summary::after{content:'−'}summary:focus-visible{outline:2px solid var(--environment);outline-offset:4px}
        table{width:100%;border-collapse:collapse;font-size:12px;font-variant-numeric:tabular-nums}th,td{padding:8px 0;border-bottom:1px solid var(--rule);text-align:left}th{color:var(--muted);font-weight:400}th:not(:first-child),td:not(:first-child){text-align:right}.table-note{padding-top:10px}
        .legend-block{margin-top:24px;padding-top:18px;border-top:1px solid var(--rule)}.legend{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:3px;margin:12px 0 9px}.sample{font-size:12px;font-variant-numeric:tabular-nums}.swatch{display:block;height:13px;margin-bottom:7px;border:1px solid var(--swatch-border)}.sample span:last-child{display:block;text-align:center;white-space:nowrap}.legend-title{display:flex;align-items:center;gap:8px}
        dl{margin:0}.conditions{display:grid;grid-template-columns:85px minmax(0,1fr);gap:10px 14px;font-size:12px}.conditions dt{color:var(--muted)}.conditions dd{margin:0;overflow-wrap:anywhere;font-variant-numeric:tabular-nums}.provenance{padding-bottom:12px}.hash{font:11px/1.7 Consolas,monospace}.context-note{margin-top:18px}.diagnostics{margin-top:12px;color:var(--state-fg);font-size:12px}
        .decision-grid{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid var(--fg)}.decision{padding:23px 30px 25px 0;min-width:0}.decision:last-child{padding-left:28px;padding-right:0;border-left:1px solid var(--rule)}.decision .text{font-size:13px;margin-bottom:12px}.decision .section-head{margin-bottom:18px}
        footer{display:flex;justify-content:space-between;gap:20px;border-top:1px solid var(--rule);padding-top:14px;font-size:10px;color:var(--muted);letter-spacing:.025em}.footer-brand{font-weight:600;letter-spacing:.08em}
        @media(max-width:760px){main{padding:24px}.title-row{align-items:start;flex-direction:column;gap:14px}.title-row h1{font-size:30px}.metrics{grid-template-columns:repeat(3,minmax(0,1fr));gap:16px 0}.metric.primary{grid-column:1/-1;padding:0 0 17px;border-bottom:1px solid var(--rule)}.metric:nth-child(2){padding-left:0;border-left:0}.metric{padding:0 16px}.metric dd{font-size:28px}.report-grid{grid-template-columns:1fr}.visual{padding:23px 0}.context{border-left:0;border-top:1px solid var(--rule);padding:23px 0}.decision-grid{grid-template-columns:1fr}.decision,.decision:last-child{padding:23px 0;border-left:0}.decision:last-child{border-top:1px solid var(--rule)}.conditions{grid-template-columns:100px minmax(0,1fr)}footer{flex-direction:column;gap:5px}}
        @media(max-width:380px){main{padding:18px 16px}.brand{font-size:9px;letter-spacing:.07em;gap:7px}.mark{width:23px;height:23px}.edition{font-size:10px}.title-row{margin-top:24px}.title-row h1{font-size:27px}.metric dd{font-size:24px}.metric.primary dd{font-size:50px}.metric{padding:0 10px}.unit{font-size:12px;margin-left:3px}.conditions{grid-template-columns:85px minmax(0,1fr)}.section-head h2{font-size:16px}.legend{gap:2px}.sample{font-size:11px}.chart text,.chart .count{font-size:16px}}
        @media print{:root{--bg:white;--paper:white;--fg:#20292e;--muted:#53616b;--rule:#c6ced1;--result:#48585a;--environment:#226b61;--compare:#73506e;--settings:#58528b;--run:#8a652e;--state-bg:#f5f1e9;--state-fg:#73501f;--swatch-border:#889399;--scheme:light}main{max-width:none;padding:12px}.state,.swatch,.bar{print-color-adjust:exact}details>summary{display:none}details::details-content{content-visibility:visible}section,.metrics,.decision{break-inside:avoid}footer{margin-top:12px}}
        """;

    private static string Icon(string kind) => "<svg class=\"icon\" viewBox=\"0 0 24 24\" aria-hidden=\"true\">" + (kind switch
    {
        "sun" => "<circle cx=\"12\" cy=\"12\" r=\"4\"/><path d=\"M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5\"/>",
        "chart" => "<path d=\"M3 3v18h18M7 17v-5m5 5V7m5 10V4\"/>",
        "location" => "<path d=\"M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z\"/><circle cx=\"12\" cy=\"10\" r=\"2\"/>",
        "compare" => "<path d=\"M3 7h16m-4-4 4 4-4 4M21 17H5m4-4-4 4 4 4\"/>",
        "target" => "<circle cx=\"12\" cy=\"12\" r=\"8\"/><circle cx=\"12\" cy=\"12\" r=\"3\"/><path d=\"M12 2v2m0 16v2M2 12h2m16 0h2\"/>",
        _ => "<circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M12 11v6m0-10v.1\"/>"
    }) + "</svg>";

    private static void Heading(StringBuilder page, string index, string title, string icon, string theme = "") =>
        page.Append("<div class=\"section-head ").Append(theme).Append("\"><span class=\"index\">").Append(index).Append("</span><h2>").Append(title).Append("</h2>").Append(Icon(icon)).Append("</div>");

    internal static string Render(SunHoursResult result, string state, string comparison, string assessment, string diagnostics, bool dark)
    {
        var bins = SunHoursResultPage.Distribution(result);
        var input = result.InputParameters;
        var requestedHours = input.SunSource?.HoursOfYear;
        var sampleWindow = requestedHours is { Length: > 0 } && requestedHours.All(h => double.IsFinite(h) && h >= 0 && h < 8760)
            ? $"{SampleTime(requestedHours[0])} → {SampleTime(requestedHours[^1])}（{requestedHours.Length} 點）" : "未提供";
        var location = result.Metadata.GetValueOrDefault("Location", input.SunSource?.Location.Name ?? "未提供");
        var page = new StringBuilder();
        page.Append("<!doctype html><html lang=\"zh-Hant\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\"><title>日照時數｜完成結果摘要</title><style>");
        page.Append(dark
            ? ":root{--scheme:dark;--bg:#181d20;--paper:#20272b;--fg:#edf1f2;--muted:#b3c0c5;--rule:#435157;--result:#b5c7c9;--environment:#8ecbbf;--compare:#d2b0ca;--settings:#bbb1e0;--run:#d4b778;--state-bg:#302c24;--state-fg:#e3c994;--swatch-border:#89999e;}"
            : ":root{--scheme:light;--bg:#e9edef;--paper:#fcfcfa;--fg:#263238;--muted:#5a6c75;--rule:#d7dfe0;--result:#48585a;--environment:#226b61;--compare:#73506e;--settings:#58528b;--run:#8a652e;--state-bg:#f4f0e6;--state-fg:#795820;--swatch-border:#89979c;}");
        page.Append(Styles).Append("</style></head><body><main><header><div class=\"masthead\"><div class=\"brand\"><span class=\"mark\">").Append(Icon("sun")).Append("</span>ENVIRONMENTAL HUB</div><span class=\"edition\">建築性能 · 成果摘要</span></div><div class=\"title-row\"><div><p class=\"eyebrow\">SOLAR / 日照分析</p><h1>直射日照時數</h1><p class=\"subtitle\">幾何遮蔭下的日照分布與分析條件</p></div><p class=\"location\">").Append(Icon("location")).Append(E(location)).Append("</p></div></header><div class=\"state\" role=\"note\">").Append(Icon("info")).Append("<p class=\"text\">").Append(E(state)).Append("</p></div><dl class=\"metrics\">");
        foreach (var metric in new[] { ("格點平均日照", N(result.Statistics.Mean), "h", "primary"), ("最小日照", N(result.Statistics.Minimum), "h", ""), ("最大日照", N(result.Statistics.Maximum), "h", ""), ("分析格點", result.Values.Length.ToString(CultureInfo.InvariantCulture), "點", "") })
            page.Append("<div class=\"metric ").Append(metric.Item4).Append("\"><dt>").Append(metric.Item1).Append("</dt><dd>").Append(metric.Item2).Append("<span class=\"unit\">").Append(metric.Item3).Append("</span></dd></div>");
        page.Append("</dl><p class=\"note metric-note\">格點算術平均，未按面積加權。日照時數不代表照度、日射能量或法規判定。</p><div class=\"report-grid\"><section class=\"visual\">");
        Heading(page, "01", "日照分布", "chart");
        page.Append("<p class=\"note\">讀取不同日照區間的格點數，掌握模型的日照分布。</p><figure><svg class=\"chart\" viewBox=\"0 0 440 228\" role=\"img\" aria-label=\"日照時數分布；完整區間與格點數見可展開表格\">");
        int peak = bins.Max(b => b.Count);
        double axisStep = Math.Max(2, Math.Pow(10, Math.Floor(Math.Log10(peak))));
        double axisMax = Math.Ceiling(peak / axisStep) * axisStep;
        for (int tick = 0; tick <= 2; tick++)
        {
            double y = 180 - tick * 71;
            page.Append("<path class=\"grid\" d=\"M34 ").Append(N(y)).Append("H432\"/><text x=\"26\" y=\"").Append(N(y + 4)).Append("\" text-anchor=\"end\">").Append(N(axisMax * tick / 2.0)).Append("</text>");
        }
        for (int i = 0; i < bins.Length; i++)
        {
            var bin = bins[i]; double height = 142.0 * bin.Count / axisMax, pitch = 390.0 / bins.Length, x = 38 + i * pitch;
            page.Append("<rect class=\"bar\" x=\"").Append(N(x)).Append("\" y=\"").Append(N(180 - height)).Append("\" width=\"").Append(N(pitch - 6)).Append("\" height=\"").Append(N(height)).Append("\"><title>").Append(N(bin.Lower)).Append("–").Append(N(bin.Upper)).Append(" h：").Append(bin.Count).Append(" 點</title></rect><text class=\"count\" x=\"").Append(N(x + (pitch - 6) / 2)).Append("\" y=\"").Append(N(170 - height)).Append("\" text-anchor=\"middle\">").Append(bin.Count).Append("</text>");
        }
        page.Append("<text x=\"34\" y=\"204\">").Append(N(bins[0].Lower)).Append(" h</text>");
        if (bins.Length > 1) page.Append("<text x=\"233\" y=\"204\" text-anchor=\"middle\">").Append(N((bins[0].Lower + bins[^1].Upper) / 2)).Append(" h</text>");
        page.Append("<text x=\"432\" y=\"204\" text-anchor=\"end\">").Append(N(bins[^1].Upper)).Append(" h</text></svg><figcaption><span>縱軸 格點數 / 橫軸 日照時數 h</span><span>統計柱色</span></figcaption></figure><details><summary>完整區間數據</summary><table><thead><tr><th scope=\"col\">日照區間 h</th><th scope=\"col\">格點數</th><th scope=\"col\">占比 %</th></tr></thead><tbody>");
        foreach (var bin in bins)
            page.Append("<tr><td>").Append(bin.Lower == bin.Upper ? N(bin.Lower) : $"[{N(bin.Lower)}, {N(bin.Upper)}{(bin.Last ? "]" : ")")}").Append("</td><td>").Append(bin.Count).Append("</td><td>").Append(N(100.0 * bin.Count / result.Values.Length)).Append("</td></tr>");
        page.Append("</tbody></table><p class=\"note table-note\">左界包含、右界不包含；最後區間包含最大值。全數相同時顯示單一值。占比按格點計算，非面積比例。</p></details><div class=\"legend-block\"><h3 class=\"legend-title\">原生模型色樣</h3>");
        var samples = SunHoursResultPage.NativeSamples(result);
        if (samples is null) page.Append("<p class=\"note\">無法對應原生面色樣 · 請檢視視埠網格，不推定插值色階。</p>");
        else
        {
            page.Append("<div class=\"legend\" style=\"grid-template-columns:repeat(").Append(samples.Length).Append(",minmax(0,1fr))\">");
            foreach (var sample in samples)
                page.Append("<div class=\"sample\"><span class=\"swatch\" style=\"background:#").Append((sample.Color & 0xffffff).ToString("X6", CultureInfo.InvariantCulture)).Append("\"></span><span>").Append(N(sample.Value)).Append(" h</span></div>");
            page.Append("</div><p class=\"note\">實際網格面色樣，無插值。統計柱色與模型色樣分開呈現；跨方案請比較數值。</p>");
        }
        page.Append("</div></section><section class=\"context\">");
        Heading(page, "02", "分析條件", "location", "environment");
        page.Append("<dl class=\"conditions\">");
        var conditions = new[] { ("地點", location), ("首／尾取樣", sampleWindow), ("網格／偏移", $"{N(input.GridMetres)} / {N(input.OffsetMetres)} m"), ("時間取樣", $"{input.TimeStepsPerHour} 步／小時"), ("有效太陽向量", $"{result.SunlightVectors.Length} 個"), ("時間制", input.SunSource?.SolarTime == true ? "真太陽時" : "當地標準時間"), ("北向", $"{N(input.SunSource?.NorthDegrees ?? 0)}°"), ("模型單位", result.Metadata.GetValueOrDefault("ModelUnits", "未提供")), ("自遮蔭", input.GeometryBlocks ? "開啟" : "關閉") };
        foreach (var condition in conditions) page.Append("<dt>").Append(condition.Item1).Append("</dt><dd>").Append(E(condition.Item2)).Append("</dd>");
        page.Append("</dl><p class=\"note context-note\">以上為完成結果的條件快照。日期按非閏年 HOY 換算；首尾均為取樣點，不代表連續涵蓋期間。向量權重不等於曆時長度。</p><details><summary>完成時間與來源追溯</summary><dl class=\"conditions provenance\">");
        foreach (var item in new[] { ("完成時間", result.Timestamp.ToString("yyyy-MM-dd HH:mm:ss zzz", CultureInfo.InvariantCulture)), ("求解耗時", $"{N(result.ExecutionTimeSeconds)} s"), ("太陽來源摘要", result.Metadata.GetValueOrDefault("SunSourceSha256", "未提供")), ("模型識別摘要", result.Metadata.GetValueOrDefault("GeometrySha256", "未提供")) })
            page.Append("<dt>").Append(item.Item1).Append("</dt><dd class=\"hash\">").Append(E(item.Item2)).Append("</dd>");
        page.Append("</dl><p class=\"note\">來源摘要用於追溯，不是目前模型的獨立幾何驗證。</p></details>");
        if (!string.IsNullOrWhiteSpace(diagnostics)) page.Append("<p class=\"text diagnostics\">").Append(E(diagnostics)).Append("</p>");
        page.Append("</section></div><div class=\"decision-grid\"><section class=\"decision\">");
        Heading(page, "03", "專案目標評估", "target", "settings");
        page.Append("<p class=\"text\">").Append(E(assessment)).Append("</p><p class=\"note\">使用者設定的包含上下限區間，不代表法規合規。</p></section><section class=\"decision\">");
        Heading(page, "04", "方案比較", "compare", "compare");
        page.Append("<p class=\"text\">").Append(E(comparison)).Append("</p><p class=\"note\">選擇方案與定位 Rhino 模型，請使用原生控制項。</p></section></div><footer><span class=\"footer-brand\">ENVIRONMENTAL HUB / 建築環境模擬</span><span>只讀結果快照 · 未重新求解 · 單位 h</span></footer></main></body></html>");
        return page.ToString();
    }
}
