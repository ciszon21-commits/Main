
import os
import django
import sys

# Add the project directory to sys.path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from LunchOrder.models import Restaurant

restaurants = Restaurant.objects.all()
if not restaurants:
    print("NO RESTAURANTS FOUND")
else:
    for r in restaurants:
        print(f"ID: {r.id}, Name: {r.name}")
