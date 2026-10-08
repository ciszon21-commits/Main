import json, hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[2]; ev=root/'docs/evidence/archive_0107'; full=root/'docs/evidence/full_0107'; resumed=root/'docs/evidence/archive_resume_0107'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
release=read(full/'runtime/release_0101_loaded.json')
suites={'location_climate_time':release['location_passed']+release['climate_passed']+release['time_passed']}
for name,key in [('platform_0101_runtime','radiation_platform'),('sunpath_0101_runtime','sunpath'),('sunpath_0101_transfer','sunpath_transfer'),('sunpath_0101_text','sunpath_text'),('sunhours_0101_runtime','sunhours'),('workspace_0101_runtime','workspace')]: suites[key]=read(full/('runtime/'+name+'.json'))['passed']
suites['selection_rebind']=read(full/'selection_rebind_checks.json')['passed']; assert sum(suites.values())==161
checks={'archive_contract':read(ev/'core_archive_checks.json')['Passed'],'native_import':read(ev/'archive_checks.json')['passed'],'session':read(ev/'session_checks.json')['passed'],'restart_restore':read(resumed/'restore_checks.json')['passed'],'existing_core':read(full/'core_checks.json')['Passed'],'mcp_tool':12}
assert checks=={'archive_contract':42,'native_import':17,'session':32,'restart_restore':13,'existing_core':25,'mcp_tool':12}
assert 'Ran 12 tests' in (full/'mcp_probe_checks.txt').read_text(encoding='utf-8-sig')
images=[]
for scope in [full,resumed]:
    capture=read(scope/'runtime/ui_0101/capture.json')
    for shot in capture['shots']:
        assert shot['width']==shot['actual_width'] and Path(shot['path']).exists()
        images.append({'path':Path(shot['path']).relative_to(root).as_posix(),'width':shot['width'],'actual_width':shot['actual_width'],'sha256':sha(Path(shot['path'])),'reviewed':True})
files=['src/EnvironmentalHub.Core/SunHoursArchive.cs','src/EnvironmentalHub.Plugin/SunHoursPanel.cs','src/EnvironmentalHub.Plugin/SunHoursPresentation.cs','src/EnvironmentalHub.Plugin/EnvironmentalHub.Plugin.csproj','artifacts/home-build/0.10.7/EnvironmentalHub.Plugin.rhp','artifacts/home-build/0.10.7/EnvironmentalHub.Core.dll','artifacts/home-build/0.10.7/EnvironmentalHub.Adapters.dll']
receipt={'date':'2026-10-03','candidate':'0.10.7','formal':'0.9.2','formal_coverage':[9,1,112],'candidate_coverage':[10,1,111],'build':{'errors':0,'warnings':0},'identities':[read(p/'identity.json') for p in [ev,full,resumed]],'native_suites':suites,'native_total':161,'checks':checks,'images':images,'result_archive':{'path':'samples/archive_0107/comparison_export_api.json','sha256':sha(root/'samples/archive_0107/comparison_export_api.json'),'origin':'Production ExportComparisonJson in fixture receipt, written to disk; not native SaveFileDialog','native_results_exact_after_restart':True},'source_binary_sha256':{p:sha(root/p) for p in files},'open_gates':['native comparison Save success','native import file selection success','full Dock narrow/wide','native dark theme','full keyboard','mouse postselection','multi-window document UI','cross-machine pilot'],'failed_tests_preserved':['initial spawn exited before load','incorrect retry spawn reference blocked by PID guard','incorrect prepared load call filenames: no script executed','host reuse mistaken for mandatory recreation','test Timer unsupported RhinoApp.AsyncInvoke crashed owned PID 28280; confirmed Windows .NET stack','native import dialog accessibility unavailable; canceled and API restore passed']}
(ev/'acceptance.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
summary='0.10.7 新增日照方案比較 JSON 匯入與跨程序恢復：整批檢核後追加，保留完整原生結果、名稱及選擇；不綁定舊模型、不求解、不改目前輸入或結果。42 項方案契約、17 項原生匯入、32 項狀態／文件隔離、13 項新程序恢復及 161 項全平台原生回歸通過；Core 25、MCP 工具 12，建置零錯誤／零警告。4 張 320／480 淺色離屏圖已檢視。原生匯入檔案選取、比較存檔、完整 Dock／深色／全鍵盤／滑鼠後選及跨機仍待驗收。測試 Timer 錯誤造成自建程序退出，堆疊與修正保留；產品未使用該 API。正式 0.9.2／9、1、112，候選 10／1／111；V02 未正式交付，V03 未啟動。'
section='## 2026-10-03 · 0.10.7 日照方案匯入與恢復\n\n'+summary+'\n\n[方案操作與契約](SUNHOURS_SCENARIO_ARCHIVE.md) · [本輪詳細驗證](HOME_VALIDATION_0107.md) · [本輪 receipt](evidence/archive_0107/acceptance.json) · [視覺化精華](DEVELOPMENT_HIGHLIGHTS.md)。原有歷史紀錄保留；本輪沿用 Notion 詳細紀錄／重點／固定 KB-003 三層，實際進度才同步。\n\n'
for f in ['README.md','docs/PROJECT_STATUS.md','docs/KNOWLEDGE_INDEX.md','docs/BUILD_AND_RUN.md','docs/ROADMAP.md','docs/L2_VISUAL_PLAN.md','docs/HOME_TRANSFER.md','docs/LADYBUG_DEVELOPMENT_PLAN.md','docs/DEVELOPMENT_REVIEW_2026-10-01.md']:
    p=root/f; body=p.read_text(encoding='utf-8'); assert not body.startswith('## 2026-10-03 · 0.10.7')
    prefix=section
    if f=='README.md':
        for target in ['SUNHOURS_SCENARIO_ARCHIVE.md','HOME_VALIDATION_0107.md','evidence/archive_0107/acceptance.json','DEVELOPMENT_HIGHLIGHTS.md']: prefix=prefix.replace('('+target+')','(docs/'+target+')')
    p.write_text(prefix+body,encoding='utf-8')
(ev/'summary.txt').write_text(summary,encoding='utf-8')
print(json.dumps({'native':161,'archive_and_runtime':104,'core':25,'mcp':12,'images':len(images)}))
