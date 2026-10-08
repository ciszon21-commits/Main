test = sc.sticky['ESH_WEBVIEW_0108']; browser = test['browser']
print(str(test['dom_task'].Result))
test['navigation_events'] = []
def loading(sender, e):
    test['navigation_events'].append({'uri': str(e.Uri), 'absolute': str(e.Uri.AbsoluteUri), 'cancel': bool(e.Cancel)})
    json.dump(test['navigation_events'], open(os.path.join(evidence, 'navigation.json'), 'w', encoding='utf-8'), indent=2)
test['loading_logger'] = loading
browser.DocumentLoading += loading
browser.LoadHtml(open(os.path.join(evidence, 'summary-light.html'), encoding='utf-8').read(), None)
print('reload queued')
