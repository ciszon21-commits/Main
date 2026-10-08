using Eto.Drawing;
using Eto.Forms;

namespace EnvironmentalHub.Plugin;

// Optional local-only reader. Native result controls remain available during initialization/failure.
internal sealed class SunHoursWebSummary : Panel
{
    private readonly Label status = HubUi.Hint("圖像摘要為試驗功能；可隨時收合並使用原生結果。");
    private readonly Panel browserHost = new() { Height = 640 };
    private WebView? browser;
    private string? currentDataUri;
    internal string LoadState => status.Text;
    internal SunHoursWebSummary()
    {
        var layout = new DynamicLayout { Spacing = new Size(0, 8) };
        layout.AddRow(status); layout.AddRow(browserHost); Content = layout;
    }
    internal void ShowHtml(string html)
    {
        // The installed Eto handler initializes asynchronously; outer catches cannot promise recovery
        // from dispatcher failures. Keep native UI/HTML export available until host acceptance closes.
        if (System.Environment.GetEnvironmentVariable("ENVIRONMENTALHUB_WEBVIEW_PROBE") != "1")
        {
            status.Text = "WebView 宿主驗證中，預設未啟用。請使用「匯出圖像摘要 HTML」檢視圖表；原生結果仍可使用。";
            return;
        }
        try
        {
            if (browser is null)
            {
                browser = new WebView { BrowserContextMenuEnabled = false };
                browser.DocumentLoading += (_, e) => e.Cancel = !SunHoursResultPage.AllowedNavigation(e.Uri, currentDataUri);
                browser.OpenNewWindow += (_, e) => e.Cancel = true;
                // No links, no script, no command/message bridge and no new-window handler.
                browser.DocumentLoaded += (_, _) => status.Text = browser.DocumentTitle == "日照時數｜完成結果摘要" ? "圖像摘要已載入 · 只讀；模型操作請使用原生控制項。" : "圖像摘要未完成載入；請收合並使用原生結果或 HTML 匯出。";
                browserHost.Content = browser;
            }
            status.Text = "正在載入圖像摘要；若空白或無法載入，請收合並使用原生結果。";
            currentDataUri = SunHoursResultPage.DataUri(html);
            browser.LoadHtml(html);
        }
        catch (Exception e)
        {
            browserHost.Content = null; browser?.Dispose(); browser = null;
            status.Text = "圖像摘要未能載入 · 原生結果仍可使用。\n" + HubText.Error(e);
        }
    }
}
