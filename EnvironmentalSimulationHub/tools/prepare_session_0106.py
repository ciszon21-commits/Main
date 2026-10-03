"""Prepare versioned tests without rewriting historical fixtures or receipts."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
for old, new in [('tools/export_ui_0105','tools/session_0106')]:
    dest = root / new
    assert not dest.exists(), 'Preserve prepared test sources; use a new versioned scope instead'
    dest.mkdir(exist_ok=True)
    for source in (root / old).glob('*.py'):
        if source.name == 'prepare_cleanup.py':
            continue
        body = source.read_text(encoding='utf-8')
        body = body.replace('export_ui_0105','session_0106')
        body = body.replace("=='0.10.5.0'", "=='0.10.6.0'")
        if source.name == 'prepare_load.py':
            body = body.replace(".replace('docs/evidence/home_0105','docs/evidence/session_0106')", ".replace('docs/evidence/home_0105','docs/evidence/session_0106').replace('0.10.5','0.10.6')")
        body = body.replace("select = next(c for c in panel.Controls if False) if False else None\n", '')
        (dest / source.name).write_text(body,encoding='utf-8')
evidence = root / 'docs/evidence/session_0106'
evidence.mkdir(exist_ok=True)
(root / 'tools/session_0106/spawn_calls.json').write_text(
    (root / 'tools/native_ui_0105/spawn_calls.json').read_text(encoding='utf-8'),encoding='utf-8')
print('Prepared 0.10.6 owned-session tests')
