from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, CharacterClass


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """當 User 創建或更新時，自動處理 UserProfile
    
    功能：
    1. 新使用者創建時自動創建 UserProfile
    2. Superuser 自動獲得 ADMIN 角色
    3. 一般使用者默認為 ADVENTURER 角色
    4. 更新時同步 superuser 狀態到 ADMIN 角色
    """
    if created:
        # 新使用者創建
        try:
            # 檢查是否已有 profile（避免重複創建）
            profile = UserProfile.objects.get(user=instance)
        except UserProfile.DoesNotExist:
            # 獲取默認職業
            default_class = CharacterClass.objects.first()
            if not default_class:
                # 如果沒有任何職業，創建默認的土木戰士
                default_class = CharacterClass.objects.create(
                    code='CIVIL',
                    name='土木戰士',
                    description='專精土木工程的職業'
                )
            
            # 根據是否為 superuser 設置角色
            role = 'ADMIN' if instance.is_superuser else 'ADVENTURER'
            
            # 創建 UserProfile
            profile = UserProfile.objects.create(
                user=instance,
                employee_id=f'EMP{instance.id:05d}',
                character_class=default_class,
                role=role
            )
    else:
        # 使用者更新 - 同步 superuser 狀態
        try:
            profile = instance.rpg_profile
            # 如果變成 superuser，自動升級為 ADMIN
            if instance.is_superuser and profile.role != 'ADMIN':
                profile.role = 'ADMIN'
                profile.save(update_fields=['role'])
            # 注意：不會自動降級，避免誤操作
        except UserProfile.DoesNotExist:
            # 如果使用者存在但沒有 profile，這裡不處理
            # 讓 get_or_create_user_profile 函數處理
            pass
