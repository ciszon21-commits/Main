assert os.path.exists(fixture_path)
workspace.ShowModule(module_type)
doc.Objects.UnselectAll()
assert doc.Objects.Select(System.Guid(fixture['geometry']))
before = panel.CompletedResultJson
select = next(c for c in panel.Controls if False) if False else None
def walk(c):
    yield c
    if isinstance(c,forms.Container):
        for child in c.Controls:
            for item in walk(child):
                yield item
button = next(c for c in walk(panel) if isinstance(c,forms.Button) and c.Text=='選取分析面／模型…')
button.PerformClick()
selected = panel.GetType().GetField('selected',flags).GetValue(panel)
assert [str(x) for x in selected] == [fixture['geometry']]
assert panel.CompletedResultJson == before and panel.ScenarioCount == 2
doc.Objects.UnselectAll()
json.dump({'passed':2,'cases':['production_picker_accepts_native_preselection','completed_result_and_two_scenarios_preserved_after_selection'],
           'pid':identity['pid'],'scope':'Production button -> Rhino GetObject; existing native preselection, mouse postselection still pending'},
          open(os.path.join(evidence,'picker_checks.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
read_state()
