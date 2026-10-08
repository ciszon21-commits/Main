from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
scope='archive_resume_0107'; dest=root/'tools'/scope
assert not dest.exists()
dest.mkdir(); (root/'docs/evidence'/scope).mkdir()
for name in ['common.py','prepare_load.py','spawn_calls.json','prepare_cleanup.py','run_action.py']:
    body=(root/'tools/archive_0107'/name).read_text(encoding='utf-8').replace('archive_0107',scope).replace('spawn_retry_transport.json','spawn_transport.json')
    if name=='run_action.py': body=body.replace("'verify_exports','archive_checks'", "'verify_exports','restore','archive_checks'")
    (dest/name).write_text(body,encoding='utf-8')
fixture=json.loads((root/'docs/evidence/archive_0107/fixture.json').read_text(encoding='utf-8'))
(root/'samples/archive_0107/comparison_export_api.json').write_text(fixture['comparison_json'],encoding='utf-8',newline='')
