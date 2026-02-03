import os
import django
from django.utils import timezone

# 設定 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.models import DailyTrialProgress, UserProfile
from django.contrib.auth import get_user_model

def reset_daily_trial():
    User = get_user_model()
    try:
        # 獲取第一個用戶 (通常是管理員/您)
        user = User.objects.first()
        if not user:
            print("沒有找到任何用戶！")
            return

        profile = UserProfile.objects.get(user=user)
        
        # 獲取今天的日期
        today = timezone.now().date()
        
        # 刪除今天的所有試煉進度
        deleted_count, _ = DailyTrialProgress.objects.filter(
            user_profile=profile,
            daily_task__date=today
        ).delete()
        
        print(f"✅ 成功！已刪除用戶 {user.username} 今天 ({today}) 的 {deleted_count} 筆試煉進度。")
        print("➡️ 請重新整理「每日工程挑戰」頁面，所有任務應已重置為「開始挑戰」狀態。")

    except Exception as e:
        print(f"❌ 發生錯誤: {e}")

if __name__ == '__main__':
    reset_daily_trial()
