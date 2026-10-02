import os,json,clr
clr.AddReference('Grasshopper')
import Grasshopper as GH
import Rhino
from Grasshopper.Kernel.Parameters import Param_GenericObject
from Grasshopper.Kernel.Types import GH_ObjectWrapper
from Grasshopper.Kernel.Data import GH_Path
root='C:/Users/08432.SINOLTD/00.DEVE/31.AEC/RHINO_Deve/EnvironmentalSimulationHub'
folder='C:/Program Files/ladybug_tools/grasshopper/ladybug_grasshopper/user_objects'
d=GH.Kernel.GH_Document();d.Enabled=False
try:
 c=GH.Kernel.GH_UserObject(os.path.join(folder,'LB Direct Sun Hours.ghuser')).InstantiateObject();c.CreateAttributes();d.AddObject(c,False)
 def bind(name,values):
  p=Param_GenericObject();p.CreateAttributes()
  for v in values:p.PersistentData.Append(GH_ObjectWrapper(v),GH_Path(0))
  d.AddObject(p,False);next(i for i in c.Params.Input if i.Name==name).AddSource(p)
 scale=Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters,__rhino_doc__.ModelUnitSystem)
 plate=Rhino.Geometry.PlaneSurface(Rhino.Geometry.Plane.WorldXY,Rhino.Geometry.Interval(0,4*scale),Rhino.Geometry.Interval(0,4*scale)).ToBrep()
 bind('_vectors',[Rhino.Geometry.Vector3d(0,0,-1),Rhino.Geometry.Vector3d(1,0,-1)])
 bind('_geometry',[plate]);bind('_grid_size',[scale]);bind('_timestep_',[2]);bind('_cpu_count_',[1]);bind('_run',[True])
 GH.Instances.DocumentServer.AddDocument(d);d.Enabled=True;d.NewSolution(False)
 report={'model_units':str(__rhino_doc__.ModelUnitSystem),'inputs':[{'name':p.Name,'description':p.Description,'optional':p.Optional} for p in c.Params.Input],'outputs':[],'errors':list(c.RuntimeMessages(GH.Kernel.GH_RuntimeMessageLevel.Error)),'warnings':list(c.RuntimeMessages(GH.Kernel.GH_RuntimeMessageLevel.Warning)),'code':c.Code}
 for p in c.Params.Output:
  vals=[x.ScriptVariable() for x in p.VolatileData.AllData(True)]
  report['outputs'].append({'name':p.Name,'count':len(vals),'types':list(set(str(type(x)) for x in vals)),'sample':[str(x) for x in vals[:4]],'description':p.Description})
 json.dump(report,open(os.path.join(root,'docs/evidence/sunhours_native_audit.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
 print(json.dumps({k:v for k,v in report.items() if k!='code'},ensure_ascii=False))
finally:GH.Instances.DocumentServer.RemoveDocument(d);d.Dispose()
