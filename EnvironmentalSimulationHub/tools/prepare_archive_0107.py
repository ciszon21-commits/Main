from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
assert not (root/'tools/archive_0107').exists()
for scope,source in [('archive_0107','session_final_0106'),('full_0107','full_0106')]:
    dest=root/'tools'/scope; dest.mkdir()
    (root/'docs/evidence'/scope).mkdir()
    names=['common.py','fixture.py','prepare_load.py','session_checks.py','prepare_cleanup.py'] if scope=='archive_0107' else ['load_release.py','prepare_load.py','prepare_validation.py','selection_rebind_checks.py']
    for name in names:
        body=(root/'tools'/source/name).read_text(encoding='utf-8').replace(source,scope).replace('0.10.6','0.10.7')
        if name=='prepare_load.py': body=body.replace("'0.10.5','0.10.7'", "'0.10.5','0.10.7'")
        (dest/name).write_text(body,encoding='utf-8')
    (dest/'spawn_calls.json').write_text((root/'tools'/source/'spawn_calls.json').read_text(encoding='utf-8'),encoding='utf-8')
body=(root/'tools/session_0106/Set-CandidatePath.ps1').read_text(encoding='utf-8').replace('session_0106','archive_0107').replace('0.10.6','0.10.7')
(root/'tools/archive_0107/Set-CandidatePath.ps1').write_text(body,encoding='utf-8')
body=(root/'tools/session_final_0106/run_action.py').read_text(encoding='utf-8').replace('session_final_0106','archive_0107')
body=body.replace("'verify_exports'", "'verify_exports','archive_checks','open_comparison_export','open_import','capture','verify_dialog'")
(root/'tools/archive_0107/run_action.py').write_text(body,encoding='utf-8')
