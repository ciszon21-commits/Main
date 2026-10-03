assert os.path.exists(fixture_path)
workspace.ShowModule(module_type)
panel.ShowStage(5)
button = panel.GetType().GetField('export',flags).GetValue(panel)
assert button.Enabled and panel.CompletedResultJson is not None
forms.Application.Instance.AsyncInvoke(lambda: button.PerformClick())
print(json.dumps({'scheduled':'production_result_export','pid':identity['pid']}))
