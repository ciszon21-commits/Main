import hashlib
from pathlib import Path
saved=Path(outputs)/'result_from_native_dialog.json'
assert saved.is_file()
actual=json.loads(saved.read_text(encoding='utf-8-sig'))
assert actual==json.loads(fixture['result_json'])==json.loads(panel.ExportResultJson())
assert json.loads(panel.ExportComparisonJson())==json.loads(fixture['comparison_json']) and panel.ScenarioCount==2
assert not (Path(outputs)/'comparison_from_native_dialog.json').exists()
record={'pid':identity['pid'],'passed':3,'cases':['production_result_dialog_saved_exact_full_contract','comparison_cancel_preserves_two_scenarios_and_interpretation','comparison_cancel_created_no_file'],
        'result_sha256':hashlib.sha256(saved.read_bytes()).hexdigest(),'result_path':str(saved),
        'statistics':actual['NativeResult']['Statistics'],'baseline_mean':fixture['baseline_mean'],
        'comparison_successful_save':'NOT_ACCEPTED: native accessibility unavailable on comparison modal',
        'modal_mcp_timeouts':'Preserved as UNVERIFIED; successful result saving established by filename accessibility readback and exact disk JSON, not by timeout receipts',
        'state':read_state()}
json.dump(record,open(os.path.join(evidence,'export_checks.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(json.dumps({'export_checks':3,'result_saved_and_exact':True,'comparison_save':'NOT_ACCEPTED'}))
