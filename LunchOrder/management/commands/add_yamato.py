from django.core.management.base import BaseCommand
from LunchOrder.models import Restaurant, MenuItem

class Command(BaseCommand):
    help = 'Add Yamato Restaurant and Menu'

    def handle(self, *args, **options):
        # Create Restaurant
        restaurant, created = Restaurant.objects.get_or_create(
            name='大和食堂(興中店)',
            defaults={
                'phone': '07-3385098',
                'address': '高雄市苓雅區興中一路294號',
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created restaurant: {restaurant.name}'))
        else:
            self.stdout.write(f'Restaurant already exists: {restaurant.name}')

        # Menu Items
        menu_items = [
            {'name': '大和排骨飯', 'price': 120, 'category': 'pork'},
            {'name': '西西里雞排', 'price': 145, 'category': 'chicken'},
            {'name': '挪威烤鯖魚', 'price': 150, 'category': 'fish'},
            {'name': '泰式打拋豬', 'price': 135, 'category': 'pork'},
            {'name': '招牌炸雞腿', 'price': 145, 'category': 'chicken'},
            {'name': '香焰豬五花', 'price': 130, 'category': 'pork'},
            {'name': '古早味滷雞腿', 'price': 140, 'category': 'chicken'},
            {'name': '塔香舒肥雞', 'price': 140, 'category': 'chicken'},
            {'name': '經典香雞排', 'price': 119, 'category': 'chicken'},
            {'name': '精選鮭魚', 'price': 165, 'category': 'fish'},
            {'name': '醬烤山賊雞', 'price': 140, 'category': 'chicken'},
            {'name': '義式烤肋排', 'price': 195, 'category': 'pork'},
            {'name': '德式豬腳', 'price': 160, 'category': 'pork'},
            {'name': '香草舒肥雞', 'price': 140, 'category': 'chicken'},
            {'name': '蒲燒鰻魚', 'price': 240, 'category': 'fish'},
            {'name': '蒜香舒肥牛', 'price': 220, 'category': 'beef'},
            {'name': '蔬食餐盒', 'price': 120, 'category': 'veg'},
        ]

        created_count = 0
        updated_count = 0
        
        for item_data in menu_items:
            item, created = MenuItem.objects.update_or_create(
                restaurant=restaurant,
                name=item_data['name'],
                defaults={
                    'price': item_data['price'],
                    'category': item_data['category'],
                    'is_available': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  + Created {item.name} ${item.price}')
            else:
                updated_count += 1
                self.stdout.write(f'  * Updated {item.name} ${item.price}')

        self.stdout.write(self.style.SUCCESS(f'Finished: {created_count} created, {updated_count} updated.'))
