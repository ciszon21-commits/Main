cases=[]
def check(condition,name):
    assert condition,name
    cases.append(name)
legacy=open(os.path.join(root,'samples/archive_0107/legacy_comparison.json'),encoding='utf-8').read()
check(panel.CompletedResultJson is None and panel.ScenarioCount==0,'fresh_registered_module')
before_models=[str(o.Id) for o in doc.Objects]
check(panel.ImportScenariosJson(legacy)==2,'legacy_0106_comparison_imported')
loaded=json.loads(panel.ExportComparisonJson()); original=json.loads(legacy)
check([s['Result'] for s in loaded['Scenarios']]==[s['Result'] for s in original['Scenarios']],'full_native_results_preserved')
check(loaded['BaselineIndex']==0 and loaded['CandidateIndex']==1,'selection_restored')
check(all(s['Imported'] for s in loaded['Scenarios']) and '歷史' in panel.ComparisonText,'historical_origin_disclosed')
check('Δ' in panel.ComparisonText and '9.574' in panel.ComparisonText,'compatible_actual_conditions_allow_difference')
check(panel.CompletedResultJson is None and before_models==[str(o.Id) for o in doc.Objects],'import_does_not_run_solver_or_create_preview')
check(not panel.GetType().GetField('run',flags).GetValue(panel).Enabled,'historical_geometry_not_bound_to_active_document')
before=panel.ExportComparisonJson()
for name,text in [('same_names',legacy),('malformed','{'),('late_invalid_result',None)]:
    if text is None:
        value=json.loads(legacy); value['Scenarios'][0]['Name']='合法新名稱'; value['Scenarios'][1]['Name']='另一新名稱'; value['Scenarios'][1]['Result']['Statistics']['Mean']=999
        text=json.dumps(value)
    try:
        panel.ImportScenariosJson(text)
        raise AssertionError('Invalid import accepted')
    except System.ArgumentException: pass
    check(before==panel.ExportComparisonJson() and panel.ScenarioCount==2,name+'_leaves_all_existing_scenarios_unchanged')
# Changing physical source while retaining metadata must suppress deltas.
changed=json.loads(legacy)
for s in changed['Scenarios']: s['Name']='北向改動 '+s['Name']
changed['Scenarios'][1]['Result']['InputParameters']['SunSource']['NorthDegrees']=90
check(panel.ImportScenariosJson(json.dumps(changed))==2,'append_archive')
check('無法直接比較' in panel.ComparisonText and 'Δ' not in panel.ComparisonText,'actual_source_change_suppresses_delta_despite_matching_metadata')
appended=json.loads(panel.ExportComparisonJson())
check(appended['BaselineIndex']==2 and appended['CandidateIndex']==3,'append_selection_offset_correct')
panel.CompareScenarios(0,1)
for cmd in ['_EnvironmentalHub','_EnvironmentalSunHours']: check(Rhino.RhinoApp.RunScript(cmd,False),'navigate_'+cmd)
check(panel.ScenarioCount==4 and before_models==[str(o.Id) for o in doc.Objects],'navigation_keeps_imported_data_and_model')
report={'version':'0.10.7','passed':len(cases),'cases':cases,'pid':identity['pid'],'state':read_state()}
json.dump(report,open(os.path.join(evidence,'archive_checks.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(json.dumps({'archive_native_checks':len(cases)}))
