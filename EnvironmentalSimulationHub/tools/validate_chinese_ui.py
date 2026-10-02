"""Native Chinese UI coverage and navigation; run only in the owned 0.8.6 slot."""
import Rhino,System,os,json,clr,re
clr.AddReference('Eto')
from Eto.Forms import Button,DropDown,CheckBox,Label,TextBox
root='C:/Users/08432.SINOLTD/00.DEVE/31.AEC/RHINO_Deve/EnvironmentalSimulationHub'
ids=['7281a8f2-e2c4-4c27-bcb5-22cbb0688b32','1c0c5ac3-b820-42f2-9aaa-1e0f50356d1a','5f78d8d4-e9a1-4713-bb04-d08466339735','499a99e8-8e73-4a6b-8208-fc879e413d36','06843693-df8a-421c-938b-96e2b9e88066','c62382ce-7709-4fcd-9dfb-447d1d8a08c0']
commands=['EnvironmentalHub','EnvironmentalWeather','EnvironmentalLocation','EnvironmentalClimate','EnvironmentalTime','EnvironmentalRadiation']
def walk(control):
    yield control
    if hasattr(control,'Controls'):
        for child in control.Controls:
            for descendant in walk(child):yield descendant
panels=[]
for command,guid in zip(commands,ids):
    Rhino.RhinoApp.RunScript(command,False)
    panel=Rhino.UI.Panels.GetPanel(System.Guid(guid))
    assert str(panel.GetType().Assembly.GetName().Version)=='0.8.6.0'
    panels.append(panel)
overview,weather=panels[0:2];prior=weather.SummaryText
buttons=[c for c in walk(overview) if isinstance(c,Button) and (c.Text.startswith('開啟 ') or c.Text=='開始日射分析')]
assert len(buttons)==5
for i,button in enumerate(buttons):
    button.PerformClick()
    assert Rhino.UI.Panels.IsPanelVisible(System.Guid(ids[[5,1,2,3,4][i]]))
controls=list(walk(panels[4]))
choice=next(c for c in controls if isinstance(c,DropDown) and c.Items.Count==6)
open_button=next(c for c in controls if isinstance(c,Button) and c.Text=='開啟')
for i,guid in enumerate(ids):
    choice.SelectedIndex=i;open_button.PerformClick()
    assert Rhino.UI.Panels.IsPanelVisible(System.Guid(guid))
assert weather.SummaryText==prior
coverage=[]
for panel in panels:
    text=[]
    for control in walk(panel):
        if isinstance(control,(Button,CheckBox)):
            assert re.search(r'[\u4e00-\u9fff]',str(control.Text)),str(control.Text)
            text.append(str(control.Text))
    selectors=[c for c in walk(panel) if isinstance(c,DropDown)]
    for selector in selectors:
        for item in selector.Items:
            value=str(item.Text)
            assert re.search(r'[\u4e00-\u9fff]',value) or value in ('STAT','DDY') or selector.GetType().Name=='DropDown' and value.startswith(('Baseline','Candidate','Two-hour')),value
    coverage.append({'panel':str(panel.GetType().Name),'buttons_and_checkboxes':text})
Rhino.RhinoApp.RunScript('EnvironmentalHub',False)
report={'version':'0.8.6','language':'zh-TW','overview_buttons_verified':5,'shared_navigation_routes_verified':6,'navigation_preserves_weather_result':True,'coverage':coverage,'scope':'Native Eto buttons, checkboxes, selectors and registered navigation; native field data, paths and user scenario names retain original values.'}
json.dump(report,open(os.path.join(root,'docs/evidence/chinese_086_ui.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(json.dumps({'chinese_panels':len(coverage),'overview_buttons':5,'shared_routes':6}))
