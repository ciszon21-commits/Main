import os, json, System, Rhino, scriptcontext as sc
from System.Reflection import BindingFlags
import Eto.Forms as forms
import Eto.Drawing as drawing

assert System.Diagnostics.Process.GetCurrentProcess().Id == __OWNED_PID__
owned_slot = __OWNED_SLOT__
doc = __rhino_doc__
assert doc is not None and doc.Path in (None, '') and doc.Objects.Count == 0
assert Rhino.RhinoDoc.ActiveDoc.RuntimeSerialNumber == doc.RuntimeSerialNumber
evidence = os.path.join(root, 'docs/evidence/deploy_0109')
release = os.path.join(root, 'artifacts/releases/0.10.9/EnvironmentalHub.Plugin.rhp')
plugin_id = System.Guid('bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f')
workspace_id = System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32')
plugin = Rhino.PlugIns.PlugIn.Find(plugin_id)
if plugin is None:
    assert Rhino.PlugIns.PlugIn.LoadPlugIn(plugin_id)
    plugin = Rhino.PlugIns.PlugIn.Find(plugin_id)
assert plugin is not None
assembly = plugin.GetType().Assembly
assert str(assembly.GetName().Version) == '0.10.9.0'
assert os.path.normcase(os.path.normpath(str(assembly.Location))) == os.path.normcase(os.path.normpath(release))
assert os.path.normcase(os.path.normpath(str(Rhino.PlugIns.PlugIn.PathFromId(plugin_id)))) == os.path.normcase(os.path.normpath(release))
assert Rhino.RhinoApp.RunScript('_EnvironmentalSunHours', False)
Rhino.RhinoApp.Wait()
workspace = Rhino.UI.Panels.GetPanel(workspace_id, doc)
assert workspace is not None
panel_type = assembly.GetType('EnvironmentalHub.Plugin.SunHoursPanel')
panel = workspace.GetModule(panel_type)
flags = BindingFlags.NonPublic | BindingFlags.Instance
checks = []
def check(name, condition):
    assert condition, name
    checks.append(name)
def field(name):
    return panel_type.GetField(name, flags).GetValue(panel)
identity = {'version':'0.10.9.0','loaded_path':str(assembly.Location),'registered_path':str(Rhino.PlugIns.PlugIn.PathFromId(plugin_id)),
            'pid':__OWNED_PID__,'slot':owned_slot,'document_serial':int(doc.RuntimeSerialNumber),
            'rhino':str(Rhino.RhinoApp.Version),'runtime':str(System.Environment.Version),'scope':'Fresh owned Rhino; actual registered production plugin'}
json.dump(identity, open(os.path.join(evidence, 'identity.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
check('deployed version and registration match', True)
check('single registered workspace opens SunHours', workspace.ActiveModule.Name == 'SunHoursPanel')
check('summary remains lazy before result', field('webSummary') is None)

# Fresh owned fixture only; no existing/user document is changed.
doc.AdjustModelUnitSystem(Rhino.UnitSystem.Millimeters, False)
surface = Rhino.Geometry.PlaneSurface(Rhino.Geometry.Plane.WorldXY, Rhino.Geometry.Interval(0, 8000), Rhino.Geometry.Interval(0, 8000))
brep = surface.ToBrep(); geometry = doc.Objects.AddBrep(brep); brep.Dispose(); surface.Dispose()
assert geometry != System.Guid.Empty
request = json.load(open(os.path.join(root, 'samples/archive_0107/legacy_comparison.json'), encoding='utf-8'))['Scenarios'][0]['Result']['InputParameters']
request['GeometryIds'] = [str(geometry)]; request['ContextIds'] = []
Rhino.RhinoApp.RunScript('_Grasshopper', False)
baseline = json.loads(str(panel.ExecuteJson(json.dumps(request))))
check('fresh unshaded native solve matches baseline 256 points / 13 h', baseline['Statistics']['Count'] == 256 and baseline['Statistics']['Minimum'] == 13 and baseline['Statistics']['Maximum'] == 13)
panel.SaveScenario('部署驗證｜無遮蔭')
plane = Rhino.Geometry.Plane(Rhino.Geometry.Point3d(0, 0, 3000), Rhino.Geometry.Vector3d.ZAxis)
surface = Rhino.Geometry.PlaneSurface(plane, Rhino.Geometry.Interval(0, 4000), Rhino.Geometry.Interval(0, 8000))
brep = surface.ToBrep(); shade = doc.Objects.AddBrep(brep); brep.Dispose(); surface.Dispose()
request['ContextIds'] = [str(shade)]
shaded = json.loads(str(panel.ExecuteJson(json.dumps(request))))
check('fresh shaded native solve matches 8-13 h / mean 9.57421875', shaded['Statistics']['Count'] == 256 and shaded['Statistics']['Minimum'] == 8 and shaded['Statistics']['Maximum'] == 13 and abs(shaded['Statistics']['Mean'] - 9.57421875) < 1e-9)
panel.SaveScenario('部署驗證｜新增遮蔭'); panel.CompareScenarios(0, 1)
check('native A/B comparison contains real mean difference', '-3.426' in str(panel.ComparisonText))
native_before = str(panel.CompletedResultJson)
panel.SetTargetRange(8, 13)
html = str(panel.ExportSummaryHtml())
check('new report rendered through actual deployed panel', '首／尾取樣' in html and '完整區間數據' in html and '歷史驗證資料' not in html)
open(os.path.join(evidence, 'current-summary.html'), 'w', encoding='utf-8').write(html)
json.dump(shaded, open(os.path.join(evidence, 'current-result.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
open(os.path.join(evidence, 'current-comparison.json'), 'w', encoding='utf-8').write(str(panel.ExportComparisonJson()))
check('presentation assessment preserves full native result', str(panel.CompletedResultJson) == native_before)
try:
    panel.ExecuteJson('{}')
except System.Exception:
    pass
except Exception:
    pass
else:
    raise AssertionError('Invalid request was accepted')
check('failed validation preserves native result and marks previous state', str(panel.CompletedResultJson) == native_before and '前次結果' in str(panel.ExportSummaryHtml()))
crc = {str(i):int(doc.Objects.FindId(i).Geometry.DataCRC(0)) for i in [geometry, shade]}
weather_type = assembly.GetType('EnvironmentalHub.Plugin.WeatherPanel')
workspace.ShowModule(weather_type); workspace.ShowModule(panel_type)
check('workspace module navigation preserves result and scenarios', System.Object.ReferenceEquals(panel, workspace.GetModule(panel_type)) and str(panel.CompletedResultJson) == native_before and panel.ScenarioCount == 2)
System.Environment.SetEnvironmentVariable('ENVIRONMENTALHUB_WEBVIEW_PROBE', None)
field('summaryHost').Visible = True
panel_type.GetMethod('RefreshSummary', flags).Invoke(panel, None)
summary = field('webSummary')
check('disabled WebView does not create asynchronous browser host', summary is not None and summary.GetType().GetField('browser', flags).GetValue(summary) is None)
field('summaryHost').Visible = False
panel.ShowStage(4)

# Exercise actual SDK docking, not an unregistered clone/test form.
siblings = [g for g in Rhino.UI.Panels.GetOpenPanelIds() if g != workspace_id and len(Rhino.UI.Panels.PanelDockBars(g)) > 0]
dock_record = {'available_siblings':len(siblings)}
if siblings:
    target = Rhino.UI.Panels.PanelDockBar(siblings[0])
    Rhino.UI.Panels.ClosePanel(workspace_id, doc)
    returned = Rhino.UI.Panels.OpenPanel(target, workspace_id, True)
    Rhino.RhinoApp.Wait()
    workspace = Rhino.UI.Panels.GetPanel(workspace_id, doc)
    panel = workspace.GetModule(panel_type)
    check('actual dock roundtrip retains result/scenarios', str(panel.CompletedResultJson) == native_before and panel.ScenarioCount == 2)
    dock_record.update({'requested_dock':str(target),'actual_dock':str(Rhino.UI.Panels.PanelDockBar(workspace_id)),'returned':str(returned),'workspace_size':str(workspace.Size)})
    check('SDK confirms requested dock container', Rhino.UI.Panels.PanelDockBar(workspace_id) == target)
else:
    dock_record['scope'] = 'No existing native dock sibling; full Dock acceptance remains pending'
Rhino.UI.Panels.FloatPanel(workspace_id, Rhino.UI.Panels.FloatPanelMode.Show)
Rhino.RhinoApp.Wait()
workspace = Rhino.UI.Panels.GetPanel(workspace_id, doc); panel = workspace.GetModule(panel_type)
check('float roundtrip retains result/scenarios', str(panel.CompletedResultJson) == native_before and panel.ScenarioCount == 2)
check('model geometry unchanged by presentation/navigation', all(int(doc.Objects.FindId(System.Guid(i)).Geometry.DataCRC(0)) == value for i,value in crc.items()))
sc.sticky['ESH_DEPLOY_0109'] = {'identity':identity,'checks':checks,'model_ids':[geometry,shade],'crc':crc,'workspace':workspace,'panel':panel,'dock':dock_record}
json.dump({'identity':identity,'passed':len(checks),'checks':checks,'baseline':baseline['Statistics'],'shaded':shaded['Statistics'],'dock':dock_record,
           'scope':'Fresh registered native solves, export API, state, actual Dock/float. SaveFileDialog and keyboard not claimed.'},
          open(os.path.join(evidence, 'native_checks.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps({'passed':len(checks),'version':'0.10.9','baseline':baseline['Statistics'],'shaded':shaded['Statistics']}, ensure_ascii=False))
