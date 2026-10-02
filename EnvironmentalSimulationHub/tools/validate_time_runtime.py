"""Injected into formal regression; original GH components supply references."""
import os,json,System,clr,Rhino
clr.AddReference('Grasshopper')
import Grasshopper as GH
from Grasshopper.Kernel.Parameters import Param_GenericObject
from Grasshopper.Kernel.Types import GH_ObjectWrapper
from Grasshopper.Kernel.Data import GH_Path
folder='C:/Program Files/ladybug_tools/grasshopper/ladybug_grasshopper/user_objects'
assembly=System.Reflection.Assembly.LoadFrom(os.path.join(root,'artifacts','releases','0.7.2','EnvironmentalHub.Adapters.dll'))
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
tp=Rhino.UI.Panels.GetPanel(System.Guid('06843693-df8a-421c-938b-96e2b9e88066'))
time_result=json.loads(tp.ExecutePeriodJson(json.dumps({'StartMonth':6,'StartDay':21,'EndMonth':6,'EndDay':21})))
assert len(time_result['HoursOfYear'])==24
flags=System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic
def time_control(name):return tp.GetType().GetField(name,flags).GetValue(tp)
assert time_control('sm').Value==6 and time_control('ed').Value==21
time_control('run').PerformClick();assert tp.StatusText.startswith('Calculated')
tp.ExecuteCalendarJson(json.dumps({'Month':6,'Day':21,'Hour':13,'Minute':30}))
assert '13:30' in tp.SummaryText and time_control('mode').SelectedIndex==1
time_control('run').PerformClick();assert '13:30' in tp.SummaryText
prior=tp.SummaryText
try:tp.ExecutePeriodJson(json.dumps({'TimeStep':7}))
except Exception:pass
else:raise RuntimeError('Panel accepted invalid step')
assert tp.SummaryText==prior and 'Previous result retained' in tp.StatusText
Rhino.RhinoApp.RunScript('EnvironmentalHub',False)
overview_id=System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32')
assert Rhino.UI.Panels.IsPanelVisible(overview_id)
assert GH.Instances.DocumentServer.DocumentCount==before
assert 'Latitude' in climate_panel.SummaryText and '"type"' not in climate_panel.SummaryText
friendly=json.loads(climate_panel.ExecuteJson(json.dumps({'Format':'STAT','FilePath':paths[0][1]})))
period_index=next(i for i,o in enumerate(friendly['Outputs']) if o['Kind']=='AnalysisPeriod')
selector.SelectedIndex=period_index
assert 'Start' in climate_panel.SummaryText and 'Local standard time' in climate_panel.SummaryText
report['friendly_climate_location_and_period_verified']=True
report.update({'time_cases':time_cases,'time_passed':len(time_cases),'time_native_buttons_verified':True,'time_failure_preserves_result':True,'time_gh_cleanup':True,'overview_visible':True})
json.dump(time_result,open(os.path.join(root,'samples','weather','analysis_period.json'),'w',encoding='utf-8'),indent=2)
