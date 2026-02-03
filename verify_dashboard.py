import os
import django
import sys
sys.path.append('D:\\10.vibecoding\\CoDevStudio-07729')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CoDevStudio.settings")
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from EngineerRPG.views import dashboard

def verify_dashboard():
    print("Verifying Dashboard...")
    
    # Get user
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("No user found.")
        return

    factory = RequestFactory()
    request = factory.get('/rpg/dashboard/')
    request.user = user
    request.session = {}
    
    # Run View
    response = dashboard(request)
    print(f"Status: {response.status_code}")
    
    # Check Content
    content = response.content.decode('utf-8')
    
    # Check for trial titles we know exist from previous check
    # Trial 2: 每日工程挑戰
    # Trial 3: 每日工程實務挑戰
    # Trial 1: 每日工程挑戰
    
    if "每日工程挑戰" in content or "每日工程實務挑戰" in content:
        print("PASS: Found daily trial titles in dashboard.")
    else:
        print("FAIL: Daily trial titles NOT found.")
        # Print a snippet of where the daily trials should be
        idx = content.find("今日練功副本")
        if idx != -1:
             print(f"Snippet: {content[idx:idx+500]}...")
        else:
             print("Snippet: '今日練功副本' section not found.")

if __name__ == "__main__":
    verify_dashboard()
