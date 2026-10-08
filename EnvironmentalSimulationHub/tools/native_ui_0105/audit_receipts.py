import ast
import hashlib
import json
from pathlib import Path
root = Path(__file__).resolve().parents[2]
ev = root / 'docs/evidence/native_ui_0105'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
acceptance = read(ev / 'acceptance.json')
assert acceptance['native_additional_checks'] == 7 and acceptance['mcp_tool_tests'] == 12
for name, expected in acceptance['source_sha256'].items():
    assert digest(root / name) == expected, name
sync = read(root / 'docs/evidence/notion_native_ui_0105_sync_2026-10-03.json')
assert sync['verified_pages'] == len(sync['records']) == 9
assert sync['counts'] == dict(total=194,unique_records=194,catalog_count=122,formal_integrated=9,formal_backend=1,formal_pending=112)
for record in sync['records']:
    assert record['readback_verified'] and digest(root / record['source']) == record['source_sha256'],record['record_id']
previous = read(root / 'docs/evidence/home_0105/acceptance.json')
for name,expected in previous['evidence_files'].items():
    assert digest(root / 'docs/evidence/home_0105' / name) == expected,name
for path in (root / 'tools/native_ui_0105').glob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
print(json.dumps(dict(status='VERIFIED',native_additional=7,tool_tests=12,notion_readbacks=9,previous_receipt_hashes=len(previous['evidence_files']))))
