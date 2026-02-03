import os
import django
import sys
from django.utils import timezone
import datetime

sys.path.append('D:\\10.vibecoding\\CoDevStudio-07729')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CoDevStudio.settings")
django.setup()

from EngineerRPG.models import Trial

def check_daily_trials():
    print(f"Server Timezone: {timezone.get_current_timezone_name()}")
    now = timezone.now()
    today = now.date()
    print(f"Current Server Time: {now}")
    print(f"Target Date (today): {today}")
    
    print("\n--- All Daily Trials ---")
    dailies = Trial.objects.filter(is_daily=True)
    if not dailies.exists():
        print("No trials found with is_daily=True")
    
    for t in dailies:
        status = []
        if t.is_active: status.append("Active")
        else: status.append("Inactive")
        
        match_date = (t.refresh_date == today)
        status.append(f"Date Match: {match_date} (DB: {t.refresh_date} vs Today: {today})")
        
        print(f"ID: {t.id} | Title: {t.title} | {', '.join(status)}")
        
    print("\n--- Query Test ---")
    matches = Trial.objects.filter(is_daily=True, is_active=True, refresh_date=today)
    print(f"Found {matches.count()} matches for query: is_daily=True, is_active=True, refresh_date={today}")

if __name__ == "__main__":
    check_daily_trials()
