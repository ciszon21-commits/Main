import os
import django
import sys

# Setup django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.models import UserProfile, Team, PromotionRequest
from django.contrib.auth.models import User
from django.db.models import Q

def debug():
    search_name = '黃瑞澤'
    p = UserProfile.objects.filter(
        Q(user__username__icontains=search_name) | 
        Q(user__first_name__icontains=search_name) | 
        Q(user__last_name__icontains=search_name)
    ).first()
    
    if not p:
        print(f"User '{search_name}' not found.")
        return

    print(f"FOUND|{p.id}|{p.user.username}|{p.rank}|{p.level}|{p.current_team.id if p.current_team else 0}|{p.current_team.name if p.current_team else 'None'}")
    
    # Check if they have pending promotion requests
    pending = PromotionRequest.objects.filter(applicant=p, status='PENDING').first()
    if pending:
        print(f"PENDING_REQUEST|{pending.id}|From {pending.current_level} to {pending.target_level}")
    else:
        print("NO_PENDING_REQUEST")

if __name__ == '__main__':
    debug()
