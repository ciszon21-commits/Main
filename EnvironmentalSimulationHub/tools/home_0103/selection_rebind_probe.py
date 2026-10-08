"""Probe explicit geometry reselection after a unit change in the owned test doc."""
import json, os, System, Rhino
from System.Reflection import BindingFlags

assert System.Diagnostics.Process.GetCurrentProcess().Id == 29180
doc = __rhino_doc__
assert doc.RuntimeSerialNumber == 268435457 and doc.Path in (None, '')
root = 'I:/中興工程-工作區/00.DEVE-HOME/GIT-Base/Main/EnvironmentalSimulationHub'
flags = BindingFlags.Instance | BindingFlags.NonPublic
workspace = Rhino.UI.Panels.GetPanel(System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32'))
panel_type = workspace.GetType().Assembly.GetType('EnvironmentalHub.Plugin.SunHoursPanel')
panel = System.Activator.CreateInstance(panel_type)
units = doc.ModelUnitSystem
original_objects = sorted(str(obj.Id) for obj in doc.Objects)
fixture = System.Guid.Empty
report = {'version': str(panel_type.Assembly.GetName().Version), 'scope': 'Public SDK selection recovery; not native picker or full UI acceptance', 'cases': []}
try:
    mesh = Rhino.Geometry.Mesh()
    for x, y in [(0, 0), (1, 0), (1, 1), (0, 1)]:
        mesh.Vertices.Add(x, y, 0)
    mesh.Faces.AddFace(0, 1, 2, 3)
    fixture = doc.Objects.AddMesh(mesh)
    assert fixture != System.Guid.Empty
    ids = System.Array[System.Guid]([fixture])
    empty = System.Array[System.Guid]([])
    panel.SetGeometry(ids, empty)
    report['cases'].append('initial_geometry_selection_succeeds')
    changed_units = Rhino.UnitSystem.Meters if units != Rhino.UnitSystem.Meters else Rhino.UnitSystem.Millimeters
    doc.AdjustModelUnitSystem(changed_units, False)
    try:
        panel_type.GetMethod('RequireDocument', flags).Invoke(panel, None)
        raise AssertionError('Stale unit selection accepted')
    except System.Reflection.TargetInvocationException as exc:
        assert 'SUNH-DOC-002' in str(exc.InnerException)
    report['cases'].append('stale_unit_selection_remains_blocked')
    try:
        panel.SetGeometry(ids, empty)
        panel_type.GetMethod('RequireDocument', flags).Invoke(panel, None)
        assert panel_type.GetField('inputUnits', flags).GetValue(panel) == str(changed_units)
        report['reselection_after_units_change'] = 'PASS'
        report['cases'].append('explicit_geometry_reselection_recovers_current_document_units')
    except Exception as exc:
        report['reselection_after_units_change'] = 'FAIL'
        report['reselection_error'] = str(exc)
finally:
    doc.AdjustModelUnitSystem(units, False)
    if fixture != System.Guid.Empty:
        doc.Objects.Delete(fixture, True)
    panel.Dispose()
    assert sorted(str(obj.Id) for obj in doc.Objects) == original_objects
    assert doc.ModelUnitSystem == units
    report['cases'].append('test_units_and_geometry_restored')
    dest = os.path.join(root, 'docs/evidence/home_0103')
    os.makedirs(dest, exist_ok=True)
    json.dump(report, open(os.path.join(dest, 'selection_rebind_before.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps(report))
