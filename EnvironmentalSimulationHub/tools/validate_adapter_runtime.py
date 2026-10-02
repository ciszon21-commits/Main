"""Compare the C# adapter with an independent copy of the stock GH definition.

Caller injects hub_root, adapter_dll and core_dll. Existing active GH is preserved.
"""
import os
import json
import copy
import clr
import System
import Rhino
clr.AddReference('Grasshopper')
import Grasshopper as GH
from Grasshopper.Kernel.Parameters import Param_GenericObject
from Grasshopper.Kernel.Types import GH_ObjectWrapper, GH_Brep
from Grasshopper.Kernel.Data import GH_Path
clr.AddReference(core_dll)
assembly = System.Reflection.Assembly.LoadFrom(adapter_dll)
adapter = assembly.GetType('EnvironmentalHub.Adapters.LadybugRadiationAdapter')
configuration = {'UserObjectDirectory': 'C:/Program Files/ladybug_tools/grasshopper/ladybug_grasshopper/user_objects',
                 'RadianceBinDirectory': 'C:/Program Files/ladybug_tools/radiance/bin'}
doc = __rhino_doc__
original = json.load(open(os.path.join(hub_root, 'samples', 'radiation_smoke', 'runtime_result.json'), encoding='utf-8'))
base = {'GeometryIds': [original['rhino_input_object_id']], 'WeatherFile': original['weather'],
        'OutputDirectory': os.path.join(hub_root, 'samples', 'adapter_validation', 'annual'),
        'GridMetres': 1, 'AcceptWarnings': True}

def invoke(method, request, config=configuration):
    return json.loads(adapter.GetMethod(method).Invoke(None, System.Array[System.Object](
        [doc, json.dumps(request), json.dumps(config)])))

def stock(request):
    io = GH.Kernel.GH_DocumentIO()
    if not io.Open(os.path.join(hub_root, 'docs', 'evidence', 'radiation_verified_checkpoint.gh')):
        raise RuntimeError('Stock workflow read failed')
    definition = io.Document
    definition.Enabled = False
    components = {o.Name: o for o in definition.Objects if isinstance(o, GH.Kernel.IGH_Component)}
    sky, radiation = components['LB Cumulative Sky Matrix'], components['LB Incident Radiation']
    def bind(component, name, values):
        p = next(p for p in component.Params.Input if p.Name == name)
        p.RemoveAllSources()
        q = Param_GenericObject()
        q.CreateAttributes()
        for value in values:
            q.PersistentData.Append(GH_ObjectWrapper(value), GH_Path(0))
        definition.AddObject(q, False)
        p.AddSource(q)
    scale = Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters, doc.ModelUnitSystem)
    geometry = next(o for o in definition.Objects if o.NickName.startswith('AnalysisGeometry'))
    geometry.PersistentData.Clear()
    for object_id in request['GeometryIds']:
        geometry.PersistentData.Append(GH_Brep(doc.Objects.FindId(System.Guid(object_id)).Geometry.DuplicateBrep()), GH_Path(0))
    bind(sky, 'north_', [request.get('NorthDegrees', 0)])
    if request.get('HoursOfYear'): bind(sky, '_hoys_', request['HoursOfYear'])
    output_folder = request['OutputDirectory'] + '_stock'
    os.makedirs(output_folder, exist_ok=True)
    bind(sky, '_folder_', [output_folder])
    bind(radiation, '_grid_size', [request['GridMetres'] * scale])
    if request.get('ContextIds'):
        bind(radiation, 'context_', [doc.Objects.FindId(System.Guid(g)).Geometry.DuplicateBrep() for g in request['ContextIds']])
    GH.Instances.DocumentServer.AddDocument(definition)
    try:
        definition.Enabled = True
        definition.NewSolution(True)
        errors = [str(e) for c in components.values() for e in c.RuntimeMessages(GH.Kernel.GH_RuntimeMessageLevel.Error)]
        if errors: raise RuntimeError(str(errors))
        p = next(p for p in radiation.Params.Output if p.Name == 'results')
        return [float(v.Value) for v in p.VolatileData.AllData(True)]
    finally:
        GH.Instances.DocumentServer.RemoveDocument(definition)
        definition.Dispose()

reports = []
temporary_ids = []
try:
    # A real Rhino Brep acting as a vertical context wall, 4m high at the east edge.
    scale = Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters, doc.ModelUnitSystem)
    wall_plane = Rhino.Geometry.Plane(Rhino.Geometry.Point3d(2 * scale, 0, 0), Rhino.Geometry.Vector3d.YAxis, Rhino.Geometry.Vector3d.ZAxis)
    wall = Rhino.Geometry.PlaneSurface(wall_plane, Rhino.Geometry.Interval(0, 4 * scale), Rhino.Geometry.Interval(0, 4 * scale)).ToBrep()
    wall_id = doc.Objects.AddBrep(wall)
    temporary_ids.append(wall_id)
    source = doc.Objects.FindId(System.Guid(base['GeometryIds'][0])).Geometry.DuplicateBrep()
    source.Transform(Rhino.Geometry.Transform.Scale(Rhino.Geometry.Point3d.Origin, 2))
    scaled_id = doc.Objects.AddBrep(source)
    temporary_ids.append(scaled_id)
    for name, changes in [('annual', {}), ('shaded_rotated_period', {'ContextIds': [str(wall_id)],
          'NorthDegrees': 90, 'HoursOfYear': list(range(4000, 4024))}),
          ('scaled_8m_grid_2m', {'GeometryIds': [str(scaled_id)], 'GridMetres': 2})]:
        request = dict(base, **changes)
        request['OutputDirectory'] = os.path.join(hub_root, 'samples', 'adapter_validation', name)
        reference = stock(request)
        result = invoke('RunJson', request)
        if len(reference) != len(result['Values']) or not reference: raise RuntimeError('Value count mismatch')
        difference = max(abs(a-b) for a,b in zip(reference, result['Values']))
        if difference > 1e-9: raise RuntimeError(name + ' differs from stock Ladybug')
        reports.append({'case': name, 'count': len(reference), 'max_absolute_difference': difference,
                        'stock_statistics': {'min': min(reference), 'max': max(reference), 'mean': sum(reference)/len(reference)},
                        'adapter_statistics': result['Statistics'], 'request': request,
                        'actual_solver': result['Metadata']['ActualGendaymtxExecutable']})
    # Prove execution gates block errors/warnings instead of writing solver outputs.
    for name, changes, expected in [('missing_geometry', {'GeometryIds': []}, 'RAD-INPUT-001'),
            ('missing_epw', {'WeatherFile': 'missing.epw'}, 'CLIMATE-EPW-003'),
            ('bad_grid', {'GridMetres': 0}, 'RAD-PARAM-001'),
            ('invalid_period', {'HoursOfYear': [8760]}, 'RAD-PERIOD-001'),
            ('unaccepted_warning', {'AcceptWarnings': False}, 'RAD-WARNING-001')]:
        request = dict(base, **changes)
        request['OutputDirectory'] = os.path.join(hub_root, 'samples', 'adapter_validation', 'blocked_' + name)
        try:
            invoke('RunJson', request)
            raise AssertionError(name + ' unexpectedly executed')
        except System.Reflection.TargetInvocationException as exc:
            if expected not in str(exc): raise
        if os.path.exists(request['OutputDirectory']): raise AssertionError('Blocked run wrote output')
        reports.append({'case': name, 'blocked': True, 'expected_code': expected})
finally:
    for object_id in temporary_ids: doc.Objects.Delete(object_id, True)
    doc.Views.Redraw()
path = os.path.join(hub_root, 'docs', 'evidence', 'adapter_runtime_validation.json')
with open(path, 'w', encoding='utf-8') as f: json.dump(reports, f, indent=2)
print(json.dumps({'passed': len(reports), 'report': path}))
