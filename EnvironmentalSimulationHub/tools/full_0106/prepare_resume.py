import json
from pathlib import Path
root=Path(__file__).resolve().parents[2]; here=Path(__file__).resolve().parent
calls=json.loads((here/'native_regression_calls.json').read_text(encoding='utf-8'))
receipt=json.loads((root/'docs/evidence/full_0106/native_regression_transport.json').read_text(encoding='utf-8'))
index=len(receipt['calls'])-1
assert 'ClosePanel(workspace_id)' in calls[index]['arguments']['script']
old="Rhino.UI.Panels.ClosePanel(workspace_id)\nRhino.RhinoApp.RunScript('EnvironmentalWeather', False)\nassert System.Object.ReferenceEquals(workspace, Rhino.UI.Panels.GetPanel(workspace_id))"
new="Rhino.UI.Panels.ClosePanel(workspace_id)\nRhino.RhinoApp.RunScript('EnvironmentalWeather', False)\nworkspace = Rhino.UI.Panels.GetPanel(workspace_id)\nassert all(System.Object.ReferenceEquals(view, workspace.GetModule(t)) for t, view in zip(types, views))"
assert old in calls[index]['arguments']['script']
calls[index]['arguments']['script']=calls[index]['arguments']['script'].replace(old,new)
(here/'resume_regression_calls.json').write_text(json.dumps(calls[index:],ensure_ascii=False),encoding='utf-8')
print(json.dumps({'successful_call_prefix':index,'remaining_calls':len(calls)-index,'old_assertion':'shell identity','new_assertion':'same cached views and full state'}))
