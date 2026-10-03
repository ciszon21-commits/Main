"""Create the load call only from a successful, non-adopted spawn receipt."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
receipt = json.loads((ROOT / 'docs/evidence/full_0107/spawn_transport.json').read_text(encoding='utf-8'))
assert receipt['status'] == 'MCP_RESPONDED' and not receipt.get('error')
slot = json.loads(receipt['calls'][0]['response']['result']['content'][0]['text'])['payload']
assert not slot['adopted']
calls = [{'name': 'run_python', 'arguments': {'slot': slot['slotId'],
          'script': (HERE / 'load_release.py').read_text(encoding='utf-8')}}]
(HERE / 'load_release_calls.json').write_text(json.dumps(calls, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
print(json.dumps({'slot': slot['slotId'], 'pid': slot['pid']}))
