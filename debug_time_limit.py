from EngineerRPG.models import Trial, DailyTrialTask
from datetime import date

# Check today's tasks
today = date.today()
tasks = DailyTrialTask.objects.filter(date=today)
print(f"Today's tasks: {tasks.count()}")
for task in tasks:
    print(f"Task {task.task_number}: Trial ID {task.trial.id}, Title: {task.trial.title}, Time Limit: {task.trial.time_limit_minutes}")

# Check all daily trials
daily_trials = Trial.objects.filter(trial_type='DAILY')
print(f"\nAll Daily Trials ({daily_trials.count()}):")
for trial in daily_trials:
    print(f"ID: {trial.id}, Title: {trial.title}, Time Limit: {trial.time_limit_minutes}")

# Force update
print("\nForce updating all DAILY trials to 10 minutes...")
updated = Trial.objects.filter(trial_type='DAILY').update(time_limit_minutes=10)
print(f"Updated {updated} trials.")

# Verify again
tasks = DailyTrialTask.objects.filter(date=today) # Query again to be sure
for task in tasks:
    print(f"Task {task.task_number} (Refreshed): Trial ID {task.trial.id}, Time Limit: {task.trial.time_limit_minutes}")
