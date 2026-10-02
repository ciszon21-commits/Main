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
import time
try:
 doc.ModelUnitSystem=Rhino.UnitSystem.Meters
 plane=Rhino.Geometry.PlaneSurface(Rhino.Geometry.Plane.WorldXY,Rhino.Geometry.Interval(0,32),Rhino.Geometry.Interval(0,32))
 geometry_id=add(plane.ToBrep());plane.Dispose()
 r=request([geometry_id],'scale_4096',GridMetres=0.5)
 start=time.monotonic();result=compare('scale_4096',r)
 if len(result['Values'])!=4096:raise RuntimeError('Expected 4096 cells')
 reports[-1]['stock_and_adapter_seconds']=time.monotonic()-start
 reports[-1]['adapter_seconds']=result['ExecutionTimeSeconds']
 # Real Radiance files, relocated only inside the ignored test work directory.
 relocated=os.path.join(run_root,'relocated_radiance');os.makedirs(relocated)
 for name in ['gendaymtx.exe','rtrace.exe']:shutil.copyfile(os.path.join(config['RadianceBinDirectory'],name),os.path.join(relocated,name))
 mismatch=dict(config,RadianceBinDirectory=relocated)
 failed_request=request([geometry_id],'solver_provenance_failure',GridMetres=2,HoursOfYear=list(range(4000,4024)))
 before=GH.Instances.DocumentServer.DocumentCount
 rejected=False
 try:invoke('RunJson',failed_request,mismatch)
 except System.Reflection.TargetInvocationException as e:
  if 'RAD-SOLVER-005' not in str(e):raise
  rejected=True
 if not rejected or GH.Instances.DocumentServer.DocumentCount!=before:raise RuntimeError('Post-solve failure leaked')
 if os.path.exists(os.path.join(failed_request['OutputDirectory'],'analysis_result.json')):raise RuntimeError('Rejected solve exported a result')
 reports.append({'case':'post_solve_provenance_failure','expected_code':'RAD-SOLVER-005','gh_cleanup':True,'result_json_absent':True})
finally:
 clear();doc.ModelUnitSystem=original_units;doc.Modified=original_modified;doc.Views.Redraw()
if GH.Instances.DocumentServer.DocumentCount!=original_documents:raise RuntimeError('GH document count not restored')
report={'release':'0.3.0','passed':len(reports),'cases':reports,'active_fixture_objects_remaining':sum(1 for o in doc.Objects if not o.IsDeleted),'output_root':run_root,'limits':'4096 cells on one flat surface; not full-project capacity or external solver crash certification.'}
with open(os.path.join(hub_root,'docs','evidence','radiation_scale_validation.json'),'w',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
