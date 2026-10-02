import System,Rhino
workspace_id=System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32')
view_types={'7281a8f2-e2c4-4c27-bcb5-22cbb0688b32': 'HubOverviewPanel', '1c0c5ac3-b820-42f2-9aaa-1e0f50356d1a': 'WeatherPanel', '5f78d8d4-e9a1-4713-bb04-d08466339735': 'LocationPanel', '499a99e8-8e73-4a6b-8208-fc879e413d36': 'ClimateFilePanel', '06843693-df8a-421c-938b-96e2b9e88066': 'TimePanel', 'c62382ce-7709-4fcd-9dfb-447d1d8a08c0': 'RadiationPanel'}
def get_view(guid):
 workspace=Rhino.UI.Panels.GetPanel(workspace_id)
 return workspace.GetModule(workspace.GetType().Assembly.GetType('EnvironmentalHub.Plugin.'+view_types[str(guid)]))
import os,json,System,Rhino
from System.Reflection import BindingFlags
root='C:\\Users\\08432.SINOLTD\\00.DEVE\\31.AEC\\RHINO_Deve\\EnvironmentalSimulationHub'
path=os.path.join(root,'artifacts','releases','0.8.7','EnvironmentalHub.Plugin.rhp')
guid=System.Guid('bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f')
plugin=Rhino.PlugIns.PlugIn.Find(guid)
if plugin is None:
 Rhino.PlugIns.PlugIn.LoadPlugIn(path);plugin=Rhino.PlugIns.PlugIn.Find(guid)
if plugin is None or plugin.GetType().Assembly.Location!=path or str(plugin.GetType().Assembly.GetName().Version)!='0.8.7.0':raise RuntimeError('Wrong release loaded')
if Rhino.PlugIns.PlugIn.PathFromId(guid)!=path:raise RuntimeError('Wrong registration')
Rhino.RhinoApp.RunScript('_EnvironmentalWeather',False)
panel_id=System.Guid('1c0c5ac3-b820-42f2-9aaa-1e0f50356d1a')
panel=get_view(panel_id)
if panel is None or panel.ProductVersion!='0.8.7':raise RuntimeError('Weather panel missing')
weather=json.load(open(os.path.join(root,'samples','radiation_smoke','runtime_result.json'),encoding='utf-8'))['weather']
r={'WeatherFile':weather,'HoursOfYear':list(range(4000,4024))}
result=json.loads(panel.ExecuteJson(json.dumps(r)))
if len(result['Series'])!=18:raise RuntimeError('Weather fields missing')
flags=BindingFlags.Instance|BindingFlags.NonPublic
fields=panel.GetType().GetField('fields',flags).GetValue(panel)
if fields.Items.Count!=18:raise RuntimeError('Field selector incomplete')
wind=next(i for i,s in enumerate(result['Series']) if s['Output']=='wind_direction')
fields.SelectedIndex=wind
if '平均值' in panel.SummaryText:raise RuntimeError('Wind direction shown with arithmetic mean')
ground=next(i for i,s in enumerate(result['Series']) if s['Output']=='ground_temperature')
fields.SelectedIndex=ground
if '12 逐月資料' not in panel.SummaryText:raise RuntimeError('Ground collection summary incorrect')
boundary=json.loads(panel.ExecuteJson(json.dumps({'WeatherFile':weather,'HoursOfYear':[0,8759]})))
custom=panel.GetType().GetField('customHours',flags).GetValue(panel)
if custom is None or list(custom)!=[0,8759]:raise RuntimeError('Noncontiguous selection lost')
old=panel.SummaryText;failed=False
try:panel.ExecuteJson(json.dumps({'WeatherFile':'missing.epw'}))
except Exception:failed=True
if not failed or panel.SummaryText!=old or '已保留前次結果' not in panel.StatusText:raise RuntimeError('Import failure lost previous result')
result=json.loads(panel.ExecuteJson(json.dumps(r)))
# Regression through the formal registered radiation panel.
Rhino.RhinoApp.RunScript('_EnvironmentalRadiation',False)
rad=get_view(System.Guid('c62382ce-7709-4fcd-9dfb-447d1d8a08c0'))
doc=__rhino_doc__;assert len(list(doc.Objects))==0,'Dedicated empty release document required'
scale=Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters,doc.ModelUnitSystem)
surface=Rhino.Geometry.PlaneSurface(Rhino.Geometry.Plane.WorldXY,Rhino.Geometry.Interval(0,4*scale),Rhino.Geometry.Interval(0,4*scale))
i=doc.Objects.AddBrep(surface.ToBrep())
try:
 radiation=json.loads(rad.ExecuteJson(json.dumps({'GeometryIds':[str(i)],'WeatherFile':weather,'GridMetres':1,'AcceptWarnings':True,'OutputDirectory':os.path.join(root,'samples','release_087_radiation')})))
 if abs(radiation['Statistics']['Mean']-1233.3471168086037)>1e-9:raise RuntimeError('Radiation regression')
 rad.ResetResult()
finally:doc.Objects.Delete(i,True);doc.Views.Redraw();surface.Dispose()
Rhino.RhinoApp.RunScript('_EnvironmentalWeather',False)
report={'version':panel.ProductVersion,'loaded_path':plugin.GetType().Assembly.Location,'registered_path':Rhino.PlugIns.PlugIn.PathFromId(guid),'weather_panel_visible':Rhino.UI.Panels.IsPanelVisible(workspace_id),'collections':len(result['Series']),'field_selector_verified':True,'monthly_summary_verified':True,'wind_direction_mean_suppressed':True,'custom_hours_preserved':True,'failed_import_preserves_result':True,'radiation_regression_mean':radiation['Statistics']['Mean'],'status':panel.StatusText,'visual_qa':'Not claimed; MCP/native control state verified','slot':'aardvark'}
"""Injected into fresh formal-release Rhino by the release replay script."""
import os, json, System, clr
clr.AddReference('Grasshopper')
import Grasshopper as GH
from Grasshopper.Kernel.Parameters import Param_GenericObject
from Grasshopper.Kernel.Types import GH_ObjectWrapper
from Grasshopper.Kernel.Data import GH_Path
folder='C:/Program Files/ladybug_tools/grasshopper/ladybug_grasshopper/user_objects'
assembly=plugin.GetType().Assembly
adapter=System.Reflection.Assembly.LoadFrom(os.path.join(root,'artifacts','releases','0.8.7','EnvironmentalHub.Adapters.dll'))
location_type=adapter.GetType('EnvironmentalHub.Adapters.LadybugLocationAdapter')
core=System.Reflection.Assembly.LoadFrom(os.path.join(root,'artifacts','releases','0.8.7','EnvironmentalHub.Core.dll'))
display=core.GetType('EnvironmentalHub.Core.ClimateDisplay').GetMethod('UtcOffset')
def run_location(request):
 return json.loads(location_type.GetMethod('RunJson').Invoke(None,System.Array[System.Object]([json.dumps(request),folder])))
def stock_location(request):
 d=GH.Kernel.GH_Document(); d.Enabled=False
 try:
  def make(name):
   c=GH.Kernel.GH_UserObject(os.path.join(folder,name+'.ghuser')).InstantiateObject();c.CreateAttributes();d.AddObject(c,False);return c
  c=make('LB Construct Location');deconstruct=make('LB Deconstruct Location')
  for key,value in [('_name_',request.get('Name','-')),('_latitude_',request.get('Latitude',0)),('_longitude_',request.get('Longitude',0)),('_time_zone_',request.get('TimeZone')),('_elevation_',request.get('ElevationMetres',0))]:
   if value is None:continue
   p=Param_GenericObject();p.CreateAttributes();p.PersistentData.Append(GH_ObjectWrapper(value),GH_Path(0));d.AddObject(p,False)
   next(i for i in c.Params.Input if i.Name==key).AddSource(p)
  deconstruct.Params.Input[0].AddSource(next(o for o in c.Params.Output if o.Name=='location'))
  GH.Instances.DocumentServer.AddDocument(d);d.Enabled=True;d.NewSolution(False)
  for obj in [c,deconstruct]:
   if list(obj.RuntimeMessages(GH.Kernel.GH_RuntimeMessageLevel.Error)):raise RuntimeError('Stock component failed')
  return {str(o.Name):list(o.VolatileData.AllData(True))[0].ScriptVariable() for o in deconstruct.Params.Output}
 finally:GH.Instances.DocumentServer.RemoveDocument(d);d.Dispose()
before=GH.Instances.DocumentServer.DocumentCount
location_cases=[]
for title,request in [
 ('taipei',{'Name':'Taipei','Latitude':25.033,'Longitude':121.5654,'TimeZone':8,'ElevationMetres':12}),
 ('positive_half',{'Name':'Half hour','Latitude':28.61,'Longitude':77.21,'TimeZone':5.5,'ElevationMetres':216}),
 ('negative_half',{'Name':'Negative half','Latitude':47.56,'Longitude':-52.71,'TimeZone':-3.5,'ElevationMetres':0}),
 ('quarter',{'Name':'Quarter hour','Latitude':27.7,'Longitude':85.3,'TimeZone':5.75,'ElevationMetres':1400}),
 ('estimated',{'Name':'Estimated','Latitude':25,'Longitude':121,'ElevationMetres':-2}),
 ('defaults',{})]:
 expected=stock_location(request);actual=run_location(request);p=actual['Location']
 for field,key in [('City','name'),('Latitude','latitude'),('Longitude','longitude'),('TimeZone','time_zone'),('Elevation','elevation')]:
  if p[field]!=expected[key]:raise RuntimeError('Location mismatch '+field)
 if request.get('TimeZone') is None and not any(w['Code']=='CLIMATE-LOCATION-002' for w in actual['Warnings']):raise RuntimeError('Missing estimate warning')
 location_cases.append({'case':title,'stock_matches':True,'time_zone':p['TimeZone']})
for title,request,code in [('bad_latitude',{'Latitude':91},'CLIMATE-LOCATION-001'),('bad_longitude',{'Longitude':181},'CLIMATE-LOCATION-001'),('bad_zone',{'TimeZone':13},'CLIMATE-LOCATION-001'),('null',None,'CLIMATE-CONTRACT-001'),('schema',{'SchemaVersion':'2'},'CLIMATE-CONTRACT-001')]:
 try:run_location(request)
 except Exception as e:
  if code not in str(e):raise
  location_cases.append({'case':title,'blocked':True,'code':code})
 else:raise RuntimeError('Invalid request accepted')
for value,expected in [(5.5,'UTC+5.5'),(-3.5,'UTC-3.5'),(5.75,'UTC+5.75'),(0,'UTC0')]:
 for culture in ['en-US','fr-FR']:
  old=System.Threading.Thread.CurrentThread.CurrentCulture
  try:
   System.Threading.Thread.CurrentThread.CurrentCulture=System.Globalization.CultureInfo(culture)
   actual=display.Invoke(None,System.Array[System.Object]([System.Double(value)]))
   if actual!=expected:raise RuntimeError('UTC formatting mismatch')
  finally:System.Threading.Thread.CurrentThread.CurrentCulture=old
Rhino.RhinoApp.RunScript('EnvironmentalLocation',False)
location_panel_id=System.Guid('5f78d8d4-e9a1-4713-bb04-d08466339735')
location_panel=get_view(location_panel_id)
result=json.loads(location_panel.ExecuteJson(json.dumps({'Name':'Kathmandu','Latitude':27.7,'Longitude':85.3,'TimeZone':5.75,'ElevationMetres':1400})))
assert 'UTC+5.75' in location_panel.SummaryText
prior=location_panel.SummaryText
try:location_panel.ExecuteJson(json.dumps({'Latitude':91}))
except Exception:pass
else:raise RuntimeError('Panel accepted invalid location')
assert location_panel.SummaryText==prior and '已保留前次結果' in location_panel.StatusText
assert GH.Instances.DocumentServer.DocumentCount==before
# Real EPW fixture with half-hour offset: verify the Weather Panel's rendered text.
fixture=os.path.join(root,'artifacts','weather_half_timezone.epw')
with open(weather,encoding='utf-8') as f:lines=f.readlines()
header=lines[0].rstrip('\n').split(',');header[8]='5.5';lines[0]=','.join(header)+'\n'
with open(fixture,'w',encoding='utf-8') as f:f.writelines(lines)
half=json.loads(panel.ExecuteJson(json.dumps({'WeatherFile':fixture,'HoursOfYear':[0]})))
flags=System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance
label=panel.GetType().GetField('location',flags).GetValue(panel)
assert half['Location']['TimeZone']==5.5 and 'UTC+5.5' in label.Text
# Restore real unmodified source weather to leave useful panel state.
panel.ExecuteJson(json.dumps({'WeatherFile':weather,'HoursOfYear':list(range(4000,4024))}))
report.update({'location_cases':location_cases,'location_passed':len(location_cases),'timezone_format_cases':8,
 'location_panel_visible':Rhino.UI.Panels.IsPanelVisible(location_panel_id), 'location_panel_failure_preserved':True,
 'weather_half_timezone_display_verified':True,'location_gh_cleanup':True})
json.dump(result,open(os.path.join(root,'samples','weather_087','constructed_location.json'),'w',encoding='utf-8'),indent=2)

"""Injected into formal release replay; independent original GH serialization."""
import clr,os,json,System
clr.AddReference('Grasshopper')
import Grasshopper as GH
from Grasshopper.Kernel.Parameters import Param_GenericObject
from Grasshopper.Kernel.Types import GH_ObjectWrapper
from Grasshopper.Kernel.Data import GH_Path
folder='C:/Program Files/ladybug_tools/grasshopper/ladybug_grasshopper/user_objects'
adapter=System.Reflection.Assembly.LoadFrom(os.path.join(root,'artifacts','releases','0.8.7','EnvironmentalHub.Adapters.dll'))
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
   json.dump(result,open(os.path.join(root,'samples','weather_087','import_'+fmt.lower()+'.json'),'w',encoding='utf-8'),indent=2)
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
climate_panel=get_view(climate_panel_id)
stat_result=json.loads(climate_panel.ExecuteJson(json.dumps({'Format':'STAT','FilePath':paths[0][1]})))
selector=climate_panel.GetType().GetField('outputs',System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic).GetValue(climate_panel)
assert selector.Items.Count==len(stat_result['Outputs'])
design=next(i for i,o in enumerate(stat_result['Outputs']) if o['Kind']=='DesignDay');selector.SelectedIndex=design
assert '最高乾球溫度' in climate_panel.SummaryText
radiation_index=next(i for i,o in enumerate(stat_result['Outputs']) if 'values' in (o['Data'] or {}) and isinstance(o['Data'],dict));selector.SelectedIndex=radiation_index
assert '8760 筆數值' in climate_panel.SummaryText
ddy_result=json.loads(climate_panel.ExecuteJson(json.dumps({'Format':'DDY','FilePath':paths[0][1].replace('.stat','.ddy')})))
previous=climate_panel.SummaryText
try:climate_panel.ExecuteJson(json.dumps({'Format':'STAT','FilePath':bad}))
except Exception:pass
else:raise RuntimeError('Panel accepted malformed STAT')
assert climate_panel.SummaryText==previous and '已保留前次結果' in climate_panel.StatusText
assert GH.Instances.DocumentServer.DocumentCount==before
report.update({'climate_cases':climate_cases,'climate_passed':len(climate_cases),'climate_panel_visible':Rhino.UI.Panels.IsPanelVisible(climate_panel_id),
 'climate_selector_verified':True,'climate_failure_preserves_result':True,'climate_gh_cleanup':True})

"""Injected into formal regression; original GH components supply references."""
import os,json,System,clr,Rhino
clr.AddReference('Grasshopper')
import Grasshopper as GH
from Grasshopper.Kernel.Parameters import Param_GenericObject
from Grasshopper.Kernel.Types import GH_ObjectWrapper
from Grasshopper.Kernel.Data import GH_Path
folder='C:/Program Files/ladybug_tools/grasshopper/ladybug_grasshopper/user_objects'
assembly=System.Reflection.Assembly.LoadFrom(os.path.join(root,'artifacts','releases','0.8.7','EnvironmentalHub.Adapters.dll'))
time_type=assembly.GetType('EnvironmentalHub.Adapters.LadybugTimeAdapter')
def run_time(request,method):return json.loads(time_type.GetMethod(method).Invoke(None,System.Array[System.Object]([json.dumps(request),folder])))
def stock_time(request,period):
 d=GH.Kernel.GH_Document();d.Enabled=False
 try:
  def make(name):
   c=GH.Kernel.GH_UserObject(os.path.join(folder,name+'.ghuser')).InstantiateObject();c.CreateAttributes();d.AddObject(c,False);return c
  if period:
   c=make('LB Analysis Period')
   pairs=[('_start_month_',request.get('StartMonth',1)),('_start_day_',request.get('StartDay',1)),('_start_hour_',request.get('StartHour',0)),('_end_month_',request.get('EndMonth',12)),('_end_day_',request.get('EndDay',31)),('_end_hour_',request.get('EndHour',23)),('_timestep_',request.get('TimeStep',1))]
  elif request.get('Mode','Calculate')=='FromHOY':c=make('LB HOY to DateTime');pairs=[('_hoy',request['HourOfYear'])]
  else:c=make('LB Calculate HOY');pairs=[('_month_',request.get('Month',1)),('_day_',request.get('Day',1)),('_hour_',request.get('Hour',0)),('_minute_',request.get('Minute',0))]
  for key,value in pairs:
   p=Param_GenericObject();p.CreateAttributes();p.PersistentData.Append(GH_ObjectWrapper(value),GH_Path(0));d.AddObject(p,False);next(i for i in c.Params.Input if i.Name==key).AddSource(p)
  def serialize(output,code,list_access=False):
   h=make('LB Construct Location');h.Code=code;h.Params.Input[0].TypeHint=None
   if list_access:h.Params.Input[0].Access=GH.Kernel.GH_ParamAccess.list
   h.Params.Input[0].AddSource(next(o for o in c.Params.Output if o.Name==output));return h
  if period:
   data=serialize('period','import json\nlocation=json.dumps(_name_.to_dict())')
   dates=serialize('dates','import json\nlocation=json.dumps([v.to_array() for v in _name_])',True)
  else:data=serialize('date',"import json\nlocation=json.dumps({'date':_name_.to_array(),'hoy':_name_.hoy,'doy':_name_.doy})")
  GH.Instances.DocumentServer.AddDocument(d);d.Enabled=True;d.NewSolution(False)
  for item in [c,data]+([dates] if period else []):
   errors=list(item.RuntimeMessages(GH.Kernel.GH_RuntimeMessageLevel.Error))
   if errors:raise RuntimeError('Original reference failed '+str(errors))
  def read(h):return json.loads(str(list(next(o for o in h.Params.Output if o.Name=='location').VolatileData.AllData(True))[0].ScriptVariable()))
  if period:return {'Period':read(data),'Dates':read(dates),'HoursOfYear':[float(v.ScriptVariable()) for v in next(o for o in c.Params.Output if o.Name=='hoys').VolatileData.AllData(True)]}
  return read(data)
 finally:GH.Instances.DocumentServer.RemoveDocument(d);d.Dispose()
before=GH.Instances.DocumentServer.DocumentCount;time_cases=[]
for name,request in [('annual',{}),('summer_day',{'StartMonth':6,'StartDay':21,'EndMonth':6,'EndDay':21}),('cross_year',{'StartMonth':12,'StartDay':31,'EndMonth':1,'EndDay':1}),('overnight',{'StartMonth':6,'StartDay':21,'StartHour':22,'EndMonth':6,'EndDay':22,'EndHour':3}),('subhour',{'StartMonth':1,'StartDay':1,'StartHour':8,'EndMonth':1,'EndDay':1,'EndHour':9,'TimeStep':3}),('native_end_day',{'StartMonth':2,'StartDay':1,'EndMonth':2,'EndDay':31})]:
 expected=stock_time(request,True);actual=run_time(request,'PeriodJson')
 assert actual['Period']==expected['Period'] and actual['HoursOfYear']==expected['HoursOfYear']
 assert [[v['Month'],v['Day'],v['Hour'],v['Minute']] for v in actual['Times']]==[v[:4] for v in expected['Dates']]
 assert GH.Instances.DocumentServer.DocumentCount==before
 time_cases.append({'case':name,'time_steps':len(actual['Times']),'native_matches':True})
for name,request in [('minute',{'Month':6,'Day':21,'Hour':13,'Minute':30}),('last_minute',{'Month':12,'Day':31,'Hour':23,'Minute':59}),('zero_hoy',{'Mode':'FromHOY','HourOfYear':0}),('fractional_hoy',{'Mode':'FromHOY','HourOfYear':4085.5})]:
 expected=stock_time(request,False);actual=run_time(request,'CalendarJson');t=actual['Time']
 assert [t['Month'],t['Day'],t['Hour'],t['Minute']]==expected['date'][:4] and t['HourOfYear']==expected['hoy'] and actual['DayOfYear']==expected['doy']
 time_cases.append({'case':name,'native_matches':True})
for name,method,request,code in [('bad_step','PeriodJson',{'TimeStep':7},'CLIMATE-PERIOD-001'),('bad_month','PeriodJson',{'StartMonth':0},'CLIMATE-PERIOD-001'),('bad_hour','PeriodJson',{'EndHour':24},'CLIMATE-PERIOD-001'),('null_period','PeriodJson',None,'CLIMATE-CONTRACT-001'),('leap_date','CalendarJson',{'Month':2,'Day':29},'CLIMATE-PERIOD-001'),('bad_hoy','CalendarJson',{'Mode':'FromHOY','HourOfYear':8760},'CLIMATE-PERIOD-001'),('bad_mode','CalendarJson',{'Mode':'bad'},'CLIMATE-CONTRACT-001')]:
 try:run_time(request,method)
 except Exception as e:
  if code not in str(e):raise
  time_cases.append({'case':name,'blocked':True,'code':code})
 else:raise RuntimeError('Invalid time request accepted')
Rhino.RhinoApp.RunScript('EnvironmentalTime',False)
tp=get_view(System.Guid('06843693-df8a-421c-938b-96e2b9e88066'))
time_result=json.loads(tp.ExecutePeriodJson(json.dumps({'StartMonth':6,'StartDay':21,'EndMonth':6,'EndDay':21})))
assert len(time_result['HoursOfYear'])==24
flags=System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic
def time_control(name):return tp.GetType().GetField(name,flags).GetValue(tp)
assert time_control('sm').Value==6 and time_control('ed').Value==21
time_control('run').PerformClick();assert tp.StatusText.startswith('計算完成')
tp.ExecuteCalendarJson(json.dumps({'Month':6,'Day':21,'Hour':13,'Minute':30}))
assert '13:30' in tp.SummaryText and time_control('mode').SelectedIndex==1
time_control('run').PerformClick();assert '13:30' in tp.SummaryText
prior=tp.SummaryText
try:tp.ExecutePeriodJson(json.dumps({'TimeStep':7}))
except Exception:pass
else:raise RuntimeError('Panel accepted invalid step')
assert tp.SummaryText==prior and '已保留前次結果' in tp.StatusText
Rhino.RhinoApp.RunScript('EnvironmentalHub',False)
overview_id=System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32')
assert Rhino.UI.Panels.IsPanelVisible(overview_id)
assert GH.Instances.DocumentServer.DocumentCount==before
assert '緯度' in climate_panel.SummaryText and '"type"' not in climate_panel.SummaryText
friendly=json.loads(climate_panel.ExecuteJson(json.dumps({'Format':'STAT','FilePath':paths[0][1]})))
period_index=next(i for i,o in enumerate(friendly['Outputs']) if o['Kind']=='AnalysisPeriod')
selector.SelectedIndex=period_index
assert '起始' in climate_panel.SummaryText and '當地標準時間' in climate_panel.SummaryText
report['friendly_climate_location_and_period_verified']=True
report.update({'time_cases':time_cases,'time_passed':len(time_cases),'time_native_buttons_verified':True,'time_failure_preserves_result':True,'time_gh_cleanup':True,'overview_visible':True})
json.dump(time_result,open(os.path.join(root,'samples','weather_087','analysis_period.json'),'w',encoding='utf-8'),indent=2)


# Verify visible Chinese field names and immutable original contracts.
assert list(result['InputParameters'].keys())==['SchemaVersion','Format','FilePath']
assert str(panel.GetType().GetField('fields',flags).GetValue(panel).Items[0].Text).startswith('乾球溫度')
text_type=plugin.GetType().Assembly.GetType('EnvironmentalHub.Plugin.HubText')
error_method=text_type.GetMethod('Error',BindingFlags.Static|BindingFlags.NonPublic)
detail=error_method.Invoke(None,System.Array[System.Object]([System.Exception('CLIMATE-FILE-001: Wrong file.')]))
assert 'CLIMATE-FILE-001' in detail and '副檔名' in detail
unknown=error_method.Invoke(None,System.Array[System.Object]([System.Exception('Native message 42')]))
assert '原始診斷' in unknown and 'Native message 42' in unknown
report['language']='zh-TW'
report['chinese_weather_selector']=True
report['chinese_diagnostics_preserve_codes']=True
report['unknown_native_diagnostics_preserved']=True

json.dump(report,open(os.path.join(root,'docs','evidence','release_087_loaded.json'),'w',encoding='utf-8'),indent=2)
print(json.dumps(report))
