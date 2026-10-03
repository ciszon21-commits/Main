assert os.path.exists(fixture_path)
workspace.ShowModule(module_type)
panel.ShowStage(5)
button = panel.GetType().GetField('exportCompare',flags).GetValue(panel)
assert button.Enabled and panel.ScenarioCount==2
forms.Application.Instance.AsyncInvoke(lambda: button.PerformClick())
print(json.dumps({'scheduled':'production_comparison_export','pid':identity['pid']}))
