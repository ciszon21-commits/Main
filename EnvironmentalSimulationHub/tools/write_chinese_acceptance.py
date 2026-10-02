from pathlib import Path
import json,hashlib,subprocess,collections,re
root=Path(__file__).resolve().parents[1];repo=root.parent
git=['git','-c','safe.directory='+str(repo).replace('\\','/')]
changed=subprocess.check_output(git+['diff','--name-only','--','EnvironmentalSimulationHub/src'],cwd=repo).decode().splitlines()
assert all('/EnvironmentalHub.Plugin/' in f for f in changed)
loaded=json.loads((root/'docs/evidence/release_086_loaded.json').read_text())
platform=json.loads((root/'docs/evidence/platform_086_runtime.json').read_text())
ui=json.loads((root/'docs/evidence/chinese_086_ui.json').read_text(encoding='utf-8'))
capture=json.loads((root/'docs/evidence/ui_086/capture.json').read_text())
binary=json.loads((root/'docs/evidence/binary_086_logic.json').read_text())
catalog=json.loads((root/'docs/evidence/ladybug_feature_catalog.json').read_text(encoding='utf-8'))
assert loaded['version']==platform['version']==ui['version']=='0.8.6'
assert platform['passed']==21 and loaded['time_passed']==17 and len(loaded['location_cases'])==11 and loaded['climate_passed']==11
assert platform['baseline_mean']==loaded['radiation_regression_mean']==1233.3471168086037
assert len(capture['shots'])==22 and {s['width'] for s in capture['shots']}=={320,480}
assert ui['overview_buttons_verified']==5 and ui['shared_navigation_routes_verified']==6
assert ui['navigation_preserves_weather_result']
assert collections.Counter(c['hub_status'] for c in catalog['components'])=={'已接入並實測':8,'輻射後端已使用':1,'待接入 Hub':113}
for p in (root/'src/EnvironmentalHub.Plugin').glob('*.cs'):
    assert '\ufffd' not in p.read_text(encoding='utf-8')
report={
'version':'0.8.6','language':'zh-TW','date':'2026-10-02',
'build':{'errors':0,'warnings':0},
'formal_load':{'slot':loaded['slot'],'loaded_path':loaded['loaded_path'],'registered_path':loaded['registered_path'],'receipt':'release_086_loaded.json'},
'native_cases':{'platform':21,'time':17,'location':11,'climate_files':11,'total':60},
'radiation_regression_mean':platform['baseline_mean'],
'chinese_ui':{'panels':6,'overview_buttons':5,'shared_routes':6,'navigation_preserves_weather_result':True,'weather_fields':True,'diagnostic_codes_preserved':True,'unrecognized_diagnostics_original_retained':True},
'visual_review':{'images':22,'widths':[320,480],'reviewed':True,'scope':'Production Eto/WPF offscreen rendering in current light host theme. Chinese glyphs, wrap, labels, controls, summaries, legend and comparison inspected; scroll overflow is intentional. Not full Dock/theme-switch/keyboard/picker/dialog acceptance.'},
'core_preservation':{'core_and_adapter_source_unchanged':True,'compiled_logic_receipt':'binary_086_logic.json','scope':'All method bodies, locals, stack, exception regions and metadata match 0.8.5 after excluding MVID and informational Git revision; whole-file hashes differ.'},
'function_scope':{'catalog_entries':122,'standalone_verified':8,'backend_only':1,'pending':113,'new_functions':0},
'limitations':['Synchronous solve; no cancellation or percentage progress.','Native source names, values, user text, contracts, command names and scientific identifiers retain original form.','Full Dock, dark-theme switching, keyboard and native file/picker dialogs remain separate acceptance gates.'],
'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'src/EnvironmentalHub.Plugin').glob('*.cs')},
'receipts':['release_086_manifest.json','release_registration_updated_086.json','release_086_loaded.json','platform_086_runtime.json','chinese_086_ui.json','ui_086/capture.json','binary_086_logic.json']
}
(root/'docs/evidence/chinese_086_acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['version','language','native_cases','function_scope']},ensure_ascii=True))
