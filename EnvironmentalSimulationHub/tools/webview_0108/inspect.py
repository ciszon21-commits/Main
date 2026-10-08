from System.Reflection import BindingFlags
test = sc.sticky['ESH_WEBVIEW_0108']; browser = test['browser']; summary = test['summary']
flags = BindingFlags.Instance | BindingFlags.NonPublic
status = summary.GetType().GetField('status', flags).GetValue(summary).Text
handler = browser.Handler
control = handler.GetType().GetProperty('Control').GetValue(handler)
core = control.CoreWebView2
record = {'status': str(status), 'handler': str(handler.GetType().FullName), 'control': str(control.GetType().FullName), 'core_ready': core is not None, 'width': float(control.ActualWidth), 'height': float(control.ActualHeight), 'object_count': doc.Objects.Count}
if core is not None:
    record['profile'] = str(core.Environment.UserDataFolder)
    record['browser_version'] = str(core.Environment.BrowserVersionString)
    assert os.path.normcase(os.path.abspath(record['profile'])).startswith(os.path.normcase(os.path.abspath(os.path.join(root, 'artifacts/webview_0108'))))
    test['dom_task'] = browser.ExecuteScriptAsync('return JSON.stringify({title:document.title,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,text:document.body.innerText});')
json.dump(record, open(os.path.join(evidence, 'native_inspect.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps(record, ensure_ascii=False))
