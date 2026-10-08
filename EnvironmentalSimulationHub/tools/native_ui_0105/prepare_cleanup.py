import json
from pathlib import Path
root = Path(__file__).resolve().parents[2]
here = Path(__file__).resolve().parent
spawn = json.loads((root / 'docs/evidence/native_ui_0105/spawn_transport.json').read_text(encoding='utf-8'))
slot = json.loads(spawn['calls'][0]['response']['result']['content'][0]['text'])['payload']
assert not slot['adopted']
script = (here / 'common.py').read_text(encoding='utf-8') + '\nassert not doc.Modified\nread_state()\n'
calls = [{'name':'run_python','arguments':{'slot':slot['slotId'],'script':script}},
         {'name':'close_slot','arguments':{'slot':slot['slotId']}}]
(here / 'cleanup_calls.json').write_text(json.dumps(calls,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'slot':slot['slotId'],'pid':slot['pid']}))
