import os, json, System, Rhino
import Eto.Forms as forms
import Eto.Drawing as drawing
from System.Reflection import BindingFlags
root = 'I:/中興工程-工作區/00.DEVE-HOME/GIT-Base/Main/EnvironmentalSimulationHub'
identity = json.load(open(os.path.join(root, 'docs/evidence/native_ui_0105/identity.json'), encoding='utf-8'))
doc = __rhino_doc__
assert System.Diagnostics.Process.GetCurrentProcess().Id == identity['pid']
assert doc.RuntimeSerialNumber == identity['document_serial'] and doc.Path in (None, '')
guid = System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32')
workspace = Rhino.UI.Panels.GetPanel(guid, doc)
if workspace is None:
    assert Rhino.RhinoApp.RunScript('_EnvironmentalSunHours', False)
    Rhino.RhinoApp.Wait()
    workspace = Rhino.UI.Panels.GetPanel(guid, doc)
assert str(workspace.GetType().Assembly.GetName().Version) == '0.10.5.0'
flags = BindingFlags.Instance | BindingFlags.NonPublic
module_type = workspace.GetType().Assembly.GetType('EnvironmentalHub.Plugin.SunHoursPanel')
panel = workspace.GetModule(module_type)
assert doc.Objects.Count == 0, 'Unexpected model content; stop all UI mutations'

def walk(control):
    yield control
    if isinstance(control, forms.Container):
        for child in control.Controls:
            for descendant in walk(child):
                yield descendant

def read_state():
    controls = list(walk(workspace))
    state = {'pid':identity['pid'], 'version':'0.10.5', 'objects':doc.Objects.Count,
             'units':str(doc.ModelUnitSystem), 'active_module':workspace.ActiveModule.Name,
             'panel_size':str(workspace.Size), 'parent_type':workspace.ParentWindow.GetType().FullName,
             'parent_handle':workspace.ParentWindow.NativeHandle.ToInt64(),
             'focused':[{'type':c.GetType().Name,'text':getattr(c,'Text',None)} for c in controls if c.HasFocus],
             'status':panel.StatusText, 'completed_result':panel.CompletedResultJson}
    print(json.dumps(state, ensure_ascii=False))
    return state
