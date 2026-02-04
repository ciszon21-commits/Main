"""
檢查並修復 Superuser 權限問題

此腳本會：
1. 檢查所有 superuser 的 UserProfile.role
2. 自動將 superuser 的 role 設置為 ADMIN
3. 顯示白名單管理頁面的訪問方式
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from EngineerRPG.models import UserProfile


class Command(BaseCommand):
    help = '檢查並修復 superuser 的 ADMIN 權限'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('檢查 Superuser 權限狀態'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # 獲取所有 superuser
        superusers = User.objects.filter(is_superuser=True)
        
        if not superusers.exists():
            self.stdout.write(self.style.WARNING('⚠ 系統中沒有 superuser'))
            return
        
        self.stdout.write(f'\n找到 {superusers.count()} 個 superuser：\n')
        
        fixed_count = 0
        for user in superusers:
            try:
                profile = user.rpg_profile
                current_role = profile.role
                
                self.stdout.write(f'  👤 {user.username}')
                self.stdout.write(f'     ├─ 當前角色: {profile.get_role_display()} ({current_role})')
                
                if current_role != 'ADMIN':
                    profile.role = 'ADMIN'
                    profile.save(update_fields=['role'])
                    self.stdout.write(self.style.SUCCESS(f'     └─ ✅ 已修復為 ADMIN'))
                    fixed_count += 1
                else:
                    self.stdout.write(self.style.SUCCESS(f'     └─ ✓ 已經是 ADMIN'))
                    
            except UserProfile.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'     └─ ⚠ 沒有 UserProfile，請先登入一次'))
        
        self.stdout.write('\n' + '=' * 60)
        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'✅ 已修復 {fixed_count} 個 superuser 的權限'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ 所有 superuser 權限正常'))
        
        self.stdout.write('\n📍 訪問管理面板：')
        self.stdout.write('  - 管理面板：http://127.0.0.1:8000/rpg/admin-panel/')
        self.stdout.write('  - 白名單管理：http://127.0.0.1:8000/rpg/admin-panel/whitelist/')
        self.stdout.write('\n💡 白名單功能：')
        self.stdout.write('  - 在白名單管理頁面，您可以將其他使用者設置為管理員')
        self.stdout.write('  - 可授予的角色：OFFICER（公會幹部）、MANAGER（公會會長）、ADMIN（創世神）')
        self.stdout.write('=' * 60 + '\n')
