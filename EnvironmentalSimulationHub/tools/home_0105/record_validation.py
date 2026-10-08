"""Aggregate this candidate's actual evidence without changing historical receipts."""
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / 'docs/evidence/home_0105'
RT = EV / 'runtime'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

identity = read(EV / 'identity.json')
for name in ['load_transport', 'native_regression_transport', 'presentation_export_transport']:
    transport = read(EV / (name + '.json'))
    assert transport['status'] == 'MCP_RESPONDED' and not transport.get('error')
loaded = read(RT / 'release_0101_loaded.json')
assert loaded['version'] == '0.10.5'
assert loaded['radiation_regression_mean'] == 1233.3471168086037
suites = {'location_climate_time': sum(loaded[k + '_passed'] for k in ['location', 'climate', 'time'])}
for name in ['platform', 'sunpath', 'sunpath_text', 'sunpath_transfer', 'sunhours', 'workspace']:
    file = {'sunpath_text': 'sunpath_0101_text.json', 'sunpath_transfer': 'sunpath_0101_transfer.json'}.get(name, name + '_0101_runtime.json')
    result = read(RT / file)
    assert result['version'] == '0.10.5'
    suites[name] = result['passed']
assert sum(suites.values()) == 154
rebind = read(EV / 'selection_rebind_checks.json')
assert rebind['passed'] == 7 and rebind['pid'] == identity['pid']
suites['selection_rebind'] = rebind['passed']
width = read(EV / 'floating_width_checks.json')
assert width['passed'] == 7 and width['pid'] == identity['pid']
suites['floating_width'] = width['passed']
assert read(EV / 'core_checks.json')['Passed'] == 25
assert read(EV / 'export_roundtrip.json')['passed'] == 3
capture = read(RT / 'ui_0101/capture.json')
assert len(capture['shots']) == 44
assert all(s['width'] == s['actual_width'] and s['width'] in [320, 480] for s in capture['shots'])
viewport = read(RT / 'ui_0101/viewport_capture.json')
assert viewport['version'] == '0.10.5' and len(viewport['paths']) == 2
assert viewport['statistics'] == {'Count': 256, 'Minimum': 7, 'Maximum': 13, 'Mean': 9.08203125}
for path in [Path(s['path']) for s in capture['shots']] + [Path(p) for p in viewport['paths']]:
    path.resolve().relative_to(EV.resolve())
    assert path.stat().st_size > 1000
test = subprocess.run(['python', str(ROOT / 'tests/mcp_probe_checks.py')], capture_output=True, text=True)
assert test.returncode == 0, test.stderr
write(EV / 'mcp_probe_checks.json', {'passed': 8, 'exit_code': 0, 'stdout': test.stdout, 'stderr': test.stderr})
build = ROOT / 'artifacts/home-build/0.10.5'
write(EV / 'build_manifest.json', {'version': '0.10.5', 'build_errors': 0, 'build_warnings': 0,
    'sdk': '8.0.425', 'identity': identity, 'registered_path': loaded['registered_path'],
    'load_scope': 'Explicit SDK candidate load; registration readback is not formal deployment acceptance',
    'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'source_files': {p.relative_to(ROOT).as_posix(): digest(p) for p in [ROOT / 'src/EnvironmentalHub.Plugin/HubWorkspacePanel.cs', ROOT / 'src/EnvironmentalHub.Plugin/EnvironmentalHub.Plugin.csproj']},
    'files': {p.name: digest(p) for p in sorted(build.iterdir()) if p.suffix in ['.rhp', '.dll', '.json']}})
write(EV / 'ui_review.json', {'version': '0.10.5', 'date': '2026-10-03', 'reviewed_images': 44,
    'method': '11 contact sheets at original pixel size; both real viewport PNGs inspected',
    'widths': [320, 480], 'theme': 'current light Eto/WPF theme', 'viewport_images_reviewed': 2,
    'sunhours_numeric_and_legend_width_defects': 'NOT_REPRODUCED',
    'floating_initial_width': '500 outer / 490 content; 7 native checks passed',
    'full_native_dock': 'NOT_ACCEPTED', 'native_dark_theme': 'NOT_TESTED',
    'keyboard_picker_file_dialog': 'NOT_TESTED',
    'capture_error': 'window capture timed out: timed out waiting on channel',
    'scope': 'Production offscreen controls and real 3D viewport; full native interaction remains pending'})
catalog_path = ROOT / 'docs/evidence/ladybug_feature_catalog.json'
catalog = read(catalog_path)
installed = Path('C:/Program Files/ladybug_tools/grasshopper/ladybug_grasshopper/user_objects')
matches = sum(digest(installed / c['file']).lower() == c['sha256'].lower() for c in catalog['components'])
assert len(catalog['components']) == matches == 122
acceptance = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'version': '0.10.5',
    'status': 'NATIVE_VERIFIED_FULL_UI_PENDING', 'formal_release': '0.9.2',
    'formal_coverage': {'standalone': 9, 'backend': 1, 'pending': 112},
    'candidate_coverage': {'standalone': 10, 'backend': 1, 'pending': 111},
    'native_checks': sum(suites.values()), 'native_suites': suites, 'core_checks': 25,
    'mcp_protocol_checks': 8, 'export_roundtrip_checks': 3, 'offscreen_ui_images_reviewed': 44,
    'real_viewport_images_reviewed': 2, 'ladybug_inventory_hash_matches': matches,
    'radiation_mean_kwh_m2': loaded['radiation_regression_mean'], 'sunhours_taipei': viewport['statistics'],
    'remaining_gates': ['native narrow/wide Dock', 'native theme switching', 'keyboard and picker/file dialogs', 'formal release/pilot'],
    'notion_sync_receipt': 'docs/evidence/notion_home_0105_sync_2026-10-03.json',
    'historical_receipts_modified': False,
    'width_issue': {'id': 'UI-WIDTH-0103', 'status': 'FLOATING_FIXED_NATIVE_VISUAL_QA_PENDING', 'scope': 'Measured actual floating container; docked layout not accepted'},
    'rejected_intermediate_candidate': 'home_0104/candidate_disposition.json',
    'evidence_files': {p.relative_to(EV).as_posix(): digest(p) for p in sorted(EV.rglob('*.json')) if p.name != 'acceptance.json'}}
write(EV / 'acceptance.json', acceptance)
candidate = next(c for c in catalog['components'] if c['id'] == 'LB-061')
candidate.update(candidate_source_version='0.10.5', candidate_home_version='0.10.5',
    candidate_home_status='日照時數 45 項及重綁 7 項通過；全平台 168 項（含浮動寬度 7 項）通過；44 張淺色離屏版面已檢視；初始浮動寬度已修正，完整原生 UI 待驗收',
    candidate_home_evidence='home_0105/acceptance.json')
write(catalog_path, catalog)
md_path = ROOT / 'docs/LADYBUG_FEATURE_TABLE.md'
md = md_path.read_text(encoding='utf-8')
md = re.sub(r'^候選接續註記[^\n]*', '候選接續註記（2026-10-03）：正式 9／1／112 保留；LB-061 在 0.10.5 通過 45 項日照與 7 項重綁，全平台 168 項（含浮動寬度 7 項）；44 張淺色離屏版面已檢視，初始浮動寬度已修正，完整原生 UI 待驗收。[本輪驗證](HOME_VALIDATION_0105.md)。', md, count=1, flags=re.M)
md_path.write_text(md, encoding='utf-8', newline='\n')
html_path = ROOT / 'docs/LADYBUG_FEATURE_TABLE.html'
html = html_path.read_text(encoding='utf-8')
html, count = re.subn(r'const entries\s*=\s*\[.*?\];', lambda _: 'const entries=' + json.dumps(catalog['components'], ensure_ascii=False) + ';', html, count=1, flags=re.S)
assert count == 1
html = html.replace('LB-061 候選 0.10.2 已在家用機通過原生 45 項及窄／寬淺色離屏檢視；初始浮動寬度已修正，完整原生 UI 待驗收，正式交付狀態未增加。', 'LB-061 候選 0.10.5：45 項日照＋7 項重綁，全平台 168 項（含浮動寬度 7 項）通過；44 張淺色離屏檢視，初始浮動寬度已修正，完整原生 UI 待驗收，正式交付狀態未增加。')
html_path.write_text(html, encoding='utf-8', newline='\n')
print(json.dumps({'native': sum(suites.values()), 'core': 25, 'protocol': 8, 'export': 3, 'inventory': matches}))
