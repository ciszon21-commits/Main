import System, Rhino
assert System.Diagnostics.Process.GetCurrentProcess().Id == 29180, 'Wrong Rhino process'
assert __rhino_doc__.RuntimeSerialNumber == 268435457, 'Wrong test document'
assert __rhino_doc__.Path in (None, ''), 'Only the owned unsaved test document is allowed'
"""Owned visual fixture with real shade/unshaded snapshots; native numerical outputs only."""
import os, json, System, Rhino
root = 'I:/中興工程-工作區/00.DEVE-HOME/GIT-Base/Main/EnvironmentalSimulationHub'
doc = __rhino_doc__
assert doc.RuntimeSerialNumber == json.load(open(os.path.join(root, 'docs/evidence/home_0102/runtime/platform_0101_runtime.json'), encoding='utf-8'))['document_serial']
Rhino.RhinoApp.RunScript('EnvironmentalSunHours', False)
workspace = Rhino.UI.Panels.GetPanel(System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32'))
panel = workspace.GetModule(workspace.GetType().Assembly.GetType('EnvironmentalHub.Plugin.SunHoursPanel'))
scale = Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters, doc.ModelUnitSystem)
plane = Rhino.Geometry.PlaneSurface(Rhino.Geometry.Plane.WorldXY, Rhino.Geometry.Interval(0, 8 * scale), Rhino.Geometry.Interval(0, 8 * scale)).ToBrep()
ground = doc.Objects.AddBrep(plane)
plane.Dispose()
canopy = Rhino.Geometry.Box(Rhino.Geometry.Plane.WorldXY, Rhino.Geometry.Interval(0, 4 * scale), Rhino.Geometry.Interval(0, 8 * scale), Rhino.Geometry.Interval(2.5 * scale, 2.8 * scale)).ToBrep()
shade = doc.Objects.AddBrep(canopy)
canopy.Dispose()
request = {'GeometryIds': [str(ground)], 'ContextIds': [], 'SunSource': {'Location': {'Name': '臺北', 'Latitude': 25.033, 'Longitude': 121.5654, 'TimeZone': 8}, 'HoursOfYear': list(range(4110, 4123))}, 'GridMetres': 0.5, 'OffsetMetres': 0.1, 'CpuCount': 1, 'TimeStepsPerHour': 1, 'GeometryBlocks': True, 'AcceptWarnings': True}
panel.SetDisplayOffset(0.002)
a = json.loads(panel.ExecuteJson(json.dumps(request)))
first = panel.ScenarioCount
panel.SaveScenario('視覺示範 · 無遮蔭')
request['ContextIds'] = [str(shade)]
b = json.loads(panel.ExecuteJson(json.dumps(request)))
panel.SaveScenario('視覺示範 · 遮蔭')
panel.CompareScenarios(first, first + 1)
panel.SetTargetRange(2, 8)
assert len(set(b['Values'])) > 5 and b['Statistics']['Count'] == 256
dest = os.path.join(root, 'samples/home_0102/sunhours_visual_0101')
os.makedirs(dest, exist_ok=True)
json.dump(b, open(os.path.join(dest, 'native_result.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump({'version': '0.10.2', 'document_serial': doc.RuntimeSerialNumber, 'geometry': [str(ground), str(shade)], 'unshaded': a['Statistics'], 'shaded': b['Statistics'], 'native_colors': len(set((c for m in b['ResultMesh'] for c in m['VertexColorsArgb']))), 'scope': 'Owned Taipei sample, June 21 hourly 06:00 through 18:00 inclusive; not a project or compliance result.'}, open(os.path.join(root, 'docs/evidence/home_0102/runtime/sunhours_0101_visual_fixture.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps(b['Statistics']))