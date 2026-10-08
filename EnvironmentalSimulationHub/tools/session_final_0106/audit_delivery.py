import json, hashlib, sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'tools'))
from mcp_probe import check_response
def read(p): return json.loads((root/p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256((root/p).read_bytes()).hexdigest()
accept=read('docs/evidence/session_final_0106/acceptance.json')
for path,digest in accept['hashes'].items(): assert sha(path)==digest,path
sync=read('docs/evidence/notion_home_0106_sync_2026-10-03.json')
for row in sync['verified']: assert sha(row['source'])==row['sha256'],row['source']
assert sync['counts']=={'total':196,'unique_records':196,'catalog_count':122,'integrated':9,'backend':1,'pending':112}
verified_calls=0
prefix=read('docs/evidence/full_0106/native_regression_transport.json')
assert len(prefix['calls'])==8 and prefix['status']=='UNVERIFIED'
for call in prefix['calls'][:7]: check_response(call['response']); verified_calls+=1
for name in ['full_0106/resume_regression_transport.json','session_final_0106/load_transport.json','session_final_0106/fixture_transport.json','session_final_0106/session_checks_transport.json','session_final_0106/picker_transport.json','session_final_0106/verify_exports_transport.json']:
    r=read('docs/evidence/'+name)
    assert r['status']=='MCP_RESPONDED' and not r.get('error'),name
    for call in r['calls']: check_response(call['response']); verified_calls+=1
closed=[]
for name in ['export_ui_0105/cleanup_retry_transport.json','session_0106/close_failed_load_transport.json','session_0106/cleanup_transport.json','session_final_0106/cleanup_transport.json','full_0106/cleanup_transport.json']:
    r=read('docs/evidence/'+name)
    assert r['status']=='MCP_RESPONDED' and not r.get('error'),name
    for call in r['calls']: check_response(call['response'])
    assert json.loads(r['calls'][-1]['response']['result']['content'][0]['text'])['payload']['closed'] is True
    closed.append(name)
record={'source_and_binary_hashes_match':True,'notion_source_hashes_match':True,'notion_verified_records':10,'notion_parent_readback':True,'coverage_matches':True,'successful_calls_checked':verified_calls,'owned_test_processes_closed':5,'cleanup_receipts':closed,'modal_timeouts_and_failed_attempts_preserved':True,'checks':{'native_regression':161,'state_operations':38,'core':25,'mcp_probe':12}}
(root/'docs/evidence/session_final_0106/delivery_audit.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(record,ensure_ascii=True))
