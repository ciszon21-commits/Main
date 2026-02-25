from django.core.management.base import BaseCommand
from django.conf import settings
from EngineerRPG.models import Equipment
from PIL import Image, ImageDraw
import os

class Command(BaseCommand):
    help = 'Generates placeholder icons for equipment'

    def handle(self, *args, **options):
        self.stdout.write('Generating equipment icons...')
        items = Equipment.objects.all()
        for item in items:
            self.generate_icon(item)
        self.stdout.write(self.style.SUCCESS('Successfully generated icons'))

    def generate_icon(self, equipment):
        # Colors based on type
        colors = {
            'HELMET': '#3498db', # Blue
            'ARMOR': '#2ecc71', # Green
            'BOOTS': '#f1c40f', # Yellow
            'TOOL': '#9b59b6', # Purple
        }
        bg_color = colors.get(equipment.equipment_type, '#95a5a6') # Gray default
        
        # Create image
        size = (128, 128)
        img = Image.new('RGB', size, color=bg_color)
        d = ImageDraw.Draw(img)
        
        # Add Tier Badge (if Armor)
        if equipment.equipment_type != 'TOOL':
            tier_text = f"T{equipment.tier}"
            d.text((10, 10), tier_text, fill="white")
        
        # Add Initials
        initials = "".join([word[0] for word in equipment.name.split() if word])[:2]
        # Simple centered text (rudimentary centering)
        d.text((40, 50), initials, fill="white")
        
        # Save
        filename = f"icon_{equipment.id}_{equipment.equipment_type}.png"
        save_dir = os.path.join(settings.MEDIA_ROOT, 'rpg', 'equipment_icons')
        os.makedirs(save_dir, exist_ok=True)
        
        file_path = os.path.join(save_dir, filename)
        img.save(file_path)
        
        # Update model
        equipment.icon = f"rpg/equipment_icons/{filename}"
        equipment.save()
        print(f"Generated icon for {equipment.name}: {file_path}")
