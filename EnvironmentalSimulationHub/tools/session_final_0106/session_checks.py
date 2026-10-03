from Eto.Forms import TextBox, NumericStepper, CheckBox, DropDown
cases = []
def check(condition,name):
    assert condition,name
    cases.append(name)
def walk(c):
    yield c
    if hasattr(c,'Controls'):
        for child in c.Controls:
            for descendant in walk(child): yield descendant
def snapshot(view):
    data = {name:str(getattr(view,name)) for name in ['CompletedResultJson','CompletedSelectionJson','SummaryText','ComparisonText','AssessmentText'] if hasattr(view,name)}
    data['inputs']=[(str(c.GetType().Name),str(c.Text) if isinstance(c,TextBox) else str(c.Value) if isinstance(c,NumericStepper) else str(c.Checked) if isinstance(c,CheckBox) else str(c.SelectedIndex)) for c in walk(view) if isinstance(c,(TextBox,NumericStepper,CheckBox,DropDown))]
    return data
types=[m.Item2 for m in workspace.GetType().Assembly.GetType('EnvironmentalHub.Plugin.HubUi').GetField('Modules',BindingFlags.Static|BindingFlags.NonPublic).GetValue(None)]
views=[workspace.GetModule(t) for t in types]
# Temporary focus visibility is intentionally released on navigation.
panel.ReleaseFocusVisibility()
name=views[2].GetType().GetField('name',flags).GetValue(views[2]); original_name=name.Text
name.Text='尚未完成的中文草稿 · 0.10.6'
before=[snapshot(v) for v in views]
result_before=panel.ExportResultJson(); compare_before=panel.ExportComparisonJson()
model_before={str(o.Id):str(o.Geometry.DataCRC(0)) for o in doc.Objects}
for i,command in enumerate(['EnvironmentalHub','EnvironmentalWeather','EnvironmentalLocation','EnvironmentalClimate','EnvironmentalTime','EnvironmentalRadiation','EnvironmentalSunPath','EnvironmentalSunHours']):
    check(Rhino.RhinoApp.RunScript(command,False),'command:'+command)
    workspace=Rhino.UI.Panels.GetPanel(guid,doc)
    check(System.Object.ReferenceEquals(views[i],workspace.GetModule(types[i])),'cached_view:'+command)
after_navigation=[snapshot(v) for v in views]
if before != after_navigation:
    json.dump({'before':before,'after':after_navigation},open(os.path.join(evidence,'navigation_difference.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
check(before == after_navigation,'all_draft_inputs_and_completed_results_survive_navigation')
workspace.ShowModule(module_type)
old_hash=workspace.GetHashCode()
dock=next(i for i in Rhino.UI.Panels.GetOpenPanelIds() if i != guid and len(Rhino.UI.Panels.PanelDockBars(i))>0)
Rhino.UI.Panels.ClosePanel(guid,doc)
check(Rhino.UI.Panels.OpenPanel(Rhino.UI.Panels.PanelDockBars(dock)[0],guid,True) != System.Guid.Empty,'native_open_in_other_dock_container')
Rhino.RhinoApp.Wait()
workspace=Rhino.UI.Panels.GetPanel(guid,doc)
check(workspace.GetHashCode()!=old_hash,'native_host_recreated_workspace_shell')
check(workspace.ActiveModule == module_type,'active_module_survives_shell_recreation')
check(all(System.Object.ReferenceEquals(v,workspace.GetModule(t)) for t,v in zip(types,views)),'all_eight_cached_views_reattached_to_new_shell')
panel=workspace.GetModule(module_type)
check(result_before==panel.ExportResultJson(),'full_result_contract_preserved_without_resolve')
check(compare_before==panel.ExportComparisonJson() and panel.ScenarioCount==2,'both_scenarios_and_comparison_preserved_without_resolve')
check(before == [snapshot(v) for v in views],'all_draft_inputs_preserved_after_native_dock_move')
check(model_before == {str(o.Id):str(o.Geometry.DataCRC(0)) for o in doc.Objects},'native_dock_move_leaves_model_and_owned_previews_unchanged')
Rhino.UI.Panels.ClosePanel(guid,doc)
check(Rhino.RhinoApp.RunScript('_EnvironmentalSunHours',False),'native_close_and_command_reopen')
workspace=Rhino.UI.Panels.GetPanel(guid,doc); panel=workspace.GetModule(module_type)
check(compare_before==panel.ExportComparisonJson(),'close_reopen_preserves_comparison')
# A normal offscreen shell must not bind to the user's document session.
isolated=System.Activator.CreateInstance(workspace.GetType()); isolated.ShowModule(module_type)
check(not System.Object.ReferenceEquals(panel,isolated.GetModule(module_type)) and isolated.GetModule(module_type).CompletedResultJson is None,'unregistered_capture_shell_uses_independent_cache')
isolated.Dispose()
check(result_before==panel.ExportResultJson(),'disposing_capture_shell_leaves_registered_results_alive')
sessions=workspace.GetType().GetField('sessions',BindingFlags.Static|BindingFlags.NonPublic).GetValue(None)
count_before=sessions.Count
other_doc=Rhino.RhinoDoc.CreateHeadless(None); other=System.Activator.CreateInstance(workspace.GetType())
try:
    other.PanelShown(other_doc.RuntimeSerialNumber,Rhino.UI.ShowPanelReason.Show)
    other_panel=other.GetModule(module_type)
    check(not System.Object.ReferenceEquals(panel,other_panel) and other_panel.CompletedResultJson is None,'second_headless_document_has_independent_empty_session')
    check(sessions.Count == count_before+1,'second_document_session_registered')
    other.PanelClosing(other_doc.RuntimeSerialNumber,True)
    check(sessions.Count == count_before,'document_close_callback_releases_only_that_session')
    check(compare_before==panel.ExportComparisonJson(),'closing_other_document_preserves_original_session')
finally:
    other.Dispose(); other_doc.Dispose()
name.Text=original_name
report={'version':'0.10.6','passed':len(cases),'cases':cases,'pid':identity['pid'],'old_shell_hash':old_hash,'new_shell_hash':workspace.GetHashCode(),'registered_instances':len(Rhino.UI.Panels.GetPanels(guid,doc)),'headless_scope':'Document isolation and closing callback; not a multi-window UI acceptance','state':read_state()}
json.dump(report,open(os.path.join(evidence,'session_checks.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(json.dumps({'session_checks':len(cases)}))
