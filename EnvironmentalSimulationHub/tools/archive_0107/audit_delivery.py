import json, hashlib, sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'tools'))
from mcp_probe import check_response
def read(p): return json.loads((root/p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256((root/p).read_bytes()).hexdigest()
receipt=read('docs/evidence/archive_0107/acceptance.json')
assert all(sha(p)==v for p,v in receipt['source_binary_sha256'].items())
sync=read('docs/evidence/notion_home_0107_sync_2026-10-03.json')
assert len(sync['records_readback'])==11
assert all(sha(p['source'])==p['source_sha256'] for p in sync['records_readback'])
assert sync['visual']['mermaid_diagrams']==4 and sync['counts']=={'total':197,'unique_ids':197,'catalog':122,'integrated':9,'backend':1,'pending':112}
files=['archive_0107/load_corrected_transport.json','archive_0107/archive_checks_transport.json','archive_0107/fixture_transport.json','archive_0107/session_checks_corrected_transport.json','full_0107/load_final_transport.json','full_0107/native_regression_final_transport.json','full_0107/capture_comparison_transport.json','full_0107/cleanup_transport.json','archive_resume_0107/load_transport.json','archive_resume_0107/restore_transport.json','archive_resume_0107/capture_transport.json','archive_resume_0107/owned_exit_transport.json']
calls=0
for path in files:
    transport=read('docs/evidence/'+path)
    assert transport['status']=='MCP_RESPONDED' and not transport.get('error')
    for call in transport['calls']: check_response(call['response']); calls+=1
assert read('docs/evidence/archive_resume_0107/owned_exit_guard.json')['empty_unmodified']
cleanup=read('docs/evidence/archive_0107/process_cleanup_readback.json')
assert cleanup['test_pids']==[28756,28280,18536,20924] and cleanup['remaining_test_pids']==[] and cleanup['user_rhino_21244_present']
proof={'candidate':'0.10.7','source_binary_sha256_match':True,'notion_11_source_sha256_match':True,'successful_mcp_calls_checked':calls,'native_total':161,'archive_contract_and_runtime':104,'core':25,'mcp_tool':12,'images_reviewed':4,'formal_coverage':[9,1,112],'candidate_coverage':[10,1,111],'owned_process_ids':[28756,28280,18536,20924],'lifecycle_evidence':{'28756':'Exited before load; no model script executed','28280':'Confirmed unsupported API in test Timer callback; recorded .NET stack','18536':'Owned object inventory, empty/unmodified and successful close_slot','20924':'Router re-adopted owned process; original non-adopted spawn + empty/unmodified guard; native Exit succeeded'},'native_dialog_success_claimed':False,'notion_504_retry':'Targeted edits succeeded; full readback and original child database preserved'}
(root/'docs/evidence/archive_0107/delivery_audit.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(proof,ensure_ascii=True))
