import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'tools/capture_workspace_087.py').read_text(encoding='utf-8').replace('ui_087','ui_090').replace('weather_087','weather_090')
s=s.replace('for name,command,guid in modules:',"modules += [(name,'EnvironmentalSunPath','sunpath') for name in ['sunpath_input','sunpath_settings','sunpath_results','sunpath_error']]\nfor name,command,guid in modules:")
s=s.replace('source=get_view(System.Guid(guid))',"source=Rhino.UI.Panels.GetPanel(workspace_id).GetModule(Rhino.UI.Panels.GetPanel(workspace_id).GetType().Assembly.GetType('EnvironmentalHub.Plugin.SunPathPanel')) if guid=='sunpath' else get_view(System.Guid(guid))")
s=s.replace('for field in source.GetType().GetFields(flags):',"for field in ([] if name=='sunpath_input' else source.GetType().GetFields(flags)):")
s=s.replace('try:native=workspace.ControlObject',"""if name.startswith('sunpath') and name!='sunpath_input':
  panel.GetType().GetField('result',flags).SetValue(panel,source.GetType().GetField('result',flags).GetValue(source))
  if name=='sunpath_settings':panel.GetType().GetField('reveal',flags).GetValue(panel).Checked=True
  if name=='sunpath_error':
   try:panel.ExecuteJson(json.dumps({'RadiusMetres':0}))
   except Exception:pass
 try:native=workspace.ControlObject""")
s=s.replace('   # Draw through a VisualBrush',"""   if name in ['sunpath_settings','sunpath_results','sunpath_error']:
    field={'sunpath_settings':'month','sunpath_results':'summary','sunpath_error':'run'}[name]
    target=panel.GetType().GetField(field,flags).GetValue(panel);scroll=panel.Content
    top=scroll.Content.PointToScreen(Drawing.PointF.Empty);position=target.PointToScreen(Drawing.PointF.Empty)
    scroll.ScrollPosition=Drawing.Point(0,max(0,int(position.Y-top.Y)-12));native.UpdateLayout()
   # Draw through a VisualBrush""")
(root/'tools/capture_workspace_090.py').write_text(s,encoding='utf-8')
slot=json.loads(json.loads((root/'docs/evidence/release_090_slot_transport.json').read_text(encoding='utf-8'))['calls'][0]['response']['result']['content'][0]['text'])['payload']['slotId']
scripts=['restore_visual_state_090','validate_workspace_090','capture_workspace_090']
(root/'tools/final_ui_090_calls.json').write_text(json.dumps([{'name':'run_python','arguments':{'slot':slot,'script':(root/'tools'/(f+'.py')).read_text(encoding='utf-8')}} for f in scripts]),encoding='utf-8')
