
import os
import sys
import django
from django.conf import settings

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from EngineerRPG.views import start_trial
from EngineerRPG.models import Trial, DailyTrialTask
import datetime

def verify_context():
    # Get user 1
    user = User.objects.get(id=1)
    print(f"Testing User: {user.username}")
    
    # Get a trial
    trial = Trial.objects.first()
    if not trial:
        print("No trial found.")
        return

    # Setup Request
    factory = RequestFactory()
    request = factory.get(f'/rpg/daily_trial/start/{trial.id}/')
    request.user = user
    request.session = {}
    
    # Run View (partially, just to check context logic if possible, 
    # but start_trial returns HttpResponse, accessing context is hard without using inspection or middleware)
    
    # Instead, let's replicate the logic EXACTLY as in views.py
    from EngineerRPG.views import get_or_create_user_profile
    profile = get_or_create_user_profile(user)
    
    has_app = (
        (profile.equipped_tool_1 and profile.equipped_tool_1.equipment.id == 10) or
        (profile.equipped_tool_2 and profile.equipped_tool_2.equipment.id == 10) or
        (profile.equipped_tool_3 and profile.equipped_tool_3.equipment.id == 10)
    )
    
    print(f"Logic Result in Script: {has_app}")
    
    # Also check the raw output form my previous `check_equipment_id.py` which confirmed "工程查驗 APP" is ID 10.
    # And `debug_equipment.py` confirmed user has it.
    
    # IMPORTANT: The user said "I cannot find the skill button".
    # Check if the button is hidden by CSS?
    # View html content:
    # <p id="engineeringAppStatus" class="text-sm text-stone-light" style="display: none;">
    # The button itself:
    # <button ... id="engineeringAppBtn" onclick="toggleEngineeringApp()">
    
    # Maybe the user is looking for it in a different place?
    # It is in `action-buttons` div.
    
    pass

if __name__ == "__main__":
    verify_context()
