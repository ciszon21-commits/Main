import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'docs/evidence/release_060_slot_transport.json').read_text(encoding='utf-8'))
slot=json.loads(data['calls'][0]['response']['result']['content'][0]['text'])['payload']['slotId']
call=json.loads((root/'tools/release_050_calls.json').read_text(encoding='utf-8'))[0]
script=call['arguments']['script'].replace('0.5.0','0.6.0').replace('release_050','release_060').replace("'slot': 'aardvark'","'slot': "+repr(slot))
script=script.replace("'slot':'aardvark'", "'slot':"+repr(slot))
script=script.replace('json.dump(report,',(root/'tools/validate_climate_runtime.py').read_text(encoding='utf-8')+'\njson.dump(report,',1)
call['arguments']['script']=script;call['arguments']['slot']=slot
(root/'tools/release_060_calls.json').write_text(json.dumps([call],indent=2),encoding='utf-8')
(root/'tools/climate_ui_calls.json').write_text(json.dumps([{'name':'run_python','arguments':{'slot':slot,'script':(root/'tools/validate_climate_ui.py').read_text(encoding='utf-8')}}],indent=2),encoding='utf-8')
print('Prepared full 0.6.0 regression for',slot)
