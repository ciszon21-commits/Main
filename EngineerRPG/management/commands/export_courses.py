"""
匯出課程資料為 Python 程式碼
將現有的 Course 匯出為可執行的初始化程式碼
"""

from django.core.management.base import BaseCommand
from EngineerRPG.models import Course
import json


class Command(BaseCommand):
    help = '匯出課程資料為 Python 程式碼'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='EngineerRPG/management/commands/init_courses_data.py',
            help='輸出檔案路徑'
        )

    def handle(self, *args, **options):
        output_file = options['output']
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('開始匯出課程資料...'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        # 匯出課程
        courses = Course.objects.all()
        self.stdout.write(f'\n📚 匯出課程: {courses.count()} 個')
        
        courses_data = []
        for course in courses:
            # 取得關聯的技能節點名稱
            skill_node_names = list(course.skill_nodes.values_list('name', flat=True))
            
            # 取得關聯的題目分類名稱（透過題目的分類）
            question_categories = set()
            for question in course.questions.all():
                if question.category:
                    question_categories.add(question.category.name)
            
            course_dict = {
                'title': course.title,
                'description': course.description,
                'content_type': course.content_type,
                'content_url': course.content_url,
                'duration_minutes': course.duration_minutes,
                'passing_score': course.passing_score,
                'exam_time_limit': course.exam_time_limit,
                'skill_node_names': skill_node_names,
                'question_category_names': list(question_categories),
                'question_count': course.questions.count(),
            }
            courses_data.append(course_dict)
            
            self.stdout.write(f'   - {course.title}')
            self.stdout.write(f'     關聯技能: {len(skill_node_names)}個')
            self.stdout.write(f'     考試題目: {course.questions.count()}題')
        
        # 生成 Python 程式碼
        self.stdout.write(f'\n💾 生成 Python 程式碼...')
        
        code = self._generate_code(courses_data)
        
        # 寫入檔案
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS(f'✅ 匯出完成！'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(f'   輸出檔案: {output_file}')
        self.stdout.write(f'   課程總數: {len(courses_data)} 個')
        self.stdout.write(self.style.SUCCESS('=' * 80))
    
    def _generate_code(self, courses_data):
        """生成 Python 程式碼"""
        
        code = '''"""
課程初始化資料
此檔案由 export_courses command 自動生成
包含課程資料及其與技能節點、題目的關聯
"""

# 課程資料
COURSES = '''
        
        code += json.dumps(courses_data, ensure_ascii=False, indent=4)
        
        code += '''
'''
        
        return code
