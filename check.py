import os
import django
import datetime
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from LunchOrder.models import LunchOrder, RestaurantSchedule
from django.utils import timezone

today = timezone.localtime(timezone.now()).date()

print("Deleting records for today:", today)

# Delete orders
orders = LunchOrder.objects.filter(order_date=today)
order_count = orders.count()
orders.delete()
print(f"Deleted {order_count} lunch orders.")

# Delete schedule
schedules = RestaurantSchedule.objects.filter(date=today)
schedule_count = schedules.count()
schedules.delete()
print(f"Deleted {schedule_count} restaurant schedules.")

