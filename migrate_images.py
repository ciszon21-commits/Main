import os
import shutil
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from LunchOrder.models import Restaurant
from django.conf import settings

static_dir = os.path.join(settings.BASE_DIR, 'LunchOrder', 'static', 'LunchOrder')
media_dir = os.path.join(settings.MEDIA_ROOT, 'lunch_menus')

os.makedirs(media_dir, exist_ok=True)

restaurants = Restaurant.objects.exclude(image_file__isnull=True).exclude(image_file='')

for r in restaurants:
    old_filename = str(r.image_file)
    
    # Check if already migrated
    if old_filename.startswith('lunch_menus/'):
        continue
        
    old_path = os.path.join(static_dir, old_filename)
    new_path = os.path.join(media_dir, old_filename)
    
    if os.path.exists(old_path):
        shutil.copy2(old_path, new_path)
        print(f"Copied {old_path} to {new_path}")
    else:
        print(f"Warning: File {old_path} not found.")
        
    # Update db 
    r.image_file = f"lunch_menus/{old_filename}"
    r.save()
    print(f"Updated {r.name} image_file to {r.image_file}")
    
print("Migration completed.")
