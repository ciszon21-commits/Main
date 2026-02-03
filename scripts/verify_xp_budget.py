import os
import django
import sys
import json
from django.test import RequestFactory
from django.db.models import Sum

# Setup Django
sys.path.append('D:\\10.vibecoding\\CoDevStudio-07729')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CoDevStudio.settings")
django.setup()

from EngineerRPG.models import SkillNode, CharacterClass, User
from EngineerRPG.views import api_save_skill_node, api_auto_distribute_xp

def test_xp_budget_features():
    print("Testing XP Budget Features...")
    
    # Setup Admin User
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser('admin_test', 'admin@test.com', 'password')
        # Ensure profile exists and role is ADMIN
        profile = admin_user.rpg_profile
        profile.role = 'ADMIN'
        profile.save()
    else:
        profile = admin_user.rpg_profile
        if profile.role != 'ADMIN':
            profile.role = 'ADMIN'
            profile.save()

    factory = RequestFactory()
    
    # 1. Test Strict Limit (ROOT > 4500)
    print("\n[TEST 1] Testing ROOT XP Limit (> 4500)...")
    
    # Calculate current ROOT XP
    current_root = SkillNode.objects.filter(node_type='ROOT').aggregate(Sum('exp_reward'))['exp_reward__sum'] or 0
    remaining = 4500 - current_root
    
    # Attempt to add a node exceeding remaining
    excess_xp = remaining + 100
    
    data = {
        'name': 'Over Limit Skill',
        'type': 'ROOT',
        'exp_reward': excess_xp,
        'description': 'Test'
    }
    
    request = factory.post(
        '/rpg/api/skill-editor/node/save/', 
        data=json.dumps(data), 
        content_type='application/json'
    )
    request.user = admin_user
    
    response = api_save_skill_node(request)
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 400:
        print("   PASS: Blocked excess ROOT XP.")
    else:
        print(f"   FAIL: {response.content}")

    # 2. Test Auto Distribute
    print("\n[TEST 2] Testing Auto Distribute (ROOT)...")
    
    # Create a small gap if none exists (delete a temp skill if needed, or reduce one)
    # Let's find a ROOT skill and reduce its XP by 100 temporarily
    root_skill = SkillNode.objects.filter(node_type='ROOT').first()
    if root_skill:
        original_xp = root_skill.exp_reward
        root_skill.exp_reward = max(0, original_xp - 100)
        root_skill.save()
        
        # Call Auto Distribute
        dist_data = {'type': 'ROOT'}
        request_dist = factory.post(
            '/rpg/api/skill-editor/auto-distribute/',
            data=json.dumps(dist_data),
            content_type='application/json'
        )
        request_dist.user = admin_user
        
        response_dist = api_auto_distribute_xp(request_dist)
        print(f"   Distribute Status: {response_dist.status_code}")
        
        # Verify Total is 4500
        new_total = SkillNode.objects.filter(node_type='ROOT').aggregate(Sum('exp_reward'))['exp_reward__sum'] or 0
        if new_total == 4500:
            print("   PASS: Auto distributed to exactly 4500.")
        else:
             print(f"   FAIL: Total is {new_total}")
             
    else:
        print("   SKIP: No ROOT skills found.")

if __name__ == "__main__":
    try:
        test_xp_budget_features()
    except Exception as e:
        print(f"Error: {e}")
