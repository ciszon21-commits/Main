import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CoDevStudio.settings")
django.setup()

from django.test import RequestFactory
from EngineerRPG.views import api_auto_layout_skill_tree
from django.contrib.auth.models import User

def run_test():
    user = User.objects.first()
        
    rf = RequestFactory()
    request = rf.post('/rpg/api/skill-tree/auto-layout/', 
                     data=json.dumps({"class_code": "CIVIL"}), 
                     content_type='application/json')
    request.user = user
    request.session = {}

    print("Testing unwrapped function...")
    try:
        # access the innermost function
        unwrapped = api_auto_layout_skill_tree
        while hasattr(unwrapped, '__wrapped__'):
            unwrapped = unwrapped.__wrapped__
            
        res = unwrapped(request)
        print("Inner function returned:", type(res))
        if res:
            print("STATUS:", res.status_code)
    except Exception as e:
        print("Inner function exception:", e)

if __name__ == '__main__':
    run_test()
