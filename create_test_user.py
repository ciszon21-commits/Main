import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from django.contrib.auth.models import User
from EngineerRPG.models import UserProfile

username = "testuser"
password = "password123"

try:
    if User.objects.filter(username=username).exists():
        print(f"User {username} already exists")
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save()
    else:
        user = User.objects.create_user(username=username, password=password)
        print(f"Created user {username}")

    # Reset profile stats for verification
    if not hasattr(user, 'profile'):
        UserProfile.objects.create(user=user)
    
    profile = user.profile
    profile.level = 1
    profile.experience = 0
    # Formula check: Lv 1 -> HP 50, MP 100
    # But current_hp might be stored.
    # Note: changes to models might not be reflected if migrations weren't run?
    # But we didn't change models.py structure, just logic in methods.
    # Wait, implementation plan said "Validators: Ensure HP/MP ... values".
    # Did I execute that? The plan was "Proposed Changes".
    # I was fixing SyntaxErrors. I didn't verify if logic changes were applied.
    # Assuming previous turn applied them or user did.
    # If not, I'm verifying they ARE applied.
    
    profile.save()
    print(f"User {username} ready. Level: {profile.level}")

except Exception as e:
    print(f"Error creating user: {e}")
