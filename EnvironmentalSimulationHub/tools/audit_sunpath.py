import os,json,clr,System
clr.AddReference('Grasshopper')
import Grasshopper as GH
from Grasshopper.Kernel.Parameters import Param_GenericObject
from Grasshopper.Kernel.Types import GH_ObjectWrapper
from Grasshopper.Kernel.Data import GH_Path
root='C:/Users/08432.SINOLTD/00.DEVE/31.AEC/RHINO_Deve/EnvironmentalSimulationHub'
folder='C:/Program Files/ladybug_tools/grasshopper/ladybug_grasshopper/user_objects'
d=GH.Kernel.GH_Document();d.Enabled=False
try:
 def make(name):
  c=GH.Kernel.GH_UserObject(os.path.join(folder,name+'.ghuser')).InstantiateObject();c.CreateAttributes();d.AddObject(c,False);return c
 def bind(c,name,values):
  p=Param_GenericObject();p.CreateAttributes()
  for v in values:p.PersistentData.Append(GH_ObjectWrapper(v),GH_Path(0))
  d.AddObject(p,False);next(i for i in c.Params.Input if i.Name==name).AddSource(p)
 loc=make('LB Construct Location');sun=make('LB SunPath')
 for k,v in [('_name_','Taipei'),('_latitude_',25.033),('_longitude_',121.5654),('_time_zone_',8)]:bind(loc,k,[v])
 next(i for i in sun.Params.Input if i.Name=='_location').AddSource(next(o for o in loc.Params.Output if o.Name=='location'))
 bind(sun,'hoys_',[0,4116,4122,4128]);bind(sun,'_scale_',[0.2])
 GH.Instances.DocumentServer.AddDocument(d);d.Enabled=True;d.NewSolution(False)
 report={'inputs':[{'name':p.Name,'description':p.Description} for p in sun.Params.Input], 'outputs':[],'errors':list(sun.RuntimeMessages(GH.Kernel.GH_RuntimeMessageLevel.Error)),'warnings':list(sun.RuntimeMessages(GH.Kernel.GH_RuntimeMessageLevel.Warning)),'code':sun.Code}
 for p in sun.Params.Output:
  vals=[x.ScriptVariable() for x in p.VolatileData.AllData(True)]
  report['outputs'].append({'name':p.Name,'count':len(vals),'types':list(set(str(type(x)) for x in vals)),'sample':[str(x) for x in vals[:4]],'description':p.Description})
 json.dump(report,open(os.path.join(root,'docs/evidence/sunpath_native_audit.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
 print(json.dumps({k:v for k,v in report.items() if k!='code'},ensure_ascii=False))
finally:GH.Instances.DocumentServer.RemoveDocument(d);d.Dispose()
