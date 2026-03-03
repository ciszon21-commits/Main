
import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from LunchOrder.models import Restaurant

# Update any restaurant containing "2026" or just the first one if we are sure
# Based on output, it was ID 2.
try:
    r = Restaurant.objects.get(id=2)
    old_name = r.name
    r.name = "勁請享用"
    r.save()
    print(f"Updated Restaurant ID {r.id}: '{old_name}' -> '{r.name}'")
except Restaurant.DoesNotExist:
    print("Restaurant ID 2 not found.")
