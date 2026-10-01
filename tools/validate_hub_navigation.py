import Rhino,System,os,json,clr
clr.AddReference('Eto')
from Eto.Forms import Button,DropDown
root='C:/Users/08432.SINOLTD/00.DEVE/31.AEC/RHINO_Deve/EnvironmentalSimulationHub'
ids=['7281a8f2-e2c4-4c27-bcb5-22cbb0688b32','1c0c5ac3-b820-42f2-9aaa-1e0f50356d1a','5f78d8d4-e9a1-4713-bb04-d08466339735','499a99e8-8e73-4a6b-8208-fc879e413d36','06843693-df8a-421c-938b-96e2b9e88066','c62382ce-7709-4fcd-9dfb-447d1d8a08c0']
def walk(control):
 yield control
 if hasattr(control,'Controls'):
  for child in control.Controls:
   for descendant in walk(child):yield descendant
overview=Rhino.UI.Panels.GetPanel(System.Guid(ids[0]))
weather=Rhino.UI.Panels.GetPanel(System.Guid(ids[1]));prior=weather.SummaryText
buttons=[c for c in walk(overview) if isinstance(c,Button) and (c.Text.startswith('Open ') or c.Text=='Start solar radiation analysis')]
assert len(buttons)==5
for i,button in enumerate(buttons):
 button.PerformClick()
 assert Rhino.UI.Panels.IsPanelVisible(System.Guid(ids[[5,1,2,3,4][i]]))
tp=Rhino.UI.Panels.GetPanel(System.Guid(ids[4]))
controls=list(walk(tp))
choice=next(c for c in controls if isinstance(c,DropDown) and c.Items.Count==6)
open_button=next(c for c in controls if isinstance(c,Button) and c.Text=='Open')
for i,guid in enumerate(ids):
 choice.SelectedIndex=i;open_button.PerformClick();assert Rhino.UI.Panels.IsPanelVisible(System.Guid(guid))
assert weather.SummaryText==prior
Rhino.RhinoApp.RunScript('EnvironmentalHub',False)
path=os.path.join(root,'docs','evidence','release_083_loaded.json')
report=json.load(open(path,encoding='utf-8'));report['overview_buttons_verified']=5;report['shared_navigation_routes_verified']=6;report['navigation_preserves_weather_result']=True
json.dump(report,open(path,'w',encoding='utf-8'),indent=2)
print('5 overview buttons / 6 shared routes verified; weather result preserved')
