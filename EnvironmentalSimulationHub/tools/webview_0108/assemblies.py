record = [{'name': str(a.GetName().Name), 'version': str(a.GetName().Version), 'path': str(a.Location)} for a in System.AppDomain.CurrentDomain.GetAssemblies() if str(a.GetName().Name).startswith('EnvironmentalHub')]
json.dump(record, open(os.path.join(evidence, 'assemblies.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps(record, ensure_ascii=False))
