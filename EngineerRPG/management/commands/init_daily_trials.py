"""
初始化每日試煉模板 + 生成今日任務

用法:
    python manage.py init_daily_trials           # 建立模板+生成今日任務
    python manage.py init_daily_trials --generate # 只生成今日任務（模板已存在時）
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from EngineerRPG.models import Trial, QuestionCategory, Question


class Command(BaseCommand):
    help = '初始化每日試煉模板並生成今日任務'

    def add_arguments(self, parser):
        parser.add_argument(
            '--generate',
            action='store_true',
            help='只生成今日任務（不建立模板）',
        )

    def handle(self, *args, **options):
        if not options['generate']:
            self._create_trial_templates()

        self._generate_daily_tasks()

    def _create_trial_templates(self):
        """建立 3 個每日試煉模板"""
        categories = list(QuestionCategory.objects.all())
        
        templates = [
            {
                'title': '晨間鍛鍊',
                'description': '清晨的基礎訓練，適合暖身的試煉。',
                'trial_type': 'DAILY',
                'question_count': 10,
                'time_limit_minutes': 15,
                'required_level': 1,
                'exp_reward': 50,
                'is_daily': True,
                'is_active': True,
            },
            {
                'title': '午間挑戰',
                'description': '中等難度的挑戰，考驗你的專業知識。',
                'trial_type': 'DAILY',
                'question_count': 10,
                'time_limit_minutes': 20,
                'required_level': 1,
                'exp_reward': 80,
                'is_daily': True,
                'is_active': True,
            },
            {
                'title': '黃昏試煉',
                'description': '一天的最終試煉，綜合測驗你的實力。',
                'trial_type': 'DAILY',
                'question_count': 10,
                'time_limit_minutes': 25,
                'required_level': 1,
                'exp_reward': 120,
                'is_daily': True,
                'is_active': True,
            },
        ]

        created_count = 0
        for tmpl in templates:
            trial, created = Trial.objects.get_or_create(
                title=tmpl['title'],
                defaults=tmpl,
            )
            if created:
                # 綁定所有啟用題目（generate_daily_tasks 會自行隨機抽題）
                trial.questions.set(Question.objects.filter(is_active=True))
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✔ 建立試煉模板: {trial.title}'))
            else:
                self.stdout.write(f'  已存在: {trial.title}')

        self.stdout.write(self.style.SUCCESS(f'\n共建立 {created_count} 個新模板'))

    def _generate_daily_tasks(self):
        """生成今日每日任務"""
        from EngineerRPG.utils import generate_daily_tasks

        today = timezone.now().date()
        self.stdout.write(f'\n生成 {today} 的每日任務...')
        
        tasks = generate_daily_tasks(date=today)
        if tasks:
            self.stdout.write(self.style.SUCCESS(f'✔ 成功生成 {len(tasks)} 個每日任務！'))
            for t in tasks:
                q_count = t.questions.count()
                self.stdout.write(f'  任務 {t.task_number}: {t.trial.title} ({q_count} 題)')
        else:
            self.stdout.write(self.style.WARNING('⚠ 無法生成任務，請檢查是否有啟用的題目與試煉模板。'))
