import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CoDevStudio.settings")
django.setup()

from django.contrib.auth.models import User
from EngineerRPG.models import UserProfile

username = '黃瑞澤'
print(f"\n{'='*20} CHECKING USER: {username} {'='*20}")

try:
    user = User.objects.get(username=username)
    print(f"✅ User Account Exists")
    print(f"   - Username: {user.username}")
    print(f"   - Email: {user.email}")
    print(f"   - Is Active: {user.is_active}")
    print(f"   - Is Staff: {user.is_staff}")
    print(f"   - Is Superuser: {user.is_superuser}")
    
    try:
        profile = UserProfile.objects.get(user=user)
        print(f"✅ RPG Profile Exists")
        print(f"   - Role: {profile.role}")
        print(f"   - Class: {profile.character_class.name}")
        print(f"   - Level: {profile.level}")
        print(f"   - Employee ID: {profile.employee_id}")
    except UserProfile.DoesNotExist:
        print("❌ ORPHAN ACCOUNT: User exists but has NO RPG Profile!")
        
except User.DoesNotExist:
    print(f"❌ User '{username}' DOES NOT EXIST in the database.")

print('='*60 + '\n')
