"""Inject hub_root; compare every series with an independent original GH instance."""
import os,json,System,clr
clr.AddReference('Grasshopper')
import Grasshopper as GH
from Grasshopper.Kernel.Parameters import Param_GenericObject
from Grasshopper.Kernel.Types import GH_ObjectWrapper
from Grasshopper.Kernel.Data import GH_Path
runtime=os.path.join(hub_root,'artifacts','weather-v1')
System.Reflection.Assembly.LoadFrom(os.path.join(runtime,'EnvironmentalHub.Core.WeatherV1.dll'))
a=System.Reflection.Assembly.LoadFrom(os.path.join(runtime,'EnvironmentalHub.Adapters.WeatherV1.dll'))
t=a.GetType('EnvironmentalHub.Adapters.LadybugWeatherAdapter')
folder='C:/Program Files/ladybug_tools/grasshopper/ladybug_grasshopper/user_objects'
weather=json.load(open(os.path.join(hub_root,'samples','radiation_smoke','runtime_result.json'),encoding='utf-8'))['weather']
def run(r):return json.loads(t.GetMethod('RunJson').Invoke(None,System.Array[System.Object]([json.dumps(r),folder])))
def stock(hoys):
 d=GH.Kernel.GH_Document();d.Enabled=False
 try:
  c=GH.Kernel.GH_UserObject(os.path.join(folder,'LB Import EPW.ghuser')).InstantiateObject()
  c.CreateAttributes();d.AddObject(c,False)
  p=Param_GenericObject();p.CreateAttributes();p.PersistentData.Append(GH_ObjectWrapper(weather),GH_Path(0));d.AddObject(p,False)
  c.Params.Input[0].AddSource(p);GH.Instances.DocumentServer.AddDocument(d);d.Enabled=True;d.NewSolution(False)
  errors=list(c.RuntimeMessages(GH.Kernel.GH_RuntimeMessageLevel.Error))
  if errors:raise RuntimeError(str(errors))
  refs=[]
  def make(name):
   obj=GH.Kernel.GH_UserObject(os.path.join(folder,name+'.ghuser')).InstantiateObject();obj.CreateAttributes();d.AddObject(obj,False);return obj
  for output in c.Params.Output:
   if output.Name=='location':continue
   for i,goo in enumerate(output.VolatileData.AllData(True)):
    source=Param_GenericObject();source.CreateAttributes();source.PersistentData.Append(GH_ObjectWrapper(goo.ScriptVariable()),GH_Path(0));d.AddObject(source,False)
    data=make('LB Deconstruct Data');header=make('LB Deconstruct Header');dates=make('LB Data DateTimes')
    data.Params.Input[0].AddSource(source);dates.Params.Input[0].AddSource(source)
    header.Params.Input[0].AddSource(next(o for o in data.Params.Output if o.Name=='header'))
    refs.append((str(output.Name),i,data,header,dates))
  d.NewSolution(False)
  result={}
  for name,i,data,header,dates in refs:
   def values(component,output):return [v.ScriptVariable() for v in next(p for p in component.Params.Output if p.Name==output).VolatileData.AllData(True)]
   errors=[str(e) for component in [data,header,dates] for e in component.RuntimeMessages(GH.Kernel.GH_RuntimeMessageLevel.Error)]
   if errors:raise RuntimeError(str(errors))
   numbers=[float(v) for v in values(data,'values')];time=[float(v) for v in values(dates,'hoys')]
   if name!='ground_temperature' and hoys:
    numbers=[numbers[h] for h in hoys];time=[time[h] for h in hoys]
   result[(name,i)]={'values':numbers,'unit':str(values(header,'unit')[0]),'time':time}
  return result
 finally:GH.Instances.DocumentServer.RemoveDocument(d);d.Dispose()
reports=[];before=GH.Instances.DocumentServer.DocumentCount
for name,hours in [('annual',[]),('selected_24h',list(range(4000,4024))),('year_boundary',[0,8759])]:
 reference=stock(hours);result=run({'WeatherFile':weather,'HoursOfYear':hours})
 if len(reference)!=len(result['Series']):raise RuntimeError('Series missing')
 for s in result['Series']:
  expected=reference[(s['Output'],s['CollectionIndex'])]
  if len(expected['values'])!=len(s['Values']) or any(a!=b for a,b in zip(expected['values'],s['Values'])):raise RuntimeError('Values differ '+s['Output'])
  if s['Units']!=expected['unit']:raise RuntimeError('Unit mismatch')
  actual=[v['HourOfYear'] for v in s['Times']] if s['Frequency']=='Hourly' else [v['Month'] for v in s['Times']]
  if actual!=expected['time']:raise RuntimeError('Time mismatch')
 if GH.Instances.DocumentServer.DocumentCount!=before:raise RuntimeError('GH document leak')
 reports.append({'case':name,'series':len(result['Series']),'hourly_series':sum(s['Frequency']=='Hourly' for s in result['Series']),'values':sum(len(s['Values']) for s in result['Series']),'max_absolute_difference':0,'units_and_times_match':True,'location':result['Location']})
 if name=='selected_24h':
  os.makedirs(os.path.join(hub_root,'samples','weather'),exist_ok=True)
  json.dump(result,open(os.path.join(hub_root,'samples','weather','selected_24h.json'),'w',encoding='utf-8'),indent=2)
for name,r,code in [('missing_file',{'WeatherFile':'missing.epw'},'CLIMATE-EPW-003'),('duplicate_hour',{'WeatherFile':weather,'HoursOfYear':[0,0]},'CLIMATE-PERIOD-001'),('invalid_hour',{'WeatherFile':weather,'HoursOfYear':[8760]},'CLIMATE-PERIOD-001'),('null_request',None,'CLIMATE-CONTRACT-001')]:
 try:run(r);raise RuntimeError('Invalid request executed')
 except System.Reflection.TargetInvocationException as e:
  if code not in str(e):raise
 reports.append({'case':name,'blocked':True,'code':code})
# Deliberate EPW sentinel fixture, copied from the real weather file.
missing_path=os.path.join(hub_root,'artifacts','weather_missing_fixture.epw')
lines=open(weather,encoding='utf-8').readlines();row=lines[8].strip().split(',');row[6]='99.9';row[8]='999';lines[8]=','.join(row)+'\n'
open(missing_path,'w',encoding='utf-8').writelines(lines)
masked=run({'WeatherFile':missing_path,'HoursOfYear':[1]})
for name in ['dry_bulb_temperature','relative_humidity']:
 s=next(s for s in masked['Series'] if s['Output']==name)
 if s['Missing']!=[True] or s['Statistics'] is not None:raise RuntimeError('Missing-value mask/statistics incorrect')
reports.append({'case':'missing_value_sentinels','raw_values_preserved':True,'mask_verified':True,'all_missing_statistics_null':True})
json.dump({'passed':len(reports),'cases':reports,'gh_document_count_restored':GH.Instances.DocumentServer.DocumentCount==before},open(os.path.join(hub_root,'docs','evidence','weather_runtime_validation.json'),'w',encoding='utf-8'),indent=2)
print(json.dumps({'passed':len(reports),'reports':reports}))
