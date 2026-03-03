from django.core.management.base import BaseCommand
from LunchOrder.models import Restaurant, MenuItem

class Command(BaseCommand):
    help = 'Add Kaoling Restaurant and Menu'

    def handle(self, *args, **options):
        # Create Restaurant
        restaurant, created = Restaurant.objects.get_or_create(
            name='高嶺(南越傳統美食)',
            defaults={
                'phone': '07-338-0252, 0902131926',
                'address': '高雄市苓雅區興中一路324號',
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created restaurant: {restaurant.name}'))
        else:
            self.stdout.write(f'Restaurant already exists: {restaurant.name}')

        # Menu Items
        menu_items = [
            {'name': '滷排骨飯', 'price': 80, 'category': 'pork'},
            {'name': '香茅雞肉飯', 'price': 80, 'category': 'chicken'},
            {'name': '酥炸大排骨飯', 'price': 85, 'category': 'pork'},
            {'name': '鳳梨滷魚飯', 'price': 75, 'category': 'fish'},
            {'name': '高嶺滷肉飯', 'price': 80, 'category': 'pork'},
            {'name': '無骨腿排飯', 'price': 95, 'category': 'chicken'},
            {'name': '辣椒鹽烤魚飯', 'price': 90, 'category': 'fish'},
            {'name': '香茅煎魚飯', 'price': 85, 'category': 'fish'},
            {'name': '烤雞腿飯', 'price': 100, 'category': 'chicken'},
            {'name': '酥炸大雞腿飯', 'price': 95, 'category': 'chicken'},
            {'name': '港式油雞腿飯', 'price': 95, 'category': 'chicken'},
            {'name': '香烤梅花豬飯', 'price': 95, 'category': 'pork'},
            {'name': '招牌雙拼飯', 'price': 95, 'category': 'other'},
            {'name': '鱈魚飯', 'price': 100, 'category': 'fish'},
            {'name': '海陸空三寶飯', 'price': 110, 'category': 'other'},
            {'name': '養生菜飯', 'price': 60, 'category': 'veg'},
            {'name': '南越香茅腿麵', 'price': 85, 'category': 'noodle'},
            {'name': '南越排骨麵', 'price': 85, 'category': 'noodle'},
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
