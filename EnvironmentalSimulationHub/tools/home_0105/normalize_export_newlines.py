"""Normalize generated sample export newlines without changing JSON values or receipts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
records = []
for version in ['home_0105']:
    folder = ROOT / 'samples' / version / 'visual_sunhours_0102'
    for name in ['comparison.json', 'result.json', 'result_with_presentation.json']:
        path = folder / name
        if not path.exists():
            continue
        before = path.read_bytes()
        after = before.replace(b'\r\r\n', b'\n').replace(b'\r\n', b'\n')
        assert json.loads(before.decode('utf-8-sig')) == json.loads(after.decode('utf-8-sig'))
        if before == after:
            continue
        path.write_bytes(after)
        records.append({'path': path.relative_to(ROOT).as_posix(),
            'raw_sha256': hashlib.sha256(before).hexdigest(),
            'normalized_sha256': hashlib.sha256(after).hexdigest(), 'json_values_equal': True})
if records:
    target = ROOT / 'docs/evidence/home_0105/export_newline_normalization.json'
    target.write_text(json.dumps({'scope': 'Generated sample JSON CRCRLF to LF only; all JSON values preserved; historical evidence receipts untouched',
                      'files': records}, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'normalized': len(records), 'json_values_equal': True}))
