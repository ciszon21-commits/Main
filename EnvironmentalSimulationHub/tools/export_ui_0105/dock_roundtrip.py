assert os.path.exists(fixture_path)
workspace.ShowModule(module_type)
before = {'workspace_hash':workspace.GetHashCode(),'result':panel.CompletedResultJson,'scenarios':panel.ScenarioCount}
target = next(g for g in Rhino.UI.Panels.GetOpenPanelIds() if g != guid and len(Rhino.UI.Panels.PanelDockBars(g))>0)
dock = Rhino.UI.Panels.PanelDockBar(target)
Rhino.UI.Panels.ClosePanel(guid,doc)
returned = Rhino.UI.Panels.OpenPanel(dock,guid,True)
assert returned != System.Guid.Empty
Rhino.RhinoApp.Wait()
all_panels = Rhino.UI.Panels.GetPanels(guid,doc)
report={'before_workspace_hash':before['workspace_hash'],'instances':[{'hash':w.GetHashCode(),'module':w.ActiveModule.Name,
        'parent':w.ParentWindow.GetType().FullName if w.ParentWindow else None,
        'visible':w.Visible,'size':str(w.Size),
        'result_present':w.GetModule(module_type).CompletedResultJson is not None,
        'scenario_count':w.GetModule(module_type).ScenarioCount} for w in all_panels],
        'returned_dockbar':str(returned),'native_float_result':Rhino.UI.Panels.FloatPanel(guid,Rhino.UI.Panels.FloatPanelMode.Show)}
Rhino.RhinoApp.Wait()
workspace = Rhino.UI.Panels.GetPanel(guid,doc)
panel = workspace.GetModule(module_type)
report['after']=read_state()
report['result_preserved']=panel.CompletedResultJson==before['result']
report['scenarios_preserved']=panel.ScenarioCount==before['scenarios']
json.dump(report,open(os.path.join(evidence,'dock_roundtrip.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
