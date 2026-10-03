import System, Rhino
assert System.Diagnostics.Process.GetCurrentProcess().Id == 29180, 'Wrong Rhino process'
assert __rhino_doc__.RuntimeSerialNumber == 268435457, 'Wrong test document'
assert __rhino_doc__.Path in (None, ''), 'Only the owned unsaved test document is allowed'
"""Independent stock GH solve comparisons in the owned formal 0.10.2 Rhino slot."""
import os, json, clr, System, Rhino, math, hashlib
clr.AddReference('Grasshopper')
clr.AddReference('Eto')
import Grasshopper as GH
from Grasshopper.Kernel.Parameters import Param_GenericObject
from Grasshopper.Kernel.Types import GH_ObjectWrapper
from Grasshopper.Kernel.Data import GH_Path
from Eto.Forms import Button
root = 'I:/中興工程-工作區/00.DEVE-HOME/GIT-Base/Main/EnvironmentalSimulationHub'
folder = 'C:/Program Files/ladybug_tools/grasshopper/ladybug_grasshopper/user_objects'
release = os.path.join(root, 'artifacts/home-build/0.10.2')
plugin_id = System.Guid('bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f')
Rhino.PlugIns.PlugIn.LoadPlugIn(os.path.join(release, 'EnvironmentalHub.Plugin.rhp'))
plugin = Rhino.PlugIns.PlugIn.Find(plugin_id)
assert plugin is not None and str(plugin.GetType().Assembly.GetName().Version) == '0.10.2.0'
assert os.path.normcase(os.path.normpath(plugin.GetType().Assembly.Location)) == os.path.normcase(os.path.normpath(os.path.join(release, 'EnvironmentalHub.Plugin.rhp')))
Rhino.RhinoApp.RunScript('EnvironmentalSunPath', False)
workspace_id = System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32')
workspace = Rhino.UI.Panels.GetPanel(workspace_id)
panel = workspace.GetModule(plugin.GetType().Assembly.GetType('EnvironmentalHub.Plugin.SunPathPanel'))
doc = __rhino_doc__
assert doc == Rhino.RhinoDoc.ActiveDoc
assert len(list(doc.Objects)) == 0, 'Owned empty document required for SunPath acceptance'
flags = System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance
adapter = System.Reflection.Assembly.LoadFrom(os.path.join(release, 'EnvironmentalHub.Adapters.dll')).GetType('EnvironmentalHub.Adapters.LadybugSunPathAdapter').GetMethod('RunJson')

def run(r):
    return json.loads(adapter.Invoke(None, System.Array[System.Object]([json.dumps(r), folder])))

def stock(r):
    d = GH.Kernel.GH_Document()
    d.Enabled = False
    try:

        def make(name):
            c = GH.Kernel.GH_UserObject(os.path.join(folder, name + '.ghuser')).InstantiateObject()
            c.CreateAttributes()
            d.AddObject(c, False)
            return c

        def bind(c, name, vals):
            p = Param_GenericObject()
            p.CreateAttributes()
            for v in vals:
                p.PersistentData.Append(GH_ObjectWrapper(v), GH_Path(0))
            d.AddObject(p, False)
            next((i for i in c.Params.Input if i.Name == name)).AddSource(p)
        l = make('LB Construct Location')
        s = make('LB SunPath')
        for (k, v) in [('_name_', r['Location']['Name']), ('_latitude_', r['Location']['Latitude']), ('_longitude_', r['Location']['Longitude']), ('_time_zone_', r['Location']['TimeZone']), ('_elevation_', r['Location'].get('ElevationMetres', 0))]:
            bind(l, k, [v])
        next((i for i in s.Params.Input if i.Name == '_location')).AddSource(next((o for o in l.Params.Output if o.Name == 'location')))
        for (k, v) in [('hoys_', r['HoursOfYear']), ('north_', [r.get('NorthDegrees', 0)]), ('solar_time_', [r.get('SolarTime', False)]), ('_scale_', [r.get('RadiusMetres', 20) / 100]), ('daily_', [r.get('Daily', False)]), ('_center_pt_', [Rhino.Geometry.Point3d(*r.get('Center', [0, 0, 0]))])]:
            bind(s, k, v)
        if r.get('Projection', '3D') != '3D':
            bind(s, 'projection_', [r['Projection']])
        GH.Instances.DocumentServer.AddDocument(d)
        d.Enabled = True
        d.NewSolution(False)
        assert not list(s.RuntimeMessages(GH.Kernel.GH_RuntimeMessageLevel.Error))

        def vals(name):
            return [x.ScriptVariable() for x in next((p for p in s.Params.Output if p.Name == name)).VolatileData.AllData(True)]

        def xyz(p):
            return [p.X, p.Y, p.Z]
        curves = []
        texts = []
        for name in ['analemma', 'daily', 'compass', 'title']:
            for v in vals(name):
                if isinstance(v, Rhino.Geometry.Arc):
                    v = Rhino.Geometry.ArcCurve(v)
                elif isinstance(v, Rhino.Geometry.Circle):
                    v = v.ToNurbsCurve()
                if isinstance(v, Rhino.Geometry.Curve):
                    curves.append((name, v.DuplicateCurve()))
                else:
                    texts.append((name, v.m_value))
        return {'hoys': vals('hoys'), 'altitudes': vals('altitudes'), 'azimuths': vals('azimuths'), 'points': [xyz(p) for p in vals('sun_pts')], 'vectors': [xyz(p) for p in vals('vectors')], 'curves': curves, 'texts': texts}
    finally:
        GH.Instances.DocumentServer.RemoveDocument(d)
        d.Dispose()
base = {'Location': {'Name': '臺北', 'Latitude': 25.033, 'Longitude': 121.5654, 'TimeZone': 8}, 'HoursOfYear': [0, 4116, 4122, 4128], 'RadiusMetres': 20, 'Center': [0, 0, 0]}
cases = []
fixtures = {}
before = GH.Instances.DocumentServer.DocumentCount

def near(a, b):
    assert abs(a - b) < 1e-08, (a, b)
variants = [('taipei_day_night', {}), ('north_rotated', {'NorthDegrees': 90}), ('solar_time', {'SolarTime': True}), ('daily_arcs', {'Daily': True}), ('fractional_hoy', {'HoursOfYear': [4116.5, 4122.25]}), ('southern_hemisphere', {'Location': {'Name': 'Sydney', 'Latitude': -33.8688, 'Longitude': 151.2093, 'TimeZone': 10}}), ('polar_night', {'Location': {'Name': 'Tromso', 'Latitude': 69.6492, 'Longitude': 18.9553, 'TimeZone': 1}, 'HoursOfYear': [12]}), ('translated_center', {'Center': [100, -50, 12], 'RadiusMetres': 30})]
variants += [(p, {'Projection': p, 'Center': [10, 20, 5]}) for p in ['Orthographic', 'Stereographic', 'Equidistant', 'Equisolid']]
for (name, change) in variants:
    r = dict(base)
    r.update(change)
    a = run(r)
    b = stock(r)
    assert len(a['Positions']) == len(b['hoys'])
    for (i, p) in enumerate(a['Positions']):
        for (field, native) in [('HourOfYear', 'hoys'), ('AltitudeDegrees', 'altitudes'), ('AzimuthDegrees', 'azimuths')]:
            near(p[field], b[native][i])
        for (field, native) in [('SunPoint', 'points'), ('SunlightVector', 'vectors')]:
            for (x, y) in zip(p[field], b[native][i]):
                near(x, y)
    assert len(a['Curves']) == len(b['curves']) and len(a['Texts']) == len(b['texts'])
    for (serialized, (output, curve)) in zip(a['Curves'], b['curves']):
        assert serialized['Output'] == output
        restored = Rhino.Geometry.GeometryBase.FromJSON(serialized['GeometryJson'])
        assert restored.IsValid
        for t in [0, 0.25, 0.5, 0.75, 1]:
            near(restored.PointAtNormalizedLength(t).DistanceTo(curve.PointAtNormalizedLength(t)), 0)
        restored.Dispose()
        curve.Dispose()
    for (t, (output, native)) in zip(a['Texts'], b['texts']):
        assert t['Output'] == output and t['Text'] == native.Text
        near(t['Height'], native.Height)
        for (x, y) in zip(t['Origin'], [native.TextPlane.OriginX, native.TextPlane.OriginY, native.TextPlane.OriginZ]):
            near(x, y)
    fixtures[name] = a
    cases.append('stock_match:' + name)
    assert GH.Instances.DocumentServer.DocumentCount == before
units = doc.ModelUnitSystem
try:
    doc.ModelUnitSystem = Rhino.UnitSystem.Millimeters
    mm = run(dict(base, Center=[1000, 2000, 3000]))
    assert mm['MetresPerModelUnit'] == 0.001
    for p in mm['Positions']:
        near(Rhino.Geometry.Point3d(*p['SunPoint']).DistanceTo(Rhino.Geometry.Point3d(1000, 2000, 3000)), 20000)
    cases.append('native_millimetre_radius_conversion')
finally:
    doc.ModelUnitSystem = units
for (key, value) in [('HoursOfYear', []), ('HoursOfYear', [4116, 4116]), ('HoursOfYear', [8760]), ('HoursOfYear', [4116.0001]), ('RadiusMetres', 0), ('NorthDegrees', 361), ('Center', [0, 0]), ('Projection', 'unsupported'), ('Location', {'Name': 'invalid', 'Latitude': 91})]:
    bad = dict(base)
    bad[key] = value
    try:
        run(bad)
    except Exception:
        pass
    else:
        raise AssertionError('Invalid input accepted: ' + key)
    assert GH.Instances.DocumentServer.DocumentCount == before
    cases.append('validation:' + key + ':' + str(value))
sentinel = doc.Objects.AddPoint(Rhino.Geometry.Point3d(150, 150, 0))
completed = json.loads(panel.ExecuteJson(json.dumps(base)))
original = panel.CompletedResultJson
owned = [o.Id for o in doc.Objects if str(o.Attributes.Name).startswith('EnvironmentalHub / SunPath')]
assert len(owned) > len(completed['Curves'])
panel.LocateResult()
panel.LocateSun()
cases.append('owned_preview_native_geometry_and_viewport_locate')
try:
    panel.ExecuteJson(json.dumps(dict(base, RadiusMetres=0)))
except Exception:
    pass
else:
    raise AssertionError('Failed run accepted')
assert panel.CompletedResultJson == original and all((doc.Objects.FindId(i) is not None for i in owned)) and ('已保留前次結果' in panel.StatusText)
cases.append('invalid_run_preserves_result_and_preview')
enabled = GH.Kernel.GH_Document.EnableSolutions
try:
    GH.Kernel.GH_Document.EnableSolutions = False
    try:
        panel.ExecuteJson(json.dumps(base))
    except Exception:
        pass
    else:
        raise AssertionError('Disabled GH accepted')
    assert panel.CompletedResultJson == original and all((doc.Objects.FindId(i) is not None for i in owned))
    cases.append('disabled_solver_preserves_result_and_preview')
finally:
    GH.Kernel.GH_Document.EnableSolutions = enabled
panel.ExecuteJson(json.dumps(dict(base, Center=[20, 30, 2], RadiusMetres=30)))
assert all((doc.Objects.FindId(i) is None for i in owned)) and doc.Objects.FindId(sentinel) is not None
cases.append('replacement_deletes_only_previous_owned_preview')
panel.DeletePreview()
assert doc.Objects.FindId(sentinel) is not None and panel.CompletedResultJson is not None
assert len([o for o in doc.Objects if str(o.Attributes.Name).startswith('EnvironmentalHub / SunPath')]) == 0
cases.append('clear_preview_retains_result_and_user_model')
old_units = doc.ModelUnitSystem
try:
    doc.ModelUnitSystem = (Rhino.UnitSystem.Meters if old_units == Rhino.UnitSystem.Millimeters else Rhino.UnitSystem.Millimeters)
    try:
        panel.ExecuteJson(json.dumps(base))
    except Exception:
        pass
    else:
        raise AssertionError('Changed units accepted without rebind')
    cases.append('changed_units_require_explicit_rebind')
finally:
    doc.ModelUnitSystem = old_units
location = workspace.GetModule(plugin.GetType().Assembly.GetType('EnvironmentalHub.Plugin.LocationPanel'))
location.ExecuteJson(json.dumps({'Name': 'Sydney', 'Latitude': -33.8688, 'Longitude': 151.2093, 'TimeZone': 10}))
panel.UseCompletedLocation()
time = workspace.GetModule(plugin.GetType().Assembly.GetType('EnvironmentalHub.Plugin.TimePanel'))
time.ExecutePeriodJson(json.dumps({'StartMonth': 6, 'StartDay': 21, 'StartHour': 10, 'EndMonth': 6, 'EndDay': 21, 'EndHour': 12, 'TimeStep': 2}))
panel.UseCompletedTime()

def walk(c):
    yield c
    if hasattr(c, 'Controls'):
        for child in c.Controls:
            for v in walk(child):
                yield v
next((b for b in walk(panel) if isinstance(b, Button) and b.Text == '檢核並建立太陽路徑')).PerformClick()
transfer = json.loads(panel.CompletedResultJson)
assert transfer['Location']['City'] == 'Sydney' and 4114.5 in transfer['InputParameters']['HoursOfYear']
cases.append('same_workspace_completed_location_fractional_period_and_button')
time.ExecuteCalendarJson(json.dumps({'Month': 6, 'Day': 21, 'Hour': 12, 'Minute': 30}))
panel.UseCompletedTime()
next((b for b in walk(panel) if isinstance(b, Button) and b.Text == '檢核並建立太陽路徑')).PerformClick()
assert json.loads(panel.CompletedResultJson)['InputParameters']['HoursOfYear'] == [4116.5]
cases.append('same_workspace_completed_calendar_transfer')
panel.DeletePreview()
doc.Objects.Delete(sentinel, True)
final = json.loads(panel.ExecuteJson(json.dumps(dict(base, HoursOfYear=[4110, 4113, 4116, 4119, 4122]))))
assert GH.Instances.DocumentServer.DocumentCount == before
cases.append('all_gh_documents_cleaned')
for (name, value) in fixtures.items():
    path = os.path.join(root, 'samples/home_0102/sunpath_0101')
    os.makedirs(path, exist_ok=True)
    json.dump(value, open(os.path.join(path, name + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
report = {'version': '0.10.2', 'passed': len(cases), 'cases': cases, 'original_userobject_sha256': hashlib.sha256(open(os.path.join(folder, 'LB SunPath.ghuser'), 'rb').read()).hexdigest(), 'positions': final['Positions'], 'curve_count': len(final['Curves']), 'text_count': len(final['Texts']), 'scope': 'Independent installed original component numerical/geometric comparison; actual workspace button, ownership, document-unit guard; full Dock/theme/dialog/colleague-machine QA not claimed'}
json.dump(report, open(os.path.join(root, 'docs/evidence/home_0102/runtime/sunpath_0101_runtime.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps({'passed': len(cases), 'curve_count': len(final['Curves']), 'positions': len(final['Positions'])}))