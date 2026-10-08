cases=[]
def check(condition,name):
    assert condition,name
    cases.append(name)
path=os.path.join(root,'samples/archive_0107/comparison_export_api.json')
saved=json.load(open(path,encoding='utf-8'))
native_import=panel.ScenarioCount==6
if not native_import:
    check(panel.ScenarioCount==0,'fresh_empty_scenarios')
    check(panel.ImportScenariosJson(open(path,encoding='utf-8').read())==6,'api_import_from_disk')
restored=json.loads(panel.ExportComparisonJson())
check(len(restored['Scenarios'])==6,'six_scenarios_restored_in_new_process')
check([s['Result'] for s in restored['Scenarios']]==[s['Result'] for s in saved['Scenarios']],'every_full_native_result_exact_after_restart')
check([s['Name'] for s in restored['Scenarios']]==[s['Name'] for s in saved['Scenarios']],'all_chinese_names_exact')
check(restored['BaselineIndex']==4 and restored['CandidateIndex']==5,'saved_comparison_selection_restored')
check(all(s['Imported'] for s in restored['Scenarios']),'all_restored_results_marked_historical')
check('13.000' in panel.ComparisonText and '9.574' in panel.ComparisonText and 'Δ' in panel.ComparisonText,'real_case_comparison_recomputed')
check('歷史' in panel.ComparisonText and panel.CompletedResultJson is None,'imported_comparison_not_current_completed_result')
check(not list(doc.Objects) and not doc.Modified,'no_old_geometry_or_preview_imported')
export_before=panel.ExportComparisonJson()
json.dump(restored,open(os.path.join(root,'samples/archive_0107/comparison_after_restart.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
check(json.load(open(os.path.join(root,'samples/archive_0107/comparison_after_restart.json'),encoding='utf-8'))==restored,'reexport_readback_exact')
Rhino.UI.Panels.ClosePanel(guid,doc); check(Rhino.RhinoApp.RunScript('_EnvironmentalSunHours',False),'close_reopen_registered_panel')
workspace=Rhino.UI.Panels.GetPanel(guid,doc); panel=workspace.GetModule(module_type)
check(export_before==panel.ExportComparisonJson(),'restored_scenarios_survive_close_reopen')
report={'version':'0.10.7','passed':len(cases),'cases':cases,'pid':identity['pid'],'previous_pid':28280,'native_import_succeeded':native_import,'source_sha256':__import__('hashlib').sha256(open(path,'rb').read()).hexdigest(),'state':read_state()}
json.dump(report,open(os.path.join(evidence,'restore_checks.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(json.dumps({'restart_restore_checks':len(cases),'native_import':native_import}))
