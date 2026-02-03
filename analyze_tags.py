import os
import django
import sys

# Setup Django environment
sys.path.append('d:\\10.vibecoding\\CoDevStudio-07729')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.models import Question, QuestionCategory

print("--- Categories ---")
for cat in QuestionCategory.objects.all():
    print(f"ID: {cat.id}, Name: {cat.name}")

print("\n--- Distinct Tags ---")
tags = Question.objects.values_list('tags', flat=True).distinct()
for tag in tags:
    print(f"'{tag}'")
