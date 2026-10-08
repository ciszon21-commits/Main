"""Read-only audit of versioned evidence, synchronized source hashes and catalog."""
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[2]
ev = root / 'docs/evidence/home_0105'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
acceptance = read(ev / 'acceptance.json')
assert acceptance['native_checks'] == 168
assert sum(acceptance['native_suites'].values()) == 168
for name, expected in acceptance['evidence_files'].items():
    assert digest(ev / name) == expected, name
manifest = read(ev / 'build_manifest.json')
for name, expected in manifest['source_files'].items():
    assert digest(root / name) == expected, name
for name, expected in manifest['files'].items():
    assert digest(root / 'artifacts/home-build/0.10.5' / name) == expected, name
sync = read(root / 'docs/evidence/notion_home_0105_sync_2026-10-03.json')
assert sync['verified_pages'] == len(sync['records']) == 9
assert sync['counts'] == dict(total=193, unique_records=193, catalog_count=122,
                              formal_integrated=9, formal_backend=1, formal_pending=112)
for record in sync['records']:
    assert record['readback_verified']
    assert digest(root / record['source']) == record['source_sha256'], record['record_id']
catalog = read(root / 'docs/evidence/ladybug_feature_catalog.json')
html = (root / 'docs/LADYBUG_FEATURE_TABLE.html').read_text(encoding='utf-8')
entries = json.loads(re.search(r'const entries\s*=\s*(\[.*?\]);', html, re.S)[1])
assert entries == catalog['components'] and len(entries) == 122
sunhours = next(c for c in entries if c['id'] == 'LB-061')
assert sunhours['candidate_home_version'] == '0.10.5'
assert 'HOME_VALIDATION_0105.md' in (root / 'docs/LADYBUG_FEATURE_TABLE.md').read_text(encoding='utf-8').splitlines()[0]
for version in ['home_0104', 'home_0105']:
    for path in (root / 'samples' / version).rglob('*.json'):
        assert b'\r\r\n' not in path.read_bytes(), str(path)
        read(path)
print(json.dumps(dict(status='VERIFIED', native=168, notion_readbacks=9,
                      catalog_entries=122, receipt_hashes=len(acceptance['evidence_files']))))
