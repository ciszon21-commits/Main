"""Run in a dedicated EMPTY Rhino slot. Inject hub_root. Original stock workflow
is independently bound; temporary geometry and model units are restored.
"""
import os,json,uuid,shutil
import System,Rhino,clr
clr.AddReference('Grasshopper')
import Grasshopper as GH
from Grasshopper.Kernel.Parameters import Param_GenericObject
from Grasshopper.Kernel.Types import GH_ObjectWrapper
from Grasshopper.Kernel.Data import GH_Path
runtime=os.path.join(hub_root,'artifacts','releases','0.3.0')
System.Reflection.Assembly.LoadFrom(os.path.join(runtime,'EnvironmentalHub.Core.dll'))
assembly=System.Reflection.Assembly.LoadFrom(os.path.join(runtime,'EnvironmentalHub.Adapters.dll'))
adapter=assembly.GetType('EnvironmentalHub.Adapters.LadybugRadiationAdapter')
doc=__rhino_doc__
if any(not o.IsDeleted for o in doc.Objects):raise RuntimeError('Dedicated empty test document required')
original_units=doc.ModelUnitSystem
original_modified=doc.Modified
original_documents=GH.Instances.DocumentServer.DocumentCount
config={'UserObjectDirectory':'C:/Program Files/ladybug_tools/grasshopper/ladybug_grasshopper/user_objects','RadianceBinDirectory':'C:/Program Files/ladybug_tools/radiance/bin'}
weather=json.load(open(os.path.join(hub_root,'samples','radiation_smoke','runtime_result.json'),encoding='utf-8'))['weather']
run_root=os.path.join(hub_root,'samples','reliability_validation',uuid.uuid4().hex)
reports=[]
owned=[]
def invoke(name,request,configuration=config):
 return json.loads(adapter.GetMethod(name).Invoke(None,System.Array[System.Object]([doc,json.dumps(request),json.dumps(configuration)])))
def request(ids,name,**extra):
 r={'GeometryIds':[str(i) for i in ids],'WeatherFile':weather,'OutputDirectory':os.path.join(run_root,name),'GridMetres':1,'AcceptWarnings':True}
 r.update(extra);return r

def stock(r):
 io=GH.Kernel.GH_DocumentIO()
 if not io.Open(os.path.join(hub_root,'docs','evidence','radiation_verified_checkpoint.gh')):raise RuntimeError('Stock read failed')
 definition=io.Document;definition.Enabled=False
 snapshots=[]
 try:
  components={o.Name:o for o in definition.Objects if isinstance(o,GH.Kernel.IGH_Component)}
  epw=components['LB Import EPW'];sky=components['LB Cumulative Sky Matrix'];rad=components['LB Incident Radiation']
  def bind(c,name,values):
   target=next(p for p in c.Params.Input if p.Name==name);target.RemoveAllSources()
   param=Param_GenericObject();param.CreateAttributes()
   for v in values:param.PersistentData.Append(GH_ObjectWrapper(v),GH_Path(0))
   definition.AddObject(param,False);target.AddSource(param)
  def geometry(ids):
   result=[doc.Objects.FindId(System.Guid(i)).Geometry.Duplicate() for i in ids];snapshots.extend(result);return result
  scale=Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters,doc.ModelUnitSystem)
  os.makedirs(r['OutputDirectory']+'_stock',exist_ok=True)
  bind(epw,'_epw_file',[r['WeatherFile']]);bind(sky,'north_',[r.get('NorthDegrees',0)])
  bind(sky,'_hoys_',r.get('HoursOfYear',[]));bind(sky,'_folder_',[r['OutputDirectory']+'_stock'])
  bind(rad,'_geometry',geometry(r['GeometryIds']));bind(rad,'context_',geometry(r.get('ContextIds',[])))
  bind(rad,'_grid_size',[r['GridMetres']*scale]);bind(rad,'_offset_dist_',[0.1*scale]);bind(rad,'_cpu_count_',[1]);bind(rad,'_run',[True])
  GH.Instances.DocumentServer.AddDocument(definition);definition.Enabled=True;definition.NewSolution(False)
  errors=[str(e) for c in components.values() for e in c.RuntimeMessages(GH.Kernel.GH_RuntimeMessageLevel.Error)]
  if errors:raise RuntimeError(str(errors))
  output=next(p for p in rad.Params.Output if p.Name=='results')
  return [float(v.ScriptVariable()) for v in output.VolatileData.AllData(True)]
 finally:
  GH.Instances.DocumentServer.RemoveDocument(definition);definition.Dispose()
  for g in snapshots:g.Dispose()
def add(geometry):
 try:
  i=doc.Objects.AddMesh(geometry) if isinstance(geometry,Rhino.Geometry.Mesh) else doc.Objects.AddBrep(geometry)
  if i==System.Guid.Empty:raise RuntimeError('Fixture insertion failed')
  owned.append(i);return i
 finally:geometry.Dispose()
def clear():
 for i in owned:doc.Objects.Delete(i,True)
 owned.clear()
def compare(name,r):
 before=GH.Instances.DocumentServer.DocumentCount
 reference=stock(r);result=invoke('RunJson',r)
 if not reference or len(reference)!=len(result['Values']):raise RuntimeError(name+' value count mismatch')
 delta=max(abs(a-b) for a,b in zip(reference,result['Values']))
 if delta>1e-9:raise RuntimeError(name+' stock mismatch '+str(delta))
 if GH.Instances.DocumentServer.DocumentCount!=before:raise RuntimeError('GH document leaked')
 reports.append({'case':name,'units':str(doc.ModelUnitSystem),'count':len(reference),'max_absolute_difference':delta,'mean':result['Statistics']['Mean'],'gh_cleanup':True})
 return result
try:
 baselines=[]
 for units in [Rhino.UnitSystem.Meters,Rhino.UnitSystem.Centimeters,Rhino.UnitSystem.Millimeters]:
  doc.ModelUnitSystem=units
  s=Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters,units)
  plane=Rhino.Geometry.PlaneSurface(Rhino.Geometry.Plane.WorldXY,Rhino.Geometry.Interval(0,4*s),Rhino.Geometry.Interval(0,4*s))
  i=add(plane.ToBrep());plane.Dispose()
  name='units_'+str(units)
  result=compare(name,request([i],name))
  if abs(result['Statistics']['Mean']-1233.3471168086037)>1e-9:raise RuntimeError('Physical units changed baseline')
  baselines.append(result['Values']);clear()
 if max(abs(a-b) for a,b in zip(baselines[0],baselines[2]))>1e-9:raise RuntimeError('Unit invariance failed')
 doc.ModelUnitSystem=Rhino.UnitSystem.Meters
 box=Rhino.Geometry.BoundingBox(Rhino.Geometry.Point3d(0,0,0),Rhino.Geometry.Point3d(4,4,3)).ToBrep()
 mesh=Rhino.Geometry.Mesh()
 for xyz in [(5,0,0),(9,0,0),(9,4,2),(5,4,1)]:mesh.Vertices.Add(*xyz)
 mesh.Faces.AddFace(0,1,2);mesh.Faces.AddFace(0,2,3);mesh.Normals.ComputeNormals()
 box_id=add(box);mesh_id=add(mesh)
 wall=Rhino.Geometry.BoundingBox(Rhino.Geometry.Point3d(10,-1,0),Rhino.Geometry.Point3d(10.3,6,5)).ToBrep()
 wall_id=add(wall)
 r=request([box_id,mesh_id],'mixed_brep_mesh',ContextIds=[str(wall_id)],HoursOfYear=list(range(4000,4024)),NorthDegrees=35)
 compare('mixed_brep_mesh',r)
 # Existing but corrupted user-object files pass availability and fail construction.
 corrupt=os.path.join(run_root,'corrupt_user_objects');os.makedirs(corrupt)
 for name in ['LB Import EPW','LB Cumulative Sky Matrix','LB Incident Radiation']:
  open(os.path.join(corrupt,name+'.ghuser'),'w',encoding='utf-8').write('Invalid GH archive for deliberate failure injection')
 broken=dict(config,UserObjectDirectory=corrupt)
 if not invoke('PreflightJson',r,broken)['CanRun']:raise RuntimeError('Construction fixture did not pass availability gate')
 before=GH.Instances.DocumentServer.DocumentCount
 failed=False
 try:invoke('RunJson',dict(r,OutputDirectory=os.path.join(run_root,'construction_failure')),broken)
 except System.Reflection.TargetInvocationException:failed=True
 if not failed or GH.Instances.DocumentServer.DocumentCount!=before:raise RuntimeError('Construction failure cleanup failed')
 reports.append({'case':'corrupt_user_object','failed_as_expected':True,'gh_cleanup':True})
 # The genuine disabled-solver execution guard must leave no solver output.
 enabled=GH.Kernel.GH_Document.EnableSolutions
 try:
  GH.Kernel.GH_Document.EnableSolutions=False
  blocked=request([box_id],'disabled_solver')
  try:invoke('RunJson',blocked);raise RuntimeError('Disabled solver executed')
  except System.Reflection.TargetInvocationException as e:
   if 'RAD-GH-001' not in str(e):raise
  if os.path.exists(blocked['OutputDirectory']):raise RuntimeError('Blocked solver created output')
 finally:GH.Kernel.GH_Document.EnableSolutions=enabled
 reports.append({'case':'disabled_solver','expected_code':'RAD-GH-001','no_output':True})
finally:
 clear();doc.ModelUnitSystem=original_units;doc.Modified=original_modified;doc.Views.Redraw()
if GH.Instances.DocumentServer.DocumentCount!=original_documents:raise RuntimeError('GH document count not restored')
report={'release':'0.3.0','passed':len(reports),'cases':reports,'units_restored':str(doc.ModelUnitSystem),'active_fixture_objects_remaining':sum(1 for o in doc.Objects if not o.IsDeleted),'output_root':run_root,'limits':'Small deterministic fixtures; no large-model or full solver crash coverage.'}
with open(os.path.join(hub_root,'docs','evidence','radiation_reliability_validation.json'),'w',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
