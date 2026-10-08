button=panel.GetType().GetField('importScenarios',flags).GetValue(panel)
assert button.Enabled
forms.Application.Instance.AsyncInvoke(System.Action(lambda:button.PerformClick()))
print('Scheduled production archive OpenFileDialog')
