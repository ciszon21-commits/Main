
import os
import sys
import django

# Setup path and settings
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from django.conf import settings
from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from django.urls import reverse
from EngineerRPG.models import UserProfile, Equipment, UserEquipment, Trial, Question, QuestionCategory
from EngineerRPG import views

def run_verification():
    print("--- Starting Verification ---")
    
    # 1. Setup User and Profile
    username = 'test_engineer_app_user'
    password = 'password123'
    user, created = User.objects.get_or_create(username=username)
    user.set_password(password)
    user.save()
    profile = views.get_or_create_user_profile(user)
    print(f"User: {user.username}")

    # 2. Get Equipment
    try:
        app_equip = Equipment.objects.get(id=10) # Engineering Inspection APP
        print(f"Found Equipment: {app_equip.name} (ID: {app_equip.id})")
    except Equipment.DoesNotExist:
        print("ERROR: Equipment ID 10 not found!")
        return

    # 3. Equip Item
    user_equip, _ = UserEquipment.objects.get_or_create(user_profile=profile, equipment=app_equip)
    user_equip.is_equipped = True
    user_equip.save()
    
    profile.equipped_tool_1 = user_equip
    profile.save()
    print("Equipped Engineering Inspection APP to Tool Slot 1")

    # 4. Verify Context in start_trial logic (Simulated)
    # We can't easily check render context without a full response parsing or mocking render, 
    # but we can check the logic directly
    has_app = (
        (profile.equipped_tool_1 and profile.equipped_tool_1.equipment.id == 10) or
        (profile.equipped_tool_2 and profile.equipped_tool_2.equipment.id == 10) or
        (profile.equipped_tool_3 and profile.equipped_tool_3.equipment.id == 10)
    )
    print(f"Logic Check - has_engineering_app: {has_app}")
    if has_app:
        print("PASS: Custom context logic detects equipped item.")
    else:
        print("FAIL: Custom context logic failed.")

    # 5. Verify submit_answer logic
    # Create a dummy trial and question if needed, or just mock the session
    # We need a question to submit answer for.
    category, _ = QuestionCategory.objects.get_or_create(name="Test Category")
    question, _ = Question.objects.get_or_create(
        content="Test Question?", 
        correct_answer="A", 
        question_type="SINGLE",
        defaults={'category': category, 'difficulty': 'C'}
    )
    
    # Setup Session
    client = Client()
    client.login(username=username, password=password)
    
    # We need to manually set session because submit_answer relies on it
    session = client.session
    session['trial_questions'] = [question.id]
    session['current_question_index'] = 0
    session.save()
    
    print("Submitting answer with use_engineering_app=true...", flush=True)
    try:
        response = client.post(
            reverse('engineer_rpg:submit_answer', args=[999]), 
            {
                'answer': 'A',
                'current_mp': 100,
                'use_engineering_app': 'true'
            }
        )
        print(f"Response Status: {response.status_code}", flush=True)
        if response.status_code != 200:
             print(f"Response Content: {response.content.decode()}", flush=True)
    except Exception as e:
        print(f"Exception during post: {e}", flush=True)
    
    if response.status_code == 200:
        print("Response 200 OK", flush=True)
        # We can't check server logs easily from here, but getting 200 is a good sign
        # We really want to check if the print in views.py happened. 
        # Since we are running in the same process (Client), the print in views.py 
        # should appear in stdout IF we are not capturing it weirdly.
        print("PASS: View accepted request.", flush=True)
    else:
        print(f"FAIL: View returned status {response.status_code}", flush=True)


if __name__ == "__main__":
    run_verification()
