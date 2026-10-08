import os, json, System, Rhino
import Eto.Forms as forms
from System.Reflection import BindingFlags
root = 'I:/中興工程-工作區/00.DEVE-HOME/GIT-Base/Main/EnvironmentalSimulationHub'
evidence = os.path.join(root,'docs/evidence/archive_0107')
outputs = os.path.join(root,'samples/archive_0107')
identity = json.load(open(os.path.join(evidence,'identity.json'),encoding='utf-8'))
doc = __rhino_doc__
assert System.Diagnostics.Process.GetCurrentProcess().Id == identity['pid']
assert doc.RuntimeSerialNumber == identity['document_serial'] and doc.Path in (None,'')
guid = System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32')
workspace = Rhino.UI.Panels.GetPanel(guid,doc)
if workspace is None:
    assert Rhino.RhinoApp.RunScript('_EnvironmentalSunHours',False)
    workspace = Rhino.UI.Panels.GetPanel(guid,doc)
assert str(workspace.GetType().Assembly.GetName().Version)=='0.10.7.0'
flags = BindingFlags.Instance | BindingFlags.NonPublic
module_type = workspace.GetType().Assembly.GetType('EnvironmentalHub.Plugin.SunHoursPanel')
panel = workspace.GetModule(module_type)
fixture_path = os.path.join(evidence,'fixture.json')
if os.path.exists(fixture_path):
    fixture = json.load(open(fixture_path,encoding='utf-8'))
    for obj in doc.Objects:
        key = str(obj.Id)
        if key in fixture['model_crc']:
            assert str(obj.Geometry.DataCRC(0)) == fixture['model_crc'][key], 'Fixture geometry changed'
        else:
            assert obj.Attributes.GetUserString('EnvironmentalHub.PreviewOwner') == 'bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f/SunHours', 'Unexpected object; stop test'
    assert all(doc.Objects.FindId(System.Guid(key)) is not None for key in fixture['model_crc'])
else:
    assert doc.Objects.Count == 0 and not doc.Modified

def read_state():
    result = panel.CompletedResultJson
    state={'pid':identity['pid'],'hwnd':Rhino.RhinoApp.MainWindowHandle().ToInt64(),
           'objects':doc.Objects.Count,'modified':doc.Modified,'units':str(doc.ModelUnitSystem),
           'module':workspace.ActiveModule.Name,'workspace_size':str(workspace.Size),
           'parent':workspace.ParentWindow.GetType().FullName,'parent_handle':workspace.ParentWindow.NativeHandle.ToInt64(),
           'registered_instances':len(Rhino.UI.Panels.GetPanels(guid,doc)),
           'result':json.loads(result)['Statistics'] if result is not None else None,
           'scenario_count':panel.ScenarioCount,'status':panel.StatusText}
    print(json.dumps(state,ensure_ascii=False))
    return state
