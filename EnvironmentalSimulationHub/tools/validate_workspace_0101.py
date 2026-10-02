"""Native state-preservation and single-dock acceptance, owned 0.10.1 Rhino slot only."""
import Rhino, System, clr, os, json
clr.AddReference('Eto')
from Eto.Forms import Button, DropDown, TextBox, NumericStepper, CheckBox
root = 'C:/Users/08432.SINOLTD/00.DEVE/31.AEC/RHINO_Deve/EnvironmentalSimulationHub'
workspace_id = System.Guid('7281a8f2-e2c4-4c27-bcb5-22cbb0688b32')
commands = ['EnvironmentalHub', 'EnvironmentalWeather', 'EnvironmentalLocation', 'EnvironmentalClimate', 'EnvironmentalTime', 'EnvironmentalRadiation', 'EnvironmentalSunPath', 'EnvironmentalSunHours']
names = ['HubOverviewPanel', 'WeatherPanel', 'LocationPanel', 'ClimateFilePanel', 'TimePanel', 'RadiationPanel', 'SunPathPanel', 'SunHoursPanel']
legacy_ids = ['1c0c5ac3-b820-42f2-9aaa-1e0f50356d1a', '5f78d8d4-e9a1-4713-bb04-d08466339735', '499a99e8-8e73-4a6b-8208-fc879e413d36', '06843693-df8a-421c-938b-96e2b9e88066', 'c62382ce-7709-4fcd-9dfb-447d1d8a08c0']
Rhino.RhinoApp.RunScript('EnvironmentalHub', False)
workspace = Rhino.UI.Panels.GetPanel(workspace_id)
assert str(workspace.GetType().Name) == 'HubWorkspacePanel'
assert str(workspace.GetType().Assembly.GetName().Version) == '0.10.1.0'
types = [workspace.GetType().Assembly.GetType('EnvironmentalHub.Plugin.' + name) for name in names]
views = [workspace.GetModule(t) for t in types]
def walk(control):
    yield control
    if hasattr(control, 'Controls'):
        for child in control.Controls:
            for descendant in walk(child): yield descendant
def snapshot(view):
    fields = ['CompletedResultJson', 'CompletedSelectionJson', 'SummaryText', 'ComparisonText', 'AssessmentText']
    result = {name: str(getattr(view, name)) for name in fields if hasattr(view, name)}
    result['input_controls'] = [(str(c.GetType().Name), str(c.Text) if isinstance(c, TextBox)
        else str(c.Value) if isinstance(c, NumericStepper) else str(c.Checked) if isinstance(c, CheckBox)
        else str(c.SelectedIndex)) for c in walk(view) if isinstance(c, (TextBox, NumericStepper, CheckBox, DropDown))]
    return result
name_control = views[2].GetType().GetField('name', System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic).GetValue(views[2])
original_name = name_control.Text
name_control.Text = '未完成的方案草稿 · 單一平台切換測試'
before = [snapshot(view) for view in views]
assert before[1].get('CompletedResultJson') not in ('', 'None'), 'Run the numerical acceptance first'
assert before[5].get('CompletedResultJson') not in ('', 'None'), 'Run platform acceptance first'
cases = []
for command, t, view in zip(commands, types, views):
    Rhino.RhinoApp.RunScript(command, False)
    assert System.Object.ReferenceEquals(workspace, Rhino.UI.Panels.GetPanel(workspace_id))
    assert workspace.ActiveModule == t
    assert System.Object.ReferenceEquals(view, workspace.GetModule(t))
    assert Rhino.UI.Panels.IsPanelVisible(workspace_id)
    cases.append('command_routes_to_same_workspace:' + command)
for guid in legacy_ids:
    assert Rhino.UI.Panels.GetPanel(System.Guid(guid)) is None
    assert not Rhino.UI.Panels.IsPanelVisible(System.Guid(guid))
cases.append('no_independent_legacy_module_panels')
selector = next(c for c in walk(workspace) if isinstance(c, DropDown) and c.Items.Count == 8)
for i, t in enumerate(types):
    selector.SelectedIndex = i
    assert workspace.ActiveModule == t
    assert System.Object.ReferenceEquals(views[i], workspace.GetModule(t))
cases.append('eight_immediate_internal_navigation_routes')
workspace.ShowModule(types[0])
buttons = [c for c in walk(views[0]) if isinstance(c, Button) and (c.Text.startswith('開啟 ') or c.Text in ['開始日射分析','開啟太陽路徑','開啟日照時數'])]
assert len(buttons) == 7
for button, index in zip(buttons, [5, 6, 7, 1, 2, 3, 4]):
    workspace.ShowModule(types[0]); button.PerformClick()
    assert workspace.ActiveModule == types[index]
cases.append('seven_overview_actions_remain_inside_workspace')
assert [snapshot(view) for view in views] == before
cases.append('draft_inputs_completed_results_and_comparisons_preserved_after_navigation')
assert workspace.CachedModuleCount == 8
cases.append('exactly_eight_cached_views_without_recreation')
previous = workspace.ActiveModule
try:
    workspace.ShowModule(System.String)
    raise AssertionError('Unknown module accepted')
except System.ArgumentException: pass
assert workspace.ActiveModule == previous
cases.append('unknown_module_preserves_current_view')
Rhino.UI.Panels.ClosePanel(workspace_id)
Rhino.RhinoApp.RunScript('EnvironmentalWeather', False)
assert System.Object.ReferenceEquals(workspace, Rhino.UI.Panels.GetPanel(workspace_id))
assert [snapshot(view) for view in views] == before
cases.append('dock_close_reopen_preserves_cached_results')
Rhino.RhinoApp.RunScript('EnvironmentalHub', False)
name_control.Text = original_name
report = {'version': '0.10.1', 'registered_panel': 'HubWorkspacePanel', 'cached_views': 8,
          'passed': len(cases), 'cases': cases, 'preserves_input_result_and_scenario_views': True,
          'scope': 'Actual registered Rhino workspace, eight commands, immediate navigation, overview actions, close/reopen and completed result/comparison preservation; same Windows Rhino session.'}
json.dump(report, open(os.path.join(root, 'docs/evidence/workspace_0101_runtime.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps({'passed': len(cases), 'one_workspace': True}))
