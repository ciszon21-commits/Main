import json,hashlib,zipfile,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
if '--replay' not in sys.argv:
 r=root/'artifacts/releases/0.7.2'
 m={'version':'0.7.2','plugin':'EnvironmentalHub.Plugin.rhp','plugin_id':'bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f','runtime':'Rhino 8 / .NET 8','files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in r.iterdir() if f.suffix in ('.dll','.rhp','.json') and f.name!='release_manifest.json'},'dependencies':'Original installed Ladybug / Radiance; no bundled solver.'}
 for path in [r/'release_manifest.json',root/'docs/evidence/release_072_manifest.json']:path.write_text(json.dumps(m,indent=2),encoding='utf-8')
 with zipfile.ZipFile(root/'artifacts/EnvironmentalHub-0.7.2.zip','w',zipfile.ZIP_DEFLATED) as z:
  for f in r.iterdir():
   if f.suffix!='.pdb':z.write(f,f.name)
 (root/'tools/release_072_slot_calls.json').write_text(json.dumps([{'name':'spawn_slot','arguments':{}}]),encoding='utf-8')
else:
 d=json.loads((root/'docs/evidence/release_072_slot_transport.json').read_text(encoding='utf-8'))
 slot=json.loads(d['calls'][0]['response']['result']['content'][0]['text'])['payload']['slotId']
 call=json.loads((root/'tools/release_060_calls.json').read_text(encoding='utf-8'))[0]
 s=call['arguments']['script'].replace('0.6.0','0.7.2').replace('release_060','release_072').replace("'_EnvironmentalHub'","'_EnvironmentalRadiation'")
 s=s.replace("'slot':'armadillo'","'slot':"+repr(slot))
 s=s.replace('json.dump(report,',(root/'tools/validate_time_runtime.py').read_text(encoding='utf-8')+'\njson.dump(report,',1)
 call['arguments']['slot']=slot;call['arguments']['script']=s
 (root/'tools/release_072_calls.json').write_text(json.dumps([call],indent=2),encoding='utf-8')
 for filename,source in [('ui_072_calls.json','capture_hub_native_panels.py'),('navigation_072_calls.json','validate_hub_navigation.py')]:
  (root/'tools'/filename).write_text(json.dumps([{'name':'run_python','arguments':{'slot':slot,'script':(root/'tools'/source).read_text(encoding='utf-8')}}],indent=2),encoding='utf-8')
 print('Prepared 0.7.2 regression for',slot)
