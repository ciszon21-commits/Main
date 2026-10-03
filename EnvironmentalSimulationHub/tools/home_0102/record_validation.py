"""Record verified home-machine scope without promoting incomplete UI acceptance."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / 'docs/evidence/home_0102'
RUNTIME = EV / 'runtime'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, encoding='utf-8').strip()


preflight = read(EV / 'environment_preflight.json')
assert preflight['Failures'] == 0 and preflight['Warnings'] == 0
loaded = read(RUNTIME / 'release_0101_loaded.json')
assert loaded['version'] == '0.10.2'
assert loaded['radiation_regression_mean'] == 1233.3471168086037
suites = {'existing_location_climate_time': loaded['location_passed'] + loaded['climate_passed'] + loaded['time_passed']}
for name in ['platform', 'sunpath', 'sunpath_text', 'sunpath_transfer', 'sunhours', 'workspace']:
    filename = {'sunpath_text': 'sunpath_0101_text.json', 'sunpath_transfer': 'sunpath_0101_transfer.json'}.get(name, name + '_0101_runtime.json')
    result = read(RUNTIME / filename)
    assert result['version'] == '0.10.2'
    suites[name] = result['passed']
assert sum(suites.values()) == 154
core = read(EV / 'core_checks.json')
assert core['Passed'] == 25
capture = read(RUNTIME / 'ui_0101/capture.json')
assert len(capture['shots']) == 44
assert all(s['actual_width'] == s['width'] and s['width'] in [320, 480] for s in capture['shots'])
export = read(EV / 'export_roundtrip.json')
assert export['passed'] == 3 and export['version'] == '0.10.2'
viewport = read(RUNTIME / 'ui_0101/viewport_capture.json')
assert len(viewport['paths']) == 2
assert viewport['statistics'] == {'Count': 256, 'Minimum': 7, 'Maximum': 13, 'Mean': 9.08203125}
for path in [Path(s['path']) for s in capture['shots']] + [Path(p) for p in viewport['paths']]:
    path.resolve().relative_to(EV.resolve())
    assert path.is_file() and path.stat().st_size > 1000

catalog_path = ROOT / 'docs/evidence/ladybug_feature_catalog.json'
catalog = read(catalog_path)
installed_root = Path('C:/Program Files/ladybug_tools/grasshopper/ladybug_grasshopper/user_objects')
inventory = []
for component in catalog['components']:
    path = installed_root / component['file']
    actual = digest(path) if path.is_file() else None
    inventory.append({'id': component['id'], 'file': component['file'], 'sha256': actual,
                      'matches_source_inventory': actual is not None and actual.lower() == component['sha256'].lower()})
assert len(inventory) == 122
write(EV / 'ladybug_inventory.json', {'scope': 'File/hash inventory only; not 122 solver acceptances',
                                    'count': len(inventory), 'matching': sum(i['matches_source_inventory'] for i in inventory),
                                    'components': inventory})

test = subprocess.run(['python', str(ROOT / 'tests/mcp_probe_checks.py')], capture_output=True, text=True)
assert test.returncode == 0, test.stderr
write(EV / 'mcp_probe_checks.json', {'passed': 8, 'exit_code': test.returncode,
                                    'stdout': test.stdout, 'stderr': test.stderr,
                                    'scope': 'Protocol/error-envelope regression; no Rhino UI actions'})
build = ROOT / 'artifacts/home-build/0.10.2'
files = {p.name: digest(p) for p in sorted(build.iterdir()) if p.suffix in ['.dll', '.rhp', '.json'] and p.name != 'home_validation_manifest.json'}
write(EV / 'build_manifest.json', {'version': '0.10.2', 'build_errors': 0, 'build_warnings': 0,
                                  'sdk': '8.0.425', 'runtime': export['runtime'], 'files': files,
                                  'source_head': git('rev-parse', 'HEAD'),
                                  'source_branch': git('branch', '--show-current'),
                                  'source_changes': git('status', '--short', '--', 'src'),
                                  'scope': 'Home build observed in this run; native load verified separately; full UI pending'})
write(EV / 'ui_review.json', {
    'date': '2026-10-03', 'version': '0.10.2', 'reviewed_images': 44,
    'widths': [320, 480], 'theme': 'current light Eto/WPF host theme',
    'review_method': '11 contact sheets at original pixel size plus individual SunHours renders',
    'sunhours_legend_and_input_width_defects': 'NOT_REPRODUCED',
    'readable_fields': ['grid', 'sensor offset', 'CPU', 'target minimum/maximum', 'display offset', 'h legend samples'],
    'viewport_images_reviewed': 2, 'viewport_native_colors': 7,
    'full_native_dock': 'NOT_ACCEPTED', 'native_dark_theme': 'NOT_TESTED',
    'keyboard_picker_file_dialog': 'NOT_TESTED',
    'capture_failures': ['FrameArrived timed out: timed out waiting on channel', 'window capture timed out: timed out waiting on channel'],
    'scope': 'Offscreen production controls and real native 3D viewport; not full Dock or native theme/dialog acceptance'
})
acceptance = {
    'recorded_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
    'date': '2026-10-03', 'version': '0.10.2', 'status': 'NATIVE_VERIFIED_FULL_UI_PENDING',
    'formal_release': '0.9.2', 'formal_coverage': {'standalone': 9, 'backend': 1, 'pending': 112},
    'candidate_coverage': {'standalone': 10, 'backend': 1, 'pending': 111},
    'native_checks': 154, 'native_suites': suites, 'core_checks': 25, 'mcp_protocol_checks': 8,
    'export_roundtrip_checks': 3, 'ui_images': 44, 'real_viewport_images': 2,
    'rhino': export['rhino'], 'runtime': export['runtime'], 'sdk': '8.0.425',
    'ladybug_inventory_count': 122, 'ladybug_inventory_hash_matches': sum(i['matches_source_inventory'] for i in inventory),
    'eddy_loaded_assemblies': export['eddy_loaded_assemblies'], 'cfd_solve': 'NOT_TESTED',
    'radiation_mean_kwh_m2': loaded['radiation_regression_mean'],
    'sunhours_taipei_sample': viewport['statistics'],
    'historical_evidence_modified': False,
    'remaining_gates': ['native Dock at narrow/wide widths', 'native theme switching', 'keyboard and native picker/file dialogs', 'formal release/pilot and Notion synchronization'],
    'next_feature': 'Sky Mask after current UI acceptance',
    'notion_sync': 'Candidate progress synced; formal release unchanged. See docs/evidence/notion_home_0102_sync_2026-10-03.json for current readback and stable IDs.',
    'evidence_files': {p.relative_to(EV).as_posix(): digest(p) for p in sorted(EV.rglob('*.json'))
                       if p.name != 'acceptance.json' and 'ui_review' not in p.parts}
}
write(EV / 'acceptance.json', acceptance)

candidate = next(c for c in catalog['components'] if c['id'] == 'LB-061')
candidate['candidate_source_version'] = '0.10.2'
candidate['candidate_home_version'] = '0.10.2'
candidate['candidate_home_status'] = '本機原生 45 項通過；320／480 px 淺色離屏版面已檢視；完整原生 Dock／深色／鍵盤／對話框待驗收'
candidate['candidate_home_evidence'] = 'home_0102/acceptance.json'
write(catalog_path, catalog)
md_path = ROOT / 'docs/LADYBUG_FEATURE_TABLE.md'
md = md_path.read_text(encoding='utf-8')
md = re.sub(r'^候選交接註記[^\n]*', '候選接續註記（2026-10-03）：正式 9／1／112 保留；LB-061 在 0.10.2 本機原生 45 項通過，窄／寬淺色離屏版面已檢視；完整原生 UI 待驗收。[本機驗收](HOME_VALIDATION_0102.md)。', md, count=1)
md_path.write_text(md, encoding='utf-8', newline='\n')
html_path = ROOT / 'docs/LADYBUG_FEATURE_TABLE.html'
html = html_path.read_text(encoding='utf-8')
html, replacements = re.subn(r'const entries\s*=\s*\[.*?\];', lambda _: 'const entries=' + json.dumps(catalog['components'], ensure_ascii=False) + ';', html, count=1, flags=re.S)
assert replacements == 1
html = html.replace("e.candidate_status+' · '+e.candidate_version+'；目前程式碼 '+e.candidate_source_version+' 僅建置，未完成新版本驗收。'",
                    "e.candidate_status+' · '+e.candidate_version+'；目前程式碼 '+e.candidate_source_version+'：'+(e.candidate_home_status||'新版本驗收待完成。')")
html = html.replace('LB-061 候選已在 0.10.1 原生實測；0.10.2 窄版排版修正僅建置，正式交付狀態未增加。',
                    'LB-061 候選 0.10.2 已在家用機通過原生 45 項及窄／寬淺色離屏檢視；完整原生 UI 待驗收，正式交付狀態未增加。')
html_path.write_text(html, encoding='utf-8', newline='\n')
print(json.dumps({'native': sum(suites.values()), 'core': 25, 'protocol': 8, 'exports': 3,
                  'ui': 44, 'inventory_matching': acceptance['ladybug_inventory_hash_matches'],
                  'status': acceptance['status']}, ensure_ascii=False))
