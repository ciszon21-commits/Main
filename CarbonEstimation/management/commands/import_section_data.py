"""
Django management command to import section estimation data.
This command populates the SectionCategory and SectionItem models with data
from the high-speed highway common sections reference.
"""

from django.core.management.base import BaseCommand
from CarbonEstimation.models import SectionCategory, SectionItem


class Command(BaseCommand):
    help = '匯入斷面概算資料（橋梁、路工、隧道、綜合）'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('開始匯入斷面資料...'))

        # 清除現有資料（選用）
        if options.get('clear', False):
            SectionItem.objects.all().delete()
            SectionCategory.objects.all().delete()
            self.stdout.write(self.style.WARNING('已清除現有斷面資料'))

        # 建立分類
        categories = [
            {'code': '橋梁', 'name': '橋梁', 'order': 1},
            {'code': '路工', 'name': '路工', 'order': 2},
            {'code': '隧道', 'name': '隧道', 'order': 3},
            {'code': '綜合', 'name': '綜合', 'order': 4},
        ]

        category_objects = {}
        for cat_data in categories:
            category, created = SectionCategory.objects.get_or_create(
                code=cat_data['code'],
                defaults={
                    'name': cat_data['name'],
                    'order': cat_data['order']
                }
            )
            category_objects[cat_data['code']] = category
            status = '建立' if created else '已存在'
            self.stdout.write(f"  分類: {category.name} ({status})")

        # 建立斷面項目
        section_items = [
            # 橋梁
            {'category': '橋梁', 'work_item': 'PC I梁吊裝工法', 'carbon': 2390.22, 'order': 1},
            {'category': '橋梁', 'work_item': 'PC箱型梁場鑄懸臂工法', 'carbon': 3148.90, 'order': 2},
            {'category': '橋梁', 'work_item': 'PC箱型梁場鑄逐跨工法', 'carbon': 2703.59, 'order': 3},
            {'category': '橋梁', 'work_item': '鋼箱梁吊裝工法', 'carbon': 4717.90, 'order': 4},
            {'category': '橋梁', 'work_item': '斜張橋場鑄工法', 'carbon': 7067.31, 'order': 5},
            
            # 路工
            {'category': '路工', 'work_item': '路塹段', 'carbon': 2200.99, 'order': 1},
            {'category': '路工', 'work_item': '路提段', 'carbon': 1749.98, 'order': 2},
            {'category': '路工', 'work_item': '半挖半填段', 'carbon': 1669.66, 'order': 3},
            
            # 隧道
            {'category': '隧道', 'work_item': 'II類岩體', 'carbon': 3421.59, 'order': 1},
            {'category': '隧道', 'work_item': 'III類岩體', 'carbon': 4051.42, 'order': 2},
            {'category': '隧道', 'work_item': 'IV類岩體', 'carbon': 4354.60, 'order': 3},
            {'category': '隧道', 'work_item': 'V類岩體', 'carbon': 4487.24, 'order': 4},
            {'category': '隧道', 'work_item': 'VI類岩體', 'carbon': 6069.74, 'order': 5},
            
            # 綜合
            {'category': '綜合', 'work_item': '土方遠運', 'carbon': 8.19, 'order': 1},
        ]

        created_count = 0
        updated_count = 0

        for item_data in section_items:
            category = category_objects[item_data['category']]
            
            item, created = SectionItem.objects.update_or_create(
                category=category,
                work_item=item_data['work_item'],
                order=item_data['order'],
                defaults={
                    'unit': 'm2',
                    'carbon_per_unit': item_data['carbon'],
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n匯入完成！'
            f'\n  分類數量: {len(categories)}'
            f'\n  新建項目: {created_count}'
            f'\n  更新項目: {updated_count}'
            f'\n  總項目數: {SectionItem.objects.count()}'
        ))

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='匯入前先清除現有的斷面資料',
        )
