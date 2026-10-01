import json,hashlib,zipfile,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
if '--replay' not in sys.argv:
 r=root/'artifacts/releases/0.8.3'
 m={'version':'0.8.3','plugin':'EnvironmentalHub.Plugin.rhp','plugin_id':'bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f','runtime':'Rhino 8 / .NET 8','files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in r.iterdir() if f.suffix in ('.dll','.rhp','.json') and f.name!='release_manifest.json'},'dependencies':'Original installed Ladybug / Radiance; unchanged simulation core.'}
 for path in [r/'release_manifest.json',root/'docs/evidence/release_083_manifest.json']:path.write_text(json.dumps(m,indent=2),encoding='utf-8')
 with zipfile.ZipFile(root/'artifacts/EnvironmentalHub-0.8.3.zip','w',zipfile.ZIP_DEFLATED) as z:
  for f in r.iterdir():
   if f.suffix!='.pdb':z.write(f,f.name)
 (root/'tools/release_083_slot_calls.json').write_text(json.dumps([{'name':'spawn_slot','arguments':{}}]),encoding='utf-8')
else:
 d=json.loads((root/'docs/evidence/release_083_slot_transport.json').read_text(encoding='utf-8'))
 slot=json.loads(d['calls'][0]['response']['result']['content'][0]['text'])['payload']['slotId']
 call=json.loads((root/'tools/release_072_calls.json').read_text(encoding='utf-8'))[0]
 call['arguments']['script']=call['arguments']['script'].replace('0.7.2','0.8.3').replace('release_072','release_083').replace("'slot': 'bonobo'","'slot': "+repr(slot)).replace("'slot':'bonobo'","'slot':"+repr(slot))
 call['arguments']['slot']=slot
 (root/'tools/release_083_calls.json').write_text(json.dumps([call],indent=2),encoding='utf-8')
 for filename,source in [('ui_083_calls.json','capture_hub_native_panels.py'),('navigation_083_calls.json','validate_hub_navigation.py'),('platform_ui_calls.json','validate_platform_ui.py')]:
  (root/'tools'/filename).write_text(json.dumps([{'name':'run_python','arguments':{'slot':slot,'script':(root/'tools'/source).read_text(encoding='utf-8')}}],indent=2),encoding='utf-8')
 print('Prepared 0.8.3 native regression for',slot)
