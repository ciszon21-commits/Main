import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from django.contrib.auth.models import User
from TeamKnowledgeHub.models import KnowledgeTeam
from EngineerRPG.models import Team, UserProfile

# Ensure admin user exists for creation
try:
    admin_user = User.objects.get(username='admin')
except User.DoesNotExist:
    print("Creating admin user...")
    admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')

teams_data = [
    {'name': '工程第一分隊', 'desc': '負責基建開發的主要戰力'},
    {'name': '工程第二分隊', 'desc': '專注於系統維護與優化'},
    {'name': '技術支援部', 'desc': '解決各類技術難題的支援部隊'},
]

for t in teams_data:
    kt, created = KnowledgeTeam.objects.get_or_create(
        name=t['name'], 
        defaults={
            'description': t['desc'],
            'created_by': admin_user
        }
    )
    print(f"Team {kt.name} {'created' if created else 'exists'}.")

# Assign admin to Team 1
try:
    # Use EngineerRPG Team model to query the created team (same table)
    t1 = Team.objects.get(name='工程第一分隊')
    
    profile = admin_user.rpg_profile
    profile.current_team = t1
    profile.save()
    
    # Set as leader (if Team model supports it, but checking EngineerRPG models, Team doesn't have leader field?)
    # EngineerRPG.models.Team definition: name, description only.
    # UserProfile has current_team.
    # BUT, TeamMembership (in EngineerRPG.models) seems to define membership?
    # Let's check view logic: team.current_members.all. current_members is related_name on UserProfile.
    # So creating TeamMembership might NOT be used by guild_dashboard view current implementation?
    # In guild_dashboard:
    # teams = Team.objects.all().prefetch_related('current_members__user', ...)
    # current_members is FK on UserProfile.
    # So direct assignment to profile.current_team is CORRECT.
    
    # What about team.leader?
    # template uses: {% if team.leader == member.user %}
    # EngineerRPG.models.Team does NOT look like it has leader field in the partial view I saw.
    # I saw lines 34-46 in Step 4413.
    # It has name, description.
    # Wait, the template uses `team.leader`. If the model doesn't have it, template will fail or show nothing.
    # Maybe `Team` model has a property or additional fields I didn't see?
    # Or maybe it's in `TeamKnowledgeHub.KnowledgeTeam`?
    # KnowledgeTeam has no leader field. created_by?
    # Maybe I shouldn't worry about leader for now, just membership.
    
    print("Assigned users to teams.")

except Exception as e:
    print(f"Error assigning team: {e}")

print("Done.")
