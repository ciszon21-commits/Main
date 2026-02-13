from django.core.management.base import BaseCommand
from LunchOrder.models import Restaurant, MenuItem

class Command(BaseCommand):
    help = 'Import 龍舫牛肉麵疙瘩 menu'

    def handle(self, *args, **options):
        # 1. Update or Create Restaurant
        restaurant, created = Restaurant.objects.update_or_create(
            name='龍舫牛肉麵疙瘩',
            defaults={
                'phone': '(07)3365330',
                'address': '高雄市文橫三路170號',
                'is_active': True,
                # 'image_file': 'menu_dragon_boat.jpg'  # Assuming user will upload or we will handle later. For now, leave as is or update if we had the file.
            }
        )
        
        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f'{action} Restaurant: {restaurant.name}'))

        # 2. Define Menu Items
        # Based on the image provided
        menu_items_data = [
            # 疙瘩類 (Gnocchi - Noodle category)
            {'name': '牛肉湯疙瘩', 'price': 140, 'category': 'noodle'},
            {'name': '牛肉乾疙瘩', 'price': 140, 'category': 'noodle'},
            {'name': '牛湯疙瘩(無肉)', 'price': 60, 'category': 'noodle'},
            {'name': '牛乾疙瘩(無肉)', 'price': 60, 'category': 'noodle'},
            {'name': '榨菜湯疙瘩', 'price': 60, 'category': 'noodle'},
            {'name': '榨菜乾疙瘩', 'price': 60, 'category': 'noodle'},

            # 麵類 (Noodles)
            {'name': '牛肉拉麵', 'price': 130, 'category': 'noodle'},
            {'name': '牛肉乾麵', 'price': 130, 'category': 'noodle'},
            {'name': '牛湯麵(無肉)', 'price': 60, 'category': 'noodle'},
            {'name': '牛乾麵(無肉)', 'price': 60, 'category': 'noodle'},
            {'name': '榨菜湯麵', 'price': 50, 'category': 'noodle'},
            {'name': '榨菜乾麵', 'price': 50, 'category': 'noodle'},
            {'name': '榨菜餛飩湯麵', 'price': 70, 'category': 'noodle'},
            {'name': '榨菜餛飩乾麵', 'price': 70, 'category': 'noodle'},

            # 飯類 (Rice)
            {'name': '牛肉蛋炒飯', 'price': 85, 'category': 'beef'},
            {'name': '蝦仁蛋炒飯', 'price': 85, 'category': 'fish'}, # Using 'fish' for seafood/shrimp as closest approximation or 'other'
            {'name': '火腿蛋炒飯', 'price': 85, 'category': 'pork'}, # Ham is usually pork
            {'name': '肉絲蛋炒飯', 'price': 85, 'category': 'pork'},
            {'name': '鮭魚蛋炒飯', 'price': 95, 'category': 'fish'},
            {'name': '肉燥飯(小)', 'price': 35, 'category': 'pork'},
            {'name': '肉燥飯(大)', 'price': 45, 'category': 'pork'},

            # 水餃類 (Dumplings - grouped under noodle or other? Let's use 'noodle' or 'other'. 'noodle' fits "flour-based")
            # Image says "水餃每個5元 (10個)", handwritten change to 60/10pc? No, handwritten says 50->60.
            # Let's look at the handwritten notes carefully.
            # 水餃 (10個) 50 -> 60.  So price is 60 for 10.
            {'name': '水餃(10個)', 'price': 60, 'category': 'noodle'},
            
            # 牛湯餃 70 -> 80
            {'name': '牛湯餃', 'price': 80, 'category': 'noodle'},
            
            # 榨菜湯餃 70 -> 80
            {'name': '榨菜湯餃', 'price': 80, 'category': 'noodle'},

            # 湯類 (Soup)
            {'name': '餛飩湯', 'price': 50, 'category': 'soup'},
            {'name': '青菜蛋花湯', 'price': 35, 'category': 'soup'},
            {'name': '魚丸湯', 'price': 35, 'category': 'soup'},
            {'name': '牛肉湯', 'price': 110, 'category': 'soup'},

            # 小菜類 (Sides)
            {'name': '燙青菜', 'price': 30, 'category': 'side'},
            {'name': '魯味1份', 'price': 30, 'category': 'side'},
            {'name': '皮蛋豆腐', 'price': 40, 'category': 'side'},
        ]

        # 3. Create Menu Items
        for item_data in menu_items_data:
            menu_item, created = MenuItem.objects.update_or_create(
                restaurant=restaurant,
                name=item_data['name'],
                defaults={
                    'price': item_data['price'],
                    'category': item_data['category'],
                    'is_available': True
                }
            )
            status = "Created" if created else "Updated"
            self.stdout.write(f'  - {status} {menu_item.name} (${menu_item.price})')

        self.stdout.write(self.style.SUCCESS('Successfully imported menu for 龍舫牛肉麵疙瘩'))
