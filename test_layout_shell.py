import json
from django.test import RequestFactory
from EngineerRPG.models import UserProfile, CharacterClass
from django.contrib.auth.models import User
from EngineerRPG.views import api_auto_layout_skill_tree

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
