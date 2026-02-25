
import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.models import Equipment

def check_id():
    try:
        equip = Equipment.objects.get(name="工程查驗 APP")
        print(f"FOUND: ID={equip.id}, Name={equip.name}, Type={equip.equipment_type}")
    except Equipment.DoesNotExist:
        print("ERROR: '工程查驗 APP' not found in database.")
        # List all tools to be helpful
        tools = Equipment.objects.filter(equipment_type__startswith='TOOL')
        print("Available Tools:")
        for t in tools:
            print(f"- ID={t.id}, Name={t.name}")

if __name__ == "__main__":
    check_id()
