test = sc.sticky['ESH_WEBVIEW_0108']; task = test.get('capture_task')
record = {'tag': test.get('capture_tag'), 'capture_error': test.get('capture_error'), 'task_status': str(task.Status) if task else None, 'exception': str(task.Exception) if task and task.IsFaulted else None, 'title': str(test['browser'].DocumentTitle)}
json.dump(record, open(os.path.join(evidence, 'capture_state.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps(record, ensure_ascii=False))
