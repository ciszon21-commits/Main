import os
import django
import sys

# Add project root to path
sys.path.append('D:\\10.vibecoding\\CoDevStudio-07729')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CoDevStudio.settings")
django.setup()

from django.contrib.auth.models import User
from EngineerRPG.models import UserProfile, SkillNode, UserSkill, CharacterClass, PromotionRequest
from EngineerRPG.views import apply_promotion, approve_request
from EngineerRPG.utils.level_system import calculate_level_from_xp
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.urls import reverse

def setup_test_env():
    # Cleanup potential conflicts first
    UserProfile.objects.filter(employee_id__in=["TEST001", "MGR001"]).delete()
    User.objects.filter(username__in=["TestIntern_V1", "ManagerUser"]).delete()

    # Create User
    username = "TestIntern_V1"
    
    # Check if civl class exists, otherwise create it or pick first
    try:
         civil = CharacterClass.objects.get(code='CIVIL')
    except CharacterClass.DoesNotExist:
         # Create dummy class if needed or pick first
         if CharacterClass.objects.exists():
             civil = CharacterClass.objects.first()
         else:
             civil = CharacterClass.objects.create(name="Civil", code="CIVIL")
             
    user = User.objects.create_user(username=username, password="password")
    profile = UserProfile.objects.create(
        user=user, 
        employee_id="TEST001", 
        character_class=civil,
        rank='INTERN'
    )
    print(f"Created user {username}")
        
    return user, profile

def test_promotion_logic():
    user, profile = setup_test_env()
    
    # 1. Test Level Cap at 10 (Intern)
    print("\n[TEST 1] Testing Intern Level Cap...")
    profile.experience = 5000 # Enough for Lv 50
    profile.update_stats() # Just to be sure?? No, update_stats does HP/MP.
    # We need to simulate the XP gain logic check.
    # Since we can't easily call the while loop in view without request, 
    # we will use the logic we implemented:
    # IF INTERN and Lv >= 10, STOP.
    
    # Let's say we set level to 10 manually, and verify apply_promotion fails
    profile.level = 10
    profile.save()
    
    factory = RequestFactory()
    
    # Try to apply promotion without skills
    print(">> Applying promotion without skills (Should Fail)...")
    request = factory.get(reverse('engineer_rpg:apply_promotion'))
    request.user = user
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    apply_promotion(request)
    # Check messages
    storage = messages
    for message in storage:
        print(f"   Message: {message}")
        if '申請失敗' in str(message):
            print("   PASS: Correctly rejected.")
            
    # 2. Grant ROOT Skills
    print("\n[TEST 2] Granting ROOT Skills and Promoting...")
    root_skills = SkillNode.objects.filter(node_type='ROOT')
    for skill in root_skills:
        UserSkill.objects.create(user_profile=profile, skill_node=skill, status='COMPLETED')
        
    # Apply again
    print(">> Applying promotion with ROOT skills (Should Pending)...")
    apply_promotion(request)
    
    req = PromotionRequest.objects.filter(applicant=profile, status='PENDING').first()
    if req:
        print(f"   PASS: Promotion Request created. Target Level: {req.target_level}")
    else:
        print("   FAIL: No request created.")
        return

    # Approve
    print(">> Approving Request (Should jump levels)...")
    # Simulate Manager
    manager = User.objects.create_user(username="ManagerUser", password="password")
    UserProfile.objects.create(user=manager, employee_id="MGR001", character_class=profile.character_class, role='MANAGER')
    
    request_approve = factory.get(reverse('engineer_rpg:approve_request', args=[req.id]))
    request_approve.user = manager
    setattr(request_approve, 'session', 'session')
    messages_approve = FallbackStorage(request_approve)
    setattr(request_approve, '_messages', messages_approve)
    
    approve_request(request_approve, req.id)
    
    profile.refresh_from_db()
    print(f"   Current Rank: {profile.rank}")
    print(f"   Current Level: {profile.level}")
    
    if profile.rank == 'ASSISTANT':
        print("   PASS: Rank updated to ASSISTANT.")
    else:
        print(f"   FAIL: Rank is {profile.rank}")
        
    if profile.level > 10:
        print(f"   PASS: Level jumped to {profile.level} (Over 10).")
    else:
         print(f"   FAIL: Level stuck at {profile.level}")

    # 3. Test Assistant -> Engineer
    print("\n[TEST 3] Testing Assistant -> Engineer...")
    # Grant 60% CORE skills
    core_skills = SkillNode.objects.filter(character_class=profile.character_class, node_type='CORE')
    target_count = int(core_skills.count() * 0.6) + 1
    print(f"   Granting {target_count} / {core_skills.count()} CORE skills...")
    
    for i, skill in enumerate(core_skills):
        if i < target_count:
             UserSkill.objects.create(user_profile=profile, skill_node=skill, status='COMPLETED')
             
    # Apply
    print(">> Applying promotion (Should Pending)...")
    apply_promotion(request)
    
    req2 = PromotionRequest.objects.filter(applicant=profile, status='PENDING').first()
    if req2:
         print(f"   PASS: Request created.")
    else:
         print("   FAIL: Request not created.")
         return
         
    # Approve
    approve_request(request_approve, req2.id)
    profile.refresh_from_db()
    
    if profile.rank == 'ENGINEER':
        print("   PASS: Rank updated to ENGINEER.")
    else:
        print(f"   FAIL: Rank is {profile.rank}")

if __name__ == "__main__":
    try:
        test_promotion_logic()
    except Exception as e:
        print(f"Error: {e}")
