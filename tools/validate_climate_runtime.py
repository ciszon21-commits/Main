"""Injected into formal release replay; independent original GH serialization."""
import clr,os,json,System
clr.AddReference('Grasshopper')
import Grasshopper as GH
from Grasshopper.Kernel.Parameters import Param_GenericObject
from Grasshopper.Kernel.Types import GH_ObjectWrapper
from Grasshopper.Kernel.Data import GH_Path
folder='C:/Program Files/ladybug_tools/grasshopper/ladybug_grasshopper/user_objects'
adapter=System.Reflection.Assembly.LoadFrom(os.path.join(root,'artifacts','releases','0.6.0','EnvironmentalHub.Adapters.dll'))
climate_type=adapter.GetType('EnvironmentalHub.Adapters.LadybugClimateFileAdapter')
def run_climate(request):return json.loads(climate_type.GetMethod('RunJson').Invoke(None,System.Array[System.Object]([json.dumps(request),folder])))
def stock_climate(path,fmt):
 d=GH.Kernel.GH_Document();d.Enabled=False
 try:
  def make(name):
   c=GH.Kernel.GH_UserObject(os.path.join(folder,name+'.ghuser')).InstantiateObject();c.CreateAttributes();d.AddObject(c,False);return c
  c=make('LB Import '+fmt);p=Param_GenericObject();p.CreateAttributes();p.PersistentData.Append(GH_ObjectWrapper(path),GH_Path(0));d.AddObject(p,False)
  c.Params.Input[0].AddSource(p);GH.Instances.DocumentServer.AddDocument(d);d.Enabled=True;d.NewSolution(False)
  if list(c.RuntimeMessages(GH.Kernel.GH_RuntimeMessageLevel.Error)):raise RuntimeError('Stock import failed')
  refs=[];items={}
  for output in c.Params.Output:
   data=list(output.VolatileData.AllData(True))
   if not data:items[(str(output.Name),-1)]={'Data':None,'EnergyPlusIdf':None};continue
   for i,goo in enumerate(data):
    native=goo.ScriptVariable()
    if native is None or isinstance(native,(str,bool,int,float)):
     items[(str(output.Name),i)]={'Data':native,'EnergyPlusIdf':None};continue
    source=Param_GenericObject();source.CreateAttributes();source.PersistentData.Append(GH_ObjectWrapper(native),GH_Path(0));d.AddObject(source,False)
    helper=make('LB Construct Location')
    # Test-only serializer in a disposable copy; installed component unmodified.
    helper.Code="import json\ndata=_name_.to_dict()\nlocation=json.dumps({'Data':data,'EnergyPlusIdf':_name_.to_idf() if data.get('type')=='DesignDay' else None})"
    helper.Params.Input[0].TypeHint=None
    helper.Params.Input[0].AddSource(source);refs.append((str(output.Name),i,helper))
  d.NewSolution(False)
  for name,i,h in refs:
   errors=list(h.RuntimeMessages(GH.Kernel.GH_RuntimeMessageLevel.Error))
   if errors:raise RuntimeError('Reference serializer failed: '+str(errors))
   output=next(o for o in h.Params.Output if o.Name=='location')
   items[(name,i)]=json.loads(str(list(output.VolatileData.AllData(True))[0].ScriptVariable()))
  return items
 finally:GH.Instances.DocumentServer.RemoveDocument(d);d.Dispose()
before=GH.Instances.DocumentServer.DocumentCount
climate_cases=[]
weather_root='C:/Program Files/ladybug_tools/resources/weather'
paths=[]
for city in ['Seattle','New.Delhi','Singapore']:
 matches=[os.path.join(base,f) for base,dirs,files in os.walk(weather_root) for f in files if f.endswith('.stat') and (city in f or city=='Singapore' and 'Changi' in f)]
 if not matches:raise RuntimeError('No reference weather for '+city)
 paths.append((city,matches[0]))
for city,stat in paths:
 for fmt,path in [('STAT',stat),('DDY',os.path.splitext(stat)[0]+'.ddy')]:
  original=stock_climate(path,fmt);result=run_climate({'Format':fmt,'FilePath':path})
  actual={(v['Output'],v['Index']):{'Data':v['Data'],'EnergyPlusIdf':v['EnergyPlusIdf']} for v in result['Outputs']}
  if actual!=original:
   differing=[str(k) for k in original if k not in actual or original[k]!=actual[k]]
   raise RuntimeError('Native outputs mismatch '+city+' '+fmt+': '+str(differing))
  if GH.Instances.DocumentServer.DocumentCount!=before:raise RuntimeError('GH leak')
  climate_cases.append({'case':city+'_'+fmt,'objects':len(actual),'all_native_json_and_idf_match':True})
  if city=='Seattle':
   json.dump(result,open(os.path.join(root,'samples','weather','import_'+fmt.lower()+'.json'),'w',encoding='utf-8'),indent=2)
bad=os.path.join(root,'artifacts','invalid_climate.stat')
with open(bad,'w') as f:f.write('not a STAT file')
for title,request,code in [('missing',{'Format':'DDY','FilePath':'missing.ddy'},'CLIMATE-FILE-001'),('extension',{'Format':'STAT','FilePath':paths[0][1].replace('.stat','.ddy')},'CLIMATE-FILE-001'),('format',{'Format':'EPW'},'CLIMATE-CONTRACT-001'),('null',None,'CLIMATE-CONTRACT-001'),('malformed',{'Format':'STAT','FilePath':bad},'CLIMATE-SOLVER-001')]:
 try:run_climate(request)
 except Exception as e:
  if code not in str(e):raise
  climate_cases.append({'case':title,'blocked':True,'code':code})
 else:raise RuntimeError('Invalid climate input accepted')
Rhino.RhinoApp.RunScript('EnvironmentalClimate',False)
climate_panel_id=System.Guid('499a99e8-8e73-4a6b-8208-fc879e413d36')
climate_panel=Rhino.UI.Panels.GetPanel(climate_panel_id)
stat_result=json.loads(climate_panel.ExecuteJson(json.dumps({'Format':'STAT','FilePath':paths[0][1]})))
selector=climate_panel.GetType().GetField('outputs',System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic).GetValue(climate_panel)
assert selector.Items.Count==len(stat_result['Outputs'])
design=next(i for i,o in enumerate(stat_result['Outputs']) if o['Kind']=='DesignDay');selector.SelectedIndex=design
assert 'Dry bulb max' in climate_panel.SummaryText
radiation_index=next(i for i,o in enumerate(stat_result['Outputs']) if 'values' in (o['Data'] or {}) and isinstance(o['Data'],dict));selector.SelectedIndex=radiation_index
assert '8760 values' in climate_panel.SummaryText
ddy_result=json.loads(climate_panel.ExecuteJson(json.dumps({'Format':'DDY','FilePath':paths[0][1].replace('.stat','.ddy')})))
previous=climate_panel.SummaryText
try:climate_panel.ExecuteJson(json.dumps({'Format':'STAT','FilePath':bad}))
except Exception:pass
else:raise RuntimeError('Panel accepted malformed STAT')
assert climate_panel.SummaryText==previous and 'Previous result retained' in climate_panel.StatusText
assert GH.Instances.DocumentServer.DocumentCount==before
report.update({'climate_cases':climate_cases,'climate_passed':len(climate_cases),'climate_panel_visible':Rhino.UI.Panels.IsPanelVisible(climate_panel_id),
 'climate_selector_verified':True,'climate_failure_preserves_result':True,'climate_gh_cleanup':True})
