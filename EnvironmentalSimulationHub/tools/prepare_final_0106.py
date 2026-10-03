from pathlib import Path
root=Path(__file__).resolve().parents[1]
assert not (root/'tools/session_final_0106').exists() and not (root/'tools/full_0106').exists(), 'Preserve prepared final test sources'
dest=root/'tools/session_final_0106'; dest.mkdir(exist_ok=True)
for p in (root/'tools/session_0106').glob('*.py'):
    if p.name in ['prepare_retry.py']: continue
    body=p.read_text(encoding='utf-8').replace('session_0106','session_final_0106')
    (dest/p.name).write_text(body,encoding='utf-8')
(dest/'spawn_calls.json').write_text((root/'tools/native_ui_0105/spawn_calls.json').read_text(encoding='utf-8'),encoding='utf-8')
(root/'docs/evidence/session_final_0106').mkdir(exist_ok=True)
dest=root/'tools/full_0106'; dest.mkdir(exist_ok=True)
for name in ['prepare_validation.py','selection_rebind_checks.py','load_release.py','prepare_load.py']:
    p=root/'tools/home_0105'/name
    body=p.read_text(encoding='utf-8').replace('home_0105','full_0106').replace('0.10.5','0.10.6')
    (dest/name).write_text(body,encoding='utf-8')
(dest/'spawn_calls.json').write_text((root/'tools/native_ui_0105/spawn_calls.json').read_text(encoding='utf-8'),encoding='utf-8')
(root/'docs/evidence/full_0106').mkdir(exist_ok=True)
print('Final candidate scopes prepared')
