assert panel.ScenarioCount==6
assert not os.path.exists(os.path.join(outputs,'comparison_from_native_dialog.json'))
button=panel.GetType().GetField('exportCompare',flags).GetValue(panel)
assert button.Enabled
forms.Application.Instance.AsyncInvoke(System.Action(lambda:button.PerformClick()))
print('Scheduled production comparison SaveFileDialog')
