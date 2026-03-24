import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CoDevStudio.settings")
django.setup()

from django.test import Client

c = Client()
payload = {
    'project_code': '0660B',
    'bridge_name': '竹北一號橋(北上線)',
    'bridge_id': 'P01N',
    'd1_manual': 0.5
}
try:
    r = c.post('/bgf-excavation/api/excavation/', payload, content_type='application/json')
    print('STATUS POST:', r.status_code)
    if r.status_code >= 400:
        print('ERROR_CONTENT:', r.content.decode('utf-8'))
    else:
        print('POST SUCCESS')
except Exception as e:
    import traceback
    traceback.print_exc()
