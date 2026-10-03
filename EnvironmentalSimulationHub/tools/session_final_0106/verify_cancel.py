from pathlib import Path
check = {'pid':identity['pid'],'result_preserved':json.loads(panel.ExportResultJson())==json.loads(fixture['result_json']),
         'comparison_preserved':json.loads(panel.ExportComparisonJson())==json.loads(fixture['comparison_json']),
         'no_export_files_created':not any(Path(outputs).glob('*native_dialog.json')),
         'scope':'Production result export button opens native SaveFileDialog; cancel observed through accessibility; successful saving unverified'}
assert check['result_preserved'] and check['comparison_preserved'] and check['no_export_files_created']
check['passed']=3
json.dump(check,open(os.path.join(evidence,'production_export_cancel.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(json.dumps(check,ensure_ascii=False))
