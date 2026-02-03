import os
import django
import sys
from django.utils import timezone

sys.path.append('D:\\10.vibecoding\\CoDevStudio-07729')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CoDevStudio.settings")
django.setup()

from EngineerRPG.models import DailyTrialTask

def check_daily_tasks():
    today = timezone.localdate()
    print(f"Checking for DailyTrialTask on {today}...")
    
    tasks = DailyTrialTask.objects.filter(date=today)
    if tasks.exists():
        print(f"Found {tasks.count()} tasks:")
        for t in tasks:
            print(f"- {t} (Trial ID: {t.trial.id})")
    else:
        print("No DailyTrialTask found for today.")

if __name__ == "__main__":
    check_daily_tasks()
