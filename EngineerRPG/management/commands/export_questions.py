"""
匯出題庫資料為 Python 程式碼
將現有的 Question 和 QuestionCategory 匯出為可執行的初始化程式碼
"""

from django.core.management.base import BaseCommand
from EngineerRPG.models import Question, QuestionCategory
import json


class Command(BaseCommand):
    help = '匯出題庫資料為 Python 程式碼'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='EngineerRPG/management/commands/init_questions_data.py',
            help='輸出檔案路徑'
        )

    def handle(self, *args, **options):
        output_file = options['output']
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('開始匯出題庫資料...'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        # 匯出題目分類
        categories = QuestionCategory.objects.all()
        self.stdout.write(f'\n📁 匯出題目分類: {categories.count()} 個')
        
        categories_data = []
        for cat in categories:
            categories_data.append({
                'name': cat.name,
                'description': cat.description,
            })
            self.stdout.write(f'   - {cat.name} ({cat.questions.count()}題)')
        
        # 匯出題目
        questions = Question.objects.all()
        self.stdout.write(f'\n📝 匯出題目: {questions.count()} 題')
        
        questions_data = []
        for q in questions:
            question_dict = {
                'content': q.content,
                'question_type': q.question_type,
                'options': q.options,
                'correct_answer': q.correct_answer,
                'explanation': q.explanation,
                'difficulty': q.difficulty,
                'category_name': q.category.name if q.category else None,
                'tags': q.tags,
                'is_active': q.is_active,
            }
            questions_data.append(question_dict)
        
        # 生成 Python 程式碼
        self.stdout.write(f'\n💾 生成 Python 程式碼...')
        
        code = self._generate_code(categories_data, questions_data)
        
        # 寫入檔案
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS(f'✅ 匯出完成！'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(f'   輸出檔案: {output_file}')
        self.stdout.write(f'   題目分類: {len(categories_data)} 個')
        self.stdout.write(f'   題目總數: {len(questions_data)} 題')
        self.stdout.write(self.style.SUCCESS('=' * 80))
    
    def _generate_code(self, categories_data, questions_data):
        """生成 Python 程式碼"""
        
        code = '''"""
題庫初始化資料
此檔案由 export_questions command 自動生成
包含題目分類和題目資料
"""

# 題目分類資料
CATEGORIES = '''
        
        code += json.dumps(categories_data, ensure_ascii=False, indent=4)
        
        code += '''

# 題目資料
QUESTIONS = '''
        
        code += json.dumps(questions_data, ensure_ascii=False, indent=4)
        
        code += '''
'''
        
        return code
