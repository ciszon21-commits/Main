from django.core.management.base import BaseCommand
from LunchOrder.models import Restaurant, MenuItem

class Command(BaseCommand):
    help = 'Add 甲仙碗粿肉粽(阿歪碗粿) Restaurant and Menu'

    def handle(self, *args, **options):
        # Create Restaurant
        restaurant, created = Restaurant.objects.get_or_create(
            name='甲仙碗粿肉粽(阿歪碗粿)',
            defaults={
                'phone': '07-331-6779',
                'address': '高雄市前鎮區復興三路127號',
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created restaurant: {restaurant.name}'))
        else:
            self.stdout.write(f'Restaurant already exists: {restaurant.name}')

        # Menu Items from the menu image
        menu_items = [
            # 主食類
            {'name': '碗粿', 'price': 35, 'category': 'other'},
            {'name': '肉粽', 'price': 55, 'category': 'other'},
            {'name': '花生粽', 'price': 45, 'category': 'other'},
            # 湯品
            {'name': '蔬活湯', 'price': 65, 'category': 'soup'},
            # 單點
            {'name': '單點炸魚', 'price': 75, 'category': 'single'},
            # 肉焿系列
            {'name': '肉焿(小)', 'price': 65, 'category': 'noodle'},
            {'name': '肉焿(大)', 'price': 75, 'category': 'noodle'},
            # 魚焿系列
            {'name': '魚焿(小)', 'price': 70, 'category': 'noodle'},
            {'name': '魚焿(大)', 'price': 90, 'category': 'noodle'},
            # 綜合焿系列
            {'name': '綜合焿(小)', 'price': 75, 'category': 'noodle'},
            {'name': '綜合焿(大)', 'price': 95, 'category': 'noodle'},
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

        self.stdout.write(self.style.SUCCESS(
            f'\nFinished: {created_count} created, {updated_count} updated.'
        ))
        self.stdout.write(self.style.WARNING(
            '\n備註：焿類可選 焿/米粉/麵/米粉麵，請於訂購時在備註欄註明。'
        ))
