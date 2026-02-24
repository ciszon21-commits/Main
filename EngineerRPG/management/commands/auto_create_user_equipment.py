from django.core.management.base import BaseCommand
from EngineerRPG.models import Equipment, UserEquipment, UserProfile

class Command(BaseCommand):
    help = '為所有玩家自動建立全套裝備的 UserEquipment 記錄'

    def handle(self, *args, **options):
        # 取得所有裝備
        all_equipment = Equipment.objects.all()
        equipment_count = all_equipment.count()
        
        self.stdout.write(f'找到 {equipment_count} 件裝備')
        
        # 取得所有玩家
        all_profiles = UserProfile.objects.all()
        profile_count = all_profiles.count()
        
        self.stdout.write(f'找到 {profile_count} 位玩家')
        
        created_count = 0
        existing_count = 0
        
        # 為每位玩家建立所有裝備
        for profile in all_profiles:
            for equipment in all_equipment:
                user_equipment, created = UserEquipment.objects.get_or_create(
                    user_profile=profile,
                    equipment=equipment,
                    defaults={
                        'enhancement_level': 0,
                        'is_equipped': False,
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[OK] 為 {profile.user.username} 建立 {equipment.name}'
                        )
                    )
                else:
                    existing_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n完成！新建 {created_count} 筆記錄，已存在 {existing_count} 筆'
            )
        )
