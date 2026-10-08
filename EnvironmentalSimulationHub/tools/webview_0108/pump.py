import time
test = sc.sticky['ESH_WEBVIEW_0108']; host = test['host']; browser = test['browser']
host.BringToFront()
host.ClientSize = __import__('Eto.Drawing', fromlist=['Size']).Size(320, 740)
host.Show(Rhino.UI.RhinoEtoApp.MainWindow)
deadline = time.monotonic() + 5
while time.monotonic() < deadline and not test['capture_task'].IsCompleted:
    Rhino.RhinoApp.Wait()
    time.sleep(.02)
record = {'capture_status': str(test['capture_task'].Status), 'dom_status': str(test['dom_task'].Status), 'visible': bool(host.Visible), 'title': str(browser.DocumentTitle)}
if test['dom_task'].IsCompleted: record['dom_raw'] = str(test['dom_task'].Result)
json.dump(record, open(os.path.join(evidence, 'pump.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps(record, ensure_ascii=False))
