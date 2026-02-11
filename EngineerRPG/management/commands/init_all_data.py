"""
統一初始化所有資料（已改為呼叫 seed_all_data）

建議直接使用：
  python manage.py seed_all_data          # 僅新增不存在的資料
  python manage.py seed_all_data --clear  # 清除後重建
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = '統一初始化所有 RPG 系統資料（已改為呼叫 seed_all_data）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='清除所有現有資料後重建',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            '  [提示] init_all_data 已改為呼叫 seed_all_data'))
        if options.get('clear'):
            call_command('seed_all_data', '--clear')
        else:
            call_command('seed_all_data')
