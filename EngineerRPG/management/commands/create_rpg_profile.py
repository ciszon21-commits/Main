"""
為現有的 Django 使用者創建 RPG 檔案
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from EngineerRPG.models import UserProfile, CharacterClass


class Command(BaseCommand):
    help = '為現有使用者創建 RPG 檔案'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='使用者名稱')
        parser.add_argument('--class', dest='char_class', type=str, default='CIVIL',
                          help='職業代碼 (CIVIL/ME/SAFETY)')
        parser.add_argument('--role', type=str, default='ADMIN',
                          help='角色 (ADVENTURER/MANAGER/ADMIN)')
        parser.add_argument('--employee-id', dest='employee_id', type=str, default='ADMIN001',
                          help='員工編號')

    def handle(self, *args, **options):
        username = options['username']
        char_class_code = options['char_class']
        role = options['role']
        employee_id = options['employee_id']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'使用者 {username} 不存在'))
            return
        
        # 檢查是否已有 RPG 檔案
        if hasattr(user, 'rpg_profile'):
            self.stdout.write(self.style.WARNING(f'使用者 {username} 已有 RPG 檔案'))
            return
        
        # 獲取職業
        try:
            character_class = CharacterClass.objects.get(code=char_class_code)
        except CharacterClass.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'職業 {char_class_code} 不存在'))
            return
        
        # 創建 RPG 檔案
        profile = UserProfile.objects.create(
            user=user,
            employee_id=employee_id,
            character_class=character_class,
            role=role,
            level=1,
            experience=0,
            hp=character_class.base_hp,
            mp=character_class.base_mp
        )
        
        self.stdout.write(self.style.SUCCESS(
            f'✅ 成功為 {username} 創建 RPG 檔案\n'
            f'   職業：{character_class.name}\n'
            f'   角色：{role}\n'
            f'   HP: {profile.hp} / MP: {profile.mp}'
        ))
