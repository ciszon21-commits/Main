import os
import django
from django.conf import settings
from django.utils import timezone
import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

def check_cutoff():
    now = timezone.localtime(timezone.now())
    today = now.date()
    
    # Logic from views.py
    cutoff_time = now.replace(hour=10, minute=15, second=0, microsecond=0)
    is_past_cutoff = (now > cutoff_time)
    
    print(f"Current Time (timezone.now()): {now}")
    print(f"Current Date (today): {today}")
    print(f"Cutoff Time: {cutoff_time}")
    print(f"Is Past Cutoff? {is_past_cutoff}")
    print(f"Time Zone: {settings.TIME_ZONE}")
    print(f"Use TZ: {settings.USE_TZ}")

    # Check naive vs aware
    print(f"Now tzinfo: {now.tzinfo}")
    print(f"Cutoff tzinfo: {cutoff_time.tzinfo}")

if __name__ == '__main__':
    try:
        check_cutoff()
    except Exception as e:
        print(f"Error: {e}")
