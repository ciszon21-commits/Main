"""Record new evidence without changing any previous acceptance receipt."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'tools'))
from mcp_probe import check_response
ev = root / 'docs/evidence/native_ui_0105'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
def payload(name):
    receipt = read(ev / name)
    assert receipt['status'] == 'MCP_RESPONDED' and not receipt.get('error')
    response = receipt['calls'][0]['response']
    check_response(response)
    return json.loads(response['result']['content'][0]['text'])['payload']
identity = read(ev / 'identity.json')
focus = payload('keyboard_tab_state.json')
assert focus['focused'][-1] == {'type':'Button','text':'首頁'}
end = payload('keyboard_end_state.json')
assert end['active_module'] == 'SunHoursPanel' and end['focused'][-1]['type'] == 'DropDown'
home = payload('keyboard_home_state.json')
assert home['active_module'] == 'HubOverviewPanel' and home['focused'][-1]['text'] == '首頁'
dock = read(ev / 'dock_guard.json')
check_response(read(ev / 'dock_guard_retry_transport.json')['calls'][0]['response'])
assert dock['passed'] == 3 and dock['pid'] == identity['pid']
dialog = read(ev / 'save_dialog_result.json')
assert dialog['result'] == 'Cancel' and not dialog['file_created']
final = payload('final_state.json')
assert final['objects'] == 0 and final['units'] == 'Millimeters' and final['completed_result'] is None
test = subprocess.run([sys.executable,str(root / 'tests/mcp_probe_checks.py')],capture_output=True,text=True)
assert test.returncode == 0 and 'Ran 12 tests' in test.stderr
audit = []
scanned = 0
for path in sorted((root / 'docs/evidence').rglob('*.json')):
    data = read(path)
    if not isinstance(data, dict) or data.get('status') != 'MCP_RESPONDED' or not isinstance(data.get('calls'),list):
        continue
    scanned += 1
    for index, call in enumerate(data['calls']):
        if 'response' not in call:
            continue
        try:
            check_response(call['response'])
        except RuntimeError as error:
            audit.append({'receipt':path.relative_to(root).as_posix(),'call_index':index,
                          'actual_status':'SCRIPT_FAILED','error':str(error).splitlines()[0]})
report = {'date':'2026-10-03','version':'0.10.5','scope':'MCP runner fix and additional native UI operation checks; plugin binary unchanged',
          'identity':identity,'native_additional_checks':7,'native_groups':{'dock_guard':3,'keyboard_navigation':3,'eto_save_dialog_cancel':1},
          'mcp_tool_tests':12,'tool_test_stdout':test.stdout,'tool_test_stderr':test.stderr,
          'previous_native_168':'Historical home_0105 suite; not rerun in this UI-only batch',
          'picker':'Activation prompt observed, Esc sent, empty state read back; successful geometry selection remains pending',
          'save_dialog_scope':dialog['scope'],'visual_qa':'PENDING: two window capture attempts timed out',
          'dark_theme':'NOT_TESTED','final_state':final,'formal_release':'0.9.2',
          'formal_coverage':{'standalone':9,'backend':1,'pending':112},'v03_started':False,
          'mcp_receipts_audited':scanned,'receipts_reclassified_read_only':audit,
          'source_sha256':{name:hashlib.sha256((root / name).read_bytes()).hexdigest() for name in ['tools/mcp_probe.py','tests/mcp_probe_checks.py']}}
destination = ev / 'acceptance.json'
assert not destination.exists()
destination.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({'native_additional':7,'tool_tests':12,'audited':scanned,'reclassified':audit},ensure_ascii=False))
