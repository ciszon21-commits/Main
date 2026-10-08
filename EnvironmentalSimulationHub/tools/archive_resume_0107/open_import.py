assert panel.ScenarioCount==0 and panel.CompletedResultJson is None
button=panel.GetType().GetField('importScenarios',flags).GetValue(panel)
assert button.Enabled
forms.Application.Instance.AsyncInvoke(System.Action(lambda:button.PerformClick()))
print('Scheduled actual archive OpenFileDialog')
