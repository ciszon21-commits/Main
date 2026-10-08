import clr
from System.Reflection import Assembly, BindingFlags
from Eto.Forms import Form
from Eto.Drawing import Size
from Microsoft.Win32 import Registry
flags = BindingFlags.Instance | BindingFlags.NonPublic
def registration():
    key = Registry.CurrentUser.OpenSubKey('Software\\McNeel\\Rhinoceros\\8.0\\Plug-ins\\bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f')
    if key is None: return None
    try: return {str(n): str(key.GetValue(n)) for n in key.GetValueNames()}
    finally: key.Dispose()
# No PlugIn.LoadPlugIn/RegisterPanel: assembly-only controls in an owned test form.
before = registration()
folder = os.path.join(root, 'artifacts/company-probe/0.10.8-fixed')
for name in ['EnvironmentalHub.Core.dll', 'EnvironmentalHub.Adapters.dll']:
    clr.AddReference(os.path.join(folder, name))
assembly = Assembly.LoadFrom(os.path.join(folder, 'EnvironmentalHub.WebViewProbe2.rhp'))
# Reset only this owned test process's prior experiment flag before checking the default gate.
System.Environment.SetEnvironmentVariable('ENVIRONMENTALHUB_WEBVIEW_PROBE', None)
assert str(assembly.GetName().Version) == '0.10.8.0'
from EnvironmentalHub.Core import SunHoursArchive
archive = SunHoursArchive.Parse(open(os.path.join(root, 'samples/archive_0107/legacy_comparison.json'), encoding='utf-8').read(), System.Array[System.String]([]))
t = assembly.GetType('EnvironmentalHub.Plugin.SunHoursPanel')
panel = System.Activator.CreateInstance(t)
checks = []
def check(name, value):
    assert value, name
    checks.append(name)
def field(name): return t.GetField(name, flags).GetValue(panel)
check('summary lazy before result', field('webSummary') is None)
try: panel.ExportSummaryHtml()
except System.InvalidOperationException: checks.append('no result summary rejected')
else: raise Exception('empty result accepted')
# Historical fixture is explicitly injected for presentation testing; never ExecuteRequest.
t.GetField('result', flags).SetValue(panel, archive.Scenarios[1].Result)
field('state').Text = '歷史驗證資料 · 未核對目前模型'
panel.SetTargetRange(2, 6)
check('project assessment reaches HTML', '專案目標 2' in panel.ExportSummaryHtml())
panel.ImportScenariosJson(open(os.path.join(root, 'samples/archive_0107/legacy_comparison.json'), encoding='utf-8').read())
check('history warning reaches HTML', '含匯入歷史結果' in panel.ExportSummaryHtml())
panel.SetSunSource(archive.Scenarios[1].Result.InputParameters.SunSource)
check('stale state reaches HTML', '前次結果' in panel.ExportSummaryHtml())
native_before = str(panel.CompletedResultJson)
panel.SetTargetRange(0, 13)
check('presentation changes preserve completed native JSON', native_before == str(panel.CompletedResultJson))
field('summaryHost').Visible = True
t.GetMethod('RefreshSummary', flags).Invoke(panel, None)
summary = field('webSummary')
st = summary.GetType()
check('default gate does not instantiate WebView', st.GetField('browser', flags).GetValue(summary) is None)
# Scope profile and experiment flag to this test process only, not persistent environment settings.
System.Environment.SetEnvironmentVariable('WEBVIEW2_USER_DATA_FOLDER', os.path.join(root, 'artifacts/webview_0108/profile'))
System.Environment.SetEnvironmentVariable('ENVIRONMENTALHUB_WEBVIEW_PROBE', '1')
host = Form(); host.Title = '本專案 WebView 隔離呈現驗證'; host.ClientSize = Size(320, 740)
field('summaryHost').Content = None
host.Content = summary
host.Show()
st.GetMethod('ShowHtml', flags).Invoke(summary, System.Array[System.Object]([panel.ExportSummaryHtml()]))
browser = st.GetField('browser', flags).GetValue(summary)
check('probe browser constructed', browser is not None)
after = registration()
check('plugin registration unchanged', before == after)
sc.sticky['ESH_WEBVIEW_0108'] = {'host': host, 'summary': summary, 'browser': browser, 'panel': panel, 'checks': checks, 'registration': before, 'assembly': assembly}
record = {'checks': checks, 'pid': System.Diagnostics.Process.GetCurrentProcess().Id, 'document_serial': int(doc.RuntimeSerialNumber), 'assembly': str(assembly.Location), 'version': str(assembly.GetName().Version), 'object_count': doc.Objects.Count, 'registration_before': before, 'registration_after': after, 'scope': 'Assembly-only test form, historical fixture; no plugin registration or solver run'}
json.dump(record, open(os.path.join(evidence, 'native_start.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps(record, ensure_ascii=False))
