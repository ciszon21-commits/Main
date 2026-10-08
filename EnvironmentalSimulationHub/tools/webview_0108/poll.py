test = sc.sticky['ESH_WEBVIEW_0108']; tag = test['capture_tag']
assert 'capture_error' not in test, test.get('capture_error')
task = test['capture_task']; assert task.IsCompleted and not task.IsFaulted
test['capture_stream'].Dispose()
dom_task = test['dom_task']; assert dom_task.IsCompleted and not dom_task.IsFaulted
# Eto's installed handler returns a JSON string with escaped quotes; decode the envelope.
raw = str(dom_task.Result)
try: dom = json.loads(raw)
except ValueError: dom = json.loads(raw.replace('\\"', '"'))
json.dump({'raw': raw, 'dom': dom}, open(os.path.join(evidence, tag + '-dom.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
assert dom['width'] == int(tag.split('-')[0]) and dom['scrollWidth'] == dom['width'], 'Horizontal overflow'
assert '歷史驗證資料' in dom['text'] and '格點算術平均' in dom['text'] and dom['rangeRows'] == 8
assert doc.Objects.Count == 0
record = {'tag': tag, 'dom': dom, 'png': tag + '.png', 'pid': System.Diagnostics.Process.GetCurrentProcess().Id, 'object_count': doc.Objects.Count, 'scope': 'Eto test form and real WebView2; HTML theme only, not Rhino dark theme or Dock'}
json.dump(record, open(os.path.join(evidence, tag + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps({'verified': tag, 'width': dom['width'], 'scrollWidth': dom['scrollWidth']}))
