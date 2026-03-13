"""
初始化題庫資料
從 init_questions_data.py 讀取資料並建立題目分類和題目
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from EngineerRPG.models import Question, QuestionCategory, SkillNode


class Command(BaseCommand):
    help = '初始化題庫資料（題目分類和題目）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='清除現有題庫資料後重建'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('開始初始化題庫資料...'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        # 匯入資料
        try:
            from .init_questions_data import CATEGORIES, QUESTIONS
        except ImportError:
            self.stdout.write(self.style.ERROR('❌ 找不到 init_questions_data.py'))
            self.stdout.write(self.style.ERROR('請先執行: python manage.py export_questions'))
            return
        
        with transaction.atomic():
            # 清除舊資料
            if options['clear']:
                self.stdout.write('\n🗑️  清除舊資料...')
                Question.objects.all().delete()
                QuestionCategory.objects.all().delete()
                self.stdout.write(self.style.WARNING('   已清除所有題目和分類'))
            
            # 建立題目分類
            self.stdout.write('\n📁 建立題目分類...')
            category_map = {}
            for cat_data in CATEGORIES:
                category, created = QuestionCategory.objects.get_or_create(
                    name=cat_data['name'],
                    defaults={'description': cat_data['description']}
                )
                category_map[cat_data['name']] = category
                action = '新增' if created else '已存在'
                self.stdout.write(f'   {action}: {category.name}')
            
            # 建立題目
            self.stdout.write('\n📝 建立題目...')
            created_count = 0
            updated_count = 0
            
            for q_data in QUESTIONS:
                # 取得分類
                category = None
                if q_data.get('category_name'):
                    category = category_map.get(q_data['category_name'])
                
                # 建立或更新題目
                question, created = Question.objects.update_or_create(
                    content=q_data['content'],
                    defaults={
                        'question_type': q_data['question_type'],
                        'options': q_data['options'],
                        'correct_answer': q_data['correct_answer'],
                        'explanation': q_data.get('explanation', ''),
                        'difficulty': q_data.get('difficulty', 'B'),
                        'category': category,
                        'tags': q_data.get('tags', ''),
                        'is_active': q_data.get('is_active', True),
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            # 統計資訊
            self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
            self.stdout.write(self.style.SUCCESS('✅ 題庫資料初始化完成！'))
            self.stdout.write(self.style.SUCCESS('=' * 80))
            self.stdout.write(f'   📁 題目分類: {QuestionCategory.objects.count()} 個')
            self.stdout.write(f'   📝 題目總數: {Question.objects.count()} 題')
            self.stdout.write(f'      - 新增: {created_count} 題')
            self.stdout.write(f'      - 更新: {updated_count} 題')
            
            # 分類統計
            self.stdout.write('\n   📊 各分類題目數量:')
            for cat in QuestionCategory.objects.all():
                count = cat.questions.count()
                self.stdout.write(f'      - {cat.name}: {count} 題')
            
            # 難度統計
            self.stdout.write('\n   📊 難度分佈:')
            for difficulty_code, difficulty_name in Question.DIFFICULTY_CHOICES:
                count = Question.objects.filter(difficulty=difficulty_code).count()
                if count > 0:
                    self.stdout.write(f'      - {difficulty_name}: {count} 題')
            
            self.stdout.write(self.style.SUCCESS('=' * 80))
