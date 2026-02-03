import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CoDevStudio.settings")
django.setup()

from django.contrib.auth.models import User
from EngineerRPG.models import UserProfile

username = '黃瑞澤'
print(f"\n{'='*20} UPGRADING USER: {username} {'='*20}")

try:
    user = User.objects.get(username=username)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"✅ User permissions updated: Staff=True, Superuser=True")
    
    try:
        profile = UserProfile.objects.get(user=user)
        profile.role = 'ADMIN'
        profile.save()
        print(f"✅ UserProfile role updated to: ADMIN")
    except UserProfile.DoesNotExist:
        print("❌ ORPHAN ACCOUNT: User exists but has NO RPG Profile!")
        
except User.DoesNotExist:
    print(f"❌ User '{username}' DOES NOT EXIST in the database.")

print('='*60 + '\n')
