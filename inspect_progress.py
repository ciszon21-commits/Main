from EngineerRPG.models import UserProfile, DailyTrialProgress, Question

username = 'SINGLE-AUTH_07729'
try:
    profile = UserProfile.objects.get(user__username=username)
except UserProfile.DoesNotExist:
    profile = UserProfile.objects.first()

# Get the latest progress
progress = DailyTrialProgress.objects.filter(user_profile=profile).order_by('-id').first()

if progress:
    print(f"Latest Progress ID: {progress.id}")
    print(f"Started At: {progress.started_at}")
    print(f"Initial HP: {progress.initial_hp}")
    print(f"Current HP: {progress.current_hp}")
    print(f"Total Damage Taken: {progress.initial_hp - progress.current_hp}")
    
    print("\nRecorded Answers:")
    answers = progress.answers
    if answers:
        count = 0
        for q_id, data in answers.items():
            count += 1
            print(f"Q{count} (ID {q_id}): Correct={data.get('is_correct')}")
            # Try to fetch the question to see difficulty
            try:
                q = Question.objects.get(id=q_id)
                print(f"  Difficulty: {q.difficulty}")
            except:
                print("  Question not found")
    else:
        print("No answers recorded.")

else:
    print("No progress found.")
