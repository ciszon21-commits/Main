import os, json, System, Rhino
import Eto.Forms as forms
import Eto.Drawing as drawing
from System.Reflection import BindingFlags

root = 'I:/中興工程-工作區/00.DEVE-HOME/GIT-Base/Main/EnvironmentalSimulationHub'
identity = json.load(open(os.path.join(root, 'docs/evidence/home_0105/identity.json'), encoding='utf-8'))
doc = __rhino_doc__
assert System.Diagnostics.Process.GetCurrentProcess().Id == identity['pid']
assert doc.RuntimeSerialNumber == identity['document_serial'] and doc.Path in (None, '')
guid = System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32')
assert Rhino.RhinoApp.RunScript('_EnvironmentalHub', False)
Rhino.RhinoApp.Wait()
workspace = Rhino.UI.Panels.GetPanel(guid, doc)
assert str(workspace.GetType().Assembly.GetName().Version) == '0.10.5.0'
window = workspace.ParentWindow
assert isinstance(window, forms.Form)
assert window.NativeHandle != Rhino.RhinoApp.MainWindowHandle()
checks = []
sizes = []
before = {'objects': sorted(str(o.Id) for o in doc.Objects), 'units': str(doc.ModelUnitSystem),
          'height': window.Size.Height, 'location': str(window.Location)}
flags = BindingFlags.Instance | BindingFlags.NonPublic
apply = workspace.GetType().GetMethod('EnsureInitialFloatingWidth', flags)
initialized = workspace.GetType().GetField('initialFloatingWidthApplied', flags)

def record(label):
    sizes.append({'case': label, 'window': str(workspace.ParentWindow.Size), 'panel': str(workspace.Size)})
    checks.append(label)

try:
    assert window.Size.Width >= 500 and workspace.Size.Width >= 480
    assert initialized.GetValue(workspace)
    record('first_native_open_has_500_outer_and_480_plus_content')
    window.Size = drawing.Size(320, window.Size.Height)
    Rhino.RhinoApp.Wait()
    assert Rhino.RhinoApp.RunScript('_EnvironmentalSunHours', False)
    Rhino.RhinoApp.Wait()
    assert window.Size.Width == 320 and workspace.ActiveModule.Name == 'SunHoursPanel'
    record('manual_narrow_width_survives_module_command')
    Rhino.UI.Panels.ClosePanel(guid, doc)
    assert Rhino.RhinoApp.RunScript('_EnvironmentalSunHours', False)
    Rhino.RhinoApp.Wait()
    window = workspace.ParentWindow
    assert window.Size.Width == 320
    assert System.Object.ReferenceEquals(workspace, Rhino.UI.Panels.GetPanel(guid, doc))
    record('manual_narrow_width_and_cached_workspace_survive_close_reopen')
    window.Size = drawing.Size(640, window.Size.Height)
    initialized.SetValue(workspace, False)
    apply.Invoke(workspace, None)
    Rhino.RhinoApp.Wait()
    assert window.Size.Width == 640
    record('initial_policy_does_not_shrink_existing_wide_window')
    window.Size = drawing.Size(300, window.Size.Height)
    initialized.SetValue(workspace, False)
    apply.Invoke(workspace, None)
    Rhino.RhinoApp.Wait()
    assert window.Size.Width == 500 and workspace.Size.Width >= 480
    assert window.Size.Height == before['height'] and str(window.Location) == before['location']
    record('cold_narrow_policy_grows_outer_only_preserving_height_and_position')
    assert sorted(str(o.Id) for o in doc.Objects) == before['objects']
    assert str(doc.ModelUnitSystem) == before['units']
    checks.append('objects_and_units_unchanged')
    # An ordinary Eto form containing a workspace clone is not Rhino's panel.
    clone = System.Activator.CreateInstance(workspace.GetType())
    ordinary = forms.Form()
    ordinary.Content = clone
    ordinary.Size = drawing.Size(320, 500)
    try:
        ordinary.Show()
        Rhino.RhinoApp.Wait()
        assert ordinary.Size.Width == 320
        clone.GetType().GetMethod('EnsureInitialFloatingWidth', flags).Invoke(clone, None)
        Rhino.RhinoApp.Wait()
        assert ordinary.Size.Width == 320
        checks.append('ordinary_form_with_unregistered_workspace_clone_is_not_resized')
    finally:
        ordinary.Close()
        ordinary.Dispose()
    report = {'version': '0.10.5', 'pid': identity['pid'], 'slot': identity['slot'],
              'passed': len(checks), 'cases': checks, 'sizes': sizes,
              'native_docking': 'NOT_TESTED: prior 0.10.4 OpenPanelAsSibling failed (home_0104/floating_width_attempt1.json)',
              'scope': 'Real Rhino floating form; public Eto Window.Size. Full dock/theme/keyboard/dialog QA remains separate.'}
    json.dump(report, open(os.path.join(root, 'docs/evidence/home_0105/floating_width_checks.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False))
finally:
    if len(checks) < 7:
        json.dump({'passed_before_failure': len(checks), 'cases': checks, 'sizes': sizes}, open(os.path.join(root, 'docs/evidence/home_0105/floating_width_partial.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    if not isinstance(workspace.ParentWindow, forms.Form):
        Rhino.UI.Panels.FloatPanel(guid, Rhino.UI.Panels.FloatPanelMode.Show)
        Rhino.RhinoApp.Wait()
    if isinstance(workspace.ParentWindow, forms.Form):
        workspace.ParentWindow.Size = drawing.Size(500, before['height'])
    initialized.SetValue(workspace, True)
