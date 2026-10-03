"""Persist only the owned SunHours sample and verify exported native data."""
import os, json, sys, System, Rhino
root = 'I:/中興工程-工作區/00.DEVE-HOME/GIT-Base/Main/EnvironmentalSimulationHub'
doc = __rhino_doc__
workspace = Rhino.UI.Panels.GetPanel(System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32'))
panel = workspace.GetModule(workspace.GetType().Assembly.GetType('EnvironmentalHub.Plugin.SunHoursPanel'))
folder = os.path.join(root, 'samples/home_0102/visual_sunhours_0102')
os.makedirs(folder, exist_ok=True)
result_path = os.path.join(folder, 'result_with_presentation.json')
comparison_path = os.path.join(folder, 'comparison.json')
result_json = panel.ExportResultJson()
comparison_json = panel.ExportComparisonJson()
with open(result_path, 'w', encoding='utf-8') as stream:
    stream.write(result_json)
with open(comparison_path, 'w', encoding='utf-8') as stream:
    stream.write(comparison_json)
exported = json.load(open(result_path, encoding='utf-8'))
assert exported['NativeResult'] == json.loads(panel.CompletedResultJson)
assert exported['Presentation']['DisplayOffsetMetres'] == .002
comparison = json.load(open(comparison_path, encoding='utf-8'))
assert len(comparison['Scenarios']) >= 2 and comparison['Metric'] == 'Arithmetic point mean, not area weighted'
fixture = json.load(open(os.path.join(root, 'docs/evidence/home_0102/runtime/sunhours_0101_visual_fixture.json'), encoding='utf-8'))
model = Rhino.FileIO.File3dm()
try:
    model.Settings.ModelUnitSystem = doc.ModelUnitSystem
    model.Settings.ModelAbsoluteTolerance = doc.ModelAbsoluteTolerance
    layer = Rhino.DocObjects.Layer()
    layer.Name = '日照時數示範'
    model.AllLayers.Add(layer)
    ids = [System.Guid(v) for v in fixture['geometry']]
    objects = [doc.Objects.FindId(v) for v in ids]
    objects += [o for o in doc.Objects if o.Attributes.GetUserString('EnvironmentalHub.PreviewOwner') == 'bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f/SunHours']
    assert all(o is not None for o in objects)
    for obj in objects:
        attributes = obj.Attributes.Duplicate()
        attributes.LayerIndex = 0
        model.Objects.Add(obj.Geometry, attributes)
    model_path = os.path.join(folder, 'sunhours_0102.3dm')
    assert model.Write(model_path, 8)
finally:
    model.Dispose()
readback = Rhino.FileIO.File3dm.Read(model_path)
try:
    assert len(list(readback.Objects)) == len(objects)
    assert readback.Settings.ModelUnitSystem == doc.ModelUnitSystem
finally:
    readback.Dispose()
info = {
    'version': '0.10.2', 'passed': 3,
    'cases': ['native_result_json_roundtrip', 'comparison_json_roundtrip', 'owned_3dm_roundtrip'],
    'runtime': str(System.Environment.Version), 'rhino': str(Rhino.RhinoApp.Version),
    'rhino_python': sys.version, 'document_serial': doc.RuntimeSerialNumber,
    'model_units': str(doc.ModelUnitSystem), 'objects_exported': len(objects),
    'eddy_loaded_assemblies': [{'name': a.GetName().Name, 'version': str(a.GetName().Version)}
                              for a in System.AppDomain.CurrentDomain.GetAssemblies()
                              if any(x in a.GetName().Name for x in ['Eddy3D', 'Provisioning', 'MetaFOAM'])],
    'paths': [model_path, result_path, comparison_path],
    'scope': 'Owned Taipei test fixture; native palette and physical result preserved; not a project or CFD validation'
}
json.dump(info, open(os.path.join(root, 'docs/evidence/home_0102/export_roundtrip.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps(info))
