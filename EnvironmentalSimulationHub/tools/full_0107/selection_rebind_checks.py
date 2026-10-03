"""Exercise public selection recovery and real native solve in the new owned Rhino."""
import os, json, System, Rhino
from System.Reflection import BindingFlags

root = 'I:/中興工程-工作區/00.DEVE-HOME/GIT-Base/Main/EnvironmentalSimulationHub'
identity = json.load(open(os.path.join(root, 'docs/evidence/full_0107/identity.json'), encoding='utf-8'))
doc = __rhino_doc__
assert System.Diagnostics.Process.GetCurrentProcess().Id == identity['pid']
assert doc.RuntimeSerialNumber == identity['document_serial'] and doc.Path in (None, '')
workspace = Rhino.UI.Panels.GetPanel(System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32'))
panel = workspace.GetModule(workspace.GetType().Assembly.GetType('EnvironmentalHub.Plugin.SunHoursPanel'))
assert str(panel.GetType().Assembly.GetName().Version) == '0.10.7.0'
flags = BindingFlags.Instance | BindingFlags.NonPublic
units = doc.ModelUnitSystem
objects = sorted(str(o.Id) for o in doc.Objects)
fixture = System.Guid.Empty
checks = []
try:
    mesh = Rhino.Geometry.Mesh()
    for x, y in [(0, 0), (1, 0), (1, 1), (0, 1)]:
        mesh.Vertices.Add(x, y, 0)
    mesh.Faces.AddFace(0, 1, 2, 3)
    fixture = doc.Objects.AddMesh(mesh)
    ids = System.Array[System.Guid]([fixture])
    empty = System.Array[System.Guid]([])
    request = {'GeometryIds': [str(fixture)], 'ContextIds': [], 'SunSource': {
        'Location': {'Name': 'Taipei', 'Latitude': 25.033, 'Longitude': 121.5654, 'TimeZone': 8},
        'HoursOfYear': [4116]}, 'TimeStepsPerHour': 1, 'GridMetres': 1, 'OffsetMetres': 0.1,
        'GeometryBlocks': True, 'CpuCount': 1, 'AcceptWarnings': True}
    result = json.loads(panel.ExecuteJson(json.dumps(request)))
    assert result['Statistics']['Count'] == 1 and result['Statistics']['Mean'] == 1
    checks.append('initial_native_solve_one_face_one_hour')
    previous = panel.CompletedResultJson
    doc.AdjustModelUnitSystem(Rhino.UnitSystem.Meters if units != Rhino.UnitSystem.Meters else Rhino.UnitSystem.Millimeters, False)
    try:
        panel.ExecuteJson(json.dumps(request))
        raise AssertionError('Stale selection unexpectedly solved')
    except System.InvalidOperationException as exc:
        assert 'SUNH-DOC-002' in str(exc)
    assert panel.CompletedResultJson == previous
    checks.append('unit_change_blocks_solve_and_preserves_completed_result')
    panel.SetGeometry(ids, empty)
    assert panel.CompletedResultJson == previous
    assert '前次結果' in panel.GetType().GetField('state', flags).GetValue(panel).Text
    checks.append('explicit_reselection_recovers_binding_keeps_previous_result_stale')
    recovered = json.loads(panel.ExecuteJson(json.dumps(request)))
    assert recovered['Statistics']['Mean'] == 1 and recovered['Metadata']['ModelUnits'] == str(doc.ModelUnitSystem)
    checks.append('native_solve_after_reselection_uses_new_model_units')
    before = list(panel.GetType().GetField('selected', flags).GetValue(panel))
    try:
        panel.SetGeometry(empty, None)
        raise AssertionError('Null context unexpectedly accepted')
    except System.ArgumentNullException:
        pass
    assert list(panel.GetType().GetField('selected', flags).GetValue(panel)) == before
    checks.append('failed_reselection_leaves_geometry_binding_unchanged')
    doc.AdjustModelUnitSystem(units, False)
    panel.SetGeometry(ids, empty)
    final = json.loads(panel.ExecuteJson(json.dumps(request)))
    assert final['Statistics']['Mean'] == 1 and final['Metadata']['ModelUnits'] == str(units)
    checks.append('original_units_can_be_reselected_and_solved_again')
finally:
    panel.DeletePreview()
    doc.AdjustModelUnitSystem(units, False)
    panel.SetGeometry(System.Array[System.Guid]([]), System.Array[System.Guid]([]))
    if fixture != System.Guid.Empty:
        doc.Objects.Delete(fixture, True)
    assert sorted(str(o.Id) for o in doc.Objects) == objects
    assert doc.ModelUnitSystem == units
    checks.append('owned_geometry_removed_and_original_document_units_restored')
report = {'version': '0.10.7', 'passed': len(checks), 'cases': checks, 'pid': identity['pid'],
          'document_serial': doc.RuntimeSerialNumber, 'scope': 'Real cached panel and stock solve after public SDK reselection; native picker and full UI remain pending'}
json.dump(report, open(os.path.join(root, 'docs/evidence/full_0107/selection_rebind_checks.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps(report))
