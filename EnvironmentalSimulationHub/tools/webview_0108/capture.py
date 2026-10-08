from Eto.Drawing import Size
from System.IO import FileStream, FileMode, FileAccess
from Microsoft.Web.WebView2.Core import CoreWebView2CapturePreviewImageFormat
test = sc.sticky['ESH_WEBVIEW_0108']; browser = test['browser']; host = test['host']
assert 'capture_task' not in test or test['capture_task'].IsCompleted
tag = str(capture_width) + '-' + capture_theme
test['capture_tag'] = tag
host.ClientSize = Size(capture_width, 740)
def capture_loaded(sender, event):
    browser.DocumentLoaded -= capture_loaded
    try:
        native = browser.Handler.GetType().GetProperty('Control').GetValue(browser.Handler)
        stream = FileStream(os.path.join(evidence, tag + '.png'), FileMode.CreateNew, FileAccess.Write)
        test['capture_stream'] = stream
        test['capture_task'] = native.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, stream)
        test['dom_task'] = browser.ExecuteScriptAsync('return JSON.stringify({title:document.title,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,text:document.body.innerText,rangeRows:document.querySelectorAll("tbody tr").length,bg:getComputedStyle(document.body).backgroundColor});')
    except Exception as ex:
        test['capture_error'] = str(ex)
        print('Capture error: ' + str(ex))
test['capture_handler'] = capture_loaded
browser.DocumentLoaded += capture_loaded
from System.Reflection import BindingFlags
test['summary'].GetType().GetMethod('ShowHtml', BindingFlags.Instance | BindingFlags.NonPublic).Invoke(test['summary'], System.Array[System.Object]([open(os.path.join(evidence, 'summary-' + capture_theme + '.html'), encoding='utf-8').read()]))
print(json.dumps({'queued': tag, 'scope': 'Real WebView2 in Eto test form, not production Dock'}))
