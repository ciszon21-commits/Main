button = next(c for c in walk(panel) if isinstance(c,forms.Button) and c.Text == '選取分析面／模型…')
forms.Application.Instance.AsyncInvoke(lambda: button.PerformClick())
print(json.dumps({'scheduled':'native_geometry_picker','pid':identity['pid']}))
