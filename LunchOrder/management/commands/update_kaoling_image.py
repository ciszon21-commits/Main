from django.core.management.base import BaseCommand
from LunchOrder.models import Restaurant

class Command(BaseCommand):
    help = 'Update Kaoling Restaurant Image'

    def handle(self, *args, **options):
        try:
            restaurant = Restaurant.objects.get(name='高嶺(南越傳統美食)')
            restaurant.image_file = 'menu_kaoling.jpg'
            restaurant.save()
            self.stdout.write(self.style.SUCCESS(f'Updated image for {restaurant.name} to menu_kaoling.jpg'))
        except Restaurant.DoesNotExist:
            self.stdout.write(self.style.ERROR('Restaurant not found'))
