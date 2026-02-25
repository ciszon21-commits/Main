import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from django.contrib.auth.models import User
from EngineerRPG.models import PromotionRequest, UserProfile, Team, TeamMembership
from EngineerRPG.utils.permissions import get_or_create_user_profile

user = User.objects.get(username='SINGLE-AUTH_07729')
profile = user.rpg_profile

is_guild_manager = profile.role in ['MANAGER', 'OFFICER']
team = profile.current_team

print(f"User: {user.username}, Role: {profile.role}, Guild Mgr: {is_guild_manager}")
print(f"Team: {team.name}")

is_dept_manager = False
try:
    membership = TeamMembership.objects.get(team=team, user=user)
    print(f"Team Memb: {membership.role}")
    if membership.role in ['LEADER', 'VICE_LEADER']:
        is_dept_manager = True
except TeamMembership.DoesNotExist:
    print("No Team Memb")

can_review_promotions = is_dept_manager
can_view_promotions = is_dept_manager or is_guild_manager

print(f"can_view: {can_view_promotions}, can_review: {can_review_promotions}")

pending_promotions = []
if can_view_promotions:
    pending_promotions = PromotionRequest.objects.filter(
        applicant__current_team=team,
        status='PENDING'
    )

print(f"Pending Promos count: {pending_promotions.count()}")
for p in pending_promotions:
    print(f"  PR ID: {p.id}")
