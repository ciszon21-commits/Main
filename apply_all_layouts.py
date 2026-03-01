import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.utils.skill_layout import apply_layout_to_db
from EngineerRPG.models import CharacterClass

def update_all_layouts():
    classes = CharacterClass.objects.all()
    for cc in classes:
        count = apply_layout_to_db(cc.code)
        print(f"Applied layout to {cc.name} ({cc.code}): {count} nodes updated.")

if __name__ == "__main__":
    update_all_layouts()
