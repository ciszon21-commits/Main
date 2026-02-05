import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from EngineerRPG.models import Equipment

class Command(BaseCommand):
    help = 'Updates equipment icons from AI generated artifacts'

    def handle(self, *args, **options):
        # Artifact directory where AI images are saved
        ARTIFACT_DIR = r"C:\Users\07729\.gemini\antigravity\brain\7c95bff2-3df4-4c3c-a6ac-41da9887f44e"
        
        # Target directory - 使用 APP 內的 static 目錄
        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        TARGET_DIR = os.path.join(app_dir, 'static', 'EngineerRPG', 'img', 'equipment_icons')
        os.makedirs(TARGET_DIR, exist_ok=True)

        # Mapping: prefix -> (Type, Tier, NameKeyword)
        mapping = {
            'helmet_t1': ('HELMET', 1, None),
            'helmet_t2': ('HELMET', 2, None),
            'helmet_t3': ('HELMET', 3, None),
            'vest_t1': ('ARMOR', 1, None),
            'vest_t2': ('ARMOR', 2, None),
            'vest_t3': ('ARMOR', 3, None),
            'boots_t1': ('BOOTS', 1, None),
            'boots_t2': ('BOOTS', 2, None),
            'boots_t3': ('BOOTS', 3, None),
            'tool_app': ('TOOL', None, 'APP'),
            'tool_drone': ('TOOL', None, '無人機'),
            'tool_camera': ('TOOL', None, '相機'),
            'tool_vr': ('TOOL', None, 'VR'),
        }

        # Get list of files in artifact dir
        artifact_files = os.listdir(ARTIFACT_DIR)

        for prefix, criteria in mapping.items():
            eq_type, tier, keyword = criteria
            
            # Find matching file in artifacts
            matching_files = [f for f in artifact_files if f.startswith(prefix + "_") and f.endswith(".png")]
            
            if not matching_files:
                self.stdout.write(self.style.WARNING(f"No artifact found for {prefix}"))
                continue
            
            matching_files.sort() 
            source_filename = matching_files[-1]
            source_path = os.path.join(ARTIFACT_DIR, source_filename)
            
            # Find Equipment in DB
            try:
                if eq_type == 'TOOL':
                    items = Equipment.objects.filter(equipment_type=eq_type, name__icontains=keyword)
                else:
                    items = Equipment.objects.filter(equipment_type=eq_type, tier=tier)
                
                if not items.exists():
                     self.stdout.write(self.style.WARNING(f"No equipment found for {prefix}"))
                     continue

                for equipment in items:
                    # Copy and Rename
                    target_filename = f"icon_{equipment.id}_{equipment.equipment_type}.png"
                    target_path = os.path.join(TARGET_DIR, target_filename)
                    
                    shutil.copy2(source_path, target_path)
                    
                    # Update DB - 儲存相對於 static 的路徑
                    equipment.icon = f"EngineerRPG/img/equipment_icons/{target_filename}"
                    equipment.save()
                    
                    self.stdout.write(self.style.SUCCESS(f"Updated {equipment.name} (ID {equipment.id}) from {source_filename}"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error updating {prefix}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS('Icon update complete.'))

