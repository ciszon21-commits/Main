import json
from pathlib import Path
root = Path(__file__).resolve().parents[2]
here = Path(__file__).resolve().parent
receipt = json.loads((root / 'docs/evidence/session_0106/spawn_transport.json').read_text(encoding='utf-8'))
assert receipt['status'] == 'MCP_RESPONDED' and not receipt.get('error')
slot = json.loads(receipt['calls'][0]['response']['result']['content'][0]['text'])['payload']
assert not slot['adopted']
script = (root / 'tools/home_0105/load_release.py').read_text(encoding='utf-8').replace('docs/evidence/home_0105','docs/evidence/session_0106').replace('0.10.5','0.10.6')
script += "\nprint(json.dumps({'hwnd': Rhino.RhinoApp.MainWindowHandle().ToInt64()}))\n"
(here / 'load_calls.json').write_text(json.dumps([{'name':'run_python','arguments':{'slot':slot['slotId'],'script':script}}],ensure_ascii=False),encoding='utf-8')
print(json.dumps(slot))
