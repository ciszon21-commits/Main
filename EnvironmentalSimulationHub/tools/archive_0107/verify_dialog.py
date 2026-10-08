path=os.path.join(outputs,'comparison_from_native_dialog.json')
saved=json.load(open(path,encoding='utf-8'))
check=json.loads(panel.ExportComparisonJson())
assert saved==check and panel.ScenarioCount==6
json.dump({'saved_exact_full_contract':True,'scenario_count':6,'pid':identity['pid'],'sha256':__import__('hashlib').sha256(open(path,'rb').read()).hexdigest()},open(os.path.join(evidence,'comparison_readback.json'),'w',encoding='utf-8'),indent=2)
print('Production comparison export exactly matches current full archive')
