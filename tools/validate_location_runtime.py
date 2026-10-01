"""Injected into fresh formal-release Rhino by the release replay script."""
import os, json, System, clr
clr.AddReference('Grasshopper')
import Grasshopper as GH
from Grasshopper.Kernel.Parameters import Param_GenericObject
from Grasshopper.Kernel.Types import GH_ObjectWrapper
from Grasshopper.Kernel.Data import GH_Path
folder='C:/Program Files/ladybug_tools/grasshopper/ladybug_grasshopper/user_objects'
assembly=plugin.GetType().Assembly
adapter=System.Reflection.Assembly.LoadFrom(os.path.join(root,'artifacts','releases','0.5.0','EnvironmentalHub.Adapters.dll'))
location_type=adapter.GetType('EnvironmentalHub.Adapters.LadybugLocationAdapter')
core=System.Reflection.Assembly.LoadFrom(os.path.join(root,'artifacts','releases','0.5.0','EnvironmentalHub.Core.dll'))
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
location_panel=Rhino.UI.Panels.GetPanel(location_panel_id)
result=json.loads(location_panel.ExecuteJson(json.dumps({'Name':'Kathmandu','Latitude':27.7,'Longitude':85.3,'TimeZone':5.75,'ElevationMetres':1400})))
assert 'UTC+5.75' in location_panel.SummaryText
prior=location_panel.SummaryText
try:location_panel.ExecuteJson(json.dumps({'Latitude':91}))
except Exception:pass
else:raise RuntimeError('Panel accepted invalid location')
assert location_panel.SummaryText==prior and 'Previous result retained' in location_panel.StatusText
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
json.dump(result,open(os.path.join(root,'samples','weather','constructed_location.json'),'w',encoding='utf-8'),indent=2)
