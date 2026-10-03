import argparse, json, subprocess, sys
from pathlib import Path
root = Path(__file__).resolve().parents[2]
here = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['fixture','read_state','dock_roundtrip','picker_preselected','open_result_export','open_comparison_export'])
parser.add_argument('--receipt',required=True)
args = parser.parse_args()
identity = json.loads((root / 'docs/evidence/export_ui_0105/identity.json').read_text(encoding='utf-8'))
spawn = json.loads((root / 'docs/evidence/export_ui_0105/spawn_transport.json').read_text(encoding='utf-8'))
slot = json.loads(spawn['calls'][0]['response']['result']['content'][0]['text'])['payload']
assert not slot['adopted'] and slot['pid']==identity['pid'] and slot['slotId']==identity['slot']
script = (here / 'common.py').read_text(encoding='utf-8')+'\n'+(here / (args.action+'.py')).read_text(encoding='utf-8')
dest = root / 'docs/evidence/export_ui_0105' / args.receipt
assert dest.parent == root / 'docs/evidence/export_ui_0105' and not dest.exists()
calls = here / (args.action+'_calls.json')
calls.write_text(json.dumps([dict(name='run_python',arguments=dict(slot=identity['slot'],script=script))],ensure_ascii=False),encoding='utf-8')
sys.exit(subprocess.call([sys.executable,str(root / 'tools/mcp_probe.py'),'C:/Users/ciszo/AppData/Roaming/McNeel/Rhinoceros/ai/bin/rhino-mcp-router.exe','--timeout','30','--calls',str(calls),'--output',str(dest)]))
