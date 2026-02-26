import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from django.contrib.auth.models import User
from EngineerRPG.models import UserProfile, TeamMembership

print("Checking user data...")

user = User.objects.filter(username__contains='黃瑞澤').first()
if not user:
    # Try finding by full name or ID
    users = User.objects.all()
    for u in users:
        if '黃瑞澤' in (u.get_full_name() or '') or '黃瑞澤' in u.username:
            user = u
            break

if user:
    print(f"Found User ID: {user.id}, Username: {user.username}, FullName: {user.get_full_name()}")
    try:
        profile = user.rpg_profile
        print(f"Profile: OK, Role: {profile.role}")
        team_name = profile.current_team.name if profile.current_team else "None"
        print(f"Profile current_team: {team_name}")
        
        # Check TeamMembership
        memberships = TeamMembership.objects.filter(user=user)
        if memberships.exists():
            for m in memberships:
                print(f"TeamMembership: {m.team.name} as {m.role}")
        else:
            print("No TeamMembership found.")
            
    except Exception as e:
        print(f"Error getting profile: {e}")
else:
    print("Could not find user '黃瑞澤'")
