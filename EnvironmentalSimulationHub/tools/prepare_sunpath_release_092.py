"""Versioned SunPath release manifest and native replay preparation."""
import hashlib,json,zipfile,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
release=root/'artifacts/releases/0.9.2'
if '--replay' not in sys.argv:
    manifest={'version':'0.9.2','plugin':'EnvironmentalHub.Plugin.rhp','plugin_id':'bc5a6bd7-4e8f-4f14-a173-ed39f8bf357f','runtime':'Rhino 8 / .NET 8',
              'files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in release.iterdir() if f.suffix in ('.dll','.rhp','.json') and f.name!='release_manifest.json'},
              'dependencies':'Original installed Ladybug/Radiance; additive SunPath adapter and contracts. Existing radiation/weather/time/location/climate solver files retained.'}
    for p in [release/'release_manifest.json',root/'docs/evidence/release_092_manifest.json']:p.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    with zipfile.ZipFile(root/'artifacts/EnvironmentalHub-0.9.2.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for f in release.iterdir():
            if f.suffix!='.pdb':archive.write(f,f.name)
    (root/'tools/release_092_slot_calls.json').write_text(json.dumps([{'name':'spawn_slot','arguments':{}}]),encoding='utf-8')
else:
    (root/'samples/weather_092').mkdir(exist_ok=True)
    transport=json.loads((root/'docs/evidence/release_092_slot_transport.json').read_text(encoding='utf-8'))
    slot=json.loads(transport['calls'][0]['response']['result']['content'][0]['text'])['payload']['slotId']
    call=json.loads((root/'tools/release_087_calls.json').read_text(encoding='utf-8'))[0]
    script=call['arguments']['script'].replace('0.8.7','0.9.2').replace('release_087','release_092').replace('weather_087','weather_092').replace("'slot':'aardvark'","'slot':"+repr(slot)).replace("'slot': 'aardvark'","'slot': "+repr(slot))
    call['arguments']={'slot':slot,'script':script}
    (root/'tools/release_092_calls.json').write_text(json.dumps([call],indent=2),encoding='utf-8')
    for name in ['validate_sunpath_092','platform_092_native','validate_workspace_092','capture_workspace_092']:
        path=root/'tools'/ (name+'.py')
        if path.exists():(root/'tools'/(name+'_calls.json')).write_text(json.dumps([{'name':'run_python','arguments':{'slot':slot,'script':path.read_text(encoding='utf-8')}}],indent=2),encoding='utf-8')
    print('Prepared owned release slot',slot)
