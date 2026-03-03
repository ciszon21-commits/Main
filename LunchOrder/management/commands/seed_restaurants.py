"""
管理命令: seed_restaurants
將所有便當店與菜單品項一次性匯入資料庫（或更新既有資料）。

用法:
    python manage.py seed_restaurants              # 建立不存在的資料（跳過已存在的）
    python manage.py seed_restaurants --force       # 刪除後重建所有資料
"""
import json
import os

from django.core.management.base import BaseCommand
from LunchOrder.models import Restaurant, MenuItem


class Command(BaseCommand):
    help = '匯入所有便當店與菜單品項至資料庫'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='刪除所有現有餐廳與品項後重新建立',
        )

    def handle(self, *args, **options):
        # 讀取 JSON 資料檔
        data_path = os.path.join(os.path.dirname(__file__), 'restaurant_data.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            restaurants_data = json.load(f)

        if options['force']:
            self.stdout.write(self.style.WARNING('⚠ --force 模式：刪除所有現有餐廳與品項...'))
            MenuItem.objects.all().delete()
            Restaurant.objects.all().delete()

        created_restaurants = 0
        skipped_restaurants = 0
        created_items = 0

        for r_data in restaurants_data:
            restaurant, created = Restaurant.objects.get_or_create(
                name=r_data['name'],
                defaults={
                    'phone': r_data.get('phone', ''),
                    'address': r_data.get('address', ''),
                    'image_file': r_data.get('image_file', ''),
                    'is_active': r_data.get('is_active', True),
                }
            )

            if created:
                created_restaurants += 1
                self.stdout.write(f'  ✅ 新增餐廳: {restaurant.name}')
            else:
                skipped_restaurants += 1
                # 更新基本資料
                updated = False
                for field in ('phone', 'address', 'image_file', 'is_active'):
                    new_val = r_data.get(field)
                    if new_val is not None and getattr(restaurant, field) != new_val:
                        setattr(restaurant, field, new_val)
                        updated = True
                if updated:
                    restaurant.save()
                    self.stdout.write(f'  🔄 更新餐廳: {restaurant.name}')
                else:
                    self.stdout.write(f'  ⏭  已存在: {restaurant.name}')

            # 處理菜單品項
            for item_data in r_data.get('items', []):
                _, item_created = MenuItem.objects.get_or_create(
                    restaurant=restaurant,
                    name=item_data['name'],
                    defaults={
                        'price': item_data.get('price', 0),
                        'category': item_data.get('category', 'single'),
                        'is_available': item_data.get('is_available', True),
                    }
                )
                if item_created:
                    created_items += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'完成！新增 {created_restaurants} 家餐廳、'
            f'{created_items} 個品項，'
            f'{skipped_restaurants} 家已存在'
        ))
