using System.Diagnostics;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Buffers.Binary;

var root = Path.GetFullPath(args[0]);
var evidence = Path.GetFullPath(Path.Combine(root, args.Length > 1 ? args[1] : "docs/evidence/webview_0108"));
if (!evidence.StartsWith(root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)) throw new ArgumentException("Evidence must stay in this project.");
var widths = args.Length > 2 ? args[2].Split(',').Select(int.Parse).ToArray() : new[] { 320, 480 };
var output = Path.Combine(evidence, "browser-verified"); Directory.CreateDirectory(output);
var profile = Path.Combine(root, "artifacts/webview_0108", "cdp-profile-" + Guid.NewGuid().ToString("N"));
Directory.CreateDirectory(profile);
var start = new ProcessStartInfo("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe") { UseShellExecute = false, CreateNoWindow = true, WindowStyle = ProcessWindowStyle.Hidden };
foreach (var argument in new[] { "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-background-networking", "--disable-component-update", "--disable-sync", "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0", "--user-data-dir=" + profile, "about:blank" }) start.ArgumentList.Add(argument);
using var process = Process.Start(start)!;
using var socket = new ClientWebSocket();
int id = 0;
async Task<JsonElement> Call(string method, object parameters)
{
    using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(12));
    int request = ++id;
    await socket.SendAsync(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new { id = request, method, @params = parameters })), WebSocketMessageType.Text, true, deadline.Token);
    while (true)
    {
        using var buffer = new MemoryStream(); var bytes = new byte[65536]; WebSocketReceiveResult received;
        do { received = await socket.ReceiveAsync(new ArraySegment<byte>(bytes), deadline.Token); if (received.MessageType == WebSocketMessageType.Close) throw new Exception("CDP closed"); buffer.Write(bytes, 0, received.Count); } while (!received.EndOfMessage);
        using var message = JsonDocument.Parse(buffer.ToArray());
        if (!message.RootElement.TryGetProperty("id", out var responseId) || responseId.GetInt32() != request) continue;
        if (message.RootElement.TryGetProperty("error", out var error)) throw new Exception(error.ToString());
        return message.RootElement.GetProperty("result").Clone();
    }
}
try
{
    var portFile = Path.Combine(profile, "DevToolsActivePort");
    for (int retry = 0; !File.Exists(portFile) && retry < 80; retry++) await Task.Delay(100);
    var port = int.Parse(File.ReadAllLines(portFile)[0]);
    using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(10) };
    using var targets = JsonDocument.Parse(await http.GetStringAsync($"http://127.0.0.1:{port}/json/list"));
    var target = targets.RootElement.EnumerateArray().First(t => t.GetProperty("type").GetString() == "page");
    await socket.ConnectAsync(new(target.GetProperty("webSocketDebuggerUrl").GetString()!), CancellationToken.None);
    await Call("Page.enable", new { });
    var records = new List<object>();
    foreach (var theme in new[] { "light", "dark" }) foreach (int width in widths)
    {
        await Call("Emulation.setDeviceMetricsOverride", new { width, height = 2100, deviceScaleFactor = 1, mobile = false });
        await Call("Page.navigate", new { url = new Uri(Path.Combine(evidence, "summary-" + theme + ".html")).AbsoluteUri });
        JsonElement facts = default;
        for (int retry = 0; retry < 30; retry++)
        {
            var result = await Call("Runtime.evaluate", new { expression = "({ready:document.readyState,title:document.title,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,height:Math.ceil(document.querySelector('main').getBoundingClientRect().height),rows:document.querySelectorAll('tbody tr').length,body:document.body.innerText,bg:getComputedStyle(document.body).backgroundColor})", returnByValue = true });
            facts = result.GetProperty("result").GetProperty("value").Clone();
            if (facts.GetProperty("ready").GetString() == "complete" && facts.GetProperty("rows").GetInt32() == 8) break;
            await Task.Delay(100);
        }
        if (facts.GetProperty("width").GetInt32() != width || facts.GetProperty("scrollWidth").GetInt32() > width || facts.GetProperty("rows").GetInt32() != 8 || !facts.GetProperty("body").GetString()!.Contains("歷史驗證資料")) throw new Exception("Actual CSS width/content/overflow check failed: " + facts);
        await Call("Runtime.evaluate", new { expression = "new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))", awaitPromise = true });
        var capture = await Call("Page.captureScreenshot", new { format = "png", captureBeyondViewport = true, clip = new { x = 0, y = 0, width, height = facts.GetProperty("height").GetInt32(), scale = 1 } });
        var png = Convert.FromBase64String(capture.GetProperty("data").GetString()!);
        if (BinaryPrimitives.ReadInt32BigEndian(png.AsSpan(16, 4)) != width) throw new Exception("PNG width mismatch");
        string tag = width + "-" + theme; File.WriteAllBytes(Path.Combine(output, tag + ".png"), png);
        // Verify native disclosure semantics and overflow with full provenance/data visible.
        var expandedResult = await Call("Runtime.evaluate", new { expression = "(()=>{document.querySelectorAll('details').forEach(d=>d.open=true);return {scrollWidth:document.documentElement.scrollWidth,height:Math.ceil(document.querySelector('main').getBoundingClientRect().height),body:document.body.innerText,disclosures:document.querySelectorAll('details[open]').length}})()", returnByValue = true });
        var expanded = expandedResult.GetProperty("result").GetProperty("value").Clone();
        if (expanded.GetProperty("scrollWidth").GetInt32() > width || !expanded.GetProperty("body").GetString()!.Contains("太陽來源摘要")) throw new Exception("Expanded source/content overflow failed");
        if (expanded.GetProperty("disclosures").GetInt32() > 0)
        {
            await Call("Runtime.evaluate", new { expression = "new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))", awaitPromise = true });
            var expandedCapture = await Call("Page.captureScreenshot", new { format = "png", captureBeyondViewport = true, clip = new { x = 0, y = 0, width, height = expanded.GetProperty("height").GetInt32(), scale = 1 } });
            File.WriteAllBytes(Path.Combine(output, tag + "-expanded.png"), Convert.FromBase64String(expandedCapture.GetProperty("data").GetString()!));
        }
        records.Add(new { tag, facts, expanded, scope = "Headless browser HTML CSS viewport; not Rhino Dock or native theme" });
    }
    File.WriteAllText(Path.Combine(output, "verification.json"), JsonSerializer.Serialize(new { Passed = records.Count, Records = records }, new JsonSerializerOptions { WriteIndented = true }));
    Console.WriteLine(JsonSerializer.Serialize(new { Passed = records.Count, Widths = widths, Scope = "Actual CSS viewport, light/dark HTML and expanded disclosures", Output = output }));
}
finally { if (!process.HasExited) process.Kill(entireProcessTree: true); }
