before = {'size':workspace.ParentWindow.Size,'location':workspace.ParentWindow.Location}
checks = []
methods = []
try:
    other = [g for g in Rhino.UI.Panels.GetOpenPanelIds() if g != guid and len(Rhino.UI.Panels.PanelDockBars(g)) > 0]
    assert other
    sibling = other[0]
    target = Rhino.UI.Panels.PanelDockBar(sibling)
    assert target != System.Guid.Empty
    Rhino.UI.Panels.ClosePanel(guid, doc)
    opened = Rhino.UI.Panels.OpenPanelAsSibling(guid, sibling, True)
    Rhino.RhinoApp.Wait()
    methods.append({'method':'OpenPanelAsSibling','returned':opened,'target':str(target)})
    if not opened:
        returned = Rhino.UI.Panels.OpenPanel(target, guid, True)
        Rhino.RhinoApp.Wait()
        methods.append({'method':'OpenPanel(dockbar, panel, true)','returned':str(returned)})
    workspace = Rhino.UI.Panels.GetPanel(guid, doc)
    assert workspace is not None
    state = read_state()
    actual = Rhino.UI.Panels.PanelDockBar(guid)
    assert actual == target, 'Panel did not enter requested existing dock container'
    checks.append('native_existing_dock_container_confirmed')
    initialized = workspace.GetType().GetField('initialFloatingWidthApplied',flags)
    apply = workspace.GetType().GetMethod('EnsureInitialFloatingWidth',flags)
    window = workspace.ParentWindow
    size = window.Size
    initialized.SetValue(workspace,False)
    apply.Invoke(workspace,None)
    Rhino.RhinoApp.Wait()
    assert window.Size == size
    assert not initialized.GetValue(workspace)
    checks.append('initial_floating_width_does_not_resize_native_docked_or_shared_container')
    assert doc.Objects.Count == 0 and not doc.Modified
    checks.append('empty_document_and_units_unchanged')
finally:
    Rhino.UI.Panels.FloatPanel(guid,Rhino.UI.Panels.FloatPanelMode.Show)
    Rhino.RhinoApp.Wait()
    workspace = Rhino.UI.Panels.GetPanel(guid,doc)
    if isinstance(workspace.ParentWindow, forms.Form) and workspace.ParentWindow.NativeHandle != Rhino.RhinoApp.MainWindowHandle():
        workspace.ParentWindow.Size = before['size']
        workspace.ParentWindow.Location = before['location']
    workspace.GetType().GetField('initialFloatingWidthApplied',flags).SetValue(workspace,True)
    report={'pid':identity['pid'],'passed':len(checks),'checks':checks,'methods':methods,
            'visual_qa':'NOT_ACCEPTED: desktop capture unavailable','after':read_state()}
    with open(os.path.join(root,'docs/evidence/native_ui_0105/dock_guard.json'),'w',encoding='utf-8') as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
