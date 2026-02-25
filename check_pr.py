import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.models import PromotionRequest, UserProfile

print("Promotion Requests:")
for p in PromotionRequest.objects.all():
    team_name = p.applicant.current_team.name if p.applicant.current_team else "None"
    print(f"ID: {p.id}, Applicant: {p.applicant.user.username}, Status: {p.status}, Team: {team_name}")
    
print("\nUser Profile:")
user_profile = UserProfile.objects.filter(user__username='SINGLE-AUTH_07729').first()
if user_profile:
    print(f"Role: {user_profile.role}, Team: {user_profile.current_team.name if user_profile.current_team else 'None'}")
