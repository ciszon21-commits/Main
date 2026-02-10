import sqlite3
import os
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from EngineerRPG.models import Question, QuestionCategory

class Command(BaseCommand):
    help = 'Import questions from the legacy eng.sqlite3db database'

    def handle(self, *args, **options):
        db_path = os.path.join(settings.BASE_DIR, 'EngineerRPG', 'eng.sqlite3db')
        
        if not os.path.exists(db_path):
            self.stdout.write(self.style.ERROR(f'Legacy database not found at {db_path}'))
            return

        User = get_user_model()
        # Find the first superuser to act as default creator/updater if needed (though Question model has no user field)
        # Keeping this logic in case future models need it or if we decide to log it.
        superuser = User.objects.filter(is_superuser=True).first()
        if not superuser:
            self.stdout.write(self.style.WARNING('No superuser found. Proceeding without a default user context.'))

        # Connect to legacy database
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Access columns by name
            cursor = conn.cursor()
            
            self.import_categories(cursor)
            self.import_questions(cursor)

            conn.close()
            self.stdout.write(self.style.SUCCESS('Import process completed successfully.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during import: {str(e)}'))

    def import_categories(self, cursor):
        self.stdout.write('Importing categories...')
        # Legacy table: EngineerRPG_questioncategory
        # Fields: id, name, description, icon (varchar path), created_at
        
        try:
            cursor.execute("SELECT * FROM EngineerRPG_questioncategory")
            categories = cursor.fetchall()
            
            count = 0
            for row in categories:
                # Map fields
                cat_name = row['name']
                cat_desc = row['description'] if 'description' in row.keys() else ''
                # Note: 'icon' in legacy might be a path string, we can try to preserve it if it matches
                # But FileField usually expects a file object or relative path from MEDIA_ROOT. 
                # We'll assume the string path is compatible or leave it blank to avoid errors.
                cat_icon = row['icon'] if 'icon' in row.keys() else None
                
                obj, created = QuestionCategory.objects.get_or_create(
                    name=cat_name,
                    defaults={
                        'description': cat_desc,
                        'icon': cat_icon
                    }
                )
                
                # If it already exists, we might want to update it? For now, we skip updating to preserve local changes
                # unless we want to force sync. Let's just update description if it was empty.
                if not created and not obj.description and cat_desc:
                    obj.description = cat_desc
                    obj.save()
                    
                count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Processed {count} categories.'))
            
        except sqlite3.OperationalError:
            self.stdout.write(self.style.WARNING('Table EngineerRPG_questioncategory not found in legacy DB.'))

    def import_questions(self, cursor):
        self.stdout.write('Importing questions...')
        # Legacy table: EngineerRPG_question
        # Fields: id, content, question_type, options, correct_answer, explanation, difficulty, tags, image, is_active, created_at, updated_at, category_id
        
        try:
            cursor.execute("SELECT * FROM EngineerRPG_question")
            questions = cursor.fetchall()
            
            count = 0
            created_count = 0
            for row in questions:
                # Find category
                category = None
                if row['category_id']:
                    # We need to find the name of the old category to match with our new ID
                    # Or we can assume IDs might align if we imported sequentially, but safer to match by logic
                    # Since we don't have the old ID -> Name mapping easily available without querying again...
                    # Let's simple query the old category table for this ID
                    cur2 = cursor.connection.cursor()
                    cur2.execute("SELECT name FROM EngineerRPG_questioncategory WHERE id = ?", (row['category_id'],))
                    cat_row = cur2.fetchone()
                    if cat_row:
                        category = QuestionCategory.objects.filter(name=cat_row['name']).first()

                # Parse JSON fields if they are strings
                options = row['options']
                if isinstance(options, str):
                    try:
                        options = json.loads(options)
                    except json.JSONDecodeError:
                        options = {}

                correct_answer = row['correct_answer']
                if isinstance(correct_answer, str):
                    try:
                        correct_answer = json.loads(correct_answer)
                    except json.JSONDecodeError:
                        # Sometimes it might be a raw string like "A" but stored as '"A"' or just 'A'
                        # If load fails, keep as string? or wrap?
                        # Target model expects JSONField.
                        pass

                # Check if question already exists (by content) to avoid duplicates
                # This could be slow for many questions, but safe.
                if Question.objects.filter(content=row['content']).exists():
                    continue

                Question.objects.create(
                    content=row['content'],
                    question_type=row['question_type'],
                    options=options,
                    correct_answer=correct_answer,
                    explanation=row['explanation'],
                    difficulty=row['difficulty'],
                    tags=row['tags'],
                    image=row['image'], # Path string
                    is_active=bool(row['is_active']),
                    category=category,
                    # We can set created_at if we want to preserve history, but Django auto_now_add might override on save
                    # To strictly preserve, we'd need to modify after create or use bulk_create
                )
                created_count += 1
                count += 1
                
                if count % 100 == 0:
                    self.stdout.write(f'Processed {count} questions...')

            self.stdout.write(self.style.SUCCESS(f'Imported {created_count} new questions (skipped {len(questions) - created_count} duplicates).'))

        except sqlite3.OperationalError as e:
            self.stdout.write(self.style.ERROR(f'Table EngineerRPG_question error: {e}'))
