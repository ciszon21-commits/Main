
import os
import sys
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.models import Equipment

def search_item(keyword):
    print(f"Searching for '{keyword}'...")
    items = Equipment.objects.filter(name__icontains=keyword)
    if not items.exists():
        print(f"No items found for '{keyword}'")
    for item in items:
        print(f"FOUND: ID={item.id}, Name='{item.name}', Type={item.equipment_type}")

if __name__ == "__main__":
    search_item('工程')
    search_item('APP')
