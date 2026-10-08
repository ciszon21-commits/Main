import json
from pathlib import Path
root = Path(__file__).resolve().parents[2]
here = Path(__file__).resolve().parent
spawn = json.loads((root / 'docs/evidence/session_0106/spawn_transport.json').read_text(encoding='utf-8'))
slot = json.loads(spawn['calls'][0]['response']['result']['content'][0]['text'])['payload']
assert not slot['adopted']
script = "import System, Rhino, json\nassert System.Diagnostics.Process.GetCurrentProcess().Id == %d\ndoc=__rhino_doc__\nassert not doc.Modified and not list(doc.Objects) and doc.Path in (None,'')\nprint(json.dumps({'pid':%d,'empty_unmodified':True}))" % (slot['pid'],slot['pid'])
(here / 'close_failed_load_calls.json').write_text(json.dumps([
    dict(name='run_python',arguments=dict(slot=slot['slotId'],script=script)),
    dict(name='close_slot',arguments=dict(slot=slot['slotId']))]),encoding='utf-8')
body=(root / 'tools/home_0105/Set-CandidatePath.ps1').read_text(encoding='utf-8')
body=body.replace('home_0105','session_0106').replace('0.10.5','0.10.6')
(here / 'Set-CandidatePath.ps1').write_text(body,encoding='utf-8')
