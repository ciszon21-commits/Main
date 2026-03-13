from django.core.management.base import BaseCommand
from LunchOrder.models import Restaurant, MenuItem


class Command(BaseCommand):
    help = '載入便當菜單資料'

    def handle(self, *args, **options):
        # 建立便當店
        restaurant, created = Restaurant.objects.get_or_create(
            name='2026年1月版便當',
            defaults={
                'phone': '',
                'address': '',
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'建立便當店: {restaurant.name}'))
        else:
            self.stdout.write(f'便當店已存在: {restaurant.name}')

        # 菜單項目資料 (從圖片解析)
        menu_items = [
            # 雞肉 CHICKEN
            {'name': '舒肥雞胸餐盒', 'price': 120, 'description': '增肌減脂推薦'},
            {'name': '祖傳雞腿餐盒', 'price': 120, 'description': ''},
            {'name': '夏日檸檬雞餐盒', 'price': 125, 'description': '新發售'},
            {'name': '蔥油嫩雞胸餐盒', 'price': 125, 'description': ''},
            {'name': '醬燒春雞餐盒', 'price': 130, 'description': '限量販售'},
            {'name': '韓式辣雞餐盒', 'price': 130, 'description': 'Best 小辣'},
            {'name': '川味香麻雞餐盒', 'price': 130, 'description': '小辣'},
            
            # 魚 FISH
            {'name': '鮮烤鯖魚餐盒', 'price': 120, 'description': ''},
            
            # 豬肉 PORK
            {'name': '泰式打拋豬餐盒', 'price': 115, 'description': '店長推薦 微辣 正港台灣豬'},
            {'name': '蒜醬里肌餐盒', 'price': 115, 'description': ''},
            {'name': '泡菜里肌餐盒', 'price': 125, 'description': '微辣'},
            {'name': '花雕滷軟骨餐盒', 'price': 125, 'description': '新發售'},
            
            # 牛肉 BEEF
            {'name': '蔥燒雪花牛餐盒', 'price': 140, 'description': ''},
            {'name': '泡菜雪花牛餐盒', 'price': 140, 'description': '新發售 微辣'},
            {'name': '照燒杏鮑菇餐盒', 'price': 105, 'description': '蔬食全餐'},
            
            # 單點品項
            {'name': '地瓜(4塊)', 'price': 15, 'description': '單點'},
            {'name': '全熟蛋', 'price': 15, 'description': '單點'},
            {'name': '紫米飯', 'price': 20, 'description': '單點'},
            {'name': '時令青菜', 'price': 35, 'description': '單點'},
            
            # 無糖冷泡茶
            {'name': '蜜香紅茶', 'price': 35, 'description': '無糖冷泡茶'},
            {'name': '高山青茶', 'price': 35, 'description': '無糖冷泡茶'},
            {'name': '桂花烏龍', 'price': 35, 'description': '無糖冷泡茶'},
            {'name': '玫瑰綠茶', 'price': 35, 'description': '無糖冷泡茶'},
            {'name': '粉玫瑰花茶', 'price': 35, 'description': '花草茶類'},
            {'name': '洋甘菊花茶', 'price': 35, 'description': '花草茶類'},
            {'name': '歐薄荷葉茶', 'price': 35, 'description': '花草茶類'},
            {'name': '藍莓水果茶', 'price': 35, 'description': '花草茶類'},
        ]

        created_count = 0
        for item_data in menu_items:
            item, created = MenuItem.objects.get_or_create(
                restaurant=restaurant,
                name=item_data['name'],
                defaults={
                    'price': item_data['price'],
                    'description': item_data['description'],
                    'is_available': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  + {item.name} ${item.price}')

        self.stdout.write(self.style.SUCCESS(f'共載入 {created_count} 個菜單項目'))
