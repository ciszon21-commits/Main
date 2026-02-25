import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from EngineerRPG.views import api_auto_layout_skill_tree

from django.test import RequestFactory
from EngineerRPG.models import UserProfile, CharacterClass
from django.contrib.auth.models import User

# get a manager/admin user
user = User.objects.filter(userprofile__role='MANAGER').first()
if not user:
    user = User.objects.first()

rf = RequestFactory()
request = rf.post('/rpg/api/skill-tree/auto-layout/', 
                 data=json.dumps({"class_code": "CIVIL"}), 
                 content_type='application/json')
request.user = user

try:
    response = api_auto_layout_skill_tree(request)
    print(f"STATUS CODE: {response.status_code}")
    print(f"RESPONSE CONTENT: {response.content.decode()}")
except Exception as e:
    import traceback
    traceback.print_exc()
