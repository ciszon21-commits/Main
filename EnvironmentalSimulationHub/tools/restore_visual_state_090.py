import os,json,System,Rhino
root='C:/Users/08432.SINOLTD/00.DEVE/31.AEC/RHINO_Deve/EnvironmentalSimulationHub'
workspace=Rhino.UI.Panels.GetPanel(System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32'))
def module(name):return workspace.GetModule(workspace.GetType().Assembly.GetType('EnvironmentalHub.Plugin.'+name))
sun=module('SunPathPanel');weather=module('WeatherPanel');sun.UseImportedWeather()
flags=System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic
request=sun.GetType().GetMethod('Request',flags).Invoke(sun,None)
import clr
clr.AddReference('System.Text.Json')
# The existing public result gives an independently readable location for this transfer.
epw=json.loads(weather.CompletedResultJson)
assert request.Location.Latitude==epw['Location']['Latitude'] and request.Location.Longitude==epw['Location']['Longitude'] and request.Location.TimeZone==epw['Location']['TimeZone']
assert json.loads(sun.CompletedResultJson)['Location']['City']=='臺北','Transfer must not overwrite the previous completed result'
json.dump({'version':'0.9.0','passed':1,'cases':['completed_epw_location_transfer_retains_previous_result']},open(os.path.join(root,'docs/evidence/sunpath_090_transfer.json'),'w',encoding='utf-8'),indent=2)
sun.ExecuteJson(json.dumps({'Location':{'Name':'臺北','Latitude':25.033,'Longitude':121.5654,'TimeZone':8},'HoursOfYear':[4110,4113,4116,4119,4122]}))
doc=__rhino_doc__;scale=Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters,doc.ModelUnitSystem)
box=Rhino.Geometry.Box(Rhino.Geometry.Plane.WorldXY,Rhino.Geometry.Interval(0,4*scale),Rhino.Geometry.Interval(0,4*scale),Rhino.Geometry.Interval(0,4*scale)).ToBrep()
fixture=doc.Objects.AddBrep(box);box.Dispose()
rad=module('RadiationPanel')
weather_path=json.loads(weather.CompletedSelectionJson)['WeatherFile']
rad.ExecuteJson(json.dumps({'GeometryIds':[str(fixture)],'WeatherFile':weather_path,'GridMetres':1,'AcceptWarnings':True,'OutputDirectory':os.path.join(root,'samples','visual_090')}))
print('Visual state restored; completed EPW transfer verified')
