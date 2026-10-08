test = sc.sticky.pop('ESH_WEBVIEW_0108', None)
if test:
    test['host'].Close()
    test['summary'].Dispose()
    test['panel'].Dispose()
    if 'capture_stream' in test: test['capture_stream'].Dispose()
assert doc.Objects.Count == 0
json.dump({'pid': System.Diagnostics.Process.GetCurrentProcess().Id, 'object_count': doc.Objects.Count, 'test_controls_disposed': True}, open(os.path.join(evidence, 'cleanup.json'), 'w'), indent=2)
print('Owned test controls disposed; blank document unchanged')
