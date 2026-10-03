import json, hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[2]
ev=root/'docs/evidence/session_final_0106'; full=root/'docs/evidence/full_0106'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
identity=read(ev/'identity.json'); full_identity=read(full/'identity.json')
assert identity['version']==full_identity['version']=='0.10.6'
assert read(ev/'session_checks.json')['passed']==33
assert read(ev/'picker_checks.json')['passed']==2
assert read(ev/'export_checks.json')['passed']==3
release=read(full/'runtime/release_0101_loaded.json')
suites={'location_climate_time':release['location_passed']+release['climate_passed']+release['time_passed']}
for name,key in [('platform_0101_runtime','radiation_platform'),('sunpath_0101_runtime','sunpath'),('sunpath_0101_transfer','sunpath_transfer'),('sunpath_0101_text','sunpath_text'),('sunhours_0101_runtime','sunhours'),('workspace_0101_runtime','workspace')]:
    suites[key]=read(full/('runtime/'+name+'.json'))['passed']
suites['selection_rebind']=read(full/'selection_rebind_checks.json')['passed']
assert sum(suites.values())==161
first=read(full/'native_regression_transport.json'); resume=read(full/'resume_regression_transport.json')
assert first['status']=='UNVERIFIED' and len(first['calls'])==8
assert resume['status']=='MCP_RESPONDED' and not resume.get('error')
files=['src/EnvironmentalHub.Plugin/HubWorkspacePanel.cs','src/EnvironmentalHub.Plugin/HubPlugin.cs','src/EnvironmentalHub.Plugin/EnvironmentalHub.Plugin.csproj','artifacts/home-build/0.10.6/EnvironmentalHub.Plugin.rhp','artifacts/home-build/0.10.6/EnvironmentalHub.Core.dll','artifacts/home-build/0.10.6/EnvironmentalHub.Adapters.dll']
record={'date':'2026-10-03','candidate':'0.10.6','formal':'0.9.2','formal_coverage':[9,1,112],'candidate_coverage':[10,1,111],
        'build':{'errors':0,'warnings':0,'output':'artifacts/home-build/0.10.6'},'identities':[identity,full_identity],
        'native_regression':{'passed':161,'suites':suites,'successful_prefix_calls':7,'resumed_calls':2,'legacy_test_change':'Retain view identity and snapshots after close/reopen; disposable shell identity is not required'},
        'additional_checks':{'state_and_document_isolation':33,'production_preselection':2,'production_export_and_comparison_cancel':3,'total':38},
        'core_checks':{'passed':25,'command':'dotnet artifacts/checks/0.10.6/EnvironmentalHub.Core.Checks.dll artifacts/weather_half_timezone.epw samples/full_0106/core_checks','evidence_scope':'25 cases observed in successful console output; test output contains intentional invalid.epw fixture','weather_sha256':sha(root/'artifacts/weather_half_timezone.epw')},
        'mcp_probe_checks':{'passed':12,'test':'tests/mcp_probe_checks.py'},
        'result':{'count':256,'unshaded_mean_h':13,'shaded_mean_h':9.57421875,'result_file':'samples/session_final_0106/result_from_native_dialog.json','sha256':sha(root/'samples/session_final_0106/result_from_native_dialog.json'),'exact_json_readback':True},
        'open_gates':['full dock visual layout','native dark theme','full keyboard and mouse postselection','successful native comparison SaveFileDialog','cross-machine pilot'],
        'not_rerun':['0.10.5 floating width 7 cases','0.10.5 44 light offscreen images and 2 viewport images'],
        'failed_attempts_preserved':['export_ui_0105/dock_roundtrip.json: real result/scenario loss in old version','export_ui_0105/cleanup_transport.json: ObjectTable.Count includes deleted objects; cleanup_retry succeeded','session_0106/load_transport.json: fresh process auto-loaded registered 0.10.5; empty process closed, registration backed up and changed','session_0106/session_checks_transport.json: transient solo visibility intentionally releases on navigation; corrected test setup','full_0106/native_regression_transport.json: obsolete shell reference assertion; same-view and full-state resume passed','native modal open MCP timeouts remain UNVERIFIED; saving proven separately by native filename and exact file readback','initial Core invocation had wrong project path; then locked default output and missing CLI args; isolated build and explicit-argument 25-case run passed'],
        'hashes':{f:sha(root/f) for f in files},'V02_formal_delivery':False,'V03_started':False}
(ev/'acceptance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
summary='0.10.6 修正 Rhino 停靠重建外框後遺失模組資料：依文件保存八個快取內部模組，保留草稿、日照結果與情境；外框釋放前卸下模組，文件關閉／Rhino 結束才釋放。建置零錯誤／零警告；本輪 161 項既有原生回歸、33 項狀態與文件隔離、2 項正式 picker 預選、3 項正式結果匯出／比較取消檢查通過，另 Core 25、MCP 工具 12。256 點日照無遮蔭平均 13 h、遮蔭 9.57421875 h；正式結果存檔 JSON 完全一致。比較成功存檔、完整 Dock 版面／深色／全鍵盤／滑鼠後選及跨機仍待驗收。正式 0.9.2／9、1、112，候選 10／1／111；V02 未正式交付，V03 未啟動。'
section='## 2026-10-03 · 0.10.6 停靠資料保留與正式匯出\n\n'+summary+'\n\n[本輪詳細範圍](HOME_VALIDATION_0106.md) · [本輪 receipt](evidence/session_final_0106/acceptance.json) · [視覺化精華](DEVELOPMENT_HIGHLIGHTS.md)。Notion 依使用者要求分成詳細資料、重點整理與視覺化精華；只在有實際進度時更新，沿用既有資料庫與固定 ID。前輪 0.10.5 的浮動寬度 7 項與 44 張離屏圖未重跑，以下保留歷史證據。\n\n'
paths=['README.md','docs/PROJECT_STATUS.md','docs/KNOWLEDGE_INDEX.md','docs/BUILD_AND_RUN.md','docs/ROADMAP.md','docs/L2_VISUAL_PLAN.md','docs/HOME_TRANSFER.md','docs/LADYBUG_DEVELOPMENT_PLAN.md','docs/DEVELOPMENT_REVIEW_2026-10-01.md']
for f in paths:
    p=root/f; body=p.read_text(encoding='utf-8')
    if not body.startswith('## 2026-10-03 · 0.10.6'):
        p.write_text(section.replace('(HOME_VALIDATION_0106.md)','(docs/HOME_VALIDATION_0106.md)').replace('(evidence/session_final_0106/acceptance.json)','(docs/evidence/session_final_0106/acceptance.json)').replace('(DEVELOPMENT_HIGHLIGHTS.md)','(docs/DEVELOPMENT_HIGHLIGHTS.md)')+body if f=='README.md' else section+body,encoding='utf-8')
(ev/'summary.txt').write_text(summary,encoding='utf-8')
print(json.dumps({'native':161,'additional':38,'core':25,'mcp':12,'formal_unchanged':True}))
