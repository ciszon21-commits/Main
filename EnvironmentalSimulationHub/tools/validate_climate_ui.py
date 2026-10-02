"""Verify the actual native import button event for both selector formats."""
import Rhino,System,os,json
root='C:/Users/08432.SINOLTD/00.DEVE/31.AEC/RHINO_Deve/EnvironmentalSimulationHub'
panel=Rhino.UI.Panels.GetPanel(System.Guid('499a99e8-8e73-4a6b-8208-fc879e413d36'))
flags=System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance
def control(name):return panel.GetType().GetField(name,flags).GetValue(panel)
path=json.load(open(os.path.join(root,'samples','weather','import_stat.json'),encoding='utf-8'))['InputParameters']['FilePath']
cases=[]
for i,fmt in [(0,'STAT'),(1,'DDY')]:
 control('format').SelectedIndex=i;control('file').Text=os.path.splitext(path)[0]+'.'+fmt.lower()
 control('import').PerformClick()
 if not panel.StatusText.startswith('Imported'):raise RuntimeError('Native '+fmt+' click failed: '+panel.StatusText)
 result=panel.GetType().GetField('result',flags).GetValue(panel)
 assert result.InputParameters.Format==fmt
 cases.append({'format':fmt,'button_request_verified':True})
receipt=os.path.join(root,'docs','evidence','release_060_loaded.json')
report=json.load(open(receipt,encoding='utf-8'));report['native_climate_import_buttons']=cases
json.dump(report,open(receipt,'w',encoding='utf-8'),indent=2)
print(json.dumps(cases))
