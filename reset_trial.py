from django.utils import timezone
from EngineerRPG.models import DailyTrialProgress, UserProfile
from django.contrib.auth import get_user_model

# 獲取當前用戶（假設用戶已登入，這裡使用第一個超級用戶做測試，或指定用戶名）
User = get_user_model()
try:
    # 這裡預設操作第一個用戶，如果用戶不是第一個，請更換 username
    user = User.objects.first() 
    profile = UserProfile.objects.get(user=user)
    
    # 獲取今天的日期
    today = timezone.now().date()
    
    # 刪除今天的所有試煉進度
    deleted_count, _ = DailyTrialProgress.objects.filter(
        user_profile=profile,
        daily_task__date=today
    ).delete()
    
    print(f"已刪除 {user.username} 今天 ({today}) 的 {deleted_count} 筆試煉進度。")
    print("您可以重新整理頁面開始新的挑戰測試。")

except User.DoesNotExist:
    print("找不到用戶。")
except Exception as e:
    print(f"發生錯誤: {e}")
