"""
初始化課程資料
從 init_courses_data.py 讀取資料並建立課程
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from EngineerRPG.models import Course, SkillNode, Question, QuestionCategory


class Command(BaseCommand):
    help = '初始化課程資料'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='清除現有課程資料後重建'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('開始初始化課程資料...'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        # 匯入資料
        try:
            from .init_courses_data import COURSES
        except ImportError:
            self.stdout.write(self.style.ERROR('❌ 找不到 init_courses_data.py'))
            self.stdout.write(self.style.ERROR('請先執行: python manage.py export_courses'))
            return
        
        with transaction.atomic():
            # 清除舊資料
            if options['clear']:
                self.stdout.write('\n🗑️  清除舊資料...')
                Course.objects.all().delete()
                self.stdout.write(self.style.WARNING('   已清除所有課程'))
            
            # 建立課程
            self.stdout.write('\n📚 建立課程...')
            created_count = 0
            updated_count = 0
            
            for course_data in COURSES:
                # 建立或更新課程
                course, created = Course.objects.update_or_create(
                    title=course_data['title'],
                    defaults={
                        'description': course_data['description'],
                        'content_type': course_data['content_type'],
                        'content_url': course_data['content_url'],
                        'duration_minutes': course_data['duration_minutes'],
                        'passing_score': course_data['passing_score'],
                        'exam_time_limit': course_data['exam_time_limit'],
                    }
                )
                
                action = '新增' if created else '更新'
                self.stdout.write(f'   {action}: {course.title}')
                
                # 關聯技能節點
                if course_data.get('skill_node_names'):
                    skill_nodes = SkillNode.objects.filter(
                        name__in=course_data['skill_node_names']
                    )
                    course.skill_nodes.set(skill_nodes)
                    self.stdout.write(f'      關聯技能: {skill_nodes.count()}個')
                
                # 關聯題目（從分類中選取）
                if course_data.get('question_category_names'):
                    questions = Question.objects.filter(
                        category__name__in=course_data['question_category_names']
                    )
                    # 如果有指定題目數量，則隨機選取
                    if course_data.get('question_count') and questions.exists():
                        questions = questions.order_by('?')[:course_data['question_count']]
                    course.questions.set(questions)
                    self.stdout.write(f'      考試題目: {course.questions.count()}題')
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            # 統計資訊
            self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
            self.stdout.write(self.style.SUCCESS('✅ 課程資料初始化完成！'))
            self.stdout.write(self.style.SUCCESS('=' * 80))
            self.stdout.write(f'   📚 課程總數: {Course.objects.count()} 個')
            self.stdout.write(f'      - 新增: {created_count} 個')
            self.stdout.write(f'      - 更新: {updated_count} 個')
            
            # 課程詳情
            self.stdout.write('\n   📊 課程列表:')
            for course in Course.objects.all():
                self.stdout.write(f'      - {course.title}')
                self.stdout.write(f'        技能: {course.skill_nodes.count()}個 | 題目: {course.questions.count()}題')
            
            self.stdout.write(self.style.SUCCESS('=' * 80))
