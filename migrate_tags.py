import os
import django
import sys
from django.db.models import Q

# Setup Django environment
sys.path.append('d:\\10.vibecoding\\CoDevStudio-07729')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.models import Question, QuestionCategory

def migrate_tags():
    print("Starting migration...")
    
    # 1. Map '品管' tag to '品質管理' category (ID 1)
    qa_cat = QuestionCategory.objects.get(name='品質管理')
    qa_questions = Question.objects.filter(tags__contains='品管')
    count_qa = qa_questions.update(category=qa_cat, tags='')
    print(f"Updated {count_qa} questions from tag '品管' to category '品質管理'.")

    # 2. Map '職安' tag to '職安衛' category (ID 2)
    safety_cat = QuestionCategory.objects.get(name='職安衛')
    safety_questions = Question.objects.filter(tags__contains='職安')
    count_safety = safety_questions.update(category=safety_cat, tags='')
    print(f"Updated {count_safety} questions from tag '職安' to category '職安衛'.")

    print("Migration complete.")

if __name__ == '__main__':
    migrate_tags()
